import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Sparkles, Mail, Lock, User, ArrowRight, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

import { api, post } from '@/lib/api'
import { useAuthStore } from '@/store/auth'
import type { AuthTokens } from '@/types'

export default function RegisterPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const tokens = await post<AuthTokens>('/api/v1/auth/register', { name, email, password })
      localStorage.setItem('clipforge.token', tokens.access_token)
      setAuth(tokens.access_token, tokens.user)
      toast.success('Account created!')
      navigate('/', { replace: true })
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-ink-950 bg-mesh-purple text-ink-100 grid place-items-center p-8">
      <div className="w-full max-w-md card p-8">
        <div className="flex items-center gap-3 mb-8">
          <div className="size-11 rounded-xl bg-gradient-to-br from-brand-500 to-pink-500 grid place-items-center">
            <Sparkles className="size-6 text-white" />
          </div>
          <div>
            <div className="text-lg font-semibold tracking-tight">ClipForge AI</div>
            <div className="text-xs text-ink-400">AI video clipping studio</div>
          </div>
        </div>

        <h1 className="text-2xl font-semibold tracking-tight mb-1">Create your account</h1>
        <p className="text-ink-400 text-sm mb-6">Start clipping in under a minute.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Name</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-ink-500" />
              <input className="input pl-10" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
          </div>
          <div>
            <label className="label">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-ink-500" />
              <input
                type="email"
                required
                className="input pl-10"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="label">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-ink-500" />
              <input
                type="password"
                required
                minLength={8}
                className="input pl-10"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="text-[11px] text-ink-500 mt-1.5">At least 8 characters.</div>
          </div>

          {error && (
            <div className="flex items-start gap-2 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2.5">
              <AlertCircle className="size-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Creating…' : (
              <>
                Create account <ArrowRight className="size-4" />
              </>
            )}
          </button>
        </form>

        <p className="mt-6 text-sm text-ink-400">
          Already have an account?{' '}
          <Link to="/login" className="text-brand-300 hover:text-brand-200">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
