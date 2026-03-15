import { cn } from '@/lib/utils'

interface CardProps {
  children: React.ReactNode
  className?: string
  title?: string
  titleRight?: React.ReactNode
}

export function Card({ children, className, title, titleRight }: CardProps) {
  return (
    <div className={cn('card p-4', className)}>
      {(title || titleRight) && (
        <div className="flex items-center justify-between mb-3">
          {title && (
            <h3 className="text-xs font-medium uppercase tracking-wider text-text-muted">
              {title}
            </h3>
          )}
          {titleRight}
        </div>
      )}
      {children}
    </div>
  )
}

export function MetricCard({
  label,
  value,
  sub,
  color = 'text-text-primary',
  className,
}: {
  label: string
  value: string | number
  sub?: string
  color?: string
  className?: string
}) {
  return (
    <div className={cn('card p-4', className)}>
      <p className="text-xs uppercase tracking-wider text-text-muted mb-1">{label}</p>
      <p className={cn('font-mono font-bold text-xl', color)}>{value}</p>
      {sub && <p className="text-xs text-text-muted mt-1">{sub}</p>}
    </div>
  )
}
