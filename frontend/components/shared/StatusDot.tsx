import { cn } from '@/lib/utils'

interface StatusDotProps {
  status: 'ok' | 'slow' | 'error' | 'unknown'
  pulse?: boolean
  label?: string
}

const COLOR_MAP = {
  ok: 'bg-accent-green shadow-[0_0_6px_rgba(0,255,136,0.8)]',
  slow: 'bg-accent-orange shadow-[0_0_6px_rgba(255,140,0,0.8)]',
  error: 'bg-accent-red shadow-[0_0_6px_rgba(255,51,102,0.8)]',
  unknown: 'bg-text-muted',
}

export function StatusDot({ status, pulse = false, label }: StatusDotProps) {
  return (
    <div className="flex items-center gap-2">
      <div className={cn(
        'w-2 h-2 rounded-full',
        COLOR_MAP[status] ?? COLOR_MAP.unknown,
        pulse && 'animate-pulse-slow',
      )} />
      {label && <span className="text-xs text-text-secondary">{label}</span>}
    </div>
  )
}
