/* ==========================================================================
   api.js — HTTP client for the API Gateway
   ========================================================================== */

const GATEWAY_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://localhost:5000"
  : window.location.origin;

const TOKEN_KEY = "phishguard_token";
const EMAIL_KEY = "phishguard_email";
const EXPIRES_AT_KEY = "phishguard_expires_at";

const REFRESH_MARGIN_MS = 5 * 60 * 1000;
const KEEP_ALIVE_INTERVAL_MS = 60 * 1000;

let refreshPromise = null;
let keepAliveTimer = null;

function parseTokenExpiryMs(token) {
  try {
    const payload = JSON.parse(
      atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))
    );
    return payload.exp ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}

const Session = {
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },
  getEmail() {
    return localStorage.getItem(EMAIL_KEY);
  },
  getExpiresAt() {
    const stored = localStorage.getItem(EXPIRES_AT_KEY);
    if (stored) {
      const value = Number(stored);
      if (!Number.isNaN(value)) return value;
    }
    const token = this.getToken();
    return token ? parseTokenExpiryMs(token) : null;
  },
  set(token, email, expiresIn) {
    localStorage.setItem(TOKEN_KEY, token);
    if (email) localStorage.setItem(EMAIL_KEY, email);
    const expiresAt = expiresIn
      ? Date.now() + expiresIn * 1000
      : parseTokenExpiryMs(token);
    if (expiresAt) {
      localStorage.setItem(EXPIRES_AT_KEY, String(expiresAt));
    }
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EMAIL_KEY);
    localStorage.removeItem(EXPIRES_AT_KEY);
    this.stopKeepAlive();
  },
  isAuthenticated() {
    return !!this.getToken();
  },
  needsRefresh() {
    const expiresAt = this.getExpiresAt();
    if (!expiresAt) return false;
    return expiresAt - Date.now() < REFRESH_MARGIN_MS;
  },
  async tryRefresh() {
    if (!this.isAuthenticated()) return false;
    if (refreshPromise) return refreshPromise;

    refreshPromise = (async () => {
      try {
        const result = await apiRequest("/api/auth/refresh", {
          method: "POST",
          auth: true,
          skipSessionRetry: true,
        });
        this.set(result.token, this.getEmail(), result.expires_in);
        return true;
      } catch {
        return false;
      } finally {
        refreshPromise = null;
      }
    })();

    return refreshPromise;
  },
  async tryRefreshIfNeeded() {
    if (!this.isAuthenticated() || !this.needsRefresh()) return false;
    return this.tryRefresh();
  },
  startKeepAlive() {
    if (keepAliveTimer) return;

    keepAliveTimer = setInterval(() => {
      this.tryRefreshIfNeeded();
    }, KEEP_ALIVE_INTERVAL_MS);

    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") {
        this.tryRefreshIfNeeded();
      }
    });

    this.tryRefreshIfNeeded();
  },
  stopKeepAlive() {
    if (!keepAliveTimer) return;
    clearInterval(keepAliveTimer);
    keepAliveTimer = null;
  },
  requireAuth() {
    if (!this.isAuthenticated()) {
      window.location.href = "index.html";
      return;
    }
    this.startKeepAlive();
  },
  redirectIfAuthenticated() {
    if (this.isAuthenticated()) {
      window.location.href = "dashboard.html";
    }
  },
};

class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

/**
 * Executes a request against the gateway.
 * @param {string} path - path from GATEWAY_URL, e.g. "/api/auth/login"
 * @param {object} options
 * @param {string} [options.method]
 * @param {object} [options.body]
 * @param {boolean} [options.auth] - includes the Authorization header
 * @param {boolean} [options.raw] - returns the Response instead of JSON (e.g. CSV)
 * @param {boolean} [options.skipSessionRetry] - do not attempt token refresh on 401
 * @param {boolean} [options._isRetry] - internal flag to avoid infinite retry loops
 */
async function apiRequest(path, {
  method = "GET",
  body,
  auth = false,
  raw = false,
  skipSessionRetry = false,
  _isRetry = false,
} = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = Session.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${GATEWAY_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (networkError) {
    throw new ApiError(
      "Could not reach the server. Check that the Docker stack is running.",
      0,
      null
    );
  }

  if (response.status === 401 && auth && !skipSessionRetry && !_isRetry) {
    const refreshed = await Session.tryRefresh();
    if (refreshed) {
      return apiRequest(path, {
        method,
        body,
        auth,
        raw,
        skipSessionRetry,
        _isRetry: true,
      });
    }
    Session.clear();
    window.location.href = "index.html?expired=1";
    throw new ApiError("Session expired.", 401, null);
  }

  if (response.status === 401 && auth) {
    Session.clear();
    window.location.href = "index.html?expired=1";
    throw new ApiError("Session expired.", 401, null);
  }

  if (raw) {
    if (!response.ok) {
      throw new ApiError("Failed to retrieve file.", response.status, null);
    }
    return response;
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    /* no JSON body */
  }

  if (!response.ok || (payload && payload.status === "error")) {
    const message = (payload && payload.message) || `Unexpected error (${response.status}).`;
    throw new ApiError(message, response.status, payload);
  }

  return payload;
}

const Api = {
  // --- auth ---
  register(email, password, name) {
    return apiRequest("/api/auth/register", {
      method: "POST",
      body: { email, password, name },
    });
  },
  login(email, password) {
    return apiRequest("/api/auth/login", {
      method: "POST",
      body: { email, password },
    });
  },
  refresh() {
    return apiRequest("/api/auth/refresh", { method: "POST", auth: true, skipSessionRetry: true });
  },
  logout() {
    return apiRequest("/api/auth/logout", { method: "POST", auth: true });
  },

  // --- campaigns ---
  listCampaigns() {
    return apiRequest("/api/campaigns", { auth: true });
  },
  getCampaign(id) {
    return apiRequest(`/api/campaigns/${id}`, { auth: true });
  },
  createCampaign(data) {
    return apiRequest("/api/campaigns", { method: "POST", body: data, auth: true });
  },
  updateCampaign(id, data) {
    return apiRequest(`/api/campaigns/${id}`, { method: "PUT", body: data, auth: true });
  },
  deleteCampaign(id) {
    return apiRequest(`/api/campaigns/${id}`, { method: "DELETE", auth: true });
  },
  sendCampaign(id) {
    return apiRequest(`/api/campaigns/${id}/send`, { method: "POST", auth: true });
  },

  // --- analytics ---
  getDashboard() {
    return apiRequest("/api/analytics/dashboard", { auth: true });
  },
  getCampaignAnalytics(id) {
    return apiRequest(`/api/analytics/campaigns/${id}`, { auth: true });
  },
  async exportCampaignCsv(id) {
    return apiRequest(`/api/analytics/campaigns/${id}/export`, { auth: true, raw: true });
  },
};
