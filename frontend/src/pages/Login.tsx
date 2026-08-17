import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { GraduationCap, Lock, Mail, BrainCircuit, ShieldCheck, TrendingUp, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Spinner } from "@/components/ui/spinner"
import { useAuth } from "@/context/AuthContext"
import { toast } from "sonner"

const featureItems = [
  {
    icon: BrainCircuit,
    title: "ML-Based Risk Prediction",
    desc: "Random Forest & Logistic Regression models trained on real academic data.",
  },
  {
    icon: Sparkles,
    title: "Explainable AI",
    desc: "Understand exactly why each student is flagged, factor by factor.",
  },
  {
    icon: ShieldCheck,
    title: "Early Intervention",
    desc: "Detect risk early and track whether interventions improve outcomes.",
  },
]

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const quickFill = (em: string, pw: string) => {
    setEmail(em)
    setPassword(pw)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!email || !password) {
      setError("Please enter your email and password.")
      return
    }
    setLoading(true)
    try {
      const res = await login(email.trim(), password)
      toast.success(`Welcome back, ${res.full_name}!`)
      navigate(res.role === "student" ? "/student" : "/dashboard")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left panel */}
      <div className="relative hidden flex-1 flex-col justify-between overflow-hidden bg-[#0f172a] p-10 text-white lg:flex">
        <div className="absolute -left-32 -top-32 h-96 w-96 rounded-full bg-indigo-600/30 blur-3xl" />
        <div className="absolute -bottom-40 -right-24 h-96 w-96 rounded-full bg-violet-600/25 blur-3xl" />

        <div className="relative flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div>
            <p className="text-lg font-bold">EduPredict AI</p>
            <p className="text-xs text-slate-400">Engineering Design Project · B.Tech</p>
          </div>
        </div>

        <div className="relative space-y-8">
          <div>
            <h1 className="text-4xl font-bold leading-tight">
              AI-Powered Student
              <br />
              Performance Intelligence
            </h1>
            <p className="mt-4 max-w-md text-slate-300">
              Predict academic risk early, understand the contributing factors,
              and intervene before it's too late.
            </p>
          </div>

          <div className="space-y-4">
            {featureItems.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + i * 0.12 }}
                className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/5 p-4 backdrop-blur"
              >
                <f.icon className="mt-0.5 h-5 w-5 text-indigo-300" />
                <div>
                  <p className="text-sm font-semibold">{f.title}</p>
                  <p className="text-xs text-slate-400">{f.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <p className="relative text-xs text-slate-500">
          Attendance + Academics + Engagement → ML → Risk Prediction → Intervention → Improvement
        </p>
      </div>

      {/* Right panel */}
      <div className="flex w-full items-center justify-center bg-[var(--background)] px-6 lg:max-w-xl">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="w-full max-w-sm"
        >
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white">
              <GraduationCap className="h-5 w-5" />
            </div>
            <div>
              <p className="font-bold">EduPredict AI</p>
              <p className="text-xs text-[var(--muted-foreground)]">AI-Powered Student Performance Intelligence</p>
            </div>
          </div>

          <h2 className="text-2xl font-bold">Sign in</h2>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            Access your academic intelligence dashboard
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@institution.edu"
                  className="pl-9"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  className="pl-9"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
              </div>
            </div>

            {error && (
              <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" size="lg" disabled={loading}>
              {loading ? (
                <>
                  <Spinner className="h-4 w-4 text-white" /> Signing in…
                </>
              ) : (
                <>
                  Sign In <TrendingUp className="h-4 w-4" />
                </>
              )}
            </Button>
          </form>

          <div className="mt-8 rounded-xl border border-dashed border-[var(--border)] p-4">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--muted-foreground)]">
              Demo accounts
            </p>
            <div className="space-y-1.5 text-xs">
              <button
                type="button"
                className="flex w-full items-center justify-between rounded-md px-2 py-1.5 hover:bg-[var(--muted)]"
                onClick={() => quickFill("faculty@edupredict.local", "Faculty@123")}
              >
                <span className="font-medium">Faculty</span>
                <span className="text-[var(--muted-foreground)]">faculty@edupredict.local</span>
              </button>
              <button
                type="button"
                className="flex w-full items-center justify-between rounded-md px-2 py-1.5 hover:bg-[var(--muted)]"
                onClick={() => quickFill("admin@edupredict.local", "Admin@123")}
              >
                <span className="font-medium">Admin</span>
                <span className="text-[var(--muted-foreground)]">admin@edupredict.local</span>
              </button>
              <button
                type="button"
                className="flex w-full items-center justify-between rounded-md px-2 py-1.5 hover:bg-[var(--muted)]"
                onClick={() => quickFill("student@edupredict.local", "Student@123")}
              >
                <span className="font-medium">Student</span>
                <span className="text-[var(--muted-foreground)]">student@edupredict.local</span>
              </button>
            </div>
            <p className="mt-2 text-[11px] text-[var(--muted-foreground)]">
              Development-only credentials. Passwords: Faculty@123 · Admin@123 · Student@123
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
