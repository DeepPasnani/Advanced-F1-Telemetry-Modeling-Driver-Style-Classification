import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getAnalysis } from '../hooks/useApi'
import Breadcrumbs from '../components/Breadcrumbs'
import LoadingSkeleton from '../components/LoadingSkeleton'
import ErrorMessage from '../components/ErrorMessage'
import PlotCard from '../components/PlotCard'
import { PLOTS, PLOT_INFO } from '../lib/plotInfo'

const STYLE_COLORS = {
  'Aggressive':        { badge: 'bg-red-500/15 text-red-400 border-red-500/30', bar: 'bg-red-500', glow: 'shadow-red-500/20' },
  'Smooth Cornering':  { badge: 'bg-green-500/15 text-green-400 border-green-500/30', bar: 'bg-green-500', glow: 'shadow-green-500/20' },
  'Late Braker':       { badge: 'bg-blue-500/15 text-blue-400 border-blue-500/30', bar: 'bg-blue-500', glow: 'shadow-blue-500/20' },
}

function metric(features, base) {
  if (features[`${base}_mean`] !== undefined) return features[`${base}_mean`]
  return features[base]
}

function formatLapTime(seconds) {
  if (seconds == null || Number.isNaN(seconds)) return null
  const m = Math.floor(seconds / 60)
  const s = (seconds % 60).toFixed(3).padStart(6, '0')
  return `${m}:${s}`
}

export default function AnalysisResults() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    setLoading(true)
    setError('')
    const controller = new AbortController()
    getAnalysis(id, controller.signal)
      .then((res) => setData(res.data))
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message) })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [id, retryCount])

  if (loading) return <LoadingSkeleton variant="card" count={3} />

  if (error) return <ErrorMessage message={error} onRetry={() => setRetryCount(c => c + 1)} backTo="/" backLabel="← Back" />

  const {
    session_id: sessionId, session, driver_codes: drivers, styles, predictions, features,
    sector_times: sectorTimes, plot_insights: plotInsights = {},
  } = data
  const firstFeatures = drivers.length > 0 ? features[drivers[0]] : {}
  const hasWeather = firstFeatures && firstFeatures.track_temp !== undefined

  return (
    <div className="animate-fade-in">
      <Breadcrumbs items={[
        { label: 'Sessions', to: '/' },
        { label: session?.grand_prix || 'Session', to: sessionId ? `/session/${sessionId}` : undefined },
        { label: 'Analysis' },
      ]} />

      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="f1-kicker">{session?.label || 'Driver Style Classification'}</span>
          <h1 className="text-2xl font-bold text-ink">Analysis Results</h1>
          <p className="mt-1 text-sm text-ink-secondary">
            <span className="font-semibold text-ink">{drivers.length}</span> drivers analyzed
          </p>
        </div>
        <Link to={`/analysis/${id}/report`} className="f1-btn-secondary">
          Full Report
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </div>

      {/* Driver cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {drivers.map((driver, i) => {
          const driverFeatures = features[driver] || {}
          const style = styles[driver] || ''
          const colors = STYLE_COLORS[style] || { badge: 'bg-gray-500/15 text-gray-400 border-gray-500/30', bar: 'bg-gray-500', glow: '' }

          const speed = metric(driverFeatures, 'mean_speed')
          const brake = metric(driverFeatures, 'brake_frequency')
          const aggression = metric(driverFeatures, 'aggression_index')
          const drs = metric(driverFeatures, 'drs_usage')
          const laps = driverFeatures.lap_count
          const predictedLapTime = formatLapTime(predictions?.[driver])
          const sectors = sectorTimes?.[driver]

          const brakeVal = brake ?? 0
          const aggressionVal = aggression ?? 0

          return (
            <div key={driver} style={{ '--i': i }}
              className="f1-card stagger-enter p-5 transition-all duration-200 hover:shadow-card-hover">
              <div className="flex items-start justify-between mb-4 gap-2">
                <h2 className="text-xl font-bold font-mono text-ink leading-none">{driver}</h2>
                <span className={`f1-badge border shrink-0 ${colors.badge}`}>{style}</span>
              </div>

              <div className="space-y-3">
                <div className="f1-stat">
                  <span className="f1-stat-label">Mean Speed</span>
                  <span className="f1-stat-value">{speed != null ? `${speed.toFixed(1)} km/h` : '—'}</span>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-ink-secondary font-medium">Brake Frequency</span>
                    <span className="font-mono text-ink">{brake != null ? brake.toFixed(3) : '—'}</span>
                  </div>
                  <div className="f1-progress">
                    <div className="f1-progress-bar bg-red-500/60" style={{ width: `${Math.min(brakeVal * 100, 100)}%` }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-ink-secondary font-medium">Aggression</span>
                    <span className="font-mono text-ink">{aggression != null ? aggression.toFixed(3) : '—'}</span>
                  </div>
                  <div className="f1-progress">
                    <div className={`f1-progress-bar ${colors.bar}`} style={{ width: `${Math.min(aggressionVal * 1000, 100)}%` }} />
                  </div>
                </div>

                {sectors && (
                  <div className="flex justify-between text-xs pt-1">
                    <span className="text-ink-muted">Sectors</span>
                    <span className="font-mono text-ink">
                      {sectors.map((s) => (s != null ? `${s.toFixed(2)}s` : 'N/A')).join(' / ')}
                    </span>
                  </div>
                )}

                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs pt-1 border-t border-border">
                  {drs != null && (
                    <span className="flex items-center gap-1.5">
                      <span className="text-ink-muted">DRS</span>
                      <span className="font-mono text-ink">{(drs * 100).toFixed(0)}%</span>
                    </span>
                  )}
                  {laps != null && (
                    <span className="flex items-center gap-1.5">
                      <span className="text-ink-muted">Laps</span>
                      <span className="font-mono text-ink">{laps}</span>
                    </span>
                  )}
                  {predictedLapTime && (
                    <span className="flex items-center gap-1.5" title="Estimated by a model fit only on this analysis's small driver sample — read as a relative comparison, not a precise forecast.">
                      <span className="text-ink-muted">Est. Lap</span>
                      <span className="font-mono text-ink">{predictedLapTime}</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Session conditions */}
      {hasWeather && (
        <div className="f1-card mt-6 p-4">
          <h3 className="f1-stat-label mb-2">Session Conditions</h3>
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <span className="text-ink-secondary">Track Temp: {firstFeatures.track_temp.toFixed(1)}°C</span>
            <span className="text-ink-secondary">Air Temp: {firstFeatures.air_temp.toFixed(1)}°C</span>
            <span className="text-ink-secondary">Rainfall: {firstFeatures.rainfall ? 'Yes' : 'No'}</span>
          </div>
        </div>
      )}

      {/* Plots */}
      {drivers.length > 0 && (
        <>
          <h2 className="text-xl font-bold text-ink mt-10 mb-4">Visualizations</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {PLOTS.map((name) => (
              <PlotCard key={name} src={`/api/analysis/${id}/plots/${name}.png`} alt={`${name.replace(/_/g, ' ')} plot`}
                title={PLOT_INFO[name].title} description={plotInsights[name] || PLOT_INFO[name].description} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
