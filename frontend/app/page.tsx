'use client'

import { useEffect, useState } from 'react'
import { getDashboardSnapshot, DashboardSnapshot, getTradesPnL, syncTrades, PnLSummary } from '@/lib/api'
import { useWSEvent } from '@/hooks/useWebSocket'
import { ControllerPanel } from '@/components/dashboard/ControllerPanel'
import { IntelligenceChat } from '@/components/dashboard/IntelligenceChat'
import { MarketTable } from '@/components/dashboard/MarketTable'
import { StartupWidget } from '@/components/dashboard/StartupWidget'
import { MetricCard } from '@/components/shared/Card'
import { Spinner } from '@/components/shared/Spinner'
import { formatUSD, formatPct, timeAgo } from '@/lib/utils'

export default function DashboardPage() {
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null)
  const [pnl, setPnl] = useState<PnLSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  useEffect(() => {
    const load = async () => {
      try { setSnapshot(await getDashboardSnapshot()) } catch {}
      try { setPnl(await getTradesPnL(7)) } catch {}
      setLoading(false)
    }
    load()
  }, [])

  const handleSync = async () => {
    setSyncing(true)
    try {
      await syncTrades()
      const p = await getTradesPnL(7)
      setPnl(p)
    } catch { /* ignore */ }
    setSyncing(false)
  }

  const wsSnapshot = useWSEvent<DashboardSnapshot | null>('snapshot', null)
  useEffect(() => { if (wsSnapshot) setSnapshot(wsSnapshot) }, [wsSnapshot])

  const marketUpdate = useWSEvent<unknown>('market_update', null)
  useEffect(() => {
    if (marketUpdate && snapshot) {
      setSnapshot(s => s ? { ...s, markets: marketUpdate as DashboardSnapshot['markets'] } : s)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [marketUpdate])

  const btcUpdate = useWSEvent<{ price: number } | null>('btc_price', null)
  useEffect(() => {
    if (btcUpdate && snapshot) {
      setSnapshot(s => s ? { ...s, btc_spot_usd: btcUpdate.price } : s)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [btcUpdate])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-text-muted">
        <Spinner size={20} />
        <span className="text-xs">Loading dashboard...</span>
      </div>
    )
  }

  if (!snapshot) {
    return (
      <div className="py-16 text-center">
        <p className="text-accent-red text-xs">Failed to connect to API</p>
        <p className="text-text-muted text-xs mt-2">Make sure the backend is running on port 8000</p>
        <code className="text-xs text-text-muted font-mono mt-2 block">
          uvicorn backend.main:app --reload
        </code>
      </div>
    )
  }

  const actNowCount = snapshot.markets.filter(m => m.action === 'ACT_NOW').length
  const avgPremium = snapshot.markets.length > 0
    ? snapshot.markets.reduce((s, m) => s + m.premium_pct, 0) / snapshot.markets.length
    : 0

  return (
    <div className="space-y-5">
      {/* Demo mode banner */}
      {snapshot.demo && (
        <div className="border border-accent-orange/30 bg-accent-orange/5 rounded px-4 py-2.5 text-xs font-mono text-accent-orange">
          DEMO MODE — Add BINANCE_API_KEY and NOONES_API_KEY to .env for live data
        </div>
      )}

      {/* Page title + meta */}
      <div>
        <h1 className="text-xl font-bold text-text-primary">Overview</h1>
        <p className="text-xs text-text-muted mt-1">
          Last scan {timeAgo(snapshot.scanned_at)} · {snapshot.markets.length} markets tracked
        </p>
      </div>

      {/* Metric tiles */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <MetricCard
          label="BTC Spot"
          value={formatUSD(snapshot.btc_spot_usd, 0)}
          color="text-accent-green"
        />
        <MetricCard
          label="7d Trades"
          value={pnl?.total_trades ?? 0}
          sub={pnl && pnl.trades_per_day > 0 ? `${pnl.trades_per_day.toFixed(1)}/day` : 'no data'}
          color="text-accent-blue"
        />
        <MetricCard
          label="7d Volume"
          value={pnl ? `${pnl.total_volume_fiat.toLocaleString(undefined, { maximumFractionDigits: 0 })} ${pnl.daily_pnl?.[0]?.date ? 'SEK' : ''}` : '$0'}
          color="text-accent-green"
        />
        <MetricCard
          label="7d Profit"
          value={formatUSD(pnl?.net_profit_usd ?? 0)}
          sub={pnl && pnl.avg_profit_per_trade > 0 ? `${formatUSD(pnl.avg_profit_per_trade)}/trade` : undefined}
          color={(pnl?.net_profit_usd ?? 0) >= 0 ? 'text-accent-green' : 'text-accent-red'}
        />
        <MetricCard
          label="Avg Confirm"
          value={pnl && pnl.avg_confirmation_lag_sec > 0
            ? `${Math.round(pnl.avg_confirmation_lag_sec / 60)}m`
            : '--'}
          sub={pnl && pnl.avg_confirmation_lag_sec > 300 ? 'Target: <5m' : pnl && pnl.avg_confirmation_lag_sec > 0 ? 'On target' : undefined}
          color={pnl && pnl.avg_confirmation_lag_sec > 300 ? 'text-accent-orange' : 'text-accent-green'}
        />
      </div>

      {/* Sync button */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleSync}
          disabled={syncing}
          className="text-xs font-mono px-3 py-1.5 rounded border border-accent-green/20 bg-accent-green/5 text-accent-green hover:bg-accent-green/10 transition-colors disabled:opacity-50"
        >
          {syncing ? 'Syncing...' : 'Sync Noones Trades'}
        </button>
        {pnl && pnl.total_trades > 0 && (
          <span className="text-xs text-text-muted font-mono">
            {pnl.total_trades} trades synced
          </span>
        )}
      </div>

      {/* Main grid: market table + right panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Market table — spans 2 cols */}
        <div className="lg:col-span-2 space-y-4">
          <MarketTable markets={snapshot.markets} />
          <IntelligenceChat />
        </div>

        {/* Right panel: startup + controller */}
        <div className="space-y-4">
          <StartupWidget />
          <ControllerPanel signals={snapshot.controller_signals} />
        </div>
      </div>
    </div>
  )
}
