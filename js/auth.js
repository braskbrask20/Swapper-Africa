let isRegistration = false;
const form = document.getElementById("authForm");
const modeButton = document.getElementById("authMode");

function updateMode() {
  document.getElementById("authTitle").textContent = isRegistration ? "Create your account" : "Welcome back";
  document.getElementById("authDescription").textContent = isRegistration ? "Start with a secure account to track your swaps." : "Sign in to manage your swaps securely.";
  document.getElementById("nameField").hidden = !isRegistration;
  document.getElementById("fullName").required = isRegistration;
  document.getElementById("authSubmit").innerHTML = isRegistration ? "Create account <span>→</span>" : "Sign in <span>→</span>";
  modeButton.textContent = isRegistration ? "Already have an account? Sign in" : "New to Swapper Africa? Create an account";
}

modeButton.addEventListener("click", () => { isRegistration = !isRegistration; updateMode(); });
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = document.getElementById("authMessage");
  const submit = document.getElementById("authSubmit");
  message.textContent = "";
  submit.disabled = true;
  try {
    const payload = { email: document.getElementById("email").value, password: document.getElementById("password").value };
    if (isRegistration) payload.full_name = document.getElementById("fullName").value;
    await SwapperAPI.authenticate(isRegistration ? "/v1/auth/register" : "/v1/auth/login", payload);
    window.location.href = "dashboard.html";
  } catch (error) { message.textContent = error.message; submit.disabled = false; }
});

if (SwapperAPI.isAuthenticated()) window.location.replace("dashboard.html");
