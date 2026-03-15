import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatUSD(n: number, decimals = 2): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(n)
}

export function formatBTC(n: number): string {
  return `₿ ${n.toFixed(6)}`
}

export function formatPct(n: number, sign = true): string {
  const s = sign && n > 0 ? '+' : ''
  return `${s}${n.toFixed(1)}%`
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`
  return `${(seconds / 3600).toFixed(1)}h`
}

export function timeAgo(ts: number): string {
  const diff = Date.now() / 1000 - ts
  if (diff < 60) return `${Math.round(diff)}s ago`
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`
  return `${Math.round(diff / 86400)}d ago`
}

export function actionColor(action: string): string {
  switch (action) {
    case 'ACT_NOW': return 'text-accent-green'
    case 'WATCH': return 'text-accent-orange'
    case 'AVOID': return 'text-accent-red'
    case 'DATA_ISSUE': return 'text-[#8844ff]'
    default: return 'text-text-secondary'
  }
}

export function actionBadgeClass(action: string): string {
  switch (action) {
    case 'ACT_NOW': return 'badge-act-now'
    case 'WATCH': return 'badge-watch'
    case 'AVOID': return 'badge-avoid'
    case 'DATA_ISSUE': return 'badge-data-issue'
    default: return ''
  }
}

export function statusColor(status: string): string {
  switch (status) {
    case 'ok': return 'text-accent-green'
    case 'slow': return 'text-accent-orange'
    case 'error': return 'text-accent-red'
    default: return 'text-text-secondary'
  }
}
