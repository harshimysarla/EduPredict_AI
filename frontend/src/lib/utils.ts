import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPercent(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined) return "—"
  return `${(v * 100).toFixed(digits)}%`
}

export function formatNumber(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined) return "—"
  return v.toFixed(digits)
}

export function formatDate(d: string | null | undefined): string {
  if (!d) return "—"
  try {
    return new Date(d).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  } catch {
    return "—"
  }
}

export function formatDateTime(d: string | null | undefined): string {
  if (!d) return "—"
  try {
    return new Date(d).toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  } catch {
    return "—"
  }
}

export function riskColor(level: string | null | undefined): string {
  switch (level) {
    case "high":
      return "#ef4444"
    case "moderate":
      return "#f59e0b"
    case "low":
      return "#10b981"
    default:
      return "#94a3b8"
  }
}

export function riskLabel(level: string | null | undefined): string {
  if (!level) return "Unpredicted"
  return level.charAt(0).toUpperCase() + level.slice(1)
}
