import { useEffect, useState } from "react"
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom"
import {
  Bell,
  BrainCircuit,
  ChevronDown,
  FileBarChart2,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Search,
  Settings,
  Sun,
  Users,
  UserRound,
  X,
  Database,
  LineChart,
  FlaskConical,
  LifeBuoy,
} from "lucide-react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { NotificationItem } from "@/types"
import { useAuth } from "@/context/AuthContext"
import { useTheme } from "@/context/ThemeContext"
import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { formatDateTime } from "@/lib/utils"

const navSections = [
  {
    label: "Overview",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { to: "/students", label: "Students", icon: Users },
      { to: "/predictions", label: "Predictions", icon: BrainCircuit },
      { to: "/analytics", label: "Analytics", icon: LineChart },
    ],
  },
  {
    label: "Management",
    items: [
      { to: "/interventions", label: "Interventions", icon: LifeBuoy },
      { to: "/model-lab", label: "Model Lab", icon: FlaskConical },
      { to: "/datasets", label: "Dataset", icon: Database },
      { to: "/reports", label: "Reports", icon: FileBarChart2 },
    ],
  },
  {
    label: "Account",
    items: [
      { to: "/settings", label: "Settings", icon: Settings },
      { to: "/profile", label: "Profile", icon: UserRound },
    ],
  },
]

const studentNavSections = [
  {
    label: "Overview",
    items: [{ to: "/student", label: "Your Dashboard", icon: LayoutDashboard }],
  },
  {
    label: "Account",
    items: [
      { to: "/settings", label: "Settings", icon: Settings },
      { to: "/profile", label: "Profile", icon: UserRound },
    ],
  },
]

function NotificationBell() {
  const { data } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api.get<NotificationItem[]>("/notifications"),
    refetchInterval: 30000,
  })
  const unread = data?.filter((n) => !n.is_read).length ?? 0
  const queryClient = useQueryClient()

  const markAllRead = async () => {
    if (!data) return
    for (const n of data.filter((x) => !x.is_read)) {
      await api.post(`/notifications/${n.id}/read`)
    }
    queryClient.invalidateQueries({ queryKey: ["notifications"] })
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="relative rounded-lg p-2 text-[var(--muted-foreground)] transition-colors hover:bg-[var(--muted)] hover:text-[var(--foreground)]">
          <Bell className="h-5 w-5" />
          {unread > 0 && (
            <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
              {unread}
            </span>
          )}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>Notifications</span>
          {unread > 0 && (
            <button
              onClick={markAllRead}
              className="text-xs text-[var(--primary)] hover:underline"
            >
              Mark all read
            </button>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <div className="max-h-80 overflow-y-auto">
          {data && data.length === 0 && (
            <div className="px-3 py-8 text-center text-sm text-[var(--muted-foreground)]">
              No notifications yet
            </div>
          )}
          {data?.slice(0, 8).map((n) => (
            <div
              key={n.id}
              className={cn(
                "flex flex-col gap-0.5 border-b border-[var(--border)] px-3 py-2.5 text-sm last:border-0",
                !n.is_read && "bg-[var(--accent)]/40",
              )}
            >
              <div className="flex items-center gap-2">
                <span className="font-medium">{n.title}</span>
                {!n.is_read && <span className="h-1.5 w-1.5 rounded-full bg-[var(--primary)]" />}
              </div>
              <p className="text-xs text-[var(--muted-foreground)]">{n.message}</p>
              <span className="mt-0.5 text-[11px] text-[var(--muted-foreground)]/70">
                {formatDateTime(n.created_at)}
              </span>
            </div>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function GlobalSearch() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const navigate = useNavigate()
  const [debounced, setDebounced] = useState("")

  useEffect(() => {
    const t = setTimeout(() => setDebounced(query), 300)
    return () => clearTimeout(t)
  }, [query])

  const { data } = useQuery({
    queryKey: ["student-search", debounced],
    queryFn: () =>
      api.get<{ id: number; student_id: string; full_name: string }[]>(
        `/students?search=${encodeURIComponent(debounced)}&page_size=6`,
      ),
    enabled: debounced.length >= 2,
  })

  return (
    <div className="relative hidden md:block">
      <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
      <Input
        placeholder="Search students…"
        className="w-56 pl-8"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
        }}
        onBlur={() => setTimeout(() => setOpen(false), 200)}
      />
      {open && debounced.length >= 2 && (
        <div className="absolute z-50 mt-1 w-72 rounded-lg border border-[var(--border)] bg-[var(--card)] p-1 shadow-lg">
          {data && data.length === 0 && (
            <div className="px-3 py-4 text-center text-sm text-[var(--muted-foreground)]">
              No students found
            </div>
          )}
          {data?.map((s) => (
            <button
              key={s.id}
              className="flex w-full items-center justify-between rounded-md px-3 py-2 text-sm hover:bg-[var(--muted)]"
              onMouseDown={() => {
                navigate(`/students/${s.id}`)
                setOpen(false)
                setQuery("")
              }}
            >
              <span className="font-medium">{s.full_name}</span>
              <span className="text-xs text-[var(--muted-foreground)]">{s.student_id}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function DataSourceBadge() {
  const { data } = useQuery({
    queryKey: ["data-source"],
    queryFn: () => api.get<{ name: string; type: string; status: string; record_count: number | null; samvidha_status?: string }>("/data-source"),
    refetchInterval: 60000,
  })
  if (!data) return null
  const activeType = data.type
  const label =
    activeType === "CSV"
      ? "Approved Academic Data"
      : activeType === "SAMVIDHA"
        ? "Samvidha Connected"
        : "Synthetic Demo Data"
  const color =
    activeType === "CSV"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
      : activeType === "SAMVIDHA"
        ? "border-sky-500/30 bg-sky-500/10 text-sky-600 dark:text-sky-400"
        : "border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400"
  return (
    <span
      className={`hidden items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold md:flex ${color}`}
      title={`Active data source: ${data.name} (${data.status})`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  )
}

export function AppShell() {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const navSectionsForRole = user?.role === "student" ? studentNavSections : navSections

  const initials = (user?.full_name ?? "U")
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase()

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-[var(--border)] bg-[var(--sidebar)] transition-transform lg:static lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-16 items-center gap-2.5 border-b border-[var(--border)] px-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-sm">
            <GraduationCap className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-bold leading-tight">EduPredict AI</p>
            <p className="text-[11px] text-[var(--muted-foreground)]">Predict Early. Intervene Smartly.</p>
          </div>
          <button
            className="ml-auto rounded-lg p-1 hover:bg-[var(--muted)] lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
          {navSectionsForRole.map((section) => (
            <div key={section.label}>
              <p className="mb-1.5 px-3 text-[11px] font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                {section.label}
              </p>
              <div className="space-y-0.5">
                {section.items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => setSidebarOpen(false)}
                    className={({ isActive }) =>
                      cn(
                        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                        isActive
                          ? "bg-[var(--primary)]/10 text-[var(--primary)]"
                          : "text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)]",
                      )
                    }
                  >
                    <item.icon className="h-4 w-4" />
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-[var(--border)] p-3">
          <div className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-[var(--muted-foreground)]">
            <BrainCircuit className="h-3.5 w-3.5 text-[var(--primary)]" />
            ML Pipeline: Random Forest · Logistic Regression
          </div>
        </div>
      </aside>

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-16 shrink-0 items-center gap-3 border-b border-[var(--border)] bg-[var(--card)] px-4 lg:px-6">
          <button
            className="rounded-lg p-2 hover:bg-[var(--muted)] lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </button>
          <GlobalSearch />
          <div className="ml-auto flex items-center gap-1.5">
            <DataSourceBadge />
            <NotificationBell />
            <button
              onClick={toggleTheme}
              className="rounded-lg p-2 text-[var(--muted-foreground)] transition-colors hover:bg-[var(--muted)] hover:text-[var(--foreground)]"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-[var(--muted)]">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback>{initials}</AvatarFallback>
                  </Avatar>
                  <span className="hidden text-left sm:block">
                    <span className="block text-sm font-medium leading-tight">{user?.full_name}</span>
                    <span className="block text-[11px] capitalize leading-tight text-[var(--muted-foreground)]">
                      {user?.role}
                    </span>
                  </span>
                  <ChevronDown className="hidden h-4 w-4 text-[var(--muted-foreground)] sm:block" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuLabel>{user?.username ?? user?.email ?? "Account"}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link to="/profile">
                    <UserRound className="h-4 w-4" /> Profile
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/settings">
                    <Settings className="h-4 w-4" /> Settings
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="text-red-500">
                  <LogOut className="h-4 w-4" /> Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
