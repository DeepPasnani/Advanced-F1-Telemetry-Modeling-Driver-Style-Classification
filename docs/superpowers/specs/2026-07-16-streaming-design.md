# Real-Time Telemetry Streaming — Design

## Concept

Add a WebSocket endpoint that replays historical telemetry data as a real-time stream, simulating live car data. Frontend connects, picks a driver, and gets pushed telemetry samples at realistic intervals (every ~100ms of session time).

This is a *simulated* live stream — real F1 live telemetry requires a paid API subscription. The replay approach is functionally identical for demo/analysis purposes.

## Minimal Surface Area

### Backend — new WebSocket endpoint in `server/main.py`

```
WS /ws/telemetry/{session_id}/{driver_code}
```

On connect:
1. Loads the driver's fastest lap telemetry
2. Sends telemetry rows one at a time, paced by the time delta between consecutive rows (using `SessionTime` column)
3. Each message: `{"distance": 123.4, "speed": 280, "throttle": 85, "brake": 0, "drs": 0, "lap_progress": 0.45}`

On disconnect: cleanup.

### Frontend — new hook `useWebSocket.js`

```js
export function useWebSocket(sessionId, driverCode) {
  // connects to ws://localhost:8080/ws/telemetry/{sessionId}/{driverCode}
  // returns { data, connected, error }
  // data updates on each message
}
```

### New Plot — live speed gauge

A simple real-time speed indicator (analog gauge or scrolling line chart) on a new "Live Telemetry" page at `/session/{id}/live`.

### Files Changed

| File | Change |
|------|--------|
| `server/main.py` | +1 WebSocket endpoint |
| `frontend/src/hooks/useWebSocket.js` | Create (new) |
| `frontend/src/pages/LiveTelemetry.jsx` | Create (new) |
| `frontend/src/App.jsx` | +1 route |

### What it won't do

- No multi-driver sync (pick one driver at a time)
- No historical recording during stream (YAGNI)
- No auth (YAGNI for local dev)

## Tradeoff

This is ~50 lines of backend + ~80 lines of frontend. Simple, self-contained, and demonstrates the concept. Real WebSocket streaming with actual F1 live data would need a different data source.

## Next

Approve this design and I'll implement it in one pass.
