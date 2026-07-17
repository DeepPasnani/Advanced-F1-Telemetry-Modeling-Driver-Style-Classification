export default function EmptyState({ icon = '🏎️', title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center animate-fade-in">
      <div className="mb-4 text-5xl leading-none">{icon}</div>
      <h2 className="text-lg font-semibold text-ink mb-1">{title}</h2>
      {description && <p className="max-w-sm text-sm text-ink-secondary mb-6">{description}</p>}
      {action && action}
    </div>
  )
}
