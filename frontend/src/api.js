export const API_BASE = import.meta.env.VITE_API_BASE;

// ─── Token helpers ──────────────────────────────────────
function getToken() {
  return localStorage.getItem("auth_token");
}

function authHeaders() {
  const token = getToken();
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

// ─── Auth endpoints ──────────────────────────────────────
export async function login(username, password) {
  const res = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Login failed (${res.status})`);
  }
  return res.json();
}

export async function register(username, email, password) {
  const res = await fetch(`${API_BASE}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Registration failed (${res.status})`);
  }
  return res.json();
}

// ─── Logout endpoint ────────────────────────────────────
// Calls backend to invalidate the JWT. Silently fails if
// the endpoint doesn't exist yet — client clears state anyway.
export async function logout() {
  try {
    await fetch(`${API_BASE}/logout`, {
      method: "POST",
      headers: authHeaders(),
    });
  } catch {
    // Backend logout endpoint may not exist yet — that's fine
  }
}

// ─── User endpoints ──────────────────────────────────────
export async function getUser(username) {
  const res = await fetch(`${API_BASE}/users/${encodeURIComponent(username)}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to fetch user (${res.status})`);
  return res.json();
}

// ─── Project endpoints ───────────────────────────────────
export async function getProjects() {
  const res = await fetch(`${API_BASE}/project/list`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to fetch projects (${res.status})`);
  return res.json();
}

export async function deployProject(body) {
  const res = await fetch(`${API_BASE}/project/deploy`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Deploy failed (${res.status})`);
  }
  const response = await res.json();
  if (response.status === "error") {
    throw new Error(response.message);
  }
  return response;
}

// ─── WebSocket ──────────────────────────────────────────
export function wsUrlForChannel(channel) {
  const wsBase = API_BASE.replace("/api/v1", "").replace(/^http/, "ws");
  return `${wsBase.replace(/\/$/, "")}/ws/${encodeURIComponent(channel)}`;
}