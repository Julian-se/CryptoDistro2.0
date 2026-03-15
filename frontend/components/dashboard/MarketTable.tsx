import { MarketSummary } from '@/lib/api'
import { cn } from '@/lib/utils'
import { formatPct } from '@/lib/utils'

interface Props {
  markets: MarketSummary[]
}

const SIGNAL_CLASS: Record<string, string> = {
  ACT_NOW:    'badge-act-now',
  WATCH:      'badge-watch',
  AVOID:      'badge-avoid',
  DATA_ISSUE: 'badge-data-issue',
}

const SIGNAL_LABEL: Record<string, string> = {
  ACT_NOW:    'ACT NOW',
  WATCH:      'WATCH',
  AVOID:      'AVOID',
  DATA_ISSUE: 'DATA',
}

export function MarketTable({ markets }: Props) {
  const actNowCount = markets.filter(m => m.action === 'ACT_NOW').length

  return (
    <div className="bg-bg-card border border-bg-border rounded-[6px] overflow-hidden">
      {/* Table header row */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-bg-border">
        <span className="text-xs font-medium uppercase tracking-wider text-text-muted">
          Market Signals
        </span>
        {actNowCount > 0 && (
          <span className="text-xs font-mono font-bold text-accent-green">
            {actNowCount} active
          </span>
        )}
      </div>

      {/* Column headers */}
      <table className="w-full">
        <thead>
          <tr className="border-b border-bg-sub">
            {['Market', 'Premium', 'Margin', 'FX Rate', 'Methods', 'Signal'].map(h => (
              <th
                key={h}
                className="text-left px-4 py-2.5 text-xs font-medium uppercase tracking-wider text-text-muted"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {markets.map(m => (
            <tr
              key={m.currency}
              className="border-b border-bg-sub last:border-0 hover:bg-white/[0.02] transition-colors"
            >
              {/* Market */}
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="text-base">{m.flag}</span>
                  <span className="text-sm font-medium text-text-primary">
                    {m.currency}
                  </span>
                </div>
              </td>

              {/* Premium */}
              <td className="px-4 py-3">
                <span
                  className={cn(
                    'font-mono font-semibold text-sm',
                    m.premium_pct >= 6 ? 'text-accent-green' : 'text-text-muted',
                  )}
                >
                  {m.premium_pct >= 0 ? '+' : ''}{formatPct(m.premium_pct)}
                </span>
              </td>

              {/* Margin */}
              <td className="px-4 py-3">
                <span className="font-mono text-sm text-text-primary">
                  {formatPct(m.suggested_margin)}
                </span>
              </td>

              {/* FX Rate */}
              <td className="px-4 py-3">
                <span className="font-mono text-sm text-text-muted">
                  {m.fx_rate > 0 ? m.fx_rate.toLocaleString(undefined, { maximumFractionDigits: 0 }) : '—'}
                </span>
              </td>

              {/* Payment methods */}
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {(m.payment_methods ?? []).slice(0, 3).map(pm => (
                    <span
                      key={pm.slug}
                      className="text-[11px] px-2 py-0.5 rounded font-medium text-accent-green border border-accent-green-border"
                      style={{ background: 'rgba(62,207,142,0.07)' }}
                    >
                      {pm.label}
                    </span>
                  ))}
                  {(m.payment_methods ?? []).length > 3 && (
                    <span className="text-xs text-text-dim">
                      +{m.payment_methods.length - 3}
                    </span>
                  )}
                </div>
              </td>

              {/* Signal */}
              <td className="px-4 py-3">
                <span
                  className={cn(
                    'text-xs font-bold px-2.5 py-1 rounded',
                    SIGNAL_CLASS[m.action] ?? 'badge-data-issue',
                  )}
                >
                  {SIGNAL_LABEL[m.action] ?? m.action}
                </span>
              </td>
            </tr>
          ))}

          {markets.length === 0 && (
            <tr>
              <td colSpan={6} className="px-4 py-8 text-center text-sm text-text-muted">
                No market data
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
