import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getReport } from '../hooks/useApi'

const PLOTS = ['cluster_scatter', 'radar_chart', 'speed_trace', 'throttle_brake', 'sector_comparison']

export default function Report() {
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

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm text-ink-muted mb-2">
          <Link to={`/analysis/${id}`} className="hover:text-ink-secondary transition-colors">Analysis</Link>
          <span>/</span>
          <span className="text-ink-secondary">Report</span>
        </div>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-ink">Driver Analysis Report</h1>
          <Link to={`/analysis/${id}`} className="f1-btn-secondary">← Back to Analysis</Link>
        </div>
      </div>

      <div className="f1-card p-6 mb-10">
        <pre className="font-mono text-sm text-ink-secondary leading-relaxed whitespace-pre-wrap">{report}</pre>
      </div>

      <h2 className="text-xl font-bold text-ink mb-4">Visualizations</h2>
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
    </div>
  )
}
