import dotenv from 'dotenv';
import { Pool } from 'pg';
import type { CreateProductInput, Product, ProductFilters } from './types.js';

dotenv.config();

export const pool = new Pool({
  host: process.env.DB_HOST ?? 'localhost',
  port: Number(process.env.DB_PORT ?? 5432),
  user: process.env.DB_USER ?? 'postgres',
  password: process.env.DB_PASSWORD ?? 'postgres',
  database: process.env.DB_NAME ?? 'loja_roupas'
});

export async function ensureSchema(): Promise<void> {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS products (
      id SERIAL PRIMARY KEY,
      name VARCHAR(120) NOT NULL,
      category VARCHAR(80) NOT NULL,
      price NUMERIC(10,2) NOT NULL,
      stock INTEGER NOT NULL DEFAULT 0,
      trend VARCHAR(20) NOT NULL DEFAULT 'up',
      image_url TEXT,
      created_at TIMESTAMP DEFAULT NOW()
    );
  `);

  const { rows } = await pool.query<{ total: number }>('SELECT COUNT(*)::int AS total FROM products');

  if (rows[0]?.total === 0) {
    await pool.query(`
      INSERT INTO products (name, category, price, stock, trend, image_url)
      VALUES
        ('Jaqueta Bomber', 'Masculino', 249.90, 12, 'up', 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400'),
        ('Vestido Midi Floral', 'Feminino', 189.90, 7, 'up', 'https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400'),
        ('Tênis Casual Branco', 'Calçados', 299.90, 18, 'down', 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400'),
        ('Blusa Tricô Premium', 'Inverno', 159.90, 5, 'up', 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400');
    `);
  }
}

export async function listProducts(filters: ProductFilters = {}): Promise<Product[]> {
  const values: Array<string | number> = [];
  const where: string[] = [];

  if (filters.category) {
    values.push(filters.category);
    where.push(`category = $${values.length}`);
  }

  if (typeof filters.minStock === 'number') {
    values.push(filters.minStock);
    where.push(`stock >= $${values.length}`);
  }

  const limit = filters.limit && filters.limit > 0 ? Math.min(filters.limit, 100) : 6;
  values.push(limit);

  const whereClause = where.length > 0 ? `WHERE ${where.join(' AND ')}` : '';

  const result = await pool.query<Product>(
    `SELECT id, name, category, price::float8 as price, stock, trend, image_url
     FROM products
     ${whereClause}
     ORDER BY id DESC
     LIMIT $${values.length}`,
    values
  );

  return result.rows;
}

export async function getDashboard(): Promise<{ totalSales: number; totalItems: number }> {
  const [salesResult, stockResult] = await Promise.all([
    pool.query<{ total_sales: number }>('SELECT COALESCE(SUM(price), 0)::float8 AS total_sales FROM products'),
    pool.query<{ total_items: number }>('SELECT COALESCE(SUM(stock), 0)::int AS total_items FROM products')
  ]);

  return {
    totalSales: salesResult.rows[0]?.total_sales ?? 0,
    totalItems: stockResult.rows[0]?.total_items ?? 0
  };
}

export async function createProduct(input: CreateProductInput): Promise<Product> {
  const result = await pool.query<Product>(
    `INSERT INTO products (name, category, price, stock, trend, image_url)
     VALUES ($1, $2, $3, $4, $5, $6)
     RETURNING id, name, category, price::float8 as price, stock, trend, image_url`,
    [input.name, input.category, input.price, input.stock, input.trend, input.image_url ?? null]
  );

  return result.rows[0] as Product;
}
