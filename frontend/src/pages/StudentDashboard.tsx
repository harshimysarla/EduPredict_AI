import { useQuery } from "@tanstack/react-query"
import {
  CalendarCheck,
  ClipboardCheck,
  Gauge,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  LifeBuoy,
  TrendingUp,
  TrendingDown,
  GraduationCap,
  MessageSquareText,
  BookOpen,
  Database,
  Minus,
} from "lucide-react"
import { api } from "@/lib/api"
import type { AcademicSummary, Intervention } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { RiskBadge } from "@/components/shared/RiskBadge"
import { PredictionTrendChart } from "@/components/charts"
import { formatDate, formatNumber, formatPercent, riskColor } from "@/lib/utils"

export default function StudentDashboard() {
  const { data: summary, isLoading } = useQuery({
    queryKey: ["student-me-summary"],
    queryFn: () => api.get<AcademicSummary>("/student/me/academic-summary"),
    refetchInterval: 60000,
  })

  const { data: interventions } = useQuery({
    queryKey: ["student-me-interventions"],
    queryFn: () => api.get<Intervention[]>("/interventions"),
    enabled: !!summary,
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    )
  }

  if (!summary) return <EmptyState title="Profile not found" description="Your student profile could not be loaded." />

  const profile = summary.profile
  const health = summary.health
  const risk = summary.risk
  const riskLevel = risk.risk_level ?? "low"
  const healthColor = riskColor(riskLevel)
  const healthLabel = riskLevel === "low" ? "GOOD" : riskLevel === "moderate" ? "FAIR" : "AT RISK"

  const trendData = summary.performance_history
    .slice()
    .sort((a, b) => (a.semester ?? 0) - (b.semester ?? 0))
    .map((h) => ({ date: h.label, probability: h.score }))

  const src = summary.data_source
  const sourceLabel =
    src?.type === "CSV"
      ? "Approved Academic Data"
      : src?.type === "SAMVIDHA"
        ? "Samvidha Connected"
        : "Synthetic Demo Data"

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Your Academic Health</h1>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            {profile.full_name} · {profile.student_id} · {profile.department} · {profile.section} · Semester {profile.semester}
          </p>
        </div>
        <Badge
          variant="outline"
          className={
            src?.type === "CSV"
              ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
              : "border-amber-500/40 bg-amber-500/10 text-amber-600 dark:text-amber-400"
          }
        >
          <Database className="mr-1.5 h-3.5 w-3.5" />
          {sourceLabel}
        </Badge>
      </div>

      {/* Health summary */}
      <Card>
        <CardContent
          className="flex flex-wrap items-center gap-5 p-6"
          style={{ background: `linear-gradient(135deg, ${healthColor}12, transparent)` }}
        >
          <div
            className="flex h-20 w-20 items-center justify-center rounded-2xl text-sm font-bold tracking-wider"
            style={{ background: healthColor, color: "#fff" }}
          >
            {healthLabel}
          </div>
          <div className="flex-1">
            <p className="text-lg font-bold">Current risk level</p>
            <div className="mt-1 flex items-center gap-2">
              <RiskBadge level={riskLevel} />
              <span className="text-sm text-[var(--muted-foreground)]">
                Risk probability:{" "}
                <span className="font-semibold text-[var(--foreground)]">
                  {risk.risk_probability != null ? formatPercent(risk.risk_probability, 1) : "—"}
                </span>
                {risk.model_name && (
                  <span className="ml-2 text-xs">· {risk.model_name}</span>
                )}
              </span>
            </div>
            <div className="mt-3 flex max-w-md items-center gap-3 text-[11px] text-[var(--muted-foreground)]">
              <span className="flex-1 text-right">Low</span>
              <div className="relative h-2 flex-1 rounded-full bg-[var(--muted)]">
                <div
                  className="absolute inset-y-0 left-0 rounded-full bg-emerald-500/70"
                  style={{ width: `${Math.min(100, Math.max(0, risk.risk_probability != null ? risk.risk_probability * 100 : 0))}%` }}
                />
              </div>
              <span className="flex-1">High</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Health metrics */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        <MetricCard icon={Gauge} label="Overall Performance" value={health.overall_performance} barClassName="bg-[var(--primary)]" />
        <MetricCard icon={CalendarCheck} label="Attendance" value={health.attendance} barClassName="bg-sky-500" />
        <MetricCard icon={Sparkles} label="Engagement" value={health.engagement} barClassName="bg-violet-500" />
        <MetricCard icon={ClipboardCheck} label="Internal 1" value={health.internal_1} barClassName="bg-indigo-500" />
        <MetricCard icon={ClipboardCheck} label="Internal 2" value={health.internal_2} barClassName="bg-fuchsia-500" />
        <MetricCard icon={ShieldCheck} label="Assignments" value={health.assignment_completion} barClassName="bg-teal-500" />
      </div>

      {/* Subject-wise analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Subject-wise Analysis</CardTitle>
          <CardDescription>Your internal assessments, assignments, and attendance per subject</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          {summary.subjects.map((s) => (
            <div key={s.subject_id} className="rounded-lg border border-[var(--border)] p-4">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold leading-tight">{s.subject_name}</p>
                  <p className="text-[11px] text-[var(--muted-foreground)]">{s.subject_code}</p>
                </div>
                <span
                  className={`flex items-center gap-0.5 text-xs font-semibold ${
                    s.trend === "up" ? "text-emerald-500" : s.trend === "down" ? "text-red-500" : "text-[var(--muted-foreground)]"
                  }`}
                >
                  {s.trend === "up" ? <TrendingUp className="h-3.5 w-3.5" /> : s.trend === "down" ? <TrendingDown className="h-3.5 w-3.5" /> : <Minus className="h-3.5 w-3.5" />}
                  {s.trend}
                </span>
              </div>
              <div className="mt-3 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-[var(--muted-foreground)]">Internal</span>
                  <span className="font-semibold">{formatNumber(s.internal_marks)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[var(--muted-foreground)]">Assignment</span>
                  <span className="font-semibold">{formatNumber(s.assignment_score)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[var(--muted-foreground)]">Attendance</span>
                  <span className="font-semibold">{formatNumber(s.attendance)}%</span>
                </div>
                <div className="flex items-center justify-between border-t border-[var(--border)] pt-2">
                  <span className="text-[var(--muted-foreground)]">Total</span>
                  <span className="flex items-center gap-1.5 text-sm font-bold">
                    {formatNumber(s.total_score)}%
                    <Badge
                      variant={s.grade && ["A", "B"].includes(s.grade) ? "success" : s.grade === "F" ? "destructive" : "warning"}
                      className="text-[10px]"
                    >
                      {s.grade ?? "—"}
                    </Badge>
                  </span>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Performance History</CardTitle>
          <CardDescription>Your scores across internal assessments and subjects</CardDescription>
        </CardHeader>
        <CardContent>
          {trendData.length === 0 ? (
            <EmptyState
              icon={ShieldAlert}
              title="No performance history available"
              description="Your academic records will appear here once they are loaded."
            />
          ) : (
            <PredictionTrendChart data={trendData} />
          )}
        </CardContent>
      </Card>

      {/* Recommendations */}
      {summary.recommendations.length > 0 && (
        <Card className="border-indigo-500/30 bg-indigo-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquareText className="h-4 w-4 text-[var(--primary)]" /> Your Recommendations
            </CardTitle>
            <CardDescription>Personalized actions based on your latest prediction</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {summary.recommendations.map((r, i) => (
                <li key={i} className="flex items-start gap-2.5 text-sm">
                  <span className="mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--primary)]/10 text-[11px] font-bold text-[var(--primary)]">
                    {i + 1}
                  </span>
                  <span className="text-[var(--muted-foreground)]">{r}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Active interventions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LifeBuoy className="h-4 w-4 text-[var(--primary)]" /> Active Interventions
          </CardTitle>
          <CardDescription>Support plans assigned by your faculty</CardDescription>
        </CardHeader>
        <CardContent>
          {!interventions?.length ? (
            <EmptyState
              icon={LifeBuoy}
              title="No active interventions"
              description="You have no assigned intervention plans right now."
            />
          ) : (
            <div className="space-y-3">
              {interventions
                .filter((iv) => iv.status !== "cancelled")
                .map((iv) => (
                  <div key={iv.id} className="rounded-lg border border-[var(--border)] p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <BookOpen className="h-4 w-4 text-[var(--primary)]" />
                        <p className="font-medium">{iv.title}</p>
                        <Badge variant="secondary" className="capitalize">
                          {iv.type.replace(/_/g, " ")}
                        </Badge>
                      </div>
                      <Badge
                        variant={
                          iv.status === "completed" ? "success" : iv.status === "in_progress" ? "info" : "warning"
                        }
                        className="capitalize"
                      >
                        {iv.status.replace(/_/g, " ")}
                      </Badge>
                    </div>
                    {iv.description && (
                      <p className="mt-2 text-sm text-[var(--muted-foreground)]">{iv.description}</p>
                    )}
                    <div className="mt-2 flex flex-wrap gap-4 text-xs text-[var(--muted-foreground)]">
                      <span className="flex items-center gap-1">
                        <GraduationCap className="h-3 w-3" /> {iv.faculty_name}
                      </span>
                      <span>Assigned: {formatDate(iv.assigned_date)}</span>
                      {iv.follow_up_date && <span>Follow-up: {formatDate(iv.follow_up_date)}</span>}
                    </div>
                  </div>
                ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function MetricCard({
  icon: Icon,
  label,
  value,
  barClassName,
}: {
  icon: typeof Gauge
  label: string
  value: number | null | undefined
  barClassName: string
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
          <Icon className={`h-3.5 w-3.5 ${barClassName}`} /> {label}
        </div>
        <p className="mt-1.5 text-2xl font-bold">{value != null ? `${formatNumber(value)}%` : "—"}</p>
        <Progress value={value ?? 0} className="mt-2 h-1.5" indicatorClassName={barClassName} />
      </CardContent>
    </Card>
  )
}