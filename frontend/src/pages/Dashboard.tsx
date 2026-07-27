import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import CourseTree from '../components/CourseTree'
import ProgramStatus from '../components/ProgramStatus'
import RecommendationMode from '../components/RecommendationMode'
import ChatWidget from '../components/ChatWidget'

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
    <div className="mx-auto max-w-6xl px-4 py-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">AI Course Compass</h1>
        <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-400">
          <span>{session?.user.email}</span>
          <button onClick={signOut} className="rounded border border-slate-300 px-2 py-1 dark:border-slate-600">
            Log out
          </button>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="flex flex-col gap-4 lg:col-span-2">
          <ProgramStatus key={`status-${refreshKey}`} />
          <CourseTree completed={completed} onToggleComplete={onToggleComplete} />
          <RecommendationMode refreshKey={refreshKey} />
        </div>
        <div className="lg:col-span-1">
          <ChatWidget />
        </div>
      </div>
    </div>
  )
}
