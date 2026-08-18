import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { GraduationCap, Lock, User, Eye, EyeOff, ShieldCheck, TrendingUp, Sparkles, UserRound, KeyRound } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Spinner } from "@/components/ui/spinner"
import { useAuth } from "@/context/AuthContext"
import { toast } from "sonner"

const PORTAL_DEMO_ACCOUNTS = [
  { username: "24951A05B3", name: "Mysarla Harshith", tag: "CSE · Sem V · CGPA 9.22" },
  { username: "24951A05C3", name: "K. Vishnu Vardhan", tag: "CSE · Sem V · CGPA 8.45" },
  { username: "24951A05C5", name: "P. Rithvik Reddy", tag: "CSE · Sem V · CGPA 7.62" },
  { username: "24951A05B8", name: "V. Ananya Sharma", tag: "CSE · Sem V · CGPA 8.92" },
]

const STAFF_ACCOUNTS = [
  { username: "admin", name: "Administrator", tag: "admin" },
  { username: "faculty", name: "Faculty (CSE)", tag: "faculty" },
]

const featureItems = [
  {
    icon: ShieldCheck,
    title: "Performance Index",
    desc: "A single 0–100 score from academics, attendance, internals, trend and credit completion.",
  },
  {
    icon: TrendingUp,
    title: "CGPA & SGPA Trends",
    desc: "Semester-by-semester academic trajectory, exactly like your college portal.",
  },
  {
    icon: Sparkles,
    title: "Actionable Insights",
    desc: "Rule-based strengths, risks and recommendations — no claims of hidden AI models.",
  },
]

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [remember, setRemember] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const quickFill = (user: string, pw: string) => {
    setUsername(user)
    setPassword(pw)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!username || !password) {
      setError("Please enter your roll number (username) and password.")
      return
    }
    setLoading(true)
    try {
      const res = await login(username.trim(), password, remember)
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
            <p className="text-xs text-slate-400">College Academic Performance Analysis Platform</p>
          </div>
        </div>

        <div className="relative space-y-8">
          <div>
            <h1 className="text-4xl font-bold leading-tight">
              Student Academic
              <br />
              Performance Portal
            </h1>
            <p className="mt-4 max-w-md text-slate-300">
              A realistic college academic performance analysis system — the same data
              your Samvidha portal provides (grades, attendance, SGPA, CGPA), analysed
              into clear, actionable intelligence.
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
          Grades · Attendance · Internals → Performance Index → Insights → Improvement
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
              <p className="text-xs text-[var(--muted-foreground)]">Student Academic Performance Portal</p>
            </div>
          </div>

          <h2 className="text-2xl font-bold">Sign in</h2>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            Use your roll number as the username
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Roll number / Username</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
                <Input
                  id="username"
                  type="text"
                  placeholder="e.g. 24951A05B3"
                  className="pl-9"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  className="pl-9 pr-10"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded p-1 text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <label className="flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="h-4 w-4 rounded border-[var(--input)] accent-[var(--primary)]"
              />
              Remember me
            </label>

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
            <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-[var(--muted-foreground)]">
              <KeyRound className="h-3.5 w-3.5" /> Demo mode · Portal accounts
            </p>
            <div className="space-y-1.5 text-xs">
              {PORTAL_DEMO_ACCOUNTS.map((a) => (
                <button
                  key={a.username}
                  type="button"
                  className="flex w-full items-center justify-between gap-2 rounded-md px-2 py-1.5 hover:bg-[var(--muted)]"
                  onClick={() => quickFill(a.username, "demo123")}
                >
                  <span className="flex min-w-0 items-center gap-1.5">
                    <UserRound className="h-3.5 w-3.5 shrink-0 text-[var(--muted-foreground)]" />
                    <span className="truncate font-medium">{a.name}</span>
                  </span>
                  <span className="shrink-0 text-[var(--muted-foreground)]">{a.username}</span>
                </button>
              ))}
            </div>
            <p className="mt-2 text-[11px] text-[var(--muted-foreground)]">
              Portal demo accounts share the password demo123 (development-only).
            </p>
            <div className="mt-3 border-t border-[var(--border)] pt-3">
              <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-[var(--muted-foreground)]">
                Staff accounts
              </p>
              <div className="space-y-1">
                {STAFF_ACCOUNTS.map((a) => (
                  <button
                    key={a.username}
                    type="button"
                    className="flex w-full items-center justify-between rounded-md px-2 py-1.5 hover:bg-[var(--muted)]"
                    onClick={() => quickFill(a.username, a.username === "admin" ? "Admin@123" : "Faculty@123")}
                  >
                    <span className="font-medium">{a.name}</span>
                    <span className="text-[var(--muted-foreground)]">{a.tag}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}