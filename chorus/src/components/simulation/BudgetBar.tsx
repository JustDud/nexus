import { motion } from 'framer-motion'
import { useSimulation } from '../../context/SimulationContext'

function remainingColor(remainingPct: number): string {
  if (remainingPct > 50) return '#4AE8C0'
  if (remainingPct > 30) return '#f59e0b'
  return '#ef4444'
}

export function BudgetBar() {
  const { state } = useSimulation()

  const spent     = state.spentBudget
  const total     = state.totalBudget
  const remaining = total - spent
  const spentPct  = Math.min((spent / total) * 100, 100)
  const remainPct = Math.max(0, 100 - spentPct)
  const leftColor = remainingColor(remainPct)

  return (
    <div
      style={{
        background: 'rgba(8, 12, 24, 0.9)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderTop: `1px solid ${state.dangerMode ? 'rgba(239,68,68,0.4)' : 'rgba(100, 200, 255, 0.1)'}`,
        boxShadow: '0 -2px 20px rgba(60, 140, 255, 0.06)',
        transition: 'border-color 800ms ease',
      }}
    >
      {/* Main bar row */}
      <div
        className="flex items-center gap-4"
        style={{ padding: '12px 24px' }}
      >
        {/* Label */}
        <span
          style={{
            fontFamily: "'Space Mono', monospace",
            fontWeight: 600,
            fontSize: 13,
            color: '#A0AEC0',
            letterSpacing: '0.15em',
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
              background: 'rgba(100, 200, 255, 0.1)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <motion.div
              style={{
                height: '100%',
                background: 'linear-gradient(90deg, #3B82F6 0%, #4AE8C0 100%)',
                transformOrigin: 'left',
                boxShadow: '0 0 8px rgba(74, 232, 192, 0.3)',
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
              fontSize: 14,
              color: '#D0D8E4',
            }}
          >
            ${spent.toLocaleString()} spent
          </span>
          <span
            style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 14,
              color: '#D0D8E4',
            }}
          >
            of ${total.toLocaleString()} —
          </span>
          <motion.span
            style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 16,
              fontWeight: 700,
              color: leftColor,
              lineHeight: 1,
              textShadow: !state.dangerMode && remainPct > 50 ? '0 0 12px rgba(74, 232, 192, 0.3)' : 'none',
            }}
            animate={state.dangerMode ? { opacity: [1, 0.5, 1] } : { opacity: 1 }}
            transition={state.dangerMode ? { duration: 1.2, repeat: Infinity } : {}}
          >
            ${remaining.toLocaleString()} left
          </motion.span>
        </div>

      </div>
    </div>
  )
}
