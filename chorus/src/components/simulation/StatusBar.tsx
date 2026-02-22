import { AnimatePresence, motion } from 'framer-motion'
import { useSimulation } from '../../context/SimulationContext'
import { formatElapsed } from '../../lib/utils'

const STAGES = ['researching', 'planning', 'building', 'deploying', 'operating', 'complete'] as const

const STAGE_LABEL: Record<string, string> = {
  researching: 'RESEARCH',
  planning:    'PLANNING',
  building:    'BUILDING',
  deploying:   'DEPLOY',
  operating:   'OPS',
  complete:    'COMPLETE',
}

interface StatusBarProps {
  isPaused?: boolean
  isMuted?: boolean
  onToggleMute?: () => void
  onStop?: () => void
  operationsRound?: number
  isDebating?: boolean
  isEavesdropping?: boolean
  onToggleEavesdrop?: () => void
}

export function StatusBar({ isMuted, onToggleMute, onStop, isDebating, isEavesdropping, onToggleEavesdrop }: StatusBarProps) {
  const { state } = useSimulation()

  const currentStageIdx = STAGES.indexOf(state.stage as typeof STAGES[number])
  const burnRate = state.elapsedSeconds > 0
    ? (state.spentBudget / (state.elapsedSeconds / 60)).toFixed(1)
    : '0.0'

  const missionTitle = state.projectTitle || state.mission

  return (
    <div
      className="nexus-status-bar flex items-center justify-between gap-4 px-5"
      style={{
        height: 52,
        background: 'rgba(5,5,10,0.98)',
        borderBottom: `1px solid ${state.dangerMode ? 'rgba(239,68,68,0.4)' : '#111'}`,
        backdropFilter: 'blur(16px)',
        transition: 'border-color 800ms ease',
        zIndex: 10,
      }}
    >
      {/* LEFT: NEXUS // mission */}
      <div
        className="flex items-center gap-2 min-w-0 flex-shrink-0"
        style={{ maxWidth: 280, position: 'relative', zIndex: 1 }}
      >
        <span
          className="text-white whitespace-nowrap"
          style={{
            fontFamily: 'Orbitron, sans-serif',
            fontWeight: 900,
            fontSize: 18,
            letterSpacing: '0.2em',
          }}
        >
          NEXUS //
        </span>
        <span
          className="text-[#333] select-none flex-shrink-0"
          style={{ fontSize: 14, fontWeight: 700 }}
        >
          /
        </span>
        <span
          className="truncate"
          style={{
            fontFamily: "'Space Mono', monospace",
            fontWeight: 400,
            fontSize: 13,
            color: '#64748b',
            maxWidth: 200,
          }}
          title={state.mission}
        >
          {missionTitle || 'no mission set'}
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

      {/* CENTER: stage pills */}
      <div
        className="flex items-center flex-shrink-0"
        style={{ gap: 0, position: 'relative', zIndex: 1 }}
      >
        {STAGES.map((stage, i) => {
          const isPast    = i < currentStageIdx
          const isCurrent = i === currentStageIdx
          const isLast    = i === STAGES.length - 1

          return (
            <div key={stage} className="flex items-center">
              <div
                style={{
                  fontFamily: "'Space Mono', monospace",
                  fontWeight: 700,
                  fontSize: 11,
                  padding: '2px 8px',
                  letterSpacing: '0.05em',
                  background: isCurrent ? 'white' : 'transparent',
                  color: isCurrent
                    ? '#000'
                    : isPast
                    ? '#3b82f6'
                    : '#1f2937',
                  textDecoration: isPast ? 'line-through' : 'none',
                  opacity: isPast ? 0.5 : 1,
                  transition: 'all 400ms ease',
                  whiteSpace: 'nowrap',
                }}
              >
                {STAGE_LABEL[stage]}
              </div>
              {!isLast && (
                <span style={{ color: '#333', fontSize: 14, margin: '0 2px', userSelect: 'none' }}>›</span>
              )}
            </div>
          )
        })}
      </div>

      {/* RIGHT: elapsed time + burn rate + controls */}
      <div
        className="flex items-center gap-4 flex-shrink-0"
        style={{ position: 'relative', zIndex: 1 }}
      >
        {state.dangerMode && (
          <motion.span
            style={{
              fontFamily: "'Space Mono', monospace",
              fontWeight: 700,
              fontSize: 10,
              color: '#ef4444',
              letterSpacing: '0.15em',
            }}
            animate={{ opacity: [1, 0.2, 1] }}
            transition={{ duration: 0.7, repeat: Infinity }}
          >
            ⚠ LOW FUNDS
          </motion.span>
        )}
        <div className="text-right">
          <motion.div
            style={{
              fontFamily: "'VT323', monospace",
              fontSize: 28,
              lineHeight: 1,
              color: state.dangerMode ? '#ef4444' : 'white',
              letterSpacing: '0.05em',
            }}
            animate={state.dangerMode ? { opacity: [1, 0.5, 1] } : { opacity: 1 }}
            transition={state.dangerMode ? { duration: 1.2, repeat: Infinity } : {}}
          >
            {formatElapsed(state.elapsedSeconds)}
          </motion.div>
          <div
            style={{
              fontFamily: "'Space Mono', monospace",
              fontWeight: 400,
              fontSize: 10,
              color: '#64748b',
              lineHeight: 1.2,
            }}
          >
            ${burnRate}/min
          </div>
        </div>

        {/* Eavesdrop button — only during debate */}
        <AnimatePresence>
          {isDebating && onToggleEavesdrop && (
            <motion.button
              key="eavesdrop"
              initial={{ opacity: 0, scale: 0.9, width: 0 }}
              animate={{ opacity: 1, scale: 1, width: 'auto' }}
              exit={{ opacity: 0, scale: 0.9, width: 0 }}
              transition={{ duration: 0.25 }}
              onClick={onToggleEavesdrop}
              className="flex items-center gap-1.5 px-3 py-1 rounded-lg overflow-hidden"
              style={{
                background: isEavesdropping ? 'rgba(139,92,246,0.2)' : 'rgba(255,255,255,0.05)',
                border: `1px solid ${isEavesdropping ? 'rgba(139,92,246,0.5)' : 'rgba(255,255,255,0.1)'}`,
                color: isEavesdropping ? '#a78bfa' : '#94a3b8',
                transition: 'background 200ms, border-color 200ms, color 200ms',
              }}
              title={isEavesdropping ? 'Stop listening to agents' : 'Listen to agent debate'}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 18v-6a9 9 0 0 1 18 0v6" />
                <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z" />
              </svg>
              <span style={{
                fontFamily: "'Space Mono', monospace",
                fontWeight: 700,
                fontSize: 10,
                letterSpacing: '0.05em',
                whiteSpace: 'nowrap',
              }}>
                {isEavesdropping ? 'STOP LISTENING' : 'LISTEN IN'}
              </span>
              {isEavesdropping && (
                <motion.span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    background: '#a78bfa',
                  }}
                  animate={{ opacity: [1, 0.3, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                />
              )}
            </motion.button>
          )}
        </AnimatePresence>

        {/* Mute / unmute button */}
        {onToggleMute && (
          <button
            onClick={onToggleMute}
            className="p-1.5 rounded-lg transition-colors hover:bg-[#1a1a2e]"
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                <line x1="23" y1="9" x2="17" y2="15" />
                <line x1="17" y1="9" x2="23" y2="15" />
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
    </div>
  )
}
