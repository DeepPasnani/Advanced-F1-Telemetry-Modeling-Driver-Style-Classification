import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getReport } from '../hooks/useApi'

const PLOTS = ['cluster_scatter', 'radar_chart', 'speed_trace', 'throttle_brake', 'sector_comparison']

export default function AnalysisResults() {
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

  if (loading) return <p className="text-center mt-20 text-gray-400">Loading analysis...</p>
  if (error) return <p className="text-center mt-20 text-red-400">{error}</p>

  const sections = report.split('\n\n').filter(s => s.startsWith('Driver:'))

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Analysis Results</h1>
        <Link to={`/analysis/${id}/report`}
          className="bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded font-semibold transition">
          Full Report →
        </Link>
      </div>

      <div className="grid md:grid-cols-3 gap-4 mb-8">
        {sections.map((section) => {
          const lines = section.split('\n')
          const driver = lines[0].replace('Driver: ', '')
          const style = lines[1]?.replace('  Style Classification: ', '')
          const speed = lines[2]?.replace('  Mean Speed: ', '')
          const brake = lines[3]?.replace('  Brake Frequency: ', '')
          const aggression = lines[4]?.replace('  Aggression Index: ', '')
          const styleColor = style?.includes('Aggressive') ? 'bg-red-700' :
            style?.includes('Smooth') ? 'bg-green-700' : 'bg-blue-700'
          return (
            <div key={driver} className="bg-gray-900 rounded-lg p-5 border border-gray-800">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-2xl font-bold font-mono">{driver}</h2>
                <span className={`${styleColor} text-xs px-2 py-1 rounded-full`}>{style}</span>
              </div>
              <p className="text-gray-400 text-sm">Speed: {speed}</p>
              <p className="text-gray-400 text-sm">Brake: {brake}</p>
              <p className="text-gray-400 text-sm">Aggression: {aggression}</p>
            </div>
          )
        })}
      </div>

      <h2 className="text-2xl font-bold mb-4">Plots</h2>
      <div className="grid md:grid-cols-2 gap-4 mb-6">
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
