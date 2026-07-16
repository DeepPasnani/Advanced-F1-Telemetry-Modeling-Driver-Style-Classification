# F1 Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a React + Vite + Tailwind dashboard for the F1 Telemetry API.

**Architecture:** Vite dev server proxies `/api` to FastAPI backend. React Router handles multi-page navigation. Custom hooks encapsulate API calls. Tailwind for styling.

**Tech Stack:** Vite, React 18, React Router v6, Tailwind CSS, fetch API

## Global Constraints

- All API calls go through Vite proxy: `/api/*` → `http://localhost:8000/*`
- No backend changes — the existing API is the single source of truth
- Follow standard Vite React project structure (`src/`, `src/components/`, `src/pages/`, `src/hooks/`)
- Port 5173 (Vite default) for dev server

---

### Task 1: Scaffold Vite + React + Tailwind Project

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/index.css`
- Create: `frontend/src/components/Header.jsx`

**Interfaces:**
- Produces: bootable Vite dev server with React, Tailwind, and React Router

- [ ] **Step 1: Create package.json**

```json
{
  "name": "f1-dashboard",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

- [ ] **Step 2: Create vite.config.js**

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

- [ ] **Step 3: Create tailwind.config.js**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
}
```

- [ ] **Step 4: Create postcss.config.js**

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 5: Create index.html**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>F1 Telemetry Dashboard</title>
  </head>
  <body class="bg-gray-950 text-gray-100">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Create src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 7: Create src/main.jsx**

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
)
```

- [ ] **Step 8: Create src/App.jsx**

```jsx
import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Home from './pages/Home'
import SessionDetail from './pages/SessionDetail'
import AnalysisResults from './pages/AnalysisResults'
import Report from './pages/Report'

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
        </Routes>
      </main>
    </div>
  )
}
```

- [ ] **Step 9: Create src/components/Header.jsx**

```jsx
import { Link } from 'react-router-dom'

export default function Header() {
  return (
    <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
      <nav className="container mx-auto flex items-center gap-6">
        <Link to="/" className="text-xl font-bold text-red-500">F1 Telemetry</Link>
        <Link to="/" className="text-gray-300 hover:text-white">Home</Link>
      </nav>
    </header>
  )
}
```

- [ ] **Step 10: Install deps + verify dev server boots**

```bash
cd frontend && npm install && npx vite --host 0.0.0.0 &
sleep 3 && curl -s http://localhost:5173 | head -5
kill %1
```

Expected: HTML page with `<div id="root">` is returned

- [ ] **Step 11: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold Vite + React + Tailwind project"
```

---

### Task 2: Create API Hook

**Files:**
- Create: `frontend/src/hooks/useApi.js`

**Interfaces:**
- Produces: `fetchApi(path, options)` — wraps fetch with `/api` prefix, JSON parsing, error handling
- Consumed by: all page components

- [ ] **Step 1: Write the hook**

```js
const BASE = '/api'

export async function fetchApi(path, options = {}) {
  const url = `${BASE}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`)
  }
  return data
}

export async function getSessions() {
  return fetchApi('/sessions')
}

export async function loadSession(year, grandPrix, sessionType = 'R') {
  return fetchApi('/sessions/load', {
    method: 'POST',
    body: JSON.stringify({ year, grand_prix: grandPrix, session_type: sessionType }),
  })
}

export async function getDrivers(sessionId) {
  return fetchApi(`/sessions/${sessionId}/drivers`)
}

export async function analyzeDrivers(sessionId, driverCodes) {
  return fetchApi(`/sessions/${sessionId}/analyze`, {
    method: 'POST',
    body: JSON.stringify({ driver_codes: driverCodes }),
  })
}

export async function getReport(analysisId) {
  return fetchApi(`/analysis/${analysisId}/report`)
}
```

- [ ] **Step 2: Create page directory structure**

```bash
mkdir -p frontend/src/pages frontend/src/components frontend/src/hooks
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useApi.js
git commit -m "feat: add API hook layer"
```

---

### Task 3: Build Home Page

**Files:**
- Create: `frontend/src/pages/Home.jsx`

**Behavior:**
- On mount, `GET /sessions` and display cards
- Each card shows session info + link to `/session/:id`
- "Load New Session" button opens inline form (year, grand prix, session type)
- On submit, `POST /sessions/load`, then redirect to `/session/:id`
- Empty state when no sessions

- [ ] **Step 1: Write the page**

```jsx
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
        <form onSubmit={handleLoad} className="bg-gray-900 p-6 rounded-lg mb-6 space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm mb-1">Year</label>
              <input type="number" value={form.year} onChange={e => setForm({...form, year: +e.target.value})}
                className="w-full bg-gray-800 rounded px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm mb-1">Grand Prix</label>
              <input type="text" value={form.grand_prix} onChange={e => setForm({...form, grand_prix: e.target.value})}
                placeholder="e.g. Bahrain" className="w-full bg-gray-800 rounded px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm mb-1">Session</label>
              <select value={form.session_type} onChange={e => setForm({...form, session_type: e.target.value})}
                className="w-full bg-gray-800 rounded px-3 py-2">
                <option value="R">Race</option>
                <option value="Q">Qualifying</option>
                <option value="FP1">Practice 1</option>
                <option value="FP2">Practice 2</option>
                <option value="FP3">Practice 3</option>
              </select>
            </div>
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button type="submit" className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded font-semibold">
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
              className="bg-gray-900 hover:bg-gray-800 rounded-lg p-4 cursor-pointer border border-gray-800">
              <p className="font-semibold">{id}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Home.jsx
git commit -m "feat: add Home page with session list and load form"
```

---

### Task 4: Build Session Detail Page

**Files:**
- Create: `frontend/src/pages/SessionDetail.jsx`

**Behavior:**
- Reads `:id` from URL params
- `GET /sessions/:id/drivers` → display driver list with checkboxes
- "Run Analysis" button → `POST /sessions/:id/analyze` with selected drivers → redirect to `/analysis/:id`
- Loading and error states

- [ ] **Step 1: Write the page**

```jsx
import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
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
      <h1 className="text-3xl font-bold mb-6">Session Drivers</h1>
      <p className="text-gray-400 mb-4">Session ID: {id}</p>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3 mb-6">
        {drivers.map((code) => (
          <button key={code} onClick={() => toggle(code)}
            className={`p-3 rounded-lg border font-mono text-center transition
              ${selected.includes(code)
                ? 'bg-red-600 border-red-500 text-white'
                : 'bg-gray-900 border-gray-800 text-gray-300 hover:border-gray-600'}`}>
            {code}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-4">
        <p className="text-gray-400">{selected.length} driver(s) selected</p>
        <button onClick={handleAnalyze} disabled={analyzing || selected.length === 0}
          className="bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed px-6 py-2 rounded font-semibold">
          {analyzing ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>
      {error && <p className="text-red-400 mt-2">{error}</p>}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/SessionDetail.jsx
git commit -m "feat: add Session Detail page with driver selection"
```

---

### Task 5: Build Analysis Results Page

**Files:**
- Create: `frontend/src/pages/AnalysisResults.jsx`

**Behavior:**
- Reads `:id` from URL params
- Fetches report via `GET /analysis/:id/report`
- Displays: per-driver style badges, predictions table, features table, link to report page
- Plot images embedded from `/api/analysis/:id/plots/:name`

- [ ] **Step 1: Write the page**

```jsx
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

  // Parse driver sections from report text
  const sections = report.split('\n\n').filter(s => s.startsWith('Driver:'))

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Analysis Results</h1>
        <Link to={`/analysis/${id}/report`}
          className="bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded font-semibold">
          Full Report →
        </Link>
      </div>

      {/* Driver Style Cards */}
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

      {/* Plots */}
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/AnalysisResults.jsx
git commit -m "feat: add Analysis Results page with style cards and plots"
```

---

### Task 6: Build Report Page

**Files:**
- Create: `frontend/src/pages/Report.jsx`

**Behavior:**
- Reads `:id` from URL params
- Fetches `GET /analysis/:id/report` — displays formatted report text
- Shows all plot images below the report
- "Back to Analysis" link

- [ ] **Step 1: Write the page**

```jsx
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

      {/* Report Text */}
      <div className="bg-gray-900 rounded-lg p-6 border border-gray-800 mb-8">
        <pre className="text-gray-200 font-mono text-sm whitespace-pre-wrap">{report}</pre>
      </div>

      {/* Plots */}
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Report.jsx
git commit -m "feat: add Report page with full text and plots"
```

---

### Task 7: Integration Smoke Test

**Files:** None new — starts both servers and verifies the full frontend + backend flow.

- [ ] **Step 1: Start backend**

```bash
cd /home/deepp/Deep-Files/Projects/Github/Project Repos/Advanced-F1-Telemetry-Modeling-Driver-Style-Classification-main
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000 &
sleep 3
curl -s http://127.0.0.1:8000/sessions && echo " Backend OK"
```

- [ ] **Step 2: Start frontend**

```bash
cd frontend && npx vite --host 0.0.0.0 &
sleep 3
curl -s http://localhost:5173 | grep -q 'root' && echo " Frontend OK"
```

- [ ] **Step 3: Test API proxy**

```bash
curl -s http://localhost:5173/api/sessions | python -m json.tool
```

Expected: `{ "status": "ok", "data": [...] }`

- [ ] **Step 4: Load a session through the proxy**

```bash
curl -s -X POST http://localhost:5173/api/sessions/load \
  -H "Content-Type: application/json" \
  -d '{"year": 2023, "grand_prix": "Bahrain", "session_type": "R"}' | python -m json.tool
```

Expected: 200 response with session_id

- [ ] **Step 5: Kill servers**

```bash
kill %1 %2 2>/dev/null
```

- [ ] **Step 6: Commit any final fixes**

```bash
git add -A && git commit -m "chore: finalize Phase 2 dashboard"
```
