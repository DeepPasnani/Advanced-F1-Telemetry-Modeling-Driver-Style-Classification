import { useEffect, useRef, useState } from 'react'

const RETRY_INTERVAL_MS = 1200
const MAX_ATTEMPTS = 25 // ~30s ceiling before giving up

export default function PlotCard({ src, alt, id, title, description }) {
  const [loaded, setLoaded] = useState(false)
  const [failed, setFailed] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const timeoutRef = useRef(null)

  useEffect(() => {
    setLoaded(false)
    setFailed(false)
    setAttempt(0)
  }, [src])

  useEffect(() => () => clearTimeout(timeoutRef.current), [])

  const handleError = () => {
    if (attempt + 1 >= MAX_ATTEMPTS) {
      setFailed(true)
      return
    }
    timeoutRef.current = setTimeout(() => setAttempt((a) => a + 1), RETRY_INTERVAL_MS)
  }

  const cacheBustedSrc = attempt > 0 ? `${src}?retry=${attempt}` : src

  return (
    <div className="f1-card overflow-hidden p-2 transition-all duration-200 hover:shadow-card-hover">
      {!loaded && !failed && (
        <div className="flex aspect-video flex-col items-center justify-center gap-2 bg-surface animate-pulse rounded-lg">
          <div className="h-8 w-8 rounded-full border-2 border-border border-t-accent animate-spin" />
          {attempt > 2 && <span className="text-xs text-ink-muted">Generating plot…</span>}
        </div>
      )}
      {failed && (
        <div className="flex aspect-video flex-col items-center justify-center gap-2 bg-surface rounded-lg text-center px-4">
          <span className="text-xs text-ink-muted">Couldn't load this plot.</span>
          <button
            onClick={() => { setFailed(false); setAttempt(0) }}
            className="f1-btn-secondary py-1 px-3 text-xs"
          >
            Retry
          </button>
        </div>
      )}
      <img
        id={id}
        src={cacheBustedSrc}
        alt={alt}
        className={`w-full rounded-lg transition-opacity duration-300 ${loaded ? 'opacity-100' : 'opacity-0 h-0'}`}
        loading="lazy"
        onLoad={() => setLoaded(true)}
        onError={handleError}
      />
      {(title || description) && (
        <div className="px-2 pb-1.5 pt-3">
          {title && <h4 className="text-xs font-semibold text-ink">{title}</h4>}
          {description && <p className="mt-0.5 text-xs leading-relaxed text-ink-secondary">{description}</p>}
        </div>
      )}
    </div>
  )
}
