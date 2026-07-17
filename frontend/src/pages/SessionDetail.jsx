import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getDrivers, analyzeDrivers } from '../hooks/useApi'

export default function SessionDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [drivers, setDrivers] = useState([])
  const [selected, setSelected] = useState([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
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
    try {
      const res = await analyzeDrivers(id, selected)
      navigate(`/analysis/${res.data.analysis_id}`)
    } catch (err) {
      setError(err.message)
      setAnalyzing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="h-8 w-8 animate-pulse-slow rounded-full border-2 border-accent border-t-transparent" />
      </div>
    )
  }

  if (error && drivers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <p className="text-red-400">{error}</p>
        <Link to="/" className="f1-btn-secondary mt-4">← Back to Sessions</Link>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm text-ink-muted mb-2">
          <Link to="/" className="hover:text-ink-secondary transition-colors">Sessions</Link>
          <span>/</span>
          <span className="text-ink-secondary font-mono">{id.slice(0, 8)}</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-ink">Select Drivers</h1>
            <p className="mt-1 text-sm text-ink-secondary">
              {drivers.length} drivers in session &middot; {selected.length} selected
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link to={`/session/${id}/live`} className="f1-btn-secondary">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Live Telemetry
            </Link>
            <button
              onClick={handleAnalyze}
              disabled={analyzing || selected.length === 0}
              className="f1-btn-primary"
            >
              {analyzing ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Analyzing...
                </>
              ) : (
                'Run Analysis'
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {drivers.map((code) => {
          const isSelected = selected.includes(code)
          return (
            <button
              key={code}
              onClick={() => toggle(code)}
              className={`relative flex flex-col items-center justify-center rounded-xl border px-4 py-4 font-mono text-sm font-semibold transition-all duration-150 ${
                isSelected
                  ? 'border-accent bg-accent/10 text-accent shadow-sm shadow-accent/20'
                  : 'border-border bg-surface text-ink-secondary hover:border-ink-muted hover:text-ink'
              }`}
            >
              <span className="text-lg">{code}</span>
              {isSelected && (
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-accent" />
              )}
            </button>
          )
        })}
      </div>

      {error && (
        <p className="mt-4 text-sm text-red-400">{error}</p>
      )}
    </div>
  )
}
