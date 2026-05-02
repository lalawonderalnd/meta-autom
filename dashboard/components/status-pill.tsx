'use client'

import { cn } from '@/lib/utils'
import { STATUS_COLORS, STATUS_BG_COLORS, type AccountStatus } from '@/lib/types'

interface StatusPillProps {
  status: AccountStatus
  className?: string
}

export function StatusPill({ status, className }: StatusPillProps) {
  const isGlowing = status === 'ACTIVE'
  
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-sm border text-[11px] font-mono font-semibold uppercase tracking-wider',
        STATUS_COLORS[status],
        STATUS_BG_COLORS[status],
        `border-${STATUS_COLORS[status].replace('text-', '')}`,
        isGlowing && 'status-active',
        className
      )}
    >
      {status.replace('_', ' ')}
    </span>
  )
}
