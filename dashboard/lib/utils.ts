import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`
  }
  return num.toString()
}

export function truncateMiddle(str: string, maxLength: number = 20): string {
  if (str.length <= maxLength) return str
  const half = Math.floor(maxLength / 2)
  return `${str.slice(0, half)}…${str.slice(-half)}`
}
