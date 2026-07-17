import { useState } from 'react'

export default function PlotCard({ src, alt, id }) {
  const [loaded, setLoaded] = useState(false)
  return (
    <div className="f1-card overflow-hidden p-2 transition-all duration-200 hover:shadow-card-hover">
      {!loaded && (
        <div className="flex aspect-video items-center justify-center bg-surface animate-pulse rounded-lg">
          <div className="h-8 w-8 rounded-full border-2 border-border border-t-accent animate-spin" />
        </div>
      )}
      <img
        id={id}
        src={src}
        alt={alt}
        className={`w-full rounded-lg transition-opacity duration-300 ${loaded ? 'opacity-100' : 'opacity-0 h-0'}`}
        loading="lazy"
        onLoad={() => setLoaded(true)}
      />
    </div>
  )
}
