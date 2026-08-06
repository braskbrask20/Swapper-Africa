let dashboardUser = { balance: { BTC: 0, ETH: 0, USDT: 0, SOL: 0 }, transactions: [] };

const connectedWallet = localStorage.getItem("connectedWallet");
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

async function initVerificationBanner() {
  if (!isSignedIn()) return;
  try {
    const profile = await SwapperAPI.request("/v1/auth/me");
    localStorage.setItem("swapper_profile", JSON.stringify(profile));
    if (profile.is_email_verified) return;

    const banner = document.getElementById("verifyBanner");
    const bannerText = document.getElementById("verifyBannerText");
    const resendButton = document.getElementById("resendVerification");
    banner.hidden = false;
    resendButton.addEventListener("click", async () => {
      resendButton.disabled = true;
      try {
        const response = await SwapperAPI.request("/v1/auth/verify-email/request", { method: "POST" });
        let text = response.detail;
        if (response.dev_verification_token) {
          const link = `${window.location.origin}${window.location.pathname.replace("dashboard.html", "")}auth.html?mode=verify&token=${encodeURIComponent(response.dev_verification_token)}`;
          text = `No email provider is connected yet (dev mode) — verify here: `;
          bannerText.textContent = text;
          const anchor = document.createElement("a");
          anchor.href = link;
          anchor.textContent = link;
          bannerText.appendChild(anchor);
          return;
        }
        bannerText.textContent = text;
      } finally {
        resendButton.disabled = false;
      }
    });
  } catch (error) {
    // Non-critical -- skip the banner rather than block the page on it.
  }
}

async function init() {
  const clearSlowLoadHint = warnIfSlowToLoad(emptyActivity, "Waking up the server — this can take up to a minute on the first request.");
  try {
    dashboardUser = await getAccountSnapshot();
    document.getElementById("totalBalance").textContent = formatUsd(getPortfolioValue(dashboardUser));
    document.getElementById("totalTransactions").textContent = dashboardUser.transactions.length;
    renderTransactions();
  } catch (error) {
    emptyActivity.hidden = false;
    emptyActivity.textContent = "Could not load your activity. Please refresh to try again.";
  } finally {
    clearSlowLoadHint();
  }
  initVerificationBanner();
}

init();
