import { useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { useAuth } from '@/lib/auth'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function Login() {
  const { user, loading } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Redirect to home if user is already authenticated
  if (!loading && user) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) return

    setSubmitting(true)
    setError(null)

    try {
      const { error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (signInError) {
        setError(signInError.message)
      } else {
        navigate('/', { replace: true })
      }
    } catch (err: any) {
      setError(err?.message || 'An unexpected error occurred. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-950 text-slate-200">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-700 border-t-white" />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen w-screen items-center justify-center bg-slate-950 px-4 relative overflow-hidden font-sans">
      {/* Subtle architectural background grid and vignette */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b12_1px,transparent_1px),linear-gradient(to_bottom,#1e293b12_1px,transparent_1px)] bg-[size:3.5rem_3.5rem]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(255,255,255,0.06),rgba(2,6,23,0.95))]" />

      {/* Ambient glow around card */}
      <div className="relative z-10 w-full max-w-[420px]">
        <div className="absolute -inset-0.5 rounded-3xl bg-gradient-to-b from-slate-700/30 via-slate-800/10 to-transparent blur-xl opacity-80 -z-10" />

        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/90 p-8 backdrop-blur-2xl shadow-2xl relative overflow-hidden">
          {/* Subtle top edge specular highlight */}
          <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-slate-500/30 to-transparent" />

          {/* Branding & Header */}
          <div className="text-center space-y-3 mb-8">
            <div className="inline-flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-950/80 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-slate-400 shadow-inner">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Driftwood Capital • Analyst Portal</span>
            </div>

            <h1 className="text-2xl font-extrabold tracking-tight text-white sm:text-3xl">
              Document Copilot
            </h1>
            <p className="text-xs text-slate-400 leading-relaxed max-w-[280px] mx-auto">
              Sourced SEC intelligence & instant thesis condensation for senior equities analysts
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="rounded-xl bg-red-950/60 border border-red-800/50 p-3.5 text-xs text-red-300 flex items-center gap-2.5 animate-in fade-in duration-200">
                <span className="h-2 w-2 rounded-full bg-red-500 shrink-0" />
                <span className="leading-relaxed font-medium">{error}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Analyst Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="keerthika@driftwood.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={submitting}
                className="h-11 rounded-xl border border-slate-800 bg-slate-950/70 px-3.5 text-sm text-white placeholder-slate-600 focus-visible:border-slate-500 focus-visible:ring-1 focus-visible:ring-slate-500 transition-all shadow-inner"
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Password
                </Label>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={submitting}
                className="h-11 rounded-xl border border-slate-800 bg-slate-950/70 px-3.5 text-sm text-white placeholder-slate-600 focus-visible:border-slate-500 focus-visible:ring-1 focus-visible:ring-slate-500 transition-all shadow-inner"
              />
            </div>

            <div className="pt-2">
              <Button
                type="submit"
                disabled={submitting || !email || !password}
                className="group w-full h-11 rounded-xl bg-white text-slate-950 font-bold text-sm tracking-wide shadow-[0_0_20px_rgba(255,255,255,0.12)] hover:bg-slate-100 hover:shadow-[0_0_28px_rgba(255,255,255,0.22)] active:scale-[0.99] disabled:bg-slate-800 disabled:text-slate-600 disabled:shadow-none transition-all duration-200 flex items-center justify-center gap-2"
              >
                <span>{submitting ? 'Authenticating...' : 'Sign In to Workspace'}</span>
              </Button>
            </div>
          </form>

          {/* Footer note */}
          <div className="mt-6 border-t border-slate-800/60 pt-4 text-center">
            <p className="text-[11px] text-slate-500 font-medium">
              Internal research platform • Protected by Supabase Auth
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

