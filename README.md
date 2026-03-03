# Loja de Roupas (Frontend + Backend)

Projeto full stack de uma loja de roupas com:
- **Backend** em Node.js nativo (sem dependências externas)
- **Frontend** estático (HTML, CSS e JavaScript)

---

## ✅ Pré-requisitos

- Node.js 18+ (recomendado)

Para verificar sua versão:

```bash
node -v
```

---

## 🚀 Passo a passo para executar o código

### 1) Entrar na pasta do projeto

```bash
cd /workspace/loja-de-roupas
```

### 2) Iniciar o servidor

Você pode usar qualquer uma das opções abaixo:

```bash
npm start
```

ou

```bash
node server.js
```

### 3) Acessar no navegador

Abra:

```text
http://localhost:3000
```

---

## 🧪 Passo a passo para testar rapidamente

Com o servidor rodando, execute:

### Verificar saúde da API

```bash
curl -s http://localhost:3000/api/health
```

### Listar produtos

```bash
curl -s http://localhost:3000/api/products
```

### Adicionar item ao carrinho

```bash
curl -s -X POST http://localhost:3000/api/cart \
  -H 'Content-Type: application/json' \
  -d '{"productId":1,"quantity":2}'
```

### Consultar carrinho

```bash
curl -s http://localhost:3000/api/cart
```

### Finalizar pedido

```bash
curl -s -X POST http://localhost:3000/api/orders
```

### Listar pedidos

```bash
curl -s http://localhost:3000/api/orders
```

---

## 📁 Estrutura principal

- `server.js` → backend/API e servidor de arquivos estáticos
- `public/index.html` → estrutura da página
- `public/style.css` → estilos
- `public/app.js` → lógica do frontend (consumo da API)
- `package.json` → scripts de execução

---

## ℹ️ Observação

Este projeto foi feito sem bibliotecas externas para funcionar mesmo em ambientes onde `npm install` pode estar bloqueado.
