import { useEffect, useMemo, useState } from 'react'
import { api, type Plan, type Term } from '../lib/api'

export default function PlanSetup({ onChanged }: { onChanged?: () => void }) {
  const [plan, setPlan] = useState<Plan | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [newTermType, setNewTermType] = useState<'summer' | 'winter'>('summer')
  const [afterPosition, setAfterPosition] = useState<number | ''>('')

  const load = () => {
    api.getPlan().then(setPlan).catch((e) => setError(e instanceof Error ? e.message : 'Failed to load plan'))
  }

  useEffect(load, [])

  const terms = plan?.terms ?? []

  const courseCountByTerm = useMemo(() => {
    const counts: Record<string, number> = {}
    if (plan) {
      for (const pc of plan.planned_courses) {
        if (pc.term_id) counts[pc.term_id] = (counts[pc.term_id] ?? 0) + 1
      }
    }
    return counts
  }, [plan])

  const addTerm = async () => {
    if (afterPosition === '') return
    setError(null)
    try {
      const afterTerm = terms.find((t) => t.position === afterPosition)
      const yearMatch = afterTerm?.label.match(/Year \d+/)
      const anchor = yearMatch ? yearMatch[0] : afterTerm?.label ?? ''
      const label = `${newTermType === 'summer' ? 'Summer' : 'Winter'} after ${anchor}`
      await api.addTerm(newTermType, label, afterPosition)
      load()
      onChanged?.()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to add term')
    }
  }

  const removeTerm = async (term: Term) => {
    const count = courseCountByTerm[term.id] ?? 0
    if (count > 0) {
      const noun = count === 1 ? 'course' : 'courses'
      const ok = window.confirm(
        `"${term.label}" has ${count} ${noun} in it. Removing this term will move ${
          count === 1 ? 'it' : 'them'
        } back to Unscheduled — they won't be deleted, just unscheduled. Remove "${term.label}"?`,
      )
      if (!ok) return
    }
    setError(null)
    try {
      await api.removeTerm(term.id)
      load()
      onChanged?.()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to remove term')
    }
  }

  return (
    <div className="rounded-sm border border-line bg-surface">
      <div className="border-b border-line px-4 py-3">
        <h2 className="font-display text-[15px] font-bold text-ink">Terms</h2>
      </div>

      {error && <p className="px-4 pt-3 text-sm text-maroon">{error}</p>}

      <div className="flex flex-col">
        {terms.map((t) => (
          <div
            key={t.id}
            className="flex flex-wrap items-center gap-2.5 border-t border-line px-4 py-2 first:border-t-0"
          >
            <span className="text-sm text-ink">{t.label}</span>
            <span
              className={`rounded-full px-2 py-0.5 text-[11px] font-semibold whitespace-nowrap ${
                t.term_type === 'summer' || t.term_type === 'winter'
                  ? 'bg-gold-soft text-gold'
                  : 'bg-maroon-soft text-maroon'
              }`}
            >
              {t.term_type}
            </span>
            <span className="font-mono text-xs text-ink-faint">
              {courseCountByTerm[t.id] ?? 0} course{(courseCountByTerm[t.id] ?? 0) === 1 ? '' : 's'}
            </span>
            <button
              onClick={() => removeTerm(t)}
              className="ml-auto text-xs text-ink-faint hover:text-maroon"
            >
              remove
            </button>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2 border-t border-line px-4 py-3">
        <div className="flex gap-1.5">
          {(['summer', 'winter'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setNewTermType(t)}
              className={`rounded-sm border px-3 py-1.5 text-sm font-medium capitalize ${
                newTermType === t
                  ? 'border-maroon bg-maroon-soft text-maroon'
                  : 'border-line-strong text-ink-soft hover:border-maroon hover:text-maroon'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <select
          value={afterPosition}
          onChange={(e) => setAfterPosition(e.target.value === '' ? '' : Number(e.target.value))}
          className="min-w-0 flex-1 rounded-sm border border-line-strong bg-surface px-2 py-1 text-sm text-ink"
        >
          <option value="">after…</option>
          {terms.map((t) => (
            <option key={t.id} value={t.position}>after {t.label}</option>
          ))}
        </select>
        <button
          onClick={addTerm}
          disabled={afterPosition === ''}
          className="rounded-sm border border-line-strong px-3 py-1.5 text-sm text-ink-soft hover:border-maroon hover:text-maroon disabled:opacity-50"
        >
          Add term
        </button>
      </div>
    </div>
  )
}
