import { useEffect, useState } from 'react'
import { useDraggable, useDroppable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { api, type Plan, type PlannedCourse } from '../lib/api'

function CourseChip({ course }: { course: PlannedCourse }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `cal:${course.course_code}`,
    data: { code: course.course_code, termId: course.term_id, status: course.status },
  })
  const style = transform ? { transform: CSS.Translate.toString(transform), zIndex: 20 } : undefined

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-1.5 rounded-sm border border-line-strong bg-surface px-2 py-1 text-xs text-ink ${
        isDragging ? 'opacity-50' : ''
      } ${course.status === 'completed' ? 'line-through opacity-70' : ''}`}
    >
      <span {...listeners} {...attributes} className="cursor-grab select-none active:cursor-grabbing">
        ⠿
      </span>
      <span className="font-mono font-semibold">{course.course_code}</span>
      <span className="text-ink-faint">{course.credits}cr</span>
    </div>
  )
}

function TermColumn({ term, courses }: { term: Plan['terms'][number]; courses: PlannedCourse[] }) {
  const { setNodeRef, isOver } = useDroppable({ id: `term:${term.id}` })
  const isExtra = term.term_type === 'summer' || term.term_type === 'winter'
  const credits = courses.reduce((sum, c) => sum + c.credits, 0)

  return (
    <div
      ref={setNodeRef}
      className={`flex w-56 shrink-0 flex-col rounded-sm border ${
        isOver ? 'border-maroon bg-maroon-soft/40' : 'border-line'
      } ${isExtra ? 'bg-paper' : 'bg-surface'}`}
    >
      <div className="border-b border-line px-3 py-2">
        <p className="text-[13px] font-semibold text-ink">{term.label}</p>
        <p className="font-mono text-[11px] text-ink-faint">{credits} credits{isExtra ? ' · extra' : ''}</p>
      </div>
      <div className="flex min-h-[64px] flex-col gap-1.5 p-2">
        {courses.map((c) => (
          <CourseChip key={c.course_code} course={c} />
        ))}
      </div>
    </div>
  )
}

function UnscheduledBucket({ courses }: { courses: PlannedCourse[] }) {
  const { setNodeRef, isOver } = useDroppable({ id: 'unscheduled' })
  return (
    <div
      ref={setNodeRef}
      className={`flex w-56 shrink-0 flex-col rounded-sm border border-dashed ${
        isOver ? 'border-maroon bg-maroon-soft/40' : 'border-line-strong'
      }`}
    >
      <div className="border-b border-line-strong px-3 py-2">
        <p className="text-[13px] font-semibold text-ink-soft">Unscheduled</p>
        <p className="text-[11px] text-ink-faint">drag here to remove from a term</p>
      </div>
      <div className="flex min-h-[64px] flex-col gap-1.5 p-2">
        {courses.map((c) => (
          <CourseChip key={c.course_code} course={c} />
        ))}
      </div>
    </div>
  )
}

export default function SemesterCalendar() {
  const [plan, setPlan] = useState<Plan | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getPlan().then(setPlan).catch((e) => setError(e instanceof Error ? e.message : 'Failed to load plan'))
  }, [])

  if (error) {
    return <div className="rounded-sm border border-line bg-surface p-4 text-sm text-maroon">{error}</div>
  }

  if (!plan || !plan.settings) {
    return (
      <div className="rounded-sm border border-line bg-surface p-4 text-sm text-ink-soft">
        Set up your plan below to see your semester calendar.
      </div>
    )
  }

  const coursesByTerm: Record<string, PlannedCourse[]> = {}
  const unscheduled: PlannedCourse[] = []
  for (const pc of plan.planned_courses) {
    if (pc.term_id) {
      ;(coursesByTerm[pc.term_id] ??= []).push(pc)
    } else if (pc.status !== 'skipped' && pc.status !== 'credited') {
      // Skipped/credited courses are never on the calendar at all — not even the backlog.
      unscheduled.push(pc)
    }
  }

  return (
    <div className="rounded-sm border border-line bg-surface">
      <div className="border-b border-line px-4 py-3">
        <h2 className="font-display text-[15px] font-bold text-ink">Semester calendar</h2>
      </div>
      <div className="flex gap-3 overflow-x-auto p-4">
        {plan.terms.map((term) => (
          <TermColumn key={term.id} term={term} courses={coursesByTerm[term.id] ?? []} />
        ))}
        <UnscheduledBucket courses={unscheduled} />
      </div>
    </div>
  )
}
