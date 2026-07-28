import { useEffect, useMemo, useState } from 'react'
import { api, type Course, type PrereqNode } from '../lib/api'

export default function CourseTree({
  completed,
  onToggleComplete,
}: {
  completed: Set<string>
  onToggleComplete: (code: string) => void
}) {
  const [allCourses, setAllCourses] = useState<Course[]>([])
  const [query, setQuery] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [tree, setTree] = useState<PrereqNode | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.listCourses().then(setAllCourses).catch(() => {})
  }, [])

  const suggestions = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return []
    return allCourses
      .filter((c) => c.code.toLowerCase().includes(q) || c.title.toLowerCase().includes(q))
      .slice(0, 8)
  }, [query, allCourses])

  const lookup = async (code: string) => {
    setLoading(true)
    setError(null)
    setShowSuggestions(false)
    try {
      setTree(await api.getPrereqTree(code.toUpperCase()))
      setQuery(code)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to look up course')
      setTree(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-sm border border-line bg-surface">
      <div className="border-b border-line px-4 py-3">
        <h2 className="font-display text-[15px] font-bold text-ink">Prerequisite explorer</h2>
      </div>
      <div className="relative px-4 pt-3">
        <input
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setShowSuggestions(true)
          }}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
          onKeyDown={(e) => e.key === 'Enter' && suggestions[0] && lookup(suggestions[0].code)}
          placeholder="Start typing a course code or title…"
          className="w-full rounded-sm border border-line-strong bg-surface px-3 py-1.5 text-sm text-ink placeholder:text-ink-faint focus:border-maroon focus:outline-none"
        />
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute inset-x-4 z-10 mt-1 max-h-64 overflow-y-auto rounded-sm border border-line-strong bg-surface shadow-md">
            {suggestions.map((c) => (
              <button
                key={c.code}
                onMouseDown={() => lookup(c.code)}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm hover:bg-paper"
              >
                <span className="font-mono font-semibold text-ink">{c.code}</span>
                <span className="text-ink-soft">{c.title}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {error && <p className="px-4 pt-3 text-sm text-maroon">{error}</p>}
      {loading && <p className="px-4 pt-3 text-sm text-ink-faint">Loading…</p>}

      {tree && (
        <div className="p-4">
          <div className="flex items-center gap-2 py-1">
            <input
              type="checkbox"
              checked={completed.has(tree.code)}
              onChange={() => onToggleComplete(tree.code)}
              className="h-4 w-4 accent-maroon"
            />
            <span className="text-ink">
              <span className="font-mono font-semibold">{tree.code}</span> — {tree.title}
            </span>
            {tree.satisfied ? (
              <span className="rounded-full bg-gold-soft px-2 py-0.5 text-[11px] font-semibold text-gold">met</span>
            ) : (
              <span className="rounded-full bg-maroon-soft px-2 py-0.5 text-[11px] font-semibold text-maroon">not yet met</span>
            )}
          </div>
          {tree.children.length === 0 ? (
            <p className="pl-6 text-xs text-ink-faint">No prerequisites.</p>
          ) : (
            <div className="flex flex-col gap-1 pl-6">
              {tree.children.map((child) => (
                <div key={child.code} className="flex items-center gap-2 text-sm">
                  <span
                    className={`font-mono font-semibold ${
                      child.satisfied ? 'text-green-700 dark:text-green-400' : 'text-maroon'
                    }`}
                  >
                    {child.code}
                  </span>
                  <span className="text-ink-soft">{child.title}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
