const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const PORT = process.env.PORT || 3000;
const publicDir = path.join(__dirname, 'public');

const products = [
  { id: 1, name: 'Camiseta Básica', price: 59.9, image: 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600', category: 'Masculino', stock: 30 },
  { id: 2, name: 'Vestido Floral', price: 129.9, image: 'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=600', category: 'Feminino', stock: 20 },
  { id: 3, name: 'Jaqueta Jeans', price: 199.9, image: 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=600', category: 'Unissex', stock: 15 },
  { id: 4, name: 'Calça Slim', price: 149.9, image: 'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=600', category: 'Masculino', stock: 25 },
  { id: 5, name: 'Blusa Tricot', price: 99.9, image: 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=600', category: 'Feminino', stock: 18 },
  { id: 6, name: 'Tênis Casual', price: 219.9, image: 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=600', category: 'Unissex', stock: 22 }
];

let cart = [];
let orders = [];

function sendJson(res, status, data) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(data));
}

function getBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', (chunk) => {
      data += chunk;
      if (data.length > 1e6) {
        req.destroy();
        reject(new Error('Payload muito grande'));
      }
    });
    req.on('end', () => {
      if (!data) return resolve({});
      try {
        resolve(JSON.parse(data));
      } catch {
        reject(new Error('JSON inválido'));
      }
    });
    req.on('error', reject);
  });
}

function getDetailedCart() {
  const items = cart.map((item) => {
    const product = products.find((p) => p.id === item.productId);
    const subtotal = Number((item.quantity * product.price).toFixed(2));
    return { ...item, product, subtotal };
  });
  const total = Number(items.reduce((acc, item) => acc + item.subtotal, 0).toFixed(2));
  return { items, total };
}

function serveStatic(reqPath, res) {
  const safePath = reqPath === '/' ? '/index.html' : reqPath;
  const filePath = path.join(publicDir, safePath);
  if (!filePath.startsWith(publicDir)) {
    sendJson(res, 403, { message: 'Acesso negado' });
    return true;
  }

  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath);
    const mime = {
      '.html': 'text/html; charset=utf-8',
      '.js': 'application/javascript; charset=utf-8',
      '.css': 'text/css; charset=utf-8',
      '.json': 'application/json; charset=utf-8',
      '.png': 'image/png',
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg'
    }[ext] || 'application/octet-stream';

    res.writeHead(200, { 'Content-Type': mime });
    fs.createReadStream(filePath).pipe(res);
    return true;
  }

  return false;
}

const server = http.createServer(async (req, res) => {
  try {
    const parsedUrl = new URL(req.url, `http://${req.headers.host}`);
    const pathname = parsedUrl.pathname;

    if (pathname === '/api/health' && req.method === 'GET') {
      return sendJson(res, 200, { ok: true, message: 'API funcionando' });
    }

    if (pathname === '/api/products' && req.method === 'GET') {
      return sendJson(res, 200, products);
    }

    if (pathname === '/api/cart' && req.method === 'GET') {
      return sendJson(res, 200, getDetailedCart());
    }

    if (pathname === '/api/cart' && req.method === 'POST') {
      const { productId, quantity = 1 } = await getBody(req);
      const product = products.find((p) => p.id === Number(productId));
      if (!product) return sendJson(res, 404, { message: 'Produto não encontrado' });

      const requestedQty = Number(quantity);
      if (!Number.isInteger(requestedQty) || requestedQty <= 0) {
        return sendJson(res, 400, { message: 'Quantidade inválida' });
      }

      const existing = cart.find((item) => item.productId === product.id);
      const currentQty = existing ? existing.quantity : 0;
      if (currentQty + requestedQty > product.stock) {
        return sendJson(res, 400, { message: 'Estoque insuficiente' });
      }

      if (existing) existing.quantity += requestedQty;
      else cart.push({ productId: product.id, quantity: requestedQty });

      return sendJson(res, 201, { message: 'Item adicionado ao carrinho' });
    }

    if (pathname.startsWith('/api/cart/') && req.method === 'PUT') {
      const productId = Number(pathname.split('/').pop());
      const body = await getBody(req);
      const quantity = Number(body.quantity);
      const item = cart.find((c) => c.productId === productId);
      const product = products.find((p) => p.id === productId);
      if (!item || !product) return sendJson(res, 404, { message: 'Item não encontrado no carrinho' });
      if (!Number.isInteger(quantity) || quantity <= 0 || quantity > product.stock) {
        return sendJson(res, 400, { message: 'Quantidade inválida para o estoque disponível' });
      }

      item.quantity = quantity;
      return sendJson(res, 200, { message: 'Carrinho atualizado' });
    }

    if (pathname.startsWith('/api/cart/') && req.method === 'DELETE') {
      const productId = Number(pathname.split('/').pop());
      const index = cart.findIndex((item) => item.productId === productId);
      if (index === -1) return sendJson(res, 404, { message: 'Item não encontrado no carrinho' });

      cart.splice(index, 1);
      return sendJson(res, 200, { message: 'Item removido do carrinho' });
    }

    if (pathname === '/api/orders' && req.method === 'POST') {
      if (cart.length === 0) return sendJson(res, 400, { message: 'Carrinho vazio' });

      const orderItems = cart.map((item) => {
        const product = products.find((p) => p.id === item.productId);
        const subtotal = Number((item.quantity * product.price).toFixed(2));
        return { productId: product.id, name: product.name, quantity: item.quantity, unitPrice: product.price, subtotal };
      });
      const total = Number(orderItems.reduce((acc, item) => acc + item.subtotal, 0).toFixed(2));
      const order = {
        id: orders.length + 1,
        createdAt: new Date().toISOString(),
        items: orderItems,
        total,
        status: 'confirmado'
      };
      orders.push(order);
      cart = [];
      return sendJson(res, 201, { message: 'Pedido criado com sucesso', order });
    }

    if (pathname === '/api/orders' && req.method === 'GET') {
      return sendJson(res, 200, orders);
    }

    if (!pathname.startsWith('/api/')) {
      if (serveStatic(pathname, res)) return;
      if (serveStatic('/index.html', res)) return;
    }

    sendJson(res, 404, { message: 'Rota não encontrada' });
  } catch (error) {
    sendJson(res, 400, { message: error.message || 'Erro interno' });
  }
});

server.listen(PORT, () => {
  console.log(`Servidor rodando em http://localhost:${PORT}`);
});
