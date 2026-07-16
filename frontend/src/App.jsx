import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Home from './pages/Home'
import SessionDetail from './pages/SessionDetail'
import AnalysisResults from './pages/AnalysisResults'
import Report from './pages/Report'
import LiveTelemetry from './pages/LiveTelemetry'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/session/:id" element={<SessionDetail />} />
          <Route path="/analysis/:id" element={<AnalysisResults />} />
          <Route path="/analysis/:id/report" element={<Report />} />
          <Route path="/session/:id/live" element={<LiveTelemetry />} />
        </Routes>
      </main>
    </div>
  )
}
