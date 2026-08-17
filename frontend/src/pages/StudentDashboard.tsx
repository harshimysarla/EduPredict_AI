import { useQuery } from "@tanstack/react-query"
import {
  CalendarCheck,
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
} from "lucide-react"
import { api } from "@/lib/api"
import type { StudentSummary, PredictionResult, Intervention, AcademicRecord } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { RiskBadge } from "@/components/shared/RiskBadge"
import { PredictionTrendChart } from "@/components/charts"
import { formatDate, formatNumber, formatPercent, riskColor } from "@/lib/utils"

export default function StudentDashboard() {
  const { data: student, isLoading } = useQuery({
    queryKey: ["student-me"],
    queryFn: () =>
      api.get<
        StudentSummary & {
          full_name: string
          department_name: string | null
          section_name: string | null
        }
      >("/student/me"),
  })

  const { data: predictions } = useQuery({
    queryKey: ["student-me-predictions"],
    queryFn: () => api.get<PredictionResult[]>(`/predictions/students/${student?.id}`),
    enabled: !!student?.id,
  })

  const { data: interventions } = useQuery({
    queryKey: ["student-me-interventions"],
    queryFn: () => api.get<Intervention[]>("/interventions"),
    enabled: !!student,
  })

  const { data: academics } = useQuery({
    queryKey: ["student-me-academics"],
    queryFn: () => api.get<AcademicRecord[]>(`/students/${student?.id}/performance`),
    enabled: !!student?.id,
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

  if (!student) return <EmptyState title="Profile not found" description="Your student profile could not be loaded." />

  const latest = predictions?.[0]
  const trendData = (predictions ?? []).slice().reverse().map((p) => ({ date: p.prediction_date, probability: p.risk_probability }))
  const previous = predictions?.[1]
  const improved = previous ? latest!.risk_probability < previous.risk_probability : null

  const healthLabel =
    student.risk_level === "low" ? "GOOD" : student.risk_level === "moderate" ? "FAIR" : "AT RISK"
  const healthColor = riskColor(student.risk_level)

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Your Academic Health</h1>
        <p className="mt-1 text-sm text-[var(--muted-foreground)]">
          {student.full_name} · {student.student_id} · {student.department_name} · {student.section_name}
        </p>
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
              <RiskBadge level={student.risk_level} />
              <span className="text-sm text-[var(--muted-foreground)]">
                Risk probability: <span className="font-semibold text-[var(--foreground)]">{formatPercent(student.risk_probability, 1)}</span>
              </span>
            </div>
            {improved !== null && (
              <p className="mt-2 flex items-center gap-1.5 text-sm">
                {improved ? (
                  <>
                    <TrendingUp className="h-4 w-4 text-emerald-500" />
                    <span className="text-emerald-500">Your performance has improved compared with the previous assessment.</span>
                  </>
                ) : (
                  <>
                    <TrendingDown className="h-4 w-4 text-red-500" />
                    <span className="text-red-500">Risk has increased compared with the previous assessment — review the recommendations below.</span>
                  </>
                )}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
              <Gauge className="h-3.5 w-3.5 text-[var(--primary)]" /> Overall Performance
            </div>
            <p className="mt-1.5 text-2xl font-bold">{formatNumber(student.average_score)}%</p>
            <Progress value={student.average_score ?? 0} className="mt-2 h-1.5" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
              <CalendarCheck className="h-3.5 w-3.5 text-sky-500" /> Attendance
            </div>
            <p className="mt-1.5 text-2xl font-bold">{formatNumber(student.attendance)}%</p>
            <Progress value={student.attendance ?? 0} className="mt-2 h-1.5" indicatorClassName="bg-sky-500" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
              <Sparkles className="h-3.5 w-3.5 text-violet-500" /> Engagement
            </div>
            <p className="mt-1.5 text-2xl font-bold">{formatNumber(student.engagement)}%</p>
            <Progress value={student.engagement ?? 0} className="mt-2 h-1.5" indicatorClassName="bg-violet-500" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
              <ShieldCheck className="h-3.5 w-3.5" style={{ color: healthColor }} /> Risk Status
            </div>
            <p className="mt-1.5 text-2xl font-bold" style={{ color: healthColor }}>
              {student.risk_level ? student.risk_level.toUpperCase() : "—"}
            </p>
            <p className="mt-1 text-xs text-[var(--muted-foreground)]">
              {latest ? `${latest.model} · ${formatDate(latest.prediction_date)}` : "No prediction yet"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Probability Trend</CardTitle>
          <CardDescription>Your AI predictions over time</CardDescription>
        </CardHeader>
        <CardContent>
          {trendData.length === 0 ? (
            <EmptyState
              icon={ShieldAlert}
              title="No predictions available"
              description="Your faculty runs AI predictions that appear here."
            />
          ) : (
            <PredictionTrendChart data={trendData} />
          )}
        </CardContent>
      </Card>

      {/* Recommendations */}
      {latest && latest.recommendations.length > 0 && (
        <Card className="border-indigo-500/30 bg-indigo-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquareText className="h-4 w-4 text-[var(--primary)]" /> Your Recommendations
            </CardTitle>
            <CardDescription>Personalized actions based on your latest prediction</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {latest.recommendations.map((r, i) => (
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

      {/* Recent academics */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Academic Records</CardTitle>
          <CardDescription>Your latest subject scores</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] text-left text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
                  <th className="px-5 py-3 font-medium">Subject</th>
                  <th className="px-4 py-3 font-medium">Semester</th>
                  <th className="px-4 py-3 font-medium">Internal</th>
                  <th className="px-4 py-3 font-medium">Assignment</th>
                  <th className="px-4 py-3 font-medium">Exam</th>
                  <th className="px-5 py-3 font-medium">Total</th>
                </tr>
              </thead>
              <tbody>
                {(academics ?? []).slice(-8).map((r) => (
                  <tr key={r.id} className="border-b border-[var(--border)] last:border-0">
                    <td className="px-5 py-2.5 font-medium">{r.subject_name}</td>
                    <td className="px-4 py-2.5">{r.semester}</td>
                    <td className="px-4 py-2.5">{formatNumber(r.internal_marks)}</td>
                    <td className="px-4 py-2.5">{formatNumber(r.assignment_score)}</td>
                    <td className="px-4 py-2.5">{formatNumber(r.exam_score)}</td>
                    <td className="px-5 py-2.5 font-semibold">{formatNumber(r.total_score)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

