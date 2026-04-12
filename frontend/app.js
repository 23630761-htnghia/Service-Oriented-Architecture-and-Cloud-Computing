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
const loginEmail = document.getElementById("login-email");
const loginPassword = document.getElementById("login-password");
const loginResult = document.getElementById("login-result");
const captchaImage = document.getElementById("captcha-image");
const captchaExpiry = document.getElementById("captcha-expiry");
const captchaAnswer = document.getElementById("captcha-answer");
const refreshCaptchaBtn = document.getElementById("refresh-captcha");
const demoAccountButtons = document.querySelectorAll(".demo-account-btn");
const logoutBtn = document.getElementById("logout-btn");
const menuScreen = document.getElementById("menu-screen");
const detailScreen = document.getElementById("detail-screen");
const backToMenuBtn = document.getElementById("back-to-menu-btn");
const sessionCard = document.getElementById("session-card");
const platformSummary = document.getElementById("platform-summary");
const kpiGrid = document.getElementById("kpi-grid");
const overviewHighlight = document.getElementById("overview-highlight");
const accountForm = document.getElementById("account-form");
const accountFormResult = document.getElementById("account-form-result");
const accountsResult = document.getElementById("accounts-result");
const staffCreateForm = document.getElementById("staff-create-form");
const staffCreateResult = document.getElementById("staff-create-result");
const staffCredentialsResult = document.getElementById("staff-credentials-result");
const staffSearchInput = document.getElementById("staff-search-input");
const staffAssignmentResult = document.getElementById("staff-assignment-result");
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
const menuCards = document.querySelectorAll(".menu-card");
const tabPanels = document.querySelectorAll(".tab-panel");
const topbarStatus = document.querySelector(".topbar-status");
const platformSummaryPanel = platformSummary.closest(".panel");
const accountFormPanel = accountForm.closest(".panel");
const accountsListPanel = accountsResult.closest(".panel");
const staffCredentialsPanel = document.getElementById("staff-credentials-panel");
const staffAssignmentPanel = document.getElementById("staff-assignment-panel");
const adminAccountModePanel = document.getElementById("admin-account-mode-panel");
const adminAccountModeButtons = document.querySelectorAll("[data-admin-account-mode]");
const manageAccountSwitcherPanel = document.getElementById("manage-account-switcher-panel");
const manageAccountSectionButtons = document.querySelectorAll("[data-manage-account-section]");
const suppliersMenuCard = document.querySelector('.menu-card[data-tab="suppliers"]');
const aiToolsMenuCard = document.querySelector('.menu-card[data-tab="ai-tools"]');

let activeTab = null;

let currentSession = null;
let livestreamAccounts = [];
let currentCaptcha = null;
let captchaCountdownTimer = null;
let captchaLoadRequestId = 0;
let staffCredentialFlashMessage = "";
let accountManagementFlashMessage = "";
let adminAccountsMode = "view";
let adminManageSection = "room-create";
let activeStaffAssignmentUserId = null;
let currentUsers = [];

function applyDemoCredentials(email, password) {
  loginEmail.value = email;
  loginPassword.value = password;
  captchaAnswer.focus();
}

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

function formatHealthStatus(status) {
  if (status === "ok") return "Đang hoạt động";
  if (status === "unreachable") return "Mất kết nối";
  if (status === "unknown") return "Chưa xác định";
  return status;
}

function normalizeSearchText(value) {
  return (value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function isAdminSession() {
  return currentSession?.user?.role === "admin";
}

function isStaffSession() {
  return currentSession?.user?.role === "staff";
}

function setAdminManageSection(section = "room-create") {
  adminManageSection = section;

  manageAccountSectionButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.manageAccountSection === section);
  });

  if (!isAdminSession() || adminAccountsMode !== "manage") {
    manageAccountSwitcherPanel.classList.add("hidden");
    accountFormPanel.classList.add("hidden");
    accountsListPanel.classList.add("hidden");
    staffCredentialsPanel.classList.add("hidden");
    return;
  }

  manageAccountSwitcherPanel.classList.remove("hidden");
  accountFormPanel.classList.toggle("hidden", section !== "room-create");
  accountsListPanel.classList.toggle("hidden", section !== "room-list");
  staffCredentialsPanel.classList.toggle("hidden", section !== "staff");
}

function setAdminAccountsMode(mode = "view") {
  adminAccountsMode = mode;
  const viewMode = mode === "view";

  adminAccountModeButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.adminAccountMode === mode);
  });

  if (!isAdminSession()) {
    adminAccountModePanel.classList.add("hidden");
    staffAssignmentPanel.classList.add("hidden");
    manageAccountSwitcherPanel.classList.add("hidden");
    accountFormPanel.classList.add("hidden");
    accountsListPanel.classList.remove("hidden");
    staffCredentialsPanel.classList.add("hidden");
    return;
  }

  adminAccountModePanel.classList.remove("hidden");
  staffAssignmentPanel.classList.toggle("hidden", !viewMode);
  setAdminManageSection(adminManageSection);
}

function getOwnedAccounts(accounts = livestreamAccounts) {
  if (!isStaffSession()) return accounts;
  return accounts.filter((account) => account.owner_user_id === currentSession.user.id);
}

function inferRelevantCategoryKeys(accounts) {
  const rules = [
    { category: "Chăm sóc da", keywords: ["beauty", "cham soc da", "skincare", "lumiskin"] },
    { category: "Mẹ và bé", keywords: ["me bim", "me va be", "mom", "babynest"] },
    { category: "Gia dụng", keywords: ["gia dung", "nha cua", "homeset"] },
    { category: "Phụ kiện công nghệ", keywords: ["cong nghe", "techgo"] },
    { category: "Thời trang nữ", keywords: ["thoi trang", "urbanflex", "fashion", "outfit"] },
  ];
  const categoryKeys = new Set();
  for (const account of accounts) {
    const haystack = normalizeSearchText(`${account.name} ${account.platform_display_name} ${account.username}`);
    for (const rule of rules) {
      if (rule.keywords.some((keyword) => haystack.includes(keyword))) {
        categoryKeys.add(normalizeSearchText(rule.category));
      }
    }
  }
  return categoryKeys;
}

function getVisibleProducts(products) {
  if (!isStaffSession()) return products;
  const categoryKeys = inferRelevantCategoryKeys(getOwnedAccounts());
  if (!categoryKeys.size) return [];
  return products.filter((product) => categoryKeys.has(normalizeSearchText(product.category)));
}

function getVisibleOffers(offers, visibleProducts) {
  if (!isStaffSession()) return offers;
  const productIds = new Set(visibleProducts.map((product) => product.product_id));
  return offers.filter((offer) => productIds.has(offer.product_id));
}

function buildGroupedAccounts(accounts) {
  const grouped = new Map();
  accounts.forEach((account) => {
    if (!grouped.has(account.platform)) {
      grouped.set(account.platform, []);
    }
    grouped.get(account.platform).push(account);
  });
  return [...grouped.entries()].map(([platform, platformAccounts]) => {
    const totalViewers = platformAccounts.reduce((total, account) => total + account.current_viewers, 0);
    const totalCapacity = platformAccounts.reduce((total, account) => total + account.max_capacity, 0);
    const averageLag = platformAccounts.length
      ? (platformAccounts.reduce((total, account) => total + account.lag_signal, 0) / platformAccounts.length).toFixed(2)
      : "0.00";
    return {
      platform,
      display_name: platformAccounts[0].platform_display_name,
      accounts: platformAccounts,
      summary: {
        total_accounts: platformAccounts.length,
        total_viewers: totalViewers,
        total_capacity: totalCapacity,
        average_lag_signal: averageLag,
      },
    };
  });
}

function applyRoleBasedNavigation() {
  const adminMode = isAdminSession();
  suppliersMenuCard.classList.toggle("hidden", !adminMode);
  aiToolsMenuCard.classList.toggle("hidden", !adminMode);
  platformSummaryPanel.classList.toggle("hidden", !adminMode);
  topbarStatus.classList.toggle("hidden", !adminMode);
  setAdminAccountsMode(adminMode ? adminAccountsMode : "view");
}

function showMenuScreen() {
  activeTab = null;
  detailScreen.classList.add("hidden");
  menuScreen.classList.remove("hidden");
  tabPanels.forEach((panel) => panel.classList.add("hidden"));
}

function openTab(tabName) {
  activeTab = tabName;
  menuScreen.classList.add("hidden");
  detailScreen.classList.remove("hidden");
  tabPanels.forEach((panel) => panel.classList.add("hidden"));
  document.getElementById(`tab-${tabName}`).classList.remove("hidden");
  if (tabName === "accounts") {
    setAdminAccountsMode(isAdminSession() ? adminAccountsMode : "view");
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
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
  currentUsers = [];
  livestreamAccounts = [];
  staffCredentialFlashMessage = "";
  accountManagementFlashMessage = "";
  adminAccountsMode = "view";
  adminManageSection = "room-create";
  activeStaffAssignmentUserId = null;
  gatewayStatus.textContent = "Chưa đăng nhập";
  aiStatus.textContent = "Chưa đăng nhập";
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
  staffCredentialsResult.classList.add("muted");
  staffCredentialsResult.textContent = "Đăng nhập bằng admin để xem tài khoản nhân viên.";
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
  staffCreateResult.classList.add("muted");
  staffCreateResult.textContent = "Mỗi staff cần một mã duy nhất. Nếu mã đã tồn tại, chỉ có thể tạo lại sau khi xóa tài khoản cũ.";
  staffAssignmentResult.classList.add("muted");
  staffAssignmentResult.textContent = "Đăng nhập bằng admin để xem danh sách staff.";
  staffSearchInput.value = "";
  sessionCard.classList.add("muted");
  sessionCard.textContent = "Phiên làm việc chưa được khởi tạo.";
  accountASelect.innerHTML = "";
  accountBSelect.innerHTML = "";
  platformSummaryPanel.classList.remove("hidden");
  topbarStatus.classList.remove("hidden");
  suppliersMenuCard.classList.remove("hidden");
  aiToolsMenuCard.classList.remove("hidden");
  adminAccountModePanel.classList.add("hidden");
  staffAssignmentPanel.classList.add("hidden");
  manageAccountSwitcherPanel.classList.add("hidden");
  accountFormPanel.classList.remove("hidden");
  accountsListPanel.classList.remove("hidden");
  staffCredentialsPanel.classList.remove("hidden");
  showMenuScreen();
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
  applyRoleBasedNavigation();
  showMenuScreen();
  userStatus.textContent = `${currentSession.user.name} (${currentSession.user.role})`;
  sidebarUserName.textContent = currentSession.user.name;
  sidebarUserRole.textContent = formatRole(currentSession.user.role);
  topbarSubtitle.textContent = isAdminSession()
    ? `${currentSession.user.name} đang theo dõi hiệu suất hệ thống, hàng hóa và nhà cung cấp trong ca trực hiện tại.`
    : `${currentSession.user.name} đang theo dõi room được phân công, ca làm hiện tại và danh mục hàng hóa cần bán.`;
  sessionCard.classList.remove("muted");
  sessionCard.innerHTML = `<strong>${currentSession.user.name}</strong><br /><span>${currentSession.user.email}</span><br /><span>${formatRole(currentSession.user.role)}</span><br /><span>${currentSession.user.department}</span>`;
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${path}`);
  }
  return response.json();
}

function extractErrorMessage(error, fallback) {
  let message = String(error?.message || "").trim();
  const visited = new Set();

  while (message && !visited.has(message)) {
    visited.add(message);
    try {
      const parsed = JSON.parse(message);
      if (typeof parsed === "string") {
        message = parsed.trim();
        continue;
      }
      if (typeof parsed?.detail === "string") {
        message = parsed.detail.trim();
        continue;
      }
    } catch (parseError) {
      break;
    }
  }

  return message || fallback;
}

async function fetchGatewayHealth() {
  if (!currentSession) {
    gatewayStatus.textContent = "Chưa đăng nhập";
    aiStatus.textContent = "Chưa đăng nhập";
    return;
  }

  try {
    const data = await fetchJson("/health");
    gatewayStatus.textContent = formatHealthStatus(data.status);
    aiStatus.innerHTML = [
      `AI: ${formatHealthStatus(data.dependencies?.ai_service?.status || "unknown")}`,
      `Đăng nhập: ${formatHealthStatus(data.dependencies?.auth_service?.status || "unknown")}`,
      `Dữ liệu: ${formatHealthStatus(data.dependencies?.account_service?.status || "unknown")}`,
    ].join("<br />");
  } catch (error) {
    gatewayStatus.textContent = "Mất kết nối";
    aiStatus.innerHTML = "AI: Mất kết nối<br />Đăng nhập: Mất kết nối<br />Dữ liệu: Mất kết nối";
  }
}

async function loadCaptcha(options = {}) {
  const { autoRefresh = false } = options;
  const requestId = ++captchaLoadRequestId;
  if (captchaCountdownTimer) {
    clearInterval(captchaCountdownTimer);
    captchaCountdownTimer = null;
  }
  refreshCaptchaBtn.disabled = true;
  captchaImage.removeAttribute("src");
  captchaImage.alt = "Đang tải CAPTCHA";
  captchaExpiry.textContent = autoRefresh ? "CAPTCHA hết hạn, đang tự làm mới..." : "Đang đồng bộ mã xác thực";

  try {
    const captcha = await fetchJson("/api/v1/auth/captcha");
    if (requestId !== captchaLoadRequestId) return;

    currentCaptcha = captcha;
    captchaImage.src = `data:image/svg+xml;base64,${currentCaptcha.image_svg_base64}`;
    captchaImage.alt = "CAPTCHA đăng nhập";
    captchaAnswer.value = "";
    startCaptchaCountdown(currentCaptcha.expires_in_seconds);
  } catch (error) {
    if (requestId !== captchaLoadRequestId) return;

    currentCaptcha = null;
    captchaImage.alt = "Không thể tải CAPTCHA";
    captchaExpiry.textContent = autoRefresh ? "CAPTCHA hết hạn, chưa thể tự làm mới" : "Không thể tải CAPTCHA";
    throw error;
  } finally {
    if (requestId === captchaLoadRequestId) {
      refreshCaptchaBtn.disabled = false;
    }
  }
}

function startCaptchaCountdown(secondsRemaining) {
  let remaining = secondsRemaining;
  captchaExpiry.textContent = `Còn ${remaining} giây`;

  captchaCountdownTimer = setInterval(() => {
    remaining -= 1;
    if (remaining <= 0) {
      clearInterval(captchaCountdownTimer);
      captchaCountdownTimer = null;
      currentCaptcha = null;
      captchaExpiry.textContent = "CAPTCHA đã hết hạn, đang tự làm mới...";
      loadCaptcha({ autoRefresh: true }).catch(() => {
        loginResult.classList.remove("muted");
        loginResult.textContent = "CAPTCHA đã hết hạn. Vui lòng bấm làm mới.";
      });
      return;
    }
    captchaExpiry.textContent = `Còn ${remaining} giây`;
  }, 1000);
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

function renderStaffOverview(accounts, products, offers) {
  const shiftLabels = [...new Set(accounts.map((account) => account.shift_label))];
  const warehouses = [...new Set(accounts.map((account) => account.warehouse_location))];
  const totalViewers = accounts.reduce((total, account) => total + account.current_viewers, 0);
  const totalCapacity = accounts.reduce((total, account) => total + account.max_capacity, 0);
  const focusCategories = [...new Set(products.map((product) => product.category))];

  kpiGrid.classList.remove("muted");
  kpiGrid.innerHTML = [
    { label: "Ca làm", value: shiftLabels.join(", ") || "Chưa phân ca", note: "Khung giờ bạn đang được phân công" },
    { label: "Room phụ trách", value: String(accounts.length), note: "Số phòng livestream đang theo dõi" },
    { label: "Viewer hiện tại", value: totalViewers.toLocaleString("vi-VN"), note: `Tổng sức chứa ${totalCapacity.toLocaleString("vi-VN")} viewer` },
    { label: "Nhóm hàng", value: String(focusCategories.length), note: focusCategories.join(", ") || "Chưa có danh mục" },
  ].map((item) => `<article class="kpi-card"><span>${item.label}</span><strong>${item.value}</strong><p>${item.note}</p></article>`).join("");

  overviewHighlight.textContent = accounts.length
    ? `Bạn đang phụ trách ${accounts.map((account) => account.name).join(", ")} tại ${warehouses.join(", ")}. Danh mục trong ca hiện có ${products.length} sản phẩm và ${offers.length} offer liên quan.`
    : "Bạn chưa được phân công room livestream nào trong hệ thống.";

  sessionCard.classList.remove("muted");
  sessionCard.innerHTML = accounts.length
    ? `<strong>${currentSession.user.name}</strong><br /><span>${currentSession.user.email}</span><br /><span>${shiftLabels.join(", ")}</span><br /><span>${warehouses.join(", ")}</span><br /><span>Room phụ trách: ${accounts.map((account) => account.account_code).join(", ")}</span>`
    : `<strong>${currentSession.user.name}</strong><br /><span>${currentSession.user.email}</span><br /><span>Chưa có room được phân công.</span>`;
}

function renderStaffAssignments(users, accounts) {
  const query = normalizeSearchText(staffSearchInput.value);
  const staffUsers = users
    .filter((user) => user.role === "staff")
    .filter((user) => !query || normalizeSearchText(`${user.full_name} ${user.staff_code || ""} ${user.email}`).includes(query))
    .sort((left, right) => left.full_name.localeCompare(right.full_name, "vi"));

  if (!staffUsers.some((user) => user.user_id === activeStaffAssignmentUserId)) {
    activeStaffAssignmentUserId = null;
  }

  staffAssignmentResult.classList.remove("muted");
  if (!staffUsers.length) {
    staffAssignmentResult.innerHTML = query
      ? "Không tìm thấy staff phù hợp với từ khóa này."
      : "Chưa có staff nào trong hệ thống.";
    return;
  }

  staffAssignmentResult.innerHTML = `<div class="staff-assignment-list">${staffUsers.map((user) => {
    const assignedAccounts = accounts.filter((account) => account.owner_user_id === user.user_id);
    const isOpen = activeStaffAssignmentUserId === user.user_id;
    return `<article class="staff-assignment-card ${isOpen ? "is-open" : ""}"><button type="button" class="staff-assignment-toggle" data-user-id="${escapeHtml(user.user_id)}"><div><strong>${escapeHtml(user.full_name)}</strong><span>Mã staff: ${escapeHtml(user.staff_code || "Chưa gán")} | ${escapeHtml(user.department)}</span></div><div class="staff-assignment-summary"><strong>${assignedAccounts.length}</strong><span>room</span></div></button><div class="staff-assignment-body ${isOpen ? "" : "hidden"}"><div class="assignment-meta"><span>${escapeHtml(user.email)}</span><span>${escapeHtml(user.phone)}</span><span>${escapeHtml(user.status)}</span></div>${assignedAccounts.length ? `<div class="assignment-room-list">${assignedAccounts.map((account) => `<article class="assignment-room-card"><h3>${escapeHtml(account.name)}</h3><p>${escapeHtml(account.platform_display_name)} | ${escapeHtml(account.username)}</p><div class="table-meta"><span>Ca trực: ${escapeHtml(account.shift_label)}</span><span>Kho xử lý: ${escapeHtml(account.warehouse_location)}</span><span>Host chính: ${escapeHtml(account.owner_name)}</span><span class="tag ${account.status}">${formatStatus(account.status)}</span></div></article>`).join("")}</div>` : `<div class="inline-note muted">Staff này hiện chưa được phân công room livestream nào.</div>`}</div></article>`;
  }).join("")}</div>`;
}

function renderAccounts(groups) {
  accountsResult.classList.remove("muted");
  if (!groups.length) {
    accountsResult.innerHTML = "Bạn chưa được phân công phòng livestream nào.";
    return;
  }
  accountsResult.innerHTML = groups.map((group) => `<section class="account-table-card"><h3>${group.display_name}</h3><p class="table-subline">${group.summary.total_accounts} phòng live | ${group.summary.total_viewers.toLocaleString("vi-VN")} viewer realtime</p><div class="account-cards">${group.accounts.map((account) => `<article class="account-table-card"><h3>${account.name}</h3><p>${account.owner_name} - ${account.shift_label}</p><div class="table-meta"><span><strong>${account.current_viewers}</strong> / ${account.max_capacity} viewer</span><span>${account.username}</span><span>${account.warehouse_location}</span><span class="tag ${account.status}">${formatStatus(account.status)}</span></div>${isAdminSession() ? `<div class="credential-grid"><div class="credential-card"><span>Tài khoản live</span><strong>${account.username}</strong><small>Mật khẩu: ${account.password}</small></div><div class="credential-card"><span>Tài khoản nhân viên</span><strong>${account.owner_email || "Chưa gán"}</strong><small>Mật khẩu: ${account.owner_password || "Chưa gán"}</small></div></div>` : ""}</article>`).join("")}</div></section>`).join("");
}

function renderManagedAccounts(accounts) {
  const flashNote = accountManagementFlashMessage
    ? `<div class="inline-note">${escapeHtml(accountManagementFlashMessage)}</div>`
    : "";
  accountManagementFlashMessage = "";

  accountsResult.classList.remove("muted");
  if (!accounts.length) {
    accountsResult.innerHTML = `${flashNote}Chưa có phòng livestream nào trong hệ thống.`;
    return;
  }

  const sortedAccounts = [...accounts].sort((left, right) => {
    const platformCompare = left.platform_display_name.localeCompare(right.platform_display_name, "vi");
    if (platformCompare !== 0) return platformCompare;
    return left.name.localeCompare(right.name, "vi");
  });

  accountsResult.innerHTML = `${flashNote}<div class="account-cards">${sortedAccounts.map((account) => `<article class="account-table-card manage-account-card" data-account-id="${escapeHtml(account.account_id)}"><h3>${escapeHtml(account.name)}</h3><p>${escapeHtml(account.platform_display_name)} | ${escapeHtml(account.owner_name || "Chưa gán")}</p><div class="table-meta"><span>Username: ${escapeHtml(account.username)}</span><span>Ca trực: ${escapeHtml(account.shift_label)}</span><span>Kho xử lý: ${escapeHtml(account.warehouse_location)}</span><span><strong>${account.current_viewers}</strong> / ${account.max_capacity} viewer</span><span class="tag ${account.status}">${formatStatus(account.status)}</span></div><button type="button" class="ghost-btn danger-btn manage-account-delete-btn">Xóa phòng live</button><div class="staff-action-result muted">Admin có thể xóa room không còn sử dụng.</div></article>`).join("")}</div>`;
}

function renderStaffCredentials(users) {
  const staffUsers = users.filter((user) => user.role === "staff");
  staffCredentialsResult.classList.remove("muted");
  const flashNote = staffCredentialFlashMessage
    ? `<div class="inline-note">${escapeHtml(staffCredentialFlashMessage)}</div>`
    : "";
  staffCredentialFlashMessage = "";
  if (!staffUsers.length) {
    staffCredentialsResult.innerHTML = `${flashNote}Chưa có tài khoản nhân viên nào trong hệ thống.`;
    return;
  }
  staffCredentialsResult.innerHTML = `${flashNote}<div class="credential-grid">${staffUsers.map((user) => `<article class="credential-card staff-management-card" data-user-id="${escapeHtml(user.user_id)}"><span>${escapeHtml(user.full_name)}</span><strong>${escapeHtml(user.email)}</strong><small>Mã staff: ${escapeHtml(user.staff_code || "Chưa gán")}</small><small>Mật khẩu hiện tại: ${escapeHtml(user.password)}</small><small>Bộ phận: ${escapeHtml(user.department)}</small><form class="staff-password-form"><label>Mật khẩu mới<input name="password" type="text" value="${escapeHtml(user.password)}" minlength="3" required /></label><button type="submit" class="primary-btn staff-action-btn">Cập nhật mật khẩu</button></form><button type="button" class="ghost-btn danger-btn staff-delete-btn">Xóa tài khoản staff</button><div class="staff-action-result muted">Admin có thể cập nhật mật khẩu hoặc xóa tài khoản này.</div></article>`).join("")}</div>`;
}

async function handleStaffCreate() {
  if (!isAdminSession()) return;

  const payload = {
    staff_code: document.getElementById("staff-code").value.trim(),
    full_name: document.getElementById("staff-full-name").value.trim(),
    email: document.getElementById("staff-email").value.trim(),
    password: document.getElementById("staff-password").value.trim(),
    phone: document.getElementById("staff-phone").value.trim(),
    department: document.getElementById("staff-department").value.trim(),
  };

  staffCreateResult.classList.remove("muted");
  staffCreateResult.textContent = "Đang tạo tài khoản staff...";

  try {
    const createdUser = await fetchJson("/api/v1/users/staff", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    staffCreateResult.innerHTML = `Đã tạo staff <strong>${escapeHtml(createdUser.full_name)}</strong> với mã <strong>${escapeHtml(createdUser.staff_code || "")}</strong>.`;
    staffCreateForm.reset();
    document.getElementById("staff-password").value = "staff05";
    staffCredentialFlashMessage = `Đã thêm tài khoản ${createdUser.full_name} với mã ${createdUser.staff_code}.`;
    await loadDashboardData();
  } catch (error) {
    staffCreateResult.textContent = extractErrorMessage(error, "Không thể tạo tài khoản staff.");
  }
}

async function handleStaffPasswordUpdate(form) {
  if (!isAdminSession()) return;

  const card = form.closest(".staff-management-card");
  const userId = card?.dataset.userId;
  const passwordInput = form.querySelector('input[name="password"]');
  const submitButton = form.querySelector('button[type="submit"]');
  const resultBox = card?.querySelector(".staff-action-result");
  const nextPassword = passwordInput?.value.trim() || "";

  if (!userId || !passwordInput || !resultBox) return;
  if (nextPassword.length < 3) {
    resultBox.classList.remove("muted");
    resultBox.textContent = "Mật khẩu mới cần có ít nhất 3 ký tự.";
    passwordInput.focus();
    return;
  }

  submitButton.disabled = true;
  resultBox.classList.remove("muted");
  resultBox.textContent = "Đang cập nhật mật khẩu...";

  try {
    const updatedUser = await fetchJson(`/api/v1/users/${userId}/password`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: nextPassword }),
    });
    staffCredentialFlashMessage = `Đã cập nhật mật khẩu cho ${updatedUser.full_name}.`;
    await loadDashboardData();
  } catch (error) {
    resultBox.textContent = extractErrorMessage(error, "Không thể cập nhật mật khẩu cho tài khoản này.");
  } finally {
    submitButton.disabled = false;
  }
}

async function handleStaffDelete(button) {
  if (!isAdminSession()) return;

  const card = button.closest(".staff-management-card");
  const userId = card?.dataset.userId;
  const userEmail = card?.querySelector("strong")?.textContent || "tài khoản này";
  const resultBox = card?.querySelector(".staff-action-result");

  if (!userId || !resultBox) return;
  if (!window.confirm(`Bạn có chắc muốn xóa ${userEmail} khỏi hệ thống?`)) return;

  button.disabled = true;
  resultBox.classList.remove("muted");
  resultBox.textContent = "Đang xóa tài khoản staff...";

  try {
    const deletedUser = await fetchJson(`/api/v1/users/${userId}`, { method: "DELETE" });
    const reassignedMessage = deletedUser.reassigned_accounts
      ? ` Đã gỡ ${deletedUser.reassigned_accounts} phòng live khỏi tài khoản này.`
      : "";
    staffCredentialFlashMessage = `${deletedUser.message}${reassignedMessage}`;
    await loadDashboardData();
  } catch (error) {
    resultBox.textContent = extractErrorMessage(error, "Không thể xóa tài khoản staff này.");
  } finally {
    button.disabled = false;
  }
}

async function handleLivestreamAccountDelete(button) {
  if (!isAdminSession()) return;

  const card = button.closest(".manage-account-card");
  const accountId = card?.dataset.accountId;
  const accountName = card?.querySelector("h3")?.textContent || "phòng live này";
  const resultBox = card?.querySelector(".staff-action-result");

  if (!accountId || !resultBox) return;
  if (!window.confirm(`Bạn có chắc muốn xóa ${accountName} khỏi hệ thống?`)) return;

  button.disabled = true;
  resultBox.classList.remove("muted");
  resultBox.textContent = "Đang xóa phòng livestream...";

  try {
    const deletedAccount = await fetchJson(`/api/v1/livestream-accounts/${accountId}`, { method: "DELETE" });
    accountManagementFlashMessage = deletedAccount.message;
    await loadDashboardData();
  } catch (error) {
    resultBox.textContent = extractErrorMessage(error, "Không thể xóa phòng livestream này.");
  } finally {
    button.disabled = false;
  }
}

function renderProducts(products) {
  productsResult.classList.remove("muted");
  if (!products.length) {
    productsResult.innerHTML = "Chưa có sản phẩm nào được phân cho ca làm hiện tại.";
    return;
  }
  productsResult.innerHTML = `<div class="product-grid">${products.map((item) => `<article class="product-card"><h3>${item.name}</h3><p>${item.brand} - ${item.category}</p><div class="product-meta"><span>SKU: ${item.sku}</span><span>Giá bán: ${item.retail_price.toLocaleString("vi-VN")} đ</span><span>Giá vốn: ${item.cost_price.toLocaleString("vi-VN")} đ</span><span>Tồn kho: ${item.stock_quantity} ${item.unit}</span></div></article>`).join("")}</div>`;
}

function renderOffers(offers) {
  offersResult.classList.remove("muted");
  if (!offers.length) {
    offersResult.innerHTML = "Không có offer nào áp dụng cho room và ca làm hiện tại.";
    return;
  }
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
  currentUsers = overview.users;
  livestreamAccounts = isStaffSession() ? getOwnedAccounts(overview.livestream_accounts) : overview.livestream_accounts;
  const visibleProducts = getVisibleProducts(products);
  const visibleOffers = getVisibleOffers(offers, visibleProducts);

  if (isAdminSession()) {
    renderPlatformSummary(summary);
    renderKpis(summary, overview);
    renderStaffAssignments(overview.users, overview.livestream_accounts);
    renderManagedAccounts(overview.livestream_accounts);
    renderStaffCredentials(overview.users);
    renderSuppliers(suppliers);
    fillAccountSelectors(livestreamAccounts);
  } else {
    renderStaffOverview(livestreamAccounts, visibleProducts, visibleOffers);
    renderAccounts(buildGroupedAccounts(livestreamAccounts));
  }

  renderProducts(visibleProducts);
  renderOffers(visibleOffers);
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!currentCaptcha?.captcha_id) {
    loginResult.textContent = "CAPTCHA chưa sẵn sàng. Vui lòng làm mới và thử lại.";
    return;
  }
  loginResult.textContent = "Đang xác thực tài khoản...";
  try {
    const data = await fetchJson("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: loginEmail.value.trim(),
        password: loginPassword.value,
        captcha_id: currentCaptcha.captcha_id,
        captcha_answer: captchaAnswer.value.trim().toUpperCase(),
      }),
    });
    setSession(data);
    loginResult.classList.remove("muted");
    loginResult.innerHTML = `<strong>Đăng nhập thành công</strong><br />${data.user.name} - ${data.user.email}<br />Vai trò: ${formatRole(data.user.role)}`;
    await Promise.all([fetchGatewayHealth(), loadDashboardData()]);
  } catch (error) {
    lockToAuthScreen();
    loginResult.textContent = "Đăng nhập thất bại. Vui lòng kiểm tra email, mật khẩu và CAPTCHA.";
    await loadCaptcha();
  }
});

menuCards.forEach((button) => {
  button.addEventListener("click", () => {
    openTab(button.dataset.tab);
  });
});

adminAccountModeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setAdminAccountsMode(button.dataset.adminAccountMode);
  });
});

manageAccountSectionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setAdminManageSection(button.dataset.manageAccountSection);
  });
});

demoAccountButtons.forEach((button) => {
  button.addEventListener("click", () => {
    applyDemoCredentials(button.dataset.demoEmail, button.dataset.demoPassword);
  });
});

backToMenuBtn.addEventListener("click", () => {
  showMenuScreen();
});

refreshCaptchaBtn.addEventListener("click", async () => {
  try {
    await loadCaptcha();
  } catch (error) {
    loginResult.textContent = "Không thể tải CAPTCHA mới.";
  }
});

staffSearchInput.addEventListener("input", () => {
  if (!isAdminSession()) return;
  renderStaffAssignments(currentUsers, livestreamAccounts);
});

staffCreateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await handleStaffCreate();
});

staffAssignmentResult.addEventListener("click", (event) => {
  const toggleButton = event.target.closest(".staff-assignment-toggle");
  if (!toggleButton) return;
  const userId = toggleButton.dataset.userId;
  activeStaffAssignmentUserId = activeStaffAssignmentUserId === userId ? null : userId;
  renderStaffAssignments(currentUsers, livestreamAccounts);
});

staffCredentialsResult.addEventListener("submit", async (event) => {
  const form = event.target.closest(".staff-password-form");
  if (!form) return;
  event.preventDefault();
  await handleStaffPasswordUpdate(form);
});

staffCredentialsResult.addEventListener("click", async (event) => {
  const deleteButton = event.target.closest(".staff-delete-btn");
  if (!deleteButton) return;
  await handleStaffDelete(deleteButton);
});

accountsResult.addEventListener("click", async (event) => {
  const deleteButton = event.target.closest(".manage-account-delete-btn");
  if (!deleteButton) return;
  await handleLivestreamAccountDelete(deleteButton);
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
    password: document.getElementById("account-password").value.trim(),
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
    document.getElementById("account-password").value = "live123";
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

localStorage.removeItem(SESSION_KEY);
lockToAuthScreen();
resetDashboardState();
loadCaptcha().catch(() => {
  captchaImage.alt = "Không thể tải CAPTCHA";
  captchaExpiry.textContent = "Hãy kiểm tra auth-service rồi làm mới lại";
});
