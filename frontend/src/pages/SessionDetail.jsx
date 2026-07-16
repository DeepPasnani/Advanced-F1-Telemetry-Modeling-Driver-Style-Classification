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

  if (loading) return <p className="text-center mt-20 text-gray-400">Loading drivers...</p>
  if (error) return <p className="text-center mt-20 text-red-400">{error}</p>

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">Session Drivers</h1>
      <p className="text-gray-500 font-mono text-sm mb-6">ID: {id}</p>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3 mb-6">
        {drivers.map((code) => (
          <button key={code} onClick={() => toggle(code)}
            className={`p-3 rounded-lg border font-mono text-center transition cursor-pointer
              ${selected.includes(code)
                ? 'bg-red-600 border-red-500 text-white'
                : 'bg-gray-900 border-gray-800 text-gray-300 hover:border-gray-600'}`}>
            {code}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-4">
        <p className="text-gray-400">{selected.length} driver(s) selected</p>
        <Link to={`/session/${id}/live`}
          className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded font-semibold transition">
          Live Telemetry
        </Link>
        <button onClick={handleAnalyze} disabled={analyzing || selected.length === 0}
          className="bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed px-6 py-2 rounded font-semibold">
          {analyzing ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>
      {error && <p className="text-red-400 mt-2">{error}</p>}
    </div>
  )
}
