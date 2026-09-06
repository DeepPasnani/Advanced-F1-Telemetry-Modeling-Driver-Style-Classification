import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getDrivers, getSessionInfo, analyzeDrivers } from '../hooks/useApi'
import Breadcrumbs from '../components/Breadcrumbs'
import LoadingSkeleton from '../components/LoadingSkeleton'
import ErrorMessage from '../components/ErrorMessage'

const MIN_DRIVERS = 3

export default function SessionDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [drivers, setDrivers] = useState([])
  const [info, setInfo] = useState(null)
  const [selected, setSelected] = useState([])
  const [loading, setLoading] = useState(true)
  const [slowLoad, setSlowLoad] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    const controller = new AbortController()
    Promise.all([getDrivers(id, controller.signal), getSessionInfo(id, controller.signal)])
      .then(([driversRes, infoRes]) => {
        setDrivers(driversRes.data)
        setSelected(driversRes.data.slice(0, MIN_DRIVERS))
        setInfo(infoRes.data)
      })
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message) })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [id])

  useEffect(() => {
    if (!loading) { setSlowLoad(false); return }
    // The session's data loads lazily on this first request — a first-ever
    // (uncached) load of a session can take a while, so let the user know
    // it isn't stuck rather than leaving a bare skeleton spinning.
    const t = setTimeout(() => setSlowLoad(true), 2500)
    return () => clearTimeout(t)
  }, [loading])

  const toggle = (code) => {
    setSelected((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    )
  }

  const allSelected = drivers.length > 0 && selected.length === drivers.length
  const toggleAll = () => setSelected(allSelected ? [] : drivers)

  const canAnalyze = selected.length >= MIN_DRIVERS

  const handleAnalyze = async () => {
    if (!canAnalyze) return
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

  if (loading) return (
    <div>
      <LoadingSkeleton variant="driver-grid" />
      {slowLoad && (
        <p className="mt-4 text-center text-sm text-ink-muted">
          Fetching timing data from the F1 API — first-time loads of a session can take a little while.
        </p>
      )}
    </div>
  )

  if (error && drivers.length === 0) {
    return <ErrorMessage message={error} onRetry={() => window.location.reload()} backTo="/" backLabel="← Back to Sessions" />
  }

  return (
    <div className="animate-fade-in">
      <Breadcrumbs items={[{ label: 'Sessions', to: '/' }, { label: info ? info.grand_prix : '…' }]} />

      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          {info && <span className="f1-kicker">{info.year} &middot; {info.grand_prix}</span>}
          <h1 className="text-2xl font-bold text-ink">Select Drivers</h1>
          <p className="mt-1 text-sm text-ink-secondary">
            <span className="font-semibold text-ink">{drivers.length}</span> drivers in session &middot;{' '}
            <span className="font-semibold text-accent">{selected.length}</span> selected
            <span className="text-ink-muted"> (choose at least {MIN_DRIVERS})</span>
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
          <button type="button" onClick={toggleAll} className="f1-btn-secondary">
            {allSelected ? 'Clear All' : 'Select All'}
          </button>
          <button onClick={handleAnalyze} disabled={analyzing || !canAnalyze} className="f1-btn-primary">
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

      {selected.length > 0 && selected.length < MIN_DRIVERS && (
        <p className="mt-4 text-sm text-ink-muted">Select at least {MIN_DRIVERS} drivers to run analysis.</p>
      )}
      {error && <p className="mt-4 text-sm text-red-400" role="alert">{error}</p>}
    </div>
  )
}
