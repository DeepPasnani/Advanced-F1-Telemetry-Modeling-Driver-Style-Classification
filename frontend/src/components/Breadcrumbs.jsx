import { Link } from 'react-router-dom'

export default function Breadcrumbs({ items }) {
  return (
    <nav className="flex items-center gap-2 text-sm text-ink-muted mb-2" aria-label="Breadcrumb">
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-2">
          {i > 0 && <span className="text-border">/</span>}
          {item.to ? (
            <Link to={item.to} className="hover:text-ink-secondary transition-colors">
              {item.label}
            </Link>
          ) : (
            <span className="text-ink-secondary">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  )
}
