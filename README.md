# Sistema de Loja de Roupas (CLI)

Sistema simples para funcionar como **ficha em sistema**, com:

- cadastro de clientes,
- cadastro de roupas e estoque,
- registro de saída de roupa (pago na hora ou em aberto),
- controle de pagamentos das fichas,
- controle de caixa (entradas/saídas manuais),
- extrato e saldo do caixa.

## Requisitos

- Python 3.10+

## Como usar

```bash
python3 app.py
```

O banco SQLite (`loja.db`) é criado automaticamente na primeira execução.

## Fluxo sugerido

1. Cadastre os clientes.
2. Cadastre as roupas no estoque.
3. Registre saídas (venda):
   - pago agora: já entra no caixa,
   - não pago: fica em aberto como ficha.
4. Quando o cliente pagar, registre o pagamento da ficha.
5. Consulte extrato e saldo do caixa.
