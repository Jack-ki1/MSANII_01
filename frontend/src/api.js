// Same-origin by default (Vite proxy in dev, Flask in production). Set VITE_API_BASE to call a different origin (then add it to MSANII_ALLOWED_ORIGINS).
const BASE = import.meta.env.VITE_API_BASE || "/api";
export const API_BASE = BASE;
let csrf = "", lost = null;
export const setCsrf = (t) => { csrf = t; };
export const setOnAuthLost = (f) => { lost = f; };
export async function api(path, { method = "GET", body, form } = {}) {
  const h = {}; if (csrf) h["X-CSRF-Token"] = csrf; if (body !== undefined) h["Content-Type"] = "application/json";
  const r = await fetch(BASE + path, { method, credentials: "include", headers: h, body: form || (body !== undefined ? JSON.stringify(body) : undefined) });
  let j = {}; try { j = await r.json(); } catch { /* empty body */ }
  if (!r.ok) {
    if (r.status === 401 && !path.startsWith("/auth/") && lost) lost();
    throw Object.assign(new Error(j.error || r.statusText), { status: r.status, data: j });
  }
  return j;
}
