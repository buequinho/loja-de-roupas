import cors from 'cors';
import dotenv from 'dotenv';
import express from 'express';
import { createProduct, ensureSchema, getDashboard, listProducts } from './db.js';
import type { CreateProductInput, DashboardResponse } from './types.js';

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.get('/products', async (req, res, next) => {
  try {
    const limit = req.query.limit ? Number(req.query.limit) : undefined;
    const minStock = req.query.minStock ? Number(req.query.minStock) : undefined;
    const category = typeof req.query.category === 'string' ? req.query.category : undefined;

    const products = await listProducts({
      limit: Number.isFinite(limit) ? limit : undefined,
      minStock: Number.isFinite(minStock) ? minStock : undefined,
      category
    });

    res.json(products);
  } catch (error) {
    next(error);
  }
});

app.get('/dashboard', async (_req, res, next) => {
  try {
    const [products, summary] = await Promise.all([listProducts({ limit: 6 }), getDashboard()]);

    const payload: DashboardResponse = {
      kpis: {
        totalSales: summary.totalSales,
        totalItems: summary.totalItems,
        productsCount: products.length,
        lowStock: products.filter((product) => product.stock < 8).length
      },
      products
    };

    res.json(payload);
  } catch (error) {
    next(error);
  }
});

app.post('/products', async (req, res, next) => {
  try {
    const { name, category, price, stock, trend, image_url } = req.body as Partial<CreateProductInput>;

    if (!name || !category || typeof price !== 'number' || typeof stock !== 'number') {
      res.status(400).json({ message: 'Campos obrigatórios inválidos: name, category, price e stock.' });
      return;
    }

    if (trend && trend !== 'up' && trend !== 'down') {
      res.status(400).json({ message: "trend deve ser 'up' ou 'down'." });
      return;
    }

    const product = await createProduct({
      name,
      category,
      price,
      stock,
      trend: trend ?? 'up',
      image_url
    });

    res.status(201).json(product);
  } catch (error) {
    next(error);
  }
});

app.use((error: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  console.error('Unhandled API error:', error);
  res.status(500).json({ message: 'Erro interno do servidor.' });
});

const port = Number(process.env.PORT ?? 3333);

ensureSchema()
  .then(() => {
    app.listen(port, () => {
      console.log(`API running on http://localhost:${port}`);
    });
  })
  .catch((error) => {
    console.error('Failed to start API:', error);
    process.exit(1);
  });
