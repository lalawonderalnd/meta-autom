'use client'

import { Bell, Search } from 'lucide-react'

export function Topbar() {
  return (
    <header className="fixed left-[220px] right-0 top-0 h-12 bg-surface border-b border-border flex items-center justify-between px-4 z-10">
      {/* Breadcrumbs - placeholder */}
      <div className="text-sm text-foreground-muted">
        Dashboard
      </div>

      {/* Right side actions */}
      <div className="flex items-center gap-4">
        {/* Global search trigger */}
        <button className="flex items-center gap-2 px-3 py-1.5 rounded-sm bg-surface-elevated border border-border-strong text-xs text-foreground-muted hover:text-foreground transition-colors">
          <Search className="w-3.5 h-3.5" />
          <span>Search...</span>
          <kbd className="ml-2 px-1.5 py-0.5 rounded-sm bg-background text-[10px] font-mono">/</kbd>
        </button>

        {/* Notifications */}
        <button className="relative p-2 text-foreground-muted hover:text-foreground transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-accent-red" />
        </button>

        {/* User menu */}
        <div className="w-7 h-7 rounded-sm bg-accent-cyan/20 border border-accent-cyan/40 flex items-center justify-center">
          <span className="text-xs font-mono text-accent-cyan">OP</span>
        </div>
      </div>
    </header>
  )
}
