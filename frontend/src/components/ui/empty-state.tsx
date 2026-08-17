import type { LucideIcon } from "lucide-react"
import { Inbox } from "lucide-react"

interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description?: string
  action?: React.ReactNode
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-[var(--border)] px-6 py-16 text-center">
      <div className="rounded-full bg-[var(--muted)] p-3">
        <Icon className="h-6 w-6 text-[var(--muted-foreground)]" />
      </div>
      <div>
        <p className="text-sm font-semibold">{title}</p>
        {description && (
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">{description}</p>
        )}
      </div>
      {action}
    </div>
  )
}
