import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useWebSocket } from '../hooks/useWebSocket'

function MiniTrace({ history, maxValue, color }) {
  const w = 300; const h = 60
  if (!history.length) return <div className="h-[60px]" />
  const pts = history.map((v, i) =>
    `${i * (w / Math.max(history.length - 1, 1))},${h - (v / maxValue) * h}`
  ).join(' ')
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-[60px]" preserveAspectRatio="none">
      <polyline fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" points={pts} />
    </svg>
  )
}

const DRIVERS = ['VER','PER','ALO','SAI','HAM','RUS','LEC','NOR','PIA','GAS','STR','TSU','BOT','ZHO','ALB','MAG','HUL','OCO','DEV','SAR']

export default function LiveTelemetry() {
  const { id } = useParams()
  const [driverCode, setDriverCode] = useState('VER')
  const { data, connected, error } = useWebSocket(id, driverCode)
  const [speedHistory, setSpeedHistory] = useState([])
  const [throttleHistory, setThrottleHistory] = useState([])

  useEffect(() => {
    if (data) {
      setSpeedHistory(p => [...p.slice(-120), data.speed || 0])
      setThrottleHistory(p => [...p.slice(-120), data.throttle || 0])
    }
  }, [data])

  if (error && !connected) {
    return (
      <div className="animate-fade-in">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-ink">Live Telemetry</h1>
          <Link to={`/session/${id}`} className="f1-btn-secondary">← Back</Link>
        </div>
        <div className="f1-card p-8 text-center">
          <p className="text-red-400">{error}</p>
        </div>
      </div>
    )
  }

  const speed = data?.speed ?? 0
  const throttle = data?.throttle ?? 0
  const brake = data?.brake ?? 0
  const drs = data?.drs ?? 0
  const gear = data?.gear ?? 0
  const progress = data?.lap_progress ?? 0

  return (
    <div className="animate-fade-in">
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-ink-muted">
          <Link to={`/session/${id}`} className="hover:text-ink-secondary transition-colors">Session</Link>
          <span>/</span>
          <span className="text-ink-secondary">Live</span>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={driverCode}
            onChange={(e) => setDriverCode(e.target.value)}
            className="f1-select w-24"
          >
            {DRIVERS.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <span className={`f1-badge ${connected ? 'bg-green-500/15 text-green-400 border-green-500/30' : 'bg-red-500/15 text-red-400 border-red-500/30'} border`}>
            <span className={`mr-1.5 h-1.5 w-1.5 rounded-full ${connected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
            {connected ? 'Live' : 'Offline'}
          </span>
          <Link to={`/session/${id}`} className="f1-btn-secondary text-sm">← Back</Link>
        </div>
      </div>

      {!data && connected && (
        <div className="flex items-center justify-center py-32">
          <div className="h-8 w-8 animate-pulse-slow rounded-full border-2 border-accent border-t-transparent" />
        </div>
      )}

      {data && (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Speed gauge */}
          <div className="f1-card p-6">
            <h3 className="f1-stat-label mb-1">Speed</h3>
            <div className="flex items-baseline gap-1">
              <span className="text-6xl font-bold font-mono text-ink tabular-nums">{Math.round(speed)}</span>
              <span className="text-sm text-ink-muted font-medium">km/h</span>
            </div>
            <div className="mt-4">
              <MiniTrace history={speedHistory} maxValue={340} color="#e8002d" />
            </div>
          </div>

          {/* Throttle & Brake */}
          <div className="f1-card p-6">
            <h3 className="f1-stat-label mb-4">Throttle / Brake</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-green-400 font-semibold">Throttle</span>
                  <span className="font-mono text-ink">{Math.round(throttle)}%</span>
                </div>
                <div className="f1-progress">
                  <div className="f1-progress-bar bg-green-500" style={{ width: `${throttle}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-red-400 font-semibold">Brake</span>
                  <span className="font-mono text-ink">{brake ? 'ON' : 'OFF'}</span>
                </div>
                <div className="f1-progress">
                  <div className="f1-progress-bar bg-red-500" style={{ width: `${brake * 100}%` }} />
                </div>
              </div>
            </div>
            <div className="mt-4">
              <MiniTrace history={throttleHistory} maxValue={100} color="#22c55e" />
            </div>
          </div>

          {/* DRS, Gear, Progress */}
          <div className="f1-card p-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="text-center">
                <h3 className="f1-stat-label mb-2">DRS</h3>
                <span className={`text-3xl font-bold font-mono ${drs ? 'text-green-400' : 'text-ink-muted'}`}>
                  {drs ? 'OPEN' : 'CLSD'}
                </span>
              </div>
              <div className="text-center">
                <h3 className="f1-stat-label mb-2">Gear</h3>
                <span className="text-5xl font-bold font-mono text-ink">{gear}</span>
              </div>
            </div>
            <div className="mt-8">
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-ink-secondary font-medium">Lap Progress</span>
                <span className="font-mono text-ink">{Math.round(progress * 100)}%</span>
              </div>
              <div className="f1-progress h-2">
                <div className="f1-progress-bar bg-accent" style={{ width: `${progress * 100}%` }} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
