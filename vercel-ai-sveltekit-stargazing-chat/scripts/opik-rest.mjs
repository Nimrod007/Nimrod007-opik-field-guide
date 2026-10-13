// Tiny helpers for Opik's REST API (used only by the demo: rule setup and score checks).
// The app itself never calls these; it exports traces through opik-vercel.
const base = (process.env.OPIK_URL_OVERRIDE || "http://localhost:5173/api/").replace(/\/?$/, "/");
const headers = {
  "Content-Type": "application/json",
  "Comet-Workspace": process.env.OPIK_WORKSPACE || "default",
  ...(process.env.OPIK_API_KEY ? { Authorization: process.env.OPIK_API_KEY } : {}),
};

export async function api(method, route, body) {
  const res = await fetch(base + route.replace(/^\//, ""), {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  if (!res.ok) throw new Error(`${method} ${route} -> HTTP ${res.status}: ${text.slice(0, 400)}`);
  return text ? JSON.parse(text) : {};
}
