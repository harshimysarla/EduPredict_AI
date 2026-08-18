import { useMemo } from "react"
import { useParams, Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import {
  GraduationCap,
  CalendarCheck,
  Layers,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Beaker,
  AlertTriangle,
} from "lucide-react"
import { portalService } from "@/services/portalService"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { formatNumber } from "@/lib/utils"
import { cn } from "@/lib/utils"

export default function SemesterDetails() {
  const { sem } = useParams<{ sem: string }>()
  const semester = Number(sem)

  const { data: list } = useQuery({
    queryKey: ["portal-semesters"],
    queryFn: portalService.semesters,
  })

  const { data: detail, isLoading, isError } = useQuery({
    queryKey: ["portal-semester", semester],
    queryFn: () => portalService.semester(semester),
    enabled: Number.isFinite(semester) && semester > 0,
  })

  const semesters = useMemo(() => list?.semesters ?? [], [list])

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-72" />
        <div className="grid gap-4 md:grid-cols-4">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (isError || !detail) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Semester not found"
        description="This semester does not exist in your academic records."
      />
    )
  }

  const summary = detail.summary
  const idx = semesters.findIndex((s) => s.semester === semester)
  const prev = idx > 0 ? semesters[idx - 1].semester : null
  const next = idx >= 0 && idx < semesters.length - 1 ? semesters[idx + 1].semester : null
  const inProgress = detail.currentSemester === semester

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Semester {detail.semesterLabel || detail.semester}
            {inProgress && <Badge variant="info" className="ml-2 align-middle">In progress</Badge>}
          </h1>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            {detail.profile.name} · {detail.profile.rollNumber} · {detail.profile.branch}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {prev != null ? (
            <Link to={`/student/semesters/${prev}`}>
              <Badge variant="secondary" className="cursor-pointer gap-1 px-3 py-1.5">
                <ChevronLeft className="h-3.5 w-3.5" /> Semester {prev}
              </Badge>
            </Link>
          ) : (
            <Badge variant="outline" className="cursor-not-allowed px-3 py-1.5 opacity-40">
              <ChevronLeft className="h-3.5 w-3.5" />
            </Badge>
          )}
          {next != null ? (
            <Link to={`/student/semesters/${next}`}>
              <Badge variant="secondary" className="cursor-pointer gap-1 px-3 py-1.5">
                Semester {next} <ChevronRight className="h-3.5 w-3.5" />
              </Badge>
            </Link>
          ) : (
            <Badge variant="outline" className="cursor-not-allowed px-3 py-1.5 opacity-40">
              <ChevronRight className="h-3.5 w-3.5" />
            </Badge>
          )}
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <SummaryCard icon={GraduationCap} label="SGPA" value={summary.sgpa != null ? summary.sgpa.toFixed(2) : "—"} hint={inProgress ? "in progress" : undefined} />
        <SummaryCard icon={ClipboardList} label="Overall CGPA" value={detail.overallCgpa != null ? detail.overallCgpa.toFixed(2) : "—"} />
        <SummaryCard icon={Layers} label="Total Credits" value={String(summary.totalCredits ?? "—")} />
        <SummaryCard icon={CalendarCheck} label="Credits Earned" value={String(summary.earnedCredits ?? "—")} />
      </div>

      {/* Theory courses */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-[var(--primary)]" /> Theory Courses
          </CardTitle>
          <CardDescription>Internal assessments, AATs, totals, grades and attendance</CardDescription>
        </CardHeader>
        <CardContent>
          {detail.theoryCourses.length === 0 ? (
            <EmptyState title="No theory courses" description="No theory courses recorded for this semester." />
          ) : (
            <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)] bg-[var(--muted)]/40 text-left text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
                    <th className="px-3 py-2.5 font-medium">#</th>
                    <th className="px-3 py-2.5 font-medium">Course</th>
                    <th className="px-3 py-2.5 text-center font-medium">CIE1</th>
                    <th className="px-3 py-2.5 text-center font-medium">AAT1</th>
                    <th className="px-3 py-2.5 text-center font-medium">CIE2</th>
                    <th className="px-3 py-2.5 text-center font-medium">AAT2</th>
                    <th className="px-3 py-2.5 text-center font-medium">Total</th>
                    <th className="px-3 py-2.5 text-center font-medium">Credits</th>
                    <th className="px-3 py-2.5 text-center font-medium">Attendance</th>
                    <th className="px-3 py-2.5 text-right font-medium">Grade</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.theoryCourses.map((c) => (
                    <tr key={`${c.courseCode}-${c.serialNumber}`} className="border-b border-[var(--border)] last:border-0">
                      <td className="px-3 py-2.5 text-[var(--muted-foreground)]">{c.serialNumber ?? "—"}</td>
                      <td className="px-3 py-2.5">
                        <p className="font-medium leading-tight">{c.courseName}</p>
                        <p className="text-[11px] text-[var(--muted-foreground)]">{c.courseCode}</p>
                      </td>
                      <td className="px-3 py-2.5 text-center">{c.CIE1 ?? "—"}</td>
                      <td className="px-3 py-2.5 text-center">
                        {c.AAT1_I != null || c.AAT1_II != null ? `${c.AAT1_I ?? 0} + ${c.AAT1_II ?? 0}` : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-center">{c.CIE2 ?? "—"}</td>
                      <td className="px-3 py-2.5 text-center">
                        {c.AAT2_I != null || c.AAT2_II != null ? `${c.AAT2_I ?? 0} + ${c.AAT2_II ?? 0}` : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-center font-semibold">
                        {c.totalMarks != null ? `${formatNumber(c.totalMarks)}%` : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-center">{c.credits}</td>
                      <td className="px-3 py-2.5 text-center">
                        {c.attendance != null ? (
                          <span className={cn("font-semibold", c.attendance >= 75 ? "text-emerald-500" : "text-red-500")}>
                            {formatNumber(c.attendance)}%
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-right">
                        <GradeBadge grade={c.grade} gradePoint={c.gradePoint} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Lab courses */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Beaker className="h-4 w-4 text-[var(--primary)]" /> Laboratory Courses
          </CardTitle>
          <CardDescription>Weekly cycle marks, exam marks, totals and grades</CardDescription>
        </CardHeader>
        <CardContent>
          {detail.labCourses.length === 0 ? (
            <EmptyState title="No laboratory courses" description="No lab courses recorded for this semester." />
          ) : (
            <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)] bg-[var(--muted)]/40 text-left text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
                    <th className="px-3 py-2.5 font-medium">#</th>
                    <th className="px-3 py-2.5 font-medium">Course</th>
                    {Array.from({ length: 14 }, (_, i) => (
                      <th key={i} className="px-2 py-2.5 text-center font-medium">W{i + 1}</th>
                    ))}
                    <th className="px-3 py-2.5 text-center font-medium">Exam</th>
                    <th className="px-3 py-2.5 text-center font-medium">Total</th>
                    <th className="px-3 py-2.5 text-center font-medium">Credits</th>
                    <th className="px-3 py-2.5 text-right font-medium">Grade</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.labCourses.map((c) => (
                    <tr key={`${c.courseCode}-${c.serialNumber}`} className="border-b border-[var(--border)] last:border-0">
                      <td className="px-3 py-2.5 text-[var(--muted-foreground)]">{c.serialNumber ?? "—"}</td>
                      <td className="min-w-44 px-3 py-2.5">
                        <p className="font-medium leading-tight">{c.courseName}</p>
                        <p className="text-[11px] text-[var(--muted-foreground)]">{c.courseCode}</p>
                      </td>
                      {Array.from({ length: 14 }, (_, i) => (
                        <td key={i} className="px-2 py-2.5 text-center text-xs">
                          {c[`week${i + 1}` as keyof typeof c] ?? "—"}
                        </td>
                      ))}
                      <td className="px-3 py-2.5 text-center">{c.examMarks ?? "—"}</td>
                      <td className="px-3 py-2.5 text-center font-semibold">
                        {c.totalMarks != null ? `${formatNumber(c.totalMarks)}%` : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-center">{c.credits}</td>
                      <td className="px-3 py-2.5 text-right">
                        <GradeBadge grade={c.grade} gradePoint={c.gradePoint} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Attendance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarCheck className="h-4 w-4 text-[var(--primary)]" /> Attendance
          </CardTitle>
          <CardDescription>Satisfactory ≥75% · Condonation 65–74% · Shortage &lt;65%</CardDescription>
        </CardHeader>
        <CardContent>
          {detail.attendance.length === 0 ? (
            <EmptyState title="No attendance data" description="No attendance records for this semester." />
          ) : (
            <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)] bg-[var(--muted)]/40 text-left text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
                    <th className="px-3 py-2.5 font-medium">Course</th>
                    <th className="px-3 py-2.5 font-medium">Type</th>
                    <th className="px-3 py-2.5 text-center font-medium">Conducted</th>
                    <th className="px-3 py-2.5 text-center font-medium">Attended</th>
                    <th className="px-3 py-2.5 text-right font-medium">%</th>
                    <th className="px-3 py-2.5 text-right font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.attendance.map((a) => (
                    <tr key={a.courseCode} className="border-b border-[var(--border)] last:border-0">
                      <td className="px-3 py-2.5">
                        <p className="font-medium leading-tight">{a.courseName}</p>
                        <p className="text-[11px] text-[var(--muted-foreground)]">{a.courseCode}</p>
                      </td>
                      <td className="px-3 py-2.5">
                        <Badge variant="secondary">{a.courseType === "L" ? "Lab" : "Theory"}</Badge>
                      </td>
                      <td className="px-3 py-2.5 text-center">{a.conducted ?? "—"}</td>
                      <td className="px-3 py-2.5 text-center">{a.attended ?? "—"}</td>
                      <td className="px-3 py-2.5 text-right font-semibold">
                        {a.attendancePercentage != null ? `${formatNumber(a.attendancePercentage)}%` : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-right">
                        <StatusBadge status={a.status ?? ""} pct={a.attendancePercentage ?? null} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Grade records */}
      {detail.gradeRecords.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ClipboardList className="h-4 w-4 text-[var(--primary)]" /> Grade Records
            </CardTitle>
            <CardDescription>Final grades awarded for this semester</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border)] bg-[var(--muted)]/40 text-left text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
                    <th className="px-3 py-2.5 font-medium">Course</th>
                    <th className="px-3 py-2.5 text-center font-medium">Credits</th>
                    <th className="px-3 py-2.5 text-center font-medium">Attendance</th>
                    <th className="px-3 py-2.5 text-right font-medium">Grade</th>
                    <th className="px-3 py-2.5 text-right font-medium">Points</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.gradeRecords.map((g) => (
                    <tr key={g.courseCode} className="border-b border-[var(--border)] last:border-0">
                      <td className="px-3 py-2.5">
                        <p className="font-medium leading-tight">{g.courseName}</p>
                        <p className="text-[11px] text-[var(--muted-foreground)]">{g.courseCode}</p>
                      </td>
                      <td className="px-3 py-2.5 text-center">{g.credits}</td>
                      <td className="px-3 py-2.5 text-center">
                        {g.attendancePercentage != null ? `${formatNumber(g.attendancePercentage)}%` : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-right">
                        <GradeBadge grade={g.grade} gradePoint={g.gradePoint} />
                      </td>
                      <td className="px-3 py-2.5 text-right font-semibold">{g.gradePoint ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function SummaryCard({ icon: Icon, label, value, hint }: { icon: typeof GraduationCap; label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
          <Icon className="h-3.5 w-3.5" /> {label}
        </div>
        <p className="mt-1.5 text-2xl font-bold">{value}</p>
        {hint && <p className="mt-0.5 text-[11px] text-[var(--muted-foreground)]">{hint}</p>}
      </CardContent>
    </Card>
  )
}

function GradeBadge({ grade, gradePoint }: { grade?: string; gradePoint?: number | null }) {
  if (!grade || grade === "-") return <Badge variant="secondary">—</Badge>
  return (
    <Badge
      variant={
        gradePoint != null && gradePoint >= 9
          ? "success"
          : gradePoint != null && gradePoint >= 8
            ? "info"
            : gradePoint != null && gradePoint >= 7
              ? "warning"
              : "secondary"
      }
    >
      {grade}
    </Badge>
  )
}

function StatusBadge({ status, pct }: { status: string; pct: number | null }) {
  const effective = status || (pct == null ? "Not Available" : pct >= 75 ? "Satisfactory" : pct >= 65 ? "Condonation" : "Shortage")
  return (
    <Badge
      variant={effective === "Satisfactory" ? "success" : effective === "Condonation" ? "warning" : effective === "Not Available" ? "secondary" : "danger"}
      className="capitalize"
    >
      {effective}
    </Badge>
  )
}