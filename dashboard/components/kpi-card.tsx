'use client'

import { cn } from '@/lib/utils'

interface KpiCardProps {
  label: string
  value: number
  percentage?: number
  accent?: 'cyan' | 'amber' | 'blue' | 'magenta' | 'red' | 'violet' | 'green'
  className?: string
}

const ACCENT_COLORS = {
  cyan: 'bg-accent-cyan',
  amber: 'bg-accent-amber',
  blue: 'bg-accent-blue',
  magenta: 'bg-accent-magenta',
  red: 'bg-accent-red',
  violet: 'bg-accent-violet',
  green: 'bg-accent-green',
}

export function KpiCard({ label, value, percentage, accent = 'cyan', className }: KpiCardProps) {
  return (
    <div className={cn('relative h-[88px] p-4 bg-surface border border-border rounded-sm', className)}>
      <div className={cn('absolute top-0 left-0 right-0 h-0.5', ACCENT_COLORS[accent])} />
      
      <div className="flex items-end justify-between h-full">
        <div>
          <div className="text-[44px] font-display leading-none text-foreground">
            {value.toLocaleString()}
          </div>
          <div className="text-[10px] font-mono uppercase tracking-wider text-foreground-muted mt-1">
            {label}
          </div>
        </div>
        
        {percentage !== undefined && (
          <div className="flex items-center px-2 py-1 rounded-sm bg-surface-elevated border border-border-strong">
            <span className="text-xs font-mono text-foreground">
              {percentage.toFixed(1)}%
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
