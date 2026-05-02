'use client'

import { cn } from '@/lib/utils'

interface WarmupBarProps {
  value: number
  max?: number
  active?: boolean
}

export function WarmupBar({ value, max = 7, active = true }: WarmupBarProps) {
  if (!active) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-sm text-[11px] font-mono text-foreground-muted bg-foreground-muted/12">
        OFF
      </span>
    )
  }

  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: max }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'w-1 h-3 rounded-sm transition-all duration-250',
            i < value
              ? 'bg-accent-magenta'
              : 'border border-border-strong bg-transparent'
          )}
        />
      ))}
    </div>
  )
}
