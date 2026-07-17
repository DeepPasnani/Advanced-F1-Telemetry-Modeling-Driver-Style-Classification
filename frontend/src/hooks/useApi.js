const BASE = '/api'

/* Track all active abort controllers so we can cancel on unmount */
const activeControllers = new Map()
let ctrlId = 0

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

/* Hook-safe wrapper: tracks the controller for cleanup */
export function useFetch() {
  const controller = new AbortController()
  const id = ++ctrlId
  activeControllers.set(id, controller)

  const cancel = () => {
    controller.abort()
    activeControllers.delete(id)
  }

  const run = (path, options = {}) => {
    return fetchApi(path, options, controller.signal)
  }

  return { run, cancel, signal: controller.signal }
}

/* Named API methods (for simple one-off calls without lifecycle tracking) */
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
