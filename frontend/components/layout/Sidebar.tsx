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
import { useWebSocket, useWSEvent } from '@/hooks/useWebSocket'
import { DashboardSnapshot } from '@/lib/api'

const NAV_ITEMS = [
  { href: '/',               label: 'Overview',    icon: LayoutDashboard },
  { href: '/analytics',     label: 'Analytics',   icon: TrendingUp       },
  { href: '/refill',        label: 'Refill',      icon: Zap              },
  { href: '/simulation',    label: 'Simulation',  icon: FlaskConical     },
  { href: '/observability', label: 'System',      icon: Activity         },
]

const PAGE_LABELS: Record<string, string> = {
  '/':               'Overview',
  '/analytics':      'Analytics',
  '/refill':         'Refill',
  '/simulation':     'Simulation',
  '/observability':  'System',
}

export function Topbar() {
  const pathname = usePathname()
  const { connected } = useWebSocket()
  const pageLabel = PAGE_LABELS[pathname] ?? 'Dashboard'

  return (
    <header
      className="h-12 flex items-center shrink-0 border-b border-bg-border bg-bg-surface"
      style={{ zIndex: 10 }}
    >
      {/* Logo zone — matches sidebar width */}
      <div
        className="flex items-center gap-2.5 px-4 border-r border-bg-border h-full shrink-0"
        style={{ width: 240 }}
      >
        <div className="w-6 h-6 rounded bg-accent-green flex items-center justify-center shrink-0">
          <span className="text-xs font-black text-black">₿</span>
        </div>
        <span className="text-sm font-bold text-text-primary tracking-tight">
          CryptoDistro
        </span>
      </div>

      {/* Breadcrumb */}
      <div className="flex-1 flex items-center gap-1.5 px-5">
        <span className="text-xs text-text-muted">Dashboard</span>
        <span className="text-xs text-text-dim">/</span>
        <span className="text-xs font-medium text-text-primary">{pageLabel}</span>
      </div>

      {/* Live status */}
      <div className="flex items-center gap-2 px-5">
        <div className={cn('pulse-dot', !connected && 'bg-accent-red shadow-none')} />
        <span className="text-xs font-mono text-text-muted">
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
  const INITIAL_CAPITAL_USD = 500
  const progressPct = Math.min(100, (capitalUsd / INITIAL_CAPITAL_USD) * 100)

  return (
    <aside
      className="flex flex-col shrink-0 border-r border-bg-border bg-bg-surface overflow-y-auto"
      style={{ width: 240 }}
    >
      <div className="px-3 pt-4 pb-2">
        {/* Section label */}
        <p className="text-[11px] font-medium text-text-dim uppercase tracking-widest px-2 mb-2">
          Operator
        </p>

        {/* Nav items */}
        <nav className="space-y-0.5">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  'flex items-center gap-2.5 px-2.5 py-2 rounded-[5px] transition-colors',
                  active
                    ? 'bg-accent-green-dim border border-accent-green-border'
                    : 'hover:bg-bg-hover border border-transparent',
                )}
              >
                <Icon
                  size={16}
                  className={active ? 'text-accent-green' : 'text-text-muted'}
                  strokeWidth={1.5}
                />
                <span
                  className={cn(
                    'text-sm font-medium',
                    active ? 'text-accent-green' : 'text-text-muted',
                  )}
                >
                  {label}
                </span>
                {href === '/' && actNowCount > 0 && (
                  <span
                    className="ml-auto text-[11px] font-mono font-bold text-accent-green rounded px-1.5 py-0.5"
                    style={{ background: 'rgba(62,207,142,0.15)' }}
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
      <div className="mx-3 my-3 border-t border-bg-border" />

      {/* Capital block */}
      <div className="px-4 pb-5">
        <p className="text-[11px] font-medium text-text-dim uppercase tracking-widest mb-2">
          Noones Capital
        </p>
        <p className="font-mono font-extrabold text-accent-green leading-none text-2xl">
          ${capitalUsd.toFixed(0)}
        </p>
        <p className="text-xs font-mono text-text-muted mt-1">
          {capitalBtc.toFixed(5)} BTC · noones
        </p>
        {/* Progress bar */}
        <div
          className="mt-3 rounded-sm overflow-hidden"
          style={{ height: 3, background: 'var(--bg-border)' }}
        >
          <div
            className="h-full rounded-sm"
            style={{ width: `${progressPct}%`, background: 'var(--accent-green)' }}
          />
        </div>
      </div>
    </aside>
  )
}
