import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
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

const MESSAGE_COLLAPSE_THRESHOLD = 120

function ExpandableMessage({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false)
  const isLong = text.length > MESSAGE_COLLAPSE_THRESHOLD

  const displayText = isLong && !expanded
    ? text.slice(0, MESSAGE_COLLAPSE_THRESHOLD) + '...'
    : text

  return (
    <span>
      <span className="activity-markdown">
        <ReactMarkdown
          components={{
            p: ({ children }) => <span>{children}</span>,
            a: ({ href, children }) => (
              <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: '#60a5fa', textDecoration: 'underline' }}>
                {children}
              </a>
            ),
            strong: ({ children }) => <strong style={{ color: '#e2e8f0', fontWeight: 700 }}>{children}</strong>,
            em: ({ children }) => <em style={{ color: '#cbd5e1' }}>{children}</em>,
            code: ({ children }) => (
              <code style={{ background: 'rgba(255,255,255,0.06)', padding: '1px 4px', borderRadius: 3, fontSize: '0.9em' }}>
                {children}
              </code>
            ),
            ul: ({ children }) => <span style={{ display: 'block', paddingLeft: 12, marginTop: 2 }}>{children}</span>,
            ol: ({ children }) => <span style={{ display: 'block', paddingLeft: 12, marginTop: 2 }}>{children}</span>,
            li: ({ children }) => <span style={{ display: 'block' }}>• {children}</span>,
          }}
        >
          {displayText}
        </ReactMarkdown>
      </span>
      {isLong && (
        <button
          onClick={() => setExpanded(!expanded)}
          style={{
            fontFamily: "'Space Mono', monospace",
            fontSize: 10,
            color: '#3b82f6',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '2px 0',
            marginLeft: 4,
          }}
        >
          {expanded ? '← less' : 'see more →'}
        </button>
      )}
    </span>
  )
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
              const isDebate = entry.type === 'debate'

              /* ── Conclusion entry — distinct full-width banner ── */
              if (entry.type === 'conclusion') {
                const isFailed = entry.message.includes('FAILED')
                const accentColor = isFailed ? '#ef4444' : '#34d399'
                return (
                  <motion.div
                    key={entry.id}
                    initial={{ opacity: 0, scale: 0.96 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.4, ease: 'easeOut' }}
                    style={{
                      borderBottom: `1px solid ${accentColor}33`,
                      borderLeft: `2px solid ${accentColor}`,
                      background: `linear-gradient(90deg, ${accentColor}12, transparent)`,
                    }}
                  >
                    <div className="px-4 py-3">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                        <div style={{
                          width: 8, height: 8, borderRadius: '50%',
                          background: accentColor,
                          boxShadow: `0 0 10px ${accentColor}88`,
                        }} />
                        <span style={{
                          fontFamily: "'Space Mono', monospace",
                          fontWeight: 700,
                          fontSize: 11,
                          letterSpacing: '0.15em',
                          color: accentColor,
                        }}>
                          {isFailed ? 'MISSION FAILED' : 'MISSION COMPLETE'}
                        </span>
                      </div>
                      <div style={{
                        fontFamily: "'Share Tech Mono', monospace",
                        fontSize: 13,
                        color: '#C0C8D4',
                        lineHeight: 1.5,
                        paddingLeft: 16,
                      }}>
                        <ExpandableMessage text={entry.message} />
                      </div>
                      <div style={{
                        fontFamily: "'Share Tech Mono', monospace",
                        fontSize: 11,
                        color: '#5A6474',
                        textAlign: 'right',
                        marginTop: 4,
                      }}>
                        {timeAgo(entry.timestamp)}
                      </div>
                    </div>
                  </motion.div>
                )
              }

              return (
                <motion.div
                  key={entry.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.22, ease: 'easeOut' }}
                  style={{
                    borderBottom: '1px solid rgba(100, 200, 255, 0.06)',
                    borderLeft: isDebate ? '3px solid #8b5cf6' : `2px solid ${color}`,
                    ...(isDebate ? {
                      background: 'linear-gradient(90deg, rgba(139,92,246,0.12) 0%, rgba(59,130,246,0.06) 100%)',
                    } : {}),
                  }}
                >
                  <div className="px-4 py-2">
                    {/* First line: [AGENT] → message */}
                    <div className="flex items-start gap-2">
                      <span
                        style={{
                          fontFamily: "'Space Mono', monospace",
                          fontWeight: 700,
                          fontSize: 11,
                          color: isDebate ? '#a78bfa' : color,
                          flexShrink: 0,
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {isDebate ? '[DEBATE]' : `[${tag}]`}
                      </span>
                      <span
                        style={{
                          fontFamily: "'Share Tech Mono', monospace",
                          fontSize: 13,
                          color: isDebate ? '#c4b5fd' : '#94a3b8',
                          lineHeight: 1.4,
                          fontWeight: isDebate ? 700 : 400,
                        }}
                      >
                        → <ExpandableMessage text={entry.message} />
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
