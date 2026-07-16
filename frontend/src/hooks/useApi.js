const BASE = '/api'

export async function fetchApi(path, options = {}) {
  const url = `${BASE}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`)
  }
  return data
}

export async function getSessions() {
  return fetchApi('/sessions')
}

export async function loadSession(year, grandPrix, sessionType = 'R') {
  return fetchApi('/sessions/load', {
    method: 'POST',
    body: JSON.stringify({ year, grand_prix: grandPrix, session_type: sessionType }),
  })
}

export async function getDrivers(sessionId) {
  return fetchApi(`/sessions/${sessionId}/drivers`)
}

export async function analyzeDrivers(sessionId, driverCodes) {
  return fetchApi(`/sessions/${sessionId}/analyze`, {
    method: 'POST',
    body: JSON.stringify({ driver_codes: driverCodes }),
  })
}

export async function getReport(analysisId) {
  return fetchApi(`/analysis/${analysisId}/report`)
}
