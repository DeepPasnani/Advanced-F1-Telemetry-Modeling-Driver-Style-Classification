import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useWebSocket } from '../hooks/useWebSocket'

function MiniTrace({ history, maxValue, color }) {
  const w = 300, h = 60
  if (!history.length) return <div className="h-[60px]" />
  const points = history.map((v, i) =>
    `${i * (w / Math.max(history.length - 1, 1))},${h - (v / maxValue) * h}`
  ).join(' ')
  return (
    <svg width={w} height={h} className="w-full">
      <polyline fill="none" stroke={color} strokeWidth="2" points={points} />
    </svg>
  )
}

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
      <div>
        <h1 className="text-3xl font-bold mb-4">Live Telemetry</h1>
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-800 text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <Link to={`/session/${id}`} className="text-red-400 hover:text-red-300">← Back to Session</Link>
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
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Live Telemetry</h1>
        <div className="flex items-center gap-4">
          <select value={driverCode} onChange={e => setDriverCode(e.target.value)}
            className="bg-gray-800 rounded px-3 py-2 border border-gray-700">
            {['VER','PER','ALO','SAI','HAM','RUS','LEC','NOR','PIA','GAS','STR','TSU','BOT','ZHO','ALB','MAG','HUL','OCO','DEV','SAR'].map(c =>
              <option key={c} value={c}>{c}</option>
            )}
          </select>
          <span className={`px-2 py-1 rounded text-xs font-semibold ${connected ? 'bg-green-700' : 'bg-red-700'}`}>
            {connected ? '● Live' : '○ Disconnected'}
          </span>
          <Link to={`/session/${id}`} className="text-gray-400 hover:text-white text-sm">← Session</Link>
        </div>
      </div>

      {!data && connected && (
        <p className="text-center mt-20 text-gray-400">Waiting for telemetry data...</p>
      )}

      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Speed gauge */}
          <div className="bg-gray-900 rounded-lg p-6 border border-gray-800 text-center">
            <p className="text-gray-400 text-sm mb-2">SPEED</p>
            <p className="text-6xl font-bold text-white font-mono">{Math.round(speed)}</p>
            <p className="text-gray-500">km/h</p>
            <div className="mt-4">
              <MiniTrace history={speedHistory} maxValue={340} color="#ef4444" />
            </div>
          </div>

          {/* Throttle & Brake */}
          <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
            <p className="text-gray-400 text-sm mb-3">THROTTLE / BRAKE</p>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-green-400">Throttle</span>
                  <span className="font-mono">{Math.round(throttle)}%</span>
                </div>
                <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full transition-all"
                    style={{ width: `${throttle}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-red-400">Brake</span>
                  <span className="font-mono">{brake ? 'ON' : 'OFF'}</span>
                </div>
                <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
                  <div className="h-full bg-red-500 rounded-full transition-all"
                    style={{ width: `${brake * 100}%` }} />
                </div>
              </div>
            </div>
            <div className="mt-4">
              <MiniTrace history={throttleHistory} maxValue={100} color="#22c55e" />
            </div>
          </div>

          {/* DRS, Gear, Progress */}
          <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <p className="text-gray-400 text-sm mb-1">DRS</p>
                <p className={`text-3xl font-bold font-mono ${drs ? 'text-green-400' : 'text-gray-600'}`}>
                  {drs ? 'OPEN' : 'CLSD'}
                </p>
              </div>
              <div className="text-center">
                <p className="text-gray-400 text-sm mb-1">GEAR</p>
                <p className="text-3xl font-bold font-mono text-white">{gear}</p>
              </div>
            </div>
            <div className="mt-6">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">Lap Progress</span>
                <span className="font-mono">{Math.round(progress * 100)}%</span>
              </div>
              <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-red-600 rounded-full transition-all"
                  style={{ width: `${progress * 100}%` }} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
