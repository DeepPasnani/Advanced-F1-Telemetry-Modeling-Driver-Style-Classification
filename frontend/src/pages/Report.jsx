import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getReport, getAnalysis } from '../hooks/useApi'
import Breadcrumbs from '../components/Breadcrumbs'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import PlotCard from '../components/PlotCard'
import { PLOTS, PLOT_INFO } from '../lib/plotInfo'

export default function Report() {
  const { id } = useParams()
  const [report, setReport] = useState('')
  const [session, setSession] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [plotInsights, setPlotInsights] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    setLoading(true)
    setError('')
    const controller = new AbortController()
    Promise.all([getReport(id, controller.signal), getAnalysis(id, controller.signal)])
      .then(([reportRes, analysisRes]) => {
        setReport(reportRes.data.report)
        setSession(analysisRes.data.session)
        setSessionId(analysisRes.data.session_id)
        setPlotInsights(analysisRes.data.plot_insights || {})
      })
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message) })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [id, retryCount])

  if (loading) return <div className="py-32"><LoadingSpinner label="Loading report..." /></div>

  if (error) return <ErrorMessage message={error} onRetry={() => setRetryCount(c => c + 1)} backTo={`/analysis/${id}`} />

  return (
    <div className="animate-fade-in">
      <Breadcrumbs items={[
        { label: 'Sessions', to: '/' },
        { label: session?.grand_prix || 'Session', to: sessionId ? `/session/${sessionId}` : undefined },
        { label: 'Analysis', to: `/analysis/${id}` },
        { label: 'Report' },
      ]} />

      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="f1-kicker">{session?.label || 'Full Report'}</span>
          <h1 className="text-2xl font-bold text-ink">Driver Analysis Report</h1>
        </div>
        <Link to={`/analysis/${id}`} className="f1-btn-secondary">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back to Analysis
        </Link>
      </div>

      <div className="f1-card p-6 mb-10">
        <pre className="font-mono text-sm text-ink-secondary leading-relaxed whitespace-pre-wrap">{report}</pre>
      </div>

      <h2 className="text-xl font-bold text-ink mb-4">Visualizations</h2>
      <div className="grid gap-4 md:grid-cols-2">
        {PLOTS.map((name) => (
          <PlotCard key={name} src={`/api/analysis/${id}/plots/${name}.png`} alt={`${name.replace(/_/g, ' ')} plot`}
            title={PLOT_INFO[name].title} description={plotInsights[name] || PLOT_INFO[name].description} />
        ))}
      </div>
    </div>
  )
}
