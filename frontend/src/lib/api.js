import axios from "axios";

// Resolve backend base URL:
// 1. If REACT_APP_BACKEND_URL is set → use it (production / preview).
// 2. Otherwise → use same-origin (works with CRA "proxy" in package.json during
//    local dev, and with reverse proxies like nginx / Codespaces port forwarding
//    in production).
const CONFIGURED_URL = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/+$/, "");
const BACKEND_URL = CONFIGURED_URL || "";

export const API = BACKEND_URL ? `${BACKEND_URL}/api` : "/api";

const TOKEN_KEY = "privyalgo_token";

export const auth = {
  getToken: () => {
    try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
  },
  setToken: (t) => {
    try { localStorage.setItem(TOKEN_KEY, t); } catch { /* ignore */ }
  },
  clearToken: () => {
    try { localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
  },
};

export const api = axios.create({
  baseURL: API,
  timeout: 20000,
});

// Attach Bearer token automatically
api.interceptors.request.use((config) => {
  const t = auth.getToken();
  if (t) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${t}`;
  }
  return config;
});

// Global response error handler — never let a network error crash the app
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.code === "ECONNABORTED" || err?.code === "ERR_NETWORK" || !err?.response) {
      // eslint-disable-next-line no-console
      console.warn("[api] network error — backend unreachable:", err?.message);
    } else if (err?.response?.status === 401) {
      // token invalid → clear silently, components decide UX
      auth.clearToken();
    }
    return Promise.reject(err);
  }
);

export function resolveImage(url) {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  if (url.startsWith("/api/")) {
    return BACKEND_URL ? `${BACKEND_URL}${url}` : url;
  }
  return url;
}

// Small helper: swallow network errors gracefully so pages never blank out.
export async function safeGet(path, opts) {
  try {
    const { data } = await api.get(path, opts);
    return { ok: true, data };
  } catch (err) {
    return { ok: false, error: err?.response?.data?.detail || err?.message || "network_error" };
  }
}
