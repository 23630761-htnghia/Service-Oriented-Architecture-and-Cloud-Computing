const API_BASE = "http://localhost:8000";
const SESSION_KEY = "smartlive-demo-session-v7";
const LOCAL_STATE_KEY = "smartlive-demo-local-v6";
const PRESENCE_SESSION_KEY = "smartlive-demo-presence-id";
const REALTIME_REFRESH_MS = 3000;

const loginScreen = document.getElementById("login-screen");
const appScreen = document.getElementById("app-screen");
const loginForm = document.getElementById("login-form");
const loginEmail = document.getElementById("login-email");
const loginPassword = document.getElementById("login-password");
const loginResult = document.getElementById("login-result");
const registerForm = document.getElementById("register-form");
const registerPhone = document.getElementById("register-phone");
const registerFullName = document.getElementById("register-full-name");
const registerEmail = document.getElementById("register-email");
const registerLocation = document.getElementById("register-location");
const registerBirthYear = document.getElementById("register-birth-year");
const registerPassword = document.getElementById("register-password");
const registerResult = document.getElementById("register-result");
const openLoginBtn = document.getElementById("open-login-btn");
const openRegisterBtn = document.getElementById("open-register-btn");
const closeRegisterBtn = document.getElementById("close-register-btn");
const registerPanel = document.getElementById("register-panel");
const demoAccountButtons = document.querySelectorAll(".demo-account-btn");
const logoutBtn = document.getElementById("logout-btn");
const resetDemoBtn = document.getElementById("reset-demo-btn");

const topbarTitle = document.getElementById("topbar-title");
const topbarSubtitle = document.getElementById("topbar-subtitle");
const currentUserName = document.getElementById("current-user-name");
const currentUserRole = document.getElementById("current-user-role");
const liveRoomTitle = document.getElementById("live-room-title");
const liveRoomDescription = document.getElementById("live-room-description");
const livePreview = document.getElementById("live-preview");
const remotePreviewFrame = document.getElementById("remote-preview-frame");
const videoOverlay = document.getElementById("video-overlay");
const videoOverlayText = document.getElementById("video-overlay-text");
const liveStatusPill = document.getElementById("live-status-pill");
const sessionCard = document.getElementById("session-card");
const pinnedProductCard = document.getElementById("pinned-product-card");
const customerRoomToolbar = document.getElementById("customer-room-toolbar");
const customerRoomSearchInput = document.getElementById("customer-room-search-input");
const customerRoomList = document.getElementById("customer-room-list");

const metricLiveStatus = document.getElementById("metric-live-status");
const metricViewers = document.getElementById("metric-viewers");
const metricComments = document.getElementById("metric-comments");
const metricBlocked = document.getElementById("metric-blocked");

const staffView = document.getElementById("staff-view");
const customerView = document.getElementById("customer-view");
const commentPanel = document.getElementById("comment-form").closest(".panel");
const messagePanel = document.getElementById("message-form").closest(".panel");
const chatModal = document.getElementById("chat-modal");
const openChatBtn = document.getElementById("open-chat-btn");
const closeChatBtn = document.getElementById("close-chat-btn");

const connectMediaBtn = document.getElementById("connect-media-btn");
const toggleCameraBtn = document.getElementById("toggle-camera-btn");
const toggleMicBtn = document.getElementById("toggle-mic-btn");
const startLiveBtn = document.getElementById("start-live-btn");
const endLiveBtn = document.getElementById("end-live-btn");
const deviceStatus = document.getElementById("device-status");
const staffActionResult = document.getElementById("staff-action-result");
const staffProductList = document.getElementById("staff-product-list");

const productForm = document.getElementById("product-form");
const productNameInput = document.getElementById("product-name-input");
const productCategoryInput = document.getElementById("product-category-input");
const productPriceInput = document.getElementById("product-price-input");
const productStockInput = document.getElementById("product-stock-input");
const productHighlightInput = document.getElementById("product-highlight-input");
const liveAssignmentForm = document.getElementById("live-assignment-form");
const assignmentLiveSelect = document.getElementById("assignment-live-select");
const assignmentProductSelect = document.getElementById("assignment-product-select");
const productManagerResult = document.getElementById("product-manager-result");
const productManagerList = document.getElementById("product-manager-list");
const liveAssignmentList = document.getElementById("live-assignment-list");

const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const searchResult = document.getElementById("search-result");
const searchList = document.getElementById("search-list");
const recommendationList = document.getElementById("recommendation-list");
const cartResult = document.getElementById("cart-result");
const customerCartList = document.getElementById("customer-cart-list");
const clearCartBtn = document.getElementById("clear-cart-btn");
const checkoutBtn = document.getElementById("checkout-btn");

const commentForm = document.getElementById("comment-form");
const commentProductSelect = document.getElementById("comment-product-select");
const commentInput = document.getElementById("comment-input");
const commentResult = document.getElementById("comment-result");
const commentList = document.getElementById("comment-list");

const conversationList = document.getElementById("conversation-list");
const threadHeader = document.getElementById("thread-header");
const messageThread = document.getElementById("message-thread");
const messageForm = document.getElementById("message-form");
const messageInput = document.getElementById("message-input");
const messageResult = document.getElementById("message-result");

const INITIAL_LOCAL_STATE = {
  blockedUsers: {},
};

let currentUser = null;
let demoState = structuredClone(INITIAL_LOCAL_STATE);
let backendState = {
  accounts: [],
  products: [],
  assignments: [],
  liveOffers: [],
  customers: [],
  cartItems: [],
  orders: [],
  comments: [],
  messages: [],
};
let selectedAccountId = null;
let selectedConversationCustomerId = null;
let mediaStream = null;
let cameraEnabled = true;
let micEnabled = true;
let hostLiveEnabled = false;
let isChatModalOpen = false;
let realtimeRefreshTimer = null;
let realtimeRefreshInFlight = false;
let currentPresenceAccountId = null;
let previewBroadcastTimer = null;
let lastRemotePreviewPayload = null;
const previewChannel = typeof BroadcastChannel !== "undefined"
  ? new BroadcastChannel("smartlive-demo-preview")
  : null;

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

function formatDateTime(value) {
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "2-digit",
  }).format(new Date(value));
}

function normalizeText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .trim();
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const text = await response.text();
  let payload = null;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch (_error) {
    payload = text;
  }

  if (!response.ok) {
    const detail = payload && typeof payload === "object" ? payload.detail : payload;
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return payload;
}

function saveSession() {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify({
    currentUser,
    selectedAccountId,
    selectedConversationCustomerId,
  }));
}

function loadSession() {
  const raw = sessionStorage.getItem(SESSION_KEY);
  if (!raw) return;
  try {
    const parsed = JSON.parse(raw);
    currentUser = parsed.currentUser || null;
    if (currentUser && currentUser.role !== "staff" && currentUser.role !== "customer") {
      currentUser = null;
    }
    selectedAccountId = parsed.selectedAccountId || null;
    selectedConversationCustomerId = parsed.selectedConversationCustomerId || null;
  } catch (_error) {
    currentUser = null;
    selectedAccountId = null;
    selectedConversationCustomerId = null;
  }
}

function saveLocalState() {
  localStorage.setItem(LOCAL_STATE_KEY, JSON.stringify(demoState));
}

function setRegisterPanelOpen(open) {
  if (!registerPanel) return;
  registerPanel.classList.toggle("hidden", !open);
}

function setChatModalOpen(open) {
  isChatModalOpen = open;
  if (!chatModal) return;
  chatModal.classList.toggle("hidden", !open);
  document.body.classList.toggle("chat-open", open);
}

function getPresenceSessionId() {
  let value = sessionStorage.getItem(PRESENCE_SESSION_KEY);
  if (!value) {
    value = `presence-${Math.random().toString(36).slice(2, 10)}`;
    sessionStorage.setItem(PRESENCE_SESSION_KEY, value);
  }
  return value;
}

function getPresenceViewerId() {
  if (!currentUser) return null;
  return `${currentUser.id}-${getPresenceSessionId()}`;
}

function applyLocalState(nextState) {
  demoState = {
    ...structuredClone(INITIAL_LOCAL_STATE),
    ...(nextState || {}),
    blockedUsers: (nextState || {}).blockedUsers || {},
  };
}

function loadLocalState() {
  const raw = localStorage.getItem(LOCAL_STATE_KEY);
  if (!raw) {
    applyLocalState(structuredClone(INITIAL_LOCAL_STATE));
    return;
  }
  try {
    applyLocalState(JSON.parse(raw));
  } catch (_error) {
    applyLocalState(structuredClone(INITIAL_LOCAL_STATE));
  }
}

function setDeviceStatus(message, muted = false) {
  deviceStatus.textContent = message;
  deviceStatus.classList.toggle("muted", muted);
}

function setStaffAction(message, muted = false) {
  staffActionResult.textContent = message;
  staffActionResult.classList.toggle("muted", muted);
}

function setCartMessage(message, muted = false) {
  cartResult.textContent = message;
  cartResult.classList.toggle("muted", muted);
}

function setProductManagerMessage(message, muted = false) {
  if (!productManagerResult) return;
  productManagerResult.textContent = message;
  productManagerResult.classList.toggle("muted", muted);
}

function applyRemotePreview(payload) {
  lastRemotePreviewPayload = payload;
  if (!remotePreviewFrame) return;
  if (!payload?.frame) {
    remotePreviewFrame.src = "";
    remotePreviewFrame.classList.add("hidden");
    return;
  }
  remotePreviewFrame.src = payload.frame;
  remotePreviewFrame.classList.toggle("hidden", currentUser?.role === "staff");
}

function stopPreviewBroadcast() {
  if (!previewBroadcastTimer) return;
  clearInterval(previewBroadcastTimer);
  previewBroadcastTimer = null;
}

function publishPreviewFrame(forceClear = false) {
  if (!selectedAccountId) return;
  if (
    forceClear ||
    !currentUser ||
    currentUser.role !== "staff" ||
    !mediaStream ||
    !cameraEnabled ||
    !hostLiveEnabled ||
    !livePreview.videoWidth ||
    !livePreview.videoHeight
  ) {
    previewChannel?.postMessage({ accountId: selectedAccountId, frame: null });
    localStorage.setItem("smartlive-demo-preview-frame", JSON.stringify({ accountId: selectedAccountId, frame: null, at: Date.now() }));
    return;
  }

  const canvas = document.createElement("canvas");
  canvas.width = livePreview.videoWidth;
  canvas.height = livePreview.videoHeight;
  const context = canvas.getContext("2d");
  if (!context) return;
  context.drawImage(livePreview, 0, 0, canvas.width, canvas.height);
  const frame = canvas.toDataURL("image/jpeg", 0.72);
  const payload = { accountId: selectedAccountId, frame, at: Date.now() };
  previewChannel?.postMessage(payload);
  localStorage.setItem("smartlive-demo-preview-frame", JSON.stringify(payload));
}

function startPreviewBroadcast() {
  stopPreviewBroadcast();
  previewBroadcastTimer = setInterval(() => publishPreviewFrame(false), 900);
}

function getAllCustomers() {
  return backendState.customers || [];
}

function getCurrentCustomer() {
  return currentUser?.role === "customer"
    ? getAllCustomers().find((customer) => customer.customer_id === currentUser.id) || null
    : null;
}

function getVisibleAccounts() {
  if (currentUser?.role === "customer") {
    return [...backendState.accounts].sort((left, right) => {
      const leftLive = left.broadcast_status === "live" ? 1 : 0;
      const rightLive = right.broadcast_status === "live" ? 1 : 0;
      if (leftLive !== rightLive) return rightLive - leftLive;
      const leftHeartbeat = left.last_heartbeat_at ? new Date(left.last_heartbeat_at).getTime() : 0;
      const rightHeartbeat = right.last_heartbeat_at ? new Date(right.last_heartbeat_at).getTime() : 0;
      return rightHeartbeat - leftHeartbeat;
    });
  }
  if (currentUser?.role !== "staff") {
    return backendState.accounts;
  }
  const ownedAccounts = backendState.accounts.filter((account) => account.owner_user_id === currentUser.id);
  return ownedAccounts.length ? ownedAccounts : backendState.accounts;
}

function ensureSelectedAccount() {
  const visibleAccounts = getVisibleAccounts();
  if (!visibleAccounts.length) {
    selectedAccountId = null;
    return null;
  }
  if (selectedAccountId && !visibleAccounts.some((account) => account.account_id === selectedAccountId)) {
    selectedAccountId = null;
  }
  if (!selectedAccountId && currentUser?.role !== "customer") {
    selectedAccountId = visibleAccounts[0].account_id;
  }
  return visibleAccounts.find((account) => account.account_id === selectedAccountId) || null;
}

function getSelectedAccount() {
  return ensureSelectedAccount();
}

function getAssignedProducts(accountId) {
  const assignedProductIds = new Set(
    backendState.assignments
      .filter((assignment) => assignment.account_id === accountId)
      .map((assignment) => assignment.product_id),
  );
  return backendState.products.filter((product) => assignedProductIds.has(product.product_id));
}

function getLiveOffer(accountId) {
  return (backendState.liveOffers || []).find((offer) => offer.account_id === accountId) || null;
}

function getEffectivePrice(accountId, productId) {
  const offer = getLiveOffer(accountId);
  const product = backendState.products.find((item) => item.product_id === productId);
  if (!product) return 0;
  if (offer && offer.product_id === productId) {
    return offer.live_price;
  }
  return product.retail_price;
}

function getConversationCustomerIds() {
  if (currentUser?.role === "customer") {
    return currentUser ? [currentUser.id] : [];
  }
  if (currentUser?.role === "staff") {
    return [...new Set((backendState.messages || []).map((message) => message.customer_id))];
  }
  return [];
}

function buildBlockKey(accountId, customerId) {
  return `${accountId}::${customerId}`;
}

function isBlocked(accountId, customerId) {
  return Boolean(demoState.blockedUsers[buildBlockKey(accountId, customerId)]);
}

function analyzeBuyingIntent(text) {
  const normalized = normalizeText(text);
  const buyingKeywords = ["muon chot", "chot", "mua", "lay 2", "lay luon", "dat", "inbox", "chot don"];
  const priceKeywords = ["gia", "bao nhieu", "freeship", "ship", "uu dai"];
  const consultKeywords = ["da nhay cam", "tu van", "phu hop", "mui huong", "thanh phan"];
  if (buyingKeywords.some((keyword) => normalized.includes(keyword))) return "buying_intent";
  if (priceKeywords.some((keyword) => normalized.includes(keyword))) return "ask_price";
  if (consultKeywords.some((keyword) => normalized.includes(keyword))) return "consult_request";
  return "other";
}

function getVisibleComments() {
  return (backendState.comments || [])
    .filter((comment) => comment.account_id === selectedAccountId)
    .filter((comment) => !isBlocked(comment.account_id, comment.customer_id))
    .sort((left, right) => new Date(right.created_at) - new Date(left.created_at));
}

async function loadBackendData() {
  const [accounts, products, assignments, liveOffers, customers] = await Promise.all([
    fetchJson("/api/v1/livestream-accounts"),
    fetchJson("/api/v1/products"),
    fetchJson("/api/v1/livestream-product-assignments"),
    fetchJson("/api/v1/livestream-product-offers"),
    fetchJson("/api/v1/customers"),
  ]);

  backendState.accounts = accounts;
  backendState.products = products;
  backendState.assignments = assignments;
  backendState.liveOffers = liveOffers;
  backendState.customers = customers;

  if (currentUser?.role === "customer") {
    backendState.cartItems = await fetchJson(`/api/v1/customers/${currentUser.id}/cart`);
    backendState.orders = await fetchJson(`/api/v1/customers/${currentUser.id}/orders`);
  } else {
    backendState.cartItems = [];
    backendState.orders = [];
  }

  ensureSelectedAccount();
  const customerIds = getConversationCustomerIds();
  if (customerIds.length && !customerIds.includes(selectedConversationCustomerId)) {
    selectedConversationCustomerId = customerIds[0];
  }

  if (selectedAccountId) {
    backendState.comments = await fetchJson(`/api/v1/livestream-accounts/${selectedAccountId}/comments`);
    const messagePath = currentUser?.role === "customer"
      ? `/api/v1/livestream-accounts/${selectedAccountId}/messages?customer_id=${currentUser.id}`
      : `/api/v1/livestream-accounts/${selectedAccountId}/messages`;
    backendState.messages = await fetchJson(messagePath);
  } else {
    backendState.comments = [];
    backendState.messages = [];
  }

  const nextConversationCustomerIds = getConversationCustomerIds();
  if (nextConversationCustomerIds.length && !nextConversationCustomerIds.includes(selectedConversationCustomerId)) {
    selectedConversationCustomerId = nextConversationCustomerIds[0];
  }
  saveSession();
}

async function refreshDataAndRender() {
  await loadBackendData();
  await syncCurrentPresence();
  renderLayout();
}

function applyPresenceStateToAccounts(state) {
  backendState.accounts = (backendState.accounts || []).map((account) =>
    account.account_id === state.account_id
      ? {
          ...account,
          current_viewers: state.current_viewers,
          broadcast_status: state.broadcast_status,
          live_started_at: state.live_started_at,
          last_heartbeat_at: state.last_heartbeat_at,
        }
      : account
  );
}

async function syncCurrentPresence() {
  if (!currentUser || !selectedAccountId) return;
  const state = await fetchJson(`/api/v1/livestream-accounts/${selectedAccountId}/presence/heartbeat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      viewer_id: getPresenceViewerId(),
      viewer_role: currentUser.role,
      viewer_name: currentUser.name,
      is_host: currentUser.role === "staff",
      is_live: currentUser.role === "staff" ? hostLiveEnabled : false,
    }),
  });
  currentPresenceAccountId = selectedAccountId;
  applyPresenceStateToAccounts(state);
}

async function leaveCurrentPresence() {
  const viewerId = getPresenceViewerId();
  if (!currentPresenceAccountId || !viewerId) return;
  try {
    await fetchJson(`/api/v1/livestream-accounts/${currentPresenceAccountId}/presence/${encodeURIComponent(viewerId)}`, {
      method: "DELETE",
    });
  } catch (_error) {
    // Presence will expire on the next active refresh cycle if this delete fails.
  } finally {
    currentPresenceAccountId = null;
  }
}

function stopRealtimeRefresh() {
  if (!realtimeRefreshTimer) return;
  clearInterval(realtimeRefreshTimer);
  realtimeRefreshTimer = null;
}

function startRealtimeRefresh() {
  stopRealtimeRefresh();
  if (!currentUser) return;
  realtimeRefreshTimer = setInterval(async () => {
    if (!currentUser || realtimeRefreshInFlight) return;
    try {
      realtimeRefreshInFlight = true;
      await refreshDataAndRender();
    } catch (_error) {
      // Keep the current UI and retry on the next interval.
    } finally {
      realtimeRefreshInFlight = false;
    }
  }, REALTIME_REFRESH_MS);
}

function renderLiveSummary() {
  const account = getSelectedAccount();
  if (!account) {
    topbarTitle.textContent = "Chưa có phòng live";
    liveRoomTitle.textContent = "Chưa có phòng live";
    sessionCard.innerHTML = '<p class="muted">Hệ thống chưa có phòng live nào trong database.</p>';
    pinnedProductCard.innerHTML = '<p class="muted">Chưa có sản phẩm ghim cho phiên live này.</p>';
    metricLiveStatus.textContent = "Trong";
    metricViewers.textContent = "0";
    metricComments.textContent = "0";
    metricBlocked.textContent = "0";
    if (currentUser?.role === "customer") {
      topbarTitle.textContent = "Chọn phòng live";
      liveRoomTitle.textContent = "Chọn phòng live để bắt đầu xem";
      sessionCard.innerHTML = '<p class="muted">Hãy chọn một phòng live ở thanh phía trên để xem camera, sản phẩm ghim và bình luận theo thời gian thực.</p>';
      pinnedProductCard.innerHTML = '<p class="muted">Chưa có sản phẩm ghim vì bạn chưa chọn phòng live.</p>';
      metricLiveStatus.textContent = "Chưa chọn";
      liveStatusPill.textContent = "Chưa chọn";
      liveStatusPill.className = "status-pill offline";
      remotePreviewFrame?.classList.add("hidden");
      videoOverlay.classList.remove("hidden");
      videoOverlayText.textContent = "Chọn phòng live ở phía trên để xem phiên đang phát và sản phẩm đang ghim.";
    }
    return;
  }

  const liveOffer = getLiveOffer(account.account_id);
  const pinnedProduct = liveOffer
    ? backendState.products.find((item) => item.product_id === liveOffer.product_id)
    : null;
  const visibleComments = getVisibleComments();
  const blockedCount = getAllCustomers().filter((customer) => isBlocked(account.account_id, customer.customer_id)).length;

  topbarTitle.textContent = account.name;
  liveRoomTitle.textContent = account.name;
  sessionCard.innerHTML = `
    <strong>${escapeHtml(account.name)}</strong>
    <div>Kenh: ${escapeHtml(account.platform_display_name)}</div>
    <div>Chu room: ${escapeHtml(account.owner_name)}</div>
    <div>Tai khoan live: ${escapeHtml(account.username)}</div>
    <div>Ca live: ${escapeHtml(account.shift_label)}</div>
    <div>Kho: ${escapeHtml(account.warehouse_location)}</div>
  `;

  if (pinnedProduct && liveOffer) {
    pinnedProductCard.innerHTML = `
      <p class="eyebrow">San pham dang ghim</p>
      <h4>${escapeHtml(pinnedProduct.name)}</h4>
      <p>${escapeHtml(pinnedProduct.description)}</p>
      <div class="product-meta">
        <span class="badge">Giá gốc ${escapeHtml(formatCurrency(liveOffer.original_price))}</span>
        <span class="badge live-badge">Gia live ${escapeHtml(formatCurrency(liveOffer.live_price))}</span>
        <span class="badge">Tồn ${escapeHtml(pinnedProduct.stock_quantity)}</span>
      </div>
      ${currentUser?.role === "customer" ? `<button type="button" class="primary-btn add-to-cart-btn" data-product-id="${pinnedProduct.product_id}">Thêm vào giỏ hàng</button>` : ""}
    `;
  } else {
    pinnedProductCard.innerHTML = '<p class="muted">Chưa có sản phẩm ghim cho phiên live này.</p>';
  }

  metricLiveStatus.textContent = account.broadcast_status === "live" ? "Đang live" : "Chưa live";
  metricViewers.textContent = String(account.current_viewers);
  metricComments.textContent = String(visibleComments.length);
  metricBlocked.textContent = String(blockedCount);
  liveStatusPill.textContent = account.broadcast_status === "live" ? "Đang live" : "Offline";
  liveStatusPill.className = `status-pill ${account.broadcast_status === "live" ? "live" : "offline"}`;
  const shouldShowRemotePreview = currentUser?.role === "customer"
    && lastRemotePreviewPayload?.accountId === account.account_id
    && Boolean(lastRemotePreviewPayload?.frame);
  remotePreviewFrame?.classList.toggle("hidden", !shouldShowRemotePreview);
  if (shouldShowRemotePreview && remotePreviewFrame) {
    remotePreviewFrame.src = lastRemotePreviewPayload.frame;
  }

  if (mediaStream && cameraEnabled && currentUser?.role === "staff") {
    videoOverlay.classList.add("hidden");
  } else if (shouldShowRemotePreview) {
    videoOverlay.classList.add("hidden");
  } else {
    videoOverlay.classList.remove("hidden");
    if (currentUser?.role === "staff") {
      videoOverlayText.textContent = mediaStream
        ? "Camera đang tắt. Bạn có thể bật lại camera để tiếp tục demo."
        : "Nhân viên bán hàng có thể cấp quyền camera và micro để bắt đầu demo.";
    } else {
      videoOverlayText.textContent = "Khách hàng đang xem phòng live được đồng bộ từ backend và có thể mua hàng bằng giỏ hàng thật.";
    }
  }

  if (currentUser?.role === "staff") {
    topbarSubtitle.textContent = "Nhân viên bán hàng đang đọc phòng live và sản phẩm được cấp từ database.";
    liveRoomDescription.textContent = "Giá live chỉ có hiệu lực sau khi nhân viên bán hàng ghim sản phẩm cho phòng live này.";
  } else {
    const customer = getCurrentCustomer();
    topbarSubtitle.textContent = "Khách hàng đang xem sản phẩm từ phòng live thật và mua hàng qua giỏ hàng được đồng bộ database.";
    liveRoomDescription.textContent = `Địa chỉ giao hàng hiện tại: ${customer?.shipping_address || currentUser?.shipping_address || "Chưa cập nhật"}.`;
  }
}

function renderProductSelectors() {
  const account = getSelectedAccount();
  const products = account ? getAssignedProducts(account.account_id) : [];
  if (!products.length || !account) {
    commentProductSelect.innerHTML = '<option value="">Chưa có sản phẩm nào trong phòng live này</option>';
    commentProductSelect.disabled = true;
    return;
  }
  commentProductSelect.disabled = false;
  commentProductSelect.innerHTML = products.map((product) => `
    <option value="${product.product_id}">${escapeHtml(product.name)} - ${escapeHtml(formatCurrency(getEffectivePrice(account.account_id, product.product_id)))}</option>
  `).join("");
}

function renderStaffProductList() {
  if (currentUser?.role !== "staff") {
    staffProductList.innerHTML = "";
    return;
  }

  const account = getSelectedAccount();
  if (!account) {
    staffProductList.innerHTML = '<div class="message-box muted">Chưa có phòng live nao de thao tac.</div>';
    return;
  }

  const liveOffer = getLiveOffer(account.account_id);
  const products = getAssignedProducts(account.account_id);
  if (!products.length) {
    staffProductList.innerHTML = '<div class="message-box muted">Chưa có sản phẩm nào được gán cho phòng live này trong database.</div>';
    return;
  }

  staffProductList.innerHTML = products.map((product) => {
    const suggestedPrice = liveOffer?.product_id === product.product_id
      ? liveOffer.live_price
      : Math.max(1000, Math.round(product.retail_price * 0.9));
    return `
      <article class="product-card ${liveOffer?.product_id === product.product_id ? "is-pinned" : ""}">
        <div class="product-card-head">
          <div>
            <h4>${escapeHtml(product.name)}</h4>
            <p>${escapeHtml(product.description)}</p>
          </div>
          ${liveOffer?.product_id === product.product_id ? '<span class="badge live-badge">Đang ghim</span>' : ""}
        </div>
        <div class="product-meta">
          <span class="badge">${escapeHtml(product.category)}</span>
          <span class="badge">Giá gốc ${escapeHtml(formatCurrency(product.retail_price))}</span>
          <span class="badge">Tồn ${escapeHtml(product.stock_quantity)}</span>
        </div>
        <label>Giá live trước khi ghim
          <input type="number" class="live-price-input" min="1000" max="${product.retail_price}" step="1000" value="${suggestedPrice}" />
        </label>
        <button type="button" class="ghost-btn pin-product-btn" data-product-id="${product.product_id}">${liveOffer?.product_id === product.product_id ? "Cập nhật giá live" : "Ghim lên live"}</button>
      </article>
    `;
  }).join("");
}

function renderCustomerRoomPicker(query = "") {
  if (!customerRoomToolbar || !customerRoomList) return;
  const isCustomer = currentUser?.role === "customer";
  customerRoomToolbar.classList.toggle("hidden", !isCustomer);
  if (!isCustomer) {
    customerRoomList.innerHTML = "";
    return;
  }

  const normalized = normalizeText(query);
  const accounts = getVisibleAccounts().filter((account) => normalizeText(
    `${account.name} ${account.platform_display_name} ${account.owner_name} ${account.shift_label} ${account.warehouse_location}`
  ).includes(normalized)).slice(0, 6);

  if (!accounts.length) {
    customerRoomList.innerHTML = '<div class="message-box muted">Không tìm thấy phòng live phù hợp với từ khóa này.</div>';
    return;
  }

  customerRoomList.innerHTML = accounts.map((account) => {
    const liveOffer = getLiveOffer(account.account_id);
    const pinnedProduct = liveOffer
      ? backendState.products.find((item) => item.product_id === liveOffer.product_id)
      : null;
    return `
      <button type="button" class="room-pill ${selectedAccountId === account.account_id ? "active" : ""} select-live-btn" data-account-id="${account.account_id}">
        <strong>${escapeHtml(account.name)}</strong>
        <span>${escapeHtml(account.platform_display_name)} • ${escapeHtml(account.owner_name)}</span>
        <small>${escapeHtml(account.broadcast_status === "live" ? "Đang live" : "Chưa live")} • ${escapeHtml(String(account.current_viewers))} viewer${pinnedProduct ? ` • ${escapeHtml(pinnedProduct.name)}` : ""}</small>
      </button>
    `;
  }).join("");
}

function searchContent(query) {
  const normalized = normalizeText(query);
  const assignedProductIds = new Set(backendState.assignments.map((assignment) => assignment.product_id));
  if (!normalized) {
    return {
      liveMatches: getVisibleAccounts().slice(0, 3),
      productMatches: selectedAccountId ? getAssignedProducts(selectedAccountId).slice(0, 8) : [],
    };
  }

  const liveMatches = getVisibleAccounts().filter((account) => normalizeText(
    `${account.name} ${account.platform_display_name} ${account.owner_name} ${account.shift_label} ${account.warehouse_location}`
  ).includes(normalized));

  const productMatches = backendState.products.filter((product) =>
    assignedProductIds.has(product.product_id) &&
    normalizeText(`${product.name} ${product.description} ${product.category} ${product.brand} ${product.sku}`).includes(normalized)
  );

  return { liveMatches, productMatches };
}

function buildRecommendations() {
  const account = getSelectedAccount();
  if (!account) {
    return { products: [], accounts: [] };
  }

  const products = getAssignedProducts(account.account_id).slice(0, 8);
  const otherAccounts = getVisibleAccounts().filter((item) => item.account_id !== account.account_id).slice(0, 4);
  return { products, accounts: otherAccounts };
}

function renderCustomerSearchAndRecommendations(query = "") {
  if (currentUser?.role !== "customer") {
    searchList.innerHTML = "";
    recommendationList.innerHTML = "";
    return;
  }

  const { liveMatches, productMatches } = searchContent(query);
  searchResult.classList.remove("muted");
  searchResult.textContent = query
    ? `Tìm thấy ${liveMatches.length} phòng live và ${productMatches.length} sản phẩm liên quan trong database.`
    : "Đang hiển thị phòng live và sản phẩm được cấp từ backend để bạn thao tác nhanh.";

  searchList.innerHTML = `
    ${liveMatches.map((account) => `
      <article class="search-card">
        <div>
          <p class="eyebrow">Phong live</p>
          <h4>${escapeHtml(account.name)}</h4>
          <p>${escapeHtml(account.platform_display_name)} - ${escapeHtml(account.owner_name)}</p>
          <div class="product-meta">
            <span class="badge ${account.broadcast_status === "live" ? "live-badge" : ""}">${escapeHtml(account.broadcast_status === "live" ? "Đang live" : "Chưa live")}</span>
            <span class="badge">${escapeHtml(account.shift_label)}</span>
            <span class="badge">${escapeHtml(account.warehouse_location)}</span>
          </div>
        </div>
        <button type="button" class="primary-btn select-live-btn" data-account-id="${account.account_id}">Xem phong nay</button>
      </article>
    `).join("")}
    ${productMatches.map((product) => `
      <article class="search-card">
        <div>
          <p class="eyebrow">San pham</p>
          <h4>${escapeHtml(product.name)}</h4>
          <p>${escapeHtml(product.description)}</p>
          <div class="product-meta">
            <span class="badge">${escapeHtml(product.category)}</span>
            <span class="badge">${escapeHtml(formatCurrency(product.retail_price))}</span>
            <span class="badge">Tồn ${escapeHtml(product.stock_quantity)}</span>
          </div>
        </div>
        <div class="inline-actions">
          <button type="button" class="ghost-btn focus-product-btn" data-product-id="${product.product_id}">Chọn sản phẩm</button>
          <button type="button" class="primary-btn add-to-cart-btn" data-product-id="${product.product_id}">Them vao gio</button>
        </div>
      </article>
    `).join("")}
  `;

  const recommendations = buildRecommendations();
  recommendationList.innerHTML = `
    ${recommendations.products.map((product) => `
      <article class="recommendation-card">
        <p class="eyebrow">Đề xuất sản phẩm</p>
        <h4>${escapeHtml(product.name)}</h4>
        <p>${escapeHtml(product.description)}</p>
        <div class="product-meta">
          <span class="badge">${escapeHtml(formatCurrency(getEffectivePrice(selectedAccountId, product.product_id)))}</span>
          <span class="badge">Tồn ${escapeHtml(product.stock_quantity)}</span>
        </div>
        <button type="button" class="primary-btn add-to-cart-btn" data-product-id="${product.product_id}">Them vao gio</button>
      </article>
    `).join("")}
    ${recommendations.accounts.map((account) => `
      <article class="recommendation-card">
        <p class="eyebrow">Phong live lien quan</p>
        <h4>${escapeHtml(account.name)}</h4>
        <p>${escapeHtml(account.platform_display_name)} - ${escapeHtml(account.owner_name)}</p>
        <div class="product-meta">
          <span class="badge ${account.broadcast_status === "live" ? "live-badge" : ""}">${escapeHtml(account.broadcast_status === "live" ? "Đang live" : "Chưa live")}</span>
        </div>
        <button type="button" class="ghost-btn select-live-btn" data-account-id="${account.account_id}">Chuyen sang phong nay</button>
      </article>
    `).join("")}
  `;
}

function renderCustomerCart() {
  if (currentUser?.role !== "customer") {
    customerCartList.innerHTML = "";
    return;
  }

  if (!backendState.cartItems.length) {
    customerCartList.innerHTML = '<div class="message-box muted">Giỏ hàng đang trống. Bạn có thể thêm sản phẩm từ phòng live được đồng bộ từ backend.</div>';
    checkoutBtn.disabled = true;
    clearCartBtn.disabled = true;
    return;
  }

  checkoutBtn.disabled = false;
  clearCartBtn.disabled = false;
  customerCartList.innerHTML = backendState.cartItems.map((item) => `
    <article class="product-card">
      <div class="product-card-head">
        <div>
          <h4>${escapeHtml(item.product_name)}</h4>
          <p>${escapeHtml(item.account_name)} - ${escapeHtml(item.platform_display_name)}</p>
        </div>
        <span class="badge">SL ${escapeHtml(item.quantity)}</span>
      </div>
      <div class="product-meta">
        <span class="badge">Giá gốc ${escapeHtml(formatCurrency(item.original_price))}</span>
        <span class="badge live-badge">Gia live ${escapeHtml(formatCurrency(item.unit_price))}</span>
        <span class="badge">Tam tinh ${escapeHtml(formatCurrency(item.line_total))}</span>
      </div>
      <div class="inline-actions">
        <button type="button" class="ghost-btn remove-cart-btn" data-cart-item-id="${item.cart_item_id}">Xoa khoi gio</button>
      </div>
    </article>
  `).join("");

  const total = backendState.cartItems.reduce((sum, item) => sum + item.line_total, 0);
  setCartMessage(`Giỏ hàng hiện có ${backendState.cartItems.length} dòng sản phẩm, tổng tạm tính ${formatCurrency(total)}.`, false);
}

function renderComments() {
  if (!selectedAccountId) {
    commentList.innerHTML = '<div class="message-box muted">Chọn phòng live để xem và gửi bình luận theo đúng phiên.</div>';
    return;
  }
  const comments = getVisibleComments();
  if (!comments.length) {
    commentList.innerHTML = '<div class="message-box muted">Chưa có bình luận nào trong phòng live này.</div>';
    return;
  }
  commentList.innerHTML = comments.map((comment) => {
    const isStaff = currentUser?.role === "staff";
    return `
      <article class="comment-card">
        <div class="comment-header">
          <div>
            <h4>${escapeHtml(comment.customer_name || "Khách hàng")}</h4>
            <p>${escapeHtml(comment.content)}</p>
          </div>
          <span class="badge">${escapeHtml(formatDateTime(comment.created_at))}</span>
        </div>
        <div class="comment-meta">
          <span class="badge">${escapeHtml(comment.product_name || "Sản phẩm")}</span>
          <span class="badge">${escapeHtml(comment.intent)}</span>
          <span class="badge">${escapeHtml(comment.customer_phone || "Online")}</span>
        </div>
        ${isStaff ? `
          <div class="comment-actions">
            <button type="button" class="ghost-btn quick-message-btn" data-user-id="${comment.customer_id}">Mo nhan tin</button>
            <button type="button" class="ghost-btn viewer-block-btn" data-account-id="${comment.account_id}" data-user-id="${comment.customer_id}">
              ${isBlocked(comment.account_id, comment.customer_id) ? "Bỏ chặn" : "Chặn khách"}
            </button>
          </div>
        ` : ""}
      </article>
    `;
  }).join("");
}

function renderConversations() {
  const customerIds = getConversationCustomerIds();
  if (!customerIds.length) {
    conversationList.innerHTML = '<div class="message-box muted">Vai trò hiện tại không dùng hội thoại này.</div>';
    threadHeader.innerHTML = "";
    messageThread.innerHTML = '<div class="message-box muted">Chưa có hội thoại nào.</div>';
    return;
  }

  if (!customerIds.includes(selectedConversationCustomerId)) {
    selectedConversationCustomerId = customerIds[0];
  }

  conversationList.innerHTML = customerIds.map((customerId) => {
    const customer = getAllCustomers().find((item) => item.customer_id === customerId);
    const thread = (backendState.messages || []).filter((message) => message.customer_id === customerId);
    const lastMessage = [...thread].sort((left, right) => new Date(right.created_at) - new Date(left.created_at))[0];
    return `
      <button type="button" class="conversation-item ${customerId === selectedConversationCustomerId ? "active" : ""}" data-customer-id="${customerId}">
        <strong>${escapeHtml(customer?.full_name || "Khách hàng")}</strong>
        <span>${escapeHtml(lastMessage?.content || "Chưa có tin nhắn")}</span>
        <small>${escapeHtml(customer?.phone || customer?.shipping_address || "Online")}</small>
      </button>
    `;
  }).join("");

  const selectedCustomer = getAllCustomers().find((item) => item.customer_id === selectedConversationCustomerId);
  const thread = (backendState.messages || [])
    .filter((message) => message.customer_id === selectedConversationCustomerId)
    .slice()
    .sort((left, right) => new Date(left.created_at) - new Date(right.created_at));
  const account = getSelectedAccount();
  const autoMessaged = thread.some((message) => message.source === "ai");

  threadHeader.innerHTML = `
    <div>
      <strong>${escapeHtml(selectedCustomer?.full_name || "Khách hàng")}</strong>
      <span>${escapeHtml(selectedCustomer?.shipping_address || "")}</span>
    </div>
    <div class="thread-badges">
      ${account ? `<span class="badge">${escapeHtml(account.name)}</span>` : ""}
      ${selectedCustomer?.phone ? `<span class="badge">${escapeHtml(selectedCustomer.phone)}</span>` : ""}
      ${autoMessaged ? '<span class="badge live-badge">AI đã mở đầu hội thoại</span>' : ""}
    </div>
  `;

  messageThread.innerHTML = thread.length ? thread.map((message) => `
    <article class="message-bubble ${message.sender_role === "customer" ? "inbound" : "outbound"}">
      <div class="message-meta">
        <strong>${escapeHtml(message.sender_name)}</strong>
        <span>${escapeHtml(formatDateTime(message.created_at))}</span>
      </div>
      <p>${escapeHtml(message.content)}</p>
      <small>${escapeHtml(message.source === "ai" ? "Tin nhắn mở đầu bởi AI" : "Tin nhắn thủ công")}</small>
    </article>
  `).join("") : '<div class="message-box muted">Chưa có tin nhắn nao trong hoi thoai nay.</div>';
}

function renderLayout() {
  const loggedIn = Boolean(currentUser);
  loginScreen.classList.toggle("hidden", loggedIn);
  appScreen.classList.toggle("hidden", !loggedIn);

  if (!loggedIn) {
    setChatModalOpen(false);
    return;
  }

  currentUserName.textContent = currentUser.name;
  currentUserRole.textContent = currentUser.role === "staff"
    ? "Nhân viên bán hàng"
    : "Khách hàng";

  staffView.classList.toggle("hidden", currentUser.role !== "staff");
  customerView.classList.toggle("hidden", currentUser.role !== "customer");
  commentPanel?.classList.remove("hidden");
  messagePanel?.classList.remove("hidden");
  customerRoomToolbar?.classList.toggle("hidden", currentUser.role !== "customer");
  commentForm.classList.toggle("hidden", currentUser.role !== "customer");

  renderLiveSummary();
  renderCustomerRoomPicker(customerRoomSearchInput?.value?.trim() || "");
  renderProductSelectors();
  renderStaffProductList();
  renderCustomerSearchAndRecommendations(searchInput.value.trim());
  renderCustomerCart();
  renderComments();
  renderConversations();

  toggleCameraBtn.textContent = cameraEnabled ? "Tat camera" : "Bat camera";
  toggleMicBtn.textContent = micEnabled ? "Tat micro" : "Bat micro";

  const blocked = currentUser.role === "customer" && selectedAccountId && isBlocked(selectedAccountId, currentUser.id);
  commentInput.disabled = Boolean(blocked);
  commentProductSelect.disabled = Boolean(blocked) || currentUser.role !== "customer" || !selectedAccountId || !commentProductSelect.value;
  commentForm.querySelector("button[type='submit']").disabled = Boolean(blocked) || currentUser.role !== "customer" || !selectedAccountId || !commentProductSelect.value;
}

async function connectMediaDevices() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setDeviceStatus("Trinh duyet hien tai khong ho tro truy cap camera va micro.", false);
    setStaffAction("Không thể demo camera và micro trên trình duyệt này.", false);
    return;
  }

  try {
    stopMediaStream();
    mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    livePreview.srcObject = mediaStream;
    startPreviewBroadcast();
    cameraEnabled = true;
    micEnabled = true;
    setDeviceStatus("Da cap quyen camera va micro thanh cong.", false);
    setStaffAction("Preview đã sẵn sàng. Bạn có thể tiếp tục demo.", false);
    renderLayout();
  } catch (_error) {
    setDeviceStatus("Không mở được camera hoặc micro. Hãy kiểm tra quyền truy cập của trình duyệt.", false);
    setStaffAction("Thiết bị chưa sẵn sàng để demo live.", false);
  }
}

function stopMediaStream() {
  if (!mediaStream) return;
  mediaStream.getTracks().forEach((track) => track.stop());
  mediaStream = null;
  livePreview.srcObject = null;
  stopPreviewBroadcast();
  publishPreviewFrame(true);
}

function toggleTrack(kind) {
  if (!mediaStream) {
    setStaffAction("Cần cấp quyền camera và micro trước khi điều khiển thiết bị.", false);
    return;
  }

  const tracks = kind === "video" ? mediaStream.getVideoTracks() : mediaStream.getAudioTracks();
  if (!tracks.length) {
    setStaffAction(`Không tìm thấy ${kind === "video" ? "camera" : "micro"} tren may nay.`, false);
    return;
  }

  const nextEnabled = !tracks[0].enabled;
  tracks.forEach((track) => {
    track.enabled = nextEnabled;
  });

  if (kind === "video") {
    cameraEnabled = nextEnabled;
    publishPreviewFrame(!nextEnabled);
    setStaffAction(nextEnabled ? "Đã bật lại camera." : "Đã tắt camera.", false);
  } else {
    micEnabled = nextEnabled;
    setStaffAction(nextEnabled ? "Đã bật lại micro." : "Đã tắt micro.", false);
  }
  renderLayout();
}

async function handleLogin(event) {
  event.preventDefault();
  loginResult.classList.remove("muted");
  loginResult.textContent = "Đang xác thực tài khoản với backend...";
  try {
    const data = await fetchJson("/api/v1/demo/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier: loginEmail.value.trim(),
        password: loginPassword.value,
      }),
    });
    if (data.user.role !== "staff" && data.user.role !== "customer") {
      currentUser = null;
      loginResult.textContent = "App demo chỉ cho phép đăng nhập bằng tài khoản nhân viên bán hàng hoặc khách hàng.";
      return;
    }
    currentUser = data.user;
    setRegisterPanelOpen(false);
    await refreshDataAndRender();
    loginResult.textContent = `Đăng nhập thành công với vai trò ${currentUser.role}.`;
  } catch (error) {
    loginResult.textContent = error.message;
  }
}

async function handleRegister(event) {
  event.preventDefault();
  registerResult.classList.remove("muted");
  registerResult.textContent = "Đang tạo tài khoản khách hàng trong database...";
  try {
    const customer = await fetchJson("/api/v1/customers/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        phone: registerPhone.value.trim(),
        email: registerEmail.value.trim(),
        password: registerPassword.value,
        full_name: registerFullName.value.trim(),
        shipping_address: registerLocation.value.trim(),
        birth_year: Number(registerBirthYear.value),
      }),
    });
    registerResult.textContent = `Đã tạo tài khoản cho ${customer.full_name}. Dữ liệu đã được đồng bộ vào database.`;
    loginEmail.value = customer.phone;
    loginPassword.value = registerPassword.value;
    registerForm.reset();
    const data = await fetchJson("/api/v1/demo/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier: customer.phone,
        password: loginPassword.value,
      }),
    });
    if (data.user.role !== "customer") {
      throw new Error("Tài khoản vừa tạo chưa được nhận diện là khách hàng.");
    }
    currentUser = data.user;
    setRegisterPanelOpen(false);
    await refreshDataAndRender();
  } catch (error) {
    registerResult.textContent = error.message;
  }
}

async function handleProductCreate(event) {
  event.preventDefault();
  setProductManagerMessage("Đang tạo sản phẩm mới trong catalog service...", false);
  try {
    const name = productNameInput.value.trim();
    const category = productCategoryInput.value.trim();
    const retailPrice = Number(productPriceInput.value);
    const stockQuantity = Number(productStockInput.value);
    const description = productHighlightInput.value.trim();
    const skuCore = normalizeText(name).replace(/[^a-z0-9]+/g, "-").toUpperCase().replace(/^-|-$/g, "").slice(0, 10) || "DEMO";
    const payload = {
      sku: `DM-${skuCore}-${String(Date.now()).slice(-4)}`,
      name,
      category,
      brand: "SmartLive Demo",
      cost_price: Math.max(1000, Math.round(retailPrice * 0.7)),
      retail_price: retailPrice,
      stock_quantity: stockQuantity,
      reorder_level: Math.max(1, Math.floor(stockQuantity * 0.2)),
      unit: "pcs",
      description,
      is_active: true,
    };
    await fetchJson("/api/v1/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    productForm.reset();
    await refreshDataAndRender();
    setProductManagerMessage("Đã thêm sản phẩm mới và đồng bộ vào database.", false);
  } catch (error) {
    setProductManagerMessage(error.message, false);
  }
}

async function handleAssignmentCreate(event) {
  event.preventDefault();
  setProductManagerMessage("Đang gán sản phẩm vào phòng live...", false);
  try {
    await fetchJson("/api/v1/livestream-product-assignments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        account_id: assignmentLiveSelect.value,
        product_id: assignmentProductSelect.value,
        assigned_by_user_id: currentUser.id,
      }),
    });
    await refreshDataAndRender();
    setProductManagerMessage("Đã gán sản phẩm vào phòng live và đồng bộ vào database.", false);
  } catch (error) {
    setProductManagerMessage(error.message, false);
  }
}

async function restockProduct(productId, quantity) {
  const product = backendState.products.find((item) => item.product_id === productId);
  if (!product) return;
  await fetchJson(`/api/v1/products/${productId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sku: product.sku,
      name: product.name,
      category: product.category,
      brand: product.brand,
      cost_price: product.cost_price,
      retail_price: product.retail_price,
      stock_quantity: product.stock_quantity + quantity,
      reorder_level: product.reorder_level,
      unit: product.unit,
      description: product.description,
      is_active: product.is_active,
    }),
  });
}

async function pinProductForLive(productId, livePrice) {
  await fetchJson("/api/v1/livestream-product-offers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      account_id: selectedAccountId,
      product_id: productId,
      live_price: livePrice,
      pinned_by_user_id: currentUser.id,
    }),
  });
}

async function addToCart(productId) {
  if (currentUser?.role !== "customer") return;
  const hasSelectedAssignment = backendState.assignments.some((assignment) =>
    assignment.account_id === selectedAccountId && assignment.product_id === productId
  );
  if (!hasSelectedAssignment) {
    const fallbackAssignment = backendState.assignments.find((assignment) => assignment.product_id === productId);
    if (fallbackAssignment) {
      selectedAccountId = fallbackAssignment.account_id;
    }
  }
  await fetchJson(`/api/v1/customers/${currentUser.id}/cart/items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      account_id: selectedAccountId,
      product_id: productId,
      quantity: 1,
    }),
  });
  await refreshDataAndRender();
  setCartMessage("Đã thêm sản phẩm vào giỏ hàng và đồng bộ lên database.", false);
}

async function removeCartItem(cartItemId) {
  if (currentUser?.role !== "customer") return;
  await fetchJson(`/api/v1/customers/${currentUser.id}/cart/items/${cartItemId}`, {
    method: "DELETE",
  });
  await refreshDataAndRender();
  setCartMessage("Đã xóa sản phẩm khỏi giỏ hàng trong database.", false);
}

async function clearCustomerCart() {
  if (currentUser?.role !== "customer") return;
  await fetchJson(`/api/v1/customers/${currentUser.id}/cart`, { method: "DELETE" });
  await refreshDataAndRender();
  setCartMessage("Đã xóa toàn bộ giỏ hàng trong database.", false);
}

async function checkoutCustomerCart() {
  if (currentUser?.role !== "customer") return;
  const data = await fetchJson(`/api/v1/customers/${currentUser.id}/checkout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  await refreshDataAndRender();
  const orderSummary = data.orders.map((order) => `${order.account_name}: ${formatCurrency(order.total_amount)}`).join(", ");
  setCartMessage(`Checkout thành công. ${orderSummary}`, false);
}

async function handleCommentSubmit(event) {
  event.preventDefault();
  if (!currentUser || currentUser.role !== "customer") return;
  if (!selectedAccountId) return;
  if (isBlocked(selectedAccountId, currentUser.id)) {
    commentResult.classList.remove("muted");
    commentResult.textContent = "Bạn đang bị chặn trong phòng live này nên không thể gửi bình luận.";
    return;
  }

  const content = commentInput.value.trim();
  const productId = commentProductSelect.value;
  if (!content) {
    commentResult.classList.remove("muted");
    commentResult.textContent = "Vui lòng nhập nội dung bình luận trước khi gửi.";
    return;
  }

  commentResult.classList.remove("muted");
  commentResult.textContent = "Đang gửi bình luận lên hệ thống...";
  try {
    const data = await fetchJson("/api/v1/livestream-comments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        account_id: selectedAccountId,
        customer_id: currentUser.id,
        product_id: productId,
        content,
      }),
    });
    commentInput.value = "";
    await refreshDataAndRender();
    commentResult.textContent = data.auto_message_sent
      ? `Đã gửi bình luận. AI đã mở hội thoại: ${data.auto_message_preview || ""}`
      : "Đã gửi bình luận và đồng bộ lên database.";
  } catch (error) {
    commentResult.textContent = error.message;
  }
  return;

  const comment = {
    id: `cmt-${Date.now()}`,
    accountId: selectedAccountId,
    userId: currentUser.id,
    productId: commentProductSelect.value,
    content,
    createdAt: new Date().toISOString(),
    intent: analyzeBuyingIntent(content),
  };
  demoState.comments.unshift(comment);
  if (comment.intent === "buying_intent") {
    createMlAutoMessage(currentUser.id, selectedAccountId, content, comment.id);
  }
  commentInput.value = "";
  saveLocalState();
  commentResult.classList.remove("muted");
  commentResult.textContent = "Bình luận đã được đưa vào live feed demo.";
  renderLayout();
}

async function handleMessageSubmit(event) {
  event.preventDefault();
  if (!currentUser) return;
  const content = messageInput.value.trim();
  if (!content) {
    messageResult.classList.remove("muted");
    messageResult.textContent = "Vui lòng nhập nội dung tin nhắn trước khi gửi.";
    return;
  }

  const customerId = currentUser.role === "customer" ? currentUser.id : selectedConversationCustomerId;
  if (!selectedAccountId || !customerId) {
    messageResult.classList.remove("muted");
    messageResult.textContent = "Chưa chọn đúng hội thoại để gửi tin nhắn.";
    return;
  }

  messageResult.classList.remove("muted");
  messageResult.textContent = "Đang gửi tin nhắn...";
  try {
    await fetchJson("/api/v1/livestream-messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        account_id: selectedAccountId,
        customer_id: customerId,
        sender_id: currentUser.id,
        sender_role: currentUser.role,
        content,
        source: "manual",
      }),
    });
    messageInput.value = "";
    await refreshDataAndRender();
    messageResult.textContent = "Đã gửi tin nhắn và đồng bộ lên database.";
  } catch (error) {
    messageResult.textContent = error.message;
  }
  return;

  if (currentUser.role === "customer") {
    appendMessage(currentUser.id, {
      senderId: currentUser.id,
      receiverId: getSelectedAccount()?.owner_user_id || "staff",
      accountId: selectedAccountId,
      direction: "inbound",
      source: "manual",
      content,
      createdAt: new Date().toISOString(),
    });
    if (analyzeBuyingIntent(content) === "buying_intent") {
      createMlAutoMessage(currentUser.id, selectedAccountId, content, `msg-${Date.now()}`);
    }
  } else if (currentUser.role === "staff" && selectedConversationCustomerId) {
    appendMessage(selectedConversationCustomerId, {
      senderId: currentUser.id,
      receiverId: selectedConversationCustomerId,
      accountId: selectedAccountId,
      direction: "outbound",
      source: "manual",
      content,
      createdAt: new Date().toISOString(),
    });
  }

  messageInput.value = "";
  saveLocalState();
  messageResult.classList.remove("muted");
  messageResult.textContent = "Tin nhắn demo đã được gửi.";
  renderLayout();
}

function handleSearchSubmit(event) {
  event.preventDefault();
  renderCustomerSearchAndRecommendations(searchInput.value.trim());
}

function attachEventListeners() {
  loginForm.addEventListener("submit", handleLogin);
  registerForm.addEventListener("submit", handleRegister);
  productForm.addEventListener("submit", handleProductCreate);
  liveAssignmentForm.addEventListener("submit", handleAssignmentCreate);
  searchForm.addEventListener("submit", handleSearchSubmit);
  commentForm.addEventListener("submit", handleCommentSubmit);
  messageForm.addEventListener("submit", handleMessageSubmit);

  demoAccountButtons.forEach((button) => {
    button.addEventListener("click", () => {
      loginEmail.value = button.dataset.email || "";
      loginPassword.value = button.dataset.password || "";
    });
  });

  openLoginBtn?.addEventListener("click", () => {
    setRegisterPanelOpen(false);
    loginEmail.focus();
  });

  openRegisterBtn?.addEventListener("click", () => {
    setRegisterPanelOpen(true);
    registerPhone.focus();
  });

  closeRegisterBtn?.addEventListener("click", () => {
    setRegisterPanelOpen(false);
  });

  openChatBtn?.addEventListener("click", () => {
    setChatModalOpen(true);
  });

  closeChatBtn?.addEventListener("click", () => {
    setChatModalOpen(false);
  });

  customerRoomSearchInput?.addEventListener("input", () => {
    renderCustomerRoomPicker(customerRoomSearchInput.value.trim());
  });

  logoutBtn.addEventListener("click", () => {
    leaveCurrentPresence();
    currentUser = null;
    backendState.cartItems = [];
    backendState.orders = [];
    stopMediaStream();
    setRegisterPanelOpen(false);
    setChatModalOpen(false);
    hostLiveEnabled = false;
    saveSession();
    renderLayout();
  });

  resetDemoBtn.addEventListener("click", () => {
    demoState = structuredClone(INITIAL_LOCAL_STATE);
    saveLocalState();
    setStaffAction("Đã reset phần state demo cục bộ. Dữ liệu trong database vẫn được giữ nguyên.", false);
    setCartMessage("Đã reset comment, tin nhắn và block local. Dữ liệu backend vẫn được giữ nguyên.", false);
    renderLayout();
  });

  connectMediaBtn.addEventListener("click", async () => {
    await connectMediaDevices();
  });
  toggleCameraBtn.addEventListener("click", () => toggleTrack("video"));
  toggleMicBtn.addEventListener("click", () => toggleTrack("audio"));
  startLiveBtn.addEventListener("click", () => setStaffAction("Demo camera đã sẵn sàng cho phòng live này.", false));
  endLiveBtn.addEventListener("click", () => setStaffAction("Da ket thuc preview demo tren trinh duyet nay.", false));
  clearCartBtn.addEventListener("click", async () => {
    try {
      await clearCustomerCart();
    } catch (error) {
      setCartMessage(error.message, false);
    }
  });
  checkoutBtn.addEventListener("click", async () => {
    try {
      await checkoutCustomerCart();
    } catch (error) {
      setCartMessage(error.message, false);
    }
  });

  document.body.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    const selectLiveButton = target.closest(".select-live-btn");
    if (selectLiveButton) {
      if (selectedAccountId && selectLiveButton.dataset.accountId !== selectedAccountId) {
        leaveCurrentPresence();
      }
      selectedAccountId = selectLiveButton.dataset.accountId || selectedAccountId;
      saveSession();
      await refreshDataAndRender();
      return;
    }

    const focusProductButton = target.closest(".focus-product-btn");
    if (focusProductButton) {
      const productId = focusProductButton.dataset.productId;
      const assignment = backendState.assignments.find((item) => item.product_id === productId);
      if (assignment) {
        if (selectedAccountId && assignment.account_id !== selectedAccountId) {
          leaveCurrentPresence();
        }
        selectedAccountId = assignment.account_id;
        await refreshDataAndRender();
      }
      if (productId) {
        commentProductSelect.value = productId;
      }
      saveSession();
      return;
    }

    const addToCartButton = target.closest(".add-to-cart-btn");
    if (addToCartButton && currentUser?.role === "customer") {
      try {
        await addToCart(addToCartButton.dataset.productId);
      } catch (error) {
        setCartMessage(error.message, false);
      }
      return;
    }

    const removeCartButton = target.closest(".remove-cart-btn");
    if (removeCartButton && currentUser?.role === "customer") {
      try {
        await removeCartItem(removeCartButton.dataset.cartItemId);
      } catch (error) {
        setCartMessage(error.message, false);
      }
      return;
    }

    const pinButton = target.closest(".pin-product-btn");
    if (pinButton && currentUser?.role === "staff") {
      const card = pinButton.closest(".product-card");
      const livePriceInput = card?.querySelector(".live-price-input");
      try {
        await pinProductForLive(pinButton.dataset.productId, Number(livePriceInput?.value));
        await refreshDataAndRender();
        setStaffAction("Đã ghim sản phẩm và đồng bộ giá live vào database.", false);
      } catch (error) {
        setStaffAction(error.message, false);
      }
      return;
    }

    const blockButton = target.closest(".viewer-block-btn");
    if (blockButton && currentUser?.role === "staff") {
      const key = buildBlockKey(blockButton.dataset.accountId, blockButton.dataset.userId);
      if (demoState.blockedUsers[key]) {
        delete demoState.blockedUsers[key];
        setStaffAction("Da bo chan khach trong demo app.", false);
      } else {
        demoState.blockedUsers[key] = { createdAt: new Date().toISOString() };
        setStaffAction("Da chan khach trong demo app.", false);
      }
      saveLocalState();
      renderLayout();
      return;
    }

    const quickMessageButton = target.closest(".quick-message-btn");
    if (quickMessageButton) {
      selectedConversationCustomerId = quickMessageButton.dataset.userId;
      saveSession();
      setChatModalOpen(true);
      renderLayout();
      return;
    }

    const conversationButton = target.closest(".conversation-item");
    if (conversationButton) {
      selectedConversationCustomerId = conversationButton.dataset.customerId;
      saveSession();
      setChatModalOpen(true);
      renderLayout();
    }
  });

  window.addEventListener("beforeunload", () => {
    leaveCurrentPresence();
    stopMediaStream();
  });

  window.addEventListener("storage", (event) => {
    if (event.key === LOCAL_STATE_KEY) {
      loadLocalState();
      renderLayout();
      return;
    }
    if (event.key === "smartlive-demo-preview-frame" && event.newValue) {
      try {
        applyRemotePreview(JSON.parse(event.newValue));
      } catch (_error) {}
    }
  });

  previewChannel?.addEventListener("message", (event) => {
    applyRemotePreview(event.data);
    renderLayout();
  });

  chatModal?.addEventListener("click", (event) => {
    if (event.target === chatModal) {
      setChatModalOpen(false);
    }
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && isChatModalOpen) {
      setChatModalOpen(false);
    }
  });
}

async function bootstrap() {
  loadSession();
  loadLocalState();
  const persistedPreview = localStorage.getItem("smartlive-demo-preview-frame");
  if (persistedPreview) {
    try {
      applyRemotePreview(JSON.parse(persistedPreview));
    } catch (_error) {}
  }
  attachEventListeners();
  setRegisterPanelOpen(false);
  startLiveBtn.addEventListener("click", async () => {
    hostLiveEnabled = true;
    try {
      await syncCurrentPresence();
      publishPreviewFrame(false);
      await loadBackendData();
      renderLayout();
    } catch (_error) {}
  });
  endLiveBtn.addEventListener("click", async () => {
    hostLiveEnabled = false;
    try {
      publishPreviewFrame(true);
      await syncCurrentPresence();
      await loadBackendData();
      renderLayout();
    } catch (_error) {}
  });
  setDeviceStatus("Chưa cấp quyền camera và micro.", true);
  setStaffAction("App demo đã sẵn sàng cho dữ liệu backend.", true);
  setCartMessage("Khách hàng có thể thêm sản phẩm vào giỏ và mua ngay với dữ liệu được đồng bộ database.", true);
  setProductManagerMessage("Quản lý sản phẩm thao tác trên catalog, assignment và giá live thông qua backend thật.", true);

  if (currentUser) {
    try {
      await refreshDataAndRender();
      return;
    } catch (_error) {
      currentUser = null;
      saveSession();
    }
  }
  renderLayout();
}

bootstrap();
