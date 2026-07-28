import { useEffect, useState } from 'react'
import { DndContext, DragOverlay, type DragEndEvent, type DragStartEvent } from '@dnd-kit/core'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import CourseTree from '../components/CourseTree'
import RecommendationMode from '../components/RecommendationMode'
import ChatWidget from '../components/ChatWidget'
import CourseChecklist from '../components/CourseChecklist'
import PlanSetup from '../components/PlanSetup'
import SemesterCalendar from '../components/SemesterCalendar'

interface DragCourseData {
  code: string
  termId: string | null
  status: string
  locked: boolean
}

export default function Dashboard() {
  const { session, signOut } = useAuth()
  const [completed, setCompleted] = useState<Set<string>>(new Set())
  const [refreshKey, setRefreshKey] = useState(0)
  const [activeDrag, setActiveDrag] = useState<DragCourseData | null>(null)

  useEffect(() => {
    api.getCompleted().then((codes) => setCompleted(new Set(codes)))
  }, [])

  const onToggleComplete = async (code: string) => {
    const isDone = completed.has(code)
    const next = new Set(completed)
    if (isDone) next.delete(code)
    else next.add(code)
    setCompleted(next)
    try {
      if (isDone) await api.unmarkCompleted(code)
      else await api.markCompleted(code)
      setRefreshKey((k) => k + 1)
    } catch {
      setCompleted(completed) // revert on failure
    }
  }

  const handleDragStart = (event: DragStartEvent) => {
    setActiveDrag((event.active.data.current as DragCourseData | undefined) ?? null)
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    setActiveDrag(null)
    const data = event.active.data.current as DragCourseData | undefined
    const overId = event.over ? String(event.over.id) : null
    if (!data || !overId) return
    if (data.locked) {
      alert('Unlock this course before moving it.')
      return
    }

    let targetTermId: string | null
    if (overId === 'unscheduled') targetTermId = null
    else if (overId.startsWith('term:')) targetTermId = overId.slice('term:'.length)
    else return

    if (targetTermId === data.termId) return

    try {
      const nextStatus = data.status === 'not_started' ? 'planned' : data.status
      await api.upsertPlanCourse({
        course_code: data.code,
        term_id: targetTermId,
        status: nextStatus,
        locked: false,
      })
      setRefreshKey((k) => k + 1)
    } catch (e) {
      if (e instanceof ApiError && typeof e.body === 'object' && e.body && 'message' in (e.body as Record<string, unknown>)) {
        alert((e.body as { message: string }).message)
      } else {
        alert(e instanceof Error ? e.message : 'Could not move that course')
      }
    }
  }

  return (
    <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="min-h-screen bg-paper">
        <div className="flex flex-wrap items-baseline justify-between gap-4 border-b border-line bg-surface px-7 py-4">
          <div className="flex items-baseline gap-2.5">
            <span className="font-display text-xl font-bold text-ink">AI Course Compass</span>
            <span className="border-l border-line-strong pl-2.5 text-[13px] text-ink-soft">BS Computer Science</span>
          </div>
          <div className="flex items-center gap-3 text-sm text-ink-soft">
            <span>{session?.user.email}</span>
            <button
              onClick={signOut}
              className="rounded-sm border border-line-strong px-2 py-1 hover:border-maroon hover:text-maroon"
            >
              Log out
            </button>
          </div>
        </div>

        <div className="mx-auto max-w-6xl px-7 py-6">
          <div className="mb-5">
            <SemesterCalendar key={`calendar-${refreshKey}`} onChanged={() => setRefreshKey((k) => k + 1)} />
          </div>

          <div className="mb-5">
            <CourseChecklist key={`checklist-${refreshKey}`} />
          </div>

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
            <div className="flex flex-col gap-5">
              <PlanSetup onChanged={() => setRefreshKey((k) => k + 1)} />
              <CourseTree completed={completed} onToggleComplete={onToggleComplete} />
              <RecommendationMode refreshKey={refreshKey} />
            </div>
            <div>
              <ChatWidget />
            </div>
          </div>
        </div>
      </div>

      <DragOverlay>
        {activeDrag && (
          <div className="rounded-sm border border-maroon bg-surface px-2 py-1 text-xs shadow-md">
            <span className="font-mono font-semibold text-ink">{activeDrag.code}</span>
          </div>
        )}
      </DragOverlay>
    </DndContext>
  )
}
