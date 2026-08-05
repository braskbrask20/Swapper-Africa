const API_URL = window.SWAPPER_API_URL || "http://localhost:8000";
const token = sessionStorage.getItem("swapper_admin_token");

async function api(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, { ...options, headers: { "Content-Type": "application/json", "Authorization": `Bearer ${sessionStorage.getItem("swapper_admin_token")}`, ...options.headers } });
  if (response.status === 401 || response.status === 403) {
    sessionStorage.removeItem("swapper_admin_token");
    if (!location.pathname.endsWith("index.html")) location.href = "index.html";
    throw new Error("Your session has ended.");
  }
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || "Request failed");
  return body;
}

const loginForm = document.getElementById("adminLoginForm");
if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = document.getElementById("loginMessage");
    message.textContent = "";
    try {
      const response = await fetch(`${API_URL}/v1/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: document.getElementById("adminEmail").value, password: document.getElementById("adminPassword").value }) });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || "Sign in failed");
      sessionStorage.setItem("swapper_admin_token", body.access_token);
      location.href = "dashboard.html";
    } catch (error) { message.textContent = error.message; }
  });
}

function renderAdminSwaps(swaps) {
  const list = document.getElementById("adminSwapList");
  list.innerHTML = "";
  document.getElementById("adminEmpty").hidden = swaps.length > 0;
  swaps.forEach((swap) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${swap.reference}</td><td>${swap.from_asset} → ${swap.to_asset}</td><td>${swap.amount} ${swap.from_asset}</td><td>${swap.amount_received} ${swap.to_asset}</td><td><span class="status-pill">${swap.status}</span></td><td>${new Date(swap.created_at).toLocaleString()}</td><td><select data-reference="${swap.reference}" aria-label="Update ${swap.reference}"><option value="pending">Pending</option><option value="processing">Processing</option><option value="completed">Completed</option><option value="failed">Failed</option><option value="cancelled">Cancelled</option></select></td>`;
    row.querySelector("select").value = swap.status;
    row.querySelector("select").addEventListener("change", async (event) => { await api(`/v1/admin/swaps/${swap.reference}`, { method: "PATCH", body: JSON.stringify({ status: event.target.value }) }); loadAdmin(); });
    list.appendChild(row);
  });
}

async function loadAdmin() {
  if (!document.getElementById("adminSwapList")) return;
  try {
    const [summary, swaps] = await Promise.all([api("/v1/admin/summary"), api("/v1/admin/swaps")]);
    document.getElementById("adminUsers").textContent = summary.users;
    document.getElementById("adminSwaps").textContent = summary.swaps;
    document.getElementById("adminPending").textContent = summary.pending_swaps;
    renderAdminSwaps(swaps);
  } catch (error) { document.getElementById("adminEmpty").hidden = false; document.getElementById("adminEmpty").textContent = error.message; }
}

if (token) loadAdmin();
const refresh = document.getElementById("refreshAdmin");
if (refresh) refresh.addEventListener("click", loadAdmin);
const signOut = document.getElementById("signOut");
if (signOut) signOut.addEventListener("click", () => { sessionStorage.removeItem("swapper_admin_token"); location.href = "index.html"; });
