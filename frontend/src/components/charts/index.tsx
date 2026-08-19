import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ScatterChart,
  Scatter,
  ZAxis,
  BarChart,
  Bar,
  Legend,
  ReferenceLine,
} from "recharts"

import type { PortalAttendanceRow } from "@/types"

export const CHART_COLORS = {
  primary: "#6366f1",
  emerald: "#10b981",
  amber: "#f59e0b",
  red: "#ef4444",
  sky: "#0ea5e9",
  violet: "#8b5cf6",
  slate: "#94a3b8",
  pink: "#ec4899",
}

const axisStyle = {
  fontSize: 11,
  fill: "var(--muted-foreground)",
}

export function RiskDonut({
  data,
}: {
  data: { name: string; value: number; level: string }[]
}) {
  const colors: Record<string, string> = {
    low: CHART_COLORS.emerald,
    moderate: CHART_COLORS.amber,
    high: CHART_COLORS.red,
  }
  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={60}
          outerRadius={90}
          paddingAngle={3}
          strokeWidth={0}
        >
          {data.map((d) => (
            <Cell key={d.name} fill={colors[d.level] ?? CHART_COLORS.slate} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}

export function PerformanceTrendChart({
  data,
}: {
  data: { semester: number; average: number }[]
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="semester" tick={axisStyle} label={{ value: "Semester", position: "insideBottom", offset: -4, fontSize: 11, fill: "var(--muted-foreground)" }} />
        <YAxis domain={[0, 100]} tick={axisStyle} />
        <Tooltip
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <Line
          type="monotone"
          dataKey="average"
          name="Average Score"
          stroke={CHART_COLORS.primary}
          strokeWidth={2.5}
          dot={{ r: 4, fill: CHART_COLORS.primary }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function AttendanceScatter({
  data,
}: {
  data: { student: string; student_id: string; attendance: number; score: number }[]
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <ScatterChart margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis
          dataKey="attendance"
          name="Attendance"
          domain={[0, 100]}
          tick={axisStyle}
          label={{ value: "Attendance %", position: "insideBottom", offset: -4, fontSize: 11, fill: "var(--muted-foreground)" }}
        />
        <YAxis
          dataKey="score"
          name="Score"
          domain={[0, 100]}
          tick={axisStyle}
          label={{ value: "Avg Score", angle: -90, position: "insideLeft", fontSize: 11, fill: "var(--muted-foreground)" }}
        />
        <ZAxis range={[40, 40]} />
        <Tooltip
          cursor={{ strokeDasharray: "3 3" }}
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <Scatter data={data} fill={CHART_COLORS.primary} fillOpacity={0.6} />
      </ScatterChart>
    </ResponsiveContainer>
  )
}

export function SubjectBarChart({
  data,
}: {
  data: { subject: string; average: number }[]
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 12, left: -18, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis
          dataKey="subject"
          tick={axisStyle}
          interval={0}
          angle={-30}
          textAnchor="end"
          height={60}
        />
        <YAxis domain={[0, 100]} tick={axisStyle} />
        <Tooltip
          cursor={{ fill: "var(--muted)", opacity: 0.4 }}
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <Bar dataKey="average" name="Avg Score" fill={CHART_COLORS.violet} radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function ScoreDistributionChart({
  data,
}: {
  data: { range: string; count: number }[]
}) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="range" tick={axisStyle} />
        <YAxis tick={axisStyle} allowDecimals={false} />
        <Tooltip
          cursor={{ fill: "var(--muted)", opacity: 0.4 }}
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <Bar dataKey="count" name="Students" fill={CHART_COLORS.sky} radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function EngagementBar({
  data,
}: {
  data: { name: string; value: number }[]
}) {
  const colors = [CHART_COLORS.red, CHART_COLORS.amber, CHART_COLORS.emerald]
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="name" tick={axisStyle} />
        <YAxis tick={axisStyle} allowDecimals={false} />
        <Tooltip
          cursor={{ fill: "var(--muted)", opacity: 0.4 }}
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <Bar dataKey="value" name="Students" radius={[6, 6, 0, 0]}>
          {data.map((d, i) => (
            <Cell key={d.name} fill={colors[i % colors.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function BeforeAfterChart({
  before,
  after,
}: {
  before: { risk: number | null; performance: number | null; attendance: number | null }
  after: { risk: number | null; performance: number | null; attendance: number | null }
}) {
  const data = [
    {
      name: "Risk Probability",
      Before: before.risk !== null ? +(before.risk * 100).toFixed(1) : 0,
      After: after.risk !== null ? +(after.risk * 100).toFixed(1) : 0,
    },
    {
      name: "Performance",
      Before: before.performance ?? 0,
      After: after.performance ?? 0,
    },
    {
      name: "Attendance",
      Before: before.attendance ?? 0,
      After: after.attendance ?? 0,
    },
  ]
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="name" tick={axisStyle} />
        <YAxis domain={[0, 100]} tick={axisStyle} />
        <Tooltip
          cursor={{ fill: "var(--muted)", opacity: 0.4 }}
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <Legend />
        <Bar dataKey="Before" fill={CHART_COLORS.red} radius={[6, 6, 0, 0]} />
        <Bar dataKey="After" fill={CHART_COLORS.emerald} radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function PredictionTrendChart({
  data,
}: {
  data: { date: string; probability: number }[]
}) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis
          dataKey="date"
          tick={axisStyle}
          tickFormatter={(d: string) => new Date(d).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
        />
        <YAxis domain={[0, 1]} tick={axisStyle} tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`} />
        <Tooltip
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
          formatter={(v) => `${(Number(v) * 100).toFixed(1)}%`}
        />
        <Line
          type="monotone"
          dataKey="probability"
          name="Risk Probability"
          stroke={CHART_COLORS.primary}
          strokeWidth={2.5}
          dot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function CgpaTrendChart({
  data,
}: {
  data: { label: string; sgpa: number | null; cgpa: number | null; completed: boolean }[]
}) {
  const points = data.map((d) => ({
    label: d.completed ? d.label : `${d.label}*`,
    sgpa: d.completed ? d.sgpa : null,
    cgpa: d.completed ? d.cgpa : null,
  }))
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={points} margin={{ top: 8, right: 16, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="label" tick={axisStyle} />
        <YAxis domain={[0, 10]} tick={axisStyle} />
        <Tooltip
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="sgpa"
          name="SGPA"
          stroke={CHART_COLORS.primary}
          strokeWidth={2.5}
          connectNulls={false}
          dot={{ r: 4, fill: CHART_COLORS.primary }}
        />
        <Line
          type="monotone"
          dataKey="cgpa"
          name="CGPA"
          stroke={CHART_COLORS.emerald}
          strokeWidth={2.5}
          connectNulls={false}
          dot={{ r: 4, fill: CHART_COLORS.emerald }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function AttendanceBarsChart({
  data,
}: {
  data: PortalAttendanceRow[]
}) {
  const chartData = data.map((d) => ({
    course: d.courseCode ?? d.courseName ?? "—",
    attendancePercentage: d.attendancePercentage ?? 0,
  }))
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} margin={{ top: 8, right: 16, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="course" tick={axisStyle} angle={-30} textAnchor="end" interval={0} height={60} />
        <YAxis domain={[0, 100]} tick={axisStyle} />
        <Tooltip
          cursor={{ fill: "var(--muted)", opacity: 0.4 }}
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <ReferenceLine y={85} stroke={CHART_COLORS.emerald} strokeDasharray="4 4" label={{ value: "85%", fontSize: 10, fill: CHART_COLORS.emerald, position: "insideTopRight" }} />
        <ReferenceLine y={75} stroke={CHART_COLORS.amber} strokeDasharray="4 4" label={{ value: "75%", fontSize: 10, fill: CHART_COLORS.amber, position: "insideTopRight" }} />
        <ReferenceLine y={65} stroke={CHART_COLORS.red} strokeDasharray="4 4" label={{ value: "65%", fontSize: 10, fill: CHART_COLORS.red, position: "insideTopRight" }} />
        <Bar
          dataKey="attendancePercentage"
          name="Attendance %"
          radius={[6, 6, 0, 0]}
        >
          {chartData.map((d, i) => {
            const pct = d.attendancePercentage ?? 0
            const color =
              pct >= 85 ? CHART_COLORS.emerald : pct >= 75 ? CHART_COLORS.primary : pct >= 65 ? CHART_COLORS.amber : CHART_COLORS.red
            return <Cell key={i} fill={color} />
          })}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
