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

function getUser() {
  try {
    const savedUser = JSON.parse(localStorage.getItem("userData"));
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
  localStorage.setItem("userData", JSON.stringify(user));
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
