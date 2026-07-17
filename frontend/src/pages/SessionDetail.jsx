import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getDrivers, analyzeDrivers } from '../hooks/useApi'
import Breadcrumbs from '../components/Breadcrumbs'
import LoadingSkeleton from '../components/LoadingSkeleton'
import ErrorMessage from '../components/ErrorMessage'

export default function SessionDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [drivers, setDrivers] = useState([])
  const [selected, setSelected] = useState([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    getDrivers(id)
      .then((res) => {
        setDrivers(res.data)
        setSelected(res.data.slice(0, 3))
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  const toggle = (code) => {
    setSelected((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    )
  }

  const handleAnalyze = async () => {
    if (selected.length === 0) return
    setAnalyzing(true)
    setError('')
    try {
      const res = await analyzeDrivers(id, selected)
      navigate(`/analysis/${res.data.analysis_id}`)
    } catch (err) {
      setError(err.message)
      setAnalyzing(false)
    }
  }

  if (loading) return <LoadingSkeleton variant="driver-grid" />

  if (error && drivers.length === 0) {
    return <ErrorMessage message={error} onRetry={() => window.location.reload()} backTo="/" backLabel="← Back to Sessions" />
  }

  return (
    <div className="animate-fade-in">
      <Breadcrumbs items={[{ label: 'Sessions', to: '/' }, { label: id.slice(0, 8) }]} />

      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink">Select Drivers</h1>
          <p className="mt-1 text-sm text-ink-secondary">
            <span className="font-semibold text-ink">{drivers.length}</span> drivers in session &middot;{' '}
            <span className="font-semibold text-accent">{selected.length}</span> selected
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to={`/session/${id}/live`} className="f1-btn-secondary">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Live
          </Link>
          <button onClick={handleAnalyze} disabled={analyzing || selected.length === 0} className="f1-btn-primary">
            {analyzing ? (
              <><div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" /> Analyzing...</>
            ) : 'Run Analysis'}
          </button>
        </div>
      </div>

      {/* Driver grid */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5" role="group" aria-label="Driver selection">
        {drivers.map((code, i) => {
          const isSelected = selected.includes(code)
          return (
            <button key={code} onClick={() => toggle(code)}
              aria-pressed={isSelected}
              style={{ '--i': i }}
              className={`stagger-enter relative flex flex-col items-center justify-center rounded-xl border px-4 py-4 font-mono text-sm font-semibold transition-all duration-150 ease-out-quart focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg ${
                isSelected
                  ? 'border-accent bg-accent/10 text-accent shadow-sm shadow-accent/20'
                  : 'border-border bg-surface text-ink-secondary hover:border-ink-muted hover:text-ink active:scale-[0.97]'
              }`}>
              <span className="text-lg">{code}</span>
              {isSelected && <span className="mt-1 h-1.5 w-1.5 rounded-full bg-accent animate-pulse-slow" />}
            </button>
          )
        })}
      </div>

      {error && <p className="mt-4 text-sm text-red-400" role="alert">{error}</p>}
    </div>
  )
}
