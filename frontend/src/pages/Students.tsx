import { useEffect, useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import {
  Search,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Users,
  UserPlus,
} from "lucide-react"
import { api } from "@/lib/api"
import type { StudentSummary, Department, Section } from "@/types"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { RiskBadge } from "@/components/shared/RiskBadge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { EmptyState } from "@/components/ui/empty-state"
import { formatDate, formatNumber, formatPercent } from "@/lib/utils"

const PAGE_SIZE = 20

export default function Students() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [search, setSearch] = useState("")
  const [debounced, setDebounced] = useState("")
  const [risk, setRisk] = useState(searchParams.get("risk") ?? "all")
  const [departmentId, setDepartmentId] = useState("all")
  const [sectionId, setSectionId] = useState("all")
  const [year, setYear] = useState("all")
  const [sort, setSort] = useState("risk_probability")
  const [order, setOrder] = useState<"asc" | "desc">("desc")
  const [page, setPage] = useState(1)

  useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 300)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => {
    setPage(1)
  }, [debounced, risk, departmentId, sectionId, year, sort, order])

  const params = new URLSearchParams()
  if (debounced) params.set("search", debounced)
  if (risk !== "all") params.set("risk", risk)
  if (departmentId !== "all") params.set("department_id", departmentId)
  if (sectionId !== "all") params.set("section_id", sectionId)
  if (year !== "all") params.set("year", year)
  params.set("sort", sort)
  params.set("order", order)
  params.set("page", String(page))
  params.set("page_size", String(PAGE_SIZE))

  const { data, isLoading, isFetching, error } = useQuery({
    queryKey: ["students", params.toString()],
    queryFn: () => api.get<StudentSummary[]>(`/students?${params.toString()}`),
    placeholderData: (prev) => prev,
  })

  const { data: departments } = useQuery({
    queryKey: ["departments"],
    queryFn: () => api.get<Department[]>("/departments"),
  })
  const { data: sections } = useQuery({
    queryKey: ["sections"],
    queryFn: () => api.get<Section[]>("/sections"),
  })

  const toggleSort = (key: string) => {
    if (sort === key) setOrder(order === "asc" ? "desc" : "asc")
    else {
      setSort(key)
      setOrder(key === "risk_probability" ? "desc" : "desc")
    }
  }

  const SortIcon = ({ column }: { column: string }) => {
    if (sort !== column) return <ArrowUpDown className="h-3 w-3 opacity-40" />
    return order === "asc" ? (
      <ArrowUp className="h-3 w-3" />
    ) : (
      <ArrowDown className="h-3 w-3" />
    )
  }

    const hasMore = (data?.length ?? 0) === PAGE_SIZE

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Students</h1>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            Search, filter, and inspect your student cohort.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => navigate("/students")}
          className="hidden"
        >
          <UserPlus className="h-4 w-4" /> Add Student
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="flex flex-wrap items-center gap-3 p-4">
          <div className="relative min-w-52 flex-1">
            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
            <Input
              placeholder="Search by name or student ID…"
              className="pl-8"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select value={risk} onValueChange={(v) => setRisk(v)}>
            <SelectTrigger className="w-36">
              <SelectValue placeholder="Risk" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Risk Levels</SelectItem>
              <SelectItem value="high">High Risk</SelectItem>
              <SelectItem value="moderate">Moderate Risk</SelectItem>
              <SelectItem value="low">Low Risk</SelectItem>
            </SelectContent>
          </Select>
          <Select value={departmentId} onValueChange={(v) => { setDepartmentId(v); setSectionId("all") }}>
            <SelectTrigger className="w-44">
              <SelectValue placeholder="Department" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Departments</SelectItem>
              {departments?.map((d) => (
                <SelectItem key={d.id} value={String(d.id)}>
                  {d.code}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={sectionId} onValueChange={setSectionId}>
            <SelectTrigger className="w-36">
              <SelectValue placeholder="Section" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sections</SelectItem>
              {sections
                ?.filter((s) => departmentId === "all" || String(s.department_id) === departmentId)
                .map((s) => (
                  <SelectItem key={s.id} value={String(s.id)}>
                    {s.name}
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
          <Select value={year} onValueChange={setYear}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Year" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Years</SelectItem>
              {[2024, 2025].map((y) => (
                <SelectItem key={y} value={String(y)}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] text-left text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
                  <th
                    className="cursor-pointer px-5 py-3 font-medium select-none"
                    onClick={() => toggleSort("name")}
                  >
                    <span className="flex items-center gap-1">Student <SortIcon column="name" /></span>
                  </th>
                  <th className="px-4 py-3 font-medium">Department</th>
                  <th className="px-4 py-3 font-medium">Section</th>
                  <th className="cursor-pointer px-4 py-3 font-medium select-none" onClick={() => toggleSort("attendance")}>
                    <span className="flex items-center gap-1">Attendance <SortIcon column="attendance" /></span>
                  </th>
                  <th className="cursor-pointer px-4 py-3 font-medium select-none" onClick={() => toggleSort("average_score")}>
                    <span className="flex items-center gap-1">Avg Score <SortIcon column="average_score" /></span>
                  </th>
                  <th className="cursor-pointer px-4 py-3 font-medium select-none" onClick={() => toggleSort("engagement")}>
                    <span className="flex items-center gap-1">Engagement <SortIcon column="engagement" /></span>
                  </th>
                  <th className="cursor-pointer px-4 py-3 font-medium select-none" onClick={() => toggleSort("risk_probability")}>
                    <span className="flex items-center gap-1">Risk Prob. <SortIcon column="risk_probability" /></span>
                  </th>
                  <th className="px-4 py-3 font-medium">Risk Level</th>
                  <th className="px-4 py-3 font-medium">Last Prediction</th>
                  <th className="px-5 py-3 text-right font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {isLoading &&
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} className="border-b border-[var(--border)] last:border-0">
                      <td colSpan={10} className="px-5 py-2.5">
                        <Skeleton className="h-8 w-full" />
                      </td>
                    </tr>
                  ))}

                {!isLoading &&
                  data?.map((s) => (
                    <tr
                      key={s.id}
                      className={`cursor-pointer border-b border-[var(--border)] transition-colors last:border-0 hover:bg-[var(--muted)] ${isFetching ? "opacity-60" : ""}`}
                      onClick={() => navigate(`/students/${s.id}`)}
                    >
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--primary)]/10 text-xs font-bold text-[var(--primary)]">
                            {s.full_name.split(" ").map((p) => p[0]).slice(0, 2).join("")}
                          </div>
                          <div>
                            <p className="font-medium">{s.full_name}</p>
                            <p className="text-xs text-[var(--muted-foreground)]">{s.student_id}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-[var(--muted-foreground)]">{s.department_name}</td>
                      <td className="px-4 py-3 text-[var(--muted-foreground)]">{s.section_name}</td>
                      <td className="px-4 py-3">{formatNumber(s.attendance)}%</td>
                      <td className="px-4 py-3 font-medium">{formatNumber(s.average_score)}%</td>
                      <td className="px-4 py-3">{formatNumber(s.engagement)}%</td>
                      <td className="px-4 py-3 font-semibold">{formatPercent(s.risk_probability, 1)}</td>
                      <td className="px-4 py-3">
                        <RiskBadge level={s.risk_level} />
                      </td>
                      <td className="px-4 py-3 text-xs text-[var(--muted-foreground)]">
                        {formatDate(s.last_prediction)}
                      </td>
                      <td className="px-5 py-3 text-right">
                        <Button variant="ghost" size="sm" className="text-[var(--primary)]">
                          View
                        </Button>
                      </td>
                    </tr>
                  ))}

                {!isLoading && data && data.length === 0 && (
                  <tr>
                    <td colSpan={10} className="px-5 py-6">
                      <EmptyState
                        icon={Users}
                        title="No students found"
                        description="Try adjusting your search or filters."
                      />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between border-t border-[var(--border)] px-5 py-3">
            <p className="text-xs text-[var(--muted-foreground)]">
              Page {page} {hasMore ? "· more pages" : ""}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                <ChevronLeft className="h-4 w-4" /> Prev
              </Button>
              <span className="text-xs text-[var(--muted-foreground)]">{page}</span>
              <Button
                variant="outline"
                size="sm"
                disabled={!hasMore}
                onClick={() => setPage((p) => p + 1)}
              >
                Next <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          Failed to load students: {error.message}
        </div>
      )}
    </div>
  )
}

