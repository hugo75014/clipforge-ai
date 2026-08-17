import { useState } from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Sparkles, Mail, Lock, ArrowRight, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

import { api, post } from '@/lib/api'
import { useAuthStore } from '@/store/auth'
import type { AuthTokens } from '@/types'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [email, setEmail] = useState('admin@clipforge.local')
  const [password, setPassword] = useState('admin_change_me')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const tokens = await post<AuthTokens>('/api/v1/auth/login', { email, password })
      localStorage.setItem('clipforge.token', tokens.access_token)
      setAuth(tokens.access_token, tokens.user)
      toast.success(`Welcome back, ${tokens.user.name || tokens.user.email}!`)
      const from = (location.state as any)?.from || '/'
      navigate(from, { replace: true })
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-ink-950 bg-mesh-purple text-ink-100 grid lg:grid-cols-2">
      {/* Left: form */}
      <div className="flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-md"
        >
          <div className="flex items-center gap-3 mb-10">
            <div className="size-11 rounded-xl bg-gradient-to-br from-brand-500 to-pink-500 grid place-items-center shadow-glow">
              <Sparkles className="size-6 text-white" />
            </div>
            <div>
              <div className="text-lg font-semibold tracking-tight">ClipForge AI</div>
              <div className="text-xs text-ink-400">AI video clipping studio</div>
            </div>
          </div>

          <h1 className="text-3xl font-semibold tracking-tight mb-2">Welcome back</h1>
          <p className="text-ink-400 mb-8">Sign in to your creator account.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-ink-500" />
                <input
                  type="email"
                  autoComplete="email"
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
                  autoComplete="current-password"
                  required
                  className="input pl-10"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            {error && (
              <div className="flex items-start gap-2 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2.5">
                <AlertCircle className="size-4 mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? 'Signing in…' : (
                <>
                  Sign in <ArrowRight className="size-4" />
                </>
              )}
            </button>
          </form>

          <p className="mt-6 text-sm text-ink-400">
            New to ClipForge?{' '}
            <Link to="/register" className="text-brand-300 hover:text-brand-200">
              Create an account
            </Link>
          </p>

          <div className="mt-8 text-xs text-ink-500 leading-relaxed">
            <div>Default admin: <code>admin@clipforge.local</code> / <code>admin_change_me</code></div>
            <div className="opacity-70 mt-1">Change these in your <code>.env</code> before going to production.</div>
          </div>
        </motion.div>
      </div>

      {/* Right: showcase */}
      <div className="hidden lg:flex items-center justify-center p-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-grid opacity-30" />
        <div className="absolute -top-40 -right-40 size-[500px] rounded-full bg-brand-500/20 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 size-[500px] rounded-full bg-pink-500/20 blur-3xl" />

        <div className="relative max-w-md text-center space-y-6">
          <div className="inline-flex chip-purple">AI-powered</div>
          <h2 className="text-4xl font-semibold tracking-tight leading-tight">
            From long video to <span className="gradient-text">viral Shorts</span> in minutes.
          </h2>
          <p className="text-ink-300 leading-relaxed">
            ClipForge AI detects the best moments, crops to vertical, adds dynamic captions, and
            exports ready-to-publish clips — for TikTok, Reels, Shorts.
          </p>
          <div className="grid grid-cols-3 gap-3 pt-6">
            {[
              { k: '4 min', v: 'avg. clip time' },
              { k: '9:16', v: 'smart crop' },
              { k: '92/100', v: 'viral score' },
            ].map((s) => (
              <div key={s.v} className="card p-4 text-left">
                <div className="text-2xl font-semibold tracking-tight gradient-text">{s.k}</div>
                <div className="text-xs text-ink-400 mt-1">{s.v}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
