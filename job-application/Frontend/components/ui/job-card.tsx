"use client"

import { cn } from "@/lib/utils"
import { Button } from "./button"

interface JobCardProps {
  title: string
  company: string
  location: string
  salary: string
  type: string
  onSelect: () => void
  className?: string
}

export function JobCard({
  title,
  company,
  location,
  salary,
  type,
  onSelect,
  className,
}: JobCardProps) {
  return (
    <Button
      variant="outline"
      onClick={onSelect}
      className={cn(
        "flex h-auto w-full flex-col items-start justify-start rounded-lg border bg-card p-4 text-left shadow-sm transition-colors hover:bg-muted/50",
        className
      )}
    >
      <div className="flex w-full items-start justify-between">
        <div className="flex flex-col gap-1">
          <p className="font-semibold text-card-foreground">{title}</p>
          <p className="text-sm text-muted-foreground">{company}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <p className="font-semibold text-primary">{salary}</p>
          <p className="text-sm text-muted-foreground">{location}</p>
        </div>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">{type}</p>
    </Button>
  )
} 