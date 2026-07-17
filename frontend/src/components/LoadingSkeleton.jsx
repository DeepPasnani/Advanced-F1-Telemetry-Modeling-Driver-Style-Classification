export default function LoadingSkeleton({ variant = 'card', count = 3 }) {
  if (variant === 'card') {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" role="status" aria-label="Loading content">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="f1-card animate-pulse p-5">
            <div className="mb-4 flex items-center justify-between">
              <div className="h-6 w-20 rounded bg-surface-raised" />
              <div className="h-5 w-24 rounded-full bg-surface-raised" />
            </div>
            <div className="space-y-3">
              <div className="space-y-2">
                <div className="h-3 w-16 rounded bg-surface-raised" />
                <div className="h-7 w-28 rounded bg-surface-raised" />
              </div>
              <div className="space-y-2">
                <div className="h-3 w-24 rounded bg-surface-raised" />
                <div className="h-2 w-full rounded-full bg-surface-raised" />
              </div>
              <div className="space-y-2">
                <div className="h-3 w-20 rounded bg-surface-raised" />
                <div className="h-2 w-full rounded-full bg-surface-raised" />
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (variant === 'driver-grid') {
    return (
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5" role="status" aria-label="Loading drivers">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="animate-pulse rounded-xl border border-border bg-surface px-4 py-5">
            <div className="mx-auto h-5 w-10 rounded bg-surface-raised" />
          </div>
        ))}
      </div>
    )
  }

  if (variant === 'list') {
    return (
      <div className="grid gap-3" role="status" aria-label="Loading list">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="animate-pulse flex items-center gap-4 rounded-xl border border-border bg-surface px-5 py-4">
            <div className="h-10 w-10 rounded-lg bg-surface-raised" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-48 rounded bg-surface-raised" />
              <div className="h-3 w-24 rounded bg-surface-raised" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  return null
}
