// SWAP CALCULATOR

const swapButton = document.getElementById("swapBtn");


const exchangeRates = {

BTC: 118000,
ETH: 3800,
USDT: 1,
SOL: 180

};



if (swapButton) {


swapButton.addEventListener("click", function(){


const from = document.getElementById("fromCoin").value;

const to = document.getElementById("toCoin").value;

const amount = Number(
document.getElementById("amount").value
);


const result =
document.getElementById("swapResult");



if(!amount || amount <= 0){

result.textContent =
"Please enter a valid amount.";

return;

// CHECK USER BALANCE

let user =
JSON.parse(localStorage.getItem("userData"));


if(user && user.balance[from] < amount){


result.textContent =
`Insufficient ${from} balance.`;


return;

}


}



const usdValue =
amount * exchangeRates[from];


const convertedAmount =
usdValue / exchangeRates[to];



result.textContent =
`${amount} ${from} ≈ ${convertedAmount.toFixed(6)} ${to}`;



// SAVE TRANSACTION

user =
JSON.parse(localStorage.getItem("userData"));



if(!user){

user = {

username:"Swapper User",

wallet:"",

balance:{
BTC:0,
ETH:0,
USDT:0,
SOL:0
},

transactions:[]

};

}

if(user.balance[from] < amount){

result.textContent =
`You do not have enough ${from}`;

return;

}

// UPDATE BALANCES

// Remove sent asset

user.balance[from] =
user.balance[from] - amount;


// Add received asset

user.balance[to] =
user.balance[to] + convertedAmount;;

user.transactions.push({

id:
"SWP-" + Date.now(),

from: from,

to: to,

amount: amount,

received: convertedAmount.toFixed(6),

status:"Completed",

date:new Date().toLocaleString()

});



localStorage.setItem(
"userData",
JSON.stringify(user)
);


});


}
