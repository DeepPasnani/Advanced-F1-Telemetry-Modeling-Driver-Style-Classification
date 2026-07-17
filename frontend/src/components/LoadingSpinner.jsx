export default function LoadingSpinner({ size = 'md', label = 'Loading...' }) {
  const sizes = { sm: 'h-5 w-5', md: 'h-8 w-8', lg: 'h-12 w-12' }
  return (
    <div className="flex flex-col items-center justify-center gap-3" role="status" aria-label={label}>
      <div className={`${sizes[size]} animate-spin rounded-full border-2 border-border border-t-accent`} />
      <span className="text-xs font-medium text-ink-muted">{label}</span>
    </div>
  )
}
