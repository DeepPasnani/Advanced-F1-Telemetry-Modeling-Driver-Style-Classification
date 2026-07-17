import { Link } from 'react-router-dom'

export default function ErrorMessage({ message, onRetry, backTo, backLabel = '← Back' }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center animate-fade-in">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/10">
        <svg className="h-8 w-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h2 className="text-lg font-semibold text-ink mb-1">Something went wrong</h2>
      <p className="max-w-md text-sm text-ink-secondary mb-6">{message}</p>
      <div className="flex items-center gap-3">
        {onRetry && (
          <button onClick={onRetry} className="f1-btn-primary">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h5M20 20v-5h-5" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 9a9 9 0 0115.36-5.36M20 15a9 9 0 01-15.36 5.36" />
            </svg>
            Try again
          </button>
        )}
        {backTo && (
          <Link to={backTo} className="f1-btn-secondary">{backLabel}</Link>
        )}
      </div>
    </div>
  )
}
