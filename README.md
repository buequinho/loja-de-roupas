# Sistema de Loja de Roupas (CLI)

Sistema simples para funcionar como **ficha em sistema**, com:

- cadastro de clientes,
- cadastro de roupas e estoque,
- registro de saída de roupa (pago na hora ou em aberto),
- controle de pagamentos das fichas,
- controle de caixa (entradas/saídas manuais),
- extrato e saldo do caixa.

## Requisitos

- Python 3.10+ instalado no computador.

## Passo a passo para executar

### 1) Abrir o terminal na pasta do projeto
Entre na pasta onde está o arquivo `app.py`.

Exemplo:

```bash
cd /workspace/loja-de-roupas
```

### 2) (Opcional) Confirmar a versão do Python

```bash
python3 --version
```

Se aparecer versão 3.10 ou maior, está ok.

### 3) Executar o sistema

```bash
python3 app.py
```

Na primeira execução, o sistema cria automaticamente o banco `loja.db` no mesmo diretório.

### 4) Usar o menu
Você verá opções numeradas no terminal. Fluxo recomendado:

1. **Cadastrar cliente**
2. **Cadastrar roupa no estoque**
3. **Registrar saída de roupa (venda/ficha)**
   - se escolher pagamento na hora, entra direto no caixa;
   - se não pagar, fica como ficha em aberto.
4. **Ver fichas em aberto**
5. **Registrar pagamento de ficha** quando o cliente pagar.
6. **Ver extrato e saldo do caixa**.

### 5) Encerrar
No menu, digite:

```text
0
```

para sair do sistema.

## Dicas rápidas

- Se quiser começar do zero, apague o arquivo `loja.db` (isso remove todos os dados).
- Use sempre IDs que o próprio sistema mostra nas listagens (cliente, roupa e saída).
