const SwapperAPI = (() => {
  const baseUrl = window.SWAPPER_API_URL || "http://127.0.0.1:8000";
  const tokenKey = "swapper_access_token";
  const profileKey = "swapper_profile";
  let profileCache = null;

  function token() { return localStorage.getItem(tokenKey); }
  function isAuthenticated() { return Boolean(token()); }
  function setToken(value) { localStorage.setItem(tokenKey, value); }
  function clearSession() { localStorage.removeItem(tokenKey); localStorage.removeItem(profileKey); profileCache = null; }
  function signOut() { clearSession(); updateHeader(); }

  async function request(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...options.headers };
    if (token()) headers.Authorization = `Bearer ${token()}`;
    let response;
    try {
      response = await fetch(`${baseUrl}${path}`, { ...options, headers });
    } catch (error) {
      throw new Error("We could not reach Swapper Africa. Please try again shortly.");
    }

    let body = null;
    try { body = await response.json(); } catch { body = null; }
    if (!response.ok) {
      if (response.status === 401) clearSession();
      throw new Error(body?.detail || "Something went wrong. Please try again.");
    }
    return body;
  }

  async function authenticate(path, payload) {
    const response = await request(path, { method: "POST", body: JSON.stringify(payload) });
    setToken(response.access_token);
    const profile = await request("/v1/auth/me");
    localStorage.setItem(profileKey, JSON.stringify(profile));
    profileCache = profile;
    updateHeader();
    return profile;
  }

  async function getProfile(reload = false) {
    if (!isAuthenticated()) return null;
    if (!profileCache && !reload) {
      const stored = localStorage.getItem(profileKey);
      if (stored) {
        try { profileCache = JSON.parse(stored); } catch {
          profileCache = null;
        }
      }
    }
    if (!profileCache || reload) {
      profileCache = await request("/v1/auth/me");
      localStorage.setItem(profileKey, JSON.stringify(profileCache));
    }
    return profileCache;
  }

  async function quote(from, to, amount) {
    return await request("/v1/quotes", { method: "POST", body: JSON.stringify({ from_asset: from, to_asset: to, amount }) });
  }

  async function createSwap(from, to, amount, expectedReceived) {
    return await request("/v1/swaps", { method: "POST", body: JSON.stringify({ from_asset: from, to_asset: to, amount, expected_received: expectedReceived }) });
  }

  async function getSwaps() {
    return await request("/v1/swaps");
  }

  function updateHeader() {
    const actions = Array.from(document.querySelectorAll(".header-action[data-auth-action]"));
    if (!actions.length) return;
    actions.forEach((action) => {
      if (isAuthenticated()) {
        action.textContent = "My activity";
        action.href = action.dataset.dashboardHref || "pages/dashboard.html";
      } else {
        action.textContent = "Sign in";
        action.href = action.dataset.authHref || "pages/auth.html";
      }
    });
  }

  return { baseUrl, token, isAuthenticated, signOut, request, authenticate, updateHeader, getProfile, quote, createSwap, getSwaps };
})();

document.addEventListener("DOMContentLoaded", SwapperAPI.updateHeader);
