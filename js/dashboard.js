const dashboardUser = getUser();
const connectedWallet = localStorage.getItem("connectedWallet");

document.getElementById("totalBalance").textContent = formatUsd(getPortfolioValue(dashboardUser));
document.getElementById("totalTransactions").textContent = dashboardUser.transactions.length;
const walletStatus = document.getElementById("walletStatus");
walletStatus.textContent = connectedWallet || "Not connected";
document.getElementById("walletDot").classList.toggle("connected", Boolean(connectedWallet));

const transactionList = document.getElementById("transactionList");
const emptyActivity = document.getElementById("emptyActivity");
if (dashboardUser.transactions.length) {
  emptyActivity.hidden = true;
  dashboardUser.transactions.forEach((item) => {
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
