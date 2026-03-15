'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { runSimulation, SimulationResult, SimRequest } from '@/lib/api'
import { SimChart } from '@/components/simulation/SimChart'
import { Card, MetricCard } from '@/components/shared/Card'
import { Spinner } from '@/components/shared/Spinner'
import { formatUSD } from '@/lib/utils'

interface ScenarioPreset {
  key: string
  label: string
  description: string
  params: SimRequest
}

const SCENARIOS: ScenarioPreset[] = [
  {
    key: 'conservative',
    label: '🇳🇬 Conservative',
    description: 'Nigeria — 6% spread, 25min fiat, 8h/day',
    params: { scenario: 'conservative', days: 30, runs: 200 },
  },
  {
    key: 'realistic',
    label: '🇦🇷 Realistic',
    description: 'Argentina — 9% spread, 20min fiat, 10h/day',
    params: { scenario: 'realistic', days: 30, runs: 200 },
  },
  {
    key: 'optimistic',
    label: '🇻🇪 Optimistic',
    description: 'Venezuela — 12% spread, 15min fiat, 12h/day',
    params: { scenario: 'optimistic', days: 30, runs: 200 },
  },
]

interface CustomParams {
  spread_pct: number
  fiat_minutes: number
  active_hours: number
  days: number
  runs: number
}

export default function SimulationPage() {
  const [custom, setCustom] = useState<CustomParams>({
    spread_pct: 9, fiat_minutes: 20, active_hours: 10, days: 30, runs: 200,
  })
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeScenario, setActiveScenario] = useState<string>('realistic')

  async function run(req: SimRequest) {
    setLoading(true)
    setError(null)
    try {
      const res = await runSimulation(req)
      setResult(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  function runCustom() {
    setActiveScenario('custom')
    run({ scenario: 'custom', ...custom })
  }

  const dailyCyclesLn = Math.floor((60 / custom.fiat_minutes) * custom.active_hours)
  const estDailyGross = (custom.spread_pct / 100) * 60 * dailyCyclesLn

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold font-mono text-text-primary">Simulation</h1>
        <p className="text-sm text-text-secondary mt-1">
          Monte Carlo P2P cycle model — Lightning velocity vs fiat verification ceiling
        </p>
      </div>

      {/* Preset scenarios */}
      <div className="grid grid-cols-3 gap-3">
        {SCENARIOS.map(s => (
          <button
            key={s.key}
            onClick={() => { setActiveScenario(s.key); run(s.params) }}
            className={`text-left card p-4 transition-all hover:border-accent-green/30 ${
              activeScenario === s.key ? 'border-accent-green/40 bg-accent-green/5' : ''
            }`}
          >
            <p className="text-sm font-semibold text-text-primary">{s.label}</p>
            <p className="text-xs text-text-muted mt-1">{s.description}</p>
          </button>
        ))}
      </div>

      {/* Custom parameters */}
      <Card title="Custom Parameters">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { key: 'spread_pct', label: 'Spread %', min: 1, max: 20, step: 0.5 },
            { key: 'fiat_minutes', label: 'Fiat Verify (min)', min: 5, max: 60, step: 1 },
            { key: 'active_hours', label: 'Hours/Day', min: 1, max: 16, step: 1 },
            { key: 'days', label: 'Days', min: 7, max: 90, step: 1 },
            { key: 'runs', label: 'MC Runs', min: 50, max: 500, step: 50 },
          ].map(({ key, label, min, max, step }) => (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-mono text-text-secondary">{label}</label>
                <span className="text-xs font-mono text-accent-green font-bold">
                  {custom[key as keyof CustomParams]}
                </span>
              </div>
              <input
                type="range" min={min} max={max} step={step}
                value={custom[key as keyof CustomParams]}
                onChange={e => setCustom(p => ({ ...p, [key]: parseFloat(e.target.value) }))}
                className="w-full accent-accent-green h-1.5 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-text-muted font-mono mt-0.5">
                <span>{min}</span><span>{max}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs text-text-muted font-mono">
            ~{dailyCyclesLn} cycles/day
            · ${estDailyGross.toFixed(0)}/day gross est.
            · ${(estDailyGross * custom.days).toFixed(0)} over {custom.days}d
          </p>
          <button
            onClick={runCustom}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded bg-accent-green/10 text-accent-green border border-accent-green/20 text-sm font-mono hover:bg-accent-green/20 disabled:opacity-50 transition-colors"
          >
            {loading ? <Spinner size={14} /> : '▶'}
            {loading ? 'Running...' : 'Run Custom'}
          </button>
        </div>
      </Card>

      {error && (
        <div className="border border-accent-red/30 bg-accent-red/5 rounded px-4 py-3 text-xs font-mono text-accent-red">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-16 gap-3 text-text-secondary">
          <Spinner size={20} />
          <span className="font-mono text-sm">Running Monte Carlo simulation...</span>
        </div>
      )}

      {result && !loading && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard
              label="30-Day Profit (median)"
              value={formatUSD(result.stats.monthly_net_profit_mean)}
              sub={`P10: ${formatUSD(result.stats.monthly_net_profit_p10)} · P90: ${formatUSD(result.stats.monthly_net_profit_p90)}`}
              color="text-accent-green"
            />
            <MetricCard
              label="Lightning Cycles/Day"
              value={result.stats.cycles_per_day_ln}
              sub={`On-chain: ${result.stats.cycles_per_day_oc}/day`}
              color="text-accent-blue"
            />
            <MetricCard
              label="Velocity Multiplier"
              value={`${result.stats.velocity_multiplier}×`}
              sub="Lightning vs on-chain"
              color={result.stats.velocity_multiplier >= 2 ? 'text-accent-green' : 'text-accent-orange'}
            />
            <MetricCard
              label="Profit per Cycle"
              value={formatUSD(result.stats.profit_per_cycle)}
              sub={`${result.params.spread_pct}% spread on $60`}
              color="text-text-primary"
            />
          </div>

          {/* Chart */}
          <Card title={`Capital Curve — ${result.params.days} days, ${result.params.runs} MC runs`}>
            <SimChart lightning={result.lightning} milestones={result.milestones} />
            <div className="flex items-center gap-4 mt-3 text-xs font-mono text-text-muted">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-0.5 bg-accent-green" />
                <span>Median capital</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-0.5 bg-accent-blue border-dashed" />
                <span>P10/P90 band</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-0.5 bg-text-muted border-dashed" />
                <span>$500 start</span>
              </div>
            </div>
          </Card>

          {/* Milestones */}
          <Card title="Simulation Milestones">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(result.milestones).map(([key, m]) => (
                <div key={key} className="text-center">
                  <p className="text-xs text-text-muted font-mono">Day {m.day}</p>
                  <p className="text-lg font-mono font-bold text-accent-green mt-1">
                    {formatUSD(m.capital)}
                  </p>
                  <p className={`text-xs font-mono mt-0.5 ${m.capital_pct_change >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                    {m.capital_pct_change >= 0 ? '+' : ''}{m.capital_pct_change}%
                  </p>
                </div>
              ))}
            </div>
          </Card>

          {/* Lightning vs On-chain comparison */}
          <Card title="Lightning vs On-Chain Comparison">
            <div className="grid grid-cols-2 gap-6">
              {[
                { label: 'Lightning (Noones built-in)', data: result.lightning, color: 'text-accent-green' },
                { label: 'On-Chain (45min settle)', data: result.onchain, color: 'text-accent-blue' },
              ].map(({ label, data, color }) => {
                const finalCapital = data.capital[data.capital.length - 1] ?? 500
                const profit = data.profit[data.profit.length - 1] ?? 0
                const roi = ((finalCapital - 500) / 500) * 100
                return (
                  <div key={label}>
                    <p className={`text-xs font-mono font-bold ${color} mb-2`}>{label}</p>
                    <div className="space-y-1 text-xs font-mono">
                      <div className="flex justify-between">
                        <span className="text-text-muted">Final capital</span>
                        <span className="text-text-primary">{formatUSD(finalCapital)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-muted">Net profit</span>
                        <span className={color}>{formatUSD(profit)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-muted">ROI</span>
                        <span className={roi >= 0 ? 'text-accent-green' : 'text-accent-red'}>
                          {roi >= 0 ? '+' : ''}{roi.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </Card>
        </motion.div>
      )}

      {!result && !loading && (
        <div className="text-center py-16 text-text-muted font-mono text-sm">
          Click a scenario above or run a custom simulation
        </div>
      )}
    </div>
  )
}
