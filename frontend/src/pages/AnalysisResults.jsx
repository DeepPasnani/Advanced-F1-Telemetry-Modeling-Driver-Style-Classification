import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getReport } from '../hooks/useApi'
import Breadcrumbs from '../components/Breadcrumbs'
import LoadingSkeleton from '../components/LoadingSkeleton'
import ErrorMessage from '../components/ErrorMessage'
import PlotCard from '../components/PlotCard'

const PLOTS = ['cluster_scatter', 'radar_chart', 'speed_trace', 'throttle_brake', 'sector_comparison']

const STYLE_COLORS = {
  'Aggressive':        { badge: 'bg-red-500/15 text-red-400 border-red-500/30', bar: 'bg-red-500', glow: 'shadow-red-500/20' },
  'Smooth Cornering':  { badge: 'bg-green-500/15 text-green-400 border-green-500/30', bar: 'bg-green-500', glow: 'shadow-green-500/20' },
  'Late Braker':       { badge: 'bg-blue-500/15 text-blue-400 border-blue-500/30', bar: 'bg-blue-500', glow: 'shadow-blue-500/20' },
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
  const [retryCount, setRetryCount] = useState(0)

  const load = () => {
    setLoading(true)
    setError('')
    getReport(id)
      .then((res) => setReport(res.data.report))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [id, retryCount])

  if (loading) return <LoadingSkeleton variant="card" count={3} />

  if (error) return <ErrorMessage message={error} onRetry={() => setRetryCount(c => c + 1)} backTo="/" backLabel="← Back" />

  const sections = report.split('\n\n').filter(s => s.startsWith('Driver:'))
  const weatherLine = report.split('\n').find(l => l.includes('Track Temp'))
  const rainfallLine = report.split('\n').find(l => l.includes('Rainfall'))

  return (
    <div className="animate-fade-in">
      <Breadcrumbs items={[
        { label: 'Sessions', to: '/' },
        { label: 'Analysis' },
      ]} />

      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink">Analysis Results</h1>
          <p className="mt-1 text-sm text-ink-secondary">
            <span className="font-semibold text-ink">{sections.length}</span> drivers analyzed
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
        {sections.map((section, i) => {
          const { driver, style, speed, brake, aggression, drs, laps } = parseSection(section)
          const colors = STYLE_COLORS[style] || { badge: 'bg-gray-500/15 text-gray-400 border-gray-500/30', bar: 'bg-gray-500', glow: '' }
          const aggressionVal = parseFloat(aggression) || 0
          const brakeVal = parseFloat(brake) || 0

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
                  <span className="f1-stat-value">{speed}</span>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-ink-secondary font-medium">Brake Frequency</span>
                    <span className="font-mono text-ink">{brake}</span>
                  </div>
                  <div className="f1-progress">
                    <div className="f1-progress-bar bg-red-500/60" style={{ width: `${Math.min(brakeVal * 100, 100)}%` }} />
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

                <div className="flex gap-4 text-xs pt-1 border-t border-border">
                  {drs && (
                    <span className="flex items-center gap-1.5">
                      <span className="text-ink-muted">DRS</span>
                      <span className="font-mono text-ink">{drs}</span>
                    </span>
                  )}
                  {laps && (
                    <span className="flex items-center gap-1.5">
                      <span className="text-ink-muted">Laps</span>
                      <span className="font-mono text-ink">{laps}</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Session conditions */}
      {weatherLine && (
        <div className="f1-card mt-6 p-4">
          <h3 className="f1-stat-label mb-2">Session Conditions</h3>
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <span className="text-ink-secondary">{weatherLine.trim()}</span>
            {rainfallLine && <span className="text-ink-secondary">{rainfallLine.trim()}</span>}
          </div>
        </div>
      )}

      {/* Plots */}
      {sections.length > 0 && (
        <>
          <h2 className="text-xl font-bold text-ink mt-10 mb-4">Visualizations</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {PLOTS.map((name) => (
              <PlotCard key={name} src={`/api/analysis/${id}/plots/${name}.png`} alt={`${name.replace(/_/g, ' ')} plot`} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
