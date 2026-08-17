import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { FileBarChart2, FileDown, ExternalLink } from "lucide-react"
import { api } from "@/lib/api"
import type { StudentSummary } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"

interface Report {
  student: {
    name: string
    student_id: string
    email: string
    department: string
    section: string
    admission_year: number
    current_semester: number
  }
  academic_health: {
    attendance: number | null
    average_score: number | null
    engagement: number | null
    risk_probability: number | null
    risk_level: string | null
  }
  prediction_summary: {
    probability: number | null
    level: string | null
    date: string | null
    model: string | null
  }
  academics: unknown[]
  attendance: unknown[]
  predictions: unknown[]
  risk_factors: { feature: string; impact: string }[]
  recommendations: string[]
  interventions: unknown[]
  generated_at: string
}

export default function Reports() {
  const [search, setSearch] = useState("")
  const [selected, setSelected] = useState<number | null>(null)

  const { data: students, isLoading } = useQuery({
    queryKey: ["report-students", search],
    queryFn: () =>
      api.get<StudentSummary[]>(
        `/students?page_size=30${search ? `&search=${encodeURIComponent(search)}` : ""}`,
      ),
  })

  const { data: report, isLoading: reportLoading } = useQuery({
    queryKey: ["report", selected],
    queryFn: () => api.get<Report>(`/reports/student/${selected}`),
    enabled: selected !== null,
  })

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Reports</h1>
        <p className="mt-1 text-sm text-[var(--muted-foreground)]">
          Generate comprehensive student performance reports with CSV export.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileBarChart2 className="h-4 w-4 text-[var(--primary)]" /> Select student
            </CardTitle>
            <CardDescription>Search and choose a student to generate a report</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
              <Input
                placeholder="Search students…"
                className="pl-8"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="max-h-80 space-y-1 overflow-y-auto pr-1">
              {isLoading &&
                Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}
              {!isLoading && !students?.length && (
                <EmptyState icon={Search} title="No students found" description="Try another search." />
              )}
              {students?.map((s) => (
                <button
                  key={s.id}
                  className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-sm transition-colors hover:bg-[var(--muted)] ${
                    selected === s.id ? "border-[var(--primary)] bg-[var(--primary)]/5" : "border-[var(--border)]"
                  }`}
                  onClick={() => setSelected(s.id)}
                >
                  <span className="font-medium">{s.full_name}</span>
                  <span className="text-xs text-[var(--muted-foreground)]">{s.student_id}</span>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Report preview</CardTitle>
            <CardDescription>
              {selected ? "Generated from live database records" : "Select a student to begin"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {reportLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-40 w-full" />
              </div>
            ) : !report ? (
              <EmptyState
                icon={FileBarChart2}
                title="No report selected"
                description="Pick a student from the list to preview their report."
              />
            ) : (
              <div className="space-y-4">
                <div className="rounded-lg border border-[var(--border)] p-4">
                  <p className="text-base font-bold">{report.student.name}</p>
                  <p className="text-xs text-[var(--muted-foreground)]">
                    {report.student.student_id} · {report.student.department} · {report.student.section} · Sem{" "}
                    {report.student.current_semester}
                  </p>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
                    <div>
                      <p className="text-xs text-[var(--muted-foreground)]">Avg Score</p>
                      <p className="font-semibold">
                        {report.academic_health.average_score?.toFixed(1) ?? "—"}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[var(--muted-foreground)]">Attendance</p>
                      <p className="font-semibold">{report.academic_health.attendance?.toFixed(1) ?? "—"}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-[var(--muted-foreground)]">Engagement</p>
                      <p className="font-semibold">{report.academic_health.engagement?.toFixed(1) ?? "—"}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-[var(--muted-foreground)]">Risk</p>
                      <p className="font-semibold uppercase">
                        {report.prediction_summary.level ?? "—"} (
                        {report.prediction_summary.probability !== null
                          ? (report.prediction_summary.probability * 100).toFixed(1)
                          : "—"}
                        %)
                      </p>
                    </div>
                  </div>
                </div>

                {report.risk_factors.length > 0 && (
                  <div>
                    <p className="mb-1.5 text-sm font-semibold">Risk factors</p>
                    <div className="flex flex-wrap gap-1.5">
                      {report.risk_factors.map((f) => (
                        <span
                          key={f.feature}
                          className="rounded-full border border-[var(--border)] px-2.5 py-0.5 text-xs capitalize"
                        >
                          {f.feature.replace(/_/g, " ")} · {f.impact}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {report.recommendations.length > 0 && (
                  <div>
                    <p className="mb-1.5 text-sm font-semibold">Recommendations</p>
                    <ul className="list-inside list-disc space-y-0.5 text-sm text-[var(--muted-foreground)]">
                      {report.recommendations.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex gap-2">
                  <Button
                    onClick={() => window.open(`/api/reports/student/${selected}/csv`, "_blank")}
                  >
                    <FileDown className="h-4 w-4" /> Export CSV
                  </Button>
                  <Button variant="outline" onClick={() => window.open(`/students/${selected}`, "_blank")}>
                    <ExternalLink className="h-4 w-4" /> Open profile
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
