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

  if (loading) return <p className="text-center mt-20 text-gray-400">Loading report...</p>
  if (error) return <p className="text-center mt-20 text-red-400">{error}</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Driver Analysis Report</h1>
        <Link to={`/analysis/${id}`}
          className="text-red-400 hover:text-red-300 font-semibold">
          ← Back to Analysis
        </Link>
      </div>

      <div className="bg-gray-900 rounded-lg p-6 border border-gray-800 mb-8">
        <pre className="text-gray-200 font-mono text-sm whitespace-pre-wrap">{report}</pre>
      </div>

      <h2 className="text-2xl font-bold mb-4">Visualizations</h2>
      <div className="grid md:grid-cols-2 gap-4">
        {PLOTS.map((name) => (
          <div key={name} className="bg-gray-900 rounded-lg p-2 border border-gray-800">
            <img src={`/api/analysis/${id}/plots/${name}.png`} alt={name}
              className="w-full rounded" />
          </div>
        ))}
      </div>
    </div>
  )
}
