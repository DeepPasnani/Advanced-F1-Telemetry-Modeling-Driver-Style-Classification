import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSessions, loadSession, fetchApi } from '../hooks/useApi'
import LoadingSkeleton from '../components/LoadingSkeleton'
import EmptyState from '../components/EmptyState'
import ErrorMessage from '../components/ErrorMessage'

const CURRENT_YEAR = new Date().getFullYear()
const EARLIEST_YEAR = 2018 // FastF1 telemetry channels are reliable from 2018 onward
const YEARS = Array.from({ length: CURRENT_YEAR + 1 - EARLIEST_YEAR }, (_, i) => CURRENT_YEAR - i)

const SESSION_TYPES = [
  { value: 'R', label: 'Race' },
  { value: 'Q', label: 'Qualifying' },
  { value: 'S', label: 'Sprint' },
  { value: 'FP1', label: 'Practice 1' },
  { value: 'FP2', label: 'Practice 2' },
  { value: 'FP3', label: 'Practice 3' },
]

export default function Home() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [year, setYear] = useState(CURRENT_YEAR)
  const [grandPrix, setGrandPrix] = useState('')
  const [sessionType, setSessionType] = useState('R')
  const [schedule, setSchedule] = useState([])
  const [scheduleLoading, setScheduleLoading] = useState(false)
  const [scheduleError, setScheduleError] = useState(false)
  const [scheduleRetryCount, setScheduleRetryCount] = useState(0)
  const [loadingSession, setLoadingSession] = useState(false)
  const [slowWake, setSlowWake] = useState(false)
  const navigate = useNavigate()
  const formRef = useRef(null)
  const fetched = useRef(false)

  useEffect(() => {
    if (fetched.current) return
    fetched.current = true
    const controller = new AbortController()
    getSessions(controller.signal)
      .then((res) => setSessions(res.data))
      .catch((err) => { if (err.name !== 'AbortError') setError(err.message || 'Failed to load sessions') })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [])

  useEffect(() => {
    // Free-tier hosts (e.g. Render) spin the backend down after a period of
    // inactivity — the first request after that wakes it back up, which can
    // take 30-60s. Surface that instead of leaving a bare spinner.
    const busy = loading || loadingSession
    if (!busy) { setSlowWake(false); return }
    const t = setTimeout(() => setSlowWake(true), 4000)
    return () => clearTimeout(t)
  }, [loading, loadingSession])

  useEffect(() => {
    setScheduleLoading(true)
    setScheduleError(false)
    setGrandPrix('')
    const controller = new AbortController()
    // Without a hard cutoff, a stalled network request to the F1 schedule
    // API left "Loading calendar…" spinning indefinitely with no way out.
    let timedOut = false
    const timeoutId = setTimeout(() => { timedOut = true; controller.abort() }, 15000)
    fetchApi(`/schedule/${year}`, {}, controller.signal)
      .then((res) => {
        setSchedule(res.data)
        if (res.data.length > 0) setGrandPrix(res.data[0])
      })
      .catch((err) => {
        if (err.name === 'AbortError' && !timedOut) return // superseded by a newer year change, not a real failure
        setSchedule([])
        setScheduleError(true)
      })
      .finally(() => { clearTimeout(timeoutId); setScheduleLoading(false) })
    return () => { clearTimeout(timeoutId); controller.abort() }
  }, [year, scheduleRetryCount])

  const handleLoad = async (e) => {
    e.preventDefault()
    if (!grandPrix) {
      setError('Select a Grand Prix')
      return
    }
    setError('')
    setLoadingSession(true)
    try {
      const res = await loadSession(year, grandPrix, sessionType)
      navigate(`/session/${res.data.session_id}`)
    } catch (err) {
      setError(err.message)
      setLoadingSession(false)
    }
  }

  if (loading) return (
    <div>
      <LoadingSkeleton variant="list" count={3} />
      {slowWake && (
        <p className="mt-4 text-center text-sm text-ink-muted">
          Waking up the backend — free-tier hosting spins down when idle, this can take up to a minute.
        </p>
      )}
    </div>
  )

  if (error && sessions.length === 0) {
    return <ErrorMessage message={error} onRetry={() => window.location.reload()} />
  }

  return (
    <div className="animate-fade-in">
      {/* Hero */}
      <div className="mb-10 flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="f1-kicker">Telemetry Dashboard</span>
          <h1 className="text-3xl font-bold text-ink">Sessions</h1>
          <p className="mt-1.5 text-sm text-ink-secondary">Load a Grand Prix session and break down every driver's style</p>
        </div>
        <button
          onClick={() => { setShowForm(!showForm); if (!showForm) setTimeout(() => formRef.current?.querySelector('select,input')?.focus(), 100) }}
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
        <form ref={formRef} onSubmit={handleLoad} className="f1-card f1-card-accent mb-10 animate-slide-up p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="f1-label" htmlFor="year">Year</label>
              <select id="year" value={year} onChange={(e) => setYear(+e.target.value)} className="f1-select">
                {YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
            <div>
              <label className="f1-label" htmlFor="gp">Grand Prix</label>
              <select id="gp" value={grandPrix} onChange={(e) => setGrandPrix(e.target.value)}
                disabled={scheduleLoading || scheduleError || schedule.length === 0} className="f1-select">
                {scheduleLoading && <option>Loading calendar…</option>}
                {!scheduleLoading && !scheduleError && schedule.length === 0 && <option>No events found</option>}
                {!scheduleLoading && scheduleError && <option>Couldn't load calendar</option>}
                {!scheduleLoading && !scheduleError && schedule.map((name) => <option key={name} value={name}>{name}</option>)}
              </select>
              {scheduleError && (
                <button type="button" onClick={() => setScheduleRetryCount((c) => c + 1)}
                  className="mt-1.5 text-xs font-medium text-accent hover:text-accent-hover">
                  Retry loading calendar
                </button>
              )}
            </div>
            <div>
              <label className="f1-label" htmlFor="session">Session</label>
              <select id="session" value={sessionType} onChange={(e) => setSessionType(e.target.value)} className="f1-select">
                {SESSION_TYPES.map(({ value, label }) => <option key={value} value={value}>{label}</option>)}
              </select>
            </div>
          </div>
          {error && <p className="mt-3 text-sm text-red-400" role="alert">{error}</p>}
          <button type="submit" disabled={loadingSession || scheduleLoading || !grandPrix} className="f1-btn-primary mt-4">
            {loadingSession ? (
              <><div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" /> Loading...</>
            ) : 'Load'}
          </button>
          {loadingSession && slowWake && (
            <p className="mt-2 text-xs text-ink-muted">Waking up the backend — this can take up to a minute on a cold start.</p>
          )}
        </form>
      )}

      {/* Session list or empty */}
      {sessions.length === 0 ? (
        <EmptyState icon="🏎️" title="No sessions loaded"
          description="Click 'Load Session' to load a Grand Prix session"
          action={<button onClick={() => setShowForm(true)} className="f1-btn-primary">+ Load Session</button>} />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3" role="list" aria-label="Session list">
          {sessions.map((session, i) => (
            <button key={session.id} onClick={() => navigate(`/session/${session.id}`)}
              className="f1-card-interactive group flex items-center gap-4 px-5 py-4 text-left"
              role="listitem" style={{ '--i': i }}
              aria-label={session.label}>
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-accent/10 font-wide text-sm font-bold text-accent">
                {String(session.year).slice(2)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-ink group-hover:text-accent transition-colors truncate">{session.grand_prix}</p>
                <p className="text-xs text-ink-muted">{session.year} &middot; {session.label.split('—').pop().trim()}</p>
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
