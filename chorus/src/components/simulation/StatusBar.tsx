import { motion } from 'framer-motion'
import { useSimulation } from '../../context/SimulationContext'
import { formatElapsed } from '../../lib/utils'
import LetterGlitch from './LetterGlitch/LetterGlitch'

const STAGES = ['researching', 'planning', 'building', 'deploying', 'complete'] as const

const STAGE_LABEL: Record<string, string> = {
  researching: 'RESEARCH',
  planning:    'PLANNING',
  building:    'BUILDING',
  deploying:   'DEPLOY',
  complete:    'COMPLETE',
}

export function StatusBar() {
  const { state } = useSimulation()

  const currentStageIdx = STAGES.indexOf(state.stage as typeof STAGES[number])
  const burnRate = state.elapsedSeconds > 0
    ? (state.spentBudget / (state.elapsedSeconds / 60)).toFixed(1)
    : '0.0'

  const missionTitle = state.mission.length > 36
    ? state.mission.slice(0, 36) + '…'
    : state.mission

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
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* LetterGlitch texture — barely-visible animated watermark */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
          opacity: 0.09,
          pointerEvents: 'none',
        }}
      >
        <LetterGlitch
          glitchColors={['#1a1535', '#0e1a30', '#141020']}
          glitchSpeed={50}
          centerVignette={true}
          outerVignette={false}
          smooth={true}
        />
      </div>
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

      {/* RIGHT: elapsed time + burn rate */}
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
      </div>
    </div>
  )
}
