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
    <div className="ml-4 border-l border-line pl-3">
      <div className="flex items-center gap-2 py-1">
        {node.children.length > 0 && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="w-4 text-xs text-ink-faint"
            aria-label={expanded ? 'Collapse' : 'Expand'}
          >
            {expanded ? '▾' : '▸'}
          </button>
        )}
        <input
          type="checkbox"
          checked={isDone}
          onChange={() => onToggleComplete(node.code)}
          className="h-4 w-4 accent-maroon"
        />
        <button
          onClick={() => setExpanded((v) => !v)}
          className={`text-left text-sm ${isDone ? 'text-ink-faint line-through' : 'text-ink'}`}
        >
          <span className="font-mono font-semibold">{node.code}</span> — {node.title}
        </button>
        {!node.satisfied && !isDone && node.missing_options.length > 0 && (
          <span className="text-xs text-maroon">
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
    <div className="rounded-sm border border-line bg-surface">
      <div className="border-b border-line px-4 py-3">
        <h2 className="font-display text-[15px] font-bold text-ink">Prerequisite explorer</h2>
      </div>
      <div className="flex gap-2 px-4 pt-3">
        <input
          value={courseCode}
          onChange={(e) => setCourseCode(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && lookup()}
          placeholder="e.g. COMPSCI 311"
          className="flex-1 rounded-sm border border-line-strong bg-surface px-3 py-1.5 text-sm text-ink placeholder:text-ink-faint focus:border-maroon focus:outline-none"
        />
        <button
          onClick={lookup}
          disabled={loading}
          className="rounded-sm bg-maroon px-3 py-1.5 text-sm font-medium text-[#fdf6f1] hover:bg-maroon-strong disabled:opacity-50"
        >
          {loading ? 'Loading…' : 'Look up'}
        </button>
      </div>
      {error && <p className="px-4 pt-3 text-sm text-maroon">{error}</p>}
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
          {tree.children.map((child) => (
            <TreeNode key={child.code} node={child} onToggleComplete={onToggleComplete} completed={completed} />
          ))}
        </div>
      )}
    </div>
  )
}
