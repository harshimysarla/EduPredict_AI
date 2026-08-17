import { ShieldAlert, ShieldCheck, ShieldQuestion, ShieldX } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

const config = {
  high: {
    variant: "danger" as const,
    icon: ShieldAlert,
    label: "High Risk",
  },
  moderate: {
    variant: "warning" as const,
    icon: ShieldX,
    label: "Moderate",
  },
  low: {
    variant: "success" as const,
    icon: ShieldCheck,
    label: "Low Risk",
  },
  unpredicted: {
    variant: "secondary" as const,
    icon: ShieldQuestion,
    label: "Unpredicted",
  },
}

export function RiskBadge({
  level,
  className,
  showIcon = true,
}: {
  level: string | null | undefined
  className?: string
  showIcon?: boolean
}) {
  const key = level ?? "unpredicted"
  const c = config[key as keyof typeof config] ?? config.unpredicted
  const Icon = c.icon
  return (
    <Badge variant={c.variant} className={cn("gap-1", className)}>
      {showIcon && <Icon className="h-3 w-3" />}
      {c.label}
    </Badge>
  )
}
