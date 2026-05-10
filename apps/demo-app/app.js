const API_BASE = "http://localhost:8000";

const products = [
  {
    product_id: "product-01",
    name: "Serum Vitamin C LumiSkin",
    category: "Skincare",
    brand: "LumiSkin",
    description: "Serum sáng da, kết cấu nhẹ, phù hợp da xỉn màu và cần phục hồi sau nắng.",
    retail_price: 169000,
    live_price: 129000,
    stock_quantity: 18,
  },
  {
    product_id: "product-09",
    name: "Tai nghe Bluetooth TechGo MiniPods",
    category: "Thiết bị công nghệ",
    brand: "TechGo",
    description: "Tai nghe không dây, hộp sạc nhỏ, phù hợp học online và gọi video hằng ngày.",
    retail_price: 259000,
    live_price: 219000,
    stock_quantity: 12,
  },
  {
    product_id: "product-05",
    name: "Bình giữ nhiệt UrbanFlex 500ml",
    category: "Đồ gia dụng",
    brand: "UrbanFlex",
    description: "Giữ nóng lạnh tốt, nắp kín, dễ mang theo khi đi học hoặc đi làm.",
    retail_price: 139000,
    live_price: 99000,
    stock_quantity: 25,
  },
];

const quickMessages = [
  "Sản phẩm này giá live bao nhiêu?",
  "Còn hàng không shop?",
  "Có ship quận 7 không?",
  "Tư vấn giúp mình sản phẩm này phù hợp với ai?",
  "Mình muốn chốt 1 sản phẩm",
  "Cho mình gặp nhân viên tư vấn",
];

const productList = document.getElementById("product-list");
const featuredProductName = document.getElementById("featured-product-name");
const featuredProductPrice = document.getElementById("featured-product-price");
const contextProduct = document.getElementById("context-product");
const quickActions = document.getElementById("quick-actions");
const messageList = document.getElementById("message-list");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const resetChatBtn = document.getElementById("reset-chat-btn");
const viewerCount = document.getElementById("viewer-count");

let selectedProductId = products[0].product_id;
let messages = [];
let isWaitingForBot = false;

function formatCurrency(value) {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value || 0);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function getSelectedProduct() {
  return products.find((product) => product.product_id === selectedProductId) || products[0];
}

function buildInitialMessages() {
  const product = getSelectedProduct();
  return [
    {
      sender_role: "ai",
      sender_name: "SmartLive AI",
      content: `Chào bạn, mình đang hỗ trợ live cho ${product.name}. Bạn có thể hỏi giá, tồn kho, phí ship hoặc nhắn nhu cầu để mình tư vấn ngay.`,
      source: "ai",
      created_at: new Date().toISOString(),
    },
  ];
}

function renderProducts() {
  productList.innerHTML = products.map((product) => {
    const isActive = product.product_id === selectedProductId;
    return `
      <button class="product-card ${isActive ? "active" : ""}" type="button" data-product-id="${escapeHtml(product.product_id)}">
        <strong>${escapeHtml(product.name)}</strong>
        <p>${escapeHtml(product.description)}</p>
        <div class="product-meta">
          <span class="tag price">${escapeHtml(formatCurrency(product.live_price))}</span>
          <span class="tag">Còn ${product.stock_quantity}</span>
          <span class="tag">${escapeHtml(product.category)}</span>
        </div>
      </button>
    `;
  }).join("");
}

function renderSelectedProduct() {
  const product = getSelectedProduct();
  featuredProductName.textContent = product.name;
  featuredProductPrice.textContent = `Giá live ${formatCurrency(product.live_price)}`;
  contextProduct.textContent = product.name;
}

function renderQuickActions() {
  quickActions.innerHTML = quickMessages.map((message) => `
    <button class="quick-action" type="button" data-message="${escapeHtml(message)}">${escapeHtml(message)}</button>
  `).join("");
}

function renderMessages() {
  const typingMessage = isWaitingForBot
    ? '<article class="message bot typing"><span>SmartLive AI đang soạn trả lời...</span><small>Chatbot AI</small></article>'
    : "";

  messageList.innerHTML = messages.map((message) => {
    const role = message.sender_role === "customer" ? "customer" : "bot";
    const sender = message.sender_role === "customer" ? "Khách hàng" : "SmartLive AI";
    return `
      <article class="message ${role}">
        <span>${escapeHtml(message.content)}</span>
        <small>${escapeHtml(sender)}</small>
      </article>
    `;
  }).join("") + typingMessage;

  messageList.scrollTop = messageList.scrollHeight;
}

function render() {
  renderSelectedProduct();
  renderProducts();
  renderQuickActions();
  renderMessages();
}

function pushMessage(senderRole, content) {
  messages.push({
    sender_role: senderRole,
    sender_name: senderRole === "customer" ? "Khách hàng" : "SmartLive AI",
    content,
    source: senderRole === "ai" ? "ai" : "manual",
    created_at: new Date().toISOString(),
  });
}

function chatbotFallbackReply(message) {
  const product = getSelectedProduct();
  const normalized = message.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  if (normalized.includes("gia") || normalized.includes("bao nhieu")) {
    return `${product.name} đang có giá live ${formatCurrency(product.live_price)}. Sản phẩm còn ${product.stock_quantity}, bạn muốn mình giữ hàng không?`;
  }
  if (normalized.includes("con hang") || normalized.includes("ton kho")) {
    return `${product.name} hiện còn ${product.stock_quantity} sản phẩm trong live. Bạn có thể chốt số lượng ngay tại chat.`;
  }
  if (normalized.includes("ship") || normalized.includes("giao")) {
    return `Shop có hỗ trợ giao hàng cho ${product.name}. Bạn gửi khu vực nhận hàng để mình kiểm tra phí ship nhanh nhé.`;
  }
  if (normalized.includes("chot") || normalized.includes("mua") || normalized.includes("dat")) {
    return `Mình ghi nhận bạn muốn chốt ${product.name}. Bạn nhắn số lượng và địa chỉ nhận hàng để shop xác nhận đơn.`;
  }
  return `Mình đang tư vấn ${product.name}. Bạn cần hỏi giá, tồn kho, phí ship hay muốn chốt đơn ạ?`;
}

async function askChatbot(message) {
  const selectedProduct = getSelectedProduct();
  const orderedProducts = [
    selectedProduct,
    ...products.filter((product) => product.product_id !== selectedProduct.product_id),
  ];

  const payload = {
    message,
    customer_name: "Khách livestream",
    account_name: "SmartLive Demo",
    products: orderedProducts,
    conversation_history: messages.slice(-12),
  };

  try {
    const response = await fetch(`${API_BASE}/api/v1/chatbot/reply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`Chatbot API failed: ${response.status}`);
    }
    const data = await response.json();
    return data.reply || chatbotFallbackReply(message);
  } catch (_error) {
    return chatbotFallbackReply(message);
  }
}

async function sendCustomerMessage(content) {
  const message = content.trim();
  if (!message || isWaitingForBot) return;

  pushMessage("customer", message);
  isWaitingForBot = true;
  renderMessages();

  const reply = await askChatbot(message);
  pushMessage("ai", reply);
  isWaitingForBot = false;
  renderMessages();
}

function selectProduct(productId) {
  selectedProductId = productId;
  const product = getSelectedProduct();
  pushMessage("ai", `Mình đã chuyển sang tư vấn ${product.name}. Bạn muốn hỏi giá, tồn kho, ship hay cách chốt đơn?`);
  render();
}

function refreshViewerCount() {
  const viewers = 1180 + Math.floor(Math.random() * 260);
  viewerCount.textContent = `${viewers.toLocaleString("vi-VN")} người xem`;
}

productList.addEventListener("click", (event) => {
  const button = event.target.closest(".product-card");
  if (!button) return;
  selectProduct(button.dataset.productId);
});

quickActions.addEventListener("click", (event) => {
  const button = event.target.closest(".quick-action");
  if (!button) return;
  sendCustomerMessage(button.dataset.message || "");
});

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  sendCustomerMessage(chatInput.value);
  chatInput.value = "";
  chatInput.focus();
});

resetChatBtn.addEventListener("click", () => {
  messages = buildInitialMessages();
  renderMessages();
  chatInput.focus();
});

messages = buildInitialMessages();
render();
setInterval(refreshViewerCount, 3500);
