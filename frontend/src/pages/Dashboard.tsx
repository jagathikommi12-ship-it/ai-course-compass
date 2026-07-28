import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import CourseTree from '../components/CourseTree'
import ProgramStatus from '../components/ProgramStatus'
import RecommendationMode from '../components/RecommendationMode'
import ChatWidget from '../components/ChatWidget'
import ChecklistPanel from '../components/ChecklistPanel'

export default function Dashboard() {
  const { session, signOut } = useAuth()
  const [completed, setCompleted] = useState<Set<string>>(new Set())
  const [refreshKey, setRefreshKey] = useState(0)

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

  return (
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

      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-5 px-7 py-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="flex flex-col gap-5">
          <ChecklistPanel key={`checklist-${refreshKey}`} />
          <ProgramStatus key={`status-${refreshKey}`} />
          <CourseTree completed={completed} onToggleComplete={onToggleComplete} />
          <RecommendationMode refreshKey={refreshKey} />
        </div>
        <div>
          <ChatWidget />
        </div>
      </div>
    </div>
  )
}
