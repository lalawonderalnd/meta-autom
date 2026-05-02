import { useEffect, useState } from 'react'
import { supabase } from './client'

type SupabaseTable = 'accounts' | 'devices' | 'jobs'

export function useRealtimeTable<T extends { id: string }>(
  table: SupabaseTable,
  initialRows: T[]
): T[] {
  const [rows, setRows] = useState<T[]>(initialRows)

  useEffect(() => {
    const channel = supabase
      .channel(`${table}-changes`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table,
        },
        (payload) => {
          const { eventType, new: newRow, old: oldRow } = payload

          if (eventType === 'INSERT' && newRow) {
            setRows((prev) => [...prev, newRow as T])
          } else if (eventType === 'UPDATE' && newRow) {
            setRows((prev) =>
              prev.map((row) => (row.id === (newRow as any).id ? (newRow as T) : row))
            )
          } else if (eventType === 'DELETE' && oldRow) {
            setRows((prev) => prev.filter((row) => row.id !== (oldRow as any).id))
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [table])

  return rows
}
