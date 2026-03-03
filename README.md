# Loja de Roupas - Opção 1 (padrão de mercado)

Stack implementada em **TypeScript ponta a ponta**:
- **Front-end:** React + TypeScript (Vite)
- **Back-end:** Node.js + Express + TypeScript
- **Banco:** PostgreSQL

## Estrutura

- `frontend/` Dashboard React.
- `backend/` API Express com rotas `/health`, `/products`, `/dashboard` e `POST /products`.
- `docker-compose.yml` PostgreSQL local.

## Como rodar

1. Suba o banco:
   ```bash
   docker compose up -d
   ```

2. Instale as dependências na raiz:
   ```bash
   npm install
   ```

3. Copie o arquivo de ambiente do backend:
   ```bash
   cp backend/.env.example backend/.env
   ```

4. Rode front + back juntos:
   ```bash
   npm run dev
   ```

## URLs
- Front-end: http://localhost:5173
- Back-end dashboard: http://localhost:3333/dashboard
- Back-end listagem: http://localhost:3333/products?limit=10&category=Masculino&minStock=5

## Evolução rápida
- Endpoint para cadastrar produto:
  ```bash
  curl -X POST http://localhost:3333/products \
    -H "Content-Type: application/json" \
    -d '{"name":"Calça Slim","category":"Masculino","price":199.9,"stock":10,"trend":"up"}'
  ```
