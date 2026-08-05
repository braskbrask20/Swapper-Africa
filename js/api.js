const SwapperAPI = (() => {
  const baseUrl = window.SWAPPER_API_URL || "http://localhost:8000";
  const tokenKey = "swapper_access_token";

  function token() { return localStorage.getItem(tokenKey); }
  function isAuthenticated() { return Boolean(token()); }
  function setToken(value) { localStorage.setItem(tokenKey, value); }
  function signOut() { localStorage.removeItem(tokenKey); localStorage.removeItem("swapper_profile"); }

  async function request(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...options.headers };
    if (token()) headers.Authorization = `Bearer ${token()}`;
    let response;
    try {
      response = await fetch(`${baseUrl}${path}`, { ...options, headers });
    } catch (error) {
      throw new Error("We could not reach Swapper Africa. Please try again shortly.");
    }
    const body = await response.json();
    if (!response.ok) {
      if (response.status === 401) signOut();
      throw new Error(body.detail || "Something went wrong. Please try again.");
    }
    return body;
  }

  async function authenticate(path, payload) {
    const response = await request(path, { method: "POST", body: JSON.stringify(payload) });
    setToken(response.access_token);
    const profile = await request("/v1/auth/me");
    localStorage.setItem("swapper_profile", JSON.stringify(profile));
    return profile;
  }

  function updateHeader() {
    const action = document.querySelector(".header-action[data-auth-action]");
    if (!action) return;
    if (isAuthenticated()) {
      action.textContent = "My activity";
      action.href = action.dataset.dashboardHref || "pages/dashboard.html";
    } else {
      action.textContent = "Sign in";
      action.href = action.dataset.authHref || "pages/auth.html";
    }
  }

  return { baseUrl, token, isAuthenticated, signOut, request, authenticate, updateHeader };
})();

document.addEventListener("DOMContentLoaded", SwapperAPI.updateHeader);
