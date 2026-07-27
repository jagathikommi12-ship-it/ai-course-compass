import { useEffect, useState } from 'react'
import { api, type Course } from '../lib/api'

export default function RecommendationMode({ refreshKey }: { refreshKey: number }) {
  const [eligible, setEligible] = useState<Course[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api
      .getRecommendations()
      .then((r) => setEligible(r.eligible_courses))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load recommendations'))
      .finally(() => setLoading(false))
  }, [refreshKey])

  return (
    <div className="rounded-sm border border-line bg-surface">
      <div className="border-b border-line px-4 py-3">
        <h2 className="font-display text-[15px] font-bold text-ink">Recommendation mode — eligible now</h2>
      </div>
      <div className="p-4">
        {error && <p className="text-sm text-maroon">{error}</p>}
        {loading ? (
          <p className="text-sm text-ink-faint">Loading…</p>
        ) : eligible.length === 0 ? (
          <p className="text-sm text-ink-faint">Check off completed courses above to see what unlocks.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {eligible.map((c) => (
              <span
                key={c.code}
                className="rounded-full border border-line-strong px-2.5 py-1 text-xs text-ink-soft"
              >
                <span className="font-mono font-semibold text-ink">{c.code}</span> {c.title}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
