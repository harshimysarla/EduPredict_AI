import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Building2, Users2, BookOpen, UserPlus, Plus } from "lucide-react"
import { api } from "@/lib/api"
import type { Department, Section, Subject } from "@/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useAuth } from "@/context/AuthContext"

export default function Settings() {
  const { user } = useAuth()

  if (user?.role !== "admin") {
    return (
      <div className="space-y-5">
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <Card>
          <CardContent className="p-6 text-sm text-[var(--muted-foreground)]">
            System configuration is managed by administrators. Your role ({user?.role}) does not have access to
            department, section, subject, or faculty management.
          </CardContent>
        </Card>
      </div>
    )
  }

  return <AdminSettings />
}

function AdminSettings() {
  const queryClient = useQueryClient()
  const [deptOpen, setDeptOpen] = useState(false)
  const [secOpen, setSecOpen] = useState(false)
  const [subjOpen, setSubjOpen] = useState(false)
  const [facOpen, setFacOpen] = useState(false)

  const [deptName, setDeptName] = useState("")
  const [deptCode, setDeptCode] = useState("")

  const [secName, setSecName] = useState("")
  const [secDept, setSecDept] = useState("")
  const [secYear, setSecYear] = useState("2025-2026")
  const [secSem, setSecSem] = useState("1")

  const [subjName, setSubjName] = useState("")
  const [subjCode, setSubjCode] = useState("")
  const [subjDept, setSubjDept] = useState("")
  const [subjSem, setSubjSem] = useState("1")

  const [facName, setFacName] = useState("")
  const [facUsername, setFacUsername] = useState("")
  const [facEmail, setFacEmail] = useState("")
  const [facPassword, setFacPassword] = useState("")
  const [facEmpId, setFacEmpId] = useState("")
  const [facDept, setFacDept] = useState("")

  const { data: departments, isLoading: deptLoading } = useQuery({
    queryKey: ["departments"],
    queryFn: () => api.get<Department[]>("/departments"),
  })
  const { data: sections, isLoading: secLoading } = useQuery({
    queryKey: ["sections"],
    queryFn: () => api.get<Section[]>("/sections"),
  })
  const { data: subjects, isLoading: subjLoading } = useQuery({
    queryKey: ["subjects"],
    queryFn: () => api.get<Subject[]>("/subjects"),
  })
  const { data: dataSources } = useQuery({
    queryKey: ["data-sources"],
    queryFn: () =>
      api.get<{ name: string; type: string; status: string; display_name: string | null; last_synced_at: string | null; record_count: number | null }[]>("/admin/data-sources"),
  })
  const { data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: () =>
      api.get<{ key: string; value: string }[]>("/admin/settings"),
  })
  const [riskLow, setRiskLow] = useState(settings?.find((s) => s.key === "risk_low")?.value ?? "0.39")
  const [riskHigh, setRiskHigh] = useState(settings?.find((s) => s.key === "risk_high")?.value ?? "0.69")
  const activate = useMutation({
    mutationFn: (type: string) => api.post(`/admin/data-sources/${type}/activate`),
    onSuccess: () => {
      toast.success("Data source activated")
      queryClient.invalidateQueries({ queryKey: ["data-sources"] })
      queryClient.invalidateQueries({ queryKey: ["data-source"] })
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Activation failed"),
  })
  const saveLow = useMutation({
    mutationFn: (value: string) => api.put(`/admin/settings/risk_low`, { value }),
    onSuccess: () => {
      toast.success("Risk thresholds saved")
      queryClient.invalidateQueries({ queryKey: ["settings"] })
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Save failed"),
  })
  const saveHigh = useMutation({
    mutationFn: (value: string) => api.put(`/admin/settings/risk_high`, { value }),
    onSuccess: () => {
      toast.success("Risk thresholds saved")
      queryClient.invalidateQueries({ queryKey: ["settings"] })
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Save failed"),
  })

  const mutation = useMutation({
    mutationFn: ({ path, body }: { path: string; body: Record<string, unknown> }) =>
      api.post(path, body),
    onSuccess: () => {
      toast.success("Created successfully")
      queryClient.invalidateQueries({ queryKey: ["departments"] })
      queryClient.invalidateQueries({ queryKey: ["sections"] })
      queryClient.invalidateQueries({ queryKey: ["subjects"] })
      setDeptOpen(false)
      setSecOpen(false)
      setSubjOpen(false)
      setFacOpen(false)
      setDeptName(""); setDeptCode("")
      setSecName(""); setSecDept("")
      setSubjName(""); setSubjCode(""); setSubjDept("")
      setFacName(""); setFacUsername(""); setFacEmail(""); setFacPassword(""); setFacEmpId(""); setFacDept("")
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Creation failed"),
  })

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-[var(--muted-foreground)]">
          Admin controls for departments, sections, subjects, and faculty accounts.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Departments */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-[var(--primary)]" /> Departments
              </CardTitle>
              <CardDescription>{departments?.length ?? 0} department(s)</CardDescription>
            </div>
            <Button size="sm" onClick={() => setDeptOpen(true)}>
              <Plus className="h-4 w-4" /> Add
            </Button>
          </CardHeader>
          <CardContent>
            {deptLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : (
              <div className="space-y-1.5">
                {departments?.map((d) => (
                  <div key={d.id} className="flex items-center justify-between rounded-lg border border-[var(--border)] px-3 py-2 text-sm">
                    <span className="font-medium">{d.name}</span>
                    <span className="text-xs text-[var(--muted-foreground)]">{d.code}</span>
                  </div>
                ))}
                {!departments?.length && <EmptyState title="No departments" />}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sections */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users2 className="h-4 w-4 text-[var(--primary)]" /> Sections
              </CardTitle>
              <CardDescription>{sections?.length ?? 0} section(s)</CardDescription>
            </div>
            <Button size="sm" onClick={() => setSecOpen(true)}>
              <Plus className="h-4 w-4" /> Add
            </Button>
          </CardHeader>
          <CardContent>
            {secLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : (
              <div className="max-h-48 space-y-1.5 overflow-y-auto">
                {sections?.map((s) => (
                  <div key={s.id} className="flex items-center justify-between rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm">
                    <span className="font-medium">{s.name}</span>
                    <span className="text-xs text-[var(--muted-foreground)]">
                      {s.academic_year} · Sem {s.semester}
                    </span>
                  </div>
                ))}
                {!sections?.length && <EmptyState title="No sections" />}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Subjects */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-[var(--primary)]" /> Subjects
              </CardTitle>
              <CardDescription>{subjects?.length ?? 0} subject(s)</CardDescription>
            </div>
            <Button size="sm" onClick={() => setSubjOpen(true)}>
              <Plus className="h-4 w-4" /> Add
            </Button>
          </CardHeader>
          <CardContent>
            {subjLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : (
              <div className="max-h-48 space-y-1.5 overflow-y-auto">
                {subjects?.map((s) => (
                  <div key={s.id} className="flex items-center justify-between rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm">
                    <span className="font-medium">{s.name}</span>
                    <span className="text-xs text-[var(--muted-foreground)]">{s.code}</span>
                  </div>
                ))}
                {!subjects?.length && <EmptyState title="No subjects" />}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Faculty */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <UserPlus className="h-4 w-4 text-[var(--primary)]" /> Faculty
              </CardTitle>
              <CardDescription>Create faculty accounts</CardDescription>
            </div>
            <Button size="sm" onClick={() => setFacOpen(true)}>
              <Plus className="h-4 w-4" /> Add
            </Button>
          </CardHeader>
          <CardContent className="text-sm text-[var(--muted-foreground)]">
            Faculty accounts receive role-based access to student data, predictions, interventions, and analytics.
          </CardContent>
        </Card>
      </div>

      {/* Department dialog */}
      <Dialog open={deptOpen} onOpenChange={setDeptOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add department</DialogTitle>
            <DialogDescription>Create a new academic department</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label>Name</Label>
              <Input value={deptName} onChange={(e) => setDeptName(e.target.value)} placeholder="e.g. Computer Science & Engineering" />
            </div>
            <div className="space-y-1.5">
              <Label>Code</Label>
              <Input value={deptCode} onChange={(e) => setDeptCode(e.target.value)} placeholder="e.g. CSE" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeptOpen(false)}>Cancel</Button>
            <Button onClick={() => mutation.mutate({ path: "/admin/departments", body: { name: deptName, code: deptCode } })}>
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Section dialog */}
      <Dialog open={secOpen} onOpenChange={setSecOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add section</DialogTitle>
            <DialogDescription>Create a new section</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label>Name</Label>
              <Input value={secName} onChange={(e) => setSecName(e.target.value)} placeholder="e.g. CSE-A" />
            </div>
            <div className="space-y-1.5">
              <Label>Department</Label>
              <Select value={secDept} onValueChange={setSecDept}>
                <SelectTrigger><SelectValue placeholder="Select department" /></SelectTrigger>
                <SelectContent>
                  {departments?.map((d) => (
                    <SelectItem key={d.id} value={String(d.id)}>{d.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Academic Year</Label>
                <Input value={secYear} onChange={(e) => setSecYear(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>Semester</Label>
                <Select value={secSem} onValueChange={setSecSem}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1</SelectItem>
                    <SelectItem value="2">2</SelectItem>
                    <SelectItem value="3">3</SelectItem>
                    <SelectItem value="4">4</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSecOpen(false)}>Cancel</Button>
            <Button
              onClick={() =>
                mutation.mutate({
                  path: "/admin/sections",
                  body: { name: secName, department_id: Number(secDept), academic_year: secYear, semester: Number(secSem) },
                })
              }
            >
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Subject dialog */}
      <Dialog open={subjOpen} onOpenChange={setSubjOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add subject</DialogTitle>
            <DialogDescription>Create a new subject</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label>Name</Label>
              <Input value={subjName} onChange={(e) => setSubjName(e.target.value)} placeholder="e.g. Machine Learning" />
            </div>
            <div className="space-y-1.5">
              <Label>Code</Label>
              <Input value={subjCode} onChange={(e) => setSubjCode(e.target.value)} placeholder="e.g. CSE204" />
            </div>
            <div className="space-y-1.5">
              <Label>Department</Label>
              <Select value={subjDept} onValueChange={setSubjDept}>
                <SelectTrigger><SelectValue placeholder="Select department" /></SelectTrigger>
                <SelectContent>
                  {departments?.map((d) => (
                    <SelectItem key={d.id} value={String(d.id)}>{d.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Semester</Label>
              <Select value={subjSem} onValueChange={setSubjSem}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1</SelectItem>
                  <SelectItem value="2">2</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSubjOpen(false)}>Cancel</Button>
            <Button
              onClick={() =>
                mutation.mutate({
                  path: "/admin/subjects",
                  body: { name: subjName, code: subjCode, department_id: Number(subjDept), semester: Number(subjSem) },
                })
              }
            >
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Faculty dialog */}
      <Dialog open={facOpen} onOpenChange={setFacOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add faculty</DialogTitle>
            <DialogDescription>Create a faculty account</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label>Full name</Label>
              <Input value={facName} onChange={(e) => setFacName(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>Username</Label>
              <Input value={facUsername} onChange={(e) => setFacUsername(e.target.value)} placeholder="e.g. faculty.ece" />
            </div>
            <div className="space-y-1.5">
              <Label>Email (optional)</Label>
              <Input type="email" value={facEmail} onChange={(e) => setFacEmail(e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Password</Label>
                <Input type="password" value={facPassword} onChange={(e) => setFacPassword(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>Employee ID</Label>
                <Input value={facEmpId} onChange={(e) => setFacEmpId(e.target.value)} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Department</Label>
              <Select value={facDept} onValueChange={setFacDept}>
                <SelectTrigger><SelectValue placeholder="Select department" /></SelectTrigger>
                <SelectContent>
                  {departments?.map((d) => (
                    <SelectItem key={d.id} value={String(d.id)}>{d.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setFacOpen(false)}>Cancel</Button>
            <Button
              onClick={() =>
                mutation.mutate({
                  path: "/admin/faculty",
                  body: {
                    full_name: facName,
                    username: facUsername,
                    email: facEmail || undefined,
                    password: facPassword,
                    employee_id: facEmpId,
                    department_id: Number(facDept),
                  },
                })
              }
            >
              Create faculty
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Data sources */}
      <Card>
        <CardHeader>
          <CardTitle>Data Sources</CardTitle>
          <CardDescription>
            Choose which academic data provider feeds dashboards and predictions.
            Demo data is synthetic; connect an approved CSV import for real records.
            Samvidha integration is planned but not yet configured.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          {dataSources?.map((ds) => {
            const statusColor =
              ds.status === "ACTIVE"
                ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                : ds.status === "NOT_CONFIGURED"
                  ? "border-red-500/40 bg-red-500/10 text-red-500"
                  : "border-[var(--border)] text-[var(--muted-foreground)]"
            return (
              <div key={ds.type} className="rounded-lg border border-[var(--border)] p-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold">{ds.display_name ?? ds.name}</p>
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${statusColor}`}>
                    {ds.status === "ACTIVE" ? "ACTIVE" : ds.status === "AVAILABLE" ? "READY" : "NOT CONFIGURED"}
                  </span>
                </div>
                <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                  {ds.record_count != null ? `${ds.record_count} academic records loaded` : "No records loaded"}
                  {ds.last_synced_at ? ` · synced ${new Date(ds.last_synced_at).toLocaleDateString()}` : ""}
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  className="mt-3 w-full"
                  disabled={ds.status === "ACTIVE" || ds.status === "NOT_CONFIGURED" || activate.isPending}
                  onClick={() => activate.mutate(ds.type)}
                >
                  {ds.status === "ACTIVE" ? "Currently Active" : ds.status === "NOT_CONFIGURED" ? "Not Available" : "Activate"}
                </Button>
              </div>
            )
          })}
        </CardContent>
      </Card>

      {/* Risk thresholds */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Thresholds</CardTitle>
          <CardDescription>
            Probability ranges that classify students as LOW / MODERATE / HIGH risk.
            Students above the high threshold are flagged for intervention.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label>Moderate risk threshold</Label>
            <Input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={riskLow}
              onChange={(e) => setRiskLow(e.target.value)}
              placeholder="0.39"
            />
            <p className="text-xs text-[var(--muted-foreground)]">
              Above this, students are classified as MODERATE risk.
            </p>
          </div>
          <div className="space-y-1.5">
            <Label>High risk threshold</Label>
            <Input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={riskHigh}
              onChange={(e) => setRiskHigh(e.target.value)}
              placeholder="0.69"
            />
            <p className="text-xs text-[var(--muted-foreground)]">
              Above this, students are classified as HIGH risk.
            </p>
          </div>
          <div className="md:col-span-2">
            <Button
              size="sm"
              disabled={saveLow.isPending || saveHigh.isPending}
              onClick={() => {
                saveLow.mutate(riskLow)
                saveHigh.mutate(riskHigh)
              }}
            >
              Save thresholds
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
