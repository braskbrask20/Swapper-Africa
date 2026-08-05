const walletUser = getUser();
const walletName = localStorage.getItem("connectedWallet");
document.getElementById("walletPortfolioValue").textContent = formatUsd(getPortfolioValue(walletUser));
document.getElementById("walletStatus").textContent = walletName || "Not connected";
document.getElementById("walletDot").classList.toggle("connected", Boolean(walletName));

const assetList = document.getElementById("assetList");
SWAPPER_ASSETS.forEach((asset) => {
  const amount = Number(walletUser.balance[asset]) || 0;
  const item = document.createElement("div");
  item.className = "asset-row-card";
  item.innerHTML = `<span class="asset-symbol">${asset}</span><div><strong>${asset === "USDT" ? "Tether" : asset}</strong><span>${asset}</span></div><div class="asset-value"><strong>${formatAsset(amount, asset)}</strong><span>${formatUsd(amount * SWAPPER_RATES[asset])}</span></div>`;
  assetList.appendChild(item);
});

document.getElementById("copyAddress").addEventListener("click", async () => {
  const address = document.getElementById("depositAddress").textContent.trim();
  try {
    await navigator.clipboard.writeText(address);
    document.getElementById("copyAddress").textContent = "Copied";
  } catch (error) {
    document.getElementById("copyAddress").textContent = "Copy unavailable";
  }
  window.setTimeout(() => { document.getElementById("copyAddress").textContent = "Copy address"; }, 1800);
});

const resetButton = document.getElementById("resetDemo");
resetButton.addEventListener("click", () => {
  if (window.confirm("Reset your demo balances and swap activity?")) {
    resetDemoUser();
    window.location.reload();
  }
});
