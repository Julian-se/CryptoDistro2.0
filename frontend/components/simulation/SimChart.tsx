'use client'

import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts'
import { SimResult, MilestonePoint } from '@/lib/api'
import { formatUSD } from '@/lib/utils'

interface SimChartProps {
  lightning: SimResult
  milestones: Record<string, MilestonePoint>
}

export function SimChart({ lightning, milestones }: SimChartProps) {
  // Build chart data from parallel arrays
  const data = lightning.capital.map((cap, i) => ({
    day: i,
    capital: cap,
    p10: lightning.p10[i],
    p90: lightning.p90[i],
    profit: lightning.profit[i],
  }))

  const milestoneList = Object.values(milestones)

  const CustomTooltip = ({ active, payload, label }: {
    active?: boolean
    payload?: { name: string; value: number; color: string }[]
    label?: number
  }) => {
    if (!active || !payload?.length) return null
    return (
      <div className="card p-3 text-xs font-mono">
        <p className="text-text-muted mb-1">Day {label}</p>
        {payload.map(p => (
          <p key={p.name} style={{ color: p.color }}>
            {p.name}: {formatUSD(p.value)}
          </p>
        ))}
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
        <defs>
          <linearGradient id="capGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#00ff88" stopOpacity={0.15} />
            <stop offset="95%" stopColor="#00ff88" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="bandGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#0088ff" stopOpacity={0.06} />
            <stop offset="95%" stopColor="#0088ff" stopOpacity={0} />
          </linearGradient>
        </defs>

        <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
        <XAxis
          dataKey="day"
          tick={{ fill: '#555577', fontSize: 11, fontFamily: 'monospace' }}
          tickLine={false}
          axisLine={{ stroke: '#1e1e2e' }}
        />
        <YAxis
          tickFormatter={v => `$${v}`}
          tick={{ fill: '#555577', fontSize: 11, fontFamily: 'monospace' }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip content={<CustomTooltip />} />

        {/* P90 band top */}
        <Area type="monotone" dataKey="p90" stroke="none" fill="url(#bandGrad)" name="P90" />
        {/* P10 band bottom */}
        <Area
          type="monotone" dataKey="p10"
          stroke="#0088ff" strokeWidth={1} strokeDasharray="4 2"
          fill="#0a0a0f" name="P10"
        />
        {/* Main curve */}
        <Area
          type="monotone" dataKey="capital"
          stroke="#00ff88" strokeWidth={2}
          fill="url(#capGrad)" name="Capital (median)"
        />

        {/* Starting capital reference */}
        <ReferenceLine y={500} stroke="#555577" strokeDasharray="3 3" />

        {/* Milestone markers */}
        {milestoneList.map(m => (
          <ReferenceLine
            key={m.day}
            x={m.day}
            stroke="#ff8c00"
            strokeDasharray="3 3"
            label={{ value: `Day ${m.day}`, fill: '#ff8c00', fontSize: 10 }}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  )
}
