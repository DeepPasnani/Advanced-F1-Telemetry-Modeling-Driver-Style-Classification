import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSessions, loadSession } from '../hooks/useApi'

export default function Home() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ year: 2024, grand_prix: '', session_type: 'R' })
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    getSessions()
      .then((res) => setSessions(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleLoad = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const res = await loadSession(form.year, form.grand_prix, form.session_type)
      navigate(`/session/${res.data.session_id}`)
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="h-8 w-8 animate-pulse-slow rounded-full border-2 border-accent border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink">Sessions</h1>
          <p className="mt-1 text-sm text-ink-secondary">Load and analyze F1 race sessions</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className={showForm ? 'f1-btn-secondary' : 'f1-btn-primary'}
        >
          {showForm ? 'Cancel' : '+ Load Session'}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleLoad}
          className="f1-card mb-8 animate-slide-up p-6"
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="f1-label">Year</label>
              <input
                type="number"
                value={form.year}
                onChange={(e) => setForm({ ...form, year: +e.target.value })}
                className="f1-input"
              />
            </div>
            <div>
              <label className="f1-label">Grand Prix</label>
              <input
                type="text"
                value={form.grand_prix}
                onChange={(e) => setForm({ ...form, grand_prix: e.target.value })}
                placeholder="e.g. Bahrain"
                className="f1-input"
              />
            </div>
            <div>
              <label className="f1-label">Session</label>
              <select
                value={form.session_type}
                onChange={(e) => setForm({ ...form, session_type: e.target.value })}
                className="f1-select"
              >
                <option value="R">Race</option>
                <option value="Q">Qualifying</option>
                <option value="FP1">Practice 1</option>
                <option value="FP2">Practice 2</option>
                <option value="FP3">Practice 3</option>
              </select>
            </div>
          </div>
          {error && (
            <p className="mt-3 text-sm text-red-400">{error}</p>
          )}
          <button type="submit" className="f1-btn-primary mt-4">
            Load
          </button>
        </form>
      )}

      {sessions.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="mb-4 text-4xl">🏎️</div>
          <h2 className="text-lg font-semibold text-ink">No sessions loaded</h2>
          <p className="mt-1 text-sm text-ink-secondary">
            Click &ldquo;+ Load Session&rdquo; to load a Grand Prix session
          </p>
        </div>
      ) : (
        <div className="grid gap-3">
          {sessions.map((id) => (
            <button
              key={id}
              onClick={() => navigate(`/session/${id}`)}
              className="f1-card group flex items-center gap-4 px-5 py-4 text-left transition-all duration-150 hover:shadow-card-hover"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10 font-mono text-sm font-bold text-accent">
                {id.slice(0, 2)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-mono text-sm font-medium text-ink group-hover:text-accent transition-colors">
                  {id}
                </p>
                <p className="text-xs text-ink-muted">Click to view drivers</p>
              </div>
              <svg className="h-5 w-5 text-ink-muted group-hover:text-ink-secondary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
