'use client'

import { ControllerSignals } from '@/lib/api'
import { Card } from '@/components/shared/Card'
import { formatUSD, formatPct, timeAgo } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface ControllerPanelProps {
  signals: ControllerSignals
}

export function ControllerPanel({ signals }: ControllerPanelProps) {
  const { inventory, spread, velocity } = signals

  return (
    <div className="space-y-3">
      {/* Inventory */}
      {inventory && (
        <Card title="Inventory Controller">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-text-muted font-mono">Hours to Empty</p>
              <p className={cn(
                'text-xl font-mono font-bold',
                inventory.predicted_hours_to_empty < 2 ? 'text-accent-red' :
                inventory.predicted_hours_to_empty < 4 ? 'text-accent-orange' : 'text-accent-green',
              )}>
                {inventory.predicted_hours_to_empty === 99 ? '∞' : `${inventory.predicted_hours_to_empty}h`}
              </p>
            </div>
            <div>
              <p className="text-xs text-text-muted font-mono">Confidence</p>
              <p className="text-xl font-mono font-bold text-text-primary">
                {(inventory.confidence * 100).toFixed(0)}%
              </p>
            </div>
          </div>

          {inventory.refill_needed && (
            <div className="mt-2 p-2 rounded bg-accent-red/10 border border-accent-red/20">
              <p className="text-xs font-mono text-accent-red">
                ⚠ REFILL NEEDED — {formatUSD(inventory.recommended_refill_usd ?? 0)} recommended
              </p>
            </div>
          )}
        </Card>
      )}

      {/* Spread */}
      {spread && (
        <Card title="Spread Controller">
          <div className="space-y-1.5">
            {Object.entries(spread.recommended_margins).map(([currency, margin]) => (
              <div key={currency} className="flex items-center justify-between text-xs font-mono">
                <span className="text-text-secondary">{currency}</span>
                <div className="flex items-center gap-3">
                  <span className="text-text-muted">
                    mkt {formatPct(spread.market_premiums[currency] ?? 0)}
                  </span>
                  <span className="text-accent-green font-bold">
                    → {formatPct(margin)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Velocity */}
      {velocity && (
        <Card title="Velocity Controller">
          {velocity.capital_constraint_note && (
            <p className="text-xs text-accent-orange font-mono mb-2">
              {velocity.capital_constraint_note}
            </p>
          )}
          <div className="space-y-1.5">
            {velocity.market_priority.map((currency, i) => (
              <div key={currency} className="flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="text-text-muted">#{i + 1}</span>
                  <span className="text-text-primary">{currency}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-text-muted">
                    {formatUSD(velocity.revenue_per_hour[currency] ?? 0)}/hr
                  </span>
                  <span className="text-accent-blue">
                    {velocity.recommended_hours[currency]}h
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {signals.last_run_at && (
        <p className="text-xs text-text-muted font-mono text-right">
          Last run: {timeAgo(signals.last_run_at)}
        </p>
      )}
    </div>
  )
}
