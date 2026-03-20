const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${path}`)
  return res.json()
}

// ── Dashboard ──────────────────────────────────────────────────────────────────

export const getDashboardSnapshot = () =>
  fetchJSON<DashboardSnapshot>('/api/dashboard/snapshot')

export const getHealth = () =>
  fetchJSON<HealthResponse>('/api/health')

// ── Markets ────────────────────────────────────────────────────────────────────

export const getMarkets = () =>
  fetchJSON<MarketSummary[]>('/api/markets')

export const getMarketDetail = (currency: string) =>
  fetchJSON<MarketDetail>(`/api/markets/${currency}`)

// ── Trades ─────────────────────────────────────────────────────────────────────

export const getTrades = (limit = 50, offset = 0) =>
  fetchJSON<TradesResponse>(`/api/trades?limit=${limit}&offset=${offset}`)

export const getTradesPnL = (days = 30) =>
  fetchJSON<PnLSummary>(`/api/trades/pnl?days=${days}`)

export const getCycles = (status = 'open') =>
  fetchJSON<Cycle[]>(`/api/trades/cycles?status=${status}`)

// ── Simulation ─────────────────────────────────────────────────────────────────

export const runSimulation = (params: SimRequest) =>
  fetchJSON<SimulationResult>('/api/simulation/run', {
    method: 'POST',
    body: JSON.stringify(params),
  })

// ── Refill ─────────────────────────────────────────────────────────────────────

export const getRefillPipeline = () =>
  fetchJSON<RefillPipeline>('/api/refill/pipeline')

export const triggerRefillScan = (method = 'all') =>
  fetchJSON<{ analysis: string; scanned_at: number }>('/api/refill/scan', {
    method: 'POST',
    body: JSON.stringify({ market: method === 'all' ? null : method }),
  })

// ── Intelligence ───────────────────────────────────────────────────────────────

export const askIntelligence = (question: string) =>
  fetchJSON<{ answer: string; duration_ms: number }>('/api/intelligence/ask', {
    method: 'POST',
    body: JSON.stringify({ question }),
  })

export const researchQuestion = (question: string) =>
  fetchJSON<{ answer: string; duration_ms: number }>('/api/intelligence/research', {
    method: 'POST',
    body: JSON.stringify({ question }),
  })

// ── Types ──────────────────────────────────────────────────────────────────────

export interface PaymentMethod {
  slug: string
  label: string
  risk: 'low' | 'medium' | 'high'
}

export interface MarketSummary {
  name: string
  flag: string
  currency: string
  premium_pct: number
  action: 'ACT_NOW' | 'WATCH' | 'AVOID' | 'DATA_ISSUE'
  suggested_margin: number
  offer_count: number
  fx_rate: number
  refill_status: string
  payment_methods: PaymentMethod[]
}

export interface PlatformBalance {
  platform: string
  btc: number
  usdt: number
  total_usd: number
  updated_at: number
}

export interface ActiveTrade {
  cycle_id: string
  started_at: number
  status: string
  buy_platform: string
  sell_platform: string
  asset: string
  notes?: string
}

export interface InventorySignal {
  predicted_hours_to_empty: number
  refill_needed: boolean
  confidence: number
  recommended_refill_usd?: number
  consumption_rate_btc_per_hour?: number
}

export interface SpreadSignal {
  recommended_margins: Record<string, number>
  market_premiums: Record<string, number>
  calibration_notes: Record<string, string>
}

export interface VelocitySignal {
  recommended_hours: Record<string, number>
  market_priority: string[]
  revenue_per_hour: Record<string, number>
  capital_constraint_note: string
}

export interface ControllerSignals {
  inventory?: InventorySignal
  spread?: SpreadSignal
  velocity?: VelocitySignal
  last_run_at?: number
}

export interface DashboardSnapshot {
  btc_spot_usd: number
  markets: MarketSummary[]
  balances: Record<string, PlatformBalance>
  active_trades: ActiveTrade[]
  open_cycles: number
  controller_signals: ControllerSignals
  scanned_at: number
  demo?: boolean
}

export interface HealthComponent {
  status: 'ok' | 'slow' | 'error'
  latency_ms: number
  last_check_at: number
  error?: string
}

export interface HealthResponse {
  status: string
  components: Record<string, HealthComponent>
  scan_metrics: {
    last_scan_at: number
    scan_interval_sec: number
    scans_last_hour: number
    scan_errors_last_hour: number
  }
  api_latency_ms: Record<string, number>
  uptime_sec: number
}

export interface MarketDetail {
  market: MarketSummary
  competitors: Record<string, CompetitorOffer[]>
  premium_history: PremiumPoint[]
}

export interface PremiumPoint {
  timestamp: number
  premium_pct: number
  btc_spot: number
  action: string
  offer_count: number
}

export interface CompetitorOffer {
  seller: string
  price: number
  margin?: number
  trades: number
  score: number
  method: string
  min_amount: number
  max_amount: number
  platform: string
}

export interface TradesResponse {
  trades: Trade[]
  total: number
}

export interface Trade {
  // P2P trade fields (synced from Noones)
  id: number
  trade_hash: string
  status: string
  trade_type: string
  asset: string
  fiat_amount: number
  fiat_currency: string
  crypto_amount: number
  fiat_rate: number
  counterparty: string
  payment_method: string
  opened_at: number
  paid_at: number | null
  released_at: number | null
  completed_at: number | null
  confirmation_lag_sec: number | null
  profit_usd: number
  fee_usd: number
  offer_hash: string
  synced_at: number
}

export interface CounterpartySummary {
  name: string
  trades: number
  volume: number
  avg_lag_sec: number
}

export interface PnLSummary {
  period_days: number
  total_trades: number
  total_volume_fiat: number
  total_crypto_sold: number
  total_profit_usd: number
  total_fees: number
  net_profit_usd: number
  avg_confirmation_lag_sec: number
  trades_per_day: number
  avg_profit_per_trade: number
  daily_pnl: DailyPnL[]
  counterparties: CounterpartySummary[]
  payment_methods: Record<string, { count: number; volume: number; profit: number; fees: number }>
}

export interface DailyPnL {
  date: string
  cycles: number
  profit: number
  volume: number
}

export const syncTrades = () =>
  fetchJSON<{ synced_at: number; fetched: number; new: number; updated: number; errors: number }>(
    '/api/trades/sync', { method: 'POST' }
  )

export interface Cycle {
  id: string
  started_at: number
  status: string
  buy_platform: string
  sell_platform: string
  asset: string
}

export interface SimRequest {
  scenario?: string
  spread_pct?: number
  fiat_minutes?: number
  active_hours?: number
  days?: number
  runs?: number
}

export interface SimResult {
  capital: number[]
  profit: number[]
  volume: number[]
  p10: number[]
  p90: number[]
  smoothed_capital: number[]
}

export interface MilestonePoint {
  day: number
  capital: number
  profit: number
  volume_day: number
  capital_pct_change: number
}

export interface SimStats {
  cycles_per_day_ln: number
  cycles_per_day_oc: number
  velocity_multiplier: number
  profit_per_cycle: number
  monthly_volume_ln: number
  monthly_volume_oc: number
  monthly_net_profit_mean: number
  monthly_net_profit_p10: number
  monthly_net_profit_p90: number
}

export interface SimParams {
  scenario: string
  spread_pct: number
  fiat_minutes: number
  active_hours: number
  days: number
  runs: number
  market?: string
}

export interface SimulationResult {
  params: SimParams
  lightning: SimResult
  onchain: SimResult
  milestones: Record<string, MilestonePoint>
  stats: SimStats
  computed_at: number
}

export interface RefillMethod {
  name: string
  currency: string
  buy_service: string
  lightning_wallet: string
  pipeline: string[]
  total_time: string
  fees: string
  kyc: string
  risk: string
  status: 'verified' | 'unconfirmed' | 'no_route'
  evidence_url?: string
  notes?: string
}

export interface RefillMarket {
  name: string
  flag: string
  currency: string
  methods: RefillMethod[]
}

export interface RefillPipeline {
  markets: RefillMarket[]
  last_updated: string
}
