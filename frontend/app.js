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
const accountPlatform = document.getElementById("account-platform");
const accountFormResult = document.getElementById("account-form-result");
const accountsResult = document.getElementById("accounts-result");
const accountsSearchInput = document.getElementById("accounts-search-input");
const staffCreateForm = document.getElementById("staff-create-form");
const staffRole = document.getElementById("staff-role");
const staffCreateResult = document.getElementById("staff-create-result");
const staffCredentialsResult = document.getElementById("staff-credentials-result");
const staffCredentialsSearchInput = document.getElementById("staff-credentials-search-input");
const staffSearchInput = document.getElementById("staff-search-input");
const staffAssignmentResult = document.getElementById("staff-assignment-result");
const productCreateForm = document.getElementById("product-create-form");
const productCreateResult = document.getElementById("product-create-result");
const productSearchInput = document.getElementById("product-search-input");
const productsResult = document.getElementById("products-result");
const assignmentCreateForm = document.getElementById("assignment-create-form");
const assignmentCreateResult = document.getElementById("assignment-create-result");
const assignmentAccountSelect = document.getElementById("assignment-account-id");
const assignmentProductSelect = document.getElementById("assignment-product-id");
const assignmentSearchInput = document.getElementById("assignment-search-input");
const productAssignmentResult = document.getElementById("product-assignment-result");
const supplierCreateForm = document.getElementById("supplier-create-form");
const supplierCreateResult = document.getElementById("supplier-create-result");
const supplierSearchInput = document.getElementById("supplier-search-input");
const suppliersResult = document.getElementById("suppliers-result");
const offerSearchInput = document.getElementById("offer-search-input");
const offersResult = document.getElementById("offers-result");
const aiSettingsForm = document.getElementById("ai-settings-form");
const aiEnabledInput = document.getElementById("ai-enabled");
const aiReplyTemplateInput = document.getElementById("ai-reply-template");
const aiSettingsResult = document.getElementById("ai-settings-result");
const menuCards = document.querySelectorAll(".menu-card");
const tabPanels = document.querySelectorAll(".tab-panel");
const topbarStatus = document.querySelector(".topbar-status");
const platformSummaryPanel = platformSummary.closest(".panel");
const accountFormPanel = accountForm.closest(".panel");
const accountsListPanel = accountsResult.closest(".panel");
const staffCredentialsPanel = document.getElementById("staff-credentials-panel");
const staffAssignmentPanel = document.getElementById("staff-assignment-panel");
const productManagementPanel = document.getElementById("product-management-panel");
const supplierManagementPanel = document.getElementById("supplier-management-panel");
const adminAccountModePanel = document.getElementById("admin-account-mode-panel");
const adminAccountModeButtons = document.querySelectorAll("[data-admin-account-mode]");
const manageAccountSwitcherPanel = document.getElementById("manage-account-switcher-panel");
const manageAccountSectionButtons = document.querySelectorAll("[data-manage-account-section]");
const catalogSectionButtons = document.querySelectorAll("[data-catalog-section]");
const catalogSections = document.querySelectorAll(".catalog-section");
const overviewMenuCard = document.querySelector('.menu-card[data-tab="overview"]');
const accountsMenuCard = document.querySelector('.menu-card[data-tab="accounts"]');
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
let productManagementFlashMessage = "";
let supplierManagementFlashMessage = "";
let productAssignmentFlashMessage = "";
let adminAccountsMode = "view";
let adminManageSection = "room-create";
let activeCatalogSection = "products";
let activeStaffAssignmentUserId = null;
let currentUsers = [];
let currentAssignments = [];
let currentAllAccounts = [];
let currentProducts = [];
let currentSuppliers = [];
let currentOffers = [];
let currentAiSettings = null;

function applyDemoCredentials(email, password) {
  loginEmail.value = email;
  loginPassword.value = password;
  captchaAnswer.focus();
}

if (accountPlatform && !accountPlatform.querySelector('option[value="demo_app"]')) {
  accountPlatform.insertAdjacentHTML("beforeend", '<option value="demo_app">Demo App</option>');
}

function formatRole(role) {
  if (role === "admin") return "Quản trị vận hành";
  if (role === "product_manager") return "Quản lý sản phẩm";
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

function includesSearch(value, query) {
  return normalizeSearchText(value).includes(query);
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

function isProductManagerSession() {
  return currentSession?.user?.role === "product_manager";
}

function canManageCatalog() {
  return isAdminSession() || isProductManagerSession();
}

function setCatalogSection(section = "products") {
  activeCatalogSection = section;

  catalogSectionButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.catalogSection === section);
  });

  catalogSections.forEach((panel) => {
    panel.classList.toggle("hidden", panel.id !== `catalog-${section}-section`);
  });
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

function buildAssignmentsByAccount(assignments = []) {
  const grouped = new Map();
  assignments.forEach((assignment) => {
    if (!grouped.has(assignment.account_id)) {
      grouped.set(assignment.account_id, []);
    }
    grouped.get(assignment.account_id).push(assignment);
  });
  return grouped;
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
  const productManagerMode = isProductManagerSession();
  const catalogManagerMode = canManageCatalog();

  overviewMenuCard.classList.toggle("hidden", productManagerMode);
  accountsMenuCard.classList.toggle("hidden", productManagerMode);
  suppliersMenuCard.classList.toggle("hidden", !(adminMode || productManagerMode));
  aiToolsMenuCard.classList.toggle("hidden", !adminMode);
  platformSummaryPanel.classList.toggle("hidden", !adminMode);
  topbarStatus.classList.toggle("hidden", !adminMode);
  productManagementPanel.classList.toggle("hidden", !catalogManagerMode);
  supplierManagementPanel.classList.toggle("hidden", !catalogManagerMode);
  assignmentCreateForm.classList.toggle("hidden", !catalogManagerMode);
  assignmentCreateResult.classList.toggle("hidden", !catalogManagerMode);
  setCatalogSection(activeCatalogSection);
  setAdminAccountsMode(adminMode ? adminAccountsMode : "view");
}

function filterAccountsBySearch(accounts, queryValue) {
  const query = normalizeSearchText(queryValue);
  if (!query) return accounts;
  return accounts.filter((account) => includesSearch(
    `${account.name} ${account.account_code} ${account.platform_display_name} ${account.username} ${account.owner_name} ${account.warehouse_location} ${account.shift_label}`,
    query,
  ));
}

function filterUsersBySearch(users, queryValue) {
  const query = normalizeSearchText(queryValue);
  if (!query) return users;
  return users.filter((user) => includesSearch(
    `${user.full_name} ${user.staff_code || ""} ${user.email} ${formatRole(user.role)} ${user.department} ${user.phone}`,
    query,
  ));
}

function filterProductsBySearch(products, queryValue) {
  const query = normalizeSearchText(queryValue);
  if (!query) return products;
  return products.filter((product) => includesSearch(
    `${product.name} ${product.sku} ${product.brand} ${product.category} ${product.description}`,
    query,
  ));
}

function filterOffersBySearch(offers, queryValue) {
  const query = normalizeSearchText(queryValue);
  if (!query) return offers;
  return offers.filter((offer) => includesSearch(
    `${offer.offer_title} ${offer.offer_code} ${offer.supplier_name} ${offer.product_name} ${offer.status}`,
    query,
  ));
}

function filterSuppliersBySearch(suppliers, queryValue) {
  const query = normalizeSearchText(queryValue);
  if (!query) return suppliers;
  return suppliers.filter((supplier) => includesSearch(
    `${supplier.name} ${supplier.supplier_code} ${supplier.contact_name} ${supplier.phone} ${supplier.email} ${supplier.address} ${supplier.status}`,
    query,
  ));
}

function filterAssignmentsBySearch(assignments, queryValue) {
  const query = normalizeSearchText(queryValue);
  if (!query) return assignments;
  return assignments.filter((assignment) => includesSearch(
    `${assignment.assignment_id} ${assignment.account_name} ${assignment.platform_display_name} ${assignment.product_name} ${assignment.product_sku} ${assignment.product_category} ${assignment.assigned_by_name || ""}`,
    query,
  ));
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
  if (tabName === "catalog") {
    setCatalogSection(activeCatalogSection);
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
  currentAssignments = [];
  currentAllAccounts = [];
  currentProducts = [];
  currentSuppliers = [];
  currentOffers = [];
  currentAiSettings = null;
  livestreamAccounts = [];
  staffCredentialFlashMessage = "";
  accountManagementFlashMessage = "";
  productManagementFlashMessage = "";
  supplierManagementFlashMessage = "";
  productAssignmentFlashMessage = "";
  adminAccountsMode = "view";
  adminManageSection = "room-create";
  activeCatalogSection = "products";
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
  staffCredentialsResult.textContent = "Đăng nhập bằng admin để xem tài khoản nội bộ.";
  productCreateResult.classList.add("muted");
  productCreateResult.textContent = "Admin hoặc quản lý sản phẩm có thể thêm mặt hàng mới tại đây.";
  productsResult.classList.add("muted");
  productsResult.textContent = "Đăng nhập để xem danh mục sản phẩm.";
  assignmentCreateResult.classList.add("muted");
  assignmentCreateResult.textContent = "Admin hoặc quản lý sản phẩm có thể gán sản phẩm cho từng phòng livestream.";
  productAssignmentResult.classList.add("muted");
  productAssignmentResult.textContent = "Đăng nhập để xem sản phẩm đã gán cho các phòng livestream.";
  supplierCreateResult.classList.add("muted");
  supplierCreateResult.textContent = "Admin hoặc quản lý sản phẩm có thể thêm nhà cung cấp mới tại đây.";
  offersResult.classList.add("muted");
  offersResult.textContent = "Đăng nhập để xem các offer hiện hành.";
  suppliersResult.classList.add("muted");
  suppliersResult.textContent = "Đăng nhập để xem danh sách nhà cung cấp.";
  accountFormResult.classList.add("muted");
  accountFormResult.textContent = "Bạn có thể thêm phòng live mới để cập nhật lại danh sách vận hành.";
  staffCreateResult.classList.add("muted");
  staffCreateResult.textContent = "Mỗi tài khoản nội bộ cần một mã duy nhất. Nếu mã đã tồn tại, chỉ có thể tạo lại sau khi xóa tài khoản cũ.";
  staffAssignmentResult.classList.add("muted");
  staffAssignmentResult.textContent = "Đăng nhập bằng admin để xem danh sách nhân viên livestream.";
  staffSearchInput.value = "";
  staffCredentialsSearchInput.value = "";
  accountsSearchInput.value = "";
  productSearchInput.value = "";
  offerSearchInput.value = "";
  supplierSearchInput.value = "";
  assignmentSearchInput.value = "";
  assignmentAccountSelect.innerHTML = "";
  assignmentProductSelect.innerHTML = "";
  aiEnabledInput.checked = false;
  aiReplyTemplateInput.value = "";
  aiSettingsResult.classList.add("muted");
  aiSettingsResult.textContent = "Đăng nhập bằng admin để xem và cập nhật cấu hình AI.";
  sessionCard.classList.add("muted");
  sessionCard.textContent = "Phiên làm việc chưa được khởi tạo.";
  platformSummaryPanel.classList.remove("hidden");
  topbarStatus.classList.remove("hidden");
  suppliersMenuCard.classList.remove("hidden");
  aiToolsMenuCard.classList.remove("hidden");
  productManagementPanel.classList.remove("hidden");
  supplierManagementPanel.classList.remove("hidden");
  assignmentCreateForm.classList.remove("hidden");
  assignmentCreateResult.classList.remove("hidden");
  adminAccountModePanel.classList.add("hidden");
  staffAssignmentPanel.classList.add("hidden");
  manageAccountSwitcherPanel.classList.add("hidden");
  accountFormPanel.classList.remove("hidden");
  accountsListPanel.classList.remove("hidden");
  staffCredentialsPanel.classList.remove("hidden");
  setCatalogSection(activeCatalogSection);
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
    : `${currentSession.user.name} đang quản lý danh mục sản phẩm, nhà cung cấp và cấu hình sản phẩm cho từng phòng livestream.`;
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
  const supplierOffers = Array.isArray(overview?.supplier_offers) ? overview.supplier_offers : [];
  const products = Array.isArray(overview?.products) ? overview.products : [];
  const livestreamAccounts = Array.isArray(overview?.livestream_accounts) ? overview.livestream_accounts : [];
  const users = Array.isArray(overview?.users) ? overview.users : [];
  const safeSummary = Array.isArray(summary) ? summary : [];

  const activeOffers = supplierOffers.filter((offer) => offer.status === "active").length;
  const totalInventory = products.reduce((total, item) => total + item.stock_quantity, 0);
  const totalViewers = safeSummary.reduce((total, item) => total + item.total_viewers, 0);
  const liveRooms = livestreamAccounts.filter((item) => item.broadcast_status === "live").length;
  const totalStaff = users.filter((item) => item.role === "staff").length;
  const warningRooms = liveRooms;
  kpiGrid.classList.remove("muted");
  kpiGrid.innerHTML = [
    { label: "Viewer realtime", value: totalViewers.toLocaleString("vi-VN"), note: "Tổng viewer đang có trên toàn hệ thống" },
    { label: "Offer active", value: activeOffers.toString(), note: "Ưu đãi nhập hàng đang hiệu lực" },
    { label: "Tồn kho sẵn bán", value: totalInventory.toLocaleString("vi-VN"), note: "Tổng đơn vị sản phẩm trong kho" },
    { label: "Room cảnh báo", value: warningRooms.toString(), note: "Phòng live đang có mức lag cần theo dõi" },
  ].map((item) => `<article class="kpi-card"><span>${item.label}</span><strong>${item.value}</strong><p>${item.note}</p></article>`).join("");
  const topPlatform = [...safeSummary].sort((a, b) => b.total_viewers - a.total_viewers)[0];
  overviewHighlight.textContent = topPlatform
    ? `${topPlatform.display_name} đang dẫn đầu với ${topPlatform.total_viewers.toLocaleString("vi-VN")} viewer realtime trên ${topPlatform.total_accounts} phòng live. Hệ thống hiện có ${warningRooms} room cần theo dõi tín hiệu lag.`
    : "Chưa có dữ liệu nền tảng để tổng hợp KPI vận hành.";
}

function renderPlatformSummary(items) {
  platformSummary.classList.remove("muted");
  platformSummary.innerHTML = items.map((item) => `<article class="kpi-card"><span>${item.display_name}</span><strong>${item.total_accounts}</strong><p>${item.total_viewers.toLocaleString("vi-VN")} / ${item.total_capacity.toLocaleString("vi-VN")} viewer | lag TB ${item.average_lag_signal}</p></article>`).join("");
}


function renderStaffAssignments(users, accounts, assignments) {
  const assignmentsByAccount = buildAssignmentsByAccount(assignments);
  const query = normalizeSearchText(staffSearchInput.value);
  const staffUsers = filterUsersBySearch(
    users.filter((user) => user.role === "staff"),
    staffSearchInput.value,
  )
    .sort((left, right) => left.full_name.localeCompare(right.full_name, "vi"));

  if (!staffUsers.some((user) => user.user_id === activeStaffAssignmentUserId)) {
    activeStaffAssignmentUserId = null;
  }

  staffAssignmentResult.classList.remove("muted");
  if (!staffUsers.length) {
    staffAssignmentResult.innerHTML = query
      ? "Không tìm thấy nhân viên livestream phù hợp với từ khóa này."
      : "Chưa có nhân viên livestream nào trong hệ thống.";
    return;
  }

  staffAssignmentResult.innerHTML = `<div class="staff-assignment-list">${staffUsers.map((user) => {
    const assignedAccounts = accounts.filter((account) => account.owner_user_id === user.user_id);
    const isOpen = activeStaffAssignmentUserId === user.user_id;
    return `<article class="staff-assignment-card ${isOpen ? "is-open" : ""}"><button type="button" class="staff-assignment-toggle" data-user-id="${escapeHtml(user.user_id)}"><div><strong>${escapeHtml(user.full_name)}</strong><span>Mã staff: ${escapeHtml(user.staff_code || "Chưa gán")} | ${escapeHtml(user.department)}</span></div><div class="staff-assignment-summary"><strong>${assignedAccounts.length}</strong><span>room</span></div></button><div class="staff-assignment-body ${isOpen ? "" : "hidden"}"><div class="assignment-meta"><span>${escapeHtml(user.email)}</span><span>${escapeHtml(user.phone)}</span><span>${escapeHtml(user.status)}</span></div>${assignedAccounts.length ? `<div class="assignment-room-list">${assignedAccounts.map((account) => {
      const accountAssignments = assignmentsByAccount.get(account.account_id) || [];
      const assignedProductNames = accountAssignments.map((item) => item.product_name).join(", ");
      return `<article class="assignment-room-card"><h3>${escapeHtml(account.name)}</h3><p>${escapeHtml(account.platform_display_name)} | ${escapeHtml(account.username)}</p><div class="table-meta"><span>Ca trực: ${escapeHtml(account.shift_label)}</span><span>Kho xử lý: ${escapeHtml(account.warehouse_location)}</span><span>Host chính: ${escapeHtml(account.owner_name)}</span><span class="tag ${account.status}">${formatStatus(account.status)}</span></div><div class="inline-note ${accountAssignments.length ? "" : "muted"}">Sản phẩm live: ${escapeHtml(assignedProductNames || "Chưa gán sản phẩm")}</div></article>`;
    }).join("")}</div>` : `<div class="inline-note muted">Staff này hiện chưa được phân công room livestream nào.</div>`}</div></article>`;
  }).join("")}</div>`;
}

function renderAccounts(groups, assignmentsByAccount) {
  accountsResult.classList.remove("muted");
  if (!groups.length) {
    accountsResult.innerHTML = "Bạn chưa được phân công phòng livestream nào.";
    return;
  }
  accountsResult.innerHTML = groups.map((group) => `<section class="account-table-card"><h3>${group.display_name}</h3><p class="table-subline">${group.summary.total_accounts} phòng live | ${group.summary.total_viewers.toLocaleString("vi-VN")} viewer realtime</p><div class="account-cards">${group.accounts.map((account) => {
    const accountAssignments = assignmentsByAccount.get(account.account_id) || [];
    return `<article class="account-table-card"><h3>${account.name}</h3><p>${account.owner_name} - ${account.shift_label}</p><div class="table-meta"><span><strong>${account.current_viewers}</strong> / ${account.max_capacity} viewer</span><span>${account.username}</span><span>${account.warehouse_location}</span><span class="tag ${account.status}">${formatStatus(account.status)}</span></div><div class="inline-note ${accountAssignments.length ? "" : "muted"}">Sản phẩm được gán: ${escapeHtml(accountAssignments.map((item) => item.product_name).join(", ") || "Chưa có sản phẩm nào")}</div>${isAdminSession() ? `<div class="credential-grid"><div class="credential-card"><span>Tài khoản live</span><strong>${account.username}</strong><small>Mật khẩu: ${account.password}</small></div><div class="credential-card"><span>Tài khoản nhân viên</span><strong>${account.owner_email || "Chưa gán"}</strong><small>Mật khẩu: ${account.owner_password || "Chưa gán"}</small></div></div>` : ""}</article>`;
  }).join("")}</div></section>`).join("");
}

function renderManagedAccounts(accounts, assignmentsByAccount) {
  const flashNote = accountManagementFlashMessage
    ? `<div class="inline-note">${escapeHtml(accountManagementFlashMessage)}</div>`
    : "";
  accountManagementFlashMessage = "";

  accountsResult.classList.remove("muted");
  if (!accounts.length) {
    accountsResult.innerHTML = `${flashNote}Chưa có phòng livestream nào trong hệ thống.`;
    return;
  }

  const sortedAccounts = filterAccountsBySearch(accounts, accountsSearchInput.value).sort((left, right) => {
    const platformCompare = left.platform_display_name.localeCompare(right.platform_display_name, "vi");
    if (platformCompare !== 0) return platformCompare;
    return left.name.localeCompare(right.name, "vi");
  });

  accountsResult.innerHTML = `${flashNote}<div class="account-cards">${sortedAccounts.map((account) => `<article class="account-table-card manage-account-card" data-account-id="${escapeHtml(account.account_id)}"><h3>${escapeHtml(account.name)}</h3><p>${escapeHtml(account.platform_display_name)} | ${escapeHtml(account.owner_name || "Chưa gán")}</p><div class="table-meta"><span>Username: ${escapeHtml(account.username)}</span><span>Ca trực: ${escapeHtml(account.shift_label)}</span><span>Kho xử lý: ${escapeHtml(account.warehouse_location)}</span><span><strong>${account.current_viewers}</strong> / ${account.max_capacity} viewer</span><span>Sản phẩm gán: ${(assignmentsByAccount.get(account.account_id) || []).length}</span><span class="tag ${account.status}">${formatStatus(account.status)}</span></div><button type="button" class="ghost-btn danger-btn manage-account-delete-btn">Xóa phòng live</button><div class="staff-action-result muted">Admin có thể xóa room không còn sử dụng.</div></article>`).join("")}</div>`;
}

function renderStaffCredentials(users) {
  const staffUsers = filterUsersBySearch(
    users.filter((user) => user.role === "staff"),
    staffCredentialsSearchInput.value,
  )
    .sort((left, right) => {
      const roleCompare = formatRole(left.role).localeCompare(formatRole(right.role), "vi");
      if (roleCompare !== 0) return roleCompare;
      return left.full_name.localeCompare(right.full_name, "vi");
    });
  staffCredentialsResult.classList.remove("muted");
  const flashNote = staffCredentialFlashMessage
    ? `<div class="inline-note">${escapeHtml(staffCredentialFlashMessage)}</div>`
    : "";
  staffCredentialFlashMessage = "";
  if (!staffUsers.length) {
    staffCredentialsResult.innerHTML = `${flashNote}Chưa có tài khoản nội bộ nào trong hệ thống.`;
    return;
  }
  staffCredentialsResult.innerHTML = `${flashNote}<div class="credential-grid">${staffUsers.map((user) => `<article class="credential-card staff-management-card" data-user-id="${escapeHtml(user.user_id)}"><span>${escapeHtml(user.full_name)}</span><strong>${escapeHtml(user.email)}</strong><small>Vai trò: ${escapeHtml(formatRole(user.role))}</small><small>Mã nội bộ: ${escapeHtml(user.staff_code || "Chưa gán")}</small><small>Mật khẩu hiện tại: ${escapeHtml(user.password)}</small><small>Bộ phận: ${escapeHtml(user.department)}</small><form class="staff-password-form"><label>Mật khẩu mới<input name="password" type="text" value="${escapeHtml(user.password)}" minlength="3" required /></label><button type="submit" class="primary-btn staff-action-btn">Cập nhật mật khẩu</button></form><button type="button" class="ghost-btn danger-btn staff-delete-btn">Xóa tài khoản</button><div class="staff-action-result muted">Admin có thể cập nhật mật khẩu hoặc xóa tài khoản này.</div></article>`).join("")}</div>`;
}

async function handleManagedUserCreate() {
  if (!isAdminSession()) return;

  const selectedRole = "staff";
  const payload = {
    staff_code: document.getElementById("staff-code").value.trim(),
    full_name: document.getElementById("staff-full-name").value.trim(),
    email: document.getElementById("staff-email").value.trim(),
    password: document.getElementById("staff-password").value.trim(),
    phone: document.getElementById("staff-phone").value.trim(),
    department: document.getElementById("staff-department").value.trim(),
    role: selectedRole,
  };

  staffCreateResult.classList.remove("muted");
  staffCreateResult.textContent = "Đang tạo tài khoản nội bộ...";

  try {
    const createdUser = await fetchJson("/api/v1/users/managed", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    staffCreateResult.innerHTML = `Đã tạo <strong>${escapeHtml(formatRole(createdUser.role))}</strong> cho <strong>${escapeHtml(createdUser.full_name)}</strong> với mã <strong>${escapeHtml(createdUser.staff_code || "")}</strong>.`;
    staffCreateForm.reset();
    staffRole.value = "staff";
    document.getElementById("staff-password").value = "staff05";
    staffCredentialFlashMessage = `Đã thêm ${formatRole(createdUser.role)} ${createdUser.full_name} với mã ${createdUser.staff_code}.`;
    await loadDashboardData();
  } catch (error) {
    staffCreateResult.textContent = extractErrorMessage(error, "Không thể tạo tài khoản nội bộ.");
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
  resultBox.textContent = "Đang xóa tài khoản nội bộ...";

  try {
    const deletedUser = await fetchJson(`/api/v1/users/${userId}`, { method: "DELETE" });
    const reassignedMessage = deletedUser.reassigned_accounts
      ? ` Đã gỡ ${deletedUser.reassigned_accounts} phòng live khỏi tài khoản này.`
      : "";
    staffCredentialFlashMessage = `${deletedUser.message}${reassignedMessage}`;
    await loadDashboardData();
  } catch (error) {
    resultBox.textContent = extractErrorMessage(error, "Không thể xóa tài khoản nội bộ này.");
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

async function handleProductCreate() {
  if (!canManageCatalog()) return;

  const payload = {
    sku: document.getElementById("product-sku").value.trim(),
    name: document.getElementById("product-name").value.trim(),
    category: document.getElementById("product-category").value.trim(),
    brand: document.getElementById("product-brand").value.trim(),
    cost_price: Number(document.getElementById("product-cost-price").value),
    retail_price: Number(document.getElementById("product-retail-price").value),
    stock_quantity: Number(document.getElementById("product-stock-quantity").value),
    reorder_level: Number(document.getElementById("product-reorder-level").value),
    unit: document.getElementById("product-unit").value.trim(),
    description: document.getElementById("product-description").value.trim(),
    is_active: document.getElementById("product-is-active").value === "true",
  };

  productCreateResult.classList.remove("muted");
  productCreateResult.textContent = "Đang thêm sản phẩm...";

  try {
    const createdProduct = await fetchJson("/api/v1/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    productCreateResult.innerHTML = `Đã thêm sản phẩm <strong>${escapeHtml(createdProduct.name)}</strong> với SKU <strong>${escapeHtml(createdProduct.sku)}</strong>.`;
    productCreateForm.reset();
    document.getElementById("product-cost-price").value = 99000;
    document.getElementById("product-retail-price").value = 189000;
    document.getElementById("product-stock-quantity").value = 120;
    document.getElementById("product-reorder-level").value = 30;
    document.getElementById("product-is-active").value = "true";
    productManagementFlashMessage = `Đã thêm sản phẩm ${createdProduct.name}.`;
    await loadDashboardData();
  } catch (error) {
    productCreateResult.textContent = extractErrorMessage(error, "Không thể thêm sản phẩm mới.");
  }
}

async function handleProductDelete(button) {
  if (!canManageCatalog()) return;

  const card = button.closest(".manage-product-card");
  const productId = card?.dataset.productId;
  const productName = card?.querySelector("h3")?.textContent || "sản phẩm này";
  const resultBox = card?.querySelector(".staff-action-result");

  if (!productId || !resultBox) return;
  if (!window.confirm(`Bạn có chắc muốn xóa ${productName} khỏi hệ thống?`)) return;

  button.disabled = true;
  resultBox.classList.remove("muted");
  resultBox.textContent = "Đang xóa sản phẩm...";

  try {
    const deletedProduct = await fetchJson(`/api/v1/products/${productId}`, { method: "DELETE" });
    productManagementFlashMessage = deletedProduct.message;
    await loadDashboardData();
  } catch (error) {
    resultBox.textContent = extractErrorMessage(error, "Không thể xóa sản phẩm này.");
  } finally {
    button.disabled = false;
  }
}

async function handleSupplierCreate() {
  if (!canManageCatalog()) return;

  const payload = {
    supplier_code: document.getElementById("supplier-code").value.trim(),
    name: document.getElementById("supplier-name").value.trim(),
    contact_name: document.getElementById("supplier-contact-name").value.trim(),
    phone: document.getElementById("supplier-phone").value.trim(),
    email: document.getElementById("supplier-email").value.trim(),
    address: document.getElementById("supplier-address").value.trim(),
    rating: Number(document.getElementById("supplier-rating").value),
    lead_time_days: Number(document.getElementById("supplier-lead-time").value),
    status: document.getElementById("supplier-status").value,
  };

  supplierCreateResult.classList.remove("muted");
  supplierCreateResult.textContent = "Đang thêm nhà cung cấp...";

  try {
    const createdSupplier = await fetchJson("/api/v1/suppliers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    supplierCreateResult.innerHTML = `Đã thêm nhà cung cấp <strong>${escapeHtml(createdSupplier.name)}</strong> với mã <strong>${escapeHtml(createdSupplier.supplier_code)}</strong>.`;
    supplierCreateForm.reset();
    document.getElementById("supplier-rating").value = 4.5;
    document.getElementById("supplier-lead-time").value = 3;
    document.getElementById("supplier-status").value = "active";
    supplierManagementFlashMessage = `Đã thêm nhà cung cấp ${createdSupplier.name}.`;
    await loadDashboardData();
  } catch (error) {
    supplierCreateResult.textContent = extractErrorMessage(error, "Không thể thêm nhà cung cấp mới.");
  }
}

async function handleSupplierDelete(button) {
  if (!canManageCatalog()) return;

  const card = button.closest(".manage-supplier-card");
  const supplierId = card?.dataset.supplierId;
  const supplierName = card?.querySelector("h3")?.textContent || "nhà cung cấp này";
  const resultBox = card?.querySelector(".staff-action-result");

  if (!supplierId || !resultBox) return;
  if (!window.confirm(`Bạn có chắc muốn xóa ${supplierName} khỏi hệ thống?`)) return;

  button.disabled = true;
  resultBox.classList.remove("muted");
  resultBox.textContent = "Đang xóa nhà cung cấp...";

  try {
    const deletedSupplier = await fetchJson(`/api/v1/suppliers/${supplierId}`, { method: "DELETE" });
    supplierManagementFlashMessage = deletedSupplier.message;
    await loadDashboardData();
  } catch (error) {
    resultBox.textContent = extractErrorMessage(error, "Không thể xóa nhà cung cấp này.");
  } finally {
    button.disabled = false;
  }
}

async function handleProductAssignmentCreate() {
  if (!canManageCatalog()) return;

  const payload = {
    account_id: assignmentAccountSelect.value,
    product_id: assignmentProductSelect.value,
    assigned_by_user_id: currentSession?.user?.id || null,
  };

  assignmentCreateResult.classList.remove("muted");
  assignmentCreateResult.textContent = "Đang gán sản phẩm cho phòng livestream...";

  try {
    const createdAssignment = await fetchJson("/api/v1/livestream-product-assignments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    assignmentCreateResult.innerHTML = `Đã gán <strong>${escapeHtml(createdAssignment.product_name)}</strong> cho <strong>${escapeHtml(createdAssignment.account_name)}</strong>.`;
    productAssignmentFlashMessage = `Đã cập nhật danh mục live cho ${createdAssignment.account_name}.`;
    await loadDashboardData();
  } catch (error) {
    assignmentCreateResult.textContent = extractErrorMessage(error, "Không thể gán sản phẩm cho phòng livestream.");
  }
}

async function handleProductAssignmentDelete(button) {
  if (!canManageCatalog()) return;

  const card = button.closest(".product-assignment-card");
  const assignmentId = card?.dataset.assignmentId;
  const productName = card?.querySelector("h3")?.textContent || "sản phẩm này";

  if (!assignmentId) return;
  if (!window.confirm(`Bạn có chắc muốn gỡ ${productName} khỏi phòng livestream?`)) return;

  button.disabled = true;

  try {
    const deletedAssignment = await fetchJson(`/api/v1/livestream-product-assignments/${assignmentId}`, { method: "DELETE" });
    productAssignmentFlashMessage = deletedAssignment.message;
    await loadDashboardData();
  } catch (error) {
    assignmentCreateResult.classList.remove("muted");
    assignmentCreateResult.textContent = extractErrorMessage(error, "Không thể gỡ sản phẩm khỏi phòng livestream.");
  } finally {
    button.disabled = false;
  }
}

function renderProducts(products, assignments) {
  const assignmentCountByProduct = new Map();
  assignments.forEach((assignment) => {
    assignmentCountByProduct.set(
      assignment.product_id,
      (assignmentCountByProduct.get(assignment.product_id) || 0) + 1,
    );
  });
  const flashNote = productManagementFlashMessage
    ? `<div class="inline-note">${escapeHtml(productManagementFlashMessage)}</div>`
    : "";
  productManagementFlashMessage = "";
  productsResult.classList.remove("muted");
  const filteredProducts = filterProductsBySearch(products, productSearchInput.value);
  if (!filteredProducts.length) {
    productsResult.innerHTML = `${flashNote}Chưa có sản phẩm nào được phân cho ca làm hiện tại.`;
    return;
  }
  productsResult.innerHTML = `${flashNote}<div class="product-grid">${filteredProducts.map((item) => `<article class="product-card manage-product-card" data-product-id="${escapeHtml(item.product_id)}"><h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.brand)} - ${escapeHtml(item.category)}</p><div class="product-meta"><span>SKU: ${escapeHtml(item.sku)}</span><span>Giá bán: ${item.retail_price.toLocaleString("vi-VN")} đ</span><span>Giá vốn: ${item.cost_price.toLocaleString("vi-VN")} đ</span><span>Tồn kho: ${item.stock_quantity} ${escapeHtml(item.unit)}</span><span>Đang gán cho: ${(assignmentCountByProduct.get(item.product_id) || 0)} room</span></div><p>${escapeHtml(item.description)}</p>${canManageCatalog() ? `<button type="button" class="ghost-btn danger-btn product-delete-btn">Xóa sản phẩm</button><div class="staff-action-result muted">Sản phẩm chỉ xóa được khi không còn offer gắn kèm.</div>` : ""}</article>`).join("")}</div>`;
}

function renderOffers(offers) {
  offersResult.classList.remove("muted");
  const filteredOffers = filterOffersBySearch(offers, offerSearchInput.value);
  if (!filteredOffers.length) {
    offersResult.innerHTML = "Không có offer nào áp dụng cho room và ca làm hiện tại.";
    return;
  }
  offersResult.innerHTML = `<div class="offer-grid">${filteredOffers.map((item) => `<article class="offer-card"><h3>${item.offer_title}</h3><p>${item.supplier_name}</p><div class="offer-meta"><span>Sản phẩm: ${item.product_name}</span><span>MOQ: ${item.min_order_quantity}</span><span>Giá nhập: ${item.unit_price.toLocaleString("vi-VN")} đ</span><span>Chiết khấu: ${item.discount_percent}%</span><span class="tag ${item.status}">${formatStatus(item.status)}</span></div></article>`).join("")}</div>`;
}

function renderSuppliers(suppliers) {
  const flashNote = supplierManagementFlashMessage
    ? `<div class="inline-note">${escapeHtml(supplierManagementFlashMessage)}</div>`
    : "";
  supplierManagementFlashMessage = "";
  suppliersResult.classList.remove("muted");
  const filteredSuppliers = filterSuppliersBySearch(suppliers, supplierSearchInput.value);
  if (!filteredSuppliers.length) {
    suppliersResult.innerHTML = `${flashNote}Chưa có nhà cung cấp nào trong hệ thống.`;
    return;
  }
  suppliersResult.innerHTML = `${flashNote}<div class="supplier-grid">${filteredSuppliers.map((item) => `<article class="supplier-card manage-supplier-card" data-supplier-id="${escapeHtml(item.supplier_id)}"><h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.contact_name)}</p><div class="supplier-meta"><span>${escapeHtml(item.phone)}</span><span>${escapeHtml(item.email)}</span><span>${escapeHtml(item.address)}</span><span>Rating: ${item.rating}/5</span><span>Lead time: ${item.lead_time_days} ngày</span><span class="tag ${escapeHtml(item.status)}">${formatStatus(item.status)}</span></div>${canManageCatalog() ? `<button type="button" class="ghost-btn danger-btn supplier-delete-btn">Xóa nhà cung cấp</button><div class="staff-action-result muted">Xóa nhà cung cấp sẽ gỡ offer và xóa luôn các sản phẩm chỉ thuộc nhà cung cấp này.</div>` : ""}</article>`).join("")}</div>`;
}

function renderProductAssignments(assignments) {
  const flashNote = productAssignmentFlashMessage
    ? `<div class="inline-note">${escapeHtml(productAssignmentFlashMessage)}</div>`
    : "";
  productAssignmentFlashMessage = "";
  productAssignmentResult.classList.remove("muted");

  const filteredAssignments = filterAssignmentsBySearch(assignments, assignmentSearchInput.value);
  if (!filteredAssignments.length) {
    productAssignmentResult.innerHTML = `${flashNote}Chưa có cấu hình gán sản phẩm nào cho các phòng livestream.`;
    return;
  }

  const grouped = new Map();
  [...filteredAssignments]
    .sort((left, right) => {
      const accountCompare = left.account_name.localeCompare(right.account_name, "vi");
      if (accountCompare !== 0) return accountCompare;
      return left.product_name.localeCompare(right.product_name, "vi");
    })
    .forEach((assignment) => {
      if (!grouped.has(assignment.account_id)) {
        grouped.set(assignment.account_id, {
          account_name: assignment.account_name,
          platform_display_name: assignment.platform_display_name,
          items: [],
        });
      }
      grouped.get(assignment.account_id).items.push(assignment);
    });

  productAssignmentResult.innerHTML = `${flashNote}<div class="account-cards">${[...grouped.entries()].map(([accountId, group]) => `<article class="account-table-card"><h3>${escapeHtml(group.account_name)}</h3><p>${escapeHtml(group.platform_display_name)} | ${group.items.length} sản phẩm được gán</p><div class="offer-grid">${group.items.map((assignment) => `<article class="offer-card product-assignment-card" data-assignment-id="${escapeHtml(assignment.assignment_id)}"><h3>${escapeHtml(assignment.product_name)}</h3><p>${escapeHtml(assignment.product_category)} | ${escapeHtml(assignment.product_sku)}</p><div class="offer-meta"><span>Mã cấu hình: ${escapeHtml(assignment.assignment_id)}</span><span>Người gán: ${escapeHtml(assignment.assigned_by_name || "Chưa ghi nhận")}</span><span>Thời điểm: ${escapeHtml(assignment.assigned_at)}</span></div>${canManageCatalog() ? `<button type="button" class="ghost-btn danger-btn assignment-delete-btn">Gỡ sản phẩm khỏi room</button>` : ""}</article>`).join("")}</div></article>`).join("")}</div>`;
}

function fillAssignmentSelectors(accounts, products) {
  const accountOptions = [...accounts]
    .sort((left, right) => left.name.localeCompare(right.name, "vi"))
    .map((account) => `<option value="${account.account_id}">${account.name} (${account.platform_display_name} - ${account.owner_name})</option>`)
    .join("");
  const productOptions = [...products]
    .sort((left, right) => left.name.localeCompare(right.name, "vi"))
    .map((product) => `<option value="${product.product_id}">${product.name} (${product.sku})</option>`)
    .join("");

  assignmentAccountSelect.innerHTML = accountOptions;
  assignmentProductSelect.innerHTML = productOptions;

  if (accounts[0]) assignmentAccountSelect.value = accounts[0].account_id;
  if (products[0]) assignmentProductSelect.value = products[0].product_id;
}

function renderAiAssistantSettings(settings, message = "") {
  if (!settings) {
    aiEnabledInput.checked = false;
    aiReplyTemplateInput.value = "";
    aiSettingsResult.classList.add("muted");
    aiSettingsResult.textContent = "Đăng nhập bằng admin để xem và cập nhật cấu hình AI.";
    return;
  }

  aiEnabledInput.checked = Boolean(settings.is_enabled);
  aiReplyTemplateInput.value = settings.customer_reply_template || "";
  aiSettingsResult.classList.remove("muted");
  aiSettingsResult.innerHTML = [
    message ? `<strong>${escapeHtml(message)}</strong>` : "",
    `<span>Trạng thái: ${settings.is_enabled ? "Đang bật" : "Đang tắt"}</span>`,
    `<span>Cập nhật lúc: ${escapeHtml(settings.updated_at || "Chưa có dữ liệu")}</span>`,
  ].filter(Boolean).join("<br />");
}

function renderDashboardViews() {
  const groupedAccounts = buildGroupedAccounts(currentAllAccounts);
  const summary = groupedAccounts.map((group) => ({
    ...group.summary,
    display_name: group.display_name,
  }));
  const visibleAssignments = currentAssignments;
  const allAssignmentsByAccount = buildAssignmentsByAccount(currentAssignments);
  livestreamAccounts = currentAllAccounts;
  const visibleProducts = currentProducts;
  const visibleOffers = currentOffers;

  if (isAdminSession()) {
    renderPlatformSummary(summary);
    renderKpis(summary, {
      supplier_offers: currentOffers,
      products: currentProducts,
      livestream_accounts: currentAllAccounts,
    });
    renderStaffAssignments(currentUsers, currentAllAccounts, currentAssignments);
    renderManagedAccounts(currentAllAccounts, allAssignmentsByAccount);
    renderStaffCredentials(currentUsers);
    renderSuppliers(currentSuppliers);
  } else if (isProductManagerSession()) {
    renderSuppliers(currentSuppliers);
  }

  if (canManageCatalog()) {
    fillAssignmentSelectors(currentAllAccounts, currentProducts);
  }

  renderProducts(visibleProducts, visibleAssignments);
  renderOffers(visibleOffers);
  renderProductAssignments(visibleAssignments);
  renderAiAssistantSettings(currentAiSettings);
}

async function loadAiAssistantSettings() {
  if (!currentSession || !isAdminSession()) {
    currentAiSettings = null;
    renderAiAssistantSettings(null);
    return;
  }

  currentAiSettings = await fetchJson("/api/v1/ai-assistant/settings");
  renderAiAssistantSettings(currentAiSettings);
}

async function loadDashboardData() {
  if (!currentSession) {
    resetDashboardState();
    return;
  }

  const overview = await fetchJson("/api/v1/database-overview");
  currentUsers = overview.users || [];
  currentAllAccounts = overview.livestream_accounts || [];
  currentProducts = overview.products || [];
  currentSuppliers = overview.suppliers || [];
  currentOffers = overview.supplier_offers || [];
  currentAssignments = overview.livestream_product_assignments || [];
  renderDashboardViews();
  await loadAiAssistantSettings();
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
    if (data.user.role !== "admin" && data.user.role !== "product_manager") {
      lockToAuthScreen();
      loginResult.classList.remove("muted");
      loginResult.textContent = "App quản lý chỉ cho phép tài khoản admin hoặc quản lý sản phẩm đăng nhập.";
      await loadCaptcha();
      return;
    }
    setSession(data);
    loginResult.classList.remove("muted");
    loginResult.innerHTML = `<strong>Đăng nhập thành công</strong><br />${data.user.name} - ${data.user.email}<br />Vai trò: ${formatRole(data.user.role)}`;
    await Promise.all([fetchGatewayHealth(), loadDashboardData()]);
  } catch (error) {
    lockToAuthScreen();
    loginResult.textContent = extractErrorMessage(
      error,
      "????ng nh???p th???t b???i. Vui l??ng ki???m tra email, m???t kh???u v?? CAPTCHA.",
    );
    await loadCaptcha();
  }
});

menuCards.forEach((button) => {
  button.addEventListener("click", () => {
    openTab(button.dataset.tab);
  });
});

catalogSectionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setCatalogSection(button.dataset.catalogSection);
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
  renderStaffAssignments(currentUsers, livestreamAccounts, currentAssignments);
});

staffCredentialsSearchInput.addEventListener("input", () => {
  if (!isAdminSession()) return;
  renderStaffCredentials(currentUsers);
});

accountsSearchInput.addEventListener("input", () => {
  if (!currentSession) return;
  renderDashboardViews();
});

productSearchInput.addEventListener("input", () => {
  if (!currentSession) return;
  renderDashboardViews();
});

offerSearchInput.addEventListener("input", () => {
  if (!currentSession) return;
  renderDashboardViews();
});

supplierSearchInput.addEventListener("input", () => {
  if (!currentSession) return;
  renderDashboardViews();
});

assignmentSearchInput.addEventListener("input", () => {
  if (!currentSession) return;
  renderDashboardViews();
});

staffCreateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await handleManagedUserCreate();
});

staffAssignmentResult.addEventListener("click", (event) => {
  const toggleButton = event.target.closest(".staff-assignment-toggle");
  if (!toggleButton) return;
  const userId = toggleButton.dataset.userId;
  activeStaffAssignmentUserId = activeStaffAssignmentUserId === userId ? null : userId;
  renderStaffAssignments(currentUsers, livestreamAccounts, currentAssignments);
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

productsResult.addEventListener("click", async (event) => {
  const deleteButton = event.target.closest(".product-delete-btn");
  if (!deleteButton) return;
  await handleProductDelete(deleteButton);
});

suppliersResult.addEventListener("click", async (event) => {
  const deleteButton = event.target.closest(".supplier-delete-btn");
  if (!deleteButton) return;
  await handleSupplierDelete(deleteButton);
});

productAssignmentResult.addEventListener("click", async (event) => {
  const deleteButton = event.target.closest(".assignment-delete-btn");
  if (!deleteButton) return;
  await handleProductAssignmentDelete(deleteButton);
});

logoutBtn.addEventListener("click", () => {
  setSession(null);
  lockToAuthScreen();
});

accountForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!isAdminSession()) return;
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

productCreateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await handleProductCreate();
});

supplierCreateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await handleSupplierCreate();
});

assignmentCreateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await handleProductAssignmentCreate();
});

aiSettingsForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!isAdminSession()) {
    renderAiAssistantSettings(currentAiSettings, "Chỉ admin mới được cập nhật cấu hình AI.");
    return;
  }

  aiSettingsResult.classList.remove("muted");
  aiSettingsResult.textContent = "Đang lưu cấu hình AI...";
  try {
    currentAiSettings = await fetchJson("/api/v1/ai-assistant/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        is_enabled: aiEnabledInput.checked,
        customer_reply_template: aiReplyTemplateInput.value.trim(),
      }),
    });
    renderAiAssistantSettings(currentAiSettings, "Đã cập nhật cấu hình AI.");
  } catch (error) {
    aiSettingsResult.classList.remove("muted");
    aiSettingsResult.textContent = extractErrorMessage(error, "Không thể lưu cấu hình AI.");
  }
});

localStorage.removeItem(SESSION_KEY);
lockToAuthScreen();
resetDashboardState();
loadCaptcha().catch(() => {
  captchaImage.alt = "Không thể tải CAPTCHA";
  captchaExpiry.textContent = "Hãy kiểm tra auth-service rồi làm mới lại";
});
