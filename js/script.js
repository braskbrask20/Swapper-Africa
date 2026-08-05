const fromCoin = document.getElementById("fromCoin");
const toCoin = document.getElementById("toCoin");
const amountInput = document.getElementById("amount");
const quoteOutput = document.getElementById("quoteOutput");
const swapButton = document.getElementById("swapBtn");
const swapResult = document.getElementById("swapResult");
const fromBalance = document.getElementById("fromBalance");
const rateDetail = document.getElementById("rateDetail");
const feeDetail = document.getElementById("feeDetail");
const quoteExpiry = document.getElementById("quoteExpiry");

function showToast(message) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.setTimeout(() => toast.classList.remove("is-visible"), 3000);
}

async function refreshQuote() {
  if (!fromCoin || !toCoin || !amountInput) return null;

  const user = getUser();
  const amount = Number(amountInput.value);
  const quote = await fetchQuote(fromCoin.value, toCoin.value, amount);
  if (fromBalance) {
    const available = formatAsset(user.balance[fromCoin.value] ?? 0, fromCoin.value);
    fromBalance.textContent = `Available: ${available}`;
  }

  if (!quote) {
    if (quoteOutput) {
      quoteOutput.textContent = fromCoin.value === toCoin.value ? "Choose two different assets." : "Enter an amount to see your quote.";
    }
    if (rateDetail) rateDetail.textContent = "—";
    if (feeDetail) feeDetail.textContent = "—";
    if (swapButton) swapButton.disabled = true;
    return null;
  }

  if (quoteOutput) quoteOutput.textContent = formatAsset(quote.received, toCoin.value);
  if (rateDetail) rateDetail.textContent = `1 ${fromCoin.value} = ${formatAsset(quote.rate, toCoin.value)}`;
  if (feeDetail) feeDetail.textContent = formatAsset(quote.fee, toCoin.value);
  if (swapButton) swapButton.disabled = false;
  return quote;
}

function updateQuoteExpiry() {
  if (!quoteExpiry) return;
  // Prevent creating multiple intervals if this is called repeatedly
  if (updateQuoteExpiry._interval) clearInterval(updateQuoteExpiry._interval);
  let seconds = 30;
  quoteExpiry.textContent = `Quote refreshes in ${seconds}s`;
  updateQuoteExpiry._interval = setInterval(() => {
    seconds = seconds <= 1 ? 30 : seconds - 1;
    quoteExpiry.textContent = `Quote refreshes in ${seconds}s`;
  }, 1000);
}

[fromCoin, toCoin, amountInput].filter(Boolean).forEach((element) => {
  element.addEventListener("input", refreshQuote);
  element.addEventListener("change", refreshQuote);
});

const flipAssets = document.getElementById("flipAssets");
if (flipAssets) {
  flipAssets.addEventListener("click", () => {
    const currentFrom = fromCoin.value;
    fromCoin.value = toCoin.value;
    toCoin.value = currentFrom;
    refreshQuote();
  });
}

document.querySelectorAll("[data-amount-percent]").forEach((button) => {
  button.addEventListener("click", () => {
    const available = getUser().balance[fromCoin.value];
    amountInput.value = String(available * (Number(button.dataset.amountPercent) / 100));
    refreshQuote();
  });
});

async function fetchQuote(from, to, amount) {
  if (!from || !to || from === to || !Number.isFinite(amount) || amount <= 0) {
    return null;
  }

  try {
    return await SwapperAPI.quote(from, to, amount);
  } catch (error) {
    return getQuote(from, to, amount);
  }
}

if (swapButton) {
  swapButton.addEventListener("click", async () => {
    if (!SwapperAPI.isAuthenticated()) {
      window.location.href = "auth.html?next=swap.html";
      return;
    }

    const user = getUser();
    const amount = Number(amountInput.value);
    const quote = await refreshQuote();

    if (!quote) {
      swapResult.textContent = fromCoin.value === toCoin.value ? "Choose two different assets." : "Enter a valid amount to see your quote.";
      return;
    }
    if (!hasEnoughBalance(user, fromCoin.value, amount)) {
      swapResult.textContent = `You do not have enough ${fromCoin.value} for this swap.`;
      return;
    }

    swapResult.textContent = "";
    localStorage.setItem("pendingSwap", JSON.stringify({
      from: fromCoin.value,
      to: toCoin.value,
      amount,
      received: quote.received,
      fee: quote.fee,
      rate: quote.rate,
      createdAt: Date.now()
    }));
    const confirmationPage = window.location.pathname.includes("/pages/") ? "confirm-swap.html" : "pages/confirm-swap.html";
    window.location.href = confirmationPage;
  });
}

const modal = document.getElementById("walletModal");
const openWalletButtons = document.querySelectorAll("[data-open-wallet]");
const closeModal = document.getElementById("closeModal");

openWalletButtons.forEach((button) => button.addEventListener("click", () => {
  if (modal) modal.classList.add("is-open");
}));

if (closeModal) closeModal.addEventListener("click", () => modal.classList.remove("is-open"));
if (modal) modal.addEventListener("click", (event) => {
  if (event.target === modal) modal.classList.remove("is-open");
});

document.querySelectorAll(".wallet-option").forEach((button) => {
  button.addEventListener("click", () => {
    const selectedWallet = button.dataset.wallet;
    localStorage.setItem("connectedWallet", selectedWallet);
    localStorage.setItem("walletStatus", "Connected");
    if (modal) modal.classList.remove("is-open");
    showToast(`${selectedWallet} connected`);
  });
});

const startSwapButton = document.getElementById("startSwapBtn");
if (startSwapButton) startSwapButton.addEventListener("click", () => {
  document.getElementById("swapPanel").scrollIntoView({ behavior: "smooth", block: "center" });
  amountInput.focus();
});

const depositWalletButton = document.getElementById("depositWalletBtn");
if (depositWalletButton) depositWalletButton.addEventListener("click", () => {
  window.location.href = "pages/wallet.html";
});

refreshQuote();
updateQuoteExpiry();
