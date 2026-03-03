export type Trend = 'up' | 'down';

export type Product = {
  id: number;
  name: string;
  category: string;
  price: number;
  stock: number;
  trend: Trend;
  image_url: string | null;
};

export type DashboardResponse = {
  kpis: {
    totalSales: number;
    totalItems: number;
    productsCount: number;
    lowStock: number;
  };
  products: Product[];
};

export type CreateProductInput = {
  name: string;
  category: string;
  price: number;
  stock: number;
  trend: Trend;
  image_url?: string;
};

export type ProductFilters = {
  category?: string;
  minStock?: number;
  limit?: number;
};
