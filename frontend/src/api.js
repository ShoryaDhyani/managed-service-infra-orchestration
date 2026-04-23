export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:9000'

export async function createProject(body) {
  const res = await fetch(`${API_BASE}/project`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return await res.json()
}

export function wsUrlForChannel(channel) {
  const base = API_BASE.replace(/^http/, 'ws')
  return `${base.replace(/\/$/, '')}/ws/${encodeURIComponent(channel)}`
}
