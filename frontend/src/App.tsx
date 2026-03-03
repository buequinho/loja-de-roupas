import { useEffect, useMemo, useState } from 'react';

type Product = {
  id: number;
  name: string;
  category: string;
  price: number;
  stock: number;
  trend: 'up' | 'down';
  image_url?: string | null;
};

type DashboardResponse = {
  kpis: {
    totalSales: number;
    totalItems: number;
    productsCount: number;
    lowStock: number;
  };
  products: Product[];
};

const apiUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:3333';

export function App() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${apiUrl}/dashboard`)
      .then((response) => {
        if (!response.ok) {
          throw new Error('Falha ao carregar dashboard');
        }
        return response.json();
      })
      .then((json: DashboardResponse) => setData(json))
      .catch(() => setError('Não foi possível carregar os dados da API.'))
      .finally(() => setLoading(false));
  }, []);

  const cards = useMemo(
    () => [
      { label: 'Vendas Totais', value: `R$ ${data?.kpis.totalSales.toFixed(2) ?? '0.00'}` },
      { label: 'Itens em Estoque', value: data?.kpis.totalItems ?? 0 },
      { label: 'Produtos na Vitrine', value: data?.kpis.productsCount ?? 0 },
      { label: 'Atenção de Estoque', value: data?.kpis.lowStock ?? 0 }
    ],
    [data]
  );

  return (
    <main className="page">
      <header className="topbar">
        <div>
          <h1>Dashboard da Loja</h1>
          <p>Visão rápida para evoluir o e-commerce com padrão de mercado.</p>
        </div>
        <button>+ Novo Produto</button>
      </header>

      {loading && <p className="info-box">Carregando dados...</p>}
      {error && <p className="error-box">{error}</p>}

      <section className="kpis">
        {cards.map((card) => (
          <article key={card.label} className="card">
            <span>{card.label}</span>
            <strong>{card.value}</strong>
          </article>
        ))}
      </section>

      <section className="table-section">
        <h2>Produtos em destaque</h2>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Produto</th>
                <th>Categoria</th>
                <th>Preço</th>
                <th>Estoque</th>
                <th>Tendência</th>
              </tr>
            </thead>
            <tbody>
              {!loading && !data?.products.length && (
                <tr>
                  <td colSpan={5}>Nenhum produto disponível.</td>
                </tr>
              )}
              {data?.products.map((product) => (
                <tr key={product.id}>
                  <td className="product-cell">
                    {product.image_url ? <img src={product.image_url} alt={product.name} /> : <div className="image-fallback" />}
                    <span>{product.name}</span>
                  </td>
                  <td>{product.category}</td>
                  <td>R$ {Number(product.price).toFixed(2)}</td>
                  <td>{product.stock}</td>
                  <td>
                    <span className={`badge ${product.trend}`}>{product.trend === 'up' ? '▲ Alta' : '▼ Baixa'}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
