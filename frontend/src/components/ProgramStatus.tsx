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
    <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">What am I still missing?</h2>
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800"
        >
          {programs.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>
      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      {status && (
        <div className="flex flex-col gap-3">
          {status.categories.map((cat) => (
            <div key={cat.category_id} className="rounded border border-slate-100 p-2 dark:border-slate-800">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-800 dark:text-slate-200">{cat.name}</span>
                {cat.satisfied ? (
                  <span className="text-xs font-medium text-green-600 dark:text-green-400">Satisfied ✓</span>
                ) : (
                  <span className="text-xs font-medium text-amber-600 dark:text-amber-400">
                    Need {cat.still_needed} more
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Completed: {cat.completed_courses.length > 0 ? cat.completed_courses.join(', ') : 'none yet'}
              </p>
            </div>
          ))}

          {Object.keys(status.ambiguous_courses).length > 0 && (
            <div className="rounded border border-amber-300 bg-amber-50 p-2 text-xs text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-300">
              <p className="mb-1 font-semibold">⚠ Double-check these before assuming they count:</p>
              <ul className="list-inside list-disc">
                {Object.entries(status.ambiguous_courses).map(([code, note]) => (
                  <li key={code}>
                    <span className="font-medium">{code}</span>: {note}
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
