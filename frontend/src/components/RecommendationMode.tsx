import { useEffect, useState } from 'react'
import { api, type Course, type DegreeProgram } from '../lib/api'

export default function RecommendationMode({ refreshKey }: { refreshKey: number }) {
  const [programs, setPrograms] = useState<DegreeProgram[]>([])
  const [selected, setSelected] = useState('')
  const [eligible, setEligible] = useState<Course[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.listPrograms().then((ps) => {
      setPrograms(ps)
      if (ps.length > 0) setSelected(ps[0].id)
    }).catch(() => {})
  }, [])

  const fetchRecommendations = () => {
    if (!selected) return
    setLoading(true)
    setError(null)
    api
      .getRecommendations(selected)
      .then((r) => setEligible(r.eligible_courses))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load recommendations'))
      .finally(() => setLoading(false))
  }

  // Once opened, keep it live as courses get checked off elsewhere.
  useEffect(() => {
    if (eligible !== null) fetchRecommendations()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey])

  return (
    <div className="rounded-sm border border-line bg-surface">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3">
        <h2 className="font-display text-[15px] font-bold text-ink">What can I take next?</h2>
        <div className="flex items-center gap-2">
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="rounded-sm border border-line-strong bg-surface px-2 py-1 text-sm text-ink"
          >
            {programs.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <button
            onClick={fetchRecommendations}
            disabled={loading || !selected}
            className="rounded-sm bg-maroon px-3 py-1.5 text-sm font-medium text-[#fdf6f1] hover:bg-maroon-strong disabled:opacity-50"
          >
            {loading ? 'Loading…' : 'Recommend'}
          </button>
        </div>
      </div>
      <div className="p-4">
        {error && <p className="text-sm text-maroon">{error}</p>}
        {eligible === null && !error && (
          <p className="text-sm text-ink-faint">
            Click Recommend to see which courses toward this program you're eligible to take next, based on what
            you've checked off in the checklist above.
          </p>
        )}
        {eligible !== null && eligible.length === 0 && (
          <p className="text-sm text-ink-faint">
            Nothing new is eligible yet — check off completed courses above to unlock more.
          </p>
        )}
        {eligible !== null && eligible.length > 0 && (
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
