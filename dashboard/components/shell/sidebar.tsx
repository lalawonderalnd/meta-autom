'use client'

import { Sidebar as SidebarIcon, LayoutDashboard, Users, Smartphone, ClipboardList, Building2, Image, Shield, Settings, LogOut } from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

const navItems = [
  { href: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/accounts', icon: Users, label: 'Accounts' },
  { href: '/devices', icon: Smartphone, label: 'Devices' },
  { href: '/jobs', icon: ClipboardList, label: 'Jobs' },
  { href: '/clients', icon: Building2, label: 'Clients' },
  { href: '/content', icon: Image, label: 'Content' },
  { href: '/proxies', icon: Shield, label: 'Proxies' },
  { href: '/settings', icon: Settings, label: 'Settings' },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 h-full w-[220px] bg-surface border-r border-border flex flex-col">
      {/* Logo */}
      <div className="h-12 flex items-center px-4 border-b border-border">
        <span className="font-display text-accent-magenta text-lg tracking-wider">
          ACCFARM
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-4 py-2 text-sm transition-colors',
                isActive
                  ? 'text-accent-cyan bg-surface-elevated border-l-2 border-accent-cyan'
                  : 'text-foreground-muted hover:text-foreground hover:bg-surface-elevated/50'
              )}
            >
              <item.icon className="w-4 h-4" />
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>

      {/* Connection status */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-2 text-xs">
          <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
          <span className="text-foreground-muted">System Online</span>
        </div>
      </div>

      {/* Logout */}
      <div className="p-4 border-t border-border">
        <button className="flex items-center gap-3 px-4 py-2 text-sm text-foreground-muted hover:text-foreground w-full transition-colors">
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  )
}
