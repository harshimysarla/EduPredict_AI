import { useQuery } from "@tanstack/react-query"
import { UserRound, Mail, Building2, BadgeCheck, CalendarDays, Layers, Gauge, BookOpenCheck } from "lucide-react"
import { api } from "@/lib/api"
import { portalService } from "@/services/portalService"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { useAuth } from "@/context/AuthContext"

export default function Profile() {
  const { user } = useAuth()

  const { data: faculty } = useQuery({
    queryKey: ["faculty-me"],
    queryFn: () => api.get<{ employee_id: string; designation: string; department: string | null; full_name: string; email: string }>("/faculty/me"),
    enabled: user?.role === "faculty" || user?.role === "admin",
  })

  const { data: portal } = useQuery({
    queryKey: ["portal-profile"],
    queryFn: portalService.profile,
    enabled: user?.role === "student",
  })

  if (!user) return <Skeleton className="h-64 w-full" />

  const initials = user.full_name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase()

  if (user.role === "student" && portal) {
    const credits = portal.creditProgress
    const rows: { label: string; value: string | undefined; icon: React.ElementType }[] = [
      { label: "Full name", value: portal.name, icon: UserRound },
      { label: "Roll number", value: portal.rollNumber ?? portal.studentId, icon: BadgeCheck },
      { label: "Username", value: user.username, icon: UserRound },
      ...(user.email ? [{ label: "Email", value: user.email, icon: Mail }] : []),
      { label: "Branch", value: portal.branch, icon: Building2 },
      { label: "Regulation", value: portal.regulation, icon: BadgeCheck },
      { label: "Section", value: portal.section, icon: Building2 },
      { label: "Year", value: portal.year != null ? String(portal.year) : undefined, icon: CalendarDays },
      { label: "Current semester", value: portal.currentSemester != null ? String(portal.currentSemester) : undefined, icon: Layers },
    ]

    return (
      <div className="space-y-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Profile</h1>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">Your academic portal profile</p>
        </div>

        <Card>
          <CardContent className="flex flex-wrap items-center gap-5 p-6">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="text-lg">{initials}</AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-lg font-bold">{portal.name}</p>
                {portal.placeholder && <Badge variant="warning">DEMO DATA</Badge>}
              </div>
              <p className="text-sm text-[var(--muted-foreground)]">
                {portal.branch} · {portal.rollNumber} · Section {portal.section} · {portal.regulation}
              </p>
            </div>
            <div className="flex gap-6 text-center">
              <div>
                <p className="text-2xl font-bold">{portal.cgpa != null ? portal.cgpa.toFixed(2) : "—"}</p>
                <p className="text-[11px] text-[var(--muted-foreground)]">CGPA</p>
              </div>
              <div>
                <p className="text-2xl font-bold">{portal.performanceIndex}</p>
                <p className="text-[11px] text-[var(--muted-foreground)]">Performance Index</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
                <Gauge className="h-3.5 w-3.5" /> Performance Index
              </div>
              <p className="mt-1.5 text-2xl font-bold">{portal.performanceIndex}</p>
              <Progress value={portal.performanceIndex} className="mt-2 h-1.5" indicatorStyle={{ backgroundColor: "#6366f1" }} />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
                <Layers className="h-3.5 w-3.5" /> Credits Completed
              </div>
              <p className="mt-1.5 text-2xl font-bold">
                {credits.completedCredits}<span className="text-base text-[var(--muted-foreground)]">/{credits.programTotalCredits}</span>
              </p>
              <Progress value={credits.completionPercent} className="mt-2 h-1.5" indicatorStyle={{ backgroundColor: "#10b981" }} />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
                <BookOpenCheck className="h-3.5 w-3.5" /> Credits Remaining
              </div>
              <p className="mt-1.5 text-2xl font-bold">{credits.remainingCredits}</p>
              <Progress value={credits.completionPercent} className="mt-2 h-1.5" indicatorStyle={{ backgroundColor: "#8b5cf6" }} />
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Account information</CardTitle>
            <CardDescription>Details associated with your portal account</CardDescription>
          </CardHeader>
          <CardContent className="divide-y divide-[var(--border)]">
            {rows.map((r) => (
              <div key={r.label} className="flex items-center justify-between py-3 text-sm">
                <span className="flex items-center gap-2 text-[var(--muted-foreground)]">
                  <r.icon className="h-4 w-4" /> {r.label}
                </span>
                <span className="font-medium capitalize">{r.value ?? "—"}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    )
  }

  const rows: { label: string; value: string | undefined; icon: React.ElementType }[] = [
    { label: "Full name", value: user.full_name, icon: UserRound },
    { label: "Username", value: user.username, icon: UserRound },
    ...(user.email ? [{ label: "Email", value: user.email, icon: Mail }] : []),
    { label: "Role", value: user.role, icon: BadgeCheck },
    ...(faculty
      ? [
          { label: "Employee ID", value: faculty.employee_id, icon: BadgeCheck },
          { label: "Designation", value: faculty.designation, icon: Building2 },
          { label: "Department", value: faculty.department ?? undefined, icon: Building2 },
        ]
      : []),
  ]

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Profile</h1>
        <p className="mt-1 text-sm text-[var(--muted-foreground)]">Your account details</p>
      </div>

      <Card>
        <CardContent className="flex items-center gap-5 p-6">
          <Avatar className="h-16 w-16">
            <AvatarFallback className="text-lg">{initials}</AvatarFallback>
          </Avatar>
          <div>
            <p className="text-lg font-bold">{user.full_name}</p>
            <p className="text-sm capitalize text-[var(--muted-foreground)]">{user.role}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Account information</CardTitle>
          <CardDescription>Details associated with your EduPredict AI account</CardDescription>
        </CardHeader>
        <CardContent className="divide-y divide-[var(--border)]">
          {rows.map((r) => (
            <div key={r.label} className="flex items-center justify-between py-3 text-sm">
              <span className="flex items-center gap-2 text-[var(--muted-foreground)]">
                <r.icon className="h-4 w-4" /> {r.label}
              </span>
              <span className="font-medium capitalize">{r.value ?? "—"}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}