import { useState } from 'react'
import { api, type PrereqNode } from '../lib/api'

function TreeNode({
  node,
  onToggleComplete,
  completed,
}: {
  node: PrereqNode
  onToggleComplete: (code: string) => void
  completed: Set<string>
}) {
  const [expanded, setExpanded] = useState(false)
  const isDone = completed.has(node.code)

  return (
    <div className="ml-4 border-l border-slate-200 pl-3 dark:border-slate-700">
      <div className="flex items-center gap-2 py-1">
        {node.children.length > 0 && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="w-4 text-xs text-slate-500 dark:text-slate-400"
            aria-label={expanded ? 'Collapse' : 'Expand'}
          >
            {expanded ? '▾' : '▸'}
          </button>
        )}
        <input
          type="checkbox"
          checked={isDone}
          onChange={() => onToggleComplete(node.code)}
          className="h-4 w-4"
        />
        <button
          onClick={() => setExpanded((v) => !v)}
          className={`text-left text-sm ${isDone ? 'text-slate-400 line-through' : 'text-slate-800 dark:text-slate-200'}`}
        >
          <span className="font-medium">{node.code}</span> — {node.title}
        </button>
        {!node.satisfied && !isDone && node.missing_options.length > 0 && (
          <span className="text-xs text-amber-600 dark:text-amber-400">
            needs {node.missing_options.map((g) => g.join(' + ')).join(' OR ')}
          </span>
        )}
      </div>
      {expanded && node.children.map((child) => (
        <TreeNode key={child.code} node={child} onToggleComplete={onToggleComplete} completed={completed} />
      ))}
    </div>
  )
}

export default function CourseTree({
  completed,
  onToggleComplete,
}: {
  completed: Set<string>
  onToggleComplete: (code: string) => void
}) {
  const [courseCode, setCourseCode] = useState('')
  const [tree, setTree] = useState<PrereqNode | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const lookup = async () => {
    if (!courseCode.trim()) return
    setLoading(true)
    setError(null)
    try {
      setTree(await api.getPrereqTree(courseCode.trim().toUpperCase()))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to look up course')
      setTree(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded border border-slate-200 p-4 dark:border-slate-700">
      <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
        Course prerequisite explorer
      </h2>
      <div className="mb-3 flex gap-2">
        <input
          value={courseCode}
          onChange={(e) => setCourseCode(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && lookup()}
          placeholder="e.g. CS 311"
          className="flex-1 rounded border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800"
        />
        <button
          onClick={lookup}
          disabled={loading}
          className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? 'Loading…' : 'Look up'}
        </button>
      </div>
      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      {tree && (
        <div>
          <div className="flex items-center gap-2 py-1">
            <input
              type="checkbox"
              checked={completed.has(tree.code)}
              onChange={() => onToggleComplete(tree.code)}
              className="h-4 w-4"
            />
            <span className="font-medium text-slate-900 dark:text-slate-100">
              {tree.code} — {tree.title}
            </span>
            {tree.satisfied ? (
              <span className="text-xs font-medium text-green-600 dark:text-green-400">Prereqs met ✓</span>
            ) : (
              <span className="text-xs font-medium text-amber-600 dark:text-amber-400">Prereqs not yet met</span>
            )}
          </div>
          {tree.children.map((child) => (
            <TreeNode key={child.code} node={child} onToggleComplete={onToggleComplete} completed={completed} />
          ))}
        </div>
      )}
    </div>
  )
}
