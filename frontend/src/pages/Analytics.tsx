import { useQuery } from "@tanstack/react-query"
import {
  Users,
  Gauge,
  CalendarCheck,
  AlertTriangle,
  Sparkles,
  TrendingUp,
} from "lucide-react"
import { api } from "@/lib/api"
import type { DashboardAnalytics } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  RiskDonut,
  PerformanceTrendChart,
  AttendanceScatter,
  SubjectBarChart,
  ScoreDistributionChart,
  EngagementBar,
} from "@/components/charts"
import { formatNumber } from "@/lib/utils"

export default function Analytics() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics"],
    queryFn: () => api.get<DashboardAnalytics>("/analytics/dashboard"),
  })

  const k = data?.kpis

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="mt-1 text-sm text-[var(--muted-foreground)]">
          Advanced insights computed from your institution's data.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          {error.message}
        </div>
      )}

      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        {[
          { label: "Total Students", value: String(k?.total_students ?? "—"), icon: Users, color: "#6366f1" },
          { label: "Avg Score", value: k ? formatNumber(k.average_performance) : "—", icon: Gauge, color: "#8b5cf6" },
          { label: "Avg Attendance", value: k ? formatNumber(k.average_attendance) : "—", icon: CalendarCheck, color: "#0ea5e9" },
          { label: "Avg Engagement", value: k ? formatNumber(k.average_engagement) : "—", icon: Sparkles, color: "#ec4899" },
          { label: "Below Att. Threshold", value: String(k?.below_attendance_threshold ?? "—"), icon: AlertTriangle, color: "#ef4444" },
          { label: "Att ↔ Perf Corr", value: data ? data.correlations.attendance_performance.toFixed(2) : "—", icon: TrendingUp, color: "#10b981" },
        ].map((s) => (
          <Card key={s.label}>
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium text-[var(--muted-foreground)]">{s.label}</p>
                  <p className="mt-1.5 text-2xl font-bold">{isLoading ? "—" : s.value}</p>
                </div>
                <div className="flex h-9 w-9 items-center justify-center rounded-lg" style={{ background: `${s.color}18`, color: s.color }}>
                  <s.icon className="h-4 w-4" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Distribution charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Risk Distribution</CardTitle>
            <CardDescription>High / moderate / low risk students</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-[240px] w-full" /> : <RiskDonut data={data?.risk_distribution ?? []} />}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Score Distribution</CardTitle>
            <CardDescription>Average score buckets</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-[240px] w-full" /> : <ScoreDistributionChart data={data?.score_distribution ?? []} />}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Engagement Distribution</CardTitle>
            <CardDescription>Engagement buckets across the cohort</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-[240px] w-full" /> : <EngagementBar data={data?.engagement_distribution ?? []} />}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Performance Trend</CardTitle>
            <CardDescription>Average score per semester</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-[240px] w-full" /> : <PerformanceTrendChart data={data?.performance_trend ?? []} />}
          </CardContent>
        </Card>
      </div>

      {/* Correlations */}
      <Card>
        <CardHeader>
          <CardTitle>Attendance vs Performance</CardTitle>
          <CardDescription>
            Pearson correlation:{" "}
            <span className="font-semibold text-[var(--foreground)]">
              {data ? data.correlations.attendance_performance.toFixed(3) : "—"}
            </span>{" "}
            · Engagement ↔ Performance:{" "}
            <span className="font-semibold text-[var(--foreground)]">
              {data ? data.correlations.engagement_performance.toFixed(3) : "—"}
            </span>
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-[260px] w-full" /> : <AttendanceScatter data={data?.attendance_performance_scatter ?? []} />}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Subject Performance</CardTitle>
          <CardDescription>Average score and record count per subject</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-[260px] w-full" /> : <SubjectBarChart data={data?.subject_performance ?? []} />}
        </CardContent>
      </Card>
    </div>
  )
}
