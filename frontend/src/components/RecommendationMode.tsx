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
    <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
      <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
        Recommendation mode — you're eligible for
      </h2>
      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      {loading ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
      ) : eligible.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Check off completed courses above to see what unlocks.
        </p>
      ) : (
        <ul className="grid grid-cols-1 gap-1 sm:grid-cols-2">
          {eligible.map((c) => (
            <li key={c.code} className="rounded bg-indigo-50 px-2 py-1 text-sm text-indigo-900 dark:bg-indigo-950 dark:text-indigo-200">
              <span className="font-medium">{c.code}</span> — {c.title}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
