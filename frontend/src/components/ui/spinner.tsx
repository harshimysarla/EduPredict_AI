import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("h-5 w-5 animate-spin text-[var(--primary)]", className)} />
}

export function PageLoader({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-24">
      <Spinner className="h-7 w-7" />
      <p className="text-sm text-[var(--muted-foreground)]">{label}</p>
    </div>
  )
}
