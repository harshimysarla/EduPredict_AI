import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  ArrowLeft,
  BrainCircuit,
  CalendarCheck,
  CheckCircle2,
  FileDown,
  Gauge,
  GraduationCap,
  LifeBuoy,
  Sparkles,
  TrendingUp,
  AlertTriangle,
  BookOpen,
  MessageSquareText,
  Plus,
  UserRound,
} from "lucide-react"
import { toast } from "sonner"
import { api } from "@/lib/api"
import type {
  StudentSummary,
  AcademicRecord,
  AttendanceRecord,
  EngagementRecord,
  PredictionResult,
  Intervention,
  InterventionImpact,
  PredictionWithWarning,
} from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { RiskBadge } from "@/components/shared/RiskBadge"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { EmptyState } from "@/components/ui/empty-state"
import { Spinner } from "@/components/ui/spinner"
import { BeforeAfterChart, PredictionTrendChart } from "@/components/charts"
import { formatDate, formatDateTime, formatNumber, formatPercent, riskColor } from "@/lib/utils"

function HealthMetric({
  label,
  value,
  icon: Icon,
  color,
  suffix = "%",
}: {
  label: string
  value: number | null | undefined
  icon: React.ElementType
  color: string
  suffix?: string
}) {
  const v = value ?? 0
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg" style={{ background: `${color}18`, color }}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline justify-between gap-2">
            <p className="text-xs font-medium text-[var(--muted-foreground)]">{label}</p>
            <p className="text-lg font-bold">{value === null || value === undefined ? "—" : `${value.toFixed(1)}${suffix}`}</p>
          </div>
          <Progress
            value={v}
            className="mt-1.5 h-1.5"
            indicatorClassName={color === "#ef4444" ? "bg-red-500" : undefined}
          />
        </div>
      </CardContent>
    </Card>
  )
}

function ImpactBadge({ label, before, after, suffix = "%" }: { label: string; before: number | null; after: number | null; suffix?: string }) {
  const improved = after !== null && before !== null && after > before
  const declined = after !== null && before !== null && after < before
  return (
    <div className="flex items-center justify-between rounded-lg border border-[var(--border)] px-3 py-2.5 text-sm">
      <span className="text-[var(--muted-foreground)]">{label}</span>
      <span className="flex items-center gap-2 font-medium">
        {before !== null ? before.toFixed(1) : "—"}
        <span className="text-[var(--muted-foreground)]">→</span>
        {after !== null ? after.toFixed(1) : "—"}
        {suffix}
        {improved && <TrendingUp className="h-4 w-4 text-emerald-500" />}
        {declined && <AlertTriangle className="h-4 w-4 text-red-500" />}
      </span>
    </div>
  )
}

const impactConfig: Record<string, string> = {
  high: "High Impact",
  medium: "Medium Impact",
  low: "Low Impact",
}

export default function StudentProfile() {
  const { id } = useParams<{ id: string }>()
  const studentId = Number(id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [predictionOpen, setPredictionOpen] = useState(false)
    const [predictionResult, setPredictionResult] = useState<PredictionWithWarning | null>(null)
  const [predictionError, setPredictionError] = useState<string | null>(null)

  const [predInputs, setPredInputs] = useState({
    attendance: "",
    previous_performance: "",
    internal_marks: "",
    assignment_score: "",
    engagement: "",
    study_hours: "",
  })

  const [ivOpen, setIvOpen] = useState(false)
  const [ivType, setIvType] = useState("mentor_meeting")
  const [ivTitle, setIvTitle] = useState("")
  const [ivDesc, setIvDesc] = useState("")
  const [ivFollowUp, setIvFollowUp] = useState("")

  const { data: student, isLoading, error } = useQuery({
    queryKey: ["student", studentId],
    queryFn: () => api.get<StudentSummary>(`/students/${studentId}`),
    enabled: !Number.isNaN(studentId),
  })

  const { data: academics } = useQuery({
    queryKey: ["student-academics", studentId],
    queryFn: () => api.get<AcademicRecord[]>(`/students/${studentId}/performance`),
    enabled: !Number.isNaN(studentId),
  })
  const { data: attendance } = useQuery({
    queryKey: ["student-attendance", studentId],
    queryFn: () => api.get<AttendanceRecord[]>(`/students/${studentId}/attendance`),
    enabled: !Number.isNaN(studentId),
  })
  const { data: engagement } = useQuery({
    queryKey: ["student-engagement", studentId],
    queryFn: () => api.get<EngagementRecord[]>(`/students/${studentId}/engagement`),
    enabled: !Number.isNaN(studentId),
  })
  const { data: predictions } = useQuery({
    queryKey: ["student-predictions", studentId],
    queryFn: () => api.get<PredictionResult[]>(`/predictions/students/${studentId}`),
    enabled: !Number.isNaN(studentId),
  })
  const { data: interventions } = useQuery({
    queryKey: ["student-interventions", studentId],
    queryFn: () => api.get<Intervention[]>(`/interventions?student_id=${studentId}`),
    enabled: !Number.isNaN(studentId),
  })
  const { data: impact } = useQuery({
    queryKey: ["student-impact", studentId],
    queryFn: () => api.get<InterventionImpact>(`/analytics/intervention-impact?student_id=${studentId}`),
    enabled: !Number.isNaN(studentId),
  })

  const runPrediction = useMutation({
    mutationFn: () =>
      api.post<PredictionWithWarning>(`/predictions?student_id=${studentId}`, {
        attendance: Number(predInputs.attendance),
        previous_performance: Number(predInputs.previous_performance),
        internal_marks: Number(predInputs.internal_marks),
        assignment_score: Number(predInputs.assignment_score),
        engagement: Number(predInputs.engagement),
        study_hours: Number(predInputs.study_hours) || 0,
      }),
    onSuccess: (res) => {
      setPredictionResult(res)
      setPredictionError(null)
      queryClient.invalidateQueries({ queryKey: ["student", studentId] })
      queryClient.invalidateQueries({ queryKey: ["student-predictions", studentId] })
      queryClient.invalidateQueries({ queryKey: ["dashboard-analytics"] })
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
      if (res.warning) {
        toast.warning("Risk level increased!", {
          description: `${res.prediction.student_name}'s risk moved from ${res.warning.previous_risk.toUpperCase()} to ${res.warning.current_risk.toUpperCase()}.`,
        })
      } else {
        toast.success("Prediction completed")
      }
    },
    onError: (err) => {
      setPredictionError(err instanceof Error ? err.message : "Prediction failed")
    },
  })

  const createIntervention = useMutation({
    mutationFn: () =>
      api.post<Intervention>("/interventions", {
        student_id: studentId,
        type: ivType,
        title: ivTitle || "Intervention",
        description: ivDesc || undefined,
        follow_up_date: ivFollowUp ? new Date(ivFollowUp).toISOString() : undefined,
      }),
    onSuccess: () => {
      toast.success("Intervention created")
      setIvOpen(false)
      setIvTitle("")
      setIvDesc("")
      queryClient.invalidateQueries({ queryKey: ["student-interventions", studentId] })
      queryClient.invalidateQueries({ queryKey: ["interventions"] })
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to create intervention"),
  })

  const updateStatus = useMutation({
    mutationFn: ({ id: iid, status: st }: { id: number; status: string }) =>
      api.put(`/interventions/${iid}`, { status: st }),
    onSuccess: () => {
      toast.success("Intervention status updated")
      queryClient.invalidateQueries({ queryKey: ["student-interventions", studentId] })
    },
  })

  const handlePredictionSubmit = () => {
    setPredictionError(null)
    for (const [k, v] of Object.entries(predInputs)) {
      if (k === "study_hours") continue
      const n = Number(v)
      if (v === "" || Number.isNaN(n) || n < 0 || n > 100) {
        setPredictionError(`Enter a valid value (0–100) for ${k.replace(/_/g, " ")}.`)
        return
      }
    }
    runPrediction.mutate()
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    )
  }

  if (error || !student) {
    return (
      <EmptyState
        icon={UserRound}
        title="Student not found"
        description="This student may not exist or you don't have access."
        action={<Button onClick={() => navigate("/students")}>Back to students</Button>}
      />
    )
  }

  const latest = predictions?.[0]
  const trendData = (predictions ?? [])
    .slice()
    .reverse()
    .map((p) => ({ date: p.prediction_date, probability: p.risk_probability }))

  return (
    <div className="space-y-6">
      <button
        className="flex items-center gap-1.5 text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
        onClick={() => navigate("/students")}
      >
        <ArrowLeft className="h-4 w-4" /> Back to students
      </button>

      {/* Header */}
      <Card>
        <CardContent className="flex flex-wrap items-center gap-5 p-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-xl font-bold text-white">
            {student.full_name.split(" ").map((p) => p[0]).slice(0, 2).join("")}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold">{student.full_name}</h1>
              <RiskBadge level={student.risk_level} />
            </div>
            <p className="mt-0.5 text-sm text-[var(--muted-foreground)]">
              {student.student_id} · {student.department_name} · Section {student.section_name} · Sem{" "}
              {student.current_semester} · Admitted {student.admission_year}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => window.open(`/api/reports/student/${student.id}/csv`, "_blank")}
            >
              <FileDown className="h-4 w-4" /> CSV Report
            </Button>
            <Button onClick={() => { setPredictionOpen(true); setPredictionResult(null) }}>
              <BrainCircuit className="h-4 w-4" /> Run AI Prediction
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Academic health */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <HealthMetric label="Overall Score" value={student.average_score} icon={Gauge} color="#6366f1" />
        <HealthMetric label="Attendance" value={student.attendance} icon={CalendarCheck} color="#0ea5e9" />
        <HealthMetric label="Engagement" value={student.engagement} icon={Sparkles} color="#8b5cf6" />
        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg" style={{ background: `${riskColor(student.risk_level)}18`, color: riskColor(student.risk_level) }}>
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-[var(--muted-foreground)]">Risk Probability</p>
              <p className="text-lg font-bold" style={{ color: riskColor(student.risk_level) }}>
                {formatPercent(student.risk_probability, 1)}
              </p>
              {latest && (
                <p className="text-[11px] text-[var(--muted-foreground)]">
                  {latest.model} · {formatDate(latest.prediction_date)}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList className="flex w-full flex-wrap justify-start overflow-x-auto sm:w-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="academics">Academics</TabsTrigger>
          <TabsTrigger value="attendance">Attendance</TabsTrigger>
          <TabsTrigger value="engagement">Engagement</TabsTrigger>
          <TabsTrigger value="predictions">Predictions</TabsTrigger>
          <TabsTrigger value="interventions">Interventions</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Risk Probability Trend</CardTitle>
                <CardDescription>Latest AI predictions over time</CardDescription>
              </CardHeader>
              <CardContent>
                {trendData.length === 0 ? (
                  <EmptyState title="No predictions yet" description="Run a prediction to see the trend." />
                ) : (
                  <PredictionTrendChart data={trendData} />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Intervention Impact</CardTitle>
                  <CardDescription>Before vs after intervention</CardDescription>
                </div>
                <LifeBuoy className="h-5 w-5 text-[var(--primary)]" />
              </CardHeader>
              <CardContent className="space-y-2">
                {impact?.intervention_count === 0 || !impact ? (
                  <EmptyState
                    icon={LifeBuoy}
                    title="No interventions yet"
                    description="Create an intervention to start tracking impact."
                  />
                ) : (
                  <>
                    <BeforeAfterChart
                      before={{ risk: impact.risk_before, performance: impact.performance_before, attendance: impact.attendance_before }}
                      after={{ risk: impact.risk_after, performance: impact.performance_after, attendance: impact.attendance_after }}
                    />
                    <ImpactBadge label="Risk Probability" before={impact.risk_before !== null ? +(impact.risk_before * 100).toFixed(1) : null} after={impact.risk_after !== null ? +(impact.risk_after * 100).toFixed(1) : null} />
                    <ImpactBadge label="Performance" before={impact.performance_before} after={impact.performance_after} />
                    <ImpactBadge label="Attendance" before={impact.attendance_before} after={impact.attendance_after} />
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {latest && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-[var(--primary)]" /> Why this prediction?
                </CardTitle>
                <CardDescription>
                  Feature impact from the trained model ({latest.model}) · {formatDateTime(latest.prediction_date)}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {latest.factors.map((f) => (
                    <div
                      key={f.feature}
                      className="flex items-center justify-between rounded-lg border border-[var(--border)] px-3 py-2.5 text-sm"
                    >
                      <span className="capitalize text-[var(--muted-foreground)]">{f.feature.replace(/_/g, " ")}</span>
                      <Badge
                        variant={
                          f.impact === "high" ? "danger" : f.impact === "medium" ? "warning" : "secondary"
                        }
                      >
                        {impactConfig[f.impact]}
                      </Badge>
                    </div>
                  ))}
                </div>
                {latest.recommendations.length > 0 && (
                  <div className="mt-4 rounded-lg border border-indigo-500/20 bg-indigo-500/5 p-4">
                    <p className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
                      <MessageSquareText className="h-4 w-4 text-[var(--primary)]" /> Recommendations
                    </p>
                    <ul className="list-inside list-disc space-y-1 text-sm text-[var(--muted-foreground)]">
                      {latest.recommendations.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="academics">
          <Card>
            <CardHeader>
              <CardTitle>Academic Records</CardTitle>
              <CardDescription>Internal assessment, assignments, and exam scores</CardDescription>
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
                      <th className="px-4 py-3 font-medium">Total</th>
                      <th className="px-5 py-3 font-medium">Grade</th>
                    </tr>
                  </thead>
                  <tbody>
                    {academics?.map((r) => (
                      <tr key={r.id} className="border-b border-[var(--border)] last:border-0">
                        <td className="px-5 py-3 font-medium">{r.subject_name}</td>
                        <td className="px-4 py-3">{r.semester}</td>
                        <td className="px-4 py-3">{formatNumber(r.internal_marks)}</td>
                        <td className="px-4 py-3">{formatNumber(r.assignment_score)}</td>
                        <td className="px-4 py-3">{formatNumber(r.exam_score)}</td>
                        <td className="px-4 py-3 font-semibold">{formatNumber(r.total_score)}</td>
                        <td className="px-5 py-3">
                          <Badge variant={r.grade === "A" || r.grade === "B" ? "success" : r.grade === "C" ? "warning" : "danger"}>
                            {r.grade}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                    {!academics?.length && (
                      <tr>
                        <td colSpan={7} className="px-5 py-8 text-center text-sm text-[var(--muted-foreground)]">
                          No academic records.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="attendance">
          <Card>
            <CardHeader>
              <CardTitle>Attendance Records</CardTitle>
              <CardDescription>Monthly attendance per subject</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-left text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
                      <th className="px-5 py-3 font-medium">Month</th>
                      <th className="px-4 py-3 font-medium">Subject</th>
                      <th className="px-4 py-3 font-medium">Classes Held</th>
                      <th className="px-4 py-3 font-medium">Attended</th>
                      <th className="px-5 py-3 font-medium">Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attendance?.map((r) => (
                      <tr key={r.id} className="border-b border-[var(--border)] last:border-0">
                        <td className="px-5 py-2.5">Month {r.month}</td>
                        <td className="px-4 py-2.5">{r.subject_name}</td>
                        <td className="px-4 py-2.5">{r.classes_held}</td>
                        <td className="px-4 py-2.5">{r.classes_attended}</td>
                        <td className="px-5 py-2.5">
                          <span
                            className={
                              (r.attendance_percentage ?? 0) < 75 ? "font-semibold text-red-500" : "font-semibold text-emerald-500"
                            }
                          >
                            {formatNumber(r.attendance_percentage)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                    {!attendance?.length && (
                      <tr>
                        <td colSpan={5} className="px-5 py-8 text-center text-sm text-[var(--muted-foreground)]">
                          No attendance records.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="engagement">
          <Card>
            <CardHeader>
              <CardTitle>Engagement Records</CardTitle>
              <CardDescription>Participation, LMS activity, and study hours</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-left text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
                      <th className="px-5 py-3 font-medium">Month</th>
                      <th className="px-4 py-3 font-medium">Participation</th>
                      <th className="px-4 py-3 font-medium">LMS Logins</th>
                      <th className="px-4 py-3 font-medium">Forum Posts</th>
                      <th className="px-4 py-3 font-medium">Study Hours</th>
                      <th className="px-5 py-3 font-medium">Engagement Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {engagement?.map((r) => (
                      <tr key={r.id} className="border-b border-[var(--border)] last:border-0">
                        <td className="px-5 py-2.5">Month {r.month}</td>
                        <td className="px-4 py-2.5">{formatNumber(r.participation_score)}%</td>
                        <td className="px-4 py-2.5">{r.lms_logins}</td>
                        <td className="px-4 py-2.5">{r.forum_posts}</td>
                        <td className="px-4 py-2.5">{r.study_hours}h</td>
                        <td className="px-5 py-2.5 font-semibold">{formatNumber(r.engagement_score)}%</td>
                      </tr>
                    ))}
                    {!engagement?.length && (
                      <tr>
                        <td colSpan={6} className="px-5 py-8 text-center text-sm text-[var(--muted-foreground)]">
                          No engagement records.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="predictions">
          <Card>
            <CardHeader>
              <CardTitle>Prediction History</CardTitle>
              <CardDescription>All AI predictions for this student</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {!predictions?.length && (
                <EmptyState
                  icon={BrainCircuit}
                  title="No predictions available"
                  description="Run an AI prediction to see the analysis."
                  action={
                    <Button onClick={() => { setPredictionOpen(true); setPredictionResult(null) }}>
                      <BrainCircuit className="h-4 w-4" /> Run Prediction
                    </Button>
                  }
                />
              )}
              {predictions?.map((p) => (
                <div key={p.id} className="rounded-lg border border-[var(--border)] p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <RiskBadge level={p.risk_level} />
                      <span className="text-lg font-bold">{formatPercent(p.risk_probability, 1)}</span>
                      <span className="text-xs text-[var(--muted-foreground)]">probability of poor performance</span>
                    </div>
                    <span className="text-xs text-[var(--muted-foreground)]">
                      {p.model} · {formatDateTime(p.prediction_date)}
                    </span>
                  </div>
                  <div className="mt-3 grid gap-1.5 sm:grid-cols-2 lg:grid-cols-3">
                    {p.factors.map((f) => (
                      <div key={f.feature} className="flex items-center justify-between rounded-md bg-[var(--muted)] px-3 py-1.5 text-xs">
                        <span className="capitalize">{f.feature.replace(/_/g, " ")}</span>
                        <Badge variant={f.impact === "high" ? "danger" : f.impact === "medium" ? "warning" : "secondary"}>
                          {f.impact}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="interventions">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Interventions</CardTitle>
                <CardDescription>Plans assigned to this student</CardDescription>
              </div>
              <Button size="sm" onClick={() => setIvOpen(true)}>
                <Plus className="h-4 w-4" /> New Intervention
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {!interventions?.length && (
                <EmptyState
                  icon={LifeBuoy}
                  title="No interventions found"
                  description="Create an intervention plan for this student."
                />
              )}
              {interventions?.map((iv) => (
                <div key={iv.id} className="rounded-lg border border-[var(--border)] p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <BookOpen className="h-4 w-4 text-[var(--primary)]" />
                      <p className="font-medium">{iv.title}</p>
                      <Badge variant="secondary" className="capitalize">
                        {iv.type.replace(/_/g, " ")}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          iv.status === "completed" ? "success" : iv.status === "in_progress" ? "info" : iv.status === "cancelled" ? "destructive" : "warning"
                        }
                        className="capitalize"
                      >
                        {iv.status.replace(/_/g, " ")}
                      </Badge>
                      {iv.status !== "completed" && iv.status !== "cancelled" && (
                        <Select
                          value={iv.status}
                          onValueChange={(v) => updateStatus.mutate({ id: iv.id, status: v })}
                        >
                          <SelectTrigger className="h-8 w-28 text-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="pending">Pending</SelectItem>
                            <SelectItem value="in_progress">In Progress</SelectItem>
                            <SelectItem value="completed">Completed</SelectItem>
                            <SelectItem value="cancelled">Cancelled</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                    </div>
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
                    {iv.completed_date && (
                      <span className="flex items-center gap-1 text-emerald-500">
                        <CheckCircle2 className="h-3 w-3" /> Completed: {formatDate(iv.completed_date)}
                      </span>
                    )}
                  </div>
                  {iv.notes && (
                    <p className="mt-2 rounded-md bg-[var(--muted)] px-3 py-2 text-xs text-[var(--muted-foreground)]">
                      {iv.notes}
                    </p>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Prediction dialog */}
      <Dialog open={predictionOpen} onOpenChange={setPredictionOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <BrainCircuit className="h-5 w-5 text-[var(--primary)]" /> AI Performance Prediction
            </DialogTitle>
            <DialogDescription>
              Enter current academic indicators for {student.full_name}. The active trained model will compute the risk.
            </DialogDescription>
          </DialogHeader>

          {predictionResult ? (
            <div className="space-y-4">
              <div
                className="rounded-xl border p-6 text-center"
                style={{
                  borderColor: `${riskColor(predictionResult.prediction.risk_level)}40`,
                  background: `${riskColor(predictionResult.prediction.risk_level)}0d`,
                }}
              >
                <p className="text-4xl font-bold" style={{ color: riskColor(predictionResult.prediction.risk_level) }}>
                  {formatPercent(predictionResult.prediction.risk_probability, 1)}
                </p>
                <p className="mt-1 text-sm text-[var(--muted-foreground)]">Probability of poor performance</p>
                <div className="mt-3 flex items-center justify-center gap-2">
                  <RiskBadge level={predictionResult.prediction.risk_level} />
                  <span className="text-xs text-[var(--muted-foreground)]">
                    {predictionResult.prediction.model} · {formatDateTime(predictionResult.prediction.prediction_date)}
                  </span>
                </div>
              </div>

              {predictionResult.warning && (
                <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
                  <p className="flex items-center gap-2 text-sm font-semibold text-red-500">
                    <AlertTriangle className="h-4 w-4" /> WARNING — Risk level increased
                  </p>
                  <p className="mt-1 text-sm">
                    Previous: <RiskBadge level={predictionResult.warning.previous_risk} className="mx-1" /> → Current:{" "}
                    <RiskBadge level={predictionResult.warning.current_risk} className="ml-1" />
                  </p>
                  <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                    Change: +{(predictionResult.warning.change * 100).toFixed(1)}% probability
                  </p>
                  {predictionResult.warning.contributing_factors.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {predictionResult.warning.contributing_factors.map((f) => (
                        <Badge key={f.feature} variant="danger" className="capitalize">
                          {f.feature.replace(/_/g, " ")}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div>
                <p className="mb-2 text-sm font-semibold">Feature impact</p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {predictionResult.prediction.factors.map((f) => (
                    <div
                      key={f.feature}
                      className="flex items-center justify-between rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
                    >
                      <span className="capitalize text-[var(--muted-foreground)]">{f.feature.replace(/_/g, " ")}</span>
                      <Badge variant={f.impact === "high" ? "danger" : f.impact === "medium" ? "warning" : "secondary"}>
                        {impactConfig[f.impact]}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-lg border border-indigo-500/20 bg-indigo-500/5 p-4">
                <p className="mb-2 text-sm font-semibold">Recommendations</p>
                <ul className="list-inside list-disc space-y-1 text-sm text-[var(--muted-foreground)]">
                  {predictionResult.prediction.recommendations.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setPredictionOpen(false)}>
                  Close
                </Button>
                <Button
                  variant="outline"
                  onClick={() => { setIvOpen(true); setPredictionOpen(false) }}
                >
                  <LifeBuoy className="h-4 w-4" /> Create Intervention
                </Button>
              </DialogFooter>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-3">
                {(
                  [
                    ["attendance", "Attendance %"],
                    ["previous_performance", "Previous Performance"],
                    ["internal_marks", "Internal Marks"],
                    ["assignment_score", "Assignment Score"],
                    ["engagement", "Engagement"],
                    ["study_hours", "Study Hours / day"],
                  ] as const
                ).map(([key, label]) => (
                  <div key={key} className="space-y-1.5">
                    <Label htmlFor={key}>{label}</Label>
                    <Input
                      id={key}
                      type="number"
                      step="0.1"
                      min={key === "study_hours" ? 0 : 0}
                      max={key === "study_hours" ? 24 : 100}
                      placeholder={key === "study_hours" ? "0–24" : "0–100"}
                      value={predInputs[key]}
                      onChange={(e) => setPredInputs({ ...predInputs, [key]: e.target.value })}
                    />
                  </div>
                ))}
              </div>
              {predictionError && (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500">
                  {predictionError}
                </div>
              )}
              <DialogFooter>
                <Button variant="outline" onClick={() => setPredictionOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handlePredictionSubmit} disabled={runPrediction.isPending}>
                  {runPrediction.isPending ? <Spinner className="h-4 w-4 text-white" /> : <BrainCircuit className="h-4 w-4" />}
                  Run Prediction
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Intervention dialog */}
      <Dialog open={ivOpen} onOpenChange={setIvOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <LifeBuoy className="h-5 w-5 text-[var(--primary)]" /> New Intervention
            </DialogTitle>
            <DialogDescription>Create an intervention plan for {student.full_name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label>Type</Label>
              <Select value={ivType} onValueChange={setIvType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mentor_meeting">Mentor Meeting</SelectItem>
                  <SelectItem value="academic_counselling">Academic Counselling</SelectItem>
                  <SelectItem value="attendance_monitoring">Attendance Monitoring</SelectItem>
                  <SelectItem value="additional_assignment">Additional Assignment</SelectItem>
                  <SelectItem value="study_plan">Study Plan</SelectItem>
                  <SelectItem value="subject_support">Subject Support</SelectItem>
                  <SelectItem value="parent_communication">Parent/Guardian Communication</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Title</Label>
              <Input
                placeholder="e.g. Weekly mentoring session"
                value={ivTitle}
                onChange={(e) => setIvTitle(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Description</Label>
              <Input
                placeholder="What will this intervention involve?"
                value={ivDesc}
                onChange={(e) => setIvDesc(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Follow-up date</Label>
              <Input
                type="date"
                value={ivFollowUp}
                onChange={(e) => setIvFollowUp(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIvOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => createIntervention.mutate()} disabled={createIntervention.isPending}>
              {createIntervention.isPending ? <Spinner className="h-4 w-4 text-white" /> : null}
              Create Intervention
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

