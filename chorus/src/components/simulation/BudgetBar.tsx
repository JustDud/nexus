import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useSimulation } from '../../context/SimulationContext'
import { AGENTS } from '../../types'

function remainingColor(remainingPct: number): string {
  if (remainingPct > 50) return '#22c55e'
  if (remainingPct > 30) return '#f59e0b'
  return '#ef4444'
}

export function BudgetBar() {
  const { state } = useSimulation()
  const [expanded, setExpanded] = useState(false)

  const spent     = state.spentBudget
  const total     = state.totalBudget
  const remaining = total - spent
  const spentPct  = Math.min((spent / total) * 100, 100)
  const remainPct = Math.max(0, 100 - spentPct)
  const leftColor = remainingColor(remainPct)

  const chartData = AGENTS.map((def) => {
    const ag = state.agents.find((a) => a.id === def.id)
    return { name: def.name.split(' ')[0], spend: ag?.totalSpent ?? 0, color: def.color }
  })

  return (
    <div
      style={{
        background: '#05050a',
        borderTop: `1px solid ${state.dangerMode ? 'rgba(239,68,68,0.4)' : '#111'}`,
        transition: 'border-color 800ms ease',
      }}
    >
      {/* Expanded breakdown chart */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 160, opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            style={{ overflow: 'hidden', padding: '16px 24px 0' }}
          >
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#64748b', fontSize: 9, fontFamily: "'Space Mono', monospace" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#64748b', fontSize: 9, fontFamily: "'Space Mono', monospace" }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `$${v}`}
                />
                <Tooltip
                  contentStyle={{
                    background: '#0a0a12',
                    border: '1px solid #111',
                    borderRadius: 0,
                    fontFamily: "'Share Tech Mono', monospace",
                    fontSize: 11,
                    color: '#f8fafc',
                  }}
                  formatter={(v: number | undefined) => [`$${v ?? 0}`, 'Spent']}
                  cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                />
                <Bar dataKey="spend" radius={[2, 2, 0, 0]}>
                  {chartData.map((e, i) => <Cell key={i} fill={e.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main bar row */}
      <div
        className="flex items-center gap-4"
        style={{ height: 48, padding: '0 24px' }}
      >
        {/* Label */}
        <span
          style={{
            fontFamily: "'Space Mono', monospace",
            fontWeight: 700,
            fontSize: 10,
            color: '#374151',
            letterSpacing: '0.2em',
            flexShrink: 0,
          }}
        >
          BUDGET
        </span>

        {/* Progress bar */}
        <div style={{ flex: 1, position: 'relative' }}>
          <div
            style={{
              height: 6,
              background: '#111',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <motion.div
              style={{
                height: '100%',
                background: 'linear-gradient(90deg, #22c55e 0%, #f59e0b 50%, #ef4444 100%)',
                transformOrigin: 'left',
              }}
              animate={{ width: `${spentPct}%` }}
              transition={{ type: 'spring', stiffness: 60, damping: 20 }}
            />
          </div>
          {/* Danger pulse overlay */}
          {state.dangerMode && (
            <motion.div
              style={{
                position: 'absolute',
                inset: 0,
                background: 'rgba(239,68,68,0.3)',
              }}
              animate={{ opacity: [0.6, 0, 0.6] }}
              transition={{ duration: 0.9, repeat: Infinity }}
            />
          )}
        </div>

        {/* Numbers */}
        <div
          className="flex items-baseline gap-1 flex-shrink-0"
          style={{ whiteSpace: 'nowrap' }}
        >
          <span
            style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 13,
              color: '#64748b',
            }}
          >
            ${spent.toLocaleString()} spent
          </span>
          <span
            style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 13,
              color: '#374151',
            }}
          >
            of ${total.toLocaleString()} —
          </span>
          <motion.span
            style={{
              fontFamily: "'VT323', monospace",
              fontSize: 22,
              color: leftColor,
              lineHeight: 1,
            }}
            animate={state.dangerMode ? { opacity: [1, 0.5, 1] } : { opacity: 1 }}
            transition={state.dangerMode ? { duration: 1.2, repeat: Infinity } : {}}
          >
            ${remaining.toLocaleString()} left
          </motion.span>
        </div>

        {/* Breakdown toggle */}
        <button
          onClick={() => setExpanded((v) => !v)}
          style={{
            fontFamily: "'Space Mono', monospace",
            fontSize: 11,
            color: '#374151',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            marginLeft: 'auto',
            flexShrink: 0,
            padding: '4px 0',
            transition: 'color 150ms ease',
          }}
          onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = '#f59e0b' }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = '#374151' }}
        >
          ↑ breakdown
        </button>
      </div>
    </div>
  )
}
