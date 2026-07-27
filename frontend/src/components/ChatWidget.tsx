import { useState, type FormEvent } from 'react'
import { api } from '../lib/api'

interface Turn {
  role: 'user' | 'assistant'
  text: string
}

export default function ChatWidget() {
  const [turns, setTurns] = useState<Turn[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const message = input.trim()
    if (!message || sending) return
    setInput('')
    setTurns((t) => [...t, { role: 'user', text: message }])
    setSending(true)
    try {
      const { reply } = await api.chat(message)
      setTurns((t) => [...t, { role: 'assistant', text: reply }])
    } catch (e) {
      setTurns((t) => [...t, { role: 'assistant', text: `Error: ${e instanceof Error ? e.message : 'failed'}` }])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex h-full flex-col rounded border border-slate-200 p-4 dark:border-slate-700">
      <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">Ask the navigator</h2>
      <div className="mb-3 flex-1 space-y-2 overflow-y-auto">
        {turns.length === 0 && (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Try: "Does COMPSCI 590RM count as a CS elective?"
          </p>
        )}
        {turns.map((t, i) => (
          <div
            key={i}
            className={`rounded px-3 py-2 text-sm ${
              t.role === 'user'
                ? 'ml-8 bg-indigo-600 text-white'
                : 'mr-8 bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200'
            }`}
          >
            {t.text}
          </div>
        ))}
        {sending && <p className="text-sm text-slate-400">Thinking…</p>}
      </div>
      <form onSubmit={onSubmit} className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          className="flex-1 rounded border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800"
        />
        <button
          type="submit"
          disabled={sending}
          className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  )
}
