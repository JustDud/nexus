import { motion } from 'framer-motion'
import { useSimulation } from '../../context/SimulationContext'
import { formatElapsed } from '../../lib/utils'

const STAGES = ['researching', 'planning', 'building', 'deploying', 'complete'] as const

const STAGE_LABELS: Record<string, string> = {
  researching: 'RESEARCHING',
  planning: 'PLANNING',
  building: 'BUILDING',
  deploying: 'DEPLOYING',
  complete: 'COMPLETE',
}

export function StatusBar() {
  const { state } = useSimulation()

  const currentStageIdx = STAGES.indexOf(state.stage as typeof STAGES[number])
  const burnRate = state.elapsedSeconds > 0
    ? (state.spentBudget / (state.elapsedSeconds / 60)).toFixed(2)
    : '0.00'

  const missionTitle = state.mission.length > 48
    ? state.mission.slice(0, 48) + '...'
    : state.mission

  return (
    <motion.div
      className="flex items-center justify-between px-6 py-3 border-b transition-all duration-700"
      style={{
        borderColor: state.dangerMode ? 'rgba(239,68,68,0.4)' : '#1a1a2e',
        background: state.dangerMode
          ? 'rgba(239,68,68,0.06)'
          : 'rgba(15,15,26,0.95)',
        backdropFilter: 'blur(12px)',
      }}
      animate={state.dangerMode ? { borderColor: ['rgba(239,68,68,0.4)', 'rgba(239,68,68,0.8)', 'rgba(239,68,68,0.4)'] } : {}}
      transition={{ duration: 1.5, repeat: state.dangerMode ? Infinity : 0 }}
    >
      {/* Mission */}
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <span className="w-2 h-2 rounded-full bg-[#3b82f6] animate-pulse flex-shrink-0" />
        <span
          className="font-mono text-xs text-[#94a3b8] truncate"
          title={state.mission}
        >
          {missionTitle || 'No mission set'}
        </span>
      </div>

      {/* Stage pipeline */}
      <div className="flex items-center gap-1 flex-shrink-0">
        {STAGES.map((stage, i) => (
          <div key={stage} className="flex items-center gap-1">
            <span
              className="font-bold text-[10px] tracking-widest transition-all duration-500"
              style={{
                fontFamily: 'Space Grotesk, sans-serif',
                color:
                  i < currentStageIdx
                    ? '#22c55e'
                    : i === currentStageIdx
                    ? '#f8fafc'
                    : '#1a1a2e',
              }}
            >
              {STAGE_LABELS[stage]}
            </span>
            {i < STAGES.length - 1 && (
              <span className="text-[#1a1a2e] text-[10px] mx-0.5">→</span>
            )}
          </div>
        ))}
      </div>

      {/* Time + burn rate */}
      <div className="flex items-center gap-4 flex-shrink-0 ml-4">
        <div className="text-right">
          <div className="font-mono text-xs text-[#f8fafc] tabular-nums">
            {formatElapsed(state.elapsedSeconds)}
          </div>
          <div
            className="font-mono text-[9px]"
            style={{ color: state.dangerMode ? '#ef4444' : '#64748b' }}
          >
            ${burnRate}/min
          </div>
        </div>
        {state.dangerMode && (
          <motion.span
            className="font-bold text-[10px] text-[#ef4444] tracking-widest"
            animate={{ opacity: [1, 0, 1] }}
            transition={{ duration: 0.6, repeat: Infinity }}
          >
            ⚠ LOW BUDGET
          </motion.span>
        )}
      </div>
    </motion.div>
  )
}
