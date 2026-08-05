let swapData = null;
try { swapData = JSON.parse(localStorage.getItem("pendingSwap")); } catch (error) { localStorage.removeItem("pendingSwap"); }

if (!swapData || !swapData.from || !swapData.to || !Number.isFinite(swapData.amount) || !Number.isFinite(swapData.received)) {
  window.location.replace("swap.html");
} else {
  document.getElementById("confirmFrom").textContent = formatAsset(swapData.amount, swapData.from);
  document.getElementById("confirmTo").textContent = formatAsset(swapData.received, swapData.to);
  document.getElementById("confirmRate").textContent = `1 ${swapData.from} = ${formatAsset(swapData.rate, swapData.to)}`;
  document.getElementById("confirmFee").textContent = formatAsset(swapData.fee, swapData.to);

  document.getElementById("confirmSwapBtn").addEventListener("click", () => {
    const button = document.getElementById("confirmSwapBtn");
    button.disabled = true;
    button.textContent = "Confirming…";
    const result = swapCrypto(swapData.from, swapData.to, swapData.amount, swapData.received);
    if (result.success) {
      localStorage.removeItem("pendingSwap");
      window.location.href = "dashboard.html";
    } else {
      button.disabled = false;
      button.textContent = "Confirm swap";
      document.getElementById("confirmMessage").textContent = result.message;
    }
  });
}
