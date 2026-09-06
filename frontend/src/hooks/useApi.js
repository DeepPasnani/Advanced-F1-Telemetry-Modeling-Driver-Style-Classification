// Same-origin by default (relative /api — works via the Vite dev proxy and
// when a single backend also serves the built frontend, e.g. Docker).
// Set VITE_API_BASE_URL at build time when the frontend is deployed
// separately from the backend (e.g. frontend on Vercel, backend elsewhere).
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const BASE = `${API_BASE_URL}/api`

export function fetchApi(path, options = {}, signal) {
  const url = `${BASE}${path}`
  return fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    signal,
    ...options,
  }).then(async (res) => {
    const data = await res.json()
    if (!res.ok) {
      const msg = data.detail || data.message || `Request failed (${res.status})`
      throw new Error(msg)
    }
    return data
  })
}

export async function getSessions(signal) {
  return fetchApi('/sessions', {}, signal)
}

export async function loadSession(year, grandPrix, sessionType = 'R', signal) {
  return fetchApi('/sessions/load', {
    method: 'POST',
    body: JSON.stringify({ year, grand_prix: grandPrix, session_type: sessionType }),
  }, signal)
}

export async function getSessionInfo(sessionId, signal) {
  return fetchApi(`/sessions/${sessionId}`, {}, signal)
}

export async function getDrivers(sessionId, signal) {
  return fetchApi(`/sessions/${sessionId}/drivers`, {}, signal)
}

export async function analyzeDrivers(sessionId, driverCodes, signal) {
  return fetchApi(`/sessions/${sessionId}/analyze`, {
    method: 'POST',
    body: JSON.stringify({ driver_codes: driverCodes }),
  }, signal)
}

export async function getAnalysis(analysisId, signal) {
  return fetchApi(`/analysis/${analysisId}`, {}, signal)
}

export async function getReport(analysisId, signal) {
  return fetchApi(`/analysis/${analysisId}/report`, {}, signal)
}
