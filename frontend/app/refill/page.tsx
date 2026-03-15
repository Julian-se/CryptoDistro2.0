'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getRefillPipeline, triggerRefillScan, RefillMethod } from '@/lib/api'
import { useApi } from '@/hooks/useApi'
import { Card } from '@/components/shared/Card'
import { Spinner } from '@/components/shared/Spinner'
import { cn } from '@/lib/utils'

const STATUS_BADGE: Record<string, { label: string; class: string }> = {
  verified: { label: '✅ Verified', class: 'text-accent-green bg-accent-green/10 border-accent-green/20' },
  unconfirmed: { label: '⚠️ Unconfirmed', class: 'text-accent-orange bg-accent-orange/10 border-accent-orange/20' },
  no_route: { label: '❌ No Route', class: 'text-accent-red bg-accent-red/10 border-accent-red/20' },
}

// Graphical interactive step-by-step pipeline visualization
function PipelineFlow({ steps, notes, evidence_url }: {
  steps: string[]
  notes?: string
  evidence_url?: string
}) {
  const [activeStep, setActiveStep] = useState<number | null>(null)

  // Color each step by type
  const stepColor = (step: string) => {
    const s = step.toLowerCase()
    if (s.includes('fiat') || s.includes('ngn') || s.includes('kes') || s.includes('ars') || s.includes('ves') || s.includes('sek') || s.includes('usd') || s.includes('zelle') || s.includes('mpesa') || s.includes('opay') || s.includes('bitnob') || s.includes('mercado') || s.includes('swish') || s.includes('safello') || s.includes('revolut') || s.includes('lemon') || s.includes('pelerin') || s.includes('strike'))
      return { bg: 'bg-accent-orange/10 border-accent-orange/30', text: 'text-white', dot: 'bg-accent-orange' }
    if (s.includes('lightning') || s.includes('ln') || s.includes('blink') || s.includes('phoenix'))
      return { bg: 'bg-[#8844ff]/10 border-[#8844ff]/30', text: 'text-white', dot: 'bg-[#8844ff]' }
    if (s.includes('noones'))
      return { bg: 'bg-accent-green/10 border-accent-green/30', text: 'text-white', dot: 'bg-accent-green' }
    if (s.includes('btc') || s.includes('bitcoin'))
      return { bg: 'bg-[#f0b90b]/10 border-[#f0b90b]/30', text: 'text-white', dot: 'bg-[#f0b90b]' }
    return { bg: 'bg-bg-surface border-bg-border', text: 'text-text-primary', dot: 'bg-text-secondary' }
  }

  // Step descriptions for interactive tooltip
  const STEP_DESCRIPTIONS: Record<string, string> = {
    'receive fiat': 'Customer sends you fiat payment (e.g. bank transfer, mobile money)',
    'bitnob': 'Log in to Bitnob — send the fiat amount to buy BTC directly in the app',
    'bitnob built-in ln': 'Bitnob has a built-in Lightning wallet — BTC is already in LN format',
    'noones': 'Send via Lightning to your Noones Lightning address — arrives in seconds',
    'lightning': 'Lightning Network — instant settlement, near-zero fees',
    'blink': 'Blink wallet (Bitcoin Beach) — receive LN payment, then send to Noones',
    'phoenix': 'Phoenix wallet — receive LN payment, then send to Noones LN address',
    'strike': 'Strike app — Zelle in, buy BTC, send via Lightning to Noones',
    'lemon cash': 'Lemon Cash — Mercado Pago in, buy BTC, withdraw via Lightning',
    'mt pelerin': 'MT Pelerin — bank transfer in, buy BTC, withdraw via Lightning (Breez SDK)',
    'safello': 'Safello — Swish/Revolut in, buy BTC. Note: on-chain withdrawal only (~$12 fee)',
    'revolut → relai': 'Revolut → SEPA Instant → Relai (2% fee, Lightning via Breez SDK, 5-15 min)',
  }

  function getDesc(step: string): string {
    const key = Object.keys(STEP_DESCRIPTIONS).find(k => step.toLowerCase().includes(k))
    return key ? STEP_DESCRIPTIONS[key] : step
  }

  return (
    <div className="mt-3">
      {/* Flow diagram */}
      <div className="flex items-center gap-0 overflow-x-auto pb-2">
        {steps.map((step, i) => {
          const colors = stepColor(step)
          const isActive = activeStep === i
          return (
            <div key={i} className="flex items-center shrink-0">
              {/* Step node */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => setActiveStep(isActive ? null : i)}
                className={cn(
                  'relative px-3 py-2 rounded-lg border text-xs font-semibold transition-all',
                  colors.bg, colors.text,
                  isActive ? 'ring-2 ring-white/20 scale-105' : '',
                )}
              >
                <div className="flex items-center gap-1.5">
                  <div className={cn('w-1.5 h-1.5 rounded-full shrink-0', colors.dot)} />
                  <span className="whitespace-nowrap">{step}</span>
                </div>
                <div className="absolute -top-1.5 -left-1.5 w-4 h-4 rounded-full bg-bg-border text-text-muted text-[9px] flex items-center justify-center font-mono">
                  {i + 1}
                </div>
              </motion.button>

              {/* Arrow */}
              {i < steps.length - 1 && (
                <div className="flex items-center px-1">
                  <motion.div
                    animate={{ x: [0, 3, 0] }}
                    transition={{ repeat: Infinity, duration: 1.5, delay: i * 0.2 }}
                    className="text-accent-green text-base"
                  >
                    →
                  </motion.div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Step detail popup */}
      <AnimatePresence>
        {activeStep !== null && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="mt-2 p-3 rounded-lg bg-bg-surface border border-accent-green/20 text-xs font-mono"
          >
            <p className="text-accent-green font-semibold mb-1">Step {activeStep + 1}: {steps[activeStep]}</p>
            <p className="text-text-primary">{getDesc(steps[activeStep])}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Notes & docs */}
      {notes && <p className="text-xs text-text-secondary mt-2 italic">{notes}</p>}
      {evidence_url && (
        <a href={evidence_url} target="_blank" rel="noopener noreferrer"
          className="text-xs text-accent-blue hover:underline mt-1 block font-mono">
          ↗ Documentation
        </a>
      )}
    </div>
  )
}

// Method card with graphical pipeline
function MethodCard({ method, index }: { method: RefillMethod; index: number }) {
  const [showPipeline, setShowPipeline] = useState(false)
  const badge = STATUS_BADGE[method.status] ?? STATUS_BADGE.unconfirmed

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="card p-4"
    >
      {/* Header row */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-bold text-white">{method.name}</p>
            <span className={cn('text-xs px-2 py-0.5 rounded border font-mono', badge.class)}>
              {badge.label}
            </span>
          </div>
          <p className="text-xs text-text-secondary font-mono mt-0.5">
            {method.buy_service} → {method.lightning_wallet} → Noones
          </p>
        </div>
        <div className="text-right text-xs font-mono ml-4 shrink-0">
          <p className="text-white font-semibold">{method.total_time}</p>
          <p className="text-text-secondary">{method.fees}</p>
        </div>
      </div>

      {/* Meta grid */}
      <div className="mt-3 grid grid-cols-3 gap-3 text-xs font-mono">
        <div className="bg-bg-surface rounded px-2 py-1.5 border border-bg-border">
          <p className="text-text-secondary uppercase text-[10px] tracking-wider">KYC</p>
          <p className="text-white font-semibold mt-0.5">{method.kyc}</p>
        </div>
        <div className="bg-bg-surface rounded px-2 py-1.5 border border-bg-border">
          <p className="text-text-secondary uppercase text-[10px] tracking-wider">Risk</p>
          <p className={`font-semibold mt-0.5 ${
            method.risk === 'low' ? 'text-accent-green' :
            method.risk === 'medium' ? 'text-accent-orange' : 'text-accent-red'
          }`}>{method.risk}</p>
        </div>
        <div className="bg-bg-surface rounded px-2 py-1.5 border border-bg-border">
          <p className="text-text-secondary uppercase text-[10px] tracking-wider">Currency</p>
          <p className="text-white font-semibold mt-0.5">{method.currency}</p>
        </div>
      </div>

      {/* Show pipeline toggle */}
      <button
        onClick={() => setShowPipeline(v => !v)}
        className={cn(
          'mt-3 text-xs font-mono px-3 py-1.5 rounded border transition-all w-full text-left flex items-center gap-2',
          showPipeline
            ? 'bg-accent-green/10 text-accent-green border-accent-green/20'
            : 'bg-bg-surface text-text-secondary border-bg-border hover:text-white hover:border-accent-green/20',
        )}
      >
        <span>{showPipeline ? '▼' : '▶'}</span>
        <span>{showPipeline ? 'Hide Pipeline' : 'Show Pipeline'}</span>
        <span className="ml-auto text-text-muted text-[10px]">{method.pipeline.length} steps — click any step for details</span>
      </button>

      <AnimatePresence>
        {showPipeline && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <PipelineFlow
              steps={method.pipeline}
              notes={method.notes}
              evidence_url={method.evidence_url}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// Manual method addition form
interface ManualMethod {
  name: string
  currency: string
  buy_service: string
  lightning_wallet: string
  steps: string[]
  total_time: string
  fees: string
  kyc: string
  risk: string
  notes: string
  newStep: string
}

function AddMethodForm({ onAdd }: { onAdd: (m: RefillMethod) => void }) {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<ManualMethod>({
    name: '', currency: '', buy_service: '', lightning_wallet: '',
    steps: [], total_time: '', fees: '', kyc: 'none', risk: 'low', notes: '', newStep: '',
  })

  function addStep() {
    if (!form.newStep.trim()) return
    setForm(f => ({ ...f, steps: [...f.steps, f.newStep.trim()], newStep: '' }))
  }

  function removeStep(i: number) {
    setForm(f => ({ ...f, steps: f.steps.filter((_, idx) => idx !== i) }))
  }

  function submit() {
    if (!form.name || !form.currency || form.steps.length < 2) return
    onAdd({
      name: form.name,
      currency: form.currency,
      buy_service: form.buy_service || form.steps[0],
      lightning_wallet: form.lightning_wallet || form.steps[form.steps.length - 2] || '',
      pipeline: form.steps,
      total_time: form.total_time || '?',
      fees: form.fees || '?',
      kyc: form.kyc,
      risk: form.risk,
      status: 'unconfirmed',
      notes: form.notes || undefined,
    })
    setForm({ name: '', currency: '', buy_service: '', lightning_wallet: '', steps: [], total_time: '', fees: '', kyc: 'none', risk: 'low', notes: '', newStep: '' })
    setOpen(false)
  }

  return (
    <div className="card border-dashed border-2 border-bg-border">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full p-4 flex items-center gap-2 text-sm font-mono text-text-secondary hover:text-white transition-colors"
      >
        <span className="text-accent-green text-lg">{open ? '−' : '+'}</span>
        <span>Add Refill Method Manually</span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden px-4 pb-4"
          >
            <div className="grid grid-cols-2 gap-3 mb-3">
              {[
                { key: 'name', placeholder: 'Method name (e.g. Swish)' },
                { key: 'currency', placeholder: 'Currency (SEK, NGN…)' },
                { key: 'buy_service', placeholder: 'Buy BTC service (e.g. Safello)' },
                { key: 'lightning_wallet', placeholder: 'LN wallet (e.g. Blink)' },
                { key: 'total_time', placeholder: 'Total time (e.g. 5-10 min)' },
                { key: 'fees', placeholder: 'Fees (e.g. ~1.5%)' },
              ].map(({ key, placeholder }) => (
                <input
                  key={key}
                  value={form[key as keyof ManualMethod] as string}
                  onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                  placeholder={placeholder}
                  className="bg-bg-surface border border-bg-border rounded px-3 py-2 text-xs font-mono text-white placeholder-text-muted focus:outline-none focus:border-accent-green/40"
                />
              ))}
            </div>

            <div className="grid grid-cols-2 gap-3 mb-3">
              <select
                value={form.kyc}
                onChange={e => setForm(f => ({ ...f, kyc: e.target.value }))}
                className="bg-bg-surface border border-bg-border rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-accent-green/40"
              >
                <option value="none">KYC: None</option>
                <option value="email">KYC: Email</option>
                <option value="id">KYC: ID required</option>
              </select>
              <select
                value={form.risk}
                onChange={e => setForm(f => ({ ...f, risk: e.target.value }))}
                className="bg-bg-surface border border-bg-border rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-accent-green/40"
              >
                <option value="low">Risk: Low</option>
                <option value="medium">Risk: Medium</option>
                <option value="high">Risk: High</option>
              </select>
            </div>

            {/* Pipeline step builder */}
            <div className="mb-3">
              <p className="text-xs text-text-secondary font-mono mb-2">Pipeline Steps (in order)</p>
              <div className="flex gap-2 mb-2">
                <input
                  value={form.newStep}
                  onChange={e => setForm(f => ({ ...f, newStep: e.target.value }))}
                  onKeyDown={e => e.key === 'Enter' && addStep()}
                  placeholder="Add step (e.g. Receive SEK via Swish)"
                  className="flex-1 bg-bg-surface border border-bg-border rounded px-3 py-2 text-xs font-mono text-white placeholder-text-muted focus:outline-none focus:border-accent-green/40"
                />
                <button
                  onClick={addStep}
                  className="px-3 py-2 rounded bg-accent-green/10 text-accent-green border border-accent-green/20 text-xs font-mono hover:bg-accent-green/20"
                >
                  + Add
                </button>
              </div>

              {/* Live pipeline preview */}
              {form.steps.length > 0 && (
                <div className="flex items-center gap-1 flex-wrap p-3 rounded bg-bg-surface border border-bg-border">
                  {form.steps.map((step, i) => (
                    <div key={i} className="flex items-center gap-1">
                      <div className="flex items-center gap-1 px-2 py-1 rounded bg-bg-border text-white text-xs font-semibold border border-bg-border relative group">
                        <span>{step}</span>
                        <button
                          onClick={() => removeStep(i)}
                          className="ml-1 text-text-muted hover:text-accent-red text-[10px]"
                        >×</button>
                      </div>
                      {i < form.steps.length - 1 && <span className="text-accent-green text-xs">→</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <textarea
              value={form.notes}
              onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
              placeholder="Notes (optional)"
              rows={2}
              className="w-full bg-bg-surface border border-bg-border rounded px-3 py-2 text-xs font-mono text-white placeholder-text-muted focus:outline-none focus:border-accent-green/40 mb-3 resize-none"
            />

            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setOpen(false)}
                className="px-3 py-1.5 text-xs font-mono text-text-muted hover:text-text-secondary"
              >
                Cancel
              </button>
              <button
                onClick={submit}
                disabled={!form.name || !form.currency || form.steps.length < 2}
                className="px-4 py-1.5 rounded bg-accent-green/10 text-accent-green border border-accent-green/20 text-xs font-mono hover:bg-accent-green/20 disabled:opacity-40"
              >
                Add Method
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function RefillPage() {
  const { data: pipeline, loading, error, refetch } = useApi(() => getRefillPipeline())
  const [scanning, setScanning] = useState(false)
  const [scanResult, setScanResult] = useState<string | null>(null)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [selectedMarket, setSelectedMarket] = useState<string>('all')
  const [manualMethods, setManualMethods] = useState<(RefillMethod & { market: string })[]>([])

  async function handleScan(method: string) {
    setScanning(true)
    setScanResult(null)
    try {
      const res = await triggerRefillScan(method)
      setScanResult(res.analysis || 'Scan complete')
      await refetch()
    } catch (e) {
      setScanResult(`Error: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setScanning(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-text-secondary">
        <Spinner size={24} />
        <span className="font-mono text-sm">Loading refill pipeline...</span>
      </div>
    )
  }

  if (error || !pipeline) {
    return (
      <div className="text-center py-16">
        <p className="text-accent-red font-mono text-sm">{error || 'No pipeline data'}</p>
      </div>
    )
  }

  const allMethods = pipeline.markets.flatMap(m => m.methods)
  const verifiedCount = allMethods.filter(m => m.status === 'verified').length
  const gapCount = allMethods.filter(m => m.status === 'no_route').length

  const displayedMarkets = pipeline.markets.map(market => ({
    ...market,
    methods: market.methods.filter(m =>
      filterStatus === 'all' || m.status === filterStatus
    ),
  })).filter(m => selectedMarket === 'all' || m.currency === selectedMarket)

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold font-mono text-text-primary">BTC Refill Pipeline</h1>
          <p className="text-sm text-text-secondary mt-1">
            Fiat received → Buy BTC → Lightning → Noones. Click any step for details.
          </p>
        </div>
        <button
          onClick={() => handleScan('all')}
          disabled={scanning}
          className="flex items-center gap-2 px-3 py-1.5 rounded bg-accent-green/10 text-accent-green border border-accent-green/20 text-xs font-mono hover:bg-accent-green/20 disabled:opacity-50"
        >
          {scanning ? <Spinner size={12} /> : '🔍'}
          {scanning ? 'Scanning...' : 'Rescan All'}
        </button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-3">
        <div className="card p-3 text-center">
          <p className="text-xl font-mono font-bold text-accent-green">{verifiedCount}</p>
          <p className="text-xs text-white font-semibold mt-0.5">Verified Routes</p>
        </div>
        <div className="card p-3 text-center">
          <p className="text-xl font-mono font-bold text-accent-orange">
            {allMethods.filter(m => m.status === 'unconfirmed').length}
          </p>
          <p className="text-xs text-white font-semibold mt-0.5">Needs Verification</p>
        </div>
        <div className="card p-3 text-center">
          <p className="text-xl font-mono font-bold text-accent-red">{gapCount}</p>
          <p className="text-xs text-white font-semibold mt-0.5">Gaps</p>
        </div>
      </div>

      {scanResult && (
        <div className="border border-accent-blue/30 bg-accent-blue/5 rounded px-4 py-3 text-xs font-mono text-white">
          {scanResult}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-1">
          {['all', 'verified', 'unconfirmed', 'no_route'].map(s => (
            <button key={s} onClick={() => setFilterStatus(s)}
              className={cn('text-xs font-mono px-2 py-1 rounded transition-colors border',
                filterStatus === s
                  ? 'bg-accent-green/10 text-white border-accent-green/20'
                  : 'text-text-secondary hover:text-white border-transparent',
              )}>
              {s === 'all' ? 'All' : s}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-1">
          {['all', ...pipeline.markets.map(m => m.currency)].map(c => (
            <button key={c} onClick={() => setSelectedMarket(c)}
              className={cn('text-xs font-mono px-2 py-1 rounded transition-colors border',
                selectedMarket === c
                  ? 'bg-accent-blue/10 text-white border-accent-blue/20'
                  : 'text-text-secondary hover:text-white border-transparent',
              )}>
              {c === 'all' ? 'All Markets' : c}
            </button>
          ))}
        </div>
      </div>

      {/* Pipeline markets */}
      {displayedMarkets.map(market => (
        <div key={market.currency}>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xl">{market.flag}</span>
            <h2 className="text-sm font-bold font-mono text-white">{market.name} ({market.currency})</h2>
          </div>
          <div className="space-y-2">
            {market.methods.map((method, i) => (
              <MethodCard key={method.name} method={method} index={i} />
            ))}
            {market.methods.length === 0 && (
              <p className="text-xs text-text-secondary font-mono px-2">No methods match filter</p>
            )}
          </div>
        </div>
      ))}

      {/* Manual methods section */}
      {manualMethods.length > 0 && (
        <div>
          <h2 className="text-sm font-bold font-mono text-white mb-3">Custom Methods</h2>
          <div className="space-y-2">
            {manualMethods.map((m, i) => (
              <MethodCard key={`manual-${i}`} method={m} index={i} />
            ))}
          </div>
        </div>
      )}

      {/* Add manually */}
      <AddMethodForm onAdd={m => setManualMethods(prev => [...prev, { ...m, market: m.currency }])} />
    </div>
  )
}
