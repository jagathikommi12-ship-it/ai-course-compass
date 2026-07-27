import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    const { error } = await signIn(email, password)
    setSubmitting(false)
    if (error) setError(error)
    else navigate('/')
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-5 px-4">
      <div>
        <p className="font-mono text-xs tracking-wide text-ink-faint uppercase">AI Course Compass</p>
        <h1 className="font-display text-2xl font-bold text-ink">Log in</h1>
      </div>
      <form onSubmit={onSubmit} className="flex flex-col gap-3">
        <input
          type="email"
          required
          placeholder="you@school.edu"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-sm border border-line-strong bg-surface px-3 py-2 text-ink placeholder:text-ink-faint focus:border-maroon focus:outline-none"
        />
        <input
          type="password"
          required
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="rounded-sm border border-line-strong bg-surface px-3 py-2 text-ink placeholder:text-ink-faint focus:border-maroon focus:outline-none"
        />
        {error && <p className="text-sm text-maroon">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="rounded-sm bg-maroon py-2 font-medium text-[#fdf6f1] hover:bg-maroon-strong disabled:opacity-50"
        >
          {submitting ? 'Logging in…' : 'Log in'}
        </button>
      </form>
      <p className="text-sm text-ink-soft">
        No account? <Link to="/signup" className="font-medium text-maroon hover:underline">Sign up</Link>
      </p>
    </div>
  )
}
