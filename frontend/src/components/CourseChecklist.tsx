import { useEffect, useState } from 'react'
import { useDraggable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import {
  api,
  ApiError,
  type ChecklistCourse,
  type DegreeProgram,
  type Plan,
  type PrereqRef,
  type ProgramChecklist,
} from '../lib/api'

function CreditsTracker({ plan }: { plan: Plan | null }) {
  if (!plan) return null
  const cs = plan.credits_summary
  const completedPct = cs.total_required > 0 ? Math.min(100, (cs.completed_credits / cs.total_required) * 100) : 0
  const scheduledPct = cs.total_required > 0 ? Math.min(100 - completedPct, (cs.scheduled_credits / cs.total_required) * 100) : 0

  return (
    <div className="border-b border-line p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h3 className="text-[13px] font-semibold text-ink">Credits</h3>
        <span className="font-mono text-xs text-ink-soft">
          {cs.completed_credits}&nbsp;earned · {cs.scheduled_credits}&nbsp;on calendar · {cs.remaining_credits}&nbsp;still needed of {cs.total_required}
        </span>
      </div>
      <div className="mt-2.5 flex h-2 w-full overflow-hidden rounded-full bg-line">
        <div className="h-full bg-maroon" style={{ width: `${completedPct}%` }} />
        <div className="h-full bg-gold" style={{ width: `${scheduledPct}%` }} />
      </div>
    </div>
  )
}

function PrereqList({ groups }: { groups: PrereqRef[][] }) {
  if (groups.length === 0) return null
  return (
    <p className="mt-1 pl-6 text-xs text-ink-faint">
      requires{' '}
      {groups.map((group, gi) => (
        <span key={gi}>
          {gi > 0 && <span> or </span>}
          {group.map((p, pi) => (
            <span key={p.code}>
              {pi > 0 && <span> and </span>}
              <span className={p.satisfied ? 'font-semibold text-green-700 dark:text-green-400' : 'font-semibold text-maroon'}>
                {p.code}
              </span>
            </span>
          ))}
        </span>
      ))}
    </p>
  )
}

function DraggableCourseRow({
  course,
  termId,
  children,
}: {
  course: ChecklistCourse
  termId: string | null
  children: React.ReactNode
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `chk:${course.code}`,
    data: { code: course.code, termId, status: course.status },
  })
  const style = transform
    ? { transform: CSS.Translate.toString(transform), zIndex: 20, position: 'relative' as const }
    : undefined

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`border-t border-line px-4 py-2 first:border-t-0 ${isDragging ? 'opacity-50' : ''}`}
    >
      <div className="flex flex-wrap items-center gap-2.5">
        <span
          {...listeners}
          {...attributes}
          className="cursor-grab select-none text-ink-faint active:cursor-grabbing"
          title="Drag onto the calendar"
        >
          ⠿
        </span>
        {children}
      </div>
    </div>
  )
}

export default function CourseChecklist() {
  const [programs, setPrograms] = useState<DegreeProgram[]>([])
  const [selected, setSelected] = useState<string>('')
  const [checklist, setChecklist] = useState<ProgramChecklist | null>(null)
  const [plan, setPlan] = useState<Plan | null>(null)
  const [termIdByCode, setTermIdByCode] = useState<Record<string, string | null>>({})
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState<Set<string>>(new Set())
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [incomingCredits, setIncomingCredits] = useState(0)

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
      setIncomingCredits(pl.settings.incoming_credits)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load checklist')
    }
  }

  useEffect(() => {
    if (selected) reload(selected)
  }, [selected])

  const saveIncomingCredits = async () => {
    if (plan && incomingCredits === plan.settings.incoming_credits) return
    try {
      await api.updatePlanSettings({ incoming_credits: incomingCredits })
      await reload(selected)
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Failed to save incoming credits')
    }
  }

  const toggleExpanded = (categoryId: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(categoryId)) next.delete(categoryId)
      else next.add(categoryId)
      return next
    })
  }

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

  const toggleComplete = (code: string, currentlyCompleted: boolean) => {
    withPending(code, async () => {
      const termId = termIdByCode[code] ?? null
      if (currentlyCompleted) {
        if (termId) {
          await api.upsertPlanCourse({ course_code: code, term_id: termId, status: 'planned' })
        } else {
          await api.removePlanCourse(code)
        }
      } else {
        await api.upsertPlanCourse({ course_code: code, term_id: termId, status: 'completed' })
      }
    })
  }

  // The dropdown covers 5 kinds of selection: not scheduled, skipped (tested
  // out of it, no credit), credit received (AP/IB/transfer), or a real term.
  const setPlacement = (code: string, status: string, value: string) => {
    withPending(code, async () => {
      if (value === 'skip') {
        await api.upsertPlanCourse({ course_code: code, term_id: null, status: 'skipped' })
      } else if (value === 'credit') {
        await api.upsertPlanCourse({ course_code: code, term_id: null, status: 'credited' })
      } else if (value === '') {
        if (status === 'skipped' || status === 'credited') {
          await api.removePlanCourse(code)
        } else if (status !== 'not_started') {
          await api.upsertPlanCourse({ course_code: code, term_id: null, status })
        }
      } else {
        const nextStatus = status === 'not_started' || status === 'skipped' || status === 'credited' ? 'planned' : status
        await api.upsertPlanCourse({ course_code: code, term_id: value, status: nextStatus })
      }
    })
  }

  return (
    <div className="rounded-sm border border-line bg-surface">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3">
        <div className="flex flex-wrap items-baseline gap-3">
          <h2 className="font-display text-[15px] font-bold text-ink">Course checklist</h2>
          <label className="flex items-center gap-1.5 text-xs text-ink-soft">
            Incoming credits (AP/IB)
            <input
              type="number"
              min={0}
              step={1}
              value={incomingCredits}
              onChange={(e) => setIncomingCredits(Number(e.target.value))}
              onBlur={saveIncomingCredits}
              onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
              className="w-16 rounded-sm border border-line-strong bg-surface px-1.5 py-0.5 text-xs text-ink focus:border-maroon focus:outline-none"
            />
          </label>
        </div>
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

      <CreditsTracker plan={plan} />

      {error && <p className="p-4 text-sm text-maroon">{error}</p>}

      {checklist && checklist.categories.map((cat) => {
        const isOpen = expanded.has(cat.category_id)
        return (
          <div key={cat.category_id} className="border-b border-line last:border-b-0">
            <button
              onClick={() => toggleExpanded(cat.category_id)}
              className="flex w-full flex-wrap items-baseline justify-between gap-2 bg-paper px-4 py-2.5 text-left hover:bg-line/30"
            >
              <div className="flex items-baseline gap-2">
                <span className="text-ink-faint">{isOpen ? '▾' : '▸'}</span>
                <span className="text-[13.5px] font-semibold text-ink">{cat.name}</span>
                {cat.description && <span className="text-xs text-ink-faint">{cat.description}</span>}
              </div>
              <span className="font-mono text-xs text-ink-soft">{cat.completed_count} / {cat.total_count}</span>
            </button>
            {isOpen && (
              <div className="flex flex-col">
                {cat.courses.map((course) => {
                  const isCompleted = course.status === 'completed'
                  const isPlanned = course.status === 'planned'
                  const busy = pending.has(course.code)
                  const dropdownValue =
                    course.status === 'skipped' ? 'skip'
                    : course.status === 'credited' ? 'credit'
                    : (termIdByCode[course.code] ?? '')
                  return (
                    <DraggableCourseRow key={course.code} course={course} termId={termIdByCode[course.code] ?? null}>
                      <input
                        type="checkbox"
                        checked={isCompleted}
                        disabled={busy}
                        onChange={() => toggleComplete(course.code, isCompleted)}
                        className="h-4 w-4 accent-maroon disabled:opacity-50"
                      />
                      <span className={`text-sm ${isCompleted ? 'text-ink-faint line-through' : 'text-ink'}`}>
                        <span className="font-mono font-semibold">{course.code}</span> — {course.title}
                      </span>
                      <span className="font-mono text-xs text-ink-faint">{course.credits} cr</span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-semibold whitespace-nowrap ${
                          course.mandatory ? 'bg-line text-ink-soft' : 'bg-gold-soft text-gold'
                        }`}
                      >
                        {course.mandatory ? 'required' : 'choice'}
                      </span>
                      {course.prereq_groups.length > 0 && (
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold whitespace-nowrap ${
                            course.prereqs_met ? 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400' : 'bg-maroon-soft text-maroon'
                          }`}
                        >
                          {course.prereqs_met ? 'prereqs met' : 'prereqs not met'}
                        </span>
                      )}
                      {isPlanned && !isCompleted && (
                        <span className="rounded-full bg-gold-soft px-2 py-0.5 text-[11px] font-semibold text-gold whitespace-nowrap">
                          on calendar
                        </span>
                      )}
                      {course.status === 'skipped' && (
                        <span className="rounded-full bg-line px-2 py-0.5 text-[11px] font-semibold text-ink-soft whitespace-nowrap">
                          skipped
                        </span>
                      )}
                      {course.status === 'credited' && (
                        <span className="rounded-full bg-gold-soft px-2 py-0.5 text-[11px] font-semibold text-gold whitespace-nowrap">
                          credit received
                        </span>
                      )}
                      <select
                        value={dropdownValue}
                        disabled={busy}
                        onChange={(e) => setPlacement(course.code, course.status, e.target.value)}
                        className="ml-auto rounded-sm border border-line-strong bg-surface px-2 py-1 text-xs text-ink disabled:opacity-50"
                      >
                        <option value="">not scheduled</option>
                        <option value="skip">Skipped (no credit)</option>
                        <option value="credit">Credit received (AP/IB/transfer)</option>
                        {(plan?.terms ?? []).map((t) => (
                          <option key={t.id} value={t.id}>{t.label}</option>
                        ))}
                      </select>
                      <div className="basis-full">
                        <PrereqList groups={course.prereq_groups} />
                        {course.ambiguous_note && (
                          <p className="mt-1 pl-6 text-xs text-gold">{course.ambiguous_note}</p>
                        )}
                        {course.satisfies_note && (
                          <p className="mt-1 pl-6 text-xs text-ink-faint">{course.satisfies_note}</p>
                        )}
                      </div>
                    </DraggableCourseRow>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
