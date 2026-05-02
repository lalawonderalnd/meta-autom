import { supabaseAdmin } from '@/lib/supabase/server'
import { KpiCard } from '@/components/kpi-card'

export const dynamic = 'force-dynamic'

async function getKpiData() {
  try {
    const { data: accounts } = await supabaseAdmin
      .from('accounts')
      .select('status, warmup_day')
    
    const total = accounts?.length || 0
    const active = accounts?.filter(a => a.status === 'ACTIVE').length || 0
    const warming = accounts?.filter(a => a.status === 'WARMING').length || 0
    const needsAttention = accounts?.filter(a => a.status === 'NEEDS_ATTENTION').length || 0
    const banned = accounts?.filter(a => a.status === 'BANNED').length || 0

    return { total, active, warming, needsAttention, banned }
  } catch (error) {
    console.error('Failed to fetch KPI data:', error)
    return { total: 0, active: 0, warming: 0, needsAttention: 0, banned: 0 }
  }
}

export default async function DashboardPage() {
  const kpi = await getKpiData()

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-5 gap-4">
        <KpiCard 
          label="Total" 
          value={kpi.total} 
          percentage={100}
          accent="cyan"
        />
        <KpiCard 
          label="Active" 
          value={kpi.active} 
          percentage={kpi.total > 0 ? (kpi.active / kpi.total) * 100 : 0}
          accent="cyan"
        />
        <KpiCard 
          label="Warming" 
          value={kpi.warming} 
          percentage={kpi.total > 0 ? (kpi.warming / kpi.total) * 100 : 0}
          accent="magenta"
        />
        <KpiCard 
          label="Needs Attention" 
          value={kpi.needsAttention} 
          percentage={kpi.total > 0 ? (kpi.needsAttention / kpi.total) * 100 : 0}
          accent="blue"
        />
        <KpiCard 
          label="Banned" 
          value={kpi.banned} 
          percentage={kpi.total > 0 ? (kpi.banned / kpi.total) * 100 : 0}
          accent="red"
        />
      </div>

      {/* Content sections placeholder */}
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-surface border border-border rounded-sm p-4">
          <h3 className="text-sm font-mono text-foreground-muted uppercase tracking-wider mb-4">
            Live Job Feed
          </h3>
          <p className="text-foreground-muted text-sm">No recent jobs</p>
        </div>
        
        <div className="bg-surface border border-border rounded-sm p-4">
          <h3 className="text-sm font-mono text-foreground-muted uppercase tracking-wider mb-4">
            Devices
          </h3>
          <p className="text-foreground-muted text-sm">No devices online</p>
        </div>
      </div>
    </div>
  )
}
