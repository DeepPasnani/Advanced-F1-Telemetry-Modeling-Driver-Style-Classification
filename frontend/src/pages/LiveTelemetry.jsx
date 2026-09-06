import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useWebSocket } from '../hooks/useWebSocket'
import Breadcrumbs from '../components/Breadcrumbs'
import LoadingSpinner from '../components/LoadingSpinner'

/* ── Rolling mini-trace with optional gradient fill ── */
function MiniTrace({ history, maxValue, color, fill }) {
  const w = 300; const h = 56
  if (!history.length) return <div className="h-[56px]" />
  // Auto-scale past the nominal max so an outlier point never clips
  // outside the trace instead of just being drawn near the top.
  const effectiveMax = Math.max(maxValue, ...history, 1)
  const step = w / Math.max(history.length - 1, 1)
  const pts = history.map((v, i) => `${i * step},${h - (v / effectiveMax) * h}`).join(' ')
  const base = `${0},${h} ${pts} ${(history.length - 1) * step},${h}`
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-[56px] overflow-visible" preserveAspectRatio="none">
      {fill && <polygon fill={fill} points={base} />}
      <polyline fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" points={pts} />
    </svg>
  )
}

const DRIVERS = ['VER','PER','ALO','SAI','HAM','RUS','LEC','NOR','PIA','GAS','STR','TSU','BOT','ZHO','ALB','MAG','HUL','OCO','DEV','SAR']

export default function LiveTelemetry() {
  const { id } = useParams()
  const [driverCode, setDriverCode] = useState('VER')
  const { data, connected, error: wsError } = useWebSocket(id, driverCode)
  const [speedHistory, setSpeedHistory] = useState([])
  const [throttleHistory, setThrottleHistory] = useState([])

  useEffect(() => {
    // Switching drivers reconnects the socket; without this the new
    // driver's trace would start mixed in with the previous one's tail.
    setSpeedHistory([])
    setThrottleHistory([])
  }, [driverCode])

  useEffect(() => {
    if (data) {
      setSpeedHistory(p => [...p.slice(-120), data.speed || 0])
      setThrottleHistory(p => [...p.slice(-120), data.throttle || 0])
    }
  }, [data])

  if (wsError && !connected) {
    return (
      <div className="animate-fade-in">
        <Breadcrumbs items={[{ label: 'Sessions', to: '/' }, { label: 'Live' }]} />
        <div className="f1-card p-8 text-center mt-4">
          <p className="text-red-400">{wsError}</p>
          <Link to={`/session/${id}`} className="f1-btn-secondary mt-4">← Back</Link>
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
      <Breadcrumbs items={[
        { label: 'Sessions', to: '/' },
        { label: 'Session', to: `/session/${id}` },
        { label: 'Live' },
      ]} />

      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="f1-kicker">Real-Time Replay</span>
          <h1 className="text-2xl font-bold text-ink">Live Telemetry</h1>
          <p className="mt-1 text-sm text-ink-secondary">Fastest-lap data, paced to real time &middot; {driverCode}</p>
        </div>
        <div className="flex items-center gap-3">
          <select value={driverCode} onChange={(e) => setDriverCode(e.target.value)}
            className="f1-select w-24" aria-label="Select driver">
            {DRIVERS.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <span className={`f1-badge border transition-all duration-300 ${
            connected
              ? 'bg-green-500/15 text-green-400 border-green-500/30 shadow-sm shadow-green-500/10'
              : 'bg-red-500/15 text-red-400 border-red-500/30'
          }`}>
            <span className={`mr-1.5 h-1.5 w-1.5 rounded-full transition-all duration-300 ${
              connected ? 'bg-green-400 animate-pulse shadow-sm shadow-green-400/50' : 'bg-red-400'
            }`} />
            {connected ? 'Live' : 'Offline'}
          </span>
        </div>
      </div>

      {!data && connected && <div className="py-32"><LoadingSpinner label="Connecting..." /></div>}

      {data && (
        <div className="grid gap-5 lg:grid-cols-3">
          {/* Speed */}
          <div className="f1-card p-5 transition-all duration-200 hover:shadow-card-hover">
            <h3 className="f1-stat-label mb-1">Speed</h3>
            <div className="flex items-baseline gap-1">
              <span className="text-6xl font-bold font-mono text-ink tabular-nums transition-all duration-150">{Math.round(speed)}</span>
              <span className="text-sm text-ink-muted font-medium">km/h</span>
            </div>
            <div className="mt-4">
              <MiniTrace history={speedHistory} maxValue={340} color="#e8002d" fill="url(#speedGrad)" />
              <svg aria-hidden="true" className="absolute pointer-events-none" style={{ width: 0, height: 0 }}>
                <defs>
                  <linearGradient id="speedGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#e8002d" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#e8002d" stopOpacity="0" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>

          {/* Throttle & Brake */}
          <div className="f1-card p-5 transition-all duration-200 hover:shadow-card-hover">
            <h3 className="f1-stat-label mb-4">Throttle / Brake</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-green-400 font-semibold">Throttle</span>
                  <span className="font-mono text-ink tabular-nums">{Math.round(throttle)}%</span>
                </div>
                <div className="f1-progress">
                  <div className="f1-progress-bar bg-green-500" style={{ width: `${throttle}%`, transitionDuration: '150ms' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-red-400 font-semibold">Brake</span>
                  <span className="font-mono text-ink tabular-nums">{brake ? 'ON' : 'OFF'}</span>
                </div>
                <div className="f1-progress">
                  <div className={`f1-progress-bar transition-all duration-150 ${brake ? 'bg-red-500 w-full' : 'bg-transparent w-0'}`} />
                </div>
              </div>
            </div>
            <div className="mt-4">
              <MiniTrace history={throttleHistory} maxValue={100} color="#22c55e" fill="url(#throttleGrad)" />
              <svg aria-hidden="true" className="absolute pointer-events-none" style={{ width: 0, height: 0 }}>
                <defs>
                  <linearGradient id="throttleGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22c55e" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>

          {/* DRS, Gear, Progress */}
          <div className="f1-card p-5 transition-all duration-200 hover:shadow-card-hover">
            <div className="grid grid-cols-2 gap-6">
              <div className="text-center">
                <h3 className="f1-stat-label mb-2">DRS</h3>
                <span className={`text-3xl font-bold font-mono transition-all duration-300 ${
                  drs ? 'text-green-400 drop-shadow-[0_0_8px_rgba(74,222,128,0.5)]' : 'text-ink-muted'
                }`}>
                  {drs ? 'OPEN' : 'CLSD'}
                </span>
              </div>
              <div className="text-center">
                <h3 className="f1-stat-label mb-2">Gear</h3>
                <span className="text-5xl font-bold font-mono text-ink tabular-nums transition-all duration-150">{gear}</span>
              </div>
            </div>
            <div className="mt-8">
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-ink-secondary font-medium">Lap Progress</span>
                <span className="font-mono text-ink tabular-nums">{Math.round(progress * 100)}%</span>
              </div>
              <div className="f1-progress h-2">
                <div className="f1-progress-bar bg-accent" style={{ width: `${progress * 100}%`, transitionDuration: '300ms' }} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
