import { Link, useLocation } from 'react-router-dom'

const NAV_ITEMS = [
  { path: '/', label: 'Sessions' },
]

export default function Header() {
  const { pathname } = useLocation()
  const isActive = (p) => pathname === p || (p !== '/' && pathname.startsWith(p))

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-bg/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-6 px-6">
        <Link to="/" className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-sm font-bold text-white">F1</span>
          <span className="text-lg font-bold tracking-tight text-ink">Telemetry</span>
        </Link>
        <nav className="flex items-center gap-1">
          {NAV_ITEMS.map(({ path, label }) => (
            <Link
              key={path}
              to={path}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors duration-150 ${
                isActive(path)
                  ? 'bg-surface-raised text-ink'
                  : 'text-ink-secondary hover:bg-surface-raised hover:text-ink'
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  )
}
