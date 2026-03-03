const STORAGE_KEY = "dashboard-products";

const form = document.querySelector("#product-form");
const idInput = document.querySelector("#product-id");
const nameInput = document.querySelector("#name");
const priceInput = document.querySelector("#price");
const stockInput = document.querySelector("#stock");
const categoryInput = document.querySelector("#category");
const submitButton = document.querySelector("#submit-button");
const cancelEditButton = document.querySelector("#cancel-edit");
const productList = document.querySelector("#product-list");
const productCount = document.querySelector("#product-count");
const emptyStateTemplate = document.querySelector("#empty-state-template");

let products = loadProducts();

renderProducts();

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const product = readFormData();
  if (!product) {
    return;
  }

  if (idInput.value) {
    products = products.map((item) => (item.id === idInput.value ? { ...item, ...product } : item));
  } else {
    products.push({
      id: crypto.randomUUID(),
      ...product,
    });
  }

  saveProducts(products);
  renderProducts();
  resetForm();
});

cancelEditButton.addEventListener("click", resetForm);

function readFormData() {
  const name = nameInput.value.trim();
  const category = categoryInput.value.trim();
  const price = Number(priceInput.value);
  const stock = Number(stockInput.value);

  if (!name || !category || Number.isNaN(price) || Number.isNaN(stock) || price < 0 || stock < 0) {
    alert("Preencha todos os campos com valores válidos.");
    return null;
  }

  return { name, category, price, stock };
}

function renderProducts() {
  productList.innerHTML = "";

  if (products.length === 0) {
    productList.append(emptyStateTemplate.content.cloneNode(true));
    updateCounter();
    return;
  }

  products.forEach((product) => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${product.name}</td>
      <td>${product.category}</td>
      <td>${formatCurrency(product.price)}</td>
      <td>${product.stock}</td>
      <td class="actions-cell">
        <button class="icon" data-action="edit" data-id="${product.id}">Editar</button>
        <button class="icon danger" data-action="delete" data-id="${product.id}">Excluir</button>
      </td>
    `;

    productList.append(row);
  });

  updateCounter();
}

productList.addEventListener("click", (event) => {
  const target = event.target;

  if (!(target instanceof HTMLButtonElement)) {
    return;
  }

  const action = target.dataset.action;
  const productId = target.dataset.id;
  const selectedProduct = products.find((product) => product.id === productId);

  if (!selectedProduct) {
    return;
  }

  if (action === "edit") {
    idInput.value = selectedProduct.id;
    nameInput.value = selectedProduct.name;
    categoryInput.value = selectedProduct.category;
    priceInput.value = selectedProduct.price;
    stockInput.value = selectedProduct.stock;

    submitButton.textContent = "Salvar alterações";
    cancelEditButton.classList.remove("hidden");
    nameInput.focus();
  }

  if (action === "delete") {
    products = products.filter((product) => product.id !== productId);
    saveProducts(products);
    renderProducts();

    if (idInput.value === productId) {
      resetForm();
    }
  }
});

function resetForm() {
  form.reset();
  idInput.value = "";
  submitButton.textContent = "Cadastrar produto";
  cancelEditButton.classList.add("hidden");
}

function updateCounter() {
  const total = products.length;
  productCount.textContent = `${total} ${total === 1 ? "produto" : "produtos"}`;
}

function formatCurrency(value) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(value);
}

function loadProducts() {
  const raw = localStorage.getItem(STORAGE_KEY);

  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveProducts(productData) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(productData));
}
