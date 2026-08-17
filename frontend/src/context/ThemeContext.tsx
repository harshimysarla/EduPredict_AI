import { createContext, useContext, useEffect, useState, type ReactNode } from "react"

type Theme = "light" | "dark"

const ThemeContext = createContext<{
  theme: Theme
  toggleTheme: () => void
}>({ theme: "light", toggleTheme: () => {} })

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem("edupredict_theme") as Theme | null
    if (saved === "light" || saved === "dark") return saved
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light"
  })

  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle("dark", theme === "dark")
    localStorage.setItem("edupredict_theme", theme)
  }, [theme])

  return (
    <ThemeContext.Provider
      value={{ theme, toggleTheme: () => setTheme((t) => (t === "dark" ? "light" : "dark")) }}
    >
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}
