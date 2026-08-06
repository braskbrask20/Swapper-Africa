const dashboardUser = getUser();
const connectedWallet = localStorage.getItem("connectedWallet");

document.getElementById("totalBalance").textContent = formatUsd(getPortfolioValue(dashboardUser));
document.getElementById("totalTransactions").textContent = dashboardUser.transactions.length;
const walletStatus = document.getElementById("walletStatus");
walletStatus.textContent = connectedWallet || "Not connected";
document.getElementById("walletDot").classList.toggle("connected", Boolean(connectedWallet));

const transactionList = document.getElementById("transactionList");
const emptyActivity = document.getElementById("emptyActivity");
const searchInput = document.getElementById("activitySearch");
const assetFilter = document.getElementById("assetFilter");

function renderTransactions() {
  transactionList.innerHTML = "";
  const searchTerm = searchInput.value.trim().toLowerCase();
  const asset = assetFilter.value;
  const matchingTransactions = dashboardUser.transactions.filter((item) => {
    const haystack = `${item.id} ${item.from} ${item.to} ${item.status} ${item.date}`.toLowerCase();
    return (!searchTerm || haystack.includes(searchTerm)) && (!asset || item.from === asset || item.to === asset);
  });
  emptyActivity.hidden = matchingTransactions.length > 0;
  emptyActivity.textContent = dashboardUser.transactions.length ? "No swaps match your filters." : "No swaps yet. Your completed swaps will appear here.";
  matchingTransactions.forEach((item) => {
    const row = document.createElement("tr");
    [item.id.slice(-6), `${formatAsset(item.amount, item.from)}`, formatAsset(item.received, item.to), item.status, item.date].forEach((value, index) => {
      const cell = document.createElement("td");
      if (index === 3) cell.innerHTML = `<span class="status-pill">${value}</span>`;
      else cell.textContent = value;
      row.appendChild(cell);
    });
    transactionList.appendChild(row);
  });
}

searchInput.addEventListener("input", renderTransactions);
assetFilter.addEventListener("change", renderTransactions);
document.getElementById("exportActivity").addEventListener("click", () => {
  const rows = [["Reference", "From", "Amount", "To", "Received", "Status", "Date"]];
  dashboardUser.transactions.forEach((item) => rows.push([item.id, item.from, item.amount, item.to, item.received, item.status, item.date]));
  const csv = rows.map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(",")).join("\n");
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  link.download = "swapper-africa-activity.csv";
  link.click();
  URL.revokeObjectURL(link.href);
});

renderTransactions();
