const TAB_SESSION_KEY = "smartlive-demo-tab-session";
const STATE_KEY = "smartlive-demo-state-v2";

const loginScreen = document.getElementById("login-screen");
const appScreen = document.getElementById("app-screen");
const loginForm = document.getElementById("login-form");
const loginEmail = document.getElementById("login-email");
const loginPassword = document.getElementById("login-password");
const loginResult = document.getElementById("login-result");
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
const connectMediaBtn = document.getElementById("connect-media-btn");
const toggleCameraBtn = document.getElementById("toggle-camera-btn");
const toggleMicBtn = document.getElementById("toggle-mic-btn");
const startLiveBtn = document.getElementById("start-live-btn");
const endLiveBtn = document.getElementById("end-live-btn");
const deviceStatus = document.getElementById("device-status");
const staffActionResult = document.getElementById("staff-action-result");
const staffProductList = document.getElementById("staff-product-list");
const viewerManagementList = document.getElementById("viewer-management-list");

const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const searchResult = document.getElementById("search-result");
const searchList = document.getElementById("search-list");
const recommendationList = document.getElementById("recommendation-list");

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

const DEMO_USERS = [
  {
    id: "staff-01",
    role: "staff",
    name: "Mai Anh",
    email: "staff.live@smartlive.vn",
    password: "123456",
    title: "Nhan vien live",
    location: "Studio SmartLive, TP.HCM",
  },
  {
    id: "customer-01",
    role: "customer",
    name: "Linh Nguyen",
    email: "linh.nguyen@gmail.com",
    password: "123456",
    title: "Khach hang",
    location: "Quan 7, TP.HCM",
    interests: ["serum", "vitamin c", "skincare"],
  },
  {
    id: "customer-02",
    role: "customer",
    name: "Thao Tran",
    email: "thao.tran@gmail.com",
    password: "123456",
    title: "Khach hang",
    location: "Thu Duc, TP.HCM",
    interests: ["da nhay cam", "phuc hoi", "skin barrier"],
  },
  {
    id: "customer-03",
    role: "customer",
    name: "Minh Anh",
    email: "minh.anh@gmail.com",
    password: "123456",
    title: "Khach hang",
    location: "Bien Hoa, Dong Nai",
    interests: ["combo", "uu dai", "kem chong nang"],
  },
];

const LIVE_SESSIONS = [
  {
    id: "live-01",
    title: "GlowHouse - Livestream skincare toi nay",
    hostName: "Mai Anh",
    schedule: "20:00 - 21:30, 18/04/2026",
    topic: "Routine skincare phuc hoi va combo uu dai trong live",
    tags: ["skincare", "serum", "vitamin c", "combo"],
    productIds: ["prd-01", "prd-02", "prd-03"],
    description: "Livestream chot serum, kem chong nang va combo phuc hoi cho da nhay cam.",
  },
  {
    id: "live-02",
    title: "Morning Care - Makeup nen mong nhe",
    hostName: "Khanh Ly",
    schedule: "09:00 - 10:00, 19/04/2026",
    tags: ["makeup", "cushion", "kem lot"],
    productIds: ["prd-04"],
    description: "Phien live makeup co nen mong nhe va san pham che phu tu nhien.",
  },
  {
    id: "live-03",
    title: "Skin Barrier Talk - Da nhay cam",
    hostName: "My Tam",
    schedule: "21:00 - 22:00, 20/04/2026",
    tags: ["da nhay cam", "skin barrier", "phuc hoi"],
    productIds: ["prd-03", "prd-05"],
    description: "Noi dung danh cho nguoi dang tim routine phuc hoi va diu da.",
  },
];

const PRODUCTS = [
  {
    id: "prd-01",
    name: "Serum Vitamin C 15%",
    price: 329000,
    category: "Skincare",
    tags: ["serum", "vitamin c", "sang da"],
    liveIds: ["live-01"],
    highlight: "Lam sang da, ho tro mo tham nhanh va de ket hop buoi sang.",
  },
  {
    id: "prd-02",
    name: "Kem chong nang Skin Barrier SPF50+",
    price: 289000,
    category: "Skincare",
    tags: ["kem chong nang", "skin barrier", "hang ngay"],
    liveIds: ["live-01"],
    highlight: "Mong nhe, khong bi da, phu hop da hon hop va da nhay cam.",
  },
  {
    id: "prd-03",
    name: "Combo phuc hoi 3 buoc",
    price: 699000,
    category: "Combo",
    tags: ["combo", "phuc hoi", "da nhay cam"],
    liveIds: ["live-01", "live-03"],
    highlight: "Sua rua mat, serum phuc hoi va kem duong cho da can cap am.",
  },
  {
    id: "prd-04",
    name: "Cushion Air Fit Glow",
    price: 359000,
    category: "Makeup",
    tags: ["cushion", "makeup", "nen mong"],
    liveIds: ["live-02"],
    highlight: "Lop nen mong nhe, che phu vua phai, hop da thuong va da kho.",
  },
  {
    id: "prd-05",
    name: "Essence diu da Skin Reset",
    price: 399000,
    category: "Skincare",
    tags: ["essence", "phuc hoi", "da nhay cam"],
    liveIds: ["live-03"],
    highlight: "Lam diu da sau kich ung va giup da giu am tot hon.",
  },
];

const INITIAL_STATE = {
  selectedLiveId: "live-01",
  liveStatusById: {
    "live-01": { isLive: false, viewerCount: 128, pinnedProductId: "prd-01" },
    "live-02": { isLive: false, viewerCount: 86, pinnedProductId: "prd-04" },
    "live-03": { isLive: false, viewerCount: 92, pinnedProductId: "prd-03" },
  },
  comments: [
    {
      id: "cmt-001",
      liveSessionId: "live-01",
      userId: "customer-01",
      productId: "prd-01",
      content: "Shop oi serum nay con hang khong, em muon chot 2 chai toi nay.",
      createdAt: "2026-04-18T20:03:00+07:00",
      intent: "buying_intent",
    },
    {
      id: "cmt-002",
      liveSessionId: "live-01",
      userId: "customer-02",
      productId: "prd-03",
      content: "Da nhay cam thi combo nay dung moi ngay duoc khong a?",
      createdAt: "2026-04-18T20:05:00+07:00",
      intent: "consult_request",
    },
    {
      id: "cmt-003",
      liveSessionId: "live-01",
      userId: "customer-03",
      productId: "prd-02",
      content: "Kem chong nang nay neu lay 2 tuyp thi co freeship khong?",
      createdAt: "2026-04-18T20:08:00+07:00",
      intent: "ask_price",
    },
  ],
  blockedUsers: {},
  mlReplyRegistry: {},
  conversations: {
    "customer-01": [
      {
        id: "msg-001",
        senderId: "staff-01",
        receiverId: "customer-01",
        liveSessionId: "live-01",
        direction: "outbound",
        source: "ml",
        content: "Chao Linh, shop da thay comment muon chot serum. Minh nhan rieng de xac nhan so luong va dia chi giao hang cho ban.",
        createdAt: "2026-04-18T20:04:00+07:00",
      },
      {
        id: "msg-002",
        senderId: "customer-01",
        receiverId: "staff-01",
        liveSessionId: "live-01",
        direction: "inbound",
        source: "manual",
        content: "Da, em muon chot 2 chai serum va 1 kem chong nang.",
        createdAt: "2026-04-18T20:06:00+07:00",
      },
    ],
    "customer-02": [
      {
        id: "msg-003",
        senderId: "customer-02",
        receiverId: "staff-01",
        liveSessionId: "live-01",
        direction: "inbound",
        source: "manual",
        content: "Shop oi da nhay cam thi combo phuc hoi co mui huong khong a?",
        createdAt: "2026-04-18T20:07:00+07:00",
      },
    ],
    "customer-03": [],
  },
};

let currentUser = null;
let appState = structuredClone(INITIAL_STATE);
let mediaStream = null;
let cameraEnabled = true;
let micEnabled = true;
let selectedLiveId = "live-01";
let selectedConversationCustomerId = "customer-01";

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatCurrency(value) {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
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
  return (value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .trim();
}

function getUserById(userId) {
  return DEMO_USERS.find((user) => user.id === userId) || null;
}

function getLiveSessionById(liveId) {
  return LIVE_SESSIONS.find((session) => session.id === liveId) || null;
}

function getProductById(productId) {
  return PRODUCTS.find((product) => product.id === productId) || null;
}

function getSelectedLive() {
  return getLiveSessionById(selectedLiveId) || LIVE_SESSIONS[0];
}

function getSelectedLiveStatus() {
  return appState.liveStatusById[selectedLiveId];
}

function buildRegistryKey(liveSessionId, customerId) {
  return `${liveSessionId}::${customerId}`;
}

function isBlocked(liveSessionId, customerId) {
  return Boolean(appState.blockedUsers[buildRegistryKey(liveSessionId, customerId)]);
}

function isAutoMessagedInSession(liveSessionId, customerId) {
  return Boolean(appState.mlReplyRegistry[buildRegistryKey(liveSessionId, customerId)]);
}

function markAutoMessaged(liveSessionId, customerId, sourceId) {
  appState.mlReplyRegistry[buildRegistryKey(liveSessionId, customerId)] = {
    sourceId,
    createdAt: new Date().toISOString(),
  };
}

function saveSharedState() {
  localStorage.setItem(STATE_KEY, JSON.stringify(appState));
}

function saveSessionState() {
  sessionStorage.setItem(TAB_SESSION_KEY, JSON.stringify({
    currentUserId: currentUser?.id ?? null,
    selectedLiveId,
    selectedConversationCustomerId,
  }));
}

function saveState() {
  saveSharedState();
  saveSessionState();
}

function applySharedState(parsedSharedState) {
  appState = {
    ...structuredClone(INITIAL_STATE),
    ...(parsedSharedState || {}),
    liveStatusById: {
      ...structuredClone(INITIAL_STATE.liveStatusById),
      ...((parsedSharedState || {}).liveStatusById || {}),
    },
    blockedUsers: (parsedSharedState || {}).blockedUsers || {},
    mlReplyRegistry: (parsedSharedState || {}).mlReplyRegistry || {},
    comments: (parsedSharedState || {}).comments || structuredClone(INITIAL_STATE.comments),
    conversations: {
      ...structuredClone(INITIAL_STATE.conversations),
      ...((parsedSharedState || {}).conversations || {}),
    },
  };
}

function loadState() {
  const savedState = localStorage.getItem(STATE_KEY);
  const savedTabSession = sessionStorage.getItem(TAB_SESSION_KEY);
  const parsedSharedState = savedState ? JSON.parse(savedState) : structuredClone(INITIAL_STATE);
  applySharedState(parsedSharedState);

  if (savedTabSession) {
    const tabSession = JSON.parse(savedTabSession);
    currentUser = tabSession.currentUserId ? getUserById(tabSession.currentUserId) : null;
    selectedLiveId = tabSession.selectedLiveId || "live-01";
    selectedConversationCustomerId = tabSession.selectedConversationCustomerId || "customer-01";
  } else {
    currentUser = null;
    selectedLiveId = "live-01";
    selectedConversationCustomerId = "customer-01";
  }
}

function resetDemoState() {
  appState = structuredClone(INITIAL_STATE);
  cameraEnabled = true;
  micEnabled = true;
  selectedLiveId = "live-01";
  selectedConversationCustomerId = "customer-01";
  saveState();
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

function ensureConversation(customerId) {
  if (!appState.conversations[customerId]) {
    appState.conversations[customerId] = [];
  }
  return appState.conversations[customerId];
}

function appendMessage(customerId, payload) {
  const thread = ensureConversation(customerId);
  thread.push({
    id: `msg-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`,
    ...payload,
  });
}

function createMlAutoMessage(customerId, liveSessionId, sourceText, sourceId) {
  if (isAutoMessagedInSession(liveSessionId, customerId)) {
    return false;
  }

  const customer = getUserById(customerId);
  const normalized = normalizeText(sourceText);
  let offerLine = "Shop da nhan duoc nhu cau mua hang cua ban va se ho tro chot don ngay trong live.";
  if (normalized.includes("serum")) {
    offerLine = "Shop da thay ban quan tam serum, minh co the giu hang va xac nhan so luong ngay bay gio.";
  } else if (normalized.includes("combo")) {
    offerLine = "Shop da thay ban quan tam combo, minh se gui nhanh thong tin uu dai va cach chot don cho ban.";
  } else if (normalized.includes("kem chong nang")) {
    offerLine = "Shop da nhan nhu cau voi kem chong nang, minh se xac nhan uu dai va so luong giup ban.";
  }

  appendMessage(customerId, {
    senderId: "staff-01",
    receiverId: customerId,
    liveSessionId,
    direction: "outbound",
    source: "ml",
    content: `Chao ${customer?.name || "ban"}, ${offerLine}`,
    createdAt: new Date().toISOString(),
  });
  markAutoMessaged(liveSessionId, customerId, sourceId);
  return true;
}

function searchContent(query) {
  const normalized = normalizeText(query);
  if (!normalized) {
    return {
      liveMatches: [getSelectedLive()],
      productMatches: PRODUCTS.filter((product) => product.liveIds.includes(selectedLiveId)).slice(0, 3),
    };
  }

  const liveMatches = LIVE_SESSIONS.filter((session) =>
    normalizeText(`${session.title} ${session.description} ${session.tags.join(" ")}`).includes(normalized),
  );

  const productMatches = PRODUCTS.filter((product) =>
    normalizeText(`${product.name} ${product.highlight} ${product.tags.join(" ")}`).includes(normalized),
  );

  return { liveMatches, productMatches };
}

function buildRecommendations() {
  const live = getSelectedLive();
  const baseKeywords = currentUser?.role === "customer"
    ? [...(currentUser.interests || []), ...live.tags]
    : [...live.tags];

  const uniqueKeywords = [...new Set(baseKeywords.map((item) => normalizeText(item)))];
  const recommendedProducts = PRODUCTS.filter((product) =>
    product.liveIds.includes(live.id) ||
    product.tags.some((tag) => uniqueKeywords.includes(normalizeText(tag))),
  ).slice(0, 4);

  const relatedLives = LIVE_SESSIONS.filter((session) =>
    session.id !== live.id && session.tags.some((tag) => uniqueKeywords.includes(normalizeText(tag))),
  ).slice(0, 2);

  return { recommendedProducts, relatedLives };
}

function getVisibleComments() {
  return appState.comments
    .filter((comment) => comment.liveSessionId === selectedLiveId)
    .filter((comment) => !isBlocked(comment.liveSessionId, comment.userId))
    .sort((left, right) => new Date(right.createdAt) - new Date(left.createdAt));
}

function getActiveCustomersForLive() {
  const liveId = selectedLiveId;
  return DEMO_USERS.filter((user) => user.role === "customer").map((user) => {
    const lastComment = appState.comments
      .filter((comment) => comment.liveSessionId === liveId && comment.userId === user.id)
      .sort((left, right) => new Date(right.createdAt) - new Date(left.createdAt))[0];
    return {
      user,
      blocked: isBlocked(liveId, user.id),
      lastComment,
    };
  });
}

function getConversationCustomerIds() {
  if (currentUser?.role === "customer") {
    return [currentUser.id];
  }
  return DEMO_USERS.filter((user) => user.role === "customer").map((user) => user.id);
}

function getSelectedConversationCustomerId() {
  if (currentUser?.role === "customer") {
    return currentUser.id;
  }

  const availableIds = getConversationCustomerIds();
  if (!availableIds.includes(selectedConversationCustomerId)) {
    selectedConversationCustomerId = availableIds[0];
  }
  return selectedConversationCustomerId;
}

function stopMediaStream() {
  if (!mediaStream) return;
  mediaStream.getTracks().forEach((track) => track.stop());
  mediaStream = null;
  livePreview.srcObject = null;
}

function setDeviceStatus(message, muted = false) {
  deviceStatus.textContent = message;
  deviceStatus.classList.toggle("muted", muted);
}

function setStaffAction(message, muted = false) {
  staffActionResult.textContent = message;
  staffActionResult.classList.toggle("muted", muted);
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
    setStaffAction("Preview da san sang. Ban co the bat dau phien live.", false);
    renderLayout();
  } catch (_error) {
    setDeviceStatus("Khong mo duoc camera hoac micro. Hay kiem tra quyen truy cap cua trinh duyet.", false);
    setStaffAction("Thiet bi chua san sang de demo live.", false);
  }
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

function renderLiveSummary() {
  const live = getSelectedLive();
  const liveStatus = getSelectedLiveStatus();
  const blockedCount = Object.keys(appState.blockedUsers).filter((key) => key.startsWith(`${live.id}::`)).length;
  const visibleComments = getVisibleComments();
  const pinnedProduct = getProductById(liveStatus.pinnedProductId);

  topbarTitle.textContent = live.title;
  liveRoomTitle.textContent = live.title;
  sessionCard.innerHTML = `
    <strong>${escapeHtml(live.title)}</strong>
    <div>Host: ${escapeHtml(live.hostName)}</div>
    <div>Lich: ${escapeHtml(live.schedule)}</div>
    <div>Chu de: ${escapeHtml(live.topic)}</div>
    <div>${escapeHtml(live.description)}</div>
  `;

  pinnedProductCard.innerHTML = pinnedProduct ? `
    <p class="eyebrow">San pham dang ghim</p>
    <h4>${escapeHtml(pinnedProduct.name)}</h4>
    <p>${escapeHtml(pinnedProduct.highlight)}</p>
    <div class="product-meta">
      <span class="badge">${escapeHtml(pinnedProduct.category)}</span>
      <span class="badge">${escapeHtml(formatCurrency(pinnedProduct.price))}</span>
    </div>
  ` : `<p class="muted">Chua co san pham ghim cho phien live nay.</p>`;

  metricLiveStatus.textContent = liveStatus.isLive ? "Dang live" : "San sang";
  metricViewers.textContent = String(liveStatus.viewerCount);
  metricComments.textContent = String(visibleComments.length);
  metricBlocked.textContent = String(blockedCount);

  liveStatusPill.textContent = liveStatus.isLive ? "Live now" : "Offline";
  liveStatusPill.className = `status-pill ${liveStatus.isLive ? "live" : "offline"}`;

  const isStaff = currentUser?.role === "staff";
  if (mediaStream && cameraEnabled) {
    videoOverlay.classList.add("hidden");
  } else {
    videoOverlay.classList.remove("hidden");
    if (isStaff) {
      videoOverlayText.textContent = mediaStream
        ? "Camera dang tat. Ban co the bat lai camera de tiep tuc live."
        : "Nhan vien live co the cap quyen camera va micro de bat dau demo.";
    } else {
      videoOverlayText.textContent = liveStatus.isLive
        ? "Host dang live tren thiet bi demo. Ban dang xem bo cuc viewer."
        : "Phien live chua bat dau. Ban co the tim them phien khac hoac xem goi y lien quan.";
    }
  }

  if (currentUser?.role === "staff") {
    topbarSubtitle.textContent = "Tai khoan nhan vien live dang dieu khien phien, xu ly comment, block khach va nhan tin voi nguoi mua.";
    liveRoomDescription.textContent = "App demo nay mo phong phia van hanh livestream. Cac xu ly ML duoc an vao luong nhan tin va comment.";
  } else {
    topbarSubtitle.textContent = "Tai khoan khach hang dang tim phien live, xem san pham, nhan goi y lien quan va nhan tin voi shop.";
    liveRoomDescription.textContent = "Khach co the tim theo ten phien live, san pham hoac chu de, sau do tham gia comment va hoi thoai voi shop.";
  }
}

function renderProductSelectors() {
  const selectedLive = getSelectedLive();
  const liveProducts = PRODUCTS.filter((product) => selectedLive.productIds.includes(product.id));
  commentProductSelect.innerHTML = liveProducts.map((product) => `
    <option value="${product.id}">${escapeHtml(product.name)} - ${escapeHtml(formatCurrency(product.price))}</option>
  `).join("");
}

function renderStaffProductList() {
  if (currentUser?.role !== "staff") {
    staffProductList.innerHTML = "";
    return;
  }

  const selectedLive = getSelectedLive();
  const liveStatus = getSelectedLiveStatus();
  const liveProducts = PRODUCTS.filter((product) => selectedLive.productIds.includes(product.id));

  staffProductList.innerHTML = liveProducts.map((product) => `
    <article class="product-card ${product.id === liveStatus.pinnedProductId ? "is-pinned" : ""}">
      <div class="product-card-head">
        <div>
          <h4>${escapeHtml(product.name)}</h4>
          <p>${escapeHtml(product.highlight)}</p>
        </div>
        ${product.id === liveStatus.pinnedProductId ? '<span class="badge live-badge">Dang ghim</span>' : ""}
      </div>
      <div class="product-meta">
        <span class="badge">${escapeHtml(product.category)}</span>
        <span class="badge">${escapeHtml(formatCurrency(product.price))}</span>
      </div>
      <button type="button" class="ghost-btn pin-product-btn" data-product-id="${product.id}">
        ${product.id === liveStatus.pinnedProductId ? "Dang ghim" : "Ghim len live"}
      </button>
    </article>
  `).join("");
}

function renderViewerManagement() {
  if (currentUser?.role !== "staff") {
    viewerManagementList.innerHTML = "";
    return;
  }

  const selectedLive = getSelectedLive();
  const activeCustomers = getActiveCustomersForLive();
  viewerManagementList.innerHTML = activeCustomers.map(({ user, blocked, lastComment }) => `
    <article class="viewer-card">
      <div>
        <strong>${escapeHtml(user.name)}</strong>
        <p>${escapeHtml(user.location)}</p>
        <small>${escapeHtml(lastComment?.content || "Chua co comment trong phien nay")}</small>
      </div>
      <button
        type="button"
        class="${blocked ? "primary-btn" : "ghost-btn"} viewer-block-btn"
        data-live-id="${selectedLive.id}"
        data-user-id="${user.id}"
      >
        ${blocked ? "Bo chan" : "Chan khach"}
      </button>
    </article>
  `).join("");
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
    ? `Tim thay ${liveMatches.length} phien live va ${productMatches.length} san pham lien quan voi "${query}".`
    : "Dang hien thi phien live hien tai va san pham lien quan de ban tham khao nhanh.";

  searchList.innerHTML = `
    ${liveMatches.map((live) => `
      <article class="search-card">
        <div>
          <p class="eyebrow">Phien live</p>
          <h4>${escapeHtml(live.title)}</h4>
          <p>${escapeHtml(live.description)}</p>
          <div class="product-meta">
            <span class="badge">${escapeHtml(live.schedule)}</span>
            <span class="badge">${escapeHtml(live.tags.join(", "))}</span>
          </div>
        </div>
        <button type="button" class="primary-btn select-live-btn" data-live-id="${live.id}">Xem phien nay</button>
      </article>
    `).join("")}
    ${productMatches.map((product) => `
      <article class="search-card">
        <div>
          <p class="eyebrow">San pham</p>
          <h4>${escapeHtml(product.name)}</h4>
          <p>${escapeHtml(product.highlight)}</p>
          <div class="product-meta">
            <span class="badge">${escapeHtml(product.category)}</span>
            <span class="badge">${escapeHtml(formatCurrency(product.price))}</span>
          </div>
        </div>
        <button type="button" class="ghost-btn focus-product-btn" data-product-id="${product.id}">Chon san pham</button>
      </article>
    `).join("")}
  `;

  const recommendations = buildRecommendations();
  recommendationList.innerHTML = `
    ${recommendations.recommendedProducts.map((product) => `
      <article class="recommendation-card">
        <p class="eyebrow">De xuat san pham</p>
        <h4>${escapeHtml(product.name)}</h4>
        <p>${escapeHtml(product.highlight)}</p>
      </article>
    `).join("")}
    ${recommendations.relatedLives.map((live) => `
      <article class="recommendation-card">
        <p class="eyebrow">Phien live lien quan</p>
        <h4>${escapeHtml(live.title)}</h4>
        <p>${escapeHtml(live.description)}</p>
      </article>
    `).join("")}
  `;
}

function renderComments() {
  const comments = getVisibleComments();
  commentList.innerHTML = comments.map((comment) => {
    const user = getUserById(comment.userId);
    const product = getProductById(comment.productId);
    const isStaff = currentUser?.role === "staff";
    return `
      <article class="comment-card">
        <div class="comment-header">
          <div>
            <h4>${escapeHtml(user?.name || "Khach hang")}</h4>
            <p>${escapeHtml(comment.content)}</p>
          </div>
          <span class="badge">${escapeHtml(formatDateTime(comment.createdAt))}</span>
        </div>
        <div class="comment-meta">
          <span class="badge">${escapeHtml(product?.name || "San pham dang xem")}</span>
          <span class="badge">${escapeHtml(comment.intent || "other")}</span>
          <span class="badge">${escapeHtml(user?.location || "Online")}</span>
        </div>
        ${isStaff ? `
          <div class="comment-actions">
            <button type="button" class="ghost-btn quick-message-btn" data-user-id="${comment.userId}">Mo nhan tin</button>
            <button type="button" class="ghost-btn viewer-block-btn" data-live-id="${comment.liveSessionId}" data-user-id="${comment.userId}">
              ${isBlocked(comment.liveSessionId, comment.userId) ? "Bo chan" : "Chan khach"}
            </button>
          </div>
        ` : ""}
      </article>
    `;
  }).join("");
}

function getThreadForSelectedConversation() {
  const customerId = getSelectedConversationCustomerId();
  return ensureConversation(customerId).slice().sort((left, right) => new Date(left.createdAt) - new Date(right.createdAt));
}

function renderConversations() {
  const customerIds = getConversationCustomerIds();
  const selectedCustomerId = getSelectedConversationCustomerId();

  conversationList.innerHTML = customerIds.map((customerId) => {
    const customer = getUserById(customerId);
    const thread = ensureConversation(customerId);
    const lastMessage = [...thread].sort((left, right) => new Date(right.createdAt) - new Date(left.createdAt))[0];
    const isBlockedNow = isBlocked(selectedLiveId, customerId);
    return `
      <button type="button" class="conversation-item ${customerId === selectedCustomerId ? "active" : ""}" data-customer-id="${customerId}">
        <strong>${escapeHtml(customer?.name || "Khach hang")}</strong>
        <span>${escapeHtml(lastMessage?.content || "Chua co tin nhan")}</span>
        <small>${escapeHtml(isBlockedNow ? "Dang bi chan trong live" : customer?.location || "Online")}</small>
      </button>
    `;
  }).join("");

  const selectedCustomer = getUserById(selectedCustomerId);
  const thread = getThreadForSelectedConversation();
  const autoMessaged = isAutoMessagedInSession(selectedLiveId, selectedCustomerId);

  threadHeader.innerHTML = `
    <div>
      <strong>${escapeHtml(selectedCustomer?.name || "Khach hang")}</strong>
      <span>${escapeHtml(selectedCustomer?.location || "")}</span>
    </div>
    <div class="thread-badges">
      <span class="badge">${escapeHtml(getSelectedLive().title)}</span>
      ${autoMessaged ? '<span class="badge live-badge">ML da mo dau hoi thoai</span>' : ""}
    </div>
  `;

  messageThread.innerHTML = thread.length ? thread.map((message) => `
    <article class="message-bubble ${message.senderId === "staff-01" ? "outbound" : "inbound"}">
      <div class="message-meta">
        <strong>${escapeHtml(getUserById(message.senderId)?.name || "SmartLive")}</strong>
        <span>${escapeHtml(formatDateTime(message.createdAt))}</span>
      </div>
      <p>${escapeHtml(message.content)}</p>
      <small>${escapeHtml(message.source === "ml" ? "Tin nhan ho tro boi ML" : "Tin nhan thu cong")}</small>
    </article>
  `).join("") : '<div class="message-box muted">Chua co tin nhan nao trong hoi thoai nay.</div>';
}

function renderLayout() {
  const loggedIn = Boolean(currentUser);
  loginScreen.classList.toggle("hidden", loggedIn);
  appScreen.classList.toggle("hidden", !loggedIn);

  if (!loggedIn) return;

  currentUserName.textContent = currentUser.name;
  currentUserRole.textContent = currentUser.title;
  staffView.classList.toggle("hidden", currentUser.role !== "staff");
  customerView.classList.toggle("hidden", currentUser.role !== "customer");

  renderLiveSummary();
  renderProductSelectors();
  renderStaffProductList();
  renderViewerManagement();
  renderCustomerSearchAndRecommendations(searchInput.value.trim());
  renderComments();
  renderConversations();

  toggleCameraBtn.textContent = cameraEnabled ? "Tat camera" : "Bat camera";
  toggleMicBtn.textContent = micEnabled ? "Tat micro" : "Bat micro";

  const blocked = currentUser.role === "customer" && isBlocked(selectedLiveId, currentUser.id);
  commentInput.disabled = blocked;
  commentProductSelect.disabled = blocked;
  commentForm.querySelector("button[type='submit']").disabled = blocked;

  if (blocked) {
    commentResult.classList.remove("muted");
    commentResult.textContent = "Ban dang bi chan trong phien live nay nen khong the tiep tuc comment.";
  }
}

function setCurrentUser(user) {
  currentUser = user;
  if (user.role === "customer") {
    selectedConversationCustomerId = user.id;
  }
  saveState();
  renderLayout();
}

function handleAutoMlFromComment(comment) {
  if (comment.intent !== "buying_intent") return;
  createMlAutoMessage(comment.userId, comment.liveSessionId, comment.content, comment.id);
}

function handleAutoMlFromMessage(customerId, liveSessionId, text, sourceId) {
  const intent = analyzeBuyingIntent(text);
  if (intent === "buying_intent") {
    createMlAutoMessage(customerId, liveSessionId, text, sourceId);
  }
}

demoAccountButtons.forEach((button) => {
  button.addEventListener("click", () => {
    loginEmail.value = button.dataset.email || "";
    loginPassword.value = button.dataset.password || "";
  });
});

loginForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const user = DEMO_USERS.find((item) => item.email === loginEmail.value.trim() && item.password === loginPassword.value);

  if (!user) {
    loginResult.classList.remove("muted");
    loginResult.textContent = "Khong tim thay tai khoan demo phu hop. Hay chon mot tai khoan goi y ben duoi.";
    return;
  }

  loginResult.classList.remove("muted");
  loginResult.textContent = `Dang nhap thanh cong voi vai tro ${user.title}.`;
  setCurrentUser(user);
});

logoutBtn.addEventListener("click", () => {
  currentUser = null;
  stopMediaStream();
  saveState();
  renderLayout();
});

resetDemoBtn.addEventListener("click", () => {
  stopMediaStream();
  resetDemoState();
  commentResult.classList.remove("muted");
  commentResult.textContent = "Da reset toan bo du lieu demo ve trang thai ban dau.";
  messageResult.classList.remove("muted");
  messageResult.textContent = "Hoi thoai da duoc reset.";
  setDeviceStatus("Chua cap quyen camera va micro.", true);
  setStaffAction("Da reset du lieu demo.", false);
  renderLayout();
});

connectMediaBtn.addEventListener("click", async () => {
  await connectMediaDevices();
});

toggleCameraBtn.addEventListener("click", () => {
  toggleTrack("video");
});

toggleMicBtn.addEventListener("click", () => {
  toggleTrack("audio");
});

startLiveBtn.addEventListener("click", () => {
  const liveStatus = getSelectedLiveStatus();
  liveStatus.isLive = true;
  liveStatus.viewerCount += 12;
  saveState();
  setStaffAction("Da bat dau phien livestream demo.", false);
  renderLayout();
});

endLiveBtn.addEventListener("click", () => {
  const liveStatus = getSelectedLiveStatus();
  liveStatus.isLive = false;
  saveState();
  setStaffAction("Da ket thuc phien livestream demo.", false);
  renderLayout();
});

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  renderCustomerSearchAndRecommendations(searchInput.value.trim());
});

searchList.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;

  const liveButton = target.closest(".select-live-btn");
  if (liveButton) {
    const liveId = liveButton.dataset.liveId;
    if (!liveId) return;
    selectedLiveId = liveId;
    saveState();
    renderLayout();
    return;
  }

  const productButton = target.closest(".focus-product-btn");
  if (productButton) {
    const productId = productButton.dataset.productId;
    if (!productId) return;
    const product = getProductById(productId);
    if (product?.liveIds?.length) {
      selectedLiveId = product.liveIds[0];
    }
    renderLayout();
    commentProductSelect.value = productId;
    searchResult.classList.remove("muted");
    searchResult.textContent = "Da chon san pham vao khung comment de ban tiep tuc thao tac nhanh.";
    saveState();
  }
});

commentForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!currentUser) return;

  const selectedLive = getSelectedLive();
  if (currentUser.role === "customer" && isBlocked(selectedLive.id, currentUser.id)) {
    commentResult.classList.remove("muted");
    commentResult.textContent = "Ban dang bi chan trong phien live nay nen khong the gui them comment.";
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
    liveSessionId: selectedLive.id,
    userId: currentUser.role === "staff" ? "staff-01" : currentUser.id,
    productId: commentProductSelect.value,
    content,
    createdAt: new Date().toISOString(),
    intent: analyzeBuyingIntent(content),
  };

  appState.comments.unshift(comment);
  const liveStatus = getSelectedLiveStatus();
  liveStatus.viewerCount += currentUser.role === "customer" ? 1 : 0;

  if (currentUser.role === "customer") {
    handleAutoMlFromComment(comment);
  }

  commentInput.value = "";
  saveState();
  commentResult.classList.remove("muted");
  commentResult.textContent = "Comment da duoc dua vao live feed ngay lap tuc.";
  renderLayout();
});

document.body.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;

  const blockButton = target.closest(".viewer-block-btn");
  if (blockButton) {
    const liveId = blockButton.dataset.liveId;
    const userId = blockButton.dataset.userId;
    if (!liveId || !userId) return;

    const key = buildRegistryKey(liveId, userId);
    if (appState.blockedUsers[key]) {
      delete appState.blockedUsers[key];
      setStaffAction(`Da bo chan ${getUserById(userId)?.name || "khach hang"} trong phien live.`, false);
    } else {
      appState.blockedUsers[key] = {
        createdAt: new Date().toISOString(),
      };
      setStaffAction(`Da chan ${getUserById(userId)?.name || "khach hang"} trong phien live.`, false);
    }

    saveState();
    renderLayout();
    return;
  }

  const pinButton = target.closest(".pin-product-btn");
  if (pinButton) {
    const productId = pinButton.dataset.productId;
    if (!productId) return;
    getSelectedLiveStatus().pinnedProductId = productId;
    saveState();
    setStaffAction("Da cap nhat san pham dang ghim tren live.", false);
    renderLayout();
    return;
  }

  const quickMessageButton = target.closest(".quick-message-btn");
  if (quickMessageButton) {
    const userId = quickMessageButton.dataset.userId;
    if (!userId) return;
    selectedConversationCustomerId = userId;
    saveSessionState();
    messageResult.classList.remove("muted");
    messageResult.textContent = "Da mo hoi thoai voi khach ngay tu feed comment.";
    renderLayout();
    return;
  }

  const conversationButton = target.closest(".conversation-item");
  if (conversationButton) {
    const customerId = conversationButton.dataset.customerId;
    if (!customerId) return;
    selectedConversationCustomerId = customerId;
    saveSessionState();
    renderLayout();
  }
});

messageForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!currentUser) return;

  const content = messageInput.value.trim();
  if (!content) {
    messageResult.classList.remove("muted");
    messageResult.textContent = "Vui long nhap noi dung tin nhan truoc khi gui.";
    return;
  }

  const customerId = getSelectedConversationCustomerId();
  const liveSessionId = selectedLiveId;

  if (currentUser.role === "staff") {
    appendMessage(customerId, {
      senderId: "staff-01",
      receiverId: customerId,
      liveSessionId,
      direction: "outbound",
      source: "manual",
      content,
      createdAt: new Date().toISOString(),
    });
  } else {
    appendMessage(currentUser.id, {
      senderId: currentUser.id,
      receiverId: "staff-01",
      liveSessionId,
      direction: "inbound",
      source: "manual",
      content,
      createdAt: new Date().toISOString(),
    });
    handleAutoMlFromMessage(currentUser.id, liveSessionId, content, `msg-source-${Date.now()}`);
  }

  messageInput.value = "";
  saveState();
  messageResult.classList.remove("muted");
  messageResult.textContent = "Tin nhan da duoc gui thanh cong.";
  renderLayout();
});

window.addEventListener("beforeunload", () => {
  stopMediaStream();
});

window.addEventListener("storage", (event) => {
  if (event.key !== STATE_KEY) return;
  const nextState = event.newValue ? JSON.parse(event.newValue) : structuredClone(INITIAL_STATE);
  applySharedState(nextState);
  renderLayout();
});

loadState();
if (!appState.comments?.length) {
  resetDemoState();
  loadState();
}
setDeviceStatus("Chua cap quyen camera va micro.", true);
setStaffAction("App demo da san sang cho nhan vien va khach hang.", true);
renderLayout();
