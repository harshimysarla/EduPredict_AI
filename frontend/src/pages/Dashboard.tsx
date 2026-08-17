import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import {
  Users,
  ShieldAlert,
  ShieldX,
  ShieldCheck,
  Gauge,
  CalendarCheck,
  ArrowUpRight,
  Activity,
  AlertTriangle,
} from "lucide-react"
import { api } from "@/lib/api"
import type { DashboardAnalytics } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { RiskBadge } from "@/components/shared/RiskBadge"
import {
  RiskDonut,
  PerformanceTrendChart,
  AttendanceScatter,
  SubjectBarChart,
} from "@/components/charts"
import { useAuth } from "@/context/AuthContext"
import { formatNumber, formatPercent } from "@/lib/utils"

function greeting() {
  const h = new Date().getHours()
  if (h < 12) return "Good morning"
  if (h < 17) return "Good afternoon"
  return "Good evening"
}

function KpiCard({
  title,
  value,
  sub,
  icon: Icon,
  color,
  loading,
}: {
  title: string
  value: string
  sub?: string
  icon: React.ElementType
  color: string
  loading: boolean
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
      <Card>
        <CardContent className="p-5">
          {loading ? (
            <Skeleton className="h-14 w-full" />
          ) : (
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-[var(--muted-foreground)]">{title}</p>
                <p className="mt-1.5 text-2xl font-bold tracking-tight">{value}</p>
                {sub && <p className="mt-0.5 text-xs text-[var(--muted-foreground)]">{sub}</p>}
              </div>
              <div
                className="flex h-9 w-9 items-center justify-center rounded-lg"
                style={{ background: `${color}18`, color }}
              >
                <Icon className="h-4.5 w-4.5" />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-analytics"],
    queryFn: () => api.get<DashboardAnalytics>("/analytics/dashboard"),
  })

  const firstName = (user?.full_name ?? "Professor").split(" ")[0]
  const k = data?.kpis

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {greeting()}, {firstName}
        </h1>
        <p className="mt-1 text-sm text-[var(--muted-foreground)]">
          Here's an overview of your students' academic health.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          Failed to load dashboard data: {error.message}
        </div>
      )}

      {/* KPI grid */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <KpiCard title="Total Students" value={String(k?.total_students ?? 0)} icon={Users} color="#6366f1" loading={isLoading} />
        <KpiCard title="High Risk" value={String(k?.high_risk ?? 0)} icon={ShieldAlert} color="#ef4444" loading={isLoading} />
        <KpiCard title="Moderate Risk" value={String(k?.moderate_risk ?? 0)} icon={ShieldX} color="#f59e0b" loading={isLoading} />
        <KpiCard title="Low Risk" value={String(k?.low_risk ?? 0)} icon={ShieldCheck} color="#10b981" loading={isLoading} />
        <KpiCard title="Avg Performance" value={k ? formatNumber(k.average_performance) : "—"} icon={Gauge} color="#8b5cf6" loading={isLoading} />
        <KpiCard title="Avg Attendance" value={k ? formatNumber(k.average_attendance) : "—"} icon={CalendarCheck} color="#0ea5e9" loading={isLoading} />
      </div>

      {/* Charts row 1 */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Performance Trend</CardTitle>
            <CardDescription>Average academic score across semesters</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[260px] w-full" />
            ) : (
              <PerformanceTrendChart data={data?.performance_trend ?? []} />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Distribution</CardTitle>
            <CardDescription>Students by current risk level</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[240px] w-full" />
            ) : (
              <>
                <RiskDonut data={data?.risk_distribution ?? []} />
                <div className="mt-2 space-y-1.5">
                  {data?.risk_distribution.map((d) => (
                    <div key={d.name} className="flex items-center justify-between text-sm">
                      <span className="text-[var(--muted-foreground)]">{d.name}</span>
                      <span className="font-semibold">{d.value}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts row 2 */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Attendance vs Performance</CardTitle>
            <CardDescription>
              {data?.correlations.attendance_performance !== undefined ? (
                <>
                  Correlation:{" "}
                  <span className="font-semibold text-[var(--foreground)]">
                    {data.correlations.attendance_performance.toFixed(2)}
                  </span>
                </>
              ) : null}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[260px] w-full" />
            ) : (
              <AttendanceScatter data={data?.attendance_performance_scatter ?? []} />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Subject Performance</CardTitle>
            <CardDescription>Average score per subject</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[260px] w-full" />
            ) : (
              <SubjectBarChart data={data?.subject_performance ?? []} />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Attention table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              Students Requiring Attention
            </CardTitle>
            <CardDescription>High-risk students sorted by risk probability</CardDescription>
          </div>
          <button
            className="flex items-center gap-1 text-sm text-[var(--primary)] hover:underline"
            onClick={() => navigate("/students?risk=high")}
          >
            View all <ArrowUpRight className="h-3.5 w-3.5" />
          </button>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] text-left text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
                  <th className="px-5 py-3 font-medium">Student</th>
                  <th className="px-4 py-3 font-medium">Attendance</th>
                  <th className="px-4 py-3 font-medium">Avg Score</th>
                  <th className="px-4 py-3 font-medium">Engagement</th>
                  <th className="px-4 py-3 font-medium">Risk Probability</th>
                  <th className="px-4 py-3 font-medium">Risk Level</th>
                  <th className="px-5 py-3 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {(data?.students_requiring_attention ?? []).slice(0, 8).map((s) => (
                  <tr
                    key={s.id}
                    className="cursor-pointer border-b border-[var(--border)] transition-colors last:border-0 hover:bg-[var(--muted)]"
                    onClick={() => navigate(`/students/${s.id}`)}
                  >
                    <td className="px-5 py-3">
                      <div>
                        <p className="font-medium">{s.name}</p>
                        <p className="text-xs text-[var(--muted-foreground)]">{s.student_id}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3">{formatNumber(s.attendance)}%</td>
                    <td className="px-4 py-3">{formatNumber(s.average_score)}%</td>
                    <td className="px-4 py-3">{formatNumber(s.engagement)}%</td>
                    <td className="px-4 py-3 font-semibold text-red-500">
                      {formatPercent(s.risk_probability, 1)}
                    </td>
                    <td className="px-4 py-3">
                      <RiskBadge level={s.risk_level} />
                    </td>
                    <td className="px-5 py-3 text-right">
                      <button className="text-xs font-medium text-[var(--primary)] hover:underline">
                        Open profile
                      </button>
                    </td>
                  </tr>
                ))}
                {!isLoading && (data?.students_requiring_attention ?? []).length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-5 py-10 text-center text-sm text-[var(--muted-foreground)]">
                      <Activity className="mx-auto mb-2 h-6 w-6 opacity-50" />
                      No high-risk students right now. Great work!
                    </td>
                  </tr>
                )}
                {isLoading && (
                  <tr>
                    <td colSpan={7} className="px-5 py-10">
                      <Skeleton className="h-10 w-full" />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
