/* ==========================================================================
   api.js — cliente HTTP para o API Gateway
   ========================================================================== */

const GATEWAY_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://localhost:5000"
  : window.location.origin;

const TOKEN_KEY = "phishguard_token";
const EMAIL_KEY = "phishguard_email";

const Session = {
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },
  getEmail() {
    return localStorage.getItem(EMAIL_KEY);
  },
  set(token, email) {
    localStorage.setItem(TOKEN_KEY, token);
    if (email) localStorage.setItem(EMAIL_KEY, email);
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EMAIL_KEY);
  },
  isAuthenticated() {
    return !!this.getToken();
  },
  requireAuth() {
    if (!this.isAuthenticated()) {
      window.location.href = "index.html";
    }
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
 * Executa um pedido contra o gateway.
 * @param {string} path - caminho a partir de GATEWAY_URL, ex. "/api/auth/login"
 * @param {object} options
 * @param {string} [options.method]
 * @param {object} [options.body]
 * @param {boolean} [options.auth] - inclui o cabeçalho Authorization
 * @param {boolean} [options.raw] - devolve a Response em vez de JSON (ex. CSV)
 */
async function apiRequest(path, { method = "GET", body, auth = false, raw = false } = {}) {
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
      "Não foi possível contactar o servidor. Verifique se o stack Docker está em execução.",
      0,
      null
    );
  }

  if (response.status === 401 && auth) {
    Session.clear();
    window.location.href = "index.html?expired=1";
    throw new ApiError("Sessão expirada.", 401, null);
  }

  if (raw) {
    if (!response.ok) {
      throw new ApiError("Falha ao obter o ficheiro.", response.status, null);
    }
    return response;
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    /* sem corpo JSON */
  }

  if (!response.ok || (payload && payload.status === "error")) {
    const message = (payload && payload.message) || `Erro inesperado (${response.status}).`;
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
