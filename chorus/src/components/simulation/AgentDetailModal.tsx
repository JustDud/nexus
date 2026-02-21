import { useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'
import { useSimulation } from '../../context/SimulationContext'
import { AGENTS, type AgentId } from '../../types'
import AgentShape from './shapes/AgentShape'
import ElectricBorder from './ElectricBorder'
import { formatElapsed } from '../../lib/utils'

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

interface AgentDetailModalProps {
  agentId: AgentId | null
  onClose: () => void
}

export function AgentDetailModal({ agentId, onClose }: AgentDetailModalProps) {
  const { state } = useSimulation()

  const isOpen     = !!agentId
  const def        = agentId ? AGENTS.find((a) => a.id === agentId) : null
  const agentState = agentId ? state.agents.find((a) => a.id === agentId) : null
  const logs       = state.activityLog.filter((e) => e.agentId === agentId)
  const startTs    = state.activityLog[0]?.timestamp ?? Date.now()

  // ESC key to close
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isOpen, onClose])

  // Lock body scroll when open
  useEffect(() => {
    if (isOpen) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  return (
    <AnimatePresence>
      {isOpen && def && agentState && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 40,
              background: 'rgba(5,5,10,0.88)',
              backdropFilter: 'blur(8px)',
            }}
          />

          {/* Modal — centered */}
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.94, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 50,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 24,
              pointerEvents: 'none',
            }}
          >
            {/* Stop click-through */}
            <div style={{ pointerEvents: 'auto' }} onClick={e => e.stopPropagation()}>
              <ElectricBorder
                color={def.color}
                speed={1}
                chaos={0.12}
                borderRadius={4}
              >
                {/* Modal panel */}
                <div
                  style={{
                    width: 620,
                    maxWidth: '90vw',
                    maxHeight: '82vh',
                    background: '#0a0a12',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                  }}
                >
                  {/* ── HEADER ─────────────────────────────── */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 16,
                      padding: '16px 20px',
                      borderBottom: `1px solid ${def.color}20`,
                      flexShrink: 0,
                    }}
                  >
                    {/* Mini 3D shape */}
                    <div style={{ flexShrink: 0 }}>
                      <AgentShape agentId={def.id} state={agentState.status} size={72} />
                    </div>

                    {/* Name + role */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          fontFamily: "'Space Mono', monospace",
                          fontWeight: 700,
                          fontSize: 13,
                          color: def.color,
                          letterSpacing: '0.18em',
                          textTransform: 'uppercase',
                        }}
                      >
                        {def.name}
                      </div>
                      <div
                        style={{
                          fontFamily: "'Share Tech Mono', monospace",
                          fontSize: 11,
                          color: '#64748b',
                          marginTop: 2,
                        }}
                      >
                        {def.role}
                      </div>
                    </div>

                    {/* Close button */}
                    <button
                      onClick={onClose}
                      style={{
                        flexShrink: 0,
                        background: 'none',
                        border: `1px solid #333`,
                        color: '#64748b',
                        cursor: 'pointer',
                        padding: 6,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'color 150ms, border-color 150ms',
                      }}
                      onMouseEnter={e => {
                        const el = e.currentTarget as HTMLButtonElement
                        el.style.color = 'white'
                        el.style.borderColor = def.color
                      }}
                      onMouseLeave={e => {
                        const el = e.currentTarget as HTMLButtonElement
                        el.style.color = '#64748b'
                        el.style.borderColor = '#333'
                      }}
                    >
                      <X size={16} />
                    </button>
                  </div>

                  {/* ── STAT PILLS ─────────────────────────── */}
                  <div
                    style={{
                      display: 'flex',
                      gap: 1,
                      background: '#111',
                      flexShrink: 0,
                    }}
                  >
                    {[
                      { label: 'STATUS',  value: agentState.status.toUpperCase() },
                      { label: 'SPENT',   value: `$${agentState.totalSpent}` },
                      { label: 'ACTIONS', value: String(agentState.completedActions.length) },
                    ].map(({ label, value }) => (
                      <div
                        key={label}
                        style={{
                          flex: 1,
                          padding: '12px 16px',
                          background: '#0a0a12',
                          border: `1px solid ${def.color}20`,
                          borderTop: 'none',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 2,
                        }}
                      >
                        <div
                          style={{
                            fontFamily: "'VT323', monospace",
                            fontSize: 24,
                            color: label === 'STATUS' && agentState.status === 'blocked'
                              ? '#ef4444'
                              : def.color,
                            lineHeight: 1,
                          }}
                        >
                          {value}
                        </div>
                        <div
                          style={{
                            fontFamily: "'Space Mono', monospace",
                            fontWeight: 400,
                            fontSize: 9,
                            color: '#64748b',
                            letterSpacing: '0.2em',
                            textTransform: 'uppercase',
                          }}
                        >
                          {label}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* ── SCROLLABLE CONTENT ─────────────────── */}
                  <div
                    className="modal-scroll"
                    style={{
                      flex: 1,
                      overflowY: 'auto',
                      minHeight: 0,
                      '--agent-color': def.color,
                    } as React.CSSProperties}
                  >
                    {/* Completed actions */}
                    {agentState.completedActions.length > 0 && (
                      <div style={{ padding: '16px 20px', borderBottom: `1px solid #111` }}>
                        <div
                          style={{
                            fontFamily: "'Space Mono', monospace",
                            fontWeight: 700,
                            fontSize: 10,
                            color: def.color,
                            letterSpacing: '0.2em',
                            textTransform: 'uppercase',
                            marginBottom: 10,
                          }}
                        >
                          // COMPLETED ACTIONS
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                          {agentState.completedActions.map((action) => (
                            <div
                              key={action.id}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 8,
                                paddingBottom: 6,
                                borderBottom: '1px solid #111',
                              }}
                            >
                              <span
                                style={{
                                  fontFamily: "'Space Mono', monospace",
                                  fontWeight: 700,
                                  fontSize: 11,
                                  color: action.status === 'approved' ? def.color : '#ef4444',
                                  flexShrink: 0,
                                }}
                              >
                                {action.status === 'approved' ? '✓' : '✗'}
                              </span>
                              <span
                                style={{
                                  fontFamily: "'Share Tech Mono', monospace",
                                  fontSize: 12,
                                  color: 'white',
                                  flex: 1,
                                  minWidth: 0,
                                }}
                              >
                                {action.description}
                              </span>
                              {action.cost > 0 && (
                                <span
                                  style={{
                                    fontFamily: "'VT323', monospace",
                                    fontSize: 16,
                                    color: def.color,
                                    flexShrink: 0,
                                  }}
                                >
                                  ${action.cost}
                                </span>
                              )}
                              <span
                                style={{
                                  fontFamily: "'Share Tech Mono', monospace",
                                  fontSize: 10,
                                  color: '#374151',
                                  flexShrink: 0,
                                }}
                              >
                                {formatElapsed(Math.floor((Date.now() - action.timestamp) / 1000))}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Reasoning log */}
                    <div style={{ padding: '16px 20px' }}>
                      <div
                        style={{
                          fontFamily: "'Space Mono', monospace",
                          fontWeight: 700,
                          fontSize: 10,
                          color: def.color,
                          letterSpacing: '0.2em',
                          textTransform: 'uppercase',
                          marginBottom: 10,
                        }}
                      >
                        // REASONING LOG
                      </div>
                      {logs.length === 0 ? (
                        <span
                          style={{
                            fontFamily: "'Share Tech Mono', monospace",
                            fontSize: 12,
                            color: '#374151',
                          }}
                        >
                          No log entries yet.
                        </span>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                          {logs.map((entry) => {
                            const entryColor = AGENTS.find(a => a.id === entry.agentId)?.color ?? '#94a3b8'
                            const tag = AGENT_TAG[entry.agentId] ?? entry.agentId.toUpperCase()
                            return (
                              <div key={entry.id}>
                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                                  <span
                                    style={{
                                      fontFamily: "'Space Mono', monospace",
                                      fontWeight: 700,
                                      fontSize: 11,
                                      color: entryColor,
                                      flexShrink: 0,
                                      whiteSpace: 'nowrap',
                                    }}
                                  >
                                    [{tag}]
                                  </span>
                                  <span
                                    style={{
                                      fontFamily: "'Share Tech Mono', monospace",
                                      fontSize: 12,
                                      color:
                                        entry.type === 'block'    ? '#ef4444'   :
                                        entry.type === 'complete' ? '#22c55e'   :
                                        entry.type === 'action'   ? entryColor  : '#94a3b8',
                                      lineHeight: 1.5,
                                    }}
                                  >
                                    → {entry.message}
                                  </span>
                                </div>
                                <div
                                  style={{
                                    fontFamily: "'Share Tech Mono', monospace",
                                    fontSize: 10,
                                    color: '#374151',
                                    textAlign: 'right',
                                    marginTop: 2,
                                  }}
                                >
                                  {formatElapsed(Math.floor((entry.timestamp - startTs) / 1000))}
                                  {' '}· {timeAgo(entry.timestamp)}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </ElectricBorder>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
