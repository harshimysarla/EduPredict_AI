import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import {
  CalendarCheck,
  GraduationCap,
  Gauge,
  BookOpen,
  Search,
  TrendingUp,
  AlertTriangle,
  ShieldCheck,
  BookOpenCheck,
  Layers,
  Database,
  ChevronRight,
  Sparkles,
} from "lucide-react"
import { portalService } from "@/services/portalService"
import type { PortalSummary } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { CgpaTrendChart, AttendanceBarsChart } from "@/components/charts"
import { formatNumber } from "@/lib/utils"
import { cn } from "@/lib/utils"

export default function StudentDashboard() {
  const { data: summary, isLoading, isError } = useQuery({
    queryKey: ["portal-summary"],
    queryFn: portalService.summary,
    refetchInterval: 60000,
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-40 w-full" />
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-56" />
          <Skeleton className="h-56" />
          <Skeleton className="h-56" />
        </div>
      </div>
    )
  }

  if (isError || !summary) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Portal data unavailable"
        description="Your academic portal data could not be loaded right now. Please try again."
      />
    )
  }

  return <Dashboard summary={summary} />
}

function Dashboard({ summary }: { summary: PortalSummary }) {
  const hero = summary.hero
  const perf = summary.performance
  const credits = summary.creditProgress

  const piColor = perf.performanceIndex >= 80 ? "#10b981" : perf.performanceIndex >= 65 ? "#6366f1" : perf.performanceIndex >= 50 ? "#f59e0b" : "#ef4444"

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl border border-[var(--border)] bg-gradient-to-r from-indigo-600/10 via-violet-600/10 to-fuchsia-600/5 p-6">
        <div className="absolute -right-20 -top-24 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl" />
        <div className="relative flex flex-wrap items-center gap-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-md">
            <GraduationCap className="h-8 w-8" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight">{hero.name}</h1>
              {summary.placeholder && (
                <Badge variant="warning">DEMO DATA</Badge>
              )}
            </div>
            <p className="mt-1 text-sm text-[var(--muted-foreground)]">
              {hero.rollNumber} · {summary.profile.branch} · Section {hero.section} · {summary.profile.regulation}
            </p>
            <p className="mt-0.5 text-xs text-[var(--muted-foreground)]">
              Current Semester: <span className="font-semibold text-[var(--foreground)]">{hero.currentSemesterLabel}</span>
            </p>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div
                className="flex h-20 w-20 items-center justify-center rounded-full border-4 text-xl font-bold"
                style={{ borderColor: piColor, color: piColor }}
              >
                {perf.performanceIndex}
              </div>
              <p className="mt-1.5 text-[11px] font-semibold uppercase tracking-wide text-[var(--muted-foreground)]">
                Performance Index
              </p>
            </div>
            <div className="hidden gap-8 text-sm sm:flex">
              <div>
                <p className="text-2xl font-bold">{hero.cgpa ?? "—"}</p>
                <p className="text-[11px] text-[var(--muted-foreground)]">CGPA</p>
              </div>
              <div>
                <p className="text-2xl font-bold">{hero.attendance != null ? `${formatNumber(hero.attendance)}%` : "—"}</p>
                <p className="text-[11px] text-[var(--muted-foreground)]">Attendance</p>
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {hero.creditsEarned}<span className="text-base text-[var(--muted-foreground)]">/{hero.programTotalCredits}</span>
                </p>
                <p className="text-[11px] text-[var(--muted-foreground)]">Credits</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Overview metrics */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <MetricCard icon={Gauge} label="Performance Index" value={perf.performanceIndex} suffix="" color="#6366f1" />
        <MetricCard icon={GraduationCap} label="CGPA" value={hero.cgpa ?? 0} suffix="" color="#10b981" scale={10} />
        <MetricCard icon={CalendarCheck} label="Attendance" value={perf.attendanceScore ?? 0} suffix="%" color="#0ea5e9" />
        <MetricCard icon={BookOpenCheck} label="Credit Completion" value={credits.completionPercent} suffix="%" color="#8b5cf6" />
      </div>

      {/* CGPA trend + breakdown */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-[var(--primary)]" /> SGPA &amp; CGPA Trend
            </CardTitle>
            <CardDescription>Semester-wise academic trajectory (* = semester in progress)</CardDescription>
          </CardHeader>
          <CardContent>
            <CgpaTrendChart data={summary.cgpaTrend} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Gauge className="h-4 w-4 text-[var(--primary)]" /> Performance Breakdown
            </CardTitle>
            <CardDescription>Component scores behind the index</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <BreakdownRow label="Academic" value={perf.academicScore} weight={perf.weights.academic} color="#6366f1" />
            <BreakdownRow label="Attendance" value={perf.attendanceScore ?? 0} weight={perf.weights.attendance} color="#0ea5e9" />
            <BreakdownRow label="Internal" value={perf.internalScore ?? 0} weight={perf.weights.internal} color="#f59e0b" />
            <BreakdownRow label="Semester Trend" value={perf.trendScore} weight={perf.weights.trend} color="#ec4899" />
            <BreakdownRow label="Completion" value={perf.creditCompletion} weight={perf.weights.completion} color="#8b5cf6" />
            <p className="text-[11px] text-[var(--muted-foreground)]">
              Weights are configured in one place in the analysis engine and explained under Insights.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Semester performance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-[var(--primary)]" /> Semester Performance
          </CardTitle>
          <CardDescription>SGPA and credits earned per semester</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {summary.semesterPerformance.map((s) => (
              <Link key={s.semester} to={`/student/semesters/${s.semester}`}>
                <div className="group rounded-lg border border-[var(--border)] p-4 transition-colors hover:border-[var(--primary)]/50 hover:bg-[var(--muted)]/40">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold">Semester {s.semester}</p>
                    <ChevronRight className="h-4 w-4 text-[var(--muted-foreground)] transition-transform group-hover:translate-x-0.5" />
                  </div>
                  <div className="mt-3 flex items-end justify-between">
                    <div>
                      <p className="text-2xl font-bold">{s.sgpa ?? "—"}</p>
                      <p className="text-[11px] text-[var(--muted-foreground)]">SGPA</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold">
                        {s.earnedCredits}<span className="text-xs text-[var(--muted-foreground)]">/{s.totalCredits}</span>
                      </p>
                      <p className="text-[11px] text-[var(--muted-foreground)]">Credits earned</p>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Attendance */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarCheck className="h-4 w-4 text-[var(--primary)]" /> Attendance Analysis
            </CardTitle>
            <CardDescription>Current semester · thresholds 85 / 75 / 65</CardDescription>
          </CardHeader>
          <CardContent>
            {summary.attendanceAnalysis.length === 0 ? (
              <EmptyState title="No attendance data" description="Attendance records for the current semester are not available." />
            ) : (
              <AttendanceBarsChart data={summary.attendanceAnalysis} />
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-[var(--primary)]" /> Attendance Status
            </CardTitle>
            <CardDescription>Satisfactory ≥75% · Condonation 65–74% · Shortage &lt;65%</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="max-h-72 overflow-y-auto rounded-lg border border-[var(--border)]">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)] bg-[var(--muted)]/40 text-left text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
                    <th className="px-3 py-2 font-medium">Course</th>
                    <th className="px-3 py-2 font-medium">Attended</th>
                    <th className="px-3 py-2 text-right font-medium">%</th>
                    <th className="px-3 py-2 text-right font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.attendanceAnalysis.map((a) => (
                    <tr key={a.courseCode} className="border-b border-[var(--border)] last:border-0">
                      <td className="px-3 py-2.5">
                        <p className="font-medium leading-tight">{a.courseName}</p>
                        <p className="text-[11px] text-[var(--muted-foreground)]">{a.courseCode}</p>
                      </td>
                      <td className="px-3 py-2.5">
                        {a.attended != null && a.conducted != null ? `${a.attended}/${a.conducted}` : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-right font-semibold">
                        {a.attendancePercentage != null ? `${formatNumber(a.attendancePercentage)}%` : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-right">
                        <AttendanceStatusBadge status={a.status ?? ""} pct={a.attendancePercentage ?? null} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Subjects table */}
      <SubjectTable initialSemester={summary.hero.currentSemester} />

      {/* Strengths / weaknesses / risks */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="border-emerald-500/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="h-4 w-4" /> Strengths
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {summary.strengths.length === 0 && <p className="text-sm text-[var(--muted-foreground)]">No strengths identified yet.</p>}
            {summary.strengths.map((s, i) => (
              <div key={i} className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-emerald-600 dark:text-emerald-400">{s.label}</p>
                <p className="mt-1 text-sm font-medium">{s.courseName}</p>
                <p className="mt-0.5 text-xs text-[var(--muted-foreground)]">{s.detail}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-amber-500/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
              <AlertTriangle className="h-4 w-4" /> Areas Requiring Attention
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {summary.weaknesses.length === 0 && (
              <p className="text-sm text-[var(--muted-foreground)]">No weak areas identified.</p>
            )}
            {summary.weaknesses.map((w, i) => (
              <div key={i} className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-amber-600 dark:text-amber-400">{w.label}</p>
                <p className="mt-1 text-sm font-medium">{w.courseName}</p>
                <p className="mt-0.5 text-xs text-[var(--muted-foreground)]">{w.detail}</p>
              </div>
            ))}
            {summary.risks.length > 0 && (
              <div className="space-y-3 border-t border-[var(--border)] pt-3">
                {summary.risks.map((r, i) => (
                  <div key={i} className="rounded-lg border border-red-500/20 bg-red-500/5 p-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-red-500">{r.category}</p>
                    <p className="mt-1 text-sm font-medium">{r.courseName}</p>
                    <p className="mt-0.5 text-xs text-[var(--muted-foreground)]">{r.detail}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-4 w-4 text-[var(--primary)]" /> Pending Courses
            </CardTitle>
            <CardDescription>Courses required vs registered (program plan)</CardDescription>
          </CardHeader>
          <CardContent>
            {summary.pendingCourses.length === 0 ? (
              <EmptyState title="No pending courses" description="No courses due registered for this student yet." />
            ) : (
              <div className="max-h-72 space-y-3 overflow-y-auto">
                {summary.pendingCourses
                  .filter((c) => c.yetToBeRegistered > 0 || c.requiredCourseCount > 0)
                  .map((c) => (
                    <div key={c.category} className="flex items-center justify-between gap-3 rounded-lg border border-[var(--border)] p-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium capitalize">{c.category.toLowerCase()}</p>
                        <p className="text-[11px] text-[var(--muted-foreground)]">
                          {c.registeredCourseCount} registered · {c.requiredCourseCount} required
                        </p>
                      </div>
                      <Badge variant={c.yetToBeRegistered > 0 ? "warning" : "success"}>
                        {c.yetToBeRegistered} pending
                      </Badge>
                    </div>
                  ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Insights */}
      <Card className="border-indigo-500/30 bg-indigo-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-[var(--primary)]" /> Performance Insights
          </CardTitle>
          <CardDescription>
            Rule-based observations derived from your academic records — transparent and explainable.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {summary.insights.map((ins, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm">
                <span
                  className={cn(
                    "mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold",
                    ins.severity === "positive" && "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
                    ins.severity === "warning" && "bg-amber-500/15 text-amber-600 dark:text-amber-400",
                    ins.severity === "neutral" && "bg-sky-500/15 text-sky-600 dark:text-sky-400",
                  )}
                >
                  {ins.severity === "positive" ? "✓" : ins.severity === "warning" ? "!" : "i"}
                </span>
                <div>
                  <p className="font-medium">{ins.title}</p>
                  <p className="text-[var(--muted-foreground)]">{ins.message}</p>
                </div>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}

function MetricCard({
  icon: Icon,
  label,
  value,
  suffix,
  color,
  scale = 100,
}: {
  icon: typeof Gauge
  label: string
  value: number
  suffix: string
  color: string
  scale?: number
}) {
  const display = scale === 10 ? value.toFixed(2) : formatNumber(value)
  const pct = Math.min(100, Math.max(0, (value / scale) * 100))
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
          <Icon className="h-3.5 w-3.5" style={{ color }} /> {label}
        </div>
        <p className="mt-1.5 text-2xl font-bold">
          {display}
          {suffix}
        </p>
        <Progress value={pct} className="mt-2 h-1.5" indicatorStyle={{ backgroundColor: color }} />
      </CardContent>
    </Card>
  )
}

function BreakdownRow({ label, value, weight, color }: { label: string; value: number; weight: number; color: string }) {
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-[var(--muted-foreground)]">{label}</span>
        <span className="font-semibold">{formatNumber(value)}</span>
      </div>
      <Progress value={value} className="mt-1.5 h-1.5" indicatorStyle={{ backgroundColor: color }} />
      <p className="mt-0.5 text-[10px] text-[var(--muted-foreground)]">weight {(weight * 100).toFixed(0)}%</p>
    </div>
  )
}

function AttendanceStatusBadge({ status, pct }: { status: string; pct: number | null }) {
  const effective = status || (pct == null ? "Not Available" : pct >= 75 ? "Satisfactory" : pct >= 65 ? "Condonation" : "Shortage")
  const variant = effective === "Satisfactory" ? "success" : effective === "Condonation" ? "warning" : "danger"
  return (
    <Badge variant={effective === "Not Available" ? "secondary" : variant} className="capitalize">
      {effective}
    </Badge>
  )
}

function SubjectTable({ initialSemester }: { initialSemester?: number }) {
  const [search, setSearch] = useState("")
  const [semester, setSemester] = useState<string>(initialSemester ? String(initialSemester) : "")
  const [courseType, setCourseType] = useState<string>("")
  const [sortBy, setSortBy] = useState("semester")
  const [order, setOrder] = useState("asc")

  const { data, isLoading } = useQuery({
    queryKey: ["portal-subjects", { search, semester, courseType, sortBy, order }],
    queryFn: () =>
      portalService.subjects({
        search: search || undefined,
        semester: semester ? Number(semester) : undefined,
        courseType: courseType || undefined,
        sortBy,
        order,
      }),
    staleTime: 15_000,
  })

  const subjects = data?.subjects ?? []
  const semesters = useMemo(
    () => Array.from(new Set(subjects.map((s) => s.semester).filter((s): s is number => s != null))).sort((a, b) => a - b),
    [subjects],
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-4 w-4 text-[var(--primary)]" /> Subject Performance
        </CardTitle>
        <CardDescription>All courses across semesters with grades, marks and attendance</CardDescription>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <div className="relative max-w-xs flex-1">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--muted-foreground)]" />
            <Input
              placeholder="Search course name or code…"
              className="pl-8"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select value={semester} onValueChange={setSemester}>
            <SelectTrigger className="w-36">
              <SelectValue placeholder="Semester" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All semesters</SelectItem>
              {semesters.map((s) => (
                <SelectItem key={s} value={String(s)}>Semester {s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={courseType} onValueChange={setCourseType}>
            <SelectTrigger className="w-36">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All types</SelectItem>
              <SelectItem value="T">Theory</SelectItem>
              <SelectItem value="L">Laboratory</SelectItem>
            </SelectContent>
          </Select>
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-36">
              <SelectValue placeholder="Sort" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="semester">Semester</SelectItem>
              <SelectItem value="courseCode">Course code</SelectItem>
              <SelectItem value="courseName">Course name</SelectItem>
              <SelectItem value="grade">Grade</SelectItem>
              <SelectItem value="attendance">Attendance</SelectItem>
              <SelectItem value="credits">Credits</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={() => setOrder((o) => (o === "asc" ? "desc" : "asc"))}>
            {order === "asc" ? "Ascending" : "Descending"}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-48 w-full" />
        ) : subjects.length === 0 ? (
          <EmptyState title="No subjects found" description="Try adjusting your search or filters." />
        ) : (
          <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] bg-[var(--muted)]/40 text-left text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
                  <th className="px-4 py-2.5 font-medium">Semester</th>
                  <th className="px-4 py-2.5 font-medium">Course</th>
                  <th className="px-4 py-2.5 font-medium">Type</th>
                  <th className="px-4 py-2.5 font-medium">Credits</th>
                  <th className="px-4 py-2.5 text-right font-medium">Total</th>
                  <th className="px-4 py-2.5 text-right font-medium">Attendance</th>
                  <th className="px-4 py-2.5 text-right font-medium">Grade</th>
                </tr>
              </thead>
              <tbody>
                {subjects.map((s, i) => (
                  <tr key={`${s.semester}-${s.courseCode ?? ''}-${i}`} className="border-b border-[var(--border)] last:border-0">
                    <td className="px-4 py-2.5">Semester {s.semester ?? '—'}</td>
                    <td className="px-4 py-2.5">
                      <p className="font-medium leading-tight">{s.courseName ?? '—'}</p>
                      <p className="text-[11px] text-[var(--muted-foreground)]">{s.courseCode ?? '—'}</p>
                    </td>
                    <td className="px-4 py-2.5">
                      <Badge variant="secondary">{s.type === "Laboratory" ? "Lab" : "Theory"}</Badge>
                    </td>
                    <td className="px-4 py-2.5">{s.credits ?? 0}</td>
                    <td className="px-4 py-2.5 text-right font-semibold">
                      {s.totalMarks != null ? `${formatNumber(s.totalMarks)}%` : "—"}
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      {s.attendance != null ? (
                        <span className={cn("font-semibold", s.attendance >= 75 ? "text-emerald-500" : "text-red-500")}>
                          {formatNumber(s.attendance)}%
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      {s.grade && s.grade !== "-" ? (
                        <Badge
                          variant={
                            s.gradePoint != null && s.gradePoint >= 9
                              ? "success"
                              : s.gradePoint != null && s.gradePoint >= 8
                                ? "info"
                                : s.gradePoint != null && s.gradePoint >= 7
                                  ? "warning"
                                  : "secondary"
                          }
                        >
                          {s.grade}
                        </Badge>
                      ) : (
                        <Badge variant="secondary">—</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}