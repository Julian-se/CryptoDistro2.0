# Visual Redesign Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the top-navbar layout and neon terminal aesthetic with a Supabase × xAI sidebar layout using `#3ECF8E` green, near-black backgrounds, and data-forward tables/charts.

**Architecture:** Five independent chunks: (1) design tokens, (2) layout shell, (3) dashboard page, (4) analytics page, (5) remaining reskins. Each chunk is independently shippable with a TypeScript check pass as the verification gate.

**Tech Stack:** Next.js 14 App Router, Tailwind CSS, Recharts, lucide-react (already installed), `usePathname` + `useWebSocket` from existing hooks.

**Spec:** `docs/superpowers/specs/2026-03-16-visual-redesign-design.md`

---

## Chunk 1: Design Tokens

Files touched: `frontend/tailwind.config.js`, `frontend/app/globals.css`

No runtime logic — pure token replacement. Verification: `npx tsc --noEmit` passes, `npm run dev` renders without crashes.

### Task 1: Update Tailwind color tokens

**Files:**
- Modify: `frontend/tailwind.config.js`

- [ ] **Step 1: Replace the `colors` block**

Open `frontend/tailwind.config.js` and replace the entire `colors` block inside `theme.extend` with:

```js
colors: {
  bg: {
    base:    '#0a0a0a',
    surface: '#0d0d0d',
    card:    '#141414',
    border:  '#242424',
    sub:     '#1a1a1a',
    hover:   '#1c1c1c',
  },
  accent: {
    green:          '#3ECF8E',
    'green-dim':    'rgba(62,207,142,0.08)',
    'green-border': 'rgba(62,207,142,0.20)',
    'green-glow':   'rgba(62,207,142,0.25)',
    orange:         '#F5A623',
    red:            '#FF4757',
    blue:           '#3B82F6',
    purple:         '#8844ff',
  },
  text: {
    primary:   '#f0f0f0',
    secondary: '#8888aa',
    muted:     '#505050',
    dim:       '#333333',
  },
},
```

Also:
- Remove the `backgroundImage` and `backgroundSize` entries for `grid-pattern` and `grid` (the grid background is being removed)
- Remove `animation.glow` entry AND the matching `keyframes.glow` block (both must go — neither is referenced after the redesign)
- Remove `accent.yellow: '#ffcc00'` — verified unused: no component references `text-accent-yellow` or `bg-accent-yellow`
- Keep `animation.pulse-slow`, `animation.scan`, `keyframes.scan`, and `fontFamily` blocks unchanged

- [ ] **Step 2: Run TypeScript check**

```bash
cd /home/ironman/CryptoDistro2.0/frontend && npx tsc --noEmit
```

Expected: 0 errors (color token changes are CSS utility names — existing code uses the same token keys, so no TS errors).

- [ ] **Step 3: Commit**

```bash
cd /home/ironman/CryptoDistro2.0/frontend
git add tailwind.config.js
git commit -m "design: update Tailwind color tokens to Supabase×xAI palette"
```

---

### Task 2: Update globals.css

**Files:**
- Modify: `frontend/app/globals.css`

- [ ] **Step 1: Replace the full file**

Replace `frontend/app/globals.css` with:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --bg-base:     #0a0a0a;
  --bg-surface:  #0d0d0d;
  --bg-card:     #141414;
  --bg-border:   #242424;
  --bg-sub:      #1a1a1a;
  --accent-green:        #3ECF8E;
  --accent-green-dim:    rgba(62, 207, 142, 0.08);
  --accent-green-border: rgba(62, 207, 142, 0.20);
  --accent-orange: #F5A623;
  --accent-red:    #FF4757;
  --accent-blue:   #3B82F6;
  --text-primary:  #f0f0f0;
  --text-muted:    #505050;
  --text-dim:      #333333;
}

* {
  box-sizing: border-box;
  padding: 0;
  margin: 0;
}

html,
body {
  max-width: 100vw;
  overflow-x: hidden;
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: 'Inter', system-ui, sans-serif;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: var(--bg-surface);
}
::-webkit-scrollbar-thumb {
  background: var(--bg-border);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: #2e2e2e;
}

/* Card */
.card {
  background: var(--bg-card);
  border: 1px solid var(--bg-border);
  border-radius: 6px;
}

/* Signal badges — use CSS vars so palette changes propagate */
.badge-act-now {
  background: rgba(62, 207, 142, 0.10);
  color: #3ECF8E;
  border: 1px solid rgba(62, 207, 142, 0.25);
}
.badge-watch {
  background: rgba(245, 166, 35, 0.10);
  color: #F5A623;
  border: 1px solid rgba(245, 166, 35, 0.25);
}
.badge-avoid {
  background: rgba(255, 71, 87, 0.10);
  color: #FF4757;
  border: 1px solid rgba(255, 71, 87, 0.25);
}
.badge-data-issue {
  background: rgba(136, 68, 255, 0.10);
  color: #8844ff;
  border: 1px solid rgba(136, 68, 255, 0.25);
}

/* Live status dot — only element that keeps glow */
.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-green);
  box-shadow: 0 0 5px rgba(62, 207, 142, 0.5);
  animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
```

Key changes from old file:
- CSS vars updated to new palette
- `.bg-grid` class removed (grid background gone)
- `.glow-green`, `.glow-orange`, `.glow-red`, `.text-glow-green` removed (no neon glows)
- `.card` border-radius `8px` → `6px`
- Badge classes rewritten to use new hex values (not raw `#00ff88`, `#ff8c00`, `#ff3366`)
- `pulse-dot` updated to new green, smaller (6px), only keeps `box-shadow` (not full glow)

- [ ] **Step 2: Run TypeScript check**

```bash
cd /home/ironman/CryptoDistro2.0/frontend && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
cd /home/ironman/CryptoDistro2.0/frontend
git add app/globals.css
git commit -m "design: update globals.css — new palette, remove neon glows and grid bg"
```

---

## Chunk 2: Layout Shell

Files touched: `frontend/components/layout/Sidebar.tsx` (new), `frontend/app/layout.tsx`

The sidebar replaces the top navbar. `Navbar.tsx` is kept as dead code for now (safe to delete after this chunk ships).

### Task 3: Create Sidebar.tsx

**Files:**
- Create: `frontend/components/layout/Sidebar.tsx`

- [ ] **Step 1: Create the file**

Create `frontend/components/layout/Sidebar.tsx` with the following content:

```tsx
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  TrendingUp,
  Zap,
  FlaskConical,
  Activity,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useWSEvent } from '@/hooks/useWebSocket'
import { DashboardSnapshot } from '@/lib/api'

const NAV_ITEMS = [
  { href: '/',              label: 'Overview',    icon: LayoutDashboard },
  { href: '/analytics',    label: 'Analytics',   icon: TrendingUp       },
  { href: '/refill',       label: 'Refill',      icon: Zap              },
  { href: '/simulation',   label: 'Simulation',  icon: FlaskConical     },
  { href: '/observability',label: 'System',      icon: Activity         },
]

// Page label for breadcrumb
const PAGE_LABELS: Record<string, string> = {
  '/':              'Overview',
  '/analytics':     'Analytics',
  '/refill':        'Refill',
  '/simulation':    'Simulation',
  '/observability': 'System',
}

export function Topbar() {
  const pathname = usePathname()
  const { connected } = useWebSocket()
  const pageLabel = PAGE_LABELS[pathname] ?? 'Dashboard'

  return (
    <header
      className="h-11 flex items-center shrink-0 border-b border-bg-border bg-bg-surface"
      style={{ zIndex: 10 }}
    >
      {/* Logo zone — matches sidebar width */}
      <div
        className="flex items-center gap-2 px-4 border-r border-bg-border h-full shrink-0"
        style={{ width: 220 }}
      >
        <div className="w-5 h-5 rounded bg-accent-green flex items-center justify-center shrink-0">
          <span className="text-[9px] font-black text-black">₿</span>
        </div>
        <span className="text-[11px] font-bold text-text-primary tracking-tight">
          CryptoDistro
        </span>
      </div>

      {/* Breadcrumb */}
      <div className="flex-1 flex items-center gap-1.5 px-4">
        <span className="text-[8px] text-text-muted">Dashboard</span>
        <span className="text-[8px] text-text-dim">/</span>
        <span className="text-[8px] font-medium text-text-primary">{pageLabel}</span>
      </div>

      {/* Live status */}
      <div className="flex items-center gap-1.5 px-4">
        <div className={cn('pulse-dot', !connected && 'bg-accent-red shadow-none')} />
        <span className="text-[8px] font-mono text-text-muted">
          {connected ? 'LIVE' : 'OFFLINE'}
        </span>
      </div>
    </header>
  )
}

export function Sidebar() {
  const pathname = usePathname()
  const snapshot = useWSEvent<DashboardSnapshot | null>('snapshot', null)

  const actNowCount = snapshot?.markets?.filter(m => m.action === 'ACT_NOW').length ?? 0
  const noonesBalance = snapshot?.balances?.noones
  const capitalUsd = noonesBalance?.total_usd ?? 0
  const capitalBtc = noonesBalance?.btc ?? 0
  // Progress: fraction of start capital (capped at 100%)
  const INITIAL_CAPITAL_USD = 500
  const progressPct = Math.min(100, (capitalUsd / INITIAL_CAPITAL_USD) * 100)

  return (
    <aside
      className="flex flex-col shrink-0 border-r border-bg-border bg-bg-surface overflow-y-auto"
      style={{ width: 220 }}
    >
      <div className="px-2.5 pt-3 pb-2">
        {/* Section label */}
        <p
          className="text-text-dim uppercase tracking-widest px-2 mb-1.5"
          style={{ fontSize: 7, letterSpacing: '0.1em' }}
        >
          Operator
        </p>

        {/* Nav items */}
        <nav className="space-y-px">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  'flex items-center gap-2 px-2 py-1.5 rounded-[5px] transition-colors',
                  active
                    ? 'bg-accent-green-dim border border-accent-green-border'
                    : 'hover:bg-bg-hover border border-transparent',
                )}
              >
                <Icon
                  size={14}
                  className={active ? 'text-accent-green' : 'text-text-muted'}
                  strokeWidth={1.5}
                />
                <span
                  className={cn(
                    'text-[9px] font-medium',
                    active ? 'text-accent-green' : 'text-text-muted',
                  )}
                >
                  {label}
                </span>
                {href === '/' && actNowCount > 0 && (
                  <span
                    className="ml-auto font-mono font-bold text-accent-green rounded-sm px-1"
                    style={{
                      fontSize: 7,
                      background: 'rgba(62,207,142,0.15)',
                    }}
                  >
                    {actNowCount}
                  </span>
                )}
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Divider */}
      <div className="mx-3 my-2 border-t border-bg-border" />

      {/* Capital block */}
      <div className="px-4 pb-4">
        <p
          className="text-text-dim uppercase tracking-widest mb-1"
          style={{ fontSize: 7, letterSpacing: '0.1em' }}
        >
          Noones Capital
        </p>
        <p
          className="font-mono font-extrabold text-accent-green leading-none"
          style={{ fontSize: 19 }}
        >
          ${capitalUsd.toFixed(0)}
        </p>
        <p className="font-mono text-text-muted mt-0.5" style={{ fontSize: 7 }}>
          {capitalBtc.toFixed(5)} BTC · noones
        </p>
        {/* Progress bar */}
        <div
          className="mt-2 rounded-sm overflow-hidden"
          style={{ height: 2, background: 'var(--bg-border)' }}
        >
          <div
            className="h-full rounded-sm"
            style={{
              width: `${progressPct}%`,
              background: 'var(--accent-green)',
            }}
          />
        </div>
      </div>
    </aside>
  )
}
```

- [ ] **Step 2: Run TypeScript check**

```bash
cd /home/ironman/CryptoDistro2.0/frontend && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
cd /home/ironman/CryptoDistro2.0/frontend
git add components/layout/Sidebar.tsx
git commit -m "feat: add Sidebar.tsx with Topbar and Sidebar named exports"
```

---

### Task 4: Update layout.tsx

**Files:**
- Modify: `frontend/app/layout.tsx`

- [ ] **Step 1: Replace layout.tsx**

Replace `frontend/app/layout.tsx` with:

```tsx
import type { Metadata } from 'next'
import './globals.css'
import { Topbar } from '@/components/layout/Sidebar'
import { Sidebar } from '@/components/layout/Sidebar'

export const metadata: Metadata = {
  title: 'CryptoDistro 2.0',
  description: 'P2P Bitcoin on/off-ramp operator dashboard',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-bg-base text-text-primary h-screen flex flex-col overflow-hidden">
        <Topbar />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-y-auto p-5">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
```

- [ ] **Step 2: Run TypeScript check**

```bash
cd /home/ironman/CryptoDistro2.0/frontend && npx tsc --noEmit
```

Expected: 0 errors. Note: `Navbar` import is now gone from layout. `Navbar.tsx` still exists but is no longer imported anywhere.

- [ ] **Step 3: Smoke test in browser**

Start dev server (`npm run dev`) and verify:
- Topbar renders at 44px height with logo, breadcrumb, live dot
- Sidebar renders at 220px width with 5 nav items and capital block
- Main content scrolls independently
- Active nav item highlights in green

- [ ] **Step 4: Commit**

```bash
cd /home/ironman/CryptoDistro2.0/frontend
git add app/layout.tsx
git commit -m "feat: replace top-navbar layout with sidebar shell"
```

---

## Chunk 3: Dashboard Page

Files touched: `frontend/components/dashboard/MarketTable.tsx` (new), `frontend/app/page.tsx`

Remove the FlowViz 3D component and market cards. Add the `MarketTable` data table. Keep `ControllerPanel` and `IntelligenceChat` in place (they reskin via token rename — no code changes needed yet).

### Task 5: Create MarketTable.tsx

**Files:**
- Create: `frontend/components/dashboard/MarketTable.tsx`

- [ ] **Step 1: Create the file**

Create `frontend/components/dashboard/MarketTable.tsx`:

```tsx
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
  ACT_NOW:    'ACT',
  WATCH:      'WATCH',
  AVOID:      'AVOID',
  DATA_ISSUE: 'DATA',
}

export function MarketTable({ markets }: Props) {
  const actNowCount = markets.filter(m => m.action === 'ACT_NOW').length

  return (
    <div className="bg-bg-card border border-bg-border rounded-[6px] overflow-hidden">
      {/* Table header row */}
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-bg-border">
        <span className="text-[8px] uppercase tracking-wider text-text-muted font-medium">
          Market Signals
        </span>
        {actNowCount > 0 && (
          <span className="text-[7px] font-mono font-bold text-accent-green">
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
                className="text-left px-3 py-2 text-[7px] uppercase tracking-wider text-text-muted font-medium"
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
              className="border-b border-bg-sub last:border-0 hover:bg-white/[0.015] transition-colors"
            >
              {/* Market */}
              <td className="px-3 py-2.5">
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px]">{m.flag}</span>
                  <span className="text-[9px] font-medium text-text-primary">
                    {m.currency}
                  </span>
                </div>
              </td>

              {/* Premium */}
              <td className="px-3 py-2.5">
                <span
                  className={cn(
                    'font-mono font-bold text-[9px]',
                    m.premium_pct >= 6 ? 'text-accent-green' : 'text-text-muted',
                  )}
                >
                  {m.premium_pct >= 0 ? '+' : ''}{formatPct(m.premium_pct)}
                </span>
              </td>

              {/* Margin */}
              <td className="px-3 py-2.5">
                <span className="font-mono text-[9px] text-text-primary">
                  {formatPct(m.suggested_margin)}
                </span>
              </td>

              {/* FX Rate */}
              <td className="px-3 py-2.5">
                <span className="font-mono text-[9px] text-text-muted">
                  {m.fx_rate > 0 ? m.fx_rate.toLocaleString(undefined, { maximumFractionDigits: 0 }) : '—'}
                </span>
              </td>

              {/* Payment methods */}
              <td className="px-3 py-2.5">
                <div className="flex flex-wrap gap-1">
                  {(m.payment_methods ?? []).slice(0, 3).map(pm => (
                    <span
                      key={pm.slug}
                      className="text-[6px] px-1.5 py-0.5 rounded-sm font-medium text-accent-green border border-accent-green-border"
                      style={{ background: 'rgba(62,207,142,0.07)' }}
                    >
                      {pm.label}
                    </span>
                  ))}
                  {(m.payment_methods ?? []).length > 3 && (
                    <span className="text-[6px] text-text-dim">
                      +{m.payment_methods.length - 3}
                    </span>
                  )}
                </div>
              </td>

              {/* Signal */}
              <td className="px-3 py-2.5">
                <span
                  className={cn(
                    'text-[7px] font-bold px-2 py-0.5 rounded-sm',
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
              <td colSpan={6} className="px-3 py-6 text-center text-[9px] text-text-muted">
                No market data
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 2: Run TypeScript check**

```bash
cd /home/ironman/CryptoDistro2.0/frontend && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
cd /home/ironman/CryptoDistro2.0/frontend
git add components/dashboard/MarketTable.tsx
git commit -m "feat: add MarketTable component (table-based market signal display)"
```

---

### Task 6: Update Dashboard page.tsx

**Files:**
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: Update page.tsx**

Replace `frontend/app/page.tsx` with:

```tsx
'use client'

import { useEffect, useState } from 'react'
import { getDashboardSnapshot, DashboardSnapshot } from '@/lib/api'
import { useWSEvent } from '@/hooks/useWebSocket'
import { ControllerPanel } from '@/components/dashboard/ControllerPanel'
import { IntelligenceChat } from '@/components/dashboard/IntelligenceChat'
import { MarketTable } from '@/components/dashboard/MarketTable'
import { MetricCard } from '@/components/shared/Card'
import { Spinner } from '@/components/shared/Spinner'
import { formatUSD, formatPct, timeAgo } from '@/lib/utils'

export default function DashboardPage() {
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboardSnapshot()
      .then(s => { setSnapshot(s); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

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
        <div className="border border-accent-orange/30 bg-accent-orange/5 rounded px-3 py-2 text-[10px] font-mono text-accent-orange">
          DEMO MODE — Add BINANCE_API_KEY and NOONES_API_KEY to .env for live data
        </div>
      )}

      {/* Page title + meta */}
      <div>
        <h1 className="text-lg font-bold text-text-primary">Overview</h1>
        <p className="text-[9px] text-text-muted mt-0.5">
          Last scan {timeAgo(snapshot.scanned_at)} · {snapshot.markets.length} markets tracked
        </p>
      </div>

      {/* Metric tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          label="BTC Spot"
          value={formatUSD(snapshot.btc_spot_usd, 0)}
          color="text-accent-green"
        />
        <MetricCard
          label="Active Markets"
          value={`${actNowCount} / ${snapshot.markets.length}`}
          color={actNowCount > 0 ? 'text-accent-green' : 'text-text-primary'}
          sub="ACT_NOW signals"
        />
        <MetricCard
          label="Avg Premium"
          value={formatPct(avgPremium)}
          color="text-accent-green"
          sub="30-day average"
        />
        <MetricCard
          label="Open Cycles"
          value={snapshot.open_cycles}
          color={snapshot.open_cycles > 0 ? 'text-accent-blue' : 'text-text-primary'}
        />
      </div>

      {/* Main grid: market table + right panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Market table — spans 2 cols */}
        <div className="lg:col-span-2 space-y-4">
          <MarketTable markets={snapshot.markets} />
          <IntelligenceChat />
        </div>

        {/* Controller panel */}
        <div>
          <ControllerPanel signals={snapshot.controller_signals} />
        </div>
      </div>
    </div>
  )
}
```

Key changes:
- Removed `FlowViz` dynamic import and render
- Removed `BalancePanel` import (capital now lives in sidebar)
- Removed `MarketCard` import (replaced by `MarketTable`)
- Added `MarketTable` + `formatPct` import
- Added `avgPremium` metric tile
- Added page title + meta line

- [ ] **Step 2: Run TypeScript check**

```bash
cd /home/ironman/CryptoDistro2.0/frontend && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
cd /home/ironman/CryptoDistro2.0/frontend
git add app/page.tsx
git commit -m "feat: replace dashboard cards+FlowViz with MarketTable, remove BalancePanel"
```

---

## Chunk 4: Analytics Page

Files touched: `frontend/app/analytics/page.tsx`

Restructure to the 2×2 area chart grid with period tabs. Keep all data logic intact — only the JSX layout changes.

### Task 7: Update Analytics page

**Files:**
- Modify: `frontend/app/analytics/page.tsx`

The analytics page is large. The changes are:
1. Replace heading style: `font-mono` → Inter, keep `text-xl font-bold`
2. Period tabs: keep `7d`, remove `14d` (spec shows 7d / 30d / 90d only); `30` default state is unchanged
3. Replace the `grid-cols-1 lg:grid-cols-3` chart section (Daily PnL bar + Market Breakdown pie + Capital Forecast area) with a 2×2 `grid-cols-2` grid of four chart cards
4. The "Premium by Market" h-bar chart must use **`snapshot.markets` data** (live `premium_pct` per market), not `pieData` (trade profit history). Add `snapshot` to the existing `useApi` calls if not already available (it is — `getSnapshot` is already imported and used for `currentCapital`)
5. Update all hardcoded chart hex colors — full list: `'#00ff88'` → `'#3ECF8E'`, `'#ff8c00'` → `'#F5A623'`, `'#ff3366'` → `'#FF4757'`, `'#0088ff'` → `'#3B82F6'`, `'#16161f'` → `'#141414'` (tooltip bg), `'#1e1e2e'` → `'#242424'` (grid lines), `'#8888aa'` → `'#505050'` (axis tick fill), `'#555577'` → `'#333333'` (dim axis fill)
6. Remove `font-mono` from heading text (labels stay uppercase but in Inter — simply omit `font-mono` class)
7. Keep Insights card, Tradeable Assets (CMC) card, and Recent Trades table — they are outside the replaced chart section and update automatically via token rename
8. The replaced section is only: the `grid grid-cols-1 lg:grid-cols-3 gap-6` div AND the separate Capital Forecast card that follows it

- [ ] **Step 1: Update chart color constants and period tabs**

In `frontend/app/analytics/page.tsx`, make these targeted edits:

**A. Replace the `COLORS` constant** (line 14):
```tsx
// Old:
const COLORS = ['#00ff88', '#0088ff', '#ff8c00', '#8844ff', '#ff3366']

// New:
const COLORS = ['#3ECF8E', '#3B82F6', '#F5A623', '#8844ff', '#FF4757']
```

**B. Replace the heading block** (around line 146–165 in the return):
```tsx
// Old:
<h1 className="text-xl font-bold font-mono text-text-primary">Analytics</h1>
<p className="text-sm text-text-secondary mt-1">PnL, performance insights, capital forecast</p>
...
{[7, 14, 30, 90].map(d => (

// New:
<h1 className="text-xl font-bold text-text-primary">Analytics</h1>
<p className="text-[9px] text-text-muted mt-0.5">PnL, performance insights, capital forecast</p>
...
{[7, 30, 90].map(d => (
```

(Remove 14d option — spec shows 7d / 30d / 90d only)

**C. Update all hardcoded chart colors in JSX** — in BarChart, AreaChart, Tooltip styles, CartesianGrid:

Replace every occurrence of:
- `'#00ff88'` → `'#3ECF8E'`
- `'#ff8c00'` → `'#F5A623'`
- `'#16161f'` → `'#141414'` (tooltip bg)
- `'#1e1e2e'` → `'#242424'` (grid lines, borders)
- `'#8888aa'` → `'#505050'` (axis tick text)
- `'#555577'` → `'#333333'` (dim axis text)

**D. Replace the chart layout** — replace the existing `grid grid-cols-1 lg:grid-cols-3 gap-6` div (containing Daily PnL bar chart + Market Breakdown pie chart) AND the Capital Forecast card below it with this 2×2 grid:

```tsx
{/* 2×2 chart grid */}
<div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
  {/* Capital Growth area chart */}
  <div className="bg-bg-card border border-bg-border rounded-[6px] p-3">
    <div className="flex items-center justify-between mb-3">
      <p className="text-[8px] uppercase tracking-wider text-text-muted">Capital Growth</p>
      <p className="text-[11px] font-mono font-bold text-accent-green">
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
        <XAxis dataKey="day" tick={{ fill: '#333333', fontSize: 9 }} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={v => `$${v}`} tick={{ fill: '#333333', fontSize: 9 }} tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 10 }}
          formatter={(v: number) => [formatUSD(v), 'Capital']}
        />
        <Area type="monotone" dataKey="capital" stroke="#3ECF8E" strokeWidth={1.5} fill="url(#capGrad)" />
      </AreaChart>
    </ResponsiveContainer>
  </div>

  {/* Daily P&L bar chart */}
  <div className="bg-bg-card border border-bg-border rounded-[6px] p-3">
    <div className="flex items-center justify-between mb-3">
      <p className="text-[8px] uppercase tracking-wider text-text-muted">Daily P&L</p>
      <p className={`text-[11px] font-mono font-bold ${totalNetProfit >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
        {formatUSD(totalNetProfit)}
      </p>
    </div>
    {dailyData.length > 0 ? (
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={dailyData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#242424" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#333333', fontSize: 9 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: string) => v.slice(5)}
          />
          <YAxis
            tickFormatter={(v: number) => `$${v}`}
            tick={{ fill: '#333333', fontSize: 9 }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 10 }}
            formatter={(v: number) => [formatUSD(v), 'Profit']}
          />
          <ReferenceLine y={0} stroke="#505050" strokeDasharray="3 3" />
          <Bar dataKey="profit" fill="#3ECF8E" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    ) : (
      <div className="h-40 flex items-center justify-center text-[9px] text-text-muted">
        No data yet
      </div>
    )}
  </div>

  {/* Premium by Market horizontal bars — uses live snapshot.markets, not trade history */}
  <div className="bg-bg-card border border-bg-border rounded-[6px] p-3">
    <div className="flex items-center justify-between mb-3">
      <p className="text-[8px] uppercase tracking-wider text-text-muted">Premium by Market</p>
      <p className="text-[11px] font-mono font-bold text-text-primary">
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
              <span className="text-[9px] text-text-primary font-medium">
                {m.flag} {m.currency}
              </span>
              <span className="text-[9px] font-mono text-accent-green">
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
        <div className="h-32 flex items-center justify-center text-[9px] text-text-muted">
          No market data
        </div>
      )}
    </div>
  </div>

  {/* 90-Day Forecast */}
  <div className="bg-bg-card border border-bg-border rounded-[6px] p-3">
    <div className="flex items-center justify-between mb-3">
      <p className="text-[8px] uppercase tracking-wider text-text-muted">90-Day Forecast</p>
      <p className={`text-[11px] font-mono font-bold ${projected90 >= currentCapital ? 'text-accent-green' : 'text-accent-red'}`}>
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
        <XAxis dataKey="day" tick={{ fill: '#333333', fontSize: 9 }} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={v => `$${v}`} tick={{ fill: '#333333', fontSize: 9 }} tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={{ background: '#141414', border: '1px solid #242424', borderRadius: 6, fontSize: 10 }}
          formatter={(v: number) => [formatUSD(v), 'Projected']}
        />
        <ReferenceLine x={30} stroke="#F5A623" strokeDasharray="3 3" label={{ value: '30d', fill: '#F5A623', fontSize: 9 }} />
        <Area type="monotone" dataKey="capital" stroke="#3ECF8E" strokeWidth={1.5} fill="url(#projGrad)" />
      </AreaChart>
    </ResponsiveContainer>
  </div>
</div>
```

Keep all sections above (metric tiles, no-data banner, insights) and below (CMC section, Recent Trades table) unchanged — they update automatically via token rename.

- [ ] **Step 2: Run TypeScript check**

```bash
cd /home/ironman/CryptoDistro2.0/frontend && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
cd /home/ironman/CryptoDistro2.0/frontend
git add app/analytics/page.tsx
git commit -m "feat: analytics 2x2 chart grid with new palette — area, bar, h-bar, forecast"
```

---

## Chunk 5: Reskin Remaining Files

Files touched: `frontend/components/shared/Card.tsx`, `frontend/app/refill/page.tsx` (minor), `frontend/app/simulation/page.tsx` (minor), `frontend/app/observability/page.tsx` (minor), `frontend/components/dashboard/ControllerPanel.tsx` (no change needed), `frontend/components/dashboard/IntelligenceChat.tsx` (no change needed)

Most of these pages update automatically when the Tailwind tokens in Chunk 1 are applied. This chunk handles the remaining items: `Card.tsx` typography tweak, and verifying the reskin pages render correctly.

### Task 8: Update MetricCard typography in Card.tsx

**Files:**
- Modify: `frontend/components/shared/Card.tsx`

The spec says MetricCard values should use 14px JetBrains Mono bold (not 2xl). Labels: 7px **Inter** uppercase muted — the `font-mono` class must be **removed** from the label (the spec explicitly removes the all-monospace label pattern; uppercase tracking stays, but the font reverts to Inter, which is the default body font).

- [ ] **Step 1: Update MetricCard**

In `frontend/components/shared/Card.tsx`, replace the `MetricCard` function:

```tsx
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
    <div className={cn('card p-2.5', className)}>
      <p className="uppercase tracking-wider text-text-muted mb-1" style={{ fontSize: 7 }}>{label}</p>
      <p className={cn('font-mono font-bold', color)} style={{ fontSize: 14 }}>{value}</p>
      {sub && <p className="text-text-muted mt-0.5" style={{ fontSize: 7 }}>{sub}</p>}
    </div>
  )
}
```

Also update the `Card` component title style to remove `font-mono` (use Inter by default):

```tsx
// Old:
<h3 className="text-xs font-mono text-text-secondary uppercase tracking-widest">

// New:
<h3 className="text-[8px] uppercase tracking-wider text-text-muted">
```

And remove the `glow` prop usage (no more `.glow-green` class):

```tsx
// Old:
<div className={cn(
  'card p-4',
  glow && 'glow-green',
  className
)}>

// New:
<div className={cn('card p-4', className)}>
```

Remove `glow?: boolean` from the `CardProps` interface too.

- [ ] **Step 2: Run TypeScript check**

```bash
cd /home/ironman/CryptoDistro2.0/frontend && npx tsc --noEmit
```

Expected: 0 errors. If `glow` prop is passed anywhere, TS will flag it — fix by removing those props at the call sites.

- [ ] **Step 3: Check glow prop usage**

```bash
cd /home/ironman/CryptoDistro2.0/frontend && grep -r "glow=" components/ app/
```

Remove any `glow={true}` or `glow` props from Card call sites found.

- [ ] **Step 4: Commit**

```bash
cd /home/ironman/CryptoDistro2.0/frontend
git add components/shared/Card.tsx
git commit -m "design: update Card/MetricCard typography and remove glow prop"
```

---

### Task 9: Verify reskin pages render correctly

The following pages use only Tailwind color utilities that update automatically via token rename in Chunk 1:
- `app/refill/page.tsx`
- `app/simulation/page.tsx`
- `app/observability/page.tsx`
- `components/dashboard/ControllerPanel.tsx`
- `components/dashboard/IntelligenceChat.tsx`

No code changes required. This task is a visual smoke-test.

- [ ] **Step 1: Remove `animate-pulse-slow` from decorative elements**

The spec says: "Keep `animate-pulse-slow` only on the live status dot." Find all usages:

```bash
cd /home/ironman/CryptoDistro2.0/frontend && grep -rn "animate-pulse-slow" app/ components/
```

For any match NOT in `Sidebar.tsx` (the live status dot), remove the `animate-pulse-slow` class from that element.

- [ ] **Step 2: Start dev server and visit each page**

```bash
cd /home/ironman/CryptoDistro2.0/frontend && npm run dev
```

Visit in browser:
- `/refill` — verify cards use `bg-bg-card`, method pills in `accent-green-dim`
- `/simulation` — verify chart lines are `#3ECF8E`, scenario cards have `bg-bg-card` borders
- `/observability` (System) — verify health status uses `accent-green`/`accent-red`/`accent-orange`

For each page, confirm:
- No neon `#00ff88` green visible (replaced by `#3ECF8E` — slightly less electric)
- No grid background pattern
- Borders are `#242424` (darker, tighter than old `#1e1e2e`)

- [ ] **Step 3: Final TypeScript check**

```bash
cd /home/ironman/CryptoDistro2.0/frontend && npx tsc --noEmit
```

Expected: 0 errors across the whole project.

- [ ] **Step 4: Delete dead files**

These components are no longer imported anywhere:
- `frontend/components/layout/Navbar.tsx` — replaced by `Sidebar.tsx`
- `frontend/components/dashboard/MarketCard.tsx` — replaced by `MarketTable.tsx`
- `frontend/components/dashboard/BalancePanel.tsx` — capital moved to sidebar

First verify they're unreferenced:

```bash
cd /home/ironman/CryptoDistro2.0/frontend
grep -r "Navbar" app/ components/ --include="*.tsx" | grep -v "Navbar.tsx"
grep -r "MarketCard" app/ components/ --include="*.tsx" | grep -v "MarketCard.tsx"
grep -r "BalancePanel" app/ components/ --include="*.tsx" | grep -v "BalancePanel.tsx"
```

Each grep should return no results. Then delete:

```bash
rm frontend/components/layout/Navbar.tsx
rm frontend/components/dashboard/MarketCard.tsx
rm frontend/components/dashboard/BalancePanel.tsx
```

- [ ] **Step 5: Final TypeScript check after deletions**

```bash
cd /home/ironman/CryptoDistro2.0/frontend && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 6: Commit**

```bash
cd /home/ironman/CryptoDistro2.0/frontend
git add -A
git commit -m "chore: delete Navbar.tsx, MarketCard.tsx, BalancePanel.tsx (replaced)"
```

---

## Optional: Remove Three.js dependencies

The `FlowViz` component used `@react-three/fiber`, `@react-three/drei`, and `three`. Now that `FlowViz` is removed from `page.tsx`, check if `FlowViz.tsx` still exists and delete it, then remove the packages.

- [ ] **Check if FlowViz.tsx still exists:**

```bash
ls frontend/components/dashboard/FlowViz.tsx 2>/dev/null && echo "exists"
```

- [ ] **If it exists, delete it and remove packages:**

```bash
rm frontend/components/dashboard/FlowViz.tsx
cd frontend && npm uninstall @react-three/fiber @react-three/drei three @types/three
```

- [ ] **Run TypeScript check:**

```bash
cd /home/ironman/CryptoDistro2.0/frontend && npx tsc --noEmit
```

- [ ] **Commit:**

```bash
cd /home/ironman/CryptoDistro2.0/frontend
git add -A
git commit -m "chore: remove FlowViz component and @react-three/* packages (~500KB bundle)"
```

---

## Summary

| Chunk | Tasks | Files | Verification |
|-------|-------|-------|-------------|
| 1 — Tokens | 1–2 | tailwind.config.js, globals.css | `tsc --noEmit` |
| 2 — Layout | 3–4 | Sidebar.tsx (new), layout.tsx | visual + `tsc` |
| 3 — Dashboard | 5–6 | MarketTable.tsx (new), page.tsx | visual + `tsc` |
| 4 — Analytics | 7 | analytics/page.tsx | visual + `tsc` |
| 5 — Reskin | 8–9 | Card.tsx, delete 3 dead files | visual + `tsc` |
