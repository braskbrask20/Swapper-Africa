const form = document.getElementById("authForm");
const modeButton = document.getElementById("authMode");
const forgotButton = document.getElementById("forgotPassword");
const message = document.getElementById("authMessage");
const devHint = document.getElementById("devHint");
const submit = document.getElementById("authSubmit");

const nameField = document.getElementById("nameField");
const emailField = document.getElementById("emailField");
const passwordField = document.getElementById("passwordField");
const fullNameInput = document.getElementById("fullName");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");

const urlParams = new URLSearchParams(window.location.search);
const actionToken = urlParams.get("token");
const requestedMode = urlParams.get("mode");

let mode = requestedMode === "reset" && actionToken ? "reset-confirm" : "login";

const COPY = {
  login: { title: "Welcome back", description: "Sign in to manage your swaps securely.", submit: "Sign in <span>→</span>" },
  register: { title: "Create your account", description: "Start with a secure account to track your swaps.", submit: "Create account <span>→</span>" },
  "reset-request": { title: "Reset your password", description: "Enter your email and we'll send you a reset link.", submit: "Send reset link <span>→</span>" },
  "reset-confirm": { title: "Choose a new password", description: "Enter a new password for your account.", submit: "Set new password <span>→</span>" }
};

function setMode(next) {
  mode = next;
  message.textContent = "";
  devHint.hidden = true;

  nameField.hidden = mode !== "register";
  fullNameInput.required = mode === "register";

  emailField.hidden = mode === "reset-confirm";
  emailInput.required = mode !== "reset-confirm";

  passwordField.hidden = mode === "reset-request";
  passwordInput.required = mode !== "reset-request";
  passwordInput.autocomplete = mode === "register" || mode === "reset-confirm" ? "new-password" : "current-password";

  document.getElementById("authTitle").textContent = COPY[mode].title;
  document.getElementById("authDescription").textContent = COPY[mode].description;
  submit.innerHTML = COPY[mode].submit;

  forgotButton.hidden = mode !== "login";
  modeButton.textContent = mode === "register" ? "Already have an account? Sign in" : "New to Swapper Africa? Create an account";
  if (mode === "reset-request") modeButton.textContent = "Back to sign in";
}

modeButton.addEventListener("click", () => setMode(mode === "register" ? "login" : "register"));
forgotButton.addEventListener("click", () => setMode("reset-request"));

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "";
  devHint.hidden = true;
  submit.disabled = true;
  try {
    if (mode === "login") {
      await SwapperAPI.authenticate("/v1/auth/login", { email: emailInput.value, password: passwordInput.value });
      window.location.href = "dashboard.html";
      return;
    }
    if (mode === "register") {
      await SwapperAPI.authenticate("/v1/auth/register", { email: emailInput.value, password: passwordInput.value, full_name: fullNameInput.value });
      window.location.href = "dashboard.html";
      return;
    }
    if (mode === "reset-request") {
      const response = await SwapperAPI.request("/v1/auth/password-reset/request", { method: "POST", body: JSON.stringify({ email: emailInput.value }) });
      message.textContent = response.detail;
      if (response.dev_reset_token) {
        const link = `${window.location.origin}${window.location.pathname}?mode=reset&token=${encodeURIComponent(response.dev_reset_token)}`;
        devHint.innerHTML = `No email provider is connected yet (dev mode) — here's your reset link: <a href="${link}">${link}</a>`;
        devHint.hidden = false;
      }
      submit.disabled = false;
      return;
    }
    if (mode === "reset-confirm") {
      const response = await SwapperAPI.request("/v1/auth/password-reset/confirm", { method: "POST", body: JSON.stringify({ token: actionToken, new_password: passwordInput.value }) });
      await SwapperAPI.completeSession(response);
      window.location.href = "dashboard.html";
    }
  } catch (error) {
    message.textContent = error.message;
    submit.disabled = false;
  }
});

async function runVerifyMode() {
  document.getElementById("authSection").hidden = true;
  const verifySection = document.getElementById("verifySection");
  verifySection.hidden = false;
  try {
    await SwapperAPI.request("/v1/auth/verify-email/confirm", { method: "POST", body: JSON.stringify({ token: actionToken }) });
    document.getElementById("verifyTitle").textContent = "Email verified";
    document.getElementById("verifyDescription").textContent = "Thanks — your email address is now confirmed.";
  } catch (error) {
    document.getElementById("verifyTitle").textContent = "Verification link invalid";
    document.getElementById("verifyDescription").textContent = error.message;
  }
}

if (requestedMode === "verify" && actionToken) {
  runVerifyMode();
} else {
  setMode(mode);
  if (mode !== "reset-confirm" && SwapperAPI.isAuthenticated()) window.location.replace("dashboard.html");
}
