#!/usr/bin/env python3
"""Sistema simples de loja de roupas com cadastro, saídas e controle de caixa."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

DB_PATH = Path("loja.db")


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


def pedir_int(msg: str) -> int:
    while True:
        val = input(msg).strip()
        try:
            return int(val)
        except ValueError:
            print("Digite um número inteiro válido.")


def pedir_float(msg: str) -> float:
    while True:
        val = input(msg).strip().replace(",", ".")
        try:
            return float(val)
        except ValueError:
            print("Digite um valor numérico válido.")


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
            print("\n=== SISTEMA LOJA DE ROUPAS ===")
            for chave, desc in opcoes.items():
                print(f"{chave} - {desc}")

            escolha = input("Escolha uma opção: ").strip()

            if escolha == "1":
                nome = input("Nome do cliente: ")
                telefone = input("Telefone: ")
                db.cadastrar_cliente(nome, telefone)
                print("Cliente cadastrado com sucesso.")

            elif escolha == "2":
                clientes = db.listar_clientes()
                if not clientes:
                    print("Nenhum cliente cadastrado.")
                for c in clientes:
                    print(f"#{c.id} - {c.nome} | Tel: {c.telefone}")

            elif escolha == "3":
                nome = input("Nome da roupa: ")
                tamanho = input("Tamanho (P/M/G/GG/etc): ")
                quantidade = pedir_int("Quantidade em estoque: ")
                preco = pedir_float("Preço unitário: R$ ")
                db.cadastrar_roupa(nome, tamanho, quantidade, preco)
                print("Roupa cadastrada no estoque.")

            elif escolha == "4":
                roupas = db.listar_roupas()
                if not roupas:
                    print("Nenhuma roupa cadastrada.")
                for r in roupas:
                    print(
                        f"#{r.id} - {r.nome} {r.tamanho} | Estoque: {r.quantidade_estoque} | R$ {r.preco:.2f}"
                    )

            elif escolha == "5":
                cliente_id = pedir_int("ID do cliente: ")
                roupa_id = pedir_int("ID da roupa: ")
                quantidade = pedir_int("Quantidade da saída: ")
                pago = input("Pagamento agora? (s/n): ").strip().lower() == "s"
                erro = db.registrar_saida(cliente_id, roupa_id, quantidade, pago)
                if erro:
                    print(f"Erro: {erro}")
                else:
                    print("Saída registrada com sucesso.")

            elif escolha == "6":
                fichas = db.listar_fichas_abertas()
                if not fichas:
                    print("Não há fichas em aberto.")
                for f in fichas:
                    print(
                        f"Saída #{f['id']} | Cliente: {f['cliente']} | {f['roupa']} x{f['quantidade']} | "
                        f"R$ {f['valor_total']:.2f} | Em: {f['criado_em']}"
                    )

            elif escolha == "7":
                saida_id = pedir_int("ID da saída para marcar como paga: ")
                erro = db.registrar_pagamento(saida_id)
                if erro:
                    print(f"Erro: {erro}")
                else:
                    print("Pagamento registrado e caixa atualizado.")

            elif escolha == "8":
                tipo = input("Tipo (ENTRADA/SAIDA): ").strip().upper()
                if tipo not in {"ENTRADA", "SAIDA"}:
                    print("Tipo inválido.")
                    continue
                valor = pedir_float("Valor: R$ ")
                descricao = input("Descrição: ")
                db.registrar_movimento_manual(tipo, valor, descricao)
                print("Movimento registrado.")

            elif escolha == "9":
                print("--- Extrato de caixa ---")
                extrato = db.extrato_caixa()
                if not extrato:
                    print("Nenhum movimento no caixa.")
                for m in extrato:
                    sinal = "+" if m["tipo"] == "ENTRADA" else "-"
                    print(
                        f"#{m['id']} [{m['criado_em']}] {m['descricao']} -> {sinal}R$ {m['valor']:.2f}"
                    )
                print(f"Saldo atual: R$ {db.saldo_caixa():.2f}")

            elif escolha == "0":
                print("Até logo!")
                break

            else:
                print("Opção inválida.")
    finally:
        db.close()


if __name__ == "__main__":
    menu()
