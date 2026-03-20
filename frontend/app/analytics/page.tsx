'use client'

import { useState, useEffect } from 'react'
import { getTrades, getTradesPnL, getDashboardSnapshot } from '@/lib/api'
import { useApi } from '@/hooks/useApi'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, AreaChart, Area, ReferenceLine,
} from 'recharts'
import { Card, MetricCard } from '@/components/shared/Card'
import { Spinner } from '@/components/shared/Spinner'
import { formatUSD, formatPct, timeAgo } from '@/lib/utils'

const COLORS = ['#3ECF8E', '#3B82F6', '#F5A623', '#8844ff', '#FF4757']

// CoinMarketCap API — set NEXT_PUBLIC_CMC_KEY in .env.local
const CMC_KEY = process.env.NEXT_PUBLIC_CMC_KEY ?? ''

interface CmcQuote {
  symbol: string
  name: string
  price: number
  percent_change_24h: number
  percent_change_7d: number
  market_cap: number
}

// Noones-tradeable assets with suggested margin multipliers
const NOONES_ASSETS = [
  { symbol: 'BTC', name: 'Bitcoin', fiat_pairs: ['NGN','ARS','VES','KES','SEK'], margin_base: 0.08 },
  { symbol: 'USDT', name: 'Tether', fiat_pairs: ['NGN','KES'], margin_base: 0.05 },
  { symbol: 'ETH', name: 'Ethereum', fiat_pairs: ['NGN','ARS'], margin_base: 0.07 },
]

async function fetchCmcPrices(): Promise<CmcQuote[]> {
  const symbols = 'BTC,ETH,USDT'
  const res = await fetch(
    `https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest?symbol=${symbols}`,
    { headers: { 'X-CMC_PRO_API_KEY': CMC_KEY, 'Accept': 'application/json' } }
  )
  if (!res.ok) throw new Error('CMC API error')
  const data = await res.json()
  return Object.values(data.data as Record<string, { 0: { symbol: string; name: string; quote: { USD: { price: number; percent_change_24h: number; percent_change_7d: number; market_cap: number } } } }>)
    .map(arr => {
      const item = (arr as unknown as { symbol: string; name: string; quote: { USD: { price: number; percent_change_24h: number; percent_change_7d: number; market_cap: number } } }[])[0]
      return {
        symbol: item.symbol,
        name: item.name,
        price: item.quote.USD.price,
        percent_change_24h: item.quote.USD.percent_change_24h,
        percent_change_7d: item.quote.USD.percent_change_7d,
        market_cap: item.quote.USD.market_cap,
      }
    })
}

// Build projection: at current daily profit rate, project capital growth
function buildProjection(dailyProfit: number, currentCapital: number, days: number): { day: number; capital: number }[] {
  return Array.from({ length: days + 1 }, (_, i) => ({
    day: i,
    capital: Math.round(currentCapital + dailyProfit * i),
  }))
}

export default function AnalyticsPage() {
  const [days, setDays] = useState(30)
  const [cmcData, setCmcData] = useState<CmcQuote[]>([])
  const [cmcLoading, setCmcLoading] = useState(true)
  const [cmcError, setCmcError] = useState<string | null>(null)

  const { data: pnl, loading: pnlLoading } = useApi(() => getTradesPnL(days), [days])
  const { data: trades } = useApi(() => getTrades(100), [])
  const { data: snapshot } = useApi(() => getDashboardSnapshot(), [])

  useEffect(() => {
    fetchCmcPrices()
      .then(setCmcData)
      .catch(e => setCmcError(e.message))
      .finally(() => setCmcLoading(false))
  }, [])

  if (pnlLoading) {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-text-secondary">
        <Spinner size={24} />
        <span className="font-mono text-sm">Loading analytics...</span>
      </div>
    )
  }

  const dailyData = pnl?.daily_pnl ?? []
  const tradeList = trades?.trades ?? []

  // P2P metrics from new schema
  const totalNetProfit = Number(pnl?.net_profit_usd ?? pnl?.total_net_profit ?? 0)
  const totalTrades = Number(pnl?.total_trades ?? pnl?.total_cycles ?? 0)
  const tradesPerDay = Number(pnl?.trades_per_day ?? pnl?.cycles_per_day ?? 0)
  const avgProfitPerTrade = Number(pnl?.avg_profit_per_trade ?? pnl?.avg_profit_per_cycle ?? 0)
  const totalFees = Number(pnl?.total_fees ?? 0)
  const totalVolume = Number(pnl?.total_volume_fiat ?? 0)
  const avgLag = Number(pnl?.avg_confirmation_lag_sec ?? 0)
  const counterparties = pnl?.counterparties ?? []
  const paymentMethods = pnl?.payment_methods ?? {}

  // Current capital from Noones balance
  const noonesBal = snapshot?.balances?.noones
  const currentCapital = noonesBal ? noonesBal.total_usd : 500

  // Projection: 30 and 90 days at current rate
  const dailyProfitRate = days > 0 ? totalNetProfit / days : 0
  const projection30 = buildProjection(dailyProfitRate, currentCapital, 30)
  const projection90 = buildProjection(dailyProfitRate, currentCapital, 90)
  const projected30 = currentCapital + dailyProfitRate * 30
  const projected90 = currentCapital + dailyProfitRate * 90

  // Insights
  const insights: { type: 'good' | 'warn' | 'info'; text: string }[] = []
  if (totalNetProfit > 0) {
    insights.push({ type: 'good', text: `Profitable over ${days} days: ${formatUSD(totalNetProfit)} net gain from ${totalTrades} trades.` })
  } else if (days > 3 && totalTrades === 0) {
    insights.push({ type: 'warn', text: `No trades synced for the last ${days} days. Hit "Sync Noones Trades" on the Overview page.` })
  }
  if (avgLag > 0 && avgLag < 300) {
    insights.push({ type: 'good', text: `Avg confirmation: ${Math.round(avgLag / 60)}min — within the 5min target.` })
  } else if (avgLag >= 300) {
    insights.push({ type: 'warn', text: `Avg confirmation lag: ${Math.round(avgLag / 60)}min. Target is <5min. Release faster after Swish confirmation.` })
  }
  if (tradesPerDay > 10) {
    insights.push({ type: 'good', text: `High velocity: ${tradesPerDay.toFixed(1)} trades/day.` })
  } else if (tradesPerDay > 0 && tradesPerDay < 5) {
    insights.push({ type: 'warn', text: `Low trade rate: ${tradesPerDay.toFixed(1)}/day. Consider increasing active hours.` })
  }
  if (dailyProfitRate > 0) {
    insights.push({ type: 'info', text: `At current pace: ${formatUSD(dailyProfitRate)}/day → ${formatUSD(projected30)} in 30d, ${formatUSD(projected90)} in 90d.` })
  }
  if (totalVolume > 0) {
    insights.push({ type: 'info', text: `Total volume: ${totalVolume.toLocaleString()} fiat over ${days} days.` })
  }
  const topCp = [...counterparties].sort((a, b) => b.volume - a.volume)[0]
  if (topCp) {
    insights.push({ type: 'info', text: `Top counterparty: ${topCp.name} — ${topCp.trades} trades, ${topCp.volume.toLocaleString()} fiat volume.` })
  }

  const hasRealData = tradeList.length > 0 || totalTrades > 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Analytics</h1>
          <p className="text-xs text-text-muted mt-1">PnL, performance insights, capital forecast</p>
        </div>
        <div className="flex items-center gap-2">
          {[7, 30, 90].map(d => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`text-xs font-mono px-2 py-1 rounded transition-colors ${
                days === d
                  ? 'bg-accent-green/10 text-accent-green border border-accent-green/20'
                  : 'text-text-muted hover:text-text-secondary'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {/* PnL Summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <MetricCard
          label="Net Profit"
          value={formatUSD(totalNetProfit)}
          color={totalNetProfit >= 0 ? 'text-accent-green' : 'text-accent-red'}
        />
        <MetricCard
          label="Total Trades"
          value={totalTrades}
          sub={`${tradesPerDay.toFixed(1)}/day avg`}
          color="text-accent-blue"
        />
        <MetricCard
          label="Volume"
          value={totalVolume > 0 ? totalVolume.toLocaleString() : '0'}
          sub="fiat total"
          color="text-accent-green"
        />
        <MetricCard
          label="Avg Confirm"
          value={avgLag > 0 ? `${Math.round(avgLag / 60)}m` : '--'}
          sub={avgLag > 300 ? 'Slow!' : avgLag > 0 ? 'Good' : ''}
          color={avgLag > 300 ? 'text-accent-orange' : 'text-accent-green'}
        />
        <MetricCard
          label="Fees Paid"
          value={formatUSD(totalFees)}
          color="text-accent-orange"
        />
      </div>

      {!hasRealData && (
        <div className="border border-accent-orange/30 bg-accent-orange/5 rounded px-4 py-3 text-xs font-mono text-accent-orange">
          No trade data yet — analytics will populate once trades are logged via the backend.
        </div>
      )}

      {/* Insights */}
      {insights.length > 0 && (
        <Card title="Insights">
          <div className="space-y-2">
            {insights.map((ins, i) => (
              <div key={i} className={`flex items-start gap-2 text-xs font-mono rounded px-3 py-2 border ${
                ins.type === 'good' ? 'text-accent-green bg-accent-green/5 border-accent-green/15' :
                ins.type === 'warn' ? 'text-accent-orange bg-accent-orange/5 border-accent-orange/15' :
                'text-text-primary bg-bg-surface border-bg-border'
              }`}>
                <span className="shrink-0 mt-0.5">
                  {ins.type === 'good' ? '▲' : ins.type === 'warn' ? '⚠' : '→'}
                </span>
                <span>{ins.text}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 2×2 chart grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Capital Growth area chart */}
        <div className="bg-bg-card border border-bg-border rounded-[6px] p-3">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-medium uppercase tracking-wider text-text-muted">Capital Growth</p>
            <p className="text-base font-mono font-bold text-accent-green">
              {formatUSD(currentCapital)}
            </p>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={projection90} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="capGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3ECF8E" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#3ECF8E" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#242424" />
              <XAxis dataKey="day" tick={{ fill: '#333333', fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tickFormatter={v => `$${v}`} tick={{ fill: '#333333', fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 12 }}
                formatter={(v: number) => [formatUSD(v), 'Capital']}
              />
              <Area type="monotone" dataKey="capital" stroke="#3ECF8E" strokeWidth={1.5} fill="url(#capGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Daily P&L bar chart */}
        <div className="bg-bg-card border border-bg-border rounded-[6px] p-3">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-medium uppercase tracking-wider text-text-muted">Daily P&L</p>
            <p className={`text-base font-mono font-bold ${totalNetProfit >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
              {formatUSD(totalNetProfit)}
            </p>
          </div>
          {dailyData.length > 0 ? (
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={dailyData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#242424" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#333333', fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v: string) => v.slice(5)}
                />
                <YAxis
                  tickFormatter={(v: number) => `$${v}`}
                  tick={{ fill: '#333333', fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 12 }}
                  formatter={(v: number) => [formatUSD(v), 'Profit']}
                />
                <ReferenceLine y={0} stroke="#505050" strokeDasharray="3 3" />
                <Bar dataKey="profit" fill="#3ECF8E" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-40 flex items-center justify-center text-sm text-text-muted">
              No data yet
            </div>
          )}
        </div>

        {/* Premium by Market horizontal bars — uses live snapshot.markets, not trade history */}
        <div className="bg-bg-card border border-bg-border rounded-[6px] p-3">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-medium uppercase tracking-wider text-text-muted">Premium by Market</p>
            <p className="text-base font-mono font-bold text-text-primary">
              {snapshot?.markets?.length ?? 0} markets
            </p>
          </div>
          <div className="space-y-2.5">
            {(snapshot?.markets ?? []).length > 0 ? (snapshot?.markets ?? []).map((m, i) => {
              const maxPremium = Math.max(...(snapshot?.markets ?? []).map(x => x.premium_pct), 1)
              const pct = Math.max(0, (m.premium_pct / maxPremium) * 100)
              return (
                <div key={m.currency}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-text-primary font-medium">
                      {m.flag} {m.currency}
                    </span>
                    <span className="text-sm font-mono text-accent-green">
                      +{formatPct(m.premium_pct)}
                    </span>
                  </div>
                  <div className="h-1 rounded-sm" style={{ background: '#242424' }}>
                    <div
                      className="h-full rounded-sm"
                      style={{ width: `${pct}%`, background: COLORS[i % COLORS.length] }}
                    />
                  </div>
                </div>
              )
            }) : (
              <div className="h-32 flex items-center justify-center text-sm text-text-muted">
                No market data
              </div>
            )}
          </div>
        </div>

        {/* 90-Day Forecast */}
        <div className="bg-bg-card border border-bg-border rounded-[6px] p-3">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-medium uppercase tracking-wider text-text-muted">90-Day Forecast</p>
            <p className={`text-base font-mono font-bold ${projected90 >= currentCapital ? 'text-accent-green' : 'text-accent-red'}`}>
              {formatUSD(projected90)}
            </p>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={projection90} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="projGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3ECF8E" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#3ECF8E" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#242424" />
              <XAxis dataKey="day" tick={{ fill: '#333333', fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tickFormatter={v => `$${v}`} tick={{ fill: '#333333', fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 12 }}
                formatter={(v: number) => [formatUSD(v), 'Projected']}
              />
              <ReferenceLine x={30} stroke="#F5A623" strokeDasharray="3 3" label={{ value: '30d', fill: '#F5A623', fontSize: 11 }} />
              <Area type="monotone" dataKey="capital" stroke="#3ECF8E" strokeWidth={1.5} fill="url(#projGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* CoinMarketCap — Tradeable Assets on Noones */}
      <Card title="Tradeable Assets — Noones P2P (via CoinMarketCap)">
        {cmcLoading && (
          <div className="flex items-center gap-2 text-text-muted text-xs font-mono py-4">
            <Spinner size={14} /> Loading CMC prices...
          </div>
        )}
        {cmcError && (
          <p className="text-xs font-mono text-accent-red py-2">CMC API error: {cmcError}</p>
        )}
        {!cmcLoading && !cmcError && (
          <div className="space-y-4">
            <p className="text-xs text-text-secondary font-mono">
              Suggested margins for P2P cycles on Noones based on current spot prices and structural market premiums.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {NOONES_ASSETS.map(asset => {
                const cmc = cmcData.find(c => c.symbol === asset.symbol)
                if (!cmc) return null
                return (
                  <div key={asset.symbol} className="card p-4 border border-bg-border">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <p className="text-sm font-bold text-white">{asset.name}</p>
                        <p className="text-xs text-text-secondary font-mono">{asset.symbol}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-mono font-bold text-accent-green">
                          {formatUSD(cmc.price, asset.symbol === 'USDT' ? 4 : 2)}
                        </p>
                        <p className={`text-xs font-mono ${cmc.percent_change_24h >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                          {formatPct(cmc.percent_change_24h)} 24h
                        </p>
                      </div>
                    </div>

                    <div className="mb-3">
                      <p className="text-[10px] text-text-muted font-mono uppercase tracking-wider mb-1">Fiat markets on Noones</p>
                      <div className="flex flex-wrap gap-1">
                        {asset.fiat_pairs.map(fiat => {
                          const mkt = snapshot?.markets?.find(m => m.currency === fiat)
                          const premium = mkt?.premium_pct ?? 0
                          const suggestedMargin = Math.max(asset.margin_base * 100, premium * 0.8)
                          return (
                            <div key={fiat} className="text-xs font-mono px-2 py-1 rounded bg-bg-surface border border-bg-border">
                              <span className="text-white font-semibold">{fiat}</span>
                              <span className="text-accent-green ml-1">+{suggestedMargin.toFixed(1)}%</span>
                            </div>
                          )
                        })}
                      </div>
                    </div>

                    <div className="text-xs font-mono">
                      <div className="flex justify-between text-text-muted">
                        <span>7d change</span>
                        <span className={cmc.percent_change_7d >= 0 ? 'text-accent-green' : 'text-accent-red'}>
                          {formatPct(cmc.percent_change_7d)}
                        </span>
                      </div>
                      <div className="flex justify-between text-text-muted mt-0.5">
                        <span>Base margin</span>
                        <span className="text-white">+{(asset.margin_base * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </Card>

      {/* Counterparty & Payment breakdown */}
      {(counterparties.length > 0 || Object.keys(paymentMethods).length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {counterparties.length > 0 && (
            <Card title="Counterparties">
              <div className="space-y-2">
                {counterparties.map(cp => (
                  <div key={cp.name} className="flex items-center justify-between py-1.5 border-b border-bg-border/50 last:border-0">
                    <div>
                      <span className="text-sm font-mono text-text-primary font-medium">{cp.name}</span>
                      <span className="text-xs text-text-muted ml-2">{cp.trades} trades</span>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-mono text-accent-green">{cp.volume.toLocaleString()}</span>
                      <span className="text-xs text-text-muted ml-2">
                        {cp.avg_lag_sec > 0 ? `${Math.round(cp.avg_lag_sec / 60)}m avg` : ''}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
          {Object.keys(paymentMethods).length > 0 && (
            <Card title="Payment Methods">
              <div className="space-y-3">
                {Object.entries(paymentMethods)
                  .sort((a, b) => b[1].count - a[1].count)
                  .map(([method, data]) => {
                    const totalCount = Object.values(paymentMethods).reduce((s, v) => s + v.count, 0)
                    const pct = totalCount > 0 ? (data.count / totalCount) * 100 : 0
                    return (
                      <div key={method} className="border-b border-bg-border/50 pb-2 last:border-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-mono text-text-primary font-medium">{method}</span>
                          <span className="text-xs font-mono text-text-muted">{data.count} trades ({pct.toFixed(0)}%)</span>
                        </div>
                        <div className="h-1 rounded-sm mb-2" style={{ background: '#242424' }}>
                          <div className="h-full rounded-sm bg-accent-green" style={{ width: `${pct}%` }} />
                        </div>
                        <div className="flex gap-4 text-[11px] font-mono">
                          <span className="text-text-muted">
                            Vol: <span className="text-text-primary">{data.volume.toLocaleString()}</span>
                          </span>
                          <span className="text-text-muted">
                            Profit: <span className="text-accent-green">{formatUSD(data.profit)}</span>
                          </span>
                          <span className="text-text-muted">
                            Fees: <span className="text-accent-orange">{formatUSD(data.fees)}</span>
                          </span>
                        </div>
                      </div>
                    )
                  })}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Recent trades */}
      <Card title="Recent P2P Trades">
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="border-b border-bg-border">
                {['Time', 'Buyer', 'Fiat', 'Crypto', 'Method', 'Confirm', 'Status'].map(h => (
                  <th key={h} className="text-left text-white py-2 pr-4 font-semibold">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tradeList.slice(0, 20).map((t, i) => (
                <tr key={t.trade_hash ?? t.id ?? i} className="border-b border-bg-border/50 hover:bg-bg-hover transition-colors">
                  <td className="py-2 pr-4 text-text-secondary">{timeAgo(t.completed_at ?? t.opened_at)}</td>
                  <td className="py-2 pr-4 text-white font-semibold">{t.counterparty || '—'}</td>
                  <td className="py-2 pr-4 text-accent-green">
                    {(t.fiat_amount ?? 0).toLocaleString()} {t.fiat_currency || ''}
                  </td>
                  <td className="py-2 pr-4 text-text-primary">
                    {(t.crypto_amount ?? 0).toFixed(2)} {t.asset || 'USDT'}
                  </td>
                  <td className="py-2 pr-4 text-text-secondary">{t.payment_method || '—'}</td>
                  <td className={`py-2 pr-4 ${
                    (t.confirmation_lag_sec ?? 0) > 300 ? 'text-accent-orange' : 'text-accent-green'
                  }`}>
                    {t.confirmation_lag_sec != null ? `${Math.round(t.confirmation_lag_sec / 60)}m` : '—'}
                  </td>
                  <td className="py-2 pr-4">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                      t.status === 'completed' ? 'text-accent-green bg-accent-green/10' :
                      t.status === 'cancelled' ? 'text-accent-red bg-accent-red/10' :
                      'text-accent-orange bg-accent-orange/10'
                    }`}>
                      {t.status}
                    </span>
                  </td>
                </tr>
              ))}
              {tradeList.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-text-muted">
                    No trades synced yet — click "Sync Noones Trades" on the Overview page
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
