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
    <div className="flex h-full flex-col rounded-sm border border-line bg-surface">
      <div className="border-b border-line px-4 py-3">
        <h2 className="font-display text-[15px] font-bold text-ink">Ask the navigator</h2>
      </div>
      <div className="flex-1 space-y-2.5 overflow-y-auto p-4">
        {turns.length === 0 && (
          <p className="text-sm text-ink-faint">
            Try: "Does COMPSCI 590RM count as a CS elective?"
          </p>
        )}
        {turns.map((t, i) => (
          <div
            key={i}
            className={`max-w-[92%] rounded-sm px-3 py-2 text-sm ${
              t.role === 'user'
                ? 'ml-auto bg-maroon text-[#fdf6f1]'
                : 'border border-line bg-paper text-ink'
            }`}
          >
            {t.text}
          </div>
        ))}
        {sending && <p className="text-sm text-ink-faint">Thinking…</p>}
      </div>
      <form onSubmit={onSubmit} className="flex gap-2 border-t border-line p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          className="flex-1 rounded-sm border border-line-strong bg-surface px-3 py-1.5 text-sm text-ink placeholder:text-ink-faint focus:border-maroon focus:outline-none"
        />
        <button
          type="submit"
          disabled={sending}
          className="rounded-sm bg-maroon px-3 py-1.5 text-sm font-medium text-[#fdf6f1] hover:bg-maroon-strong disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  )
}
