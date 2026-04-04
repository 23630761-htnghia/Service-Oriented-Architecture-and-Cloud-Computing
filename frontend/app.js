const API_BASE = "http://localhost:8000";

const gatewayStatus = document.getElementById("gateway-status");
const aiStatus = document.getElementById("ai-status");
const userStatus = document.getElementById("user-status");
const loginForm = document.getElementById("login-form");
const loginResult = document.getElementById("login-result");
const accountForm = document.getElementById("account-form");
const accountFormResult = document.getElementById("account-form-result");
const platformSummary = document.getElementById("platform-summary");
const commentForm = document.getElementById("comment-form");
const commentInput = document.getElementById("comment-input");
const commentResult = document.getElementById("comment-result");
const viewerForm = document.getElementById("viewer-form");
const viewerResult = document.getElementById("viewer-result");
const accountsResult = document.getElementById("accounts-result");
const accountASelect = document.getElementById("account-a-select");
const accountBSelect = document.getElementById("account-b-select");

let livestreamAccounts = [];

async function fetchGatewayHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    const data = await response.json();
    gatewayStatus.textContent = data.status;
    aiStatus.textContent = [
      data.dependencies?.ai_service?.status || "?",
      data.dependencies?.auth_service?.status || "?",
      data.dependencies?.account_service?.status || "?",
    ].join(" / ");
  } catch (error) {
    gatewayStatus.textContent = "unreachable";
    aiStatus.textContent = "unreachable";
  }
}

function renderPlatformSummary(items) {
  platformSummary.classList.remove("muted");
  platformSummary.innerHTML = items
    .map(
      (item) => `
        <article class="mini-stat-card">
          <span>${item.display_name}</span>
          <strong>${item.total_accounts} tài khoản</strong>
          <p>${item.total_viewers}/${item.total_capacity} viewer | lag TB ${item.average_lag_signal}</p>
        </article>
      `,
    )
    .join("");
}

function accountLine(account) {
  return `
    <li>
      <strong>${account.name}</strong> - owner ${account.owner_name},
      ${account.current_viewers}/${account.max_capacity} viewer,
      engagement ${account.engagement_rate},
      lag ${account.lag_signal},
      status ${account.status}
    </li>
  `;
}

function renderGroupedAccounts(groups) {
  accountsResult.classList.remove("muted");
  accountsResult.innerHTML = groups
    .map(
      (group) => `
        <section class="platform-group">
          <div class="platform-group-header">
            <h3>${group.display_name}</h3>
            <p>${group.summary.total_accounts} tài khoản | ${group.summary.total_viewers}/${group.summary.total_capacity} viewer</p>
          </div>
          <ul class="result-list">
            ${group.accounts.map(accountLine).join("")}
          </ul>
        </section>
      `,
    )
    .join("");
}

function fillAccountSelectors(accounts) {
  const options = accounts
    .map(
      (account) => `<option value="${account.account_id}">${account.name} (${account.platform} - ${account.owner_name})</option>`,
    )
    .join("");
  accountASelect.innerHTML = options;
  accountBSelect.innerHTML = options;
  if (accounts[0]) accountASelect.value = accounts[0].account_id;
  if (accounts[1]) accountBSelect.value = accounts[1].account_id;
}

async function fetchPlatformSummaries() {
  try {
    const response = await fetch(`${API_BASE}/api/v1/platform-summaries`);
    if (!response.ok) {
      throw new Error("Không thể tải thống kê platform.");
    }
    renderPlatformSummary(await response.json());
  } catch (error) {
    platformSummary.textContent = error.message;
  }
}

async function fetchAccounts() {
  try {
    const [accountsResponse, groupedResponse] = await Promise.all([
      fetch(`${API_BASE}/api/v1/livestream-accounts`),
      fetch(`${API_BASE}/api/v1/livestream-accounts/grouped`),
    ]);

    if (!accountsResponse.ok || !groupedResponse.ok) {
      throw new Error("Không thể tải danh sách tài khoản livestream.");
    }

    livestreamAccounts = await accountsResponse.json();
    const grouped = await groupedResponse.json();
    renderGroupedAccounts(grouped);
    fillAccountSelectors(livestreamAccounts);
  } catch (error) {
    accountsResult.textContent = error.message;
  }
}

function renderCommentResult(data) {
  commentResult.classList.remove("muted");
  commentResult.innerHTML = `
    <strong>Intent:</strong> ${data.intent}<br />
    <strong>Sentiment:</strong> ${data.sentiment}<br />
    <strong>Lead score:</strong> ${data.lead_score}<br />
    <strong>Priority:</strong> ${data.priority}<br />
    <strong>Suggested action:</strong> ${data.suggested_action}
    <ul class="result-list">
      ${data.reasons.map((reason) => `<li>${reason}</li>`).join("")}
    </ul>
  `;
}

function renderViewerResult(data) {
  viewerResult.classList.remove("muted");
  const allocations = data.allocations
    .map(
      (item) => `
        <li>
          <strong>${item.account_id}</strong>: target ${item.target_viewers} viewer,
          delta ${item.viewer_delta},
          <span class="risk-${item.lag_risk}">${item.lag_risk}</span>
        </li>
      `,
    )
    .join("");

  const transfers = data.transfer_plan.length
    ? data.transfer_plan
        .map(
          (item) => `<li>Chuyển ${item.viewers_to_shift} viewer từ <strong>${item.from_account_id}</strong> sang <strong>${item.to_account_id}</strong>.</li>`,
        )
        .join("")
    : "<li>Không cần chuyển viewer trong cửa sổ hiện tại.</li>";

  viewerResult.innerHTML = `
    <strong>Tóm tắt:</strong> ${data.summary}<br />
    <strong>Kênh ưu tiên nhận viewer mới:</strong> ${data.recommended_entry_account_id}
    <h4>Phân bổ đề xuất</h4>
    <ul class="result-list">${allocations}</ul>
    <h4>Kế hoạch điều hướng</h4>
    <ul class="result-list">${transfers}</ul>
  `;
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginResult.textContent = "Đang đăng nhập...";

  try {
    const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: document.getElementById("login-email").value.trim(),
        password: document.getElementById("login-password").value,
      }),
    });

    if (!response.ok) {
      throw new Error("Đăng nhập thất bại.");
    }

    const data = await response.json();
    userStatus.textContent = `${data.user.name} (${data.user.role})`;
    loginResult.classList.remove("muted");
    loginResult.innerHTML = `
      <strong>Access token:</strong> ${data.access_token}<br />
      <strong>User:</strong> ${data.user.name}<br />
      <strong>Email:</strong> ${data.user.email}<br />
      <strong>Role:</strong> ${data.user.role}
    `;
  } catch (error) {
    loginResult.textContent = error.message;
  }
});

accountForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  accountFormResult.textContent = "Đang tạo tài khoản livestream...";

  const payload = {
    name: document.getElementById("account-name").value.trim(),
    platform: document.getElementById("account-platform").value,
    owner_name: document.getElementById("account-owner").value.trim(),
    current_viewers: Number(document.getElementById("account-viewers").value),
    max_capacity: Number(document.getElementById("account-capacity").value),
    engagement_rate: Number(document.getElementById("account-engagement").value),
    lag_signal: Number(document.getElementById("account-lag").value),
    status: document.getElementById("account-status").value,
  };

  try {
    const response = await fetch(`${API_BASE}/api/v1/livestream-accounts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("Không thể tạo tài khoản livestream.");
    }

    const created = await response.json();
    accountFormResult.classList.remove("muted");
    accountFormResult.innerHTML = `Đã tạo tài khoản <strong>${created.name}</strong> trên nền tảng <strong>${created.platform}</strong> với mã <strong>${created.account_id}</strong>.`;
    accountForm.reset();
    document.getElementById("account-viewers").value = 120;
    document.getElementById("account-capacity").value = 800;
    document.getElementById("account-engagement").value = 0.45;
    document.getElementById("account-lag").value = 0.15;
    await Promise.all([fetchAccounts(), fetchPlatformSummaries()]);
  } catch (error) {
    accountFormResult.textContent = error.message;
  }
});

commentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  commentResult.textContent = "Đang phân tích comment...";

  try {
    const response = await fetch(`${API_BASE}/api/v1/comments/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ comment: commentInput.value.trim() }),
    });

    if (!response.ok) {
      throw new Error("Không thể phân tích comment.");
    }

    renderCommentResult(await response.json());
  } catch (error) {
    commentResult.textContent = error.message;
  }
});

function getSelectedAccounts() {
  const first = livestreamAccounts.find((account) => account.account_id === accountASelect.value);
  const second = livestreamAccounts.find((account) => account.account_id === accountBSelect.value);
  return [first, second].filter(Boolean);
}

viewerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  viewerResult.textContent = "Đang tính toán cân bằng viewer...";

  const accounts = getSelectedAccounts();
  if (accounts.length < 2) {
    viewerResult.textContent = "Cần ít nhất 2 tài khoản để cân bằng viewer.";
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/api/v1/streams/balance-viewers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        incoming_viewers: Number(document.getElementById("incoming-viewers").value),
        accounts: accounts.map((account) => ({
          account_id: account.account_id,
          platform: account.platform,
          current_viewers: account.current_viewers,
          max_capacity: account.max_capacity,
          engagement_rate: account.engagement_rate,
          lag_signal: account.lag_signal,
        })),
      }),
    });

    if (!response.ok) {
      throw new Error("Không thể tính cân bằng viewer.");
    }

    renderViewerResult(await response.json());
  } catch (error) {
    viewerResult.textContent = error.message;
  }
});

fetchGatewayHealth();
fetchPlatformSummaries();
fetchAccounts();
