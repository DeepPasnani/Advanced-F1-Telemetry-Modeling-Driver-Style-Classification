import { useEffect, useRef, useState } from 'react'
import { API_BASE_URL } from './useApi'

export function useWebSocket(sessionId, driverCode) {
  const [data, setData] = useState(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {
    if (!sessionId || !driverCode) return

    // Same-origin by default; when the API lives on a different host
    // (VITE_API_BASE_URL set — split Vercel/Railway-style deployment),
    // connect straight to it instead of the page's own origin.
    const wsBase = API_BASE_URL
      ? API_BASE_URL.replace(/^http/, 'ws')
      : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
    const url = `${wsBase}/ws/telemetry/${sessionId}/${driverCode}`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => { setConnected(false); setError('Disconnected') }
    ws.onerror = () => setError('WebSocket error')
    ws.onmessage = (e) => {
      try { setData(JSON.parse(e.data)) } catch { /* skip malformed */ }
    }

    return () => ws.close()
  }, [sessionId, driverCode])

  return { data, connected, error }
}
