const API_BASE = "http://localhost:8000";
const SESSION_KEY = "smartlive-demo-session-v6";
const LOCAL_STATE_KEY = "smartlive-demo-local-v6";

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
const videoOverlay = document.getElementById("video-overlay");
const videoOverlayText = document.getElementById("video-overlay-text");
const liveStatusPill = document.getElementById("live-status-pill");
const sessionCard = document.getElementById("session-card");
const pinnedProductCard = document.getElementById("pinned-product-card");

const metricLiveStatus = document.getElementById("metric-live-status");
const metricViewers = document.getElementById("metric-viewers");
const metricComments = document.getElementById("metric-comments");
const metricBlocked = document.getElementById("metric-blocked");

const staffView = document.getElementById("staff-view");
const customerView = document.getElementById("customer-view");
const productManagerView = document.getElementById("product-manager-view");
const commentPanel = document.getElementById("comment-form").closest(".panel");
const messagePanel = document.getElementById("message-form").closest(".panel");

const connectMediaBtn = document.getElementById("connect-media-btn");
const toggleCameraBtn = document.getElementById("toggle-camera-btn");
const toggleMicBtn = document.getElementById("toggle-mic-btn");
const startLiveBtn = document.getElementById("start-live-btn");
const endLiveBtn = document.getElementById("end-live-btn");
const deviceStatus = document.getElementById("device-status");
const staffActionResult = document.getElementById("staff-action-result");
const staffProductList = document.getElementById("staff-product-list");
const viewerManagementList = document.getElementById("viewer-management-list");

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
  comments: [],
  conversations: {},
  blockedUsers: {},
  mlReplyRegistry: {},
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
};
let selectedAccountId = null;
let selectedConversationCustomerId = null;
let mediaStream = null;
let cameraEnabled = true;
let micEnabled = true;

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

function applyLocalState(nextState) {
  demoState = {
    ...structuredClone(INITIAL_LOCAL_STATE),
    ...(nextState || {}),
    comments: (nextState || {}).comments || [],
    conversations: (nextState || {}).conversations || {},
    blockedUsers: (nextState || {}).blockedUsers || {},
    mlReplyRegistry: (nextState || {}).mlReplyRegistry || {},
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
  productManagerResult.textContent = message;
  productManagerResult.classList.toggle("muted", muted);
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
  if (!visibleAccounts.some((account) => account.account_id === selectedAccountId)) {
    selectedAccountId = visibleAccounts[0].account_id;
  }
  return visibleAccounts.find((account) => account.account_id === selectedAccountId) || visibleAccounts[0];
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
    return getAllCustomers().map((customer) => customer.customer_id);
  }
  return [];
}

function ensureConversation(customerId) {
  if (!demoState.conversations[customerId]) {
    demoState.conversations[customerId] = [];
  }
  return demoState.conversations[customerId];
}

function appendMessage(customerId, payload) {
  ensureConversation(customerId).push({
    id: `msg-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`,
    ...payload,
  });
}

function buildBlockKey(accountId, customerId) {
  return `${accountId}::${customerId}`;
}

function isBlocked(accountId, customerId) {
  return Boolean(demoState.blockedUsers[buildBlockKey(accountId, customerId)]);
}

function isAutoMessaged(accountId, customerId) {
  return Boolean(demoState.mlReplyRegistry[buildBlockKey(accountId, customerId)]);
}

function markAutoMessaged(accountId, customerId, sourceId) {
  demoState.mlReplyRegistry[buildBlockKey(accountId, customerId)] = {
    sourceId,
    createdAt: new Date().toISOString(),
  };
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

function createMlAutoMessage(customerId, accountId, sourceText, sourceId) {
  if (isAutoMessaged(accountId, customerId)) {
    return;
  }
  const customer = getAllCustomers().find((item) => item.customer_id === customerId);
  const normalized = normalizeText(sourceText);
  let offerLine = "shop da nhan duoc nhu cau mua hang cua ban va se ho tro chot don ngay trong live.";
  if (normalized.includes("serum")) {
    offerLine = "shop da thay ban quan tam serum, minh co the giu hang va xac nhan so luong ngay bay gio.";
  } else if (normalized.includes("combo")) {
    offerLine = "shop da thay ban quan tam combo, minh se gui nhanh thong tin uu dai va cach chot don cho ban.";
  }

  appendMessage(customerId, {
    senderId: getSelectedAccount()?.owner_user_id || currentUser?.id || "staff",
    receiverId: customerId,
    accountId,
    direction: "outbound",
    source: "ml",
    content: `Chao ${customer?.full_name || "ban"}, ${offerLine}`,
    createdAt: new Date().toISOString(),
  });
  markAutoMessaged(accountId, customerId, sourceId);
  saveLocalState();
}

function getVisibleComments() {
  return demoState.comments
    .filter((comment) => comment.accountId === selectedAccountId)
    .filter((comment) => !isBlocked(comment.accountId, comment.userId))
    .sort((left, right) => new Date(right.createdAt) - new Date(left.createdAt));
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
  saveSession();
}

async function refreshDataAndRender() {
  await loadBackendData();
  renderLayout();
}

function renderLiveSummary() {
  const account = getSelectedAccount();
  if (!account) {
    topbarTitle.textContent = "Chua co phong live";
    liveRoomTitle.textContent = "Chua co phong live";
    sessionCard.innerHTML = '<p class="muted">He thong chua co phong live nao trong database.</p>';
    pinnedProductCard.innerHTML = '<p class="muted">Chua co san pham ghim cho phien live nay.</p>';
    metricLiveStatus.textContent = "Trong";
    metricViewers.textContent = "0";
    metricComments.textContent = "0";
    metricBlocked.textContent = "0";
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
        <span class="badge">Gia goc ${escapeHtml(formatCurrency(liveOffer.original_price))}</span>
        <span class="badge live-badge">Gia live ${escapeHtml(formatCurrency(liveOffer.live_price))}</span>
        <span class="badge">Ton ${escapeHtml(pinnedProduct.stock_quantity)}</span>
      </div>
      ${currentUser?.role === "customer" ? `<button type="button" class="primary-btn add-to-cart-btn" data-product-id="${pinnedProduct.product_id}">Them vao gio hang</button>` : ""}
    `;
  } else {
    pinnedProductCard.innerHTML = '<p class="muted">Chua co san pham ghim cho phien live nay.</p>';
  }

  metricLiveStatus.textContent = account.status === "active" ? "Dang san sang" : account.status;
  metricViewers.textContent = String(account.current_viewers);
  metricComments.textContent = String(visibleComments.length);
  metricBlocked.textContent = String(blockedCount);
  liveStatusPill.textContent = account.status === "active" ? "Live Ready" : account.status;
  liveStatusPill.className = `status-pill ${account.status === "active" ? "live" : "offline"}`;

  if (mediaStream && cameraEnabled && currentUser?.role === "staff") {
    videoOverlay.classList.add("hidden");
  } else {
    videoOverlay.classList.remove("hidden");
    if (currentUser?.role === "staff") {
      videoOverlayText.textContent = mediaStream
        ? "Camera dang tat. Ban co the bat lai camera de tiep tuc demo."
        : "Nhan vien ban hang co the cap quyen camera va micro de bat dau demo.";
    } else if (currentUser?.role === "product_manager") {
      videoOverlayText.textContent = "Vai tro nay cau hinh san pham, ton kho va cap san pham vao phong live tu database.";
    } else {
      videoOverlayText.textContent = "Khach hang dang xem phong live duoc dong bo tu backend va co the mua hang bang gio hang that.";
    }
  }

  if (currentUser?.role === "staff") {
    topbarSubtitle.textContent = "Nhan vien ban hang dang doc phong live va san pham duoc cap tu database.";
    liveRoomDescription.textContent = "Gia live chi co hieu luc sau khi nhan vien ban hang ghim san pham cho phong live nay.";
  } else if (currentUser?.role === "product_manager") {
    topbarSubtitle.textContent = "Nhan vien quan ly san pham dang thao tac tren danh muc dung chung giua frontend chinh va demo app.";
    liveRoomDescription.textContent = "Moi thay doi san pham, ton kho va gan phong live deu duoc ghi xuong database.";
  } else {
    const customer = getCurrentCustomer();
    topbarSubtitle.textContent = "Khach hang dang xem san pham tu phong live that va mua hang qua gio hang duoc dong bo database.";
    liveRoomDescription.textContent = `Dia chi giao hang hien tai: ${customer?.shipping_address || currentUser?.shipping_address || "Chua cap nhat"}.`;
  }
}

function renderProductSelectors() {
  const account = getSelectedAccount();
  const products = account ? getAssignedProducts(account.account_id) : [];
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
    staffProductList.innerHTML = '<div class="message-box muted">Chua co phong live nao de thao tac.</div>';
    return;
  }

  const liveOffer = getLiveOffer(account.account_id);
  const products = getAssignedProducts(account.account_id);
  if (!products.length) {
    staffProductList.innerHTML = '<div class="message-box muted">Chua co san pham nao duoc gan cho phong live nay trong database.</div>';
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
          ${liveOffer?.product_id === product.product_id ? '<span class="badge live-badge">Dang ghim</span>' : ""}
        </div>
        <div class="product-meta">
          <span class="badge">${escapeHtml(product.category)}</span>
          <span class="badge">Gia goc ${escapeHtml(formatCurrency(product.retail_price))}</span>
          <span class="badge">Ton ${escapeHtml(product.stock_quantity)}</span>
        </div>
        <label>Gia live truoc khi ghim
          <input type="number" class="live-price-input" min="1000" max="${product.retail_price}" step="1000" value="${suggestedPrice}" />
        </label>
        <button type="button" class="ghost-btn pin-product-btn" data-product-id="${product.product_id}">${liveOffer?.product_id === product.product_id ? "Cap nhat gia live" : "Ghim len live"}</button>
      </article>
    `;
  }).join("");
}

function renderViewerManagement() {
  if (currentUser?.role !== "staff") {
    viewerManagementList.innerHTML = "";
    return;
  }

  const account = getSelectedAccount();
  if (!account) {
    viewerManagementList.innerHTML = "";
    return;
  }

  viewerManagementList.innerHTML = getAllCustomers().map((customer) => {
    const lastComment = demoState.comments
      .filter((comment) => comment.accountId === account.account_id && comment.userId === customer.customer_id)
      .sort((left, right) => new Date(right.createdAt) - new Date(left.createdAt))[0];
    const blocked = isBlocked(account.account_id, customer.customer_id);
    return `
      <article class="viewer-card">
        <div>
          <strong>${escapeHtml(customer.full_name)}</strong>
          <p>${escapeHtml(customer.phone)}</p>
          <small>${escapeHtml(lastComment?.content || customer.shipping_address)}</small>
        </div>
        <button type="button" class="${blocked ? "primary-btn" : "ghost-btn"} viewer-block-btn" data-account-id="${account.account_id}" data-user-id="${customer.customer_id}">
          ${blocked ? "Bo chan" : "Chan khach"}
        </button>
      </article>
    `;
  }).join("");
}

function renderProductManagerControls() {
  if (currentUser?.role !== "product_manager") {
    productManagerList.innerHTML = "";
    liveAssignmentList.innerHTML = "";
    return;
  }

  assignmentLiveSelect.innerHTML = backendState.accounts.map((account) => `
    <option value="${account.account_id}">${escapeHtml(account.name)} (${escapeHtml(account.platform_display_name)})</option>
  `).join("");

  assignmentProductSelect.innerHTML = backendState.products.map((product) => `
    <option value="${product.product_id}">${escapeHtml(product.name)} - ton ${escapeHtml(product.stock_quantity)}</option>
  `).join("");

  productManagerList.innerHTML = backendState.products.map((product) => `
    <article class="product-card">
      <div class="product-card-head">
        <div>
          <h4>${escapeHtml(product.name)}</h4>
          <p>${escapeHtml(product.description)}</p>
        </div>
        <span class="badge">${escapeHtml(product.category)}</span>
      </div>
      <div class="product-meta">
        <span class="badge">SKU ${escapeHtml(product.sku)}</span>
        <span class="badge">Gia ${escapeHtml(formatCurrency(product.retail_price))}</span>
        <span class="badge">Ton ${escapeHtml(product.stock_quantity)}</span>
      </div>
      <label>Cong them ton kho
        <input type="number" class="stock-adjust-input" min="1" step="1" value="10" />
      </label>
      <div class="inline-actions">
        <button type="button" class="ghost-btn restock-product-btn" data-product-id="${product.product_id}">Cong ton</button>
        <button type="button" class="ghost-btn remove-product-btn" data-product-id="${product.product_id}">Xoa san pham</button>
      </div>
    </article>
  `).join("");

  liveAssignmentList.innerHTML = backendState.accounts.map((account) => {
    const accountAssignments = backendState.assignments.filter((assignment) => assignment.account_id === account.account_id);
    return `
      <article class="product-card">
        <div class="product-card-head">
          <div>
            <h4>${escapeHtml(account.name)}</h4>
            <p>${escapeHtml(account.platform_display_name)} - ${escapeHtml(account.owner_name)}</p>
          </div>
          <span class="badge">${escapeHtml(account.shift_label)}</span>
        </div>
        <div class="stack">
          ${accountAssignments.length ? accountAssignments.map((assignment) => `
            <div class="viewer-card">
              <div>
                <strong>${escapeHtml(assignment.product_name)}</strong>
                <small>${escapeHtml(assignment.product_sku)} - ${escapeHtml(assignment.product_category)}</small>
              </div>
              <button type="button" class="ghost-btn unassign-product-btn" data-assignment-id="${assignment.assignment_id}">Go khoi live</button>
            </div>
          `).join("") : '<div class="message-box muted">Chua co san pham nao duoc cap cho phong live nay.</div>'}
        </div>
      </article>
    `;
  }).join("");
}

function searchContent(query) {
  const normalized = normalizeText(query);
  const assignedProductIds = new Set(backendState.assignments.map((assignment) => assignment.product_id));
  if (!normalized) {
    return {
      liveMatches: getVisibleAccounts().slice(0, 3),
      productMatches: selectedAccountId ? getAssignedProducts(selectedAccountId).slice(0, 4) : [],
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

  const products = getAssignedProducts(account.account_id).slice(0, 4);
  const otherAccounts = getVisibleAccounts().filter((item) => item.account_id !== account.account_id).slice(0, 2);
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
    ? `Tim thay ${liveMatches.length} phong live va ${productMatches.length} san pham lien quan trong database.`
    : "Dang hien thi phong live va san pham duoc cap tu backend de ban thao tac nhanh.";

  searchList.innerHTML = `
    ${liveMatches.map((account) => `
      <article class="search-card">
        <div>
          <p class="eyebrow">Phong live</p>
          <h4>${escapeHtml(account.name)}</h4>
          <p>${escapeHtml(account.platform_display_name)} - ${escapeHtml(account.owner_name)}</p>
          <div class="product-meta">
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
            <span class="badge">Ton ${escapeHtml(product.stock_quantity)}</span>
          </div>
        </div>
        <div class="inline-actions">
          <button type="button" class="ghost-btn focus-product-btn" data-product-id="${product.product_id}">Chon san pham</button>
          <button type="button" class="primary-btn add-to-cart-btn" data-product-id="${product.product_id}">Them vao gio</button>
        </div>
      </article>
    `).join("")}
  `;

  const recommendations = buildRecommendations();
  recommendationList.innerHTML = `
    ${recommendations.products.map((product) => `
      <article class="recommendation-card">
        <p class="eyebrow">De xuat san pham</p>
        <h4>${escapeHtml(product.name)}</h4>
        <p>${escapeHtml(product.description)}</p>
        <div class="product-meta">
          <span class="badge">${escapeHtml(formatCurrency(getEffectivePrice(selectedAccountId, product.product_id)))}</span>
          <span class="badge">Ton ${escapeHtml(product.stock_quantity)}</span>
        </div>
        <button type="button" class="primary-btn add-to-cart-btn" data-product-id="${product.product_id}">Them vao gio</button>
      </article>
    `).join("")}
    ${recommendations.accounts.map((account) => `
      <article class="recommendation-card">
        <p class="eyebrow">Phong live lien quan</p>
        <h4>${escapeHtml(account.name)}</h4>
        <p>${escapeHtml(account.platform_display_name)} - ${escapeHtml(account.owner_name)}</p>
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
    customerCartList.innerHTML = '<div class="message-box muted">Gio hang dang trong. Ban co the them san pham tu phong live duoc dong bo tu backend.</div>';
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
        <span class="badge">Gia goc ${escapeHtml(formatCurrency(item.original_price))}</span>
        <span class="badge live-badge">Gia live ${escapeHtml(formatCurrency(item.unit_price))}</span>
        <span class="badge">Tam tinh ${escapeHtml(formatCurrency(item.line_total))}</span>
      </div>
      <div class="inline-actions">
        <button type="button" class="ghost-btn remove-cart-btn" data-cart-item-id="${item.cart_item_id}">Xoa khoi gio</button>
      </div>
    </article>
  `).join("");

  const total = backendState.cartItems.reduce((sum, item) => sum + item.line_total, 0);
  setCartMessage(`Gio hang hien co ${backendState.cartItems.length} dong san pham, tong tam tinh ${formatCurrency(total)}.`, false);
}

function renderComments() {
  const comments = getVisibleComments();
  commentList.innerHTML = comments.map((comment) => {
    const customer = getAllCustomers().find((item) => item.customer_id === comment.userId);
    const product = backendState.products.find((item) => item.product_id === comment.productId);
    const isStaff = currentUser?.role === "staff";
    return `
      <article class="comment-card">
        <div class="comment-header">
          <div>
            <h4>${escapeHtml(customer?.full_name || "Khach hang")}</h4>
            <p>${escapeHtml(comment.content)}</p>
          </div>
          <span class="badge">${escapeHtml(formatDateTime(comment.createdAt))}</span>
        </div>
        <div class="comment-meta">
          <span class="badge">${escapeHtml(product?.name || "San pham")}</span>
          <span class="badge">${escapeHtml(comment.intent)}</span>
          <span class="badge">${escapeHtml(customer?.shipping_address || "Online")}</span>
        </div>
        ${isStaff ? `
          <div class="comment-actions">
            <button type="button" class="ghost-btn quick-message-btn" data-user-id="${comment.userId}">Mo nhan tin</button>
            <button type="button" class="ghost-btn viewer-block-btn" data-account-id="${comment.accountId}" data-user-id="${comment.userId}">
              ${isBlocked(comment.accountId, comment.userId) ? "Bo chan" : "Chan khach"}
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
    conversationList.innerHTML = '<div class="message-box muted">Vai tro hien tai khong dung hoi thoai nay.</div>';
    threadHeader.innerHTML = "";
    messageThread.innerHTML = '<div class="message-box muted">Chua co hoi thoai nao.</div>';
    return;
  }

  if (!customerIds.includes(selectedConversationCustomerId)) {
    selectedConversationCustomerId = customerIds[0];
  }

  conversationList.innerHTML = customerIds.map((customerId) => {
    const customer = getAllCustomers().find((item) => item.customer_id === customerId);
    const thread = ensureConversation(customerId);
    const lastMessage = [...thread].sort((left, right) => new Date(right.createdAt) - new Date(left.createdAt))[0];
    return `
      <button type="button" class="conversation-item ${customerId === selectedConversationCustomerId ? "active" : ""}" data-customer-id="${customerId}">
        <strong>${escapeHtml(customer?.full_name || "Khach hang")}</strong>
        <span>${escapeHtml(lastMessage?.content || "Chua co tin nhan")}</span>
        <small>${escapeHtml(customer?.phone || customer?.shipping_address || "Online")}</small>
      </button>
    `;
  }).join("");

  const selectedCustomer = getAllCustomers().find((item) => item.customer_id === selectedConversationCustomerId);
  const thread = ensureConversation(selectedConversationCustomerId).slice().sort((left, right) => new Date(left.createdAt) - new Date(right.createdAt));
  const account = getSelectedAccount();
  const autoMessaged = account ? isAutoMessaged(account.account_id, selectedConversationCustomerId) : false;

  threadHeader.innerHTML = `
    <div>
      <strong>${escapeHtml(selectedCustomer?.full_name || "Khach hang")}</strong>
      <span>${escapeHtml(selectedCustomer?.shipping_address || "")}</span>
    </div>
    <div class="thread-badges">
      ${account ? `<span class="badge">${escapeHtml(account.name)}</span>` : ""}
      ${selectedCustomer?.phone ? `<span class="badge">${escapeHtml(selectedCustomer.phone)}</span>` : ""}
      ${autoMessaged ? '<span class="badge live-badge">ML da mo dau hoi thoai</span>' : ""}
    </div>
  `;

  messageThread.innerHTML = thread.length ? thread.map((message) => `
    <article class="message-bubble ${message.senderId === selectedConversationCustomerId ? "inbound" : "outbound"}">
      <div class="message-meta">
        <strong>${escapeHtml(resolveMessageSenderName(message.senderId))}</strong>
        <span>${escapeHtml(formatDateTime(message.createdAt))}</span>
      </div>
      <p>${escapeHtml(message.content)}</p>
      <small>${escapeHtml(message.source === "ml" ? "Tin nhan ho tro boi ML" : "Tin nhan thu cong")}</small>
    </article>
  `).join("") : '<div class="message-box muted">Chua co tin nhan nao trong hoi thoai nay.</div>';
}

function resolveMessageSenderName(senderId) {
  const internal = backendState.accounts.find((account) => account.owner_user_id === senderId);
  if (internal?.owner_name) return internal.owner_name;
  if (currentUser?.id === senderId) return currentUser.name;
  const customer = getAllCustomers().find((item) => item.customer_id === senderId);
  return customer?.full_name || "SmartLive";
}

function renderLayout() {
  const loggedIn = Boolean(currentUser);
  loginScreen.classList.toggle("hidden", loggedIn);
  appScreen.classList.toggle("hidden", !loggedIn);

  if (!loggedIn) return;

  currentUserName.textContent = currentUser.name;
  currentUserRole.textContent = currentUser.role === "product_manager"
    ? "Nhan vien quan ly san pham"
    : currentUser.role === "staff"
      ? "Nhan vien ban hang"
      : "Khach hang";

  staffView.classList.toggle("hidden", currentUser.role !== "staff");
  customerView.classList.toggle("hidden", currentUser.role !== "customer");
  productManagerView.classList.toggle("hidden", currentUser.role !== "product_manager");
  commentPanel.classList.toggle("hidden", currentUser.role === "product_manager");
  messagePanel.classList.toggle("hidden", currentUser.role === "product_manager");

  renderLiveSummary();
  renderProductSelectors();
  renderStaffProductList();
  renderViewerManagement();
  renderProductManagerControls();
  renderCustomerSearchAndRecommendations(searchInput.value.trim());
  renderCustomerCart();
  renderComments();
  renderConversations();

  toggleCameraBtn.textContent = cameraEnabled ? "Tat camera" : "Bat camera";
  toggleMicBtn.textContent = micEnabled ? "Tat micro" : "Bat micro";

  const blocked = currentUser.role === "customer" && selectedAccountId && isBlocked(selectedAccountId, currentUser.id);
  commentInput.disabled = Boolean(blocked);
  commentProductSelect.disabled = Boolean(blocked);
  commentForm.querySelector("button[type='submit']").disabled = Boolean(blocked);
}

async function connectMediaDevices() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setDeviceStatus("Trinh duyet hien tai khong ho tro truy cap camera va micro.", false);
    setStaffAction("Khong the demo camera va micro tren trinh duyet nay.", false);
    return;
  }

  try {
    stopMediaStream();
    mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    livePreview.srcObject = mediaStream;
    cameraEnabled = true;
    micEnabled = true;
    setDeviceStatus("Da cap quyen camera va micro thanh cong.", false);
    setStaffAction("Preview da san sang. Ban co the tiep tuc demo.", false);
    renderLayout();
  } catch (_error) {
    setDeviceStatus("Khong mo duoc camera hoac micro. Hay kiem tra quyen truy cap cua trinh duyet.", false);
    setStaffAction("Thiet bi chua san sang de demo live.", false);
  }
}

function stopMediaStream() {
  if (!mediaStream) return;
  mediaStream.getTracks().forEach((track) => track.stop());
  mediaStream = null;
  livePreview.srcObject = null;
}

function toggleTrack(kind) {
  if (!mediaStream) {
    setStaffAction("Can cap quyen camera va micro truoc khi dieu khien thiet bi.", false);
    return;
  }

  const tracks = kind === "video" ? mediaStream.getVideoTracks() : mediaStream.getAudioTracks();
  if (!tracks.length) {
    setStaffAction(`Khong tim thay ${kind === "video" ? "camera" : "micro"} tren may nay.`, false);
    return;
  }

  const nextEnabled = !tracks[0].enabled;
  tracks.forEach((track) => {
    track.enabled = nextEnabled;
  });

  if (kind === "video") {
    cameraEnabled = nextEnabled;
    setStaffAction(nextEnabled ? "Da bat lai camera." : "Da tat camera.", false);
  } else {
    micEnabled = nextEnabled;
    setStaffAction(nextEnabled ? "Da bat lai micro." : "Da tat micro.", false);
  }
  renderLayout();
}

async function handleLogin(event) {
  event.preventDefault();
  loginResult.classList.remove("muted");
  loginResult.textContent = "Dang xac thuc tai khoan voi backend...";
  try {
    const data = await fetchJson("/api/v1/demo/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier: loginEmail.value.trim(),
        password: loginPassword.value,
      }),
    });
    currentUser = data.user;
    await refreshDataAndRender();
    loginResult.textContent = `Dang nhap thanh cong voi vai tro ${currentUser.role}.`;
  } catch (error) {
    loginResult.textContent = error.message;
  }
}

async function handleRegister(event) {
  event.preventDefault();
  registerResult.classList.remove("muted");
  registerResult.textContent = "Dang tao tai khoan khach hang trong database...";
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
    registerResult.textContent = `Da tao tai khoan cho ${customer.full_name}. Du lieu da duoc dong bo vao database.`;
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
    currentUser = data.user;
    await refreshDataAndRender();
  } catch (error) {
    registerResult.textContent = error.message;
  }
}

async function handleProductCreate(event) {
  event.preventDefault();
  setProductManagerMessage("Dang tao san pham moi trong catalog service...", false);
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
    setProductManagerMessage("Da them san pham moi va dong bo vao database.", false);
  } catch (error) {
    setProductManagerMessage(error.message, false);
  }
}

async function handleAssignmentCreate(event) {
  event.preventDefault();
  setProductManagerMessage("Dang gan san pham vao phong live...", false);
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
    setProductManagerMessage("Da gan san pham vao phong live va dong bo vao database.", false);
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
  setCartMessage("Da them san pham vao gio hang va dong bo len database.", false);
}

async function removeCartItem(cartItemId) {
  if (currentUser?.role !== "customer") return;
  await fetchJson(`/api/v1/customers/${currentUser.id}/cart/items/${cartItemId}`, {
    method: "DELETE",
  });
  await refreshDataAndRender();
  setCartMessage("Da xoa san pham khoi gio hang trong database.", false);
}

async function clearCustomerCart() {
  if (currentUser?.role !== "customer") return;
  await fetchJson(`/api/v1/customers/${currentUser.id}/cart`, { method: "DELETE" });
  await refreshDataAndRender();
  setCartMessage("Da xoa toan bo gio hang trong database.", false);
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
  setCartMessage(`Checkout thanh cong. ${orderSummary}`, false);
}

function handleCommentSubmit(event) {
  event.preventDefault();
  if (!currentUser || currentUser.role !== "customer") return;
  if (!selectedAccountId) return;
  if (isBlocked(selectedAccountId, currentUser.id)) {
    commentResult.classList.remove("muted");
    commentResult.textContent = "Ban dang bi chan trong phong live nay nen khong the gui comment.";
    return;
  }

  const content = commentInput.value.trim();
  if (!content) {
    commentResult.classList.remove("muted");
    commentResult.textContent = "Vui long nhap noi dung binh luan truoc khi gui.";
    return;
  }

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
  commentResult.textContent = "Comment da duoc dua vao live feed demo.";
  renderLayout();
}

function handleMessageSubmit(event) {
  event.preventDefault();
  if (!currentUser) return;
  const content = messageInput.value.trim();
  if (!content) {
    messageResult.classList.remove("muted");
    messageResult.textContent = "Vui long nhap noi dung tin nhan truoc khi gui.";
    return;
  }

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
  messageResult.textContent = "Tin nhan demo da duoc gui.";
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

  logoutBtn.addEventListener("click", () => {
    currentUser = null;
    backendState.cartItems = [];
    backendState.orders = [];
    stopMediaStream();
    saveSession();
    renderLayout();
  });

  resetDemoBtn.addEventListener("click", () => {
    demoState = structuredClone(INITIAL_LOCAL_STATE);
    saveLocalState();
    setStaffAction("Da reset phan state demo cuc bo. Du lieu trong database van duoc giu nguyen.", false);
    setCartMessage("Da reset comment, tin nhan va block local. Du lieu backend van duoc giu nguyen.", false);
    renderLayout();
  });

  connectMediaBtn.addEventListener("click", async () => {
    await connectMediaDevices();
  });
  toggleCameraBtn.addEventListener("click", () => toggleTrack("video"));
  toggleMicBtn.addEventListener("click", () => toggleTrack("audio"));
  startLiveBtn.addEventListener("click", () => setStaffAction("Demo camera da san sang cho phong live nay.", false));
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
      selectedAccountId = selectLiveButton.dataset.accountId || selectedAccountId;
      saveSession();
      renderLayout();
      return;
    }

    const focusProductButton = target.closest(".focus-product-btn");
    if (focusProductButton) {
      const productId = focusProductButton.dataset.productId;
      const assignment = backendState.assignments.find((item) => item.product_id === productId);
      if (assignment) {
        selectedAccountId = assignment.account_id;
        renderLayout();
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
        setStaffAction("Da ghim san pham va dong bo gia live vao database.", false);
      } catch (error) {
        setStaffAction(error.message, false);
      }
      return;
    }

    const restockButton = target.closest(".restock-product-btn");
    if (restockButton && currentUser?.role === "product_manager") {
      const card = restockButton.closest(".product-card");
      const stockInput = card?.querySelector(".stock-adjust-input");
      try {
        await restockProduct(restockButton.dataset.productId, Number(stockInput?.value));
        await refreshDataAndRender();
        setProductManagerMessage("Da cong them ton kho va dong bo vao database.", false);
      } catch (error) {
        setProductManagerMessage(error.message, false);
      }
      return;
    }

    const removeProductButton = target.closest(".remove-product-btn");
    if (removeProductButton && currentUser?.role === "product_manager") {
      try {
        await fetchJson(`/api/v1/products/${removeProductButton.dataset.productId}`, { method: "DELETE" });
        await refreshDataAndRender();
        setProductManagerMessage("Da xoa san pham khoi catalog service.", false);
      } catch (error) {
        setProductManagerMessage(error.message, false);
      }
      return;
    }

    const unassignButton = target.closest(".unassign-product-btn");
    if (unassignButton && currentUser?.role === "product_manager") {
      try {
        await fetchJson(`/api/v1/livestream-product-assignments/${unassignButton.dataset.assignmentId}`, {
          method: "DELETE",
        });
        await refreshDataAndRender();
        setProductManagerMessage("Da go san pham khoi phong live trong database.", false);
      } catch (error) {
        setProductManagerMessage(error.message, false);
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
      renderLayout();
      return;
    }

    const conversationButton = target.closest(".conversation-item");
    if (conversationButton) {
      selectedConversationCustomerId = conversationButton.dataset.customerId;
      saveSession();
      renderLayout();
    }
  });

  window.addEventListener("beforeunload", () => {
    stopMediaStream();
  });

  window.addEventListener("storage", (event) => {
    if (event.key !== LOCAL_STATE_KEY) return;
    loadLocalState();
    renderLayout();
  });
}

async function bootstrap() {
  loadSession();
  loadLocalState();
  attachEventListeners();
  setDeviceStatus("Chua cap quyen camera va micro.", true);
  setStaffAction("App demo da san sang cho du lieu backend.", true);
  setCartMessage("Khach hang co the them san pham vao gio va mua ngay voi du lieu duoc dong bo database.", true);
  setProductManagerMessage("Quan ly san pham thao tac tren catalog, assignment va gia live thong qua backend that.", true);

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
