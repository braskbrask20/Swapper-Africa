const userData = {

username: "Swapper User",

wallet: "",

balance: {

BTC: 1,

ETH: 5,

USDT: 10000,

SOL: 20

},

transactions: []

};


localStorage.setItem(
"userData",
JSON.stringify(userData)
);