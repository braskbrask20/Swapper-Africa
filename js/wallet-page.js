const walletName = localStorage.getItem("connectedWallet");
document.getElementById("walletStatus").textContent = walletName || "Not connected";
document.getElementById("walletDot").classList.toggle("connected", Boolean(walletName));

const assetList = document.getElementById("assetList");
const demoNotice = document.getElementById("demoNotice");
const resetButton = document.getElementById("resetDemo");

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

if (isSignedIn()) {
  demoNotice.textContent = "These are demo funds held in your Swapper Africa account — not a real wallet, and not real money.";
  resetButton.hidden = true;
} else {
  resetButton.addEventListener("click", () => {
    if (window.confirm("Reset your demo balances and swap activity?")) {
      resetDemoUser();
      window.location.reload();
    }
  });
}

async function init() {
  const clearSlowLoadHint = warnIfSlowToLoad(assetList, "Waking up the server — this can take up to a minute on the first request.");
  try {
    const walletUser = await getAccountSnapshot();
    document.getElementById("walletPortfolioValue").textContent = formatUsd(getPortfolioValue(walletUser));
    assetList.innerHTML = "";
    SWAPPER_ASSETS.forEach((asset) => {
      const amount = Number(walletUser.balance[asset]) || 0;
      const item = document.createElement("div");
      item.className = "asset-row-card";
      item.innerHTML = `<span class="asset-symbol">${asset}</span><div><strong>${asset === "USDT" ? "Tether" : asset}</strong><span>${asset}</span></div><div class="asset-value"><strong>${formatAsset(amount, asset)}</strong><span>${formatUsd(amount * SWAPPER_RATES[asset])}</span></div>`;
      assetList.appendChild(item);
    });
  } catch (error) {
    assetList.innerHTML = "";
    const message = document.createElement("p");
    message.className = "empty-state";
    message.textContent = "Could not load your wallet. Please refresh to try again.";
    assetList.appendChild(message);
  } finally {
    clearSlowLoadHint();
  }
}

init();
