import { useEffect, useState } from 'react'
import { api, type DegreeProgram, type ProgramStatus as ProgramStatusType } from '../lib/api'

export default function ProgramStatus() {
  const [programs, setPrograms] = useState<DegreeProgram[]>([])
  const [selected, setSelected] = useState<string>('')
  const [status, setStatus] = useState<ProgramStatusType | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.listPrograms().then((ps) => {
      setPrograms(ps)
      if (ps.length > 0) setSelected(ps[0].id)
    }).catch((e) => setError(e instanceof Error ? e.message : 'Failed to load programs'))
  }, [])

  useEffect(() => {
    if (!selected) return
    api.getProgramStatus(selected).then(setStatus).catch((e) => setError(e instanceof Error ? e.message : 'Failed to load status'))
  }, [selected])

  return (
    <div className="rounded-sm border border-line bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
        <h2 className="font-display text-[15px] font-bold text-ink">Requirement ledger</h2>
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="rounded-sm border border-line-strong bg-surface px-2 py-1 text-sm text-ink"
        >
          {programs.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>
      {error && <p className="p-4 text-sm text-maroon">{error}</p>}
      {status && (
        <div>
          {status.categories.map((cat) => (
            <div key={cat.category_id} className="border-b border-line px-4 py-2.5 last:border-b-0">
              <div className="flex items-center justify-between gap-3">
                <span className="text-[13.5px] font-semibold text-ink">{cat.name}</span>
                {cat.satisfied ? (
                  <span className="rounded-full bg-gold-soft px-2 py-0.5 text-[11px] font-semibold text-gold whitespace-nowrap">
                    satisfied
                  </span>
                ) : (
                  <span className="rounded-full bg-maroon-soft px-2 py-0.5 text-[11px] font-semibold text-maroon whitespace-nowrap">
                    {cat.still_needed} more
                  </span>
                )}
              </div>
              <p className="mt-0.5 font-mono text-xs text-ink-faint">
                {cat.completed_courses.length > 0 ? cat.completed_courses.join(', ') : 'none yet'}
              </p>
            </div>
          ))}

          {Object.keys(status.ambiguous_courses).length > 0 && (
            <div className="border-t border-line bg-paper px-4 py-3 text-xs text-ink-soft">
              <p className="mb-1.5 font-semibold text-maroon">Double-check these before assuming they count:</p>
              <ul className="flex flex-col gap-1">
                {Object.entries(status.ambiguous_courses).map(([code, note]) => (
                  <li key={code}>
                    <span className="font-mono font-semibold text-ink">{code}</span>: {note}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
