import { cn } from '@/lib/utils'

const BADGE_CLASSES: Record<string, string> = {
  ACT_NOW: 'badge-act-now',
  WATCH: 'badge-watch',
  AVOID: 'badge-avoid',
  DATA_ISSUE: 'badge-data-issue',
}

const LABELS: Record<string, string> = {
  ACT_NOW: '⚡ ACT NOW',
  WATCH: '👁 WATCH',
  AVOID: '🔴 AVOID',
  DATA_ISSUE: '⚙️ DATA ISSUE',
}

export function ActionBadge({ action }: { action: string }) {
  return (
    <span className={cn(
      'text-xs font-mono px-2 py-0.5 rounded',
      BADGE_CLASSES[action] ?? 'bg-bg-border text-text-secondary',
    )}>
      {LABELS[action] ?? action}
    </span>
  )
}
