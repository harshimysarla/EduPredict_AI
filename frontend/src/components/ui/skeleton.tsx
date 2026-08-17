import * as React from "react"
import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse-soft rounded-md bg-[var(--muted)]",
        className,
      )}
      {...props}
    />
  )
}

export { Skeleton }
