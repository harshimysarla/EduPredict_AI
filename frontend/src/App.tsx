import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Toaster } from "sonner"
import { AuthProvider, useAuth } from "@/context/AuthContext"
import { ThemeProvider } from "@/context/ThemeContext"
import { TooltipProvider } from "@/components/ui/tooltip"
import { PageLoader } from "@/components/ui/spinner"
import { AppShell } from "@/components/layout/AppShell"
import Login from "@/pages/Login"
import Dashboard from "@/pages/Dashboard"
import Students from "@/pages/Students"
import StudentProfile from "@/pages/StudentProfile"
import Predictions from "@/pages/Predictions"
import Analytics from "@/pages/Analytics"
import Interventions from "@/pages/Interventions"
import ModelLab from "@/pages/ModelLab"
import Dataset from "@/pages/Dataset"
import Reports from "@/pages/Reports"
import Settings from "@/pages/Settings"
import Profile from "@/pages/Profile"
import StudentDashboard from "@/pages/StudentDashboard"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function Protected({ roles }: { roles: string[] }) {
  const { user, loading } = useAuth()
  if (loading) return <PageLoader />
  if (!user) return <Navigate to="/login" replace />
  if (!roles.includes(user.role)) return <Navigate to={user.role === "student" ? "/student" : "/dashboard"} replace />
  return <Outlet />
}

function RedirectIfAuthed() {
  const { user, loading } = useAuth()
  if (loading) return <PageLoader />
  if (user) return <Navigate to={user.role === "student" ? "/student" : "/dashboard"} replace />
  return <Outlet />
}

function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<RedirectIfAuthed />}>
          <Route path="/login" element={<Login />} />
        </Route>

        <Route element={<Protected roles={["admin", "faculty"]} />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/students" element={<Students />} />
            <Route path="/students/:id" element={<StudentProfile />} />
            <Route path="/predictions" element={<Predictions />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/interventions" element={<Interventions />} />
            <Route path="/model-lab" element={<ModelLab />} />
            <Route path="/datasets" element={<Dataset />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/profile" element={<Profile />} />
          </Route>
        </Route>

        <Route element={<Protected roles={["student"]} />}>
          <Route element={<AppShell />}>
            <Route path="/student" element={<StudentDashboard />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <AuthProvider>
            <AppRoutes />
            <Toaster richColors position="top-right" />
          </AuthProvider>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
