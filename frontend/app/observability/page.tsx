'use client'

import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { getHealth } from '@/lib/api'
import { useApi } from '@/hooks/useApi'
import { useWebSocket } from '@/hooks/useWebSocket'
import { wsClient } from '@/lib/ws'
import { Card, MetricCard } from '@/components/shared/Card'
import { StatusDot } from '@/components/shared/StatusDot'
import { Spinner } from '@/components/shared/Spinner'
import { formatDuration, statusColor } from '@/lib/utils'

interface LogLine {
  level: string
  message: string
  timestamp: number
}

const LEVEL_COLOR: Record<string, string> = {
  ERROR: 'text-accent-red',
  WARNING: 'text-accent-orange',
  INFO: 'text-text-primary',
  DEBUG: 'text-text-muted',
}

export default function ObservabilityPage() {
  const { data: health, loading, refetch } = useApi(() => getHealth(), [], { refreshInterval: 30_000 })
  const { connected } = useWebSocket()
  const [logs, setLogs] = useState<LogLine[]>([])
  const [logsEnabled, setLogsEnabled] = useState(false)
  const logEndRef = useRef<HTMLDivElement>(null)

  // Subscribe to log stream
  useEffect(() => {
    if (logsEnabled) {
      wsClient.subscribeLogs()
      const off = wsClient.on('log_line', e => {
        const d = e.data as LogLine
        setLogs(prev => [...prev.slice(-200), d])
      })
      return () => {
        off()
        wsClient.send({ cmd: 'unsubscribe_logs' })
      }
    }
  }, [logsEnabled])

  useEffect(() => {
    if (logsEnabled) {
      logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, logsEnabled])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold font-mono text-text-primary">System Observability</h1>
          <p className="text-sm text-text-secondary mt-1">
            Health checks, uptime, WebSocket, live log stream
          </p>
        </div>
        <button
          onClick={refetch}
          className="text-xs font-mono px-3 py-1.5 rounded bg-bg-border text-text-secondary hover:text-text-primary transition-colors"
        >
          ↺ Refresh
        </button>
      </div>

      {loading && (
        <div className="flex items-center gap-3 text-text-secondary">
          <Spinner size={16} />
          <span className="font-mono text-sm">Checking components...</span>
        </div>
      )}

      {health && (
        <>
          {/* Overall status */}
          <div className="flex items-center gap-3">
            <StatusDot
              status={health.status === 'healthy' ? 'ok' : health.status === 'degraded' ? 'slow' : 'error'}
              pulse
            />
            <span className={`font-mono text-lg font-bold uppercase ${
              health.status === 'healthy' ? 'text-accent-green' :
              health.status === 'degraded' ? 'text-accent-orange' : 'text-accent-red'
            }`}>
              {health.status}
            </span>
            <span className="text-text-muted text-sm font-mono">
              · Uptime: {formatDuration(health.uptime_sec)}
            </span>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard
              label="Scans / Hour"
              value={health.scan_metrics.scans_last_hour}
              color="text-accent-blue"
            />
            <MetricCard
              label="Scan Errors"
              value={health.scan_metrics.scan_errors_last_hour}
              color={health.scan_metrics.scan_errors_last_hour > 0 ? 'text-accent-red' : 'text-accent-green'}
            />
            <MetricCard
              label="Scan Interval"
              value={`${health.scan_metrics.scan_interval_sec}s`}
              color="text-text-primary"
            />
            <MetricCard
              label="WebSocket"
              value={connected ? 'Connected' : 'Offline'}
              color={connected ? 'text-accent-green' : 'text-accent-red'}
            />
          </div>

          {/* Component grid */}
          <Card title="Component Health">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(health.components).map(([name, comp]) => (
                <motion.div
                  key={name}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center justify-between p-3 rounded bg-bg-surface border border-bg-border"
                >
                  <div className="flex items-center gap-3">
                    <StatusDot status={comp.status as 'ok' | 'slow' | 'error'} />
                    <span className="text-sm font-mono text-text-primary">{name}</span>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-mono font-bold ${statusColor(comp.status)}`}>
                      {comp.status.toUpperCase()}
                    </p>
                    <p className="text-xs text-text-muted">{comp.latency_ms.toFixed(0)}ms</p>
                    {comp.error && (
                      <p className="text-xs text-accent-red mt-0.5">{comp.error}</p>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </Card>

          {/* API Latencies */}
          <Card title="API Latencies">
            <div className="space-y-2">
              {Object.entries(health.api_latency_ms).map(([name, ms]) => (
                <div key={name} className="flex items-center gap-3">
                  <span className="text-xs font-mono text-text-secondary w-32">{name}</span>
                  <div className="flex-1 h-1.5 bg-bg-border rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        ms < 200 ? 'bg-accent-green' : ms < 1000 ? 'bg-accent-orange' : 'bg-accent-red'
                      }`}
                      style={{ width: `${Math.min(100, (ms / 2000) * 100)}%` }}
                    />
                  </div>
                  <span className={`text-xs font-mono w-16 text-right ${
                    ms < 200 ? 'text-accent-green' : ms < 1000 ? 'text-accent-orange' : 'text-accent-red'
                  }`}>
                    {ms.toFixed(0)}ms
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}

      {/* Live log stream */}
      <Card title="Live Log Stream" titleRight={
        <div className="flex items-center gap-3">
          {logsEnabled && (
            <button
              onClick={() => setLogs([])}
              className="text-xs font-mono text-text-muted hover:text-text-secondary"
            >
              Clear
            </button>
          )}
          <button
            onClick={() => setLogsEnabled(v => !v)}
            className={`text-xs font-mono px-2 py-0.5 rounded transition-colors ${
              logsEnabled
                ? 'bg-accent-green/10 text-accent-green border border-accent-green/20'
                : 'bg-bg-border text-text-muted hover:text-text-secondary'
            }`}
          >
            {logsEnabled ? '● Live' : '○ Enable'}
          </button>
        </div>
      }>
        <div className="h-64 overflow-y-auto bg-bg-surface rounded p-3 font-mono text-xs">
          {logs.length === 0 && (
            <p className="text-text-muted">
              {logsEnabled
                ? 'Waiting for log events...'
                : 'Click "Enable" to stream live backend logs'}
            </p>
          )}
          {logs.map((log, i) => (
            <div key={i} className="flex gap-3 leading-5">
              <span className="text-text-muted shrink-0">
                {new Date(log.timestamp * 1000).toTimeString().slice(0, 8)}
              </span>
              <span className={`shrink-0 w-12 ${LEVEL_COLOR[log.level] ?? 'text-text-secondary'}`}>
                {log.level}
              </span>
              <span className="text-text-secondary break-all">{log.message}</span>
            </div>
          ))}
          <div ref={logEndRef} />
        </div>
      </Card>

      {/* MCP server instructions */}
      <Card title="MCP Server — Terminal Access">
        <p className="text-xs text-text-secondary mb-3">
          Connect Claude Code to this system for terminal diagnostics and building assistance.
        </p>
        <div className="space-y-3">
          <div>
            <p className="text-xs text-text-muted font-mono mb-1">Add to ~/.claude/settings.json:</p>
            <pre className="bg-bg-surface rounded p-3 text-xs font-mono text-text-primary overflow-x-auto">{`{
  "mcpServers": {
    "cryptodistro": {
      "command": "python",
      "args": ["-m", "backend.mcp_server.server"],
      "cwd": "/home/ironman/CryptoDistro2.0"
    }
  }
}`}</pre>
          </div>
          <div>
            <p className="text-xs text-text-muted font-mono mb-1">Available MCP tools:</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {[
                { name: 'get_system_status', desc: 'Full health + controller signals' },
                { name: 'run_simulation', desc: 'Run Monte Carlo simulation' },
                { name: 'get_market_data', desc: 'Live market premiums' },
                { name: 'trigger_refill_scan', desc: 'Rescan refill routes' },
                { name: 'get_trade_history', desc: 'Trades + PnL from DB' },
              ].map(t => (
                <div key={t.name} className="flex items-start gap-2 text-xs font-mono">
                  <span className="text-accent-green shrink-0">▸</span>
                  <div>
                    <span className="text-text-primary">{t.name}</span>
                    <span className="text-text-muted ml-2">— {t.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
