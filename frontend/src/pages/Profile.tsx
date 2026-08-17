import { useQuery } from "@tanstack/react-query"
import { UserRound, Mail, Building2, BadgeCheck } from "lucide-react"
import { api } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/context/AuthContext"

export default function Profile() {
  const { user } = useAuth()

  const { data: faculty } = useQuery({
    queryKey: ["faculty-me"],
    queryFn: () => api.get<{ employee_id: string; designation: string; department: string | null; full_name: string; email: string }>("/faculty/me"),
    enabled: user?.role === "faculty" || user?.role === "admin",
  })

  const { data: student } = useQuery({
    queryKey: ["student-me"],
    queryFn: () =>
      api.get<{ student_id: string; full_name: string; department_name: string | null; section_name: string | null; current_semester: number }>("/student/me"),
    enabled: user?.role === "student",
  })

  if (!user) return <Skeleton className="h-64 w-full" />

  const initials = user.full_name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase()

  const rows: { label: string; value: string | undefined; icon: React.ElementType }[] = [
    { label: "Full name", value: user.full_name, icon: UserRound },
    { label: "Email", value: user.email, icon: Mail },
    { label: "Role", value: user.role, icon: BadgeCheck },
    ...(faculty
      ? [
          { label: "Employee ID", value: faculty.employee_id, icon: BadgeCheck },
          { label: "Designation", value: faculty.designation, icon: Building2 },
          { label: "Department", value: faculty.department ?? undefined, icon: Building2 },
        ]
      : []),
    ...(student
      ? [
          { label: "Student ID", value: student.student_id, icon: BadgeCheck },
          { label: "Department", value: student.department_name ?? undefined, icon: Building2 },
          { label: "Section", value: student.section_name ?? undefined, icon: Building2 },
          { label: "Semester", value: String(student.current_semester), icon: UserRound },
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
              <span className="font-medium capitalize">{r.value}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
