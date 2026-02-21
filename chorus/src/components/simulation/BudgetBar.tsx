import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { useSimulation } from '../../context/SimulationContext'
import { AGENTS } from '../../types'
import { GlassPanel } from '../shared/GlassPanel'
import { formatCurrency } from '../../lib/utils'

function pctColor(pct: number): string {
  if (pct > 70) return '#ef4444'
  if (pct > 50) return '#f59e0b'
  return '#22c55e'
}

export function BudgetBar() {
  const { state } = useSimulation()
  const [expanded, setExpanded] = useState(false)

  const spent = state.spentBudget
  const total = state.totalBudget
  const remaining = total - spent
  const pct = Math.min((spent / total) * 100, 100)
  const fillColor = pctColor(pct)

  const chartData = AGENTS.map((def) => {
    const agentState = state.agents.find((a) => a.id === def.id)
    return {
      name: def.id.charAt(0).toUpperCase() + def.id.slice(1),
      spend: agentState?.totalSpent ?? 0,
      color: def.color,
    }
  })

  return (
    <GlassPanel danger={state.dangerMode} className="px-6 py-4 space-y-3">
      {/* Bar row */}
      <div className="flex items-center gap-4">
        {/* Track */}
        <div className="flex-1 h-2 rounded-full bg-[#1a1a2e] overflow-hidden relative">
          <motion.div
            className="h-full rounded-full"
            style={{ background: fillColor }}
            layout
            animate={{ width: `${pct}%` }}
            transition={{ type: 'spring', stiffness: 60, damping: 20 }}
          />
          {state.dangerMode && (
            <motion.div
              className="absolute inset-0 rounded-full"
              style={{ background: '#ef444440' }}
              animate={{ opacity: [0.4, 0, 0.4] }}
              transition={{ duration: 1, repeat: Infinity }}
            />
          )}
        </div>

        {/* Labels */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <span className="font-mono text-xs text-[#94a3b8]">
            <span style={{ color: fillColor }}>{formatCurrency(spent)}</span>
            {' spent of '}
            {formatCurrency(total)}
            {' — '}
            <span className={state.dangerMode ? 'text-[#ef4444] font-bold' : 'text-[#22c55e]'}>
              {formatCurrency(remaining)} remaining
            </span>
          </span>

          <button
            onClick={() => setExpanded((v) => !v)}
            className="font-mono text-[10px] text-[#64748b] hover:text-[#3b82f6] flex items-center gap-1 transition-colors"
          >
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            breakdown
          </button>
        </div>
      </div>

      {/* Expandable breakdown chart */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 160, opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `$${v}`}
                />
                <Tooltip
                  contentStyle={{
                    background: '#0f0f1a',
                    border: '1px solid #1a1a2e',
                    borderRadius: 8,
                    fontFamily: 'JetBrains Mono',
                    fontSize: 11,
                    color: '#f8fafc',
                  }}
                  formatter={(value: number) => [`$${value}`, 'Spent']}
                  cursor={{ fill: 'rgba(59,130,246,0.05)' }}
                />
                <Bar dataKey="spend" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        )}
      </AnimatePresence>
    </GlassPanel>
  )
}
