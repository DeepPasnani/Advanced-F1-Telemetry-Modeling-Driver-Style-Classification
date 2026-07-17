import { useEffect, useRef, useState } from 'react'

export function useWebSocket(sessionId, driverCode) {
  const [data, setData] = useState(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {
    if (!sessionId || !driverCode) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws/telemetry/${sessionId}/${driverCode}`

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
