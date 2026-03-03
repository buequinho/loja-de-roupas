const productsEl = document.getElementById('products');
const cartEl = document.getElementById('cart');
const ordersEl = document.getElementById('orders');
const orderStatusEl = document.getElementById('orderStatus');
const checkoutBtn = document.getElementById('checkout');

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ message: 'Erro inesperado' }));
    throw new Error(err.message || 'Erro de requisição');
  }

  return response.json();
}

function money(value) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

async function loadProducts() {
  const products = await api('/api/products');

  productsEl.innerHTML = products.map((product) => `
    <article class="card">
      <img src="${product.image}" alt="${product.name}" />
      <div class="card-content">
        <h3>${product.name}</h3>
        <p class="muted">${product.category}</p>
        <p><strong>${money(product.price)}</strong></p>
        <p class="muted">Estoque: ${product.stock}</p>
        <button onclick="addToCart(${product.id})">Adicionar</button>
      </div>
    </article>
  `).join('');
}

async function loadCart() {
  const cart = await api('/api/cart');

  if (cart.items.length === 0) {
    cartEl.innerHTML = '<p class="muted">Carrinho vazio.</p>';
    return;
  }

  cartEl.innerHTML = `
    ${cart.items.map((item) => `
      <div class="cart-item">
        <div>
          <strong>${item.product.name}</strong>
          <div class="muted">Qtd: ${item.quantity}</div>
        </div>
        <div>
          ${money(item.subtotal)}
          <button onclick="removeFromCart(${item.productId})">Remover</button>
        </div>
      </div>
    `).join('')}
    <p><strong>Total: ${money(cart.total)}</strong></p>
  `;
}

async function loadOrders() {
  const orders = await api('/api/orders');

  if (orders.length === 0) {
    ordersEl.innerHTML = '<li class="muted">Nenhum pedido ainda.</li>';
    return;
  }

  ordersEl.innerHTML = orders.map((order) => `
    <li>
      Pedido #${order.id} - ${money(order.total)} - ${new Date(order.createdAt).toLocaleString('pt-BR')}
    </li>
  `).join('');
}

async function addToCart(productId) {
  try {
    await api('/api/cart', {
      method: 'POST',
      body: JSON.stringify({ productId, quantity: 1 }),
    });
    await loadCart();
  } catch (error) {
    alert(error.message);
  }
}

async function removeFromCart(productId) {
  try {
    await api(`/api/cart/${productId}`, { method: 'DELETE' });
    await loadCart();
  } catch (error) {
    alert(error.message);
  }
}

checkoutBtn.addEventListener('click', async () => {
  try {
    const result = await api('/api/orders', { method: 'POST' });
    orderStatusEl.textContent = `Pedido #${result.order.id} realizado com sucesso!`;
    await Promise.all([loadCart(), loadOrders()]);
  } catch (error) {
    orderStatusEl.textContent = error.message;
  }
});

window.addToCart = addToCart;
window.removeFromCart = removeFromCart;

Promise.all([loadProducts(), loadCart(), loadOrders()]);
