export type AccountStatus = 
  | 'NEW'
  | 'WARMING'
  | 'ACTIVE'
  | 'IDLE'
  | 'COOLDOWN'
  | 'NEEDS_ATTENTION'
  | 'WARNING'
  | 'SHADOWBANNED'
  | 'BANNED'
  | 'REMOVED'

export interface Account {
  id: string
  username: string | null
  package_name: string
  device_id: string | null
  client_id: string | null
  status: AccountStatus
  warmup_day: number
  posts_count: number
  followers_count: number
  following_count: number
  created_at: string
  updated_at: string
}

export interface Device {
  id: string
  name: string
  ip_address: string
  adb_port: number
  status: 'ONLINE' | 'OFFLINE' | 'DEGRADED'
  android_version: string | null
  manufacturer: string | null
  model: string | null
  max_clones: number
  clone_count: number
  created_at: string
  updated_at: string
}

export interface Job {
  id: string
  account_id: string
  device_id: string | null
  kind: 'WARMUP' | 'POST' | 'FOLLOW' | 'LIKE' | 'COMMENT' | 'UNFOLLOW'
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
  priority: number
  scheduled_for: string | null
  attempt: number
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface Client {
  id: string
  name: string
  instagram_handle: string | null
  created_at: string
}

export interface Proxy {
  id: string
  provider: string
  host: string
  port: number
  username: string
  country: string
  is_alive: boolean
  account_id: string | null
  created_at: string
}

export const STATUS_COLORS: Record<AccountStatus, string> = {
  NEW: 'text-foreground-muted',
  WARMING: 'text-accent-magenta',
  ACTIVE: 'text-accent-cyan',
  IDLE: 'text-foreground-muted',
  COOLDOWN: 'text-accent-amber',
  NEEDS_ATTENTION: 'text-accent-blue',
  WARNING: 'text-accent-amber',
  SHADOWBANNED: 'text-accent-violet',
  BANNED: 'text-accent-red',
  REMOVED: 'text-accent-violet',
}

export const STATUS_BG_COLORS: Record<AccountStatus, string> = {
  NEW: 'bg-foreground-muted/12',
  WARMING: 'bg-accent-magenta/12',
  ACTIVE: 'bg-accent-cyan/12',
  IDLE: 'bg-foreground-muted/12',
  COOLDOWN: 'bg-accent-amber/12',
  NEEDS_ATTENTION: 'bg-accent-blue/12',
  WARNING: 'bg-accent-amber/12',
  SHADOWBANNED: 'bg-accent-violet/12',
  BANNED: 'bg-accent-red/12',
  REMOVED: 'bg-accent-violet/12',
}
