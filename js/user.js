// Legacy initializer. The active wallet engine only creates this profile once,
// so visiting another page never overwrites a user's local swap history.
if (!localStorage.getItem("userData")) {
  localStorage.setItem("userData", JSON.stringify({
    username: "Swapper User",
    wallet: "",
    balance: { BTC: 1, ETH: 5, USDT: 10000, SOL: 20 },
    transactions: []
  }));
}
