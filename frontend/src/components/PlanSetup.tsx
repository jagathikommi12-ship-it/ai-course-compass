import { useEffect, useMemo, useState } from 'react'
import { api, type Plan } from '../lib/api'

const SEMESTER_OPTIONS = [6, 7, 8]

export default function PlanSetup({ onChanged }: { onChanged?: () => void }) {
  const [plan, setPlan] = useState<Plan | null>(null)
  const [incomingCredits, setIncomingCredits] = useState(0)
  const [targetSemesters, setTargetSemesters] = useState(8)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const [newTermType, setNewTermType] = useState<'summer' | 'winter'>('summer')
  const [afterPosition, setAfterPosition] = useState<number | ''>('')

  const load = () => {
    api.getPlan().then((p) => {
      setPlan(p)
      if (p.settings) {
        setIncomingCredits(p.settings.incoming_credits)
        setTargetSemesters(p.settings.target_semesters)
      }
    }).catch((e) => setError(e instanceof Error ? e.message : 'Failed to load plan'))
  }

  useEffect(load, [])

  const courseCountByTerm = useMemo(() => {
    const counts: Record<string, number> = {}
    if (plan) {
      for (const pc of plan.planned_courses) {
        if (pc.term_id) counts[pc.term_id] = (counts[pc.term_id] ?? 0) + 1
      }
    }
    return counts
  }, [plan])

  const saveSettings = async () => {
    setSaving(true)
    setError(null)
    try {
      await api.updatePlanSettings({ incoming_credits: incomingCredits, target_semesters: targetSemesters })
      load()
      onChanged?.()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save plan settings')
    } finally {
      setSaving(false)
    }
  }

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

  const removeTerm = async (termId: string) => {
    setError(null)
    try {
      await api.removeTerm(termId)
      load()
      onChanged?.()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to remove term')
    }
  }

  const hasSettings = plan?.settings != null
  const terms = plan?.terms ?? []

  return (
    <div className="rounded-sm border border-line bg-surface">
      <div className="border-b border-line px-4 py-3">
        <h2 className="font-display text-[15px] font-bold text-ink">
          {hasSettings ? 'Plan settings' : 'Set up your 4-year plan'}
        </h2>
      </div>

      {error && <p className="px-4 pt-3 text-sm text-maroon">{error}</p>}

      <div className="flex flex-col gap-4 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-sm text-ink-soft">
            Incoming credits (AP/IB)
            <input
              type="number"
              min={0}
              step={1}
              value={incomingCredits}
              onChange={(e) => setIncomingCredits(Number(e.target.value))}
              className="ml-2 w-20 rounded-sm border border-line-strong bg-surface px-2 py-1 text-sm text-ink focus:border-maroon focus:outline-none"
            />
          </label>
        </div>

        <div>
          <p className="mb-1.5 text-sm text-ink-soft">Finish undergrad in</p>
          <div className="flex gap-2">
            {SEMESTER_OPTIONS.map((n) => (
              <button
                key={n}
                onClick={() => setTargetSemesters(n)}
                className={`rounded-sm border px-3 py-1.5 text-sm font-medium ${
                  targetSemesters === n
                    ? 'border-maroon bg-maroon-soft text-maroon'
                    : 'border-line-strong text-ink-soft hover:border-maroon hover:text-maroon'
                }`}
              >
                {n} semesters
              </button>
            ))}
          </div>
          <p className="mt-1.5 text-xs text-ink-faint">
            Summer/winter terms are extra — they don't count toward this total.
          </p>
        </div>

        <button
          onClick={saveSettings}
          disabled={saving}
          className="w-fit rounded-sm bg-maroon px-3 py-1.5 text-sm font-medium text-[#fdf6f1] hover:bg-maroon-strong disabled:opacity-50"
        >
          {saving ? 'Saving…' : hasSettings ? 'Update settings' : 'Generate my plan'}
        </button>
      </div>

      {hasSettings && (
        <>
          <div className="border-t border-line px-4 py-2">
            <p className="text-sm font-semibold text-ink">Terms</p>
          </div>
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
                  onClick={() => removeTerm(t.id)}
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
        </>
      )}
    </div>
  )
}
