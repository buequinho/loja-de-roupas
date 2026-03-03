#!/usr/bin/env python3
"""Sistema simples de loja de roupas com cadastro, saídas e controle de caixa."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

DB_PATH = Path("loja.db")

# Cores ANSI (tema rosa e branco)
RESET = "\033[0m"
BOLD = "\033[1m"
ROSA = "\033[95m"
ROSA_FORTE = "\033[35m"
BRANCO = "\033[97m"
VERDE = "\033[92m"
AMARELO = "\033[93m"
VERMELHO = "\033[91m"


@dataclass
class Cliente:
    id: int
    nome: str
    telefone: str


@dataclass
class Roupa:
    id: int
    nome: str
    tamanho: str
    quantidade_estoque: int
    preco: float


class LojaDB:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    def inicializar(self) -> None:
        self.conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT,
                criado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS roupas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tamanho TEXT NOT NULL,
                quantidade_estoque INTEGER NOT NULL CHECK (quantidade_estoque >= 0),
                preco REAL NOT NULL CHECK (preco >= 0),
                criado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS saidas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                roupa_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                valor_total REAL NOT NULL CHECK (valor_total >= 0),
                pago INTEGER NOT NULL DEFAULT 0,
                criado_em TEXT NOT NULL,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                FOREIGN KEY (roupa_id) REFERENCES roupas(id)
            );

            CREATE TABLE IF NOT EXISTS caixa_movimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL CHECK (tipo IN ('ENTRADA', 'SAIDA')),
                valor REAL NOT NULL CHECK (valor >= 0),
                descricao TEXT NOT NULL,
                saida_id INTEGER,
                criado_em TEXT NOT NULL,
                FOREIGN KEY (saida_id) REFERENCES saidas(id)
            );
            """
        )
        self.conn.commit()

    def cadastrar_cliente(self, nome: str, telefone: str) -> None:
        self.conn.execute(
            "INSERT INTO clientes (nome, telefone, criado_em) VALUES (?, ?, ?)",
            (nome.strip(), telefone.strip(), _agora()),
        )
        self.conn.commit()

    def listar_clientes(self) -> list[Cliente]:
        rows = self.conn.execute(
            "SELECT id, nome, telefone FROM clientes ORDER BY nome"
        ).fetchall()
        return [Cliente(**dict(r)) for r in rows]

    def cadastrar_roupa(self, nome: str, tamanho: str, quantidade: int, preco: float) -> None:
        self.conn.execute(
            """INSERT INTO roupas (nome, tamanho, quantidade_estoque, preco, criado_em)
               VALUES (?, ?, ?, ?, ?)""",
            (nome.strip(), tamanho.strip().upper(), quantidade, preco, _agora()),
        )
        self.conn.commit()

    def listar_roupas(self) -> list[Roupa]:
        rows = self.conn.execute(
            """SELECT id, nome, tamanho, quantidade_estoque, preco
               FROM roupas ORDER BY nome, tamanho"""
        ).fetchall()
        return [Roupa(**dict(r)) for r in rows]

    def registrar_saida(
        self,
        cliente_id: int,
        roupa_id: int,
        quantidade: int,
        pago_agora: bool,
    ) -> Optional[str]:
        roupa = self.conn.execute(
            "SELECT id, nome, quantidade_estoque, preco FROM roupas WHERE id = ?",
            (roupa_id,),
        ).fetchone()
        if not roupa:
            return "Roupa não encontrada."

        if roupa["quantidade_estoque"] < quantidade:
            return "Estoque insuficiente para a quantidade solicitada."

        cliente = self.conn.execute(
            "SELECT id FROM clientes WHERE id = ?", (cliente_id,)
        ).fetchone()
        if not cliente:
            return "Cliente não encontrado."

        valor_total = quantidade * roupa["preco"]
        agora = _agora()
        cursor = self.conn.cursor()

        cursor.execute(
            """INSERT INTO saidas (cliente_id, roupa_id, quantidade, valor_total, pago, criado_em)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (cliente_id, roupa_id, quantidade, valor_total, int(pago_agora), agora),
        )
        saida_id = cursor.lastrowid

        cursor.execute(
            "UPDATE roupas SET quantidade_estoque = quantidade_estoque - ? WHERE id = ?",
            (quantidade, roupa_id),
        )

        if pago_agora:
            cursor.execute(
                """INSERT INTO caixa_movimentos (tipo, valor, descricao, saida_id, criado_em)
                   VALUES ('ENTRADA', ?, ?, ?, ?)""",
                (valor_total, f"Venda da saída #{saida_id}", saida_id, agora),
            )

        self.conn.commit()
        return None

    def listar_fichas_abertas(self) -> Iterable[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT s.id,
                   c.nome AS cliente,
                   r.nome || ' ' || r.tamanho AS roupa,
                   s.quantidade,
                   s.valor_total,
                   s.criado_em
              FROM saidas s
              JOIN clientes c ON c.id = s.cliente_id
              JOIN roupas r ON r.id = s.roupa_id
             WHERE s.pago = 0
             ORDER BY s.criado_em DESC
            """
        ).fetchall()

    def registrar_pagamento(self, saida_id: int) -> Optional[str]:
        saida = self.conn.execute(
            "SELECT id, valor_total, pago FROM saidas WHERE id = ?", (saida_id,)
        ).fetchone()
        if not saida:
            return "Saída não encontrada."
        if saida["pago"]:
            return "Essa saída já está paga."

        agora = _agora()
        cursor = self.conn.cursor()
        cursor.execute("UPDATE saidas SET pago = 1 WHERE id = ?", (saida_id,))
        cursor.execute(
            """INSERT INTO caixa_movimentos (tipo, valor, descricao, saida_id, criado_em)
               VALUES ('ENTRADA', ?, ?, ?, ?)""",
            (saida["valor_total"], f"Pagamento da saída #{saida_id}", saida_id, agora),
        )
        self.conn.commit()
        return None

    def registrar_movimento_manual(self, tipo: str, valor: float, descricao: str) -> None:
        self.conn.execute(
            """INSERT INTO caixa_movimentos (tipo, valor, descricao, saida_id, criado_em)
               VALUES (?, ?, ?, NULL, ?)""",
            (tipo, valor, descricao.strip(), _agora()),
        )
        self.conn.commit()

    def saldo_caixa(self) -> float:
        row = self.conn.execute(
            """
            SELECT COALESCE(SUM(CASE WHEN tipo='ENTRADA' THEN valor ELSE -valor END), 0) AS saldo
              FROM caixa_movimentos
            """
        ).fetchone()
        return float(row["saldo"])

    def extrato_caixa(self) -> Iterable[sqlite3.Row]:
        return self.conn.execute(
            "SELECT id, tipo, valor, descricao, criado_em FROM caixa_movimentos ORDER BY id DESC"
        ).fetchall()


def _agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def cor(texto: str, cor_ansi: str, negrito: bool = False) -> str:
    peso = BOLD if negrito else ""
    return f"{peso}{cor_ansi}{texto}{RESET}"


def sucesso(msg: str) -> None:
    print(cor(f"✔ {msg}", VERDE, negrito=True))


def aviso(msg: str) -> None:
    print(cor(f"⚠ {msg}", AMARELO, negrito=True))


def erro(msg: str) -> None:
    print(cor(f"✖ {msg}", VERMELHO, negrito=True))


def cabecalho() -> None:
    print(cor("\n╔══════════════════════════════════════════╗", ROSA_FORTE, negrito=True))
    print(cor("║      SISTEMA LOJA DE ROUPAS - CLI       ║", BRANCO, negrito=True))
    print(cor("║             Tema: Rosa e Branco         ║", ROSA, negrito=True))
    print(cor("╚══════════════════════════════════════════╝", ROSA_FORTE, negrito=True))


def pedir_int(msg: str) -> int:
    while True:
        val = input(cor(msg, BRANCO)).strip()
        try:
            return int(val)
        except ValueError:
            erro("Digite um número inteiro válido.")


def pedir_float(msg: str) -> float:
    while True:
        val = input(cor(msg, BRANCO)).strip().replace(",", ".")
        try:
            return float(val)
        except ValueError:
            erro("Digite um valor numérico válido.")


def exibir_menu(opcoes: dict[str, str]) -> None:
    cabecalho()
    for chave, desc in opcoes.items():
        print(cor(f" {chave} ", ROSA_FORTE, negrito=True) + cor(f"- {desc}", BRANCO))


def menu() -> None:
    db = LojaDB()
    db.inicializar()

    opcoes = {
        "1": "Cadastrar cliente",
        "2": "Listar clientes",
        "3": "Cadastrar roupa no estoque",
        "4": "Listar roupas",
        "5": "Registrar saída de roupa (venda/ficha)",
        "6": "Ver fichas em aberto",
        "7": "Registrar pagamento de ficha",
        "8": "Registrar movimento manual de caixa",
        "9": "Ver extrato e saldo do caixa",
        "0": "Sair",
    }

    try:
        while True:
            exibir_menu(opcoes)
            escolha = input(cor("\nEscolha uma opção: ", ROSA, negrito=True)).strip()

            if escolha == "1":
                nome = input(cor("Nome do cliente: ", BRANCO))
                telefone = input(cor("Telefone: ", BRANCO))
                db.cadastrar_cliente(nome, telefone)
                sucesso("Cliente cadastrado com sucesso.")

            elif escolha == "2":
                clientes = db.listar_clientes()
                print(cor("\n--- CLIENTES ---", ROSA_FORTE, negrito=True))
                if not clientes:
                    aviso("Nenhum cliente cadastrado.")
                for c in clientes:
                    print(cor(f"#{c.id} - {c.nome} | Tel: {c.telefone}", BRANCO))

            elif escolha == "3":
                nome = input(cor("Nome da roupa: ", BRANCO))
                tamanho = input(cor("Tamanho (P/M/G/GG/etc): ", BRANCO))
                quantidade = pedir_int("Quantidade em estoque: ")
                preco = pedir_float("Preço unitário: R$ ")
                db.cadastrar_roupa(nome, tamanho, quantidade, preco)
                sucesso("Roupa cadastrada no estoque.")

            elif escolha == "4":
                roupas = db.listar_roupas()
                print(cor("\n--- ESTOQUE ---", ROSA_FORTE, negrito=True))
                if not roupas:
                    aviso("Nenhuma roupa cadastrada.")
                for r in roupas:
                    print(
                        cor(
                            f"#{r.id} - {r.nome} {r.tamanho} | Estoque: {r.quantidade_estoque} | R$ {r.preco:.2f}",
                            BRANCO,
                        )
                    )

            elif escolha == "5":
                cliente_id = pedir_int("ID do cliente: ")
                roupa_id = pedir_int("ID da roupa: ")
                quantidade = pedir_int("Quantidade da saída: ")
                pago = input(cor("Pagamento agora? (s/n): ", BRANCO)).strip().lower() == "s"
                msg_erro = db.registrar_saida(cliente_id, roupa_id, quantidade, pago)
                if msg_erro:
                    erro(msg_erro)
                else:
                    sucesso("Saída registrada com sucesso.")

            elif escolha == "6":
                fichas = db.listar_fichas_abertas()
                print(cor("\n--- FICHAS EM ABERTO ---", ROSA_FORTE, negrito=True))
                if not fichas:
                    aviso("Não há fichas em aberto.")
                for f in fichas:
                    print(
                        cor(
                            f"Saída #{f['id']} | Cliente: {f['cliente']} | {f['roupa']} x{f['quantidade']} | "
                            f"R$ {f['valor_total']:.2f} | Em: {f['criado_em']}",
                            BRANCO,
                        )
                    )

            elif escolha == "7":
                saida_id = pedir_int("ID da saída para marcar como paga: ")
                msg_erro = db.registrar_pagamento(saida_id)
                if msg_erro:
                    erro(msg_erro)
                else:
                    sucesso("Pagamento registrado e caixa atualizado.")

            elif escolha == "8":
                tipo = input(cor("Tipo (ENTRADA/SAIDA): ", BRANCO)).strip().upper()
                if tipo not in {"ENTRADA", "SAIDA"}:
                    erro("Tipo inválido.")
                    continue
                valor = pedir_float("Valor: R$ ")
                descricao = input(cor("Descrição: ", BRANCO))
                db.registrar_movimento_manual(tipo, valor, descricao)
                sucesso("Movimento registrado.")

            elif escolha == "9":
                print(cor("\n--- EXTRATO DE CAIXA ---", ROSA_FORTE, negrito=True))
                extrato = db.extrato_caixa()
                if not extrato:
                    aviso("Nenhum movimento no caixa.")
                for m in extrato:
                    sinal = "+" if m["tipo"] == "ENTRADA" else "-"
                    cor_valor = ROSA if sinal == "+" else BRANCO
                    print(
                        cor(
                            f"#{m['id']} [{m['criado_em']}] {m['descricao']} -> {sinal}R$ {m['valor']:.2f}",
                            cor_valor,
                        )
                    )
                print(cor(f"Saldo atual: R$ {db.saldo_caixa():.2f}", ROSA_FORTE, negrito=True))

            elif escolha == "0":
                sucesso("Até logo!")
                break

            else:
                erro("Opção inválida.")

            input(cor("\nPressione ENTER para continuar...", ROSA))
    finally:
        db.close()


if __name__ == "__main__":
    menu()
