// Same-origin by default (relative /api — works via the Vite dev proxy and
// when a single backend also serves the built frontend, e.g. Docker).
// Set VITE_API_BASE_URL at build time when the frontend is deployed
// separately from the backend (e.g. frontend on Vercel, backend elsewhere).
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const BASE = `${API_BASE_URL}/api`

const NETWORK_ERROR_RETRIES = 2
const NETWORK_ERROR_RETRY_DELAY_MS = 2500

export function fetchApi(path, options = {}, signal, retriesLeft = NETWORK_ERROR_RETRIES) {
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
  }).catch((err) => {
    // fetch() rejects with a bare TypeError specifically when the request
    // never reached a server at all (connection refused/reset, DNS
    // failure) — as opposed to a real HTTP error response, or a deliberate
    // AbortController abort. On a free-tier host that's almost always a
    // backend that's mid-restart or waking from a cold start, not a
    // permanent failure, so retry a couple of times before giving up.
    const isNetworkError = err instanceof TypeError
    if (isNetworkError && retriesLeft > 0 && !signal?.aborted) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          fetchApi(path, options, signal, retriesLeft - 1).then(resolve, reject)
        }, NETWORK_ERROR_RETRY_DELAY_MS)
      })
    }
    throw err
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
