let swapData = null;
try { swapData = JSON.parse(localStorage.getItem("pendingSwap")); } catch (error) { localStorage.removeItem("pendingSwap"); }

if (!swapData || !swapData.from || !swapData.to || !Number.isFinite(swapData.amount) || !Number.isFinite(swapData.received) || !Number.isFinite(swapData.createdAt) || Date.now() - swapData.createdAt > 60000) {
  localStorage.removeItem("pendingSwap");
  window.location.replace("swap.html");
} else {
  document.getElementById("confirmFrom").textContent = formatAsset(swapData.amount, swapData.from);
  document.getElementById("confirmTo").textContent = formatAsset(swapData.received, swapData.to);
  document.getElementById("confirmRate").textContent = `1 ${swapData.from} = ${formatAsset(swapData.rate, swapData.to)}`;
  document.getElementById("confirmFee").textContent = formatAsset(swapData.fee, swapData.to);

  document.getElementById("confirmSwapBtn").addEventListener("click", async () => {
    const button = document.getElementById("confirmSwapBtn");
    const message = document.getElementById("confirmMessage");
    button.disabled = true;
    button.textContent = "Confirming…";
    message.textContent = "";
    try {
      if (isSignedIn()) {
        await SwapperAPI.request("/v1/swaps", {
          method: "POST",
          body: JSON.stringify({
            from_asset: swapData.from,
            to_asset: swapData.to,
            amount: swapData.amount,
            expected_received: swapData.received
          })
        });
      } else {
        const result = swapCrypto(swapData.from, swapData.to, swapData.amount, swapData.received);
        if (!result.success) throw new Error(result.message);
      }
      localStorage.removeItem("pendingSwap");
      window.location.href = "dashboard.html";
    } catch (error) {
      button.disabled = false;
      button.textContent = "Confirm swap";
      message.textContent = error.message;
    }
  });
}
