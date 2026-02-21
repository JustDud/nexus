import { useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useSimulation } from '../../context/SimulationContext'
import { AGENTS } from '../../types'

function agentColor(agentId: string): string {
  return AGENTS.find((a) => a.id === agentId)?.color ?? '#94a3b8'
}

const AGENT_TAG: Record<string, string> = {
  product: 'PRODUCT',
  tech:    'TECH',
  ops:     'OPS',
  finance: 'FINANCE',
}

function timeAgo(ts: number): string {
  const diff = Math.floor((Date.now() - ts) / 1000)
  if (diff < 60) return `${diff}s ago`
  return `${Math.floor(diff / 60)}m ago`
}

export function ActivityFeed() {
  const { state } = useSimulation()
  const bottomRef = useRef<HTMLDivElement>(null)
  const hasEvents = state.activityLog.length > 0

  // Max 20 entries
  const entries = state.activityLog.slice(-20)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.activityLog.length])

  return (
    <div
      className="flex flex-col h-full overflow-hidden"
      style={{
        background: 'rgba(6, 10, 20, 0.7)',
        border: '1px solid rgba(100, 200, 255, 0.08)',
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
        borderRadius: 0,
      }}
    >
      {/* Header */}
      <div
        className="flex items-center gap-2 px-4 py-3 flex-shrink-0"
        style={{ borderBottom: '1px solid rgba(100, 200, 255, 0.08)' }}
      >
        <motion.span
          className="w-2 h-2 rounded-full flex-shrink-0"
          style={{ background: '#22c55e' }}
          animate={
            hasEvents
              ? { opacity: [1, 0.4, 1], scale: [1, 1.3, 1] }
              : { opacity: [0.7, 1, 0.7], scale: [1, 1.1, 1] }
          }
          transition={{ duration: 1.5, repeat: Infinity }}
        />
        <span
          style={{
            fontFamily: "'Space Mono', monospace",
            fontWeight: 700,
            fontSize: 13,
            color: '#C0F0E8',
            letterSpacing: '0.05em',
          }}
        >
          // LIVE FEED
        </span>
        <span
          style={{
            marginLeft: 'auto',
            fontFamily: "'VT323', monospace",
            fontSize: 18,
            color: '#5A6A7A',
          }}
        >
          {state.activityLog.length}
        </span>
      </div>

      {/* Entries */}
      <div className="flex-1 overflow-y-auto min-h-0" style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(100, 200, 255, 0.015) 2px, rgba(100, 200, 255, 0.015) 4px)' }}>
        {!hasEvents ? (
          <div
            className="flex items-center gap-1 p-4"
            style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 12,
              color: '#6B7A8A',
            }}
          >
            <motion.span
              animate={{ opacity: [1, 0, 1] }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            >
              █
            </motion.span>
            <span> awaiting agent activity...</span>
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {entries.map((entry) => {
              const color = agentColor(entry.agentId)
              const tag   = AGENT_TAG[entry.agentId] ?? entry.agentId.toUpperCase()

              return (
                <motion.div
                  key={entry.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.22, ease: 'easeOut' }}
                  style={{ borderBottom: '1px solid rgba(100, 200, 255, 0.06)', borderLeft: `2px solid ${color}` }}
                >
                  <div className="px-4 py-2">
                    {/* First line: [AGENT] → message */}
                    <div className="flex items-start gap-2">
                      <span
                        style={{
                          fontFamily: "'Space Mono', monospace",
                          fontWeight: 700,
                          fontSize: 11,
                          color,
                          flexShrink: 0,
                          whiteSpace: 'nowrap',
                        }}
                      >
                        [{tag}]
                      </span>
                      <span
                        style={{
                          fontFamily: "'Share Tech Mono', monospace",
                          fontSize: 13,
                          color: '#94a3b8',
                          lineHeight: 1.4,
                        }}
                      >
                        → {entry.message}
                      </span>
                    </div>
                    {/* Timestamp */}
                    <div
                      style={{
                        fontFamily: "'Share Tech Mono', monospace",
                        fontSize: 11,
                        color: '#5A6474',
                        textAlign: 'right',
                        marginTop: 2,
                      }}
                    >
                      {timeAgo(entry.timestamp)}
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
