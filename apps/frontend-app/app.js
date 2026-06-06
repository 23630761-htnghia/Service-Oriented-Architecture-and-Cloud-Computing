const API_BASE = "http://localhost:8000";
const WS_BASE = "ws://localhost:8000";
const LIVE_ID = "00000000-0000-0000-0000-000000004001";

const roleHome = {
  CUSTOMER: "/customer/home",
  SELLER: "/seller/dashboard",
  ADMIN: "/admin/dashboard",
};

const routeRoles = {
  "/customer/home": "CUSTOMER",
  "/customer/livestreams": "CUSTOMER",
  "/customer/cart": "CUSTOMER",
  "/customer/orders": "CUSTOMER",
  "/seller/dashboard": "SELLER",
  "/seller/products": "SELLER",
  "/seller/vouchers": "SELLER",
  "/seller/livestreams": "SELLER",
  "/seller/ai-settings": "SELLER",
  "/seller/ai-logs": "SELLER",
  "/seller/fallbacks": "SELLER",
  "/admin/dashboard": "ADMIN",
  "/admin/users": "ADMIN",
  "/admin/shops": "ADMIN",
  "/admin/orders": "ADMIN",
  "/admin/ai-logs": "ADMIN",
};

const RTC_CONFIG = {
  iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
};

const state = {
  token: localStorage.getItem("smartlive_token") || "",
  user: null,
  products: [],
  vouchers: [],
  cart: [],
  selectedProductId: null,
  messages: [],
  socket: null,
  signalSocket: null,
  signalConnectionId: null,
  localStream: null,
  viewerPeerConnection: null,
  sellerPeerConnections: new Map(),
  isStudioLive: false,
  currentPath: window.location.pathname,
};

const $ = (id) => document.getElementById(id);

const els = {
  loginPage: $("login-page"),
  forbiddenPage: $("forbidden-page"),
  protectedShell: $("protected-shell"),
  loginForm: $("login-form"),
  accountSelect: $("account-select"),
  password: $("password"),
  loginStatus: $("login-status"),
  logoutBtn: $("logout-btn"),
  goHomeBtn: $("go-home-btn"),
  authStatus: $("auth-status"),
  sidebarTitle: $("sidebar-title"),
  feedback: $("global-feedback"),
  loadingBar: $("loading-bar"),
  menus: {
    CUSTOMER: $("customer-menu"),
    SELLER: $("seller-menu"),
    ADMIN: $("admin-menu"),
  },
  pages: document.querySelectorAll("[data-page]"),
  liveTitle: $("live-title"),
  featuredImage: $("featured-image"),
  customerLiveBadge: $("customer-live-badge"),
  customerLiveVideo: $("customer-live-video"),
  customerLiveStatus: $("customer-live-status"),
  featuredProductName: $("featured-product-name"),
  featuredProductPrice: $("featured-product-price"),
  customerSummary: $("customer-summary"),
  productList: $("product-list"),
  quickActions: $("quick-actions"),
  messageList: $("message-list"),
  chatForm: $("chat-form"),
  chatInput: $("chat-input"),
  cartList: $("cart-list"),
  voucherApplyForm: $("voucher-apply-form"),
  voucherCode: $("voucher-code"),
  checkoutBtn: $("checkout-btn"),
  orderList: $("order-list"),
  analytics: $("analytics"),
  productForm: $("product-form"),
  sellerProductList: $("seller-product-list"),
  voucherForm: $("voucher-form"),
  voucherList: $("voucher-list"),
  livestreamForm: $("livestream-form"),
  sellerLivestreamList: $("seller-livestream-list"),
  sellerLocalVideo: $("seller-local-video"),
  enableMediaBtn: $("enable-media-btn"),
  toggleCameraBtn: $("toggle-camera-btn"),
  toggleMicBtn: $("toggle-mic-btn"),
  startLiveBtn: $("start-live-btn"),
  stopLiveBtn: $("stop-live-btn"),
  studioLiveStatus: $("studio-live-status"),
  studioCameraStatus: $("studio-camera-status"),
  studioMicStatus: $("studio-mic-status"),
  studioError: $("studio-error"),
  aiToggle: $("ai-toggle"),
  aiSettingsForm: $("ai-settings-form"),
  sellerAiLogList: $("seller-ai-log-list"),
  fallbackList: $("fallback-list"),
  manualReplyForm: $("manual-reply-form"),
  manualReply: $("manual-reply"),
  adminSummary: $("admin-summary"),
  userList: $("user-list"),
  adminShopList: $("admin-shop-list"),
  adminOrderList: $("admin-order-list"),
  aiLogList: $("ai-log-list"),
};

const quickMessages = [
  "Sản phẩm này giá live bao nhiêu?",
  "Sản phẩm này còn hàng không?",
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

function showLoading(visible) {
  els.loadingBar.classList.toggle("hidden", !visible);
}

function notify(message, type = "success") {
  els.feedback.textContent = message;
  els.feedback.className = `feedback ${type}`;
  els.feedback.classList.remove("hidden");
  window.clearTimeout(notify.timer);
  notify.timer = window.setTimeout(() => els.feedback.classList.add("hidden"), 4500);
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
  if (!response.ok) {
    let message = `${path} failed with ${response.status}`;
    try {
      const error = await response.json();
      message = error.detail || message;
    } catch (_error) {}
    throw new Error(message);
  }
  return response.json();
}

async function withFeedback(action, successMessage) {
  showLoading(true);
  try {
    const result = await action();
    if (successMessage) notify(successMessage);
    return result;
  } catch (error) {
    notify(`Lỗi: ${error.message}`, "error");
    return null;
  } finally {
    showLoading(false);
  }
}

function normalizePath(path) {
  if (path === "/" || path === "") return state.user ? roleHome[state.user.role] : "/login";
  return path.replace(/\/$/, "") || "/";
}

function roleForPath(path) {
  if (routeRoles[path]) return routeRoles[path];
  if (/^\/customer\/livestreams\/[^/]+$/.test(path)) return "CUSTOMER";
  if (/^\/seller\/livestreams\/[^/]+\/studio$/.test(path)) return "SELLER";
  return null;
}

function pageForPath(path) {
  if (/^\/customer\/livestreams\/[^/]+$/.test(path)) return "/customer/livestreams";
  if (/^\/seller\/livestreams\/[^/]+\/studio$/.test(path)) return "/seller/livestreams/:id/studio";
  return path;
}

function livestreamIdFromPath(path) {
  const match = path.match(/^\/(?:customer|seller)\/livestreams\/([^/]+)/);
  return match ? decodeURIComponent(match[1]) : LIVE_ID;
}

function navigate(path, replace = false) {
  const target = normalizePath(path);
  if (replace) {
    window.history.replaceState({}, "", target);
  } else {
    window.history.pushState({}, "", target);
  }
  route();
}

function protectedRoute(path) {
  if (!state.user) {
    if (path !== "/login") navigate("/login", true);
    return false;
  }
  return true;
}

function roleRoute(path) {
  const requiredRole = roleForPath(path);
  if (!requiredRole) return false;
  if (state.user.role !== requiredRole) {
    showForbidden(path);
    window.setTimeout(() => navigate(roleHome[state.user.role], true), 900);
    return false;
  }
  return true;
}

function showOnly(page) {
  els.loginPage.classList.toggle("hidden", page !== "login");
  els.forbiddenPage.classList.toggle("hidden", page !== "forbidden");
  els.protectedShell.classList.toggle("hidden", page !== "protected");
}

function showForbidden(path) {
  $("forbidden-message").textContent = `Route ${path} không dành cho role ${state.user?.role || "UNKNOWN"}.`;
  showOnly("forbidden");
}

function renderShellForRole() {
  const role = state.user.role;
  els.sidebarTitle.textContent = `${role} dashboard`;
  els.authStatus.textContent = `${state.user.full_name} - ${role}`;
  Object.entries(els.menus).forEach(([menuRole, menu]) => {
    menu.classList.toggle("hidden", menuRole !== role);
  });
}

function setActiveRoute(path) {
  const page = pageForPath(path);
  document.querySelectorAll("[data-route]").forEach((link) => {
    link.classList.toggle("active", link.dataset.route === path || link.dataset.route === page);
  });
  els.pages.forEach((pageEl) => pageEl.classList.toggle("hidden", pageEl.dataset.page !== page));
}

async function route() {
  const path = normalizePath(window.location.pathname);
  state.currentPath = path;
  const page = pageForPath(path);
  if (page !== "/customer/livestreams" && page !== "/seller/livestreams/:id/studio" && state.signalSocket) {
    state.signalSocket.close();
    state.signalSocket = null;
    closeViewerPeer();
    if (!state.isStudioLive) closeSellerPeers();
  }

  if (path === "/login") {
    if (state.user) {
      navigate(roleHome[state.user.role], true);
      return;
    }
    showOnly("login");
    return;
  }

  if (!protectedRoute(path)) return;
  if (!roleRoute(path)) return;

  showOnly("protected");
  renderShellForRole();
  setActiveRoute(path);
  await refreshForRoute(path);
}

function selectedProduct() {
  return state.products.find((item) => item.product_id === state.selectedProductId) || state.products[0];
}

function renderMetrics(el, entries) {
  el.innerHTML = entries.map(([label, value]) => `
    <article class="metric"><strong>${escapeHtml(value)}</strong><span>${escapeHtml(label)}</span></article>
  `).join("");
}

function renderList(el, items, emptyText, mapper) {
  el.innerHTML = items.map(mapper).join("") || `<p>${escapeHtml(emptyText)}</p>`;
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
            <span class="tag">Còn ${escapeHtml(product.stock_quantity)}</span>
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

function renderQuickActions() {
  els.quickActions.innerHTML = quickMessages.map((message) => `
    <button class="quick-action" type="button" data-message="${escapeHtml(message)}">${escapeHtml(message)}</button>
  `).join("");
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

function appendLocalCustomerMessage(message) {
  state.messages = state.messages.filter((item) => !item.localPending);
  state.messages.push({
    sender_type: "CUSTOMER",
    message,
    localPending: true,
  });
  state.messages.push({
    sender_type: "AI",
    message: "AI đang trả lời...",
    pending: true,
  });
  renderMessages();
}

function renderCart() {
  els.cartList.innerHTML = state.cart.map((item) => {
    const product = state.products.find((entry) => entry.product_id === item.product_id);
    return `
      <article class="compact-item">
        <strong>${escapeHtml(product?.name || item.product_id)}</strong>
        <span>x${escapeHtml(item.quantity)}</span>
        <button class="delete-link" type="button" data-remove-cart="${escapeHtml(item.product_id)}">Xóa</button>
      </article>
    `;
  }).join("") || "<p>Giỏ hàng trống.</p>";
}

function renderSellerProducts() {
  els.sellerProductList.innerHTML = state.products.map((product) => `
    <article class="compact-item">
      <div>
        <strong>${escapeHtml(product.name)}</strong>
        <small>${formatCurrency(product.live_price || product.retail_price)} - tồn ${escapeHtml(product.stock_quantity)}</small>
      </div>
      <button class="delete-link" type="button" data-edit-product="${escapeHtml(product.product_id)}">Sửa</button>
      <button class="delete-link" type="button" data-pin-product="${escapeHtml(product.product_id)}">Ghim</button>
      <button class="delete-link" type="button" data-delete-product="${escapeHtml(product.product_id)}">Xóa</button>
    </article>
  `).join("") || "<p>Chưa có sản phẩm.</p>";
}

function renderVouchers() {
  els.voucherList.innerHTML = state.vouchers.map((voucher) => `
    <article class="compact-item">
      <div>
        <strong>${escapeHtml(voucher.code)} - ${escapeHtml(voucher.discount_value)}</strong>
        <small>${escapeHtml(voucher.conditions || "")}</small>
      </div>
      <button class="delete-link" type="button" data-edit-voucher="${escapeHtml(voucher.voucher_id)}">Sửa</button>
      <button class="delete-link" type="button" data-delete-voucher="${escapeHtml(voucher.voucher_id)}">Xóa</button>
    </article>
  `).join("") || "<p>Chưa có voucher.</p>";
}

async function loadCustomerBase(livestreamId = LIVE_ID) {
  const lives = await api("/livestreams");
  const live = lives.find((item) => item.id === livestreamId) || lives[0];
  els.liveTitle.textContent = live?.title || "Livestream";
  state.products = await api(`/livestreams/${livestreamId}/products`);
  state.vouchers = await api(`/livestreams/${livestreamId}/vouchers`);
  if (!state.selectedProductId && state.products.length) state.selectedProductId = state.products[0].product_id;
}

async function refreshCustomerHome() {
  await loadCustomerBase();
  const orders = await api("/orders/me");
  renderMetrics(els.customerSummary, [
    ["Sản phẩm trong live", state.products.length],
    ["Voucher khả dụng", state.vouchers.length],
    ["Đơn hàng của tôi", orders.length],
    ["AI auto-reply", "ON"],
  ]);
}

async function refreshCustomerLivestream(livestreamId = LIVE_ID) {
  await loadCustomerBase(livestreamId);
  renderProducts();
  renderQuickActions();
  renderMessages();
  connectSocket();
  connectViewerSignal(livestreamId);
}

async function refreshCustomerCart() {
  await loadCustomerBase();
  renderCart();
}

async function refreshCustomerOrders() {
  const orders = await api("/orders/me");
  renderList(els.orderList, orders, "Chưa có đơn hàng.", (order) => `
    <article class="history-item">
      <strong>${escapeHtml(order.id)} - ${escapeHtml(order.status)}</strong>
      <span>${formatCurrency(order.total_amount)}</span>
      <small>${escapeHtml(order.created_at)}</small>
    </article>
  `);
}

async function refreshSellerDashboard() {
  const analytics = await api("/seller/analytics");
  renderMetrics(els.analytics, Object.entries(analytics));
}

async function refreshSellerProducts() {
  state.products = await api(`/livestreams/${LIVE_ID}/products`);
  renderSellerProducts();
}

async function refreshSellerVouchers() {
  state.vouchers = await api("/seller/vouchers");
  renderVouchers();
}

async function refreshSellerLivestreams() {
  const lives = await api("/livestreams");
  renderList(els.sellerLivestreamList, lives, "Chưa có livestream.", (live) => `
    <article class="compact-item">
      <strong>${escapeHtml(live.title)}</strong>
      <span>${escapeHtml(live.status)} / AI ${live.ai_enabled ? "ON" : "OFF"}</span>
      <a class="primary-link small-btn" href="/seller/livestreams/${encodeURIComponent(live.id)}/studio" data-route="/seller/livestreams/${escapeHtml(live.id)}/studio">Studio</a>
    </article>
  `);
}

async function refreshSellerAILogs() {
  const logs = await api(`/seller/livestreams/${LIVE_ID}/ai-logs`);
  renderList(els.sellerAiLogList, logs, "Chưa có AI log.", (log) => `
    <article class="history-item ${log.status === "NEED_SELLER_SUPPORT" ? "escalated" : ""}">
      <strong>${escapeHtml(log.question_type || "unknown")} - ${escapeHtml(log.status)}</strong>
      <span>${escapeHtml(log.final_reply || log.error_message || "")}</span>
      <small>Confidence ${escapeHtml(log.confidence_score)}</small>
    </article>
  `);
}

async function refreshSellerFallbacks() {
  const fallbacks = await api(`/seller/livestreams/${LIVE_ID}/ai-fallbacks`);
  renderList(els.fallbackList, fallbacks, "AI chưa có câu nào cần người bán.", (item) => `
    <article class="history-item escalated">
      <strong>${escapeHtml(item.customer_name || "Khách")}</strong>
      <span>${escapeHtml(item.message)}</span>
      <small>${escapeHtml(item.intent || "")}</small>
    </article>
  `);
}

async function refreshAdminDashboard() {
  const [users, shops, orders, logs] = await Promise.all([
    api("/admin/users"),
    api("/admin/shops"),
    api("/admin/orders"),
    api("/admin/ai-logs"),
  ]);
  renderMetrics(els.adminSummary, [
    ["Users", users.length],
    ["Shops", shops.length],
    ["Orders", orders.length],
    ["AI logs", logs.length],
  ]);
}

async function refreshAdminUsers() {
  const users = await api("/admin/users");
  renderList(els.userList, users, "Chưa có user.", (user) => `
    <article class="history-item">
      <strong>${escapeHtml(user.full_name)} - ${escapeHtml(user.role)}</strong>
      <span>${escapeHtml(user.email)} - ${escapeHtml(user.status)}</span>
      <button class="delete-link" type="button" data-role-user="${escapeHtml(user.id)}" data-next-role="${user.role === "ADMIN" ? "CUSTOMER" : user.role === "SELLER" ? "ADMIN" : "SELLER"}">Đổi role</button>
      <button class="delete-link" type="button" data-lock-user="${escapeHtml(user.id)}">${user.status === "ACTIVE" ? "Khóa" : "Mở khóa"}</button>
    </article>
  `);
}

async function refreshAdminShops() {
  const shops = await api("/admin/shops");
  renderList(els.adminShopList, shops, "Chưa có shop.", (shop) => `
    <article class="history-item"><strong>${escapeHtml(shop.name)}</strong><span>Seller: ${escapeHtml(shop.seller_id)}</span></article>
  `);
}

async function refreshAdminOrders() {
  const orders = await api("/admin/orders");
  renderList(els.adminOrderList, orders, "Chưa có đơn hàng.", (order) => `
    <article class="history-item"><strong>${escapeHtml(order.id)}</strong><span>${formatCurrency(order.total_amount)} - ${escapeHtml(order.status)}</span></article>
  `);
}

async function refreshAdminAILogs() {
  const logs = await api("/admin/ai-logs");
  renderList(els.aiLogList, logs, "Chưa có log AI.", (log) => `
    <article class="history-item"><strong>${escapeHtml(log.status)}</strong><span>${escapeHtml(log.final_reply || log.error_message || "")}</span><small>${escapeHtml(log.created_at)}</small></article>
  `);
}

async function refreshForRoute(path) {
  await withFeedback(async () => {
    const page = pageForPath(path);
    if (path === "/customer/home") await refreshCustomerHome();
    if (page === "/customer/livestreams") await refreshCustomerLivestream(livestreamIdFromPath(path));
    if (path === "/customer/cart") await refreshCustomerCart();
    if (path === "/customer/orders") await refreshCustomerOrders();
    if (path === "/seller/dashboard") await refreshSellerDashboard();
    if (path === "/seller/products") await refreshSellerProducts();
    if (path === "/seller/vouchers") await refreshSellerVouchers();
    if (path === "/seller/livestreams") await refreshSellerLivestreams();
    if (page === "/seller/livestreams/:id/studio") await refreshSellerStudio(livestreamIdFromPath(path));
    if (path === "/seller/ai-settings") await refreshSellerLivestreams();
    if (path === "/seller/ai-logs") await refreshSellerAILogs();
    if (path === "/seller/fallbacks") await refreshSellerFallbacks();
    if (path === "/admin/dashboard") await refreshAdminDashboard();
    if (path === "/admin/users") await refreshAdminUsers();
    if (path === "/admin/shops") await refreshAdminShops();
    if (path === "/admin/orders") await refreshAdminOrders();
    if (path === "/admin/ai-logs") await refreshAdminAILogs();
  }, "");
}

async function login(email, password) {
  const data = await api("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  state.token = data.access_token;
  state.user = data.user;
  localStorage.setItem("smartlive_token", state.token);
  navigate(roleHome[data.user.role], true);
}

async function restoreSession() {
  if (!state.token) return;
  try {
    state.user = await api("/auth/me");
  } catch (_error) {
    state.token = "";
    state.user = null;
    localStorage.removeItem("smartlive_token");
  }
}

function logout() {
  state.token = "";
  state.user = null;
  state.cart = [];
  state.messages = [];
  localStorage.removeItem("smartlive_token");
  if (state.socket) state.socket.close();
  if (state.signalSocket) state.signalSocket.close();
  closeViewerPeer();
  closeSellerPeers();
  if (state.localStream) state.localStream.getTracks().forEach((track) => track.stop());
  navigate("/login", true);
}

function connectSocket() {
  if (!state.token || state.user?.role !== "CUSTOMER") return;
  if (state.socket) state.socket.close();
  state.socket = new WebSocket(`${WS_BASE}/ws/livestreams/${LIVE_ID}?token=${encodeURIComponent(state.token)}`);
  state.socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.event === "ai_processing") {
      if (!state.messages.some((message) => message.pending)) {
        state.messages.push({ sender_type: "AI", message: "AI đang trả lời...", pending: true });
      }
      renderMessages();
      return;
    }
    if (data.event === "customer_message") {
      state.messages = state.messages.filter((message) => {
        if (message.pending) return true;
        return !(message.localPending && message.message === data.payload.message);
      });
      state.messages.push(data.payload);
      renderMessages();
      return;
    }
    if (["ai_reply", "seller_reply", "need_seller_support"].includes(data.event)) {
      state.messages = state.messages.filter((message) => !message.pending);
      state.messages.push(data.payload);
      renderMessages();
    }
  };
}

function setStudioError(message) {
  if (els.studioError) els.studioError.textContent = message || "";
}

function updateStudioStatus() {
  const videoTrack = state.localStream?.getVideoTracks()[0];
  const audioTrack = state.localStream?.getAudioTracks()[0];
  if (els.studioCameraStatus) els.studioCameraStatus.textContent = videoTrack?.enabled ? "Camera đang bật" : "Camera tắt";
  if (els.studioMicStatus) els.studioMicStatus.textContent = audioTrack?.enabled ? "Micro đang bật" : "Micro tắt";
  if (els.studioLiveStatus) els.studioLiveStatus.textContent = state.isStudioLive ? "Livestream đang live" : "Livestream offline";
}

function setCustomerLiveStatus(message, isLive = false) {
  if (els.customerLiveStatus) els.customerLiveStatus.textContent = message;
  if (els.customerLiveBadge) {
    els.customerLiveBadge.classList.toggle("online", isLive);
    els.customerLiveBadge.classList.toggle("offline", !isLive);
  }
  if (els.customerLiveVideo) els.customerLiveVideo.classList.toggle("hidden", !isLive);
  if (els.featuredImage) els.featuredImage.classList.toggle("hidden", isLive);
}

function sendSignal(event, payload = {}) {
  if (state.signalSocket?.readyState !== WebSocket.OPEN) return;
  state.signalSocket.send(JSON.stringify({ event, payload }));
}

function closeViewerPeer() {
  if (state.viewerPeerConnection) {
    state.viewerPeerConnection.close();
    state.viewerPeerConnection = null;
  }
  if (els.customerLiveVideo) els.customerLiveVideo.srcObject = null;
}

function closeSellerPeers() {
  state.sellerPeerConnections.forEach((peer) => peer.close());
  state.sellerPeerConnections.clear();
}

function connectSignal(livestreamId, mode) {
  if (state.signalSocket) state.signalSocket.close();
  state.signalConnectionId = null;
  state.signalSocket = new WebSocket(`${WS_BASE}/ws/signaling/livestreams/${livestreamId}?token=${encodeURIComponent(state.token)}`);
  state.signalSocket.onopen = () => {
    sendSignal("join-livestream", { mode });
  };
  state.signalSocket.onerror = () => {
    if (mode === "seller") setStudioError("Không kết nối được signaling livestream.");
    if (mode === "viewer") setCustomerLiveStatus("Không kết nối được livestream.");
  };
  state.signalSocket.onmessage = async (event) => {
    const data = JSON.parse(event.data);
    await handleSignalEvent(livestreamId, mode, data.event, data.payload || {});
  };
}

async function handleSignalEvent(livestreamId, mode, event, payload) {
  if (event === "signal-ready") {
    state.signalConnectionId = payload.connection_id;
    if (mode === "seller" && state.isStudioLive) {
      sendSignal("livestream-started", {});
      sendSignal("seller-ready", {});
    }
    if (mode === "viewer") {
      setCustomerLiveStatus(payload.is_live ? "Đang kết nối livestream..." : "Livestream chưa bắt đầu", payload.is_live);
    }
    return;
  }
  if (mode === "seller") {
    await handleSellerSignal(livestreamId, event, payload);
    return;
  }
  await handleViewerSignal(livestreamId, event, payload);
}

async function handleSellerSignal(livestreamId, event, payload) {
  if (event === "viewer-joined" && state.isStudioLive && state.localStream) {
    await createSellerOffer(livestreamId, payload.from_id);
  }
  if (event === "webrtc-answer") {
    const peer = state.sellerPeerConnections.get(payload.from_id);
    if (peer && payload.answer) await peer.setRemoteDescription(new RTCSessionDescription(payload.answer));
  }
  if (event === "ice-candidate") {
    const peer = state.sellerPeerConnections.get(payload.from_id);
    if (peer && payload.candidate) await peer.addIceCandidate(new RTCIceCandidate(payload.candidate));
  }
  if (event === "peer-left") {
    const peer = state.sellerPeerConnections.get(payload.from_id);
    if (peer) peer.close();
    state.sellerPeerConnections.delete(payload.from_id);
  }
}

async function handleViewerSignal(livestreamId, event, payload) {
  if (event === "livestream-state") {
    setCustomerLiveStatus(payload.is_live ? "Đang kết nối livestream..." : "Livestream chưa bắt đầu", payload.is_live);
  }
  if (event === "livestream-started" || event === "seller-ready") {
    setCustomerLiveStatus("Đang kết nối livestream...", true);
    sendSignal("join-livestream", { viewer_id: state.signalConnectionId });
  }
  if (event === "livestream-ended" || (event === "peer-left" && payload.from_role === "SELLER")) {
    closeViewerPeer();
    setCustomerLiveStatus("Livestream đã kết thúc", false);
  }
  if (event === "webrtc-offer" && payload.offer) {
    await createViewerAnswer(livestreamId, payload.from_id, payload.offer);
  }
  if (event === "ice-candidate" && state.viewerPeerConnection && payload.candidate) {
    await state.viewerPeerConnection.addIceCandidate(new RTCIceCandidate(payload.candidate));
  }
}

async function enableSellerMedia() {
  try {
    setStudioError("");
    state.localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    els.sellerLocalVideo.srcObject = state.localStream;
    updateStudioStatus();
  } catch (error) {
    setStudioError(`Không bật được camera/micro: ${error.message}`);
  }
}

function toggleLocalTrack(kind) {
  const track = kind === "video" ? state.localStream?.getVideoTracks()[0] : state.localStream?.getAudioTracks()[0];
  if (!track) {
    setStudioError(kind === "video" ? "Không tìm thấy camera." : "Không tìm thấy micro.");
    return;
  }
  track.enabled = !track.enabled;
  updateStudioStatus();
}

async function startSellerLive() {
  const livestreamId = livestreamIdFromPath(state.currentPath);
  if (!state.localStream) {
    await enableSellerMedia();
  }
  if (!state.localStream) return;
  connectSignal(livestreamId, "seller");
  state.isStudioLive = true;
  updateStudioStatus();
  window.setTimeout(() => {
    sendSignal("livestream-started", {});
    sendSignal("seller-ready", {});
  }, 250);
}

function stopSellerLive() {
  state.isStudioLive = false;
  sendSignal("livestream-ended", {});
  closeSellerPeers();
  updateStudioStatus();
}

async function createSellerOffer(livestreamId, viewerId) {
  if (!state.localStream || !viewerId) return;
  const existing = state.sellerPeerConnections.get(viewerId);
  if (existing) existing.close();
  const peer = new RTCPeerConnection(RTC_CONFIG);
  state.localStream.getTracks().forEach((track) => peer.addTrack(track, state.localStream));
  peer.onicecandidate = (event) => {
    if (event.candidate) sendSignal("ice-candidate", { target_id: viewerId, candidate: event.candidate });
  };
  state.sellerPeerConnections.set(viewerId, peer);
  const offer = await peer.createOffer();
  await peer.setLocalDescription(offer);
  sendSignal("webrtc-offer", { target_id: viewerId, offer });
}

async function createViewerAnswer(livestreamId, sellerId, offer) {
  closeViewerPeer();
  const peer = new RTCPeerConnection(RTC_CONFIG);
  state.viewerPeerConnection = peer;
  peer.ontrack = (event) => {
    const [stream] = event.streams;
    if (stream) {
      els.customerLiveVideo.srcObject = stream;
      setCustomerLiveStatus("Livestream đang phát", true);
      els.customerLiveVideo.play().catch(() => {
        setCustomerLiveStatus("Bấm vào video để phát âm thanh", true);
      });
    }
  };
  peer.onicecandidate = (event) => {
    if (event.candidate) sendSignal("ice-candidate", { target_id: sellerId, candidate: event.candidate });
  };
  await peer.setRemoteDescription(new RTCSessionDescription(offer));
  const answer = await peer.createAnswer();
  await peer.setLocalDescription(answer);
  sendSignal("webrtc-answer", { target_id: sellerId, answer });
}

function connectViewerSignal(livestreamId = LIVE_ID) {
  if (state.user?.role !== "CUSTOMER") return;
  connectSignal(livestreamId, "viewer");
}

async function refreshSellerStudio(livestreamId = LIVE_ID) {
  await api(`/livestreams/${livestreamId}`);
  updateStudioStatus();
}

async function sendChat(message) {
  if (state.user?.role !== "CUSTOMER") return;
  appendLocalCustomerMessage(message);
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
  state.messages = state.messages.filter((item) => !item.localPending && !item.pending);
  state.messages.push(response.chat);
  if (response.chat.ai_reply) {
    state.messages.push({
      sender_type: "AI",
      message: response.chat.ai_reply,
      should_escalate: response.chat.should_escalate,
    });
  }
  renderMessages();
}

document.body.addEventListener("click", async (event) => {
  const routeLink = event.target.closest("[data-route]");
  if (routeLink) {
    event.preventDefault();
    navigate(routeLink.dataset.route);
    return;
  }
});

window.addEventListener("popstate", route);

els.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  els.loginStatus.textContent = "Đang đăng nhập...";
  const ok = await withFeedback(() => login(els.accountSelect.value, els.password.value), "Đăng nhập thành công");
  els.loginStatus.textContent = ok === null ? "Đăng nhập thất bại." : "";
});

els.logoutBtn.addEventListener("click", logout);
els.goHomeBtn.addEventListener("click", () => navigate(roleHome[state.user?.role] || "/login", true));

els.productList.addEventListener("click", async (event) => {
  const productButton = event.target.closest("[data-product-id]");
  const cartButton = event.target.closest("[data-cart-product-id]");
  if (cartButton) {
    await withFeedback(async () => {
      state.cart = await api("/cart/items", {
        method: "POST",
        body: JSON.stringify({ product_id: cartButton.dataset.cartProductId, quantity: 1 }),
      });
      renderCart();
    }, "Đã thêm vào giỏ hàng");
    return;
  }
  if (productButton) {
    state.selectedProductId = productButton.dataset.productId;
    renderProducts();
    const detail = await withFeedback(() => api(`/products/${encodeURIComponent(state.selectedProductId)}`), "");
    if (detail) notify(`Đang xem: ${detail.name} - ${formatCurrency(detail.live_price || detail.retail_price)}`);
  }
});

els.quickActions.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-message]");
  if (button) await withFeedback(() => sendChat(button.dataset.message), "");
});

els.chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = els.chatInput.value.trim();
  if (!message) return;
  els.chatInput.value = "";
  await withFeedback(() => sendChat(message), "");
});

els.cartList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-remove-cart]");
  if (!button) return;
  await withFeedback(async () => {
    state.cart = await api(`/cart/items/${encodeURIComponent(button.dataset.removeCart)}`, { method: "DELETE" });
    renderCart();
  }, "Đã xóa khỏi giỏ hàng");
});

els.voucherApplyForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const code = els.voucherCode.value.trim();
  if (!code) return;
  await withFeedback(async () => {
    const result = await api("/cart/voucher", {
      method: "POST",
      body: JSON.stringify({ code }),
    });
    notify(`Đã áp dụng mã ${result.voucher.code}`);
  }, "");
});

els.checkoutBtn.addEventListener("click", async () => {
  await withFeedback(async () => {
    const order = await api("/orders", { method: "POST", body: JSON.stringify({ items: state.cart }) });
    state.cart = [];
    renderCart();
    notify(`Đã tạo đơn ${order.id}`);
    navigate("/customer/orders");
  }, "");
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
  await withFeedback(async () => {
    await api(`/seller/products/${encodeURIComponent(product.product_id)}`, {
      method: "PUT",
      body: JSON.stringify(product),
    });
    els.productForm.reset();
    await refreshSellerProducts();
  }, "Đã lưu sản phẩm");
});

els.sellerProductList.addEventListener("click", async (event) => {
  const editButton = event.target.closest("[data-edit-product]");
  const pinButton = event.target.closest("[data-pin-product]");
  const deleteButton = event.target.closest("[data-delete-product]");
  if (editButton) {
    const product = state.products.find((item) => item.product_id === editButton.dataset.editProduct);
    if (!product) return;
    const form = els.productForm;
    form.product_id.value = product.product_id;
    form.name.value = product.name;
    form.description.value = product.description || "";
    form.retail_price.value = product.retail_price || 0;
    form.live_price.value = product.live_price || "";
    form.stock_quantity.value = product.stock_quantity || 0;
    form.variants.value = product.variants?.join(", ") || "";
    form.image_url.value = product.image_url || "";
  }
  if (pinButton) {
    await withFeedback(() => api(`/seller/livestreams/${LIVE_ID}/pin-product`, {
      method: "POST",
      body: JSON.stringify({ product_id: pinButton.dataset.pinProduct, quantity: 1 }),
    }), "Đã ghim sản phẩm vào livestream");
  }
  if (deleteButton) {
    await withFeedback(async () => {
      await api(`/seller/products/${encodeURIComponent(deleteButton.dataset.deleteProduct)}`, { method: "DELETE" });
      await refreshSellerProducts();
    }, "Đã xóa sản phẩm");
  }
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
  await withFeedback(async () => {
    await api(`/seller/vouchers/${encodeURIComponent(voucher.voucher_id)}`, {
      method: "PUT",
      body: JSON.stringify(voucher),
    });
    els.voucherForm.reset();
    await refreshSellerVouchers();
  }, "Đã lưu voucher");
});

els.voucherList.addEventListener("click", async (event) => {
  const editButton = event.target.closest("[data-edit-voucher]");
  const deleteButton = event.target.closest("[data-delete-voucher]");
  if (editButton) {
    const voucher = state.vouchers.find((item) => item.voucher_id === editButton.dataset.editVoucher);
    if (!voucher) return;
    const form = els.voucherForm;
    form.voucher_id.value = voucher.voucher_id;
    form.code.value = voucher.code;
    form.discount_value.value = voucher.discount_value;
    form.remaining_quantity.value = voucher.remaining_quantity;
    form.conditions.value = voucher.conditions || "";
    form.valid_until.value = voucher.valid_until || "";
  }
  if (deleteButton) {
    await withFeedback(async () => {
      await api(`/seller/vouchers/${encodeURIComponent(deleteButton.dataset.deleteVoucher)}`, { method: "DELETE" });
      await refreshSellerVouchers();
    }, "Đã xóa voucher");
  }
});

els.livestreamForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(els.livestreamForm);
  await withFeedback(async () => {
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
    await refreshSellerLivestreams();
  }, "Đã tạo livestream");
});

els.enableMediaBtn.addEventListener("click", () => {
  withFeedback(enableSellerMedia, "Đã bật camera/mic");
});

els.toggleCameraBtn.addEventListener("click", () => {
  toggleLocalTrack("video");
});

els.toggleMicBtn.addEventListener("click", () => {
  toggleLocalTrack("audio");
});

els.startLiveBtn.addEventListener("click", () => {
  withFeedback(startSellerLive, "Đã bắt đầu livestream");
});

els.stopLiveBtn.addEventListener("click", () => {
  stopSellerLive();
  notify("Đã dừng livestream");
});

els.aiToggle.addEventListener("change", async () => {
  await withFeedback(() => api(`/seller/livestreams/${LIVE_ID}/ai-toggle`, {
    method: "PATCH",
    body: JSON.stringify({ enabled: els.aiToggle.checked, tone: "Thân thiện, ngắn gọn, có tính chốt đơn." }),
  }), els.aiToggle.checked ? "Đã bật AI auto-reply" : "Đã tắt AI auto-reply");
});

els.aiSettingsForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(els.aiSettingsForm);
  await withFeedback(() => api("/seller/ai-settings", {
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
  }), "Đã lưu AI settings");
});

els.manualReplyForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = els.manualReply.value.trim();
  if (!message) return;
  await withFeedback(async () => {
    await api(`/seller/livestreams/${LIVE_ID}/manual-reply`, {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    els.manualReply.value = "";
    await refreshSellerFallbacks();
  }, "Đã gửi phản hồi thủ công");
});

els.userList.addEventListener("click", async (event) => {
  const roleButton = event.target.closest("[data-role-user]");
  const lockButton = event.target.closest("[data-lock-user]");
  if (roleButton) {
    await withFeedback(async () => {
      await api(`/admin/users/${roleButton.dataset.roleUser}/role`, {
        method: "PATCH",
        body: JSON.stringify({ role: roleButton.dataset.nextRole }),
      });
      await refreshAdminUsers();
    }, "Đã đổi role user");
  }
  if (lockButton) {
    await withFeedback(async () => {
      await api(`/admin/users/${lockButton.dataset.lockUser}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: lockButton.textContent === "Khóa" ? "LOCKED" : "ACTIVE" }),
      });
      await refreshAdminUsers();
    }, "Đã cập nhật trạng thái user");
  }
});

async function boot() {
  await restoreSession();
  await route();
}

boot();
