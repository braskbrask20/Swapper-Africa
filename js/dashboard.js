const connectedWallet = localStorage.getItem("connectedWallet");
const transactionList = document.getElementById("transactionList");
const emptyActivity = document.getElementById("emptyActivity");
const searchInput = document.getElementById("activitySearch");
const assetFilter = document.getElementById("assetFilter");
const signOutButton = document.getElementById("signOutBtn");

let dashboardSwaps = [];

function renderTransactions() {
  transactionList.innerHTML = "";
  const searchTerm = searchInput.value.trim().toLowerCase();
  const asset = assetFilter.value;
  const matchingTransactions = dashboardSwaps.filter((item) => {
    const haystack = `${item.reference} ${item.from_asset} ${item.to_asset} ${item.status} ${item.created_at}`.toLowerCase();
    return (!searchTerm || haystack.includes(searchTerm)) && (!asset || item.from_asset === asset || item.to_asset === asset);
  });
  emptyActivity.hidden = matchingTransactions.length > 0;
  emptyActivity.textContent = dashboardSwaps.length ? "No swaps match your filters." : "No swaps yet. Your completed swaps will appear here.";
  matchingTransactions.forEach((item) => {
    const row = document.createElement("tr");
    [item.reference.slice(-6), `${formatAsset(item.amount, item.from_asset)}`, formatAsset(item.amount_received, item.to_asset), item.status, new Date(item.created_at).toLocaleString()].forEach((value, index) => {
      const cell = document.createElement("td");
      if (index === 3) cell.innerHTML = `<span class="status-pill">${value}</span>`;
      else cell.textContent = value;
      row.appendChild(cell);
    });
    transactionList.appendChild(row);
  });
}

async function initDashboard() {
  if (!SwapperAPI.isAuthenticated()) {
    window.location.replace("auth.html?next=dashboard.html");
    return;
  }

  try {
    const profile = await SwapperAPI.getProfile(true);
    document.getElementById("totalBalance").textContent = formatUsd(getPortfolioValue({ balance: profile.balances }));
    document.getElementById("totalTransactions").textContent = "—";
    const walletStatus = document.getElementById("walletStatus");
    if (walletStatus) walletStatus.textContent = connectedWallet || profile.full_name || "Connected";
    const walletDot = document.getElementById("walletDot");
    if (walletDot) walletDot.classList.toggle("connected", Boolean(connectedWallet));

    dashboardSwaps = await SwapperAPI.getSwaps();
    document.getElementById("totalTransactions").textContent = String(dashboardSwaps.length);
    renderTransactions();
  } catch (error) {
    console.error(error);
    window.location.replace("auth.html?next=dashboard.html");
  }
}

searchInput.addEventListener("input", renderTransactions);
assetFilter.addEventListener("change", renderTransactions);

const exportButton = document.getElementById("exportActivity");
if (exportButton) {
  exportButton.addEventListener("click", () => {
    const rows = [["Reference", "From", "Amount", "To", "Received", "Status", "Date"]];
    dashboardSwaps.forEach((item) => rows.push([item.reference, item.from_asset, item.amount, item.to_asset, item.amount_received, item.status, item.created_at]));
    const csv = rows.map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(",")).join("\n");
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const ts = new Date().toISOString().replace(/[:\.]/g, "-");
    link.download = `swapper-africa-activity-${ts}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  });
}

if (signOutButton) {
  signOutButton.addEventListener("click", () => {
    SwapperAPI.signOut();
    window.location.replace("auth.html");
  });
}

initDashboard();
