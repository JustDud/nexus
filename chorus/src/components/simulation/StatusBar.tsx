import { motion } from 'framer-motion'
import { useSimulation } from '../../context/SimulationContext'
import { formatElapsed } from '../../lib/utils'

const STAGES = ['researching', 'planning', 'building', 'deploying', 'operating', 'complete'] as const

const STAGE_LABELS: Record<string, string> = {
  researching: 'RESEARCHING',
  planning: 'PLANNING',
  building: 'BUILDING',
  deploying: 'DEPLOYING',
  operating: 'OPS',
  complete: 'COMPLETE',
}

interface StatusBarProps {
  isPaused?: boolean
  isMuted?: boolean
  onToggleMute?: () => void
  onStop?: () => void
  operationsRound?: number
}

export function StatusBar({ isMuted, onToggleMute, onStop }: StatusBarProps) {
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
        {state.isPaused && (
          <motion.span
            className="font-bold text-[10px] tracking-widest px-2 py-0.5 rounded-full ml-2 flex-shrink-0"
            style={{
              fontFamily: 'Space Grotesk, sans-serif',
              background: 'rgba(239,68,68,0.15)',
              color: '#ef4444',
              border: '1px solid rgba(239,68,68,0.3)',
            }}
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ duration: 1.2, repeat: Infinity }}
          >
            WAITING FOR CEO
          </motion.span>
        )}
        {state.operationsRound > 0 && !state.isPaused && (
          <span
            className="font-mono text-[10px] text-[#64748b] ml-2 flex-shrink-0"
          >
            Week {state.operationsRound}
          </span>
        )}
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
              <span className="text-[#1a1a2e] text-[10px] mx-0.5">{'\u2192'}</span>
            )}
          </div>
        ))}
      </div>

      {/* Time + burn rate + controls */}
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
            {'\u26A0'} LOW BUDGET
          </motion.span>
        )}

        {/* Mute / unmute button */}
        {onToggleMute && (
          <button
            onClick={onToggleMute}
            className="p-1.5 rounded-lg transition-colors hover:bg-[#1a1a2e]"
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="1" y1="1" x2="23" y2="23" />
                <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
                <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2c0 .76-.12 1.5-.35 2.18" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
              </svg>
            )}
          </button>
        )}

        {/* Stop button */}
        {onStop && (
          <button
            onClick={onStop}
            className="p-1.5 rounded-lg transition-colors hover:bg-[#1a1a2e]"
            title="Stop simulation"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#ef4444" stroke="none">
              <rect x="4" y="4" width="16" height="16" rx="2" />
            </svg>
          </button>
        )}
      </div>
    </motion.div>
  )
}
