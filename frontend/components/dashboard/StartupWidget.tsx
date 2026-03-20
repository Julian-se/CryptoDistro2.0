'use client'

import { useEffect, useState } from 'react'
import { getHealth, HealthResponse } from '@/lib/api'
import { useWSEvent } from '@/hooks/useWebSocket'
import { Spinner } from '@/components/shared/Spinner'

interface SystemCheck {
  label: string
  status: 'ok' | 'checking' | 'error'
  detail?: string
}

export function StartupWidget() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Listen for live WS connection
  const wsSnapshot = useWSEvent<unknown>('snapshot', null)
  const wsConnected = wsSnapshot !== null

  useEffect(() => {
    getHealth()
      .then(h => { setHealth(h); setLoading(false) })
      .catch(e => { setError(e instanceof Error ? e.message : 'Unknown error'); setLoading(false) })
  }, [])

  const checks: SystemCheck[] = []

  if (loading) {
    checks.push({ label: 'API Backend', status: 'checking' })
    checks.push({ label: 'WebSocket', status: 'checking' })
    checks.push({ label: 'Binance', status: 'checking' })
    checks.push({ label: 'Noones', status: 'checking' })
    checks.push({ label: 'Trade Tracker', status: 'checking' })
  } else if (error) {
    checks.push({ label: 'API Backend', status: 'error', detail: 'Not reachable' })
  } else if (health) {
    checks.push({
      label: 'API Backend',
      status: 'ok',
      detail: `${(health.uptime_sec / 60).toFixed(0)}m uptime`,
    })
    checks.push({
      label: 'WebSocket',
      status: wsConnected ? 'ok' : 'error',
      detail: wsConnected ? 'Connected' : 'Disconnected',
    })

    const comps = health.components ?? {}
    for (const [name, comp] of Object.entries(comps)) {
      checks.push({
        label: name.charAt(0).toUpperCase() + name.slice(1),
        status: comp.status === 'ok' ? 'ok' : 'error',
        detail: comp.status === 'ok'
          ? `${comp.latency_ms}ms`
          : comp.error ?? 'Error',
      })
    }

    // Scan info
    if (health.scan_metrics) {
      const sm = health.scan_metrics
      checks.push({
        label: 'Scanner',
        status: sm.scan_errors_last_hour > 0 ? 'error' : sm.scans_last_hour > 0 ? 'ok' : 'checking',
        detail: sm.scans_last_hour > 0
          ? `${sm.scans_last_hour} scans/hr`
          : 'Waiting for first scan',
      })
    }
  }

  const allOk = checks.length > 0 && checks.every(c => c.status === 'ok')
  const hasErrors = checks.some(c => c.status === 'error')

  return (
    <div className="card p-5">
      {/* Header with logo */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Rounded square background */}
            <rect width="40" height="40" rx="10" fill="#3ECF8E" />
            {/* P2P arrows icon */}
            <path
              d="M12 16h12m0 0l-4-4m4 4l-4 4"
              stroke="#0a0a0a"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M28 24H16m0 0l4 4m-4-4l4-4"
              stroke="#0a0a0a"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          {/* Status dot */}
          <div
            className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-bg-card ${
              allOk ? 'bg-accent-green' : hasErrors ? 'bg-accent-red' : 'bg-accent-orange'
            }`}
          />
        </div>
        <div>
          <p className="text-sm font-bold text-accent-green tracking-tight leading-none">
            P2P-TRADE
          </p>
          <p className="text-[10px] font-mono text-text-muted mt-0.5">
            {allOk ? 'All systems operational' : hasErrors ? 'System issues detected' : 'Starting up...'}
          </p>
        </div>
      </div>

      {/* System checks */}
      <div className="space-y-1.5">
        {checks.map(check => (
          <div key={check.label} className="flex items-center justify-between py-1">
            <div className="flex items-center gap-2">
              {check.status === 'checking' ? (
                <Spinner size={10} />
              ) : (
                <div
                  className={`w-2.5 h-2.5 rounded-full ${
                    check.status === 'ok' ? 'bg-accent-green' : 'bg-accent-red'
                  }`}
                />
              )}
              <span className="text-xs font-mono text-text-primary">{check.label}</span>
            </div>
            {check.detail && (
              <span className={`text-[11px] font-mono ${
                check.status === 'ok' ? 'text-text-muted' : check.status === 'error' ? 'text-accent-red' : 'text-text-muted'
              }`}>
                {check.detail}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
