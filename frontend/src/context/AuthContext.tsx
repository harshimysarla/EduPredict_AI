import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { api, getToken, setToken } from "@/lib/api"
import type { LoginResponse, Role, User } from "@/types"

interface AuthContextValue {
  user: User | null
  role: Role | null
  loading: boolean
  login: (email: string, password: string) => Promise<LoginResponse>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }
    api
      .get<User>("/me")
      .then(setUser)
      .catch(() => {
        setToken(null)
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.post<LoginResponse>("/auth/login", { email, password })
    setToken(res.access_token)
    const me = await api.get<User>("/me")
    setUser(me)
    return res
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
    window.location.href = "/login"
  }, [])

  useEffect(() => {
    const handler = () => {
      setUser(null)
      window.location.href = "/login"
    }
    window.addEventListener("edupredict:unauthorized", handler)
    return () => window.removeEventListener("edupredict:unauthorized", handler)
  }, [])

  const value = useMemo(
    () => ({ user, role: user?.role ?? null, loading, login, logout }),
    [user, loading, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
