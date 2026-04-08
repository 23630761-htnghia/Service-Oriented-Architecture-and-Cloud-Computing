const API_BASE = "http://localhost:8000";
const SESSION_KEY = "smartlive-session";
const AUTH_LOCK_CLASS = "auth-locked";

const authScreen = document.getElementById("auth-screen");
const dashboardScreen = document.getElementById("dashboard-screen");
const gatewayStatus = document.getElementById("gateway-status");
const aiStatus = document.getElementById("ai-status");
const userStatus = document.getElementById("user-status");
const sidebarUserName = document.getElementById("sidebar-user-name");
const sidebarUserRole = document.getElementById("sidebar-user-role");
const topbarSubtitle = document.getElementById("topbar-subtitle");
const loginForm = document.getElementById("login-form");
const loginResult = document.getElementById("login-result");
const logoutBtn = document.getElementById("logout-btn");
const sessionCard = document.getElementById("session-card");
const platformSummary = document.getElementById("platform-summary");
const kpiGrid = document.getElementById("kpi-grid");
const overviewHighlight = document.getElementById("overview-highlight");
const accountForm = document.getElementById("account-form");
const accountFormResult = document.getElementById("account-form-result");
const accountsResult = document.getElementById("accounts-result");
const productsResult = document.getElementById("products-result");
const suppliersResult = document.getElementById("suppliers-result");
const offersResult = document.getElementById("offers-result");
const commentForm = document.getElementById("comment-form");
const commentInput = document.getElementById("comment-input");
const commentResult = document.getElementById("comment-result");
const viewerForm = document.getElementById("viewer-form");
const viewerResult = document.getElementById("viewer-result");
const accountASelect = document.getElementById("account-a-select");
const accountBSelect = document.getElementById("account-b-select");
const navLinks = document.querySelectorAll(".nav-link");
const tabPanels = document.querySelectorAll(".tab-panel");

let currentSession = null;
let livestreamAccounts = [];

function formatRole(role) {
  if (role === "admin") return "Quản trị vận hành";
  if (role === "staff") return "Nhân sự bán hàng";
  return role;
}

function formatStatus(status) {
  if (status === "active") return "Hoạt động";
  if (status === "stable") return "Ổn định";
  if (status === "warning") return "Cảnh báo";
  if (status === "completed") return "Hoàn tất";
  if (status === "queued") return "Đang chờ";
  if (status === "scheduled") return "Đã lên lịch";
  if (status === "failed") return "Lỗi";
  return status;
}

function lockToAuthScreen() {
  document.body.classList.add(AUTH_LOCK_CLASS);
  authScreen.classList.remove("hidden");
  dashboardScreen.classList.add("hidden");
}

function unlockDashboard() {
  document.body.classList.remove(AUTH_LOCK_CLASS);
  authScreen.classList.add("hidden");
  dashboardScreen.classList.remove("hidden");
}

function resetDashboardState() {
  livestreamAccounts = [];
  gatewayStatus.textContent = "Chờ đăng nhập";
  aiStatus.textContent = "Chờ đăng nhập";
  userStatus.textContent = "Chưa đăng nhập";
  sidebarUserName.textContent = "Chưa đăng nhập";
  sidebarUserRole.textContent = "Khách";
  topbarSubtitle.textContent = "Đăng nhập để bắt đầu phiên làm việc.";
  platformSummary.classList.add("muted");
  platformSummary.textContent = "Vui lòng đăng nhập để xem thống kê nền tảng.";
  kpiGrid.classList.add("muted");
  kpiGrid.textContent = "Thông tin KPI sẽ hiển thị sau khi đăng nhập.";
  overviewHighlight.textContent = "Đăng nhập để xem dữ liệu vận hành theo thời gian thực.";
  accountsResult.classList.add("muted");
  accountsResult.textContent = "Đăng nhập để xem danh sách tài khoản livestream.";
  productsResult.classList.add("muted");
  productsResult.textContent = "Đăng nhập để xem danh mục sản phẩm.";
  offersResult.classList.add("muted");
  offersResult.textContent = "Đăng nhập để xem các offer hiện hành.";
  suppliersResult.classList.add("muted");
  suppliersResult.textContent = "Đăng nhập để xem danh sách nhà cung cấp.";
  commentResult.classList.add("muted");
  commentResult.textContent = "Kết quả phân tích sẽ xuất hiện tại đây sau khi đăng nhập.";
  viewerResult.classList.add("muted");
  viewerResult.textContent = "Đề xuất phân bổ viewer sẽ hiển thị tại đây sau khi đăng nhập.";
  accountFormResult.classList.add("muted");
  accountFormResult.textContent = "Bạn có thể thêm phòng live mới để cập nhật lại danh sách vận hành.";
  sessionCard.classList.add("muted");
  sessionCard.textContent = "Phiên làm việc chưa được khởi tạo.";
  accountASelect.innerHTML = "";
  accountBSelect.innerHTML = "";
}

function setSession(session) {
  currentSession = session;
  if (session) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  } else {
    localStorage.removeItem(SESSION_KEY);
  }
  syncSessionUI();
}

function syncSessionUI() {
  if (!currentSession) {
    lockToAuthScreen();
    resetDashboardState();
    return;
  }

  unlockDashboard();
  userStatus.textContent = `${currentSession.user.name} (${currentSession.user.role})`;
  sidebarUserName.textContent = currentSession.user.name;
  sidebarUserRole.textContent = formatRole(currentSession.user.role);
  topbarSubtitle.textContent = `${currentSession.user.name} đang theo dõi hiệu suất hệ thống, hàng hóa và nhà cung cấp trong ca trực hiện tại.`;
  sessionCard.classList.remove("muted");
  sessionCard.innerHTML = `<strong>${currentSession.user.name}</strong><br /><span>${currentSession.user.email}</span><br /><span>${formatRole(currentSession.user.role)}</span><br /><span>Phiên đã được xác thực thành công.</span>`;
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${path}`);
  }
  return response.json();
}

async function fetchGatewayHealth() {
  if (!currentSession) {
    gatewayStatus.textContent = "Chờ đăng nhập";
    aiStatus.textContent = "Chờ đăng nhập";
    return;
  }

  try {
    const data = await fetchJson("/health");
    gatewayStatus.textContent = data.status;
    aiStatus.textContent = [
      data.dependencies?.ai_service?.status || "unknown",
      data.dependencies?.auth_service?.status || "unknown",
      data.dependencies?.account_service?.status || "unknown",
    ].join(" / ");
  } catch (error) {
    gatewayStatus.textContent = "unreachable";
    aiStatus.textContent = "unreachable";
  }
}

function renderKpis(summary, overview) {
  const activeOffers = overview.supplier_offers.filter((offer) => offer.status === "active").length;
  const totalInventory = overview.products.reduce((total, item) => total + item.stock_quantity, 0);
  const totalViewers = summary.reduce((total, item) => total + item.total_viewers, 0);
  const warningRooms = overview.livestream_accounts.filter((item) => item.status === "warning").length;
  kpiGrid.classList.remove("muted");
  kpiGrid.innerHTML = [
    { label: "Viewer realtime", value: totalViewers.toLocaleString("vi-VN"), note: "Tổng viewer đang có trên toàn hệ thống" },
    { label: "Offer active", value: activeOffers.toString(), note: "Ưu đãi nhập hàng đang hiệu lực" },
    { label: "Tồn kho sẵn bán", value: totalInventory.toLocaleString("vi-VN"), note: "Tổng đơn vị sản phẩm trong kho" },
    { label: "Room cảnh báo", value: warningRooms.toString(), note: "Phòng live đang có mức lag cần theo dõi" },
  ].map((item) => `<article class="kpi-card"><span>${item.label}</span><strong>${item.value}</strong><p>${item.note}</p></article>`).join("");
  const topPlatform = [...summary].sort((a, b) => b.total_viewers - a.total_viewers)[0];
  overviewHighlight.textContent = `${topPlatform.display_name} đang dẫn đầu với ${topPlatform.total_viewers.toLocaleString("vi-VN")} viewer realtime trên ${topPlatform.total_accounts} phòng live. Hệ thống hiện có ${warningRooms} room cần theo dõi tín hiệu lag.`;
}

function renderPlatformSummary(items) {
  platformSummary.classList.remove("muted");
  platformSummary.innerHTML = items.map((item) => `<article class="kpi-card"><span>${item.display_name}</span><strong>${item.total_accounts}</strong><p>${item.total_viewers.toLocaleString("vi-VN")} / ${item.total_capacity.toLocaleString("vi-VN")} viewer | lag TB ${item.average_lag_signal}</p></article>`).join("");
}

function renderAccounts(groups) {
  accountsResult.classList.remove("muted");
  accountsResult.innerHTML = groups.map((group) => `<section class="account-table-card"><h3>${group.display_name}</h3><p class="table-subline">${group.summary.total_accounts} phòng live | ${group.summary.total_viewers.toLocaleString("vi-VN")} viewer realtime</p><div class="account-cards">${group.accounts.map((account) => `<article class="account-table-card"><h3>${account.name}</h3><p>${account.owner_name} - ${account.shift_label}</p><div class="table-meta"><span><strong>${account.current_viewers}</strong> / ${account.max_capacity} viewer</span><span>${account.username}</span><span>${account.warehouse_location}</span><span class="tag ${account.status}">${formatStatus(account.status)}</span></div></article>`).join("")}</div></section>`).join("");
}

function renderProducts(products) {
  productsResult.classList.remove("muted");
  productsResult.innerHTML = `<div class="product-grid">${products.map((item) => `<article class="product-card"><h3>${item.name}</h3><p>${item.brand} - ${item.category}</p><div class="product-meta"><span>SKU: ${item.sku}</span><span>Giá bán: ${item.retail_price.toLocaleString("vi-VN")} đ</span><span>Giá vốn: ${item.cost_price.toLocaleString("vi-VN")} đ</span><span>Tồn kho: ${item.stock_quantity} ${item.unit}</span></div></article>`).join("")}</div>`;
}

function renderOffers(offers) {
  offersResult.classList.remove("muted");
  offersResult.innerHTML = `<div class="offer-grid">${offers.map((item) => `<article class="offer-card"><h3>${item.offer_title}</h3><p>${item.supplier_name}</p><div class="offer-meta"><span>Sản phẩm: ${item.product_name}</span><span>MOQ: ${item.min_order_quantity}</span><span>Giá nhập: ${item.unit_price.toLocaleString("vi-VN")} đ</span><span>Chiết khấu: ${item.discount_percent}%</span><span class="tag ${item.status}">${formatStatus(item.status)}</span></div></article>`).join("")}</div>`;
}

function renderSuppliers(suppliers) {
  suppliersResult.classList.remove("muted");
  suppliersResult.innerHTML = `<div class="supplier-grid">${suppliers.map((item) => `<article class="supplier-card"><h3>${item.name}</h3><p>${item.contact_name}</p><div class="supplier-meta"><span>${item.phone}</span><span>${item.email}</span><span>${item.address}</span><span>Rating: ${item.rating}/5</span><span>Lead time: ${item.lead_time_days} ngày</span></div></article>`).join("")}</div>`;
}

function fillAccountSelectors(accounts) {
  const options = accounts.map((account) => `<option value="${account.account_id}">${account.name} (${account.platform_display_name} - ${account.owner_name})</option>`).join("");
  accountASelect.innerHTML = options;
  accountBSelect.innerHTML = options;
  if (accounts[0]) accountASelect.value = accounts[0].account_id;
  if (accounts[1]) accountBSelect.value = accounts[1].account_id;
}

function renderCommentResult(data) {
  commentResult.classList.remove("muted");
  commentResult.innerHTML = `<strong>Intent:</strong> ${data.intent}<br /><strong>Sentiment:</strong> ${data.sentiment}<br /><strong>Lead score:</strong> ${data.lead_score}<br /><strong>Priority:</strong> ${data.priority}<br /><strong>Suggested action:</strong> ${data.suggested_action}<ul class="result-list">${data.reasons.map((reason) => `<li>${reason}</li>`).join("")}</ul>`;
}

function renderViewerResult(data) {
  viewerResult.classList.remove("muted");
  const allocations = data.allocations.map((item) => `<li><strong>${item.account_id}</strong>: target ${item.target_viewers} viewer, delta ${item.viewer_delta}, <span class="risk-${item.lag_risk}">${item.lag_risk}</span></li>`).join("");
  const transfers = data.transfer_plan.length ? data.transfer_plan.map((item) => `<li>Chuyển ${item.viewers_to_shift} viewer từ <strong>${item.from_account_id}</strong> sang <strong>${item.to_account_id}</strong>.</li>`).join("") : "<li>Không cần chuyển viewer trong cửa sổ hiện tại.</li>";
  viewerResult.innerHTML = `<strong>Tóm tắt:</strong> ${data.summary}<br /><strong>Room ưu tiên nhận viewer:</strong> ${data.recommended_entry_account_id}<h4>Phân bổ đề xuất</h4><ul class="result-list">${allocations}</ul><h4>Kế hoạch điều hướng</h4><ul class="result-list">${transfers}</ul>`;
}

async function loadDashboardData() {
  if (!currentSession) {
    resetDashboardState();
    return;
  }

  const [summary, overview, groups, products, suppliers, offers] = await Promise.all([
    fetchJson("/api/v1/platform-summaries"),
    fetchJson("/api/v1/database-overview"),
    fetchJson("/api/v1/livestream-accounts/grouped"),
    fetchJson("/api/v1/products"),
    fetchJson("/api/v1/suppliers"),
    fetchJson("/api/v1/supplier-offers"),
  ]);
  livestreamAccounts = overview.livestream_accounts;
  renderPlatformSummary(summary);
  renderKpis(summary, overview);
  renderAccounts(groups);
  renderProducts(products);
  renderOffers(offers);
  renderSuppliers(suppliers);
  fillAccountSelectors(livestreamAccounts);
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginResult.textContent = "Đang xác thực tài khoản...";
  try {
    const data = await fetchJson("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: document.getElementById("login-email").value.trim(), password: document.getElementById("login-password").value }),
    });
    setSession(data);
    loginResult.classList.remove("muted");
    loginResult.innerHTML = `<strong>Đăng nhập thành công</strong><br />${data.user.name} - ${data.user.email}<br />Vai trò: ${formatRole(data.user.role)}`;
    await Promise.all([fetchGatewayHealth(), loadDashboardData()]);
  } catch (error) {
    lockToAuthScreen();
    loginResult.textContent = "Đăng nhập thất bại. Vui lòng kiểm tra email hoặc mật khẩu.";
  }
});

logoutBtn.addEventListener("click", () => {
  setSession(null);
  lockToAuthScreen();
});

accountForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  accountFormResult.textContent = "Đang tạo phòng livestream...";
  const payload = {
    name: document.getElementById("account-name").value.trim(),
    platform: document.getElementById("account-platform").value,
    username: document.getElementById("account-username").value.trim(),
    owner_name: document.getElementById("account-owner").value.trim(),
    owner_user_id: "user-admin",
    backup_contact: document.getElementById("account-backup").value.trim(),
    current_viewers: Number(document.getElementById("account-viewers").value),
    max_capacity: Number(document.getElementById("account-capacity").value),
    engagement_rate: Number(document.getElementById("account-engagement").value),
    lag_signal: Number(document.getElementById("account-lag").value),
    status: document.getElementById("account-status").value,
    stream_url: document.getElementById("account-stream-url").value.trim(),
    warehouse_location: document.getElementById("account-warehouse").value.trim(),
    shift_label: document.getElementById("account-shift").value.trim(),
  };
  try {
    const created = await fetchJson("/api/v1/livestream-accounts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    accountFormResult.classList.remove("muted");
    accountFormResult.innerHTML = `Đã tạo phòng <strong>${created.name}</strong> với mã <strong>${created.account_code}</strong> tại <strong>${created.platform_display_name}</strong>.`;
    accountForm.reset();
    document.getElementById("account-viewers").value = 350;
    document.getElementById("account-capacity").value = 1400;
    document.getElementById("account-engagement").value = 0.62;
    document.getElementById("account-lag").value = 0.14;
    await loadDashboardData();
  } catch (error) {
    accountFormResult.textContent = "Không thể tạo phòng livestream. Hãy kiểm tra lại thông tin nhập.";
  }
});

commentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  commentResult.textContent = "Đang phân tích comment...";
  try {
    const data = await fetchJson("/api/v1/comments/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ comment: commentInput.value.trim() }) });
    renderCommentResult(data);
  } catch (error) {
    commentResult.textContent = "Không thể phân tích comment.";
  }
});

viewerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  viewerResult.textContent = "Đang tính toán phân bổ viewer...";
  const accounts = [accountASelect.value, accountBSelect.value].map((accountId) => livestreamAccounts.find((item) => item.account_id === accountId)).filter(Boolean);
  if (accounts.length < 2) {
    viewerResult.textContent = "Cần chọn đủ 2 phòng live để tính toán.";
    return;
  }
  try {
    const data = await fetchJson("/api/v1/streams/balance-viewers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ incoming_viewers: Number(document.getElementById("incoming-viewers").value), accounts: accounts.map((account) => ({ account_id: account.account_id, platform: account.platform, current_viewers: account.current_viewers, max_capacity: account.max_capacity, engagement_rate: account.engagement_rate, lag_signal: account.lag_signal })) }),
    });
    renderViewerResult(data);
  } catch (error) {
    viewerResult.textContent = "Không thể tính cân bằng viewer.";
  }
});

navLinks.forEach((button) => {
  button.addEventListener("click", () => {
    navLinks.forEach((item) => item.classList.remove("active"));
    tabPanels.forEach((panel) => panel.classList.add("hidden"));
    button.classList.add("active");
    document.getElementById(`tab-${button.dataset.tab}`).classList.remove("hidden");
  });
});

localStorage.removeItem(SESSION_KEY);
lockToAuthScreen();
resetDashboardState();
