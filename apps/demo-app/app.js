const API_BASE = "http://localhost:8000";
const WS_BASE = "ws://localhost:8000";
const LIVE_ID = "live-01";

const state = {
  token: localStorage.getItem("smartlive_token") || "",
  user: null,
  products: [],
  vouchers: [],
  cart: [],
  selectedProductId: null,
  messages: [],
  socket: null,
};

const $ = (id) => document.getElementById(id);

const els = {
  loginForm: $("login-form"),
  demoAccount: $("demo-account"),
  password: $("password"),
  authStatus: $("auth-status"),
  roleTabs: document.querySelectorAll(".role-tab"),
  views: document.querySelectorAll(".view-grid"),
  productList: $("product-list"),
  featuredImage: $("featured-image"),
  featuredProductName: $("featured-product-name"),
  featuredProductPrice: $("featured-product-price"),
  quickActions: $("quick-actions"),
  messageList: $("message-list"),
  chatForm: $("chat-form"),
  chatInput: $("chat-input"),
  cartList: $("cart-list"),
  checkoutBtn: $("checkout-btn"),
  orderList: $("order-list"),
  productForm: $("product-form"),
  livestreamForm: $("livestream-form"),
  sellerLivestreamList: $("seller-livestream-list"),
  voucherForm: $("voucher-form"),
  voucherList: $("voucher-list"),
  aiToggle: $("ai-toggle"),
  aiSettingsForm: $("ai-settings-form"),
  fallbackList: $("fallback-list"),
  sellerAiLogList: $("seller-ai-log-list"),
  manualReplyForm: $("manual-reply-form"),
  manualReply: $("manual-reply"),
  analytics: $("analytics"),
  userList: $("user-list"),
  adminShopList: $("admin-shop-list"),
  aiLogList: $("ai-log-list"),
  adminOrderList: $("admin-order-list"),
  viewerCount: $("viewer-count"),
};

const quickMessages = [
  "Sản phẩm này giá live bao nhiêu?",
  "Còn hàng không shop?",
  "Có mã giảm giá không?",
  "Phí ship và giao hàng thế nào?",
  "Chính sách đổi trả ra sao?",
  "Mình muốn chốt 1 sản phẩm",
];

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatCurrency(value) {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value || 0);
}

function splitCsv(value) {
  return String(value || "").split(",").map((item) => item.trim()).filter(Boolean);
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (!response.ok) throw new Error(`${path} failed with ${response.status}`);
  return response.json();
}

function showView(viewId) {
  els.views.forEach((view) => view.classList.toggle("hidden", view.id !== viewId));
  els.roleTabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.view === viewId));
}

function viewForRole(role) {
  if (role === "SELLER") return "seller-view";
  if (role === "ADMIN") return "admin-view";
  return "customer-view";
}

function selectedProduct() {
  return state.products.find((item) => item.product_id === state.selectedProductId) || state.products[0];
}

function renderProducts() {
  els.productList.innerHTML = state.products.map((product) => {
    const active = product.product_id === state.selectedProductId ? "active" : "";
    return `
      <article class="product-card ${active}">
        <button class="product-select" type="button" data-product-id="${escapeHtml(product.product_id)}">
          <strong>${escapeHtml(product.name)}</strong>
          <p>${escapeHtml(product.description)}</p>
          <div class="product-meta">
            <span class="tag price">${formatCurrency(product.live_price || product.retail_price)}</span>
            <span class="tag">Còn ${product.stock_quantity}</span>
            <span class="tag">${escapeHtml(product.variants?.join(", ") || product.category || "Phân loại")}</span>
          </div>
        </button>
        <button class="primary-btn small-btn" type="button" data-cart-product-id="${escapeHtml(product.product_id)}">Thêm giỏ</button>
      </article>
    `;
  }).join("");

  const product = selectedProduct();
  if (product) {
    els.featuredProductName.textContent = product.name;
    els.featuredProductPrice.textContent = `Giá live ${formatCurrency(product.live_price || product.retail_price)} - còn ${product.stock_quantity}`;
    els.featuredImage.src = product.image_url || "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?auto=format&fit=crop&w=1400&q=80";
  }
}

function renderMessages() {
  els.messageList.innerHTML = state.messages.map((message) => {
    const role = message.sender_type === "CUSTOMER" ? "customer" : "bot";
    const warn = message.should_escalate ? " escalated" : "";
    const label = message.sender_type === "AI" ? "AI trợ lý của shop" : (message.sender_type || "AI");
    return `
      <article class="message ${role}${warn}">
        <span>${escapeHtml(message.message || message.ai_reply || "")}</span>
        <small>${escapeHtml(label)}${message.should_escalate ? " - cần người bán" : ""}</small>
      </article>
    `;
  }).join("");
  els.messageList.scrollTop = els.messageList.scrollHeight;
}

function renderQuickActions() {
  els.quickActions.innerHTML = quickMessages.map((message) => `
    <button class="quick-action" type="button" data-message="${escapeHtml(message)}">${escapeHtml(message)}</button>
  `).join("");
}

function renderCart() {
  els.cartList.innerHTML = state.cart.map((item) => {
    const product = state.products.find((entry) => entry.product_id === item.product_id);
    return `<article class="compact-item"><strong>${escapeHtml(product?.name || item.product_id)}</strong><span>x${item.quantity}</span></article>`;
  }).join("") || "<p>Giỏ hàng trống.</p>";
}

function renderVouchers() {
  els.voucherList.innerHTML = state.vouchers.map((voucher) => `
    <article class="compact-item">
      <div>
        <strong>${escapeHtml(voucher.code)} - ${escapeHtml(voucher.discount_value)}</strong>
        <small>${escapeHtml(voucher.conditions || "")}</small>
      </div>
      <button class="delete-link" data-delete-voucher="${escapeHtml(voucher.voucher_id)}">Xóa</button>
    </article>
  `).join("") || "<p>Chưa có voucher.</p>";
}

function renderList(el, items, emptyText, mapper) {
  el.innerHTML = items.map(mapper).join("") || `<p>${emptyText}</p>`;
}

async function login(email, password) {
  const data = await api("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  state.token = data.access_token;
  state.user = data.user;
  localStorage.setItem("smartlive_token", state.token);
  els.authStatus.textContent = `${data.user.full_name} - ${data.user.role}`;
  showView(viewForRole(data.user.role));
  connectSocket();
  await refreshAll();
}

async function restoreSession() {
  if (!state.token) return;
  try {
    state.user = await api("/auth/me");
    els.authStatus.textContent = `${state.user.full_name} - ${state.user.role}`;
    showView(viewForRole(state.user.role));
    connectSocket();
  } catch (_error) {
    state.token = "";
    localStorage.removeItem("smartlive_token");
  }
}

function connectSocket() {
  if (!state.token) return;
  if (state.socket) state.socket.close();
  state.socket = new WebSocket(`${WS_BASE}/ws/livestreams/${LIVE_ID}?token=${encodeURIComponent(state.token)}`);
  state.socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.event === "ai_processing") {
      state.messages.push({ sender_type: "AI", message: "AI đang trả lời...", pending: true });
      renderMessages();
      return;
    }
    if (["customer_message", "ai_reply", "seller_reply", "need_seller_support"].includes(data.event)) {
      state.messages = state.messages.filter((message) => !message.pending);
      state.messages.push(data.payload);
      renderMessages();
      refreshSeller();
      refreshAdmin();
    }
  };
}

async function refreshCustomer() {
  const lives = await api("/livestreams");
  const live = lives[0];
  $("live-title").textContent = live?.title || "Livestream";
  els.viewerCount.textContent = `${Number(live?.viewer_count || 0).toLocaleString("vi-VN")} người xem`;
  state.products = await api(`/livestreams/${LIVE_ID}/products`);
  if (!state.selectedProductId && state.products.length) state.selectedProductId = state.products[0].product_id;
  renderProducts();
  renderQuickActions();
  renderCart();
  try {
    const orders = await api("/orders/me");
    renderList(els.orderList, orders, "Chưa có đơn hàng.", (order) => `
      <article class="compact-item"><strong>${escapeHtml(order.id)}</strong><span>${formatCurrency(order.total_amount)}</span></article>
    `);
  } catch (_error) {
    renderList(els.orderList, [], "Chưa có đơn hàng.", () => "");
  }
}

async function refreshSeller() {
  if (state.user?.role !== "SELLER") return;
  state.products = await api(`/livestreams/${LIVE_ID}/products`);
  state.vouchers = await api("/seller/vouchers");
  renderProducts();
  renderVouchers();
  const analytics = await api("/seller/analytics");
  els.analytics.innerHTML = Object.entries(analytics).map(([key, value]) => `
    <article class="metric"><strong>${escapeHtml(value)}</strong><span>${escapeHtml(key)}</span></article>
  `).join("");
  const fallbacks = await api(`/seller/livestreams/${LIVE_ID}/ai-fallbacks`);
  renderList(els.fallbackList, fallbacks, "AI chưa có câu nào cần người bán.", (item) => `
    <article class="history-item escalated"><strong>${escapeHtml(item.customer_name || "Khách")}</strong><span>${escapeHtml(item.message)}</span><small>${escapeHtml(item.intent || "")}</small></article>
  `);
  const logs = await api(`/seller/livestreams/${LIVE_ID}/ai-logs`);
  renderList(els.sellerAiLogList, logs, "Chưa có AI log.", (log) => `
    <article class="history-item ${log.status === "NEED_SELLER_SUPPORT" ? "escalated" : ""}">
      <strong>${escapeHtml(log.question_type || "unknown")} - ${escapeHtml(log.status)}</strong>
      <span>${escapeHtml(log.final_reply || log.error_message || "")}</span>
      <small>Model log confidence ${log.confidence_score}</small>
    </article>
  `);
  const lives = await api("/livestreams");
  renderList(els.sellerLivestreamList, lives, "Chưa có livestream.", (live) => `
    <article class="compact-item"><strong>${escapeHtml(live.title)}</strong><span>${escapeHtml(live.status)} / AI ${live.ai_enabled ? "ON" : "OFF"}</span></article>
  `);
}

async function refreshAdmin() {
  if (state.user?.role !== "ADMIN") return;
  const users = await api("/admin/users");
  renderList(els.userList, users, "Chưa có user.", (user) => `
    <article class="history-item">
      <strong>${escapeHtml(user.full_name)} - ${escapeHtml(user.role)}</strong>
      <span>${escapeHtml(user.email)} - ${escapeHtml(user.status)}</span>
      <button class="delete-link" data-lock-user="${escapeHtml(user.id)}">${user.status === "ACTIVE" ? "Khóa" : "Mở khóa"}</button>
    </article>
  `);
  const logs = await api("/admin/ai-logs");
  renderList(els.aiLogList, logs, "Chưa có log AI.", (log) => `
    <article class="history-item"><strong>${escapeHtml(log.status)}</strong><span>Confidence ${log.confidence_score}</span><small>${escapeHtml(log.created_at)}</small></article>
  `);
  const orders = await api("/admin/orders");
  renderList(els.adminOrderList, orders, "Chưa có đơn hàng.", (order) => `
    <article class="history-item"><strong>${escapeHtml(order.id)}</strong><span>${formatCurrency(order.total_amount)} - ${escapeHtml(order.status)}</span></article>
  `);
  const shops = await api("/admin/shops");
  renderList(els.adminShopList, shops, "Chưa có shop.", (shop) => `
    <article class="history-item"><strong>${escapeHtml(shop.name)}</strong><span>Seller: ${escapeHtml(shop.seller_id)}</span></article>
  `);
}

async function refreshAll() {
  if (!state.user) return;
  await refreshCustomer();
  await refreshSeller();
  await refreshAdmin();
}

async function sendChat(message) {
  if (state.socket?.readyState === WebSocket.OPEN) {
    state.socket.send(JSON.stringify({
      event: "customer_message",
      payload: { message, product_id: state.selectedProductId },
    }));
    return;
  }
  const response = await api(`/livestreams/${LIVE_ID}/chat`, {
    method: "POST",
    body: JSON.stringify({ message, product_id: state.selectedProductId, customer_name: state.user.full_name }),
  });
  state.messages.push(response.chat);
  renderMessages();
}

els.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await login(els.demoAccount.value, els.password.value);
});

els.roleTabs.forEach((tab) => tab.addEventListener("click", () => showView(tab.dataset.view)));

els.productList.addEventListener("click", async (event) => {
  const productButton = event.target.closest("[data-product-id]");
  const cartButton = event.target.closest("[data-cart-product-id]");
  if (cartButton) {
    const item = await api("/cart/items", {
      method: "POST",
      body: JSON.stringify({ product_id: cartButton.dataset.cartProductId, quantity: 1 }),
    });
    state.cart = item;
    renderCart();
    return;
  }
  if (productButton) {
    state.selectedProductId = productButton.dataset.productId;
    renderProducts();
  }
});

els.quickActions.addEventListener("click", (event) => {
  const button = event.target.closest("[data-message]");
  if (button) sendChat(button.dataset.message);
});

els.chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = els.chatInput.value.trim();
  if (!message) return;
  els.chatInput.value = "";
  await sendChat(message);
});

els.checkoutBtn.addEventListener("click", async () => {
  const order = await api("/orders", { method: "POST", body: JSON.stringify({ items: state.cart }) });
  state.cart = [];
  renderCart();
  await refreshCustomer();
  alert(`Đã tạo đơn ${order.id}`);
});

els.productForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(els.productForm);
  const product = {
    product_id: form.get("product_id"),
    name: form.get("name"),
    description: form.get("description") || "",
    retail_price: Number(form.get("retail_price") || 0),
    live_price: Number(form.get("live_price") || 0) || null,
    stock_quantity: Number(form.get("stock_quantity") || 0),
    variants: splitCsv(form.get("variants")),
    image_url: form.get("image_url") || null,
    category: "Livestream",
    brand: "SmartLive",
    related_product_ids: [],
  };
  await api(`/seller/products/${encodeURIComponent(product.product_id)}`, {
    method: "PUT",
    body: JSON.stringify(product),
  });
  els.productForm.reset();
  await refreshAll();
});

els.livestreamForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(els.livestreamForm);
  await api("/seller/livestreams", {
    method: "POST",
    body: JSON.stringify({
      title: form.get("title"),
      description: form.get("description") || "",
      status: "LIVE",
      ai_enabled: true,
    }),
  });
  els.livestreamForm.reset();
  await refreshSeller();
});

els.voucherForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(els.voucherForm);
  const voucher = {
    voucher_id: form.get("voucher_id"),
    code: form.get("code"),
    discount_type: "AMOUNT",
    discount_value: form.get("discount_value"),
    min_order_value: 0,
    conditions: form.get("conditions") || "",
    valid_until: form.get("valid_until") || null,
    remaining_quantity: Number(form.get("remaining_quantity") || 0),
    applicable_product_ids: [],
  };
  await api(`/seller/vouchers/${encodeURIComponent(voucher.voucher_id)}`, {
    method: "PUT",
    body: JSON.stringify(voucher),
  });
  els.voucherForm.reset();
  await refreshSeller();
});

els.voucherList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-delete-voucher]");
  if (!button) return;
  await api(`/seller/vouchers/${encodeURIComponent(button.dataset.deleteVoucher)}`, { method: "DELETE" });
  await refreshSeller();
});

els.aiToggle.addEventListener("change", async () => {
  await api(`/seller/livestreams/${LIVE_ID}/ai-toggle`, {
    method: "PATCH",
    body: JSON.stringify({ enabled: els.aiToggle.checked, tone: "Thân thiện, ngắn gọn, có tính chốt đơn." }),
  });
});

els.aiSettingsForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(els.aiSettingsForm);
  await api("/seller/ai-settings", {
    method: "PUT",
    body: JSON.stringify({
      enabled: els.aiToggle.checked,
      model_name: form.get("model_name") || "llama3.1",
      temperature: Number(form.get("temperature") || 0.2),
      max_tokens: Number(form.get("max_tokens") || 220),
      tone: form.get("tone") || "Thân thiện, ngắn gọn, có tính chốt đơn.",
      reply_style: form.get("reply_style") || "ngắn gọn, thân thiện, chốt đơn",
      auto_reply_enabled: els.aiToggle.checked,
      fallback_to_seller_enabled: true,
    }),
  });
  await refreshSeller();
});

els.manualReplyForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = els.manualReply.value.trim();
  if (!message) return;
  await api(`/seller/livestreams/${LIVE_ID}/manual-reply`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
  els.manualReply.value = "";
});

els.userList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-lock-user]");
  if (!button) return;
  const user = await api(`/admin/users/${button.dataset.lockUser}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status: button.textContent === "Khóa" ? "LOCKED" : "ACTIVE" }),
  });
  await refreshAdmin();
});

async function boot() {
  await restoreSession();
  if (!state.user) await login("customer@smartlive.test", "123456");
}

boot().catch((error) => {
  els.authStatus.textContent = `Không kết nối được backend: ${error.message}`;
});
