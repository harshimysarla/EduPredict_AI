import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { LifeBuoy, CalendarClock, CheckCircle2 } from "lucide-react"
import { api } from "@/lib/api"
import type { Intervention } from "@/types"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { Spinner } from "@/components/ui/spinner"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useState } from "react"
import { formatDate } from "@/lib/utils"

const statusVariant: Record<string, "success" | "warning" | "info" | "destructive" | "secondary"> = {
  completed: "success",
  in_progress: "info",
  pending: "warning",
  cancelled: "destructive",
}

export default function Interventions() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState("all")

  const { data, isLoading } = useQuery({
    queryKey: ["interventions", statusFilter],
    queryFn: () =>
      api.get<Intervention[]>(
        `/interventions${statusFilter !== "all" ? `?status=${statusFilter}` : ""}`,
      ),
  })

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      api.put(`/interventions/${id}`, { status }),
    onSuccess: (_, vars) => {
      toast.success(
        vars.status === "completed"
          ? "Intervention completed. Impact tracking updated."
          : "Status updated",
      )
      queryClient.invalidateQueries({ queryKey: ["interventions"] })
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Update failed"),
  })

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Interventions</h1>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            Track intervention plans and measure their impact on student outcomes.
          </p>
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
      ) : !data?.length ? (
        <EmptyState
          icon={LifeBuoy}
          title="No interventions found"
          description="Interventions created from student profiles will appear here."
          action={
            <Button onClick={() => navigate("/students")}>
              Browse students
            </Button>
          }
        />
      ) : (
        <div className="space-y-3">
          {data.map((iv) => (
            <Card key={iv.id}>
              <CardContent className="p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold">{iv.title}</p>
                      <Badge variant="secondary" className="capitalize">
                        {iv.type.replace(/_/g, " ")}
                      </Badge>
                      <Badge variant={statusVariant[iv.status] ?? "secondary"} className="capitalize">
                        {iv.status.replace(/_/g, " ")}
                      </Badge>
                    </div>
                    {iv.description && (
                      <p className="mt-1.5 text-sm text-[var(--muted-foreground)]">{iv.description}</p>
                    )}
                    <div className="mt-2.5 flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-[var(--muted-foreground)]">
                      <button
                        className="font-medium text-[var(--primary)] hover:underline"
                        onClick={() => navigate(`/students/${iv.student_id}`)}
                      >
                        {iv.student_name} ({iv.student_id_str})
                      </button>
                      <span>Faculty: {iv.faculty_name}</span>
                      <span className="flex items-center gap-1">
                        <CalendarClock className="h-3 w-3" /> Assigned {formatDate(iv.assigned_date)}
                      </span>
                      {iv.follow_up_date && <span>Follow-up {formatDate(iv.follow_up_date)}</span>}
                      {iv.completed_date && (
                        <span className="flex items-center gap-1 text-emerald-500">
                          <CheckCircle2 className="h-3 w-3" /> Completed {formatDate(iv.completed_date)}
                        </span>
                      )}
                    </div>
                    {iv.notes && (
                      <p className="mt-2 rounded-md bg-[var(--muted)] px-3 py-2 text-xs text-[var(--muted-foreground)]">
                        {iv.notes}
                      </p>
                    )}
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    {iv.status !== "completed" && iv.status !== "cancelled" && (
                      <>
                        <Select
                          value={iv.status}
                          onValueChange={(v) => updateStatus.mutate({ id: iv.id, status: v })}
                        >
                          <SelectTrigger className="h-8 w-32 text-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="pending">Pending</SelectItem>
                            <SelectItem value="in_progress">In Progress</SelectItem>
                            <SelectItem value="completed">Completed</SelectItem>
                            <SelectItem value="cancelled">Cancelled</SelectItem>
                          </SelectContent>
                        </Select>
                        {updateStatus.isPending && <Spinner className="h-4 w-4" />}
                      </>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/students/${iv.student_id}?tab=interventions`)}
                    >
                      Open student
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
