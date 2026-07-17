import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getReport } from '../hooks/useApi'

const PLOTS = ['cluster_scatter', 'radar_chart', 'speed_trace', 'throttle_brake', 'sector_comparison']

const STYLE_COLORS = {
  'Aggressive': { badge: 'bg-red-500/15 text-red-400 border-red-500/30', bar: 'bg-red-500' },
  'Smooth Cornering': { badge: 'bg-green-500/15 text-green-400 border-green-500/30', bar: 'bg-green-500' },
  'Late Braker': { badge: 'bg-blue-500/15 text-blue-400 border-blue-500/30', bar: 'bg-blue-500' },
}

function parseSection(section) {
  const lines = section.split('\n')
  const driver = lines[0].replace('Driver: ', '').trim()
  const style = lines.find(l => l.includes('Style Classification'))?.split(': ').pop()?.trim() || ''
  const speed = lines.find(l => l.includes('Mean Speed'))?.split(': ').pop()?.trim() || ''
  const brake = lines.find(l => l.includes('Brake Frequency'))?.split(': ').pop()?.trim() || ''
  const aggression = lines.find(l => l.includes('Aggression Index'))?.split(': ').pop()?.trim() || ''
  const drs = lines.find(l => l.includes('DRS Usage'))?.split(': ').pop()?.trim() || ''
  const laps = lines.find(l => l.includes('Laps Analyzed'))?.split(': ').pop()?.trim() || ''
  return { driver, style, speed, brake, aggression, drs, laps }
}

export default function AnalysisResults() {
  const { id } = useParams()
  const [report, setReport] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getReport(id)
      .then((res) => setReport(res.data.report))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="h-8 w-8 animate-pulse-slow rounded-full border-2 border-accent border-t-transparent" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <p className="text-red-400">{error}</p>
        <Link to="/" className="f1-btn-secondary mt-4">← Back</Link>
      </div>
    )
  }

  const sections = report.split('\n\n').filter(s => s.startsWith('Driver:'))
  const weatherLine = report.split('\n').find(l => l.includes('Track Temp'))
  const rainfallLine = report.split('\n').find(l => l.includes('Rainfall'))
  const hasReport = sections.length > 0

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm text-ink-muted mb-2">
          <Link to="/" className="hover:text-ink-secondary transition-colors">Sessions</Link>
          <span>/</span>
          <span className="text-ink-secondary">Analysis</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-ink">Analysis Results</h1>
            <p className="mt-1 text-sm text-ink-secondary">
              {sections.length} drivers analyzed
            </p>
          </div>
          <Link to={`/analysis/${id}/report`} className="f1-btn-secondary">
            Full Report →
          </Link>
        </div>
      </div>

      {/* Driver cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {sections.map((section) => {
          const { driver, style, speed, brake, aggression, drs, laps } = parseSection(section)
          const colors = STYLE_COLORS[style] || { badge: 'bg-gray-500/15 text-gray-400 border-gray-500/30', bar: 'bg-gray-500' }
          // Parse aggression into a 0-1 score for the bar
          const aggressionVal = parseFloat(aggression) || 0

          return (
            <div key={driver} className="f1-card animate-slide-up p-5 transition-all duration-150 hover:shadow-card-hover">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold font-mono text-ink">{driver}</h2>
                <span className={`f1-badge border ${colors.badge}`}>{style}</span>
              </div>

              <div className="space-y-3">
                <div className="f1-stat">
                  <span className="f1-stat-label">Speed</span>
                  <span className="f1-stat-value">{speed}</span>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-ink-secondary font-medium">Brake Frequency</span>
                    <span className="font-mono text-ink">{brake}</span>
                  </div>
                  <div className="f1-progress">
                    <div className="f1-progress-bar bg-red-500/60" style={{ width: `${Math.min(parseFloat(brake) * 100, 100)}%` }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-ink-secondary font-medium">Aggression</span>
                    <span className="font-mono text-ink">{aggression}</span>
                  </div>
                  <div className="f1-progress">
                    <div className={`f1-progress-bar ${colors.bar}`} style={{ width: `${Math.min(aggressionVal * 1000, 100)}%` }} />
                  </div>
                </div>

                {drs && (
                  <div className="flex justify-between text-xs">
                    <span className="text-ink-secondary font-medium">DRS Usage</span>
                    <span className="font-mono text-ink">{drs}</span>
                  </div>
                )}

                {laps && (
                  <div className="flex justify-between text-xs">
                    <span className="text-ink-secondary font-medium">Laps Analyzed</span>
                    <span className="font-mono text-ink">{laps}</span>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Session conditions */}
      {weatherLine && (
        <div className="f1-card mt-6 p-4">
          <h3 className="text-xs font-semibold tracking-wide text-ink-secondary uppercase mb-2">Session Conditions</h3>
          <div className="flex flex-wrap gap-6 text-sm">
            <span className="text-ink-secondary">{weatherLine.trim()}</span>
            {rainfallLine && <span className="text-ink-secondary">{rainfallLine.trim()}</span>}
          </div>
        </div>
      )}

      {/* Plots */}
      {hasReport && (
        <>
          <h2 className="text-xl font-bold text-ink mt-10 mb-4">Visualizations</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {PLOTS.map((name) => (
              <div key={name} className="f1-card overflow-hidden p-2">
                <img
                  src={`/api/analysis/${id}/plots/${name}.png`}
                  alt={name}
                  className="w-full rounded-lg"
                  loading="lazy"
                />
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
