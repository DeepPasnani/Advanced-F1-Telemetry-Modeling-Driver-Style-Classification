import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSessions, loadSession } from '../hooks/useApi'
import LoadingSkeleton from '../components/LoadingSkeleton'
import EmptyState from '../components/EmptyState'
import ErrorMessage from '../components/ErrorMessage'

export default function Home() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ year: 2024, grand_prix: '', session_type: 'R' })
  const [loadingSession, setLoadingSession] = useState(false)
  const navigate = useNavigate()
  const formRef = useRef(null)
  const fetched = useRef(false)

  useEffect(() => {
    if (fetched.current) return
    fetched.current = true
    getSessions()
      .then((res) => setSessions(res.data))
      .catch((err) => setError(err.message || 'Failed to load sessions'))
      .finally(() => setLoading(false))
  }, [])

  const handleLoad = async (e) => {
    e.preventDefault()
    setError('')
    setLoadingSession(true)
    try {
      const res = await loadSession(form.year, form.grand_prix, form.session_type)
      navigate(`/session/${res.data.session_id}`)
    } catch (err) {
      setError(err.message)
      setLoadingSession(false)
    }
  }

  if (loading) return <LoadingSkeleton variant="list" count={3} />

  if (error && sessions.length === 0) {
    return <ErrorMessage message={error} onRetry={() => window.location.reload()} />
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink">Sessions</h1>
          <p className="mt-1 text-sm text-ink-secondary">Load and analyze F1 race sessions</p>
        </div>
        <button
          onClick={() => { setShowForm(!showForm); if (!showForm) setTimeout(() => formRef.current?.querySelector('input')?.focus(), 100) }}
          className={showForm ? 'f1-btn-secondary' : 'f1-btn-primary'}
        >
          <svg className={`h-4 w-4 transition-transform duration-200 ${showForm ? 'rotate-45' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          {showForm ? 'Cancel' : 'Load Session'}
        </button>
      </div>

      {/* Load form */}
      {showForm && (
        <form ref={formRef} onSubmit={handleLoad} className="f1-card mb-8 animate-slide-up p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="f1-label" htmlFor="year">Year</label>
              <input id="year" type="number" value={form.year}
                onChange={(e) => setForm({ ...form, year: +e.target.value })}
                className="f1-input" />
            </div>
            <div>
              <label className="f1-label" htmlFor="gp">Grand Prix</label>
              <input id="gp" type="text" value={form.grand_prix}
                onChange={(e) => setForm({ ...form, grand_prix: e.target.value })}
                placeholder="e.g. Bahrain" className="f1-input" />
            </div>
            <div>
              <label className="f1-label" htmlFor="session">Session</label>
              <select id="session" value={form.session_type}
                onChange={(e) => setForm({ ...form, session_type: e.target.value })}
                className="f1-select">
                <option value="R">Race</option>
                <option value="Q">Qualifying</option>
                <option value="FP1">Practice 1</option>
                <option value="FP2">Practice 2</option>
                <option value="FP3">Practice 3</option>
              </select>
            </div>
          </div>
          {error && <p className="mt-3 text-sm text-red-400" role="alert">{error}</p>}
          <button type="submit" disabled={loadingSession} className="f1-btn-primary mt-4">
            {loadingSession ? (
              <><div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" /> Loading...</>
            ) : 'Load'}
          </button>
        </form>
      )}

      {/* Session list or empty */}
      {sessions.length === 0 ? (
        <EmptyState icon="🏎️" title="No sessions loaded"
          description="Click 'Load Session' to load a Grand Prix session"
          action={<button onClick={() => setShowForm(true)} className="f1-btn-primary">+ Load Session</button>} />
      ) : (
        <div className="grid gap-3" role="list" aria-label="Session list">
          {sessions.map((id, i) => (
            <button key={id} onClick={() => navigate(`/session/${id}`)}
              className="f1-card-interactive group flex items-center gap-4 px-5 py-4 text-left"
              role="listitem" style={{ '--i': i }}
              aria-label={`Session ${id.slice(0, 8)}`}>
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/10 font-mono text-sm font-bold text-accent">
                {id.slice(0, 2)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-mono text-sm font-medium text-ink group-hover:text-accent transition-colors truncate">{id}</p>
                <p className="text-xs text-ink-muted">Click to view drivers</p>
              </div>
              <svg className="h-5 w-5 shrink-0 text-ink-muted group-hover:text-ink-secondary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
