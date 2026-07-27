import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Signup() {
  const { signUp } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    const { error } = await signUp(email, password)
    setSubmitting(false)
    if (error) setError(error)
    else setDone(true)
  }

  if (done) {
    return (
      <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-4 px-4 text-center">
        <h1 className="font-display text-2xl font-bold text-ink">Check your email</h1>
        <p className="text-ink-soft">
          We sent a confirmation link to {email}. Confirm it, then{' '}
          <Link to="/login" className="font-medium text-maroon hover:underline">log in</Link>.
        </p>
      </div>
    )
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-5 px-4">
      <div>
        <p className="font-mono text-xs tracking-wide text-ink-faint uppercase">AI Course Compass</p>
        <h1 className="font-display text-2xl font-bold text-ink">Sign up</h1>
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
          minLength={6}
          placeholder="Password (min 6 characters)"
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
          {submitting ? 'Signing up…' : 'Sign up'}
        </button>
      </form>
      <p className="text-sm text-ink-soft">
        Already have an account? <Link to="/login" className="font-medium text-maroon hover:underline">Log in</Link>
      </p>
    </div>
  )
}
