const SWAPPER_RATES = {
  BTC: 118000,
  ETH: 3800,
  USDT: 1,
  SOL: 180
};

const SWAPPER_ASSETS = ["BTC", "ETH", "USDT", "SOL"];

function createDemoUser() {
  return {
    username: "Swapper User",
    wallet: "",
    balance: { BTC: 1, ETH: 5, USDT: 10000, SOL: 20 },
    transactions: []
  };
}

function getUserDataKey() {
  if (typeof SwapperAPI === "undefined" || !SwapperAPI.isAuthenticated()) return "userData";
  try {
    const account = JSON.parse(localStorage.getItem("swapper_profile"));
    return account && account.id ? `userData:${account.id}` : "userData";
  } catch (error) {
    return "userData";
  }
}

function getUser() {
  try {
    const savedUser = JSON.parse(localStorage.getItem(getUserDataKey()));
    if (savedUser && savedUser.balance && Array.isArray(savedUser.transactions)) {
      return savedUser;
    }
  } catch (error) {
    // A fresh demo profile is safer than allowing malformed local data to stop the UI.
  }

  const user = createDemoUser();
  saveUser(user);
  return user;
}

function saveUser(user) {
  localStorage.setItem(getUserDataKey(), JSON.stringify(user));
}

function resetDemoUser() {
  const user = createDemoUser();
  saveUser(user);
  localStorage.removeItem("pendingSwap");
  return user;
}

function getPortfolioValue(user) {
  return SWAPPER_ASSETS.reduce((total, asset) => {
    return total + ((Number(user.balance[asset]) || 0) * SWAPPER_RATES[asset]);
  }, 0);
}

function formatUsd(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2
  }).format(value);
}

function formatAsset(value, asset) {
  const maximumFractionDigits = asset === "USDT" ? 2 : 6;
  return `${new Intl.NumberFormat("en-US", { maximumFractionDigits }).format(value)} ${asset}`;
}

function hasEnoughBalance(user, coin, amount) {
  return Number.isFinite(amount) && amount > 0 &&
    Object.prototype.hasOwnProperty.call(user.balance, coin) &&
    user.balance[coin] >= amount;
}

function getQuote(from, to, amount) {
  if (!SWAPPER_RATES[from] || !SWAPPER_RATES[to] || from === to || !Number.isFinite(amount) || amount <= 0) {
    return null;
  }

  const grossReceived = (amount * SWAPPER_RATES[from]) / SWAPPER_RATES[to];
  const fee = grossReceived * 0.0025;
  return {
    rate: SWAPPER_RATES[from] / SWAPPER_RATES[to],
    fee,
    received: grossReceived - fee
  };
}

function swapCrypto(from, to, amount, received) {
  const user = getUser();

  if (!hasEnoughBalance(user, from, amount) || from === to || !Number.isFinite(received) || received <= 0) {
    return { success: false, message: "Your swap could not be completed. Check your balance and quote." };
  }

  user.balance[from] -= amount;
  user.balance[to] += received;
  user.transactions.unshift({
    id: `SWP-${Date.now()}`,
    from,
    to,
    amount,
    received,
    status: "Completed",
    date: new Date().toLocaleString()
  });
  saveUser(user);
  return { success: true, message: "Swap completed." };
}

function isSignedIn() {
  return typeof SwapperAPI !== "undefined" && SwapperAPI.isAuthenticated();
}

async function fetchRemoteAccount() {
  const [balanceRows, swaps] = await Promise.all([
    SwapperAPI.request("/v1/balances"),
    SwapperAPI.request("/v1/swaps")
  ]);
  const balance = { BTC: 0, ETH: 0, USDT: 0, SOL: 0 };
  balanceRows.forEach((row) => { balance[row.asset] = row.amount; });
  const transactions = swaps.map((swap) => ({
    id: swap.reference,
    from: swap.from_asset,
    to: swap.to_asset,
    amount: swap.amount,
    received: swap.amount_received,
    status: swap.status.charAt(0).toUpperCase() + swap.status.slice(1),
    date: new Date(swap.created_at).toLocaleString()
  }));
  return { balance, transactions };
}

// Guests keep the local browser demo untouched; signed-in users get their real,
// backend-owned balance and swap history instead. Always await this — for guests it
// resolves immediately, for signed-in users it makes a network call.
async function getAccountSnapshot() {
  if (!isSignedIn()) return getUser();
  return fetchRemoteAccount();
}
