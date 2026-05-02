'use client'

import { useEffect, useState } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { useRealtimeTable } from '@/hooks/use-realtime-table'
import { StatusPill } from '@/components/status-pill'
import { WarmupBar } from '@/components/warmup-bar'
import { Instagram, MoreHorizontal, Play, Square, Eye, Pencil } from 'lucide-react'
import type { Account } from '@/lib/types'
import { cn, truncateMiddle } from '@/lib/utils'

// Mock initial data for demonstration
const MOCK_ACCOUNTS: Account[] = Array.from({ length: 50 }, (_, i) => ({
  id: `acc-${i + 1}`,
  username: `user_${i + 1}`,
  package_name: `com.instagram.androidp${i + 1}`,
  device_id: `dev-${(i % 5) + 1}`,
  client_id: i % 3 === 0 ? `client-${(i % 3) + 1}` : null,
  status: ['ACTIVE', 'WARMING', 'IDLE', 'NEEDS_ATTENTION', 'BANNED'][i % 5] as any,
  warmup_day: i % 8,
  posts_count: Math.floor(Math.random() * 100),
  followers_count: Math.floor(Math.random() * 10000),
  following_count: Math.floor(Math.random() * 5000),
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}))

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>(MOCK_ACCOUNTS)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string[]>([])

  // Filter accounts
  const filteredAccounts = accounts.filter(acc => {
    const matchesSearch = searchQuery === '' || 
      acc.username?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      acc.package_name.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesStatus = statusFilter.length === 0 || statusFilter.includes(acc.status)
    
    return matchesSearch && matchesStatus
  })

  // Virtualization
  const parentRef = useState<HTMLDivElement | null>(null)[0]
  const virtualizer = useVirtualizer({
    count: filteredAccounts.length,
    getScrollElement: () => parentRef,
    estimateSize: () => 48,
    overscan: 5,
  })

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === filteredAccounts.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(filteredAccounts.map(a => a.id)))
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-display text-foreground">Accounts</h1>
        <div className="text-sm font-mono text-foreground-muted">
          {filteredAccounts.length} accounts
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder="Search accounts..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 px-3 py-2 rounded-sm bg-surface border border-border-strong text-sm text-foreground placeholder:text-foreground-subtle focus:outline-none focus:border-accent-cyan/50"
        />
        
        {/* Status filter pills */}
        {['ACTIVE', 'WARMING', 'NEEDS_ATTENTION', 'BANNED'].map(status => (
          <button
            key={status}
            onClick={() => setStatusFilter(prev => 
              prev.includes(status) 
                ? prev.filter(s => s !== status)
                : [...prev, status]
            )}
            className={cn(
              'px-3 py-1.5 rounded-sm text-[11px] font-mono uppercase tracking-wider border transition-colors',
              statusFilter.includes(status)
                ? 'bg-accent-cyan/20 border-accent-cyan text-accent-cyan'
                : 'bg-surface border-border text-foreground-muted hover:text-foreground'
            )}
          >
            {status.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Bulk actions bar */}
      {selectedIds.size > 0 && (
        <div className="flex items-center gap-3 p-3 rounded-sm bg-surface-elevated border border-border-strong">
          <span className="text-sm font-mono text-foreground-muted">
            {selectedIds.size} selected
          </span>
          <div className="h-4 w-px bg-border-strong" />
          <button className="px-3 py-1.5 rounded-sm bg-accent-cyan/20 text-accent-cyan text-xs font-mono uppercase hover:bg-accent-cyan/30 transition-colors">
            Queue Warmup
          </button>
          <button className="px-3 py-1.5 rounded-sm bg-accent-cyan/20 text-accent-cyan text-xs font-mono uppercase hover:bg-accent-cyan/30 transition-colors">
            Queue Post
          </button>
          <button className="px-3 py-1.5 rounded-sm bg-accent-amber/20 text-accent-amber text-xs font-mono uppercase hover:bg-accent-amber/30 transition-colors">
            Pause
          </button>
          <button className="px-3 py-1.5 rounded-sm bg-accent-red/20 text-accent-red text-xs font-mono uppercase hover:bg-accent-red/30 transition-colors">
            Mark Removed
          </button>
        </div>
      )}

      {/* Table */}
      <div className="border border-border rounded-sm overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-surface border-b border-border">
              <th className="w-10 p-3">
                <input
                  type="checkbox"
                  checked={selectedIds.size === filteredAccounts.length && filteredAccounts.length > 0}
                  onChange={toggleSelectAll}
                  className="rounded-sm bg-surface-elevated border-border-strong"
                />
              </th>
              <th className="text-left text-[10px] font-mono uppercase tracking-wider text-foreground-muted p-3">APP</th>
              <th className="text-left text-[10px] font-mono uppercase tracking-wider text-foreground-muted p-3">USERNAME</th>
              <th className="text-left text-[10px] font-mono uppercase tracking-wider text-foreground-muted p-3">POSTS / FLWRS / FLWNG</th>
              <th className="text-left text-[10px] font-mono uppercase tracking-wider text-foreground-muted p-3">STATUS</th>
              <th className="text-left text-[10px] font-mono uppercase tracking-wider text-foreground-muted p-3">WARMUP</th>
              <th className="text-left text-[10px] font-mono uppercase tracking-wider text-foreground-muted p-3">DEVICE</th>
              <th className="text-left text-[10px] font-mono uppercase tracking-wider text-foreground-muted p-3">PACKAGE</th>
              <th className="text-left text-[10px] font-mono uppercase tracking-wider text-foreground-muted p-3">CLIENT</th>
              <th className="text-left text-[10px] font-mono uppercase tracking-wider text-foreground-muted p-3">ACTIONS</th>
            </tr>
          </thead>
          <tbody ref={parentRef as any} className="divide-y divide-border" style={{ height: `${virtualizer.getTotalSize()}px`, overflowY: 'auto' }}>
            {virtualizer.getVirtualItems().map((virtualRow) => {
              const account = filteredAccounts[virtualRow.index]
              return (
                <tr
                  key={account.id}
                  className={cn(
                    'table-row hover:bg-surface-elevated/50 transition-colors',
                    selectedIds.has(account.id) && 'bg-surface-elevated'
                  )}
                  style={{ transform: `translateY(${virtualRow.start}px)`, position: 'absolute', top: 0, left: 0, right: 0 }}
                >
                  <td className="p-3">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(account.id)}
                      onChange={() => toggleSelect(account.id)}
                      className="rounded-sm bg-surface-elevated border-border-strong"
                    />
                  </td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <Instagram className="w-4 h-4 text-accent-magenta" />
                      <span className="text-xs font-mono text-foreground">IG</span>
                    </div>
                  </td>
                  <td className="p-3">
                    <span className="text-sm font-mono text-foreground hover:text-accent-cyan cursor-pointer">
                      {account.username || '—'}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="text-sm font-mono text-foreground">
                      {account.posts_count} / {account.followers_count.toLocaleString()} / {account.following_count.toLocaleString()}
                    </span>
                  </td>
                  <td className="p-3">
                    <StatusPill status={account.status} />
                  </td>
                  <td className="p-3">
                    <WarmupBar 
                      value={account.warmup_day} 
                      max={7}
                      active={account.status === 'WARMING'}
                    />
                  </td>
                  <td className="p-3">
                    <span className="text-sm font-mono text-foreground">
                      {account.device_id || '—'}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="text-xs font-mono text-foreground-muted">
                      {truncateMiddle(account.package_name, 16)}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="text-sm font-mono text-foreground-muted">
                      {account.client_id || '—'}
                    </span>
                  </td>
                  <td className="p-3">
                    <div className="flex items-center gap-1">
                      <button className="p-1.5 rounded-sm hover:bg-surface-elevated text-foreground-muted hover:text-foreground transition-colors" title="Watch">
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button className="p-1.5 rounded-sm hover:bg-surface-elevated text-foreground-muted hover:text-foreground transition-colors" title="Edit">
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button className="p-1.5 rounded-sm hover:bg-surface-elevated text-foreground-muted hover:text-accent-green transition-colors" title="Run">
                        <Play className="w-3.5 h-3.5" />
                      </button>
                      <button className="p-1.5 rounded-sm hover:bg-surface-elevated text-foreground-muted hover:text-accent-red transition-colors" title="Stop">
                        <Square className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
