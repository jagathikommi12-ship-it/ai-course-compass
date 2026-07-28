import { useEffect, useState } from 'react'
import { useDraggable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { api, ApiError, type DegreeProgram, type Plan, type ProgramChecklist } from '../lib/api'

function CreditsTracker({ plan }: { plan: Plan | null }) {
  if (!plan) return null
  const cs = plan.credits_summary
  const lockedPct = cs.total_required > 0 ? Math.min(100, (cs.locked_credits / cs.total_required) * 100) : 0
  const scheduledPct = cs.total_required > 0 ? Math.min(100 - lockedPct, (cs.scheduled_credits / cs.total_required) * 100) : 0

  return (
    <div className="rounded-sm border border-line bg-surface p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="font-display text-[15px] font-bold text-ink">Credits</h2>
        <span className="font-mono text-xs text-ink-soft">
          {cs.locked_credits}&nbsp;locked · {cs.scheduled_credits}&nbsp;on calendar · {cs.remaining_credits}&nbsp;still needed of {cs.total_required}
        </span>
      </div>
      <div className="mt-2.5 flex h-2 w-full overflow-hidden rounded-full bg-line">
        <div className="h-full bg-maroon" style={{ width: `${lockedPct}%` }} />
        <div className="h-full bg-gold" style={{ width: `${scheduledPct}%` }} />
      </div>
      <div className="mt-1.5 flex gap-4 text-[11px] text-ink-faint">
        <span><span className="inline-block h-2 w-2 rounded-full bg-maroon" /> locked</span>
        <span><span className="inline-block h-2 w-2 rounded-full bg-gold" /> scheduled, not locked</span>
      </div>
    </div>
  )
}

function DraggableCourseRow({
  code,
  termId,
  status,
  locked,
  children,
}: {
  code: string
  termId: string | null
  status: string
  locked: boolean
  children: React.ReactNode
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `chk:${code}`,
    data: { code, termId, status, locked },
    disabled: locked,
  })
  const style = transform
    ? { transform: CSS.Translate.toString(transform), zIndex: 20, position: 'relative' as const }
    : undefined

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex flex-wrap items-center gap-2.5 border-t border-line px-4 py-2 first:border-t-0 ${isDragging ? 'opacity-50' : ''}`}
    >
      <span
        {...(locked ? {} : listeners)}
        {...attributes}
        className={`select-none text-ink-faint ${locked ? 'opacity-30' : 'cursor-grab active:cursor-grabbing'}`}
        title={locked ? 'Unlock to drag' : 'Drag onto the calendar'}
      >
        ⠿
      </span>
      {children}
    </div>
  )
}

export default function ChecklistPanel() {
  const [programs, setPrograms] = useState<DegreeProgram[]>([])
  const [selected, setSelected] = useState<string>('')
  const [checklist, setChecklist] = useState<ProgramChecklist | null>(null)
  const [plan, setPlan] = useState<Plan | null>(null)
  const [termIdByCode, setTermIdByCode] = useState<Record<string, string | null>>({})
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState<Set<string>>(new Set())

  useEffect(() => {
    api.listPrograms().then((ps) => {
      setPrograms(ps)
      if (ps.length > 0) setSelected(ps[0].id)
    }).catch((e) => setError(e instanceof Error ? e.message : 'Failed to load programs'))
  }, [])

  const reload = async (programId: string) => {
    try {
      const [cl, pl] = await Promise.all([api.getProgramChecklist(programId), api.getPlan(programId)])
      setChecklist(cl)
      setPlan(pl)
      const map: Record<string, string | null> = {}
      for (const pc of pl.planned_courses) map[pc.course_code] = pc.term_id
      setTermIdByCode(map)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load checklist')
    }
  }

  useEffect(() => {
    if (selected) reload(selected)
  }, [selected])

  const withPending = async (code: string, fn: () => Promise<void>) => {
    setPending((p) => new Set(p).add(code))
    try {
      await fn()
      await reload(selected)
    } catch (e) {
      if (e instanceof ApiError && typeof e.body === 'object' && e.body && 'message' in (e.body as Record<string, unknown>)) {
        alert((e.body as { message: string }).message)
      } else {
        alert(e instanceof Error ? e.message : 'Something went wrong')
      }
    } finally {
      setPending((p) => {
        const next = new Set(p)
        next.delete(code)
        return next
      })
    }
  }

  const toggleComplete = (code: string, currentlyCompleted: boolean, locked: boolean) => {
    if (currentlyCompleted && locked) {
      alert('Unlock this course before unchecking it.')
      return
    }
    withPending(code, async () => {
      const termId = termIdByCode[code] ?? null
      if (currentlyCompleted) {
        if (termId) {
          await api.upsertPlanCourse({ course_code: code, term_id: termId, status: 'planned', locked: false })
        } else {
          await api.removePlanCourse(code)
        }
      } else {
        await api.upsertPlanCourse({ course_code: code, term_id: termId, status: 'completed', locked })
      }
    })
  }

  const toggleLock = (code: string, status: string, locked: boolean) => {
    withPending(code, async () => {
      const termId = termIdByCode[code] ?? null
      const nextStatus = status === 'not_started' ? 'planned' : status
      await api.upsertPlanCourse({ course_code: code, term_id: termId, status: nextStatus, locked: !locked })
    })
  }

  return (
    <div className="flex flex-col gap-5">
      <CreditsTracker plan={plan} />

      <div className="rounded-sm border border-line bg-surface">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3">
          <h2 className="font-display text-[15px] font-bold text-ink">Course checklist</h2>
          <div className="flex items-center gap-3">
            {checklist && (
              <span className="rounded-full bg-gold-soft px-2 py-0.5 text-[11px] font-semibold text-gold whitespace-nowrap">
                {checklist.total_completed} / {checklist.total_courses} done
              </span>
            )}
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
        </div>

        {error && <p className="p-4 text-sm text-maroon">{error}</p>}

        {checklist && checklist.categories.map((cat) => (
          <div key={cat.category_id} className="border-b border-line last:border-b-0">
            <div className="flex flex-wrap items-baseline justify-between gap-2 bg-paper px-4 py-2">
              <div>
                <span className="text-[13.5px] font-semibold text-ink">{cat.name}</span>
                {cat.description && <span className="ml-2 text-xs text-ink-faint">{cat.description}</span>}
              </div>
              <span className="font-mono text-xs text-ink-soft">{cat.completed_count} / {cat.total_count}</span>
            </div>
            <div className="flex flex-col">
              {cat.courses.map((course) => {
                const isCompleted = course.status === 'completed'
                const isPlanned = course.status === 'planned'
                const busy = pending.has(course.code)
                return (
                  <DraggableCourseRow
                    key={course.code}
                    code={course.code}
                    termId={termIdByCode[course.code] ?? null}
                    status={course.status}
                    locked={course.locked}
                  >
                    <input
                      type="checkbox"
                      checked={isCompleted}
                      disabled={busy}
                      onChange={() => toggleComplete(course.code, isCompleted, course.locked)}
                      className="h-4 w-4 accent-maroon disabled:opacity-50"
                    />
                    <span className={`text-sm ${isCompleted ? 'text-ink-faint line-through' : 'text-ink'}`}>
                      <span className="font-mono font-semibold">{course.code}</span> — {course.title}
                    </span>
                    <span className="font-mono text-xs text-ink-faint">{course.credits} cr</span>
                    {course.satisfies_note && (
                      <span className="text-xs text-ink-faint">{course.satisfies_note}</span>
                    )}
                    {isPlanned && !isCompleted && (
                      <span className="rounded-full bg-gold-soft px-2 py-0.5 text-[11px] font-semibold text-gold whitespace-nowrap">
                        on calendar
                      </span>
                    )}
                    <button
                      onClick={() => toggleLock(course.code, course.status, course.locked)}
                      disabled={busy}
                      className={`ml-auto rounded-full px-2 py-0.5 text-[11px] font-semibold whitespace-nowrap disabled:opacity-50 ${
                        course.locked
                          ? 'bg-maroon-soft text-maroon'
                          : 'border border-line-strong text-ink-soft hover:border-maroon hover:text-maroon'
                      }`}
                    >
                      {course.locked ? 'locked' : 'lock'}
                    </button>
                  </DraggableCourseRow>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
