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

  if (loading) return <p className="text-center mt-20 text-gray-400">Loading...</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Sessions</h1>
        <button onClick={() => setShowForm(!showForm)}
          className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded font-semibold">
          {showForm ? 'Cancel' : '+ Load Session'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleLoad} className="bg-gray-900 p-6 rounded-lg mb-6 space-y-4 border border-gray-800">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm mb-1 text-gray-400">Year</label>
              <input type="number" value={form.year}
                onChange={e => setForm({...form, year: +e.target.value})}
                className="w-full bg-gray-800 rounded px-3 py-2 border border-gray-700" />
            </div>
            <div>
              <label className="block text-sm mb-1 text-gray-400">Grand Prix</label>
              <input type="text" value={form.grand_prix}
                onChange={e => setForm({...form, grand_prix: e.target.value})}
                placeholder="e.g. Bahrain"
                className="w-full bg-gray-800 rounded px-3 py-2 border border-gray-700" />
            </div>
            <div>
              <label className="block text-sm mb-1 text-gray-400">Session</label>
              <select value={form.session_type}
                onChange={e => setForm({...form, session_type: e.target.value})}
                className="w-full bg-gray-800 rounded px-3 py-2 border border-gray-700">
                <option value="R">Race</option>
                <option value="Q">Qualifying</option>
                <option value="FP1">Practice 1</option>
                <option value="FP2">Practice 2</option>
                <option value="FP3">Practice 3</option>
              </select>
            </div>
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button type="submit"
            className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded font-semibold">
            Load
          </button>
        </form>
      )}

      {sessions.length === 0 ? (
        <div className="text-center mt-20 text-gray-500">
          <p className="text-xl mb-2">No sessions loaded yet</p>
          <p>Click "+ Load Session" to get started</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {sessions.map((id) => (
            <div key={id} onClick={() => navigate(`/session/${id}`)}
              className="bg-gray-900 hover:bg-gray-800 rounded-lg p-4 cursor-pointer border border-gray-800 transition">
              <p className="font-semibold font-mono">{id}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
