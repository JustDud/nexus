import { useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSimulation } from '../../context/SimulationContext'
import { AGENTS, type AgentId } from '../../types'

interface StripeModalProps {
  open: boolean
  onClose: () => void
}

const ACCENT = 'rgba(139,92,246'

const AGENT_COLORS: Record<AgentId, string> = {
  product: '#f59e0b',
  tech:    '#22c55e',
  ops:     '#8b5cf6',
  finance: '#ef4444',
}

const BTN_BASE: React.CSSProperties = {
  fontFamily: "'Space Mono', monospace",
  fontSize: 10,
  letterSpacing: '0.08em',
  cursor: 'pointer',
  border: 'none',
  transition: 'all 0.2s ease',
}

export function StripeModal({ open, onClose }: StripeModalProps) {
  const { state } = useSimulation()

  const stats = useMemo(() => {
    const txs = state.transactions.filter(t => t.status === 'approved')
    const totalSpent = txs.reduce((s, t) => s + t.amount, 0)
    const avgTx = txs.length > 0 ? totalSpent / txs.length : 0
    return { totalSpent, count: txs.length, avgTx }
  }, [state.transactions])

  // Spending per agent for the bar chart
  const agentSpending = useMemo(() => {
    const map: Record<string, number> = {}
    for (const tx of state.transactions) {
      if (tx.status !== 'approved') continue
      map[tx.agentId] = (map[tx.agentId] ?? 0) + tx.amount
    }
    return AGENTS.map(a => ({
      id: a.id,
      name: a.name,
      spent: map[a.id] ?? 0,
      color: AGENT_COLORS[a.id],
    }))
  }, [state.transactions])

  const maxSpend = Math.max(...agentSpending.map(a => a.spent), 1)

  // Cumulative spending timeline
  const timeline = useMemo(() => {
    const txs = state.transactions
      .filter(t => t.status === 'approved')
      .sort((a, b) => a.timestamp - b.timestamp)
    if (txs.length === 0) return []
    let cumulative = 0
    return txs.map(t => {
      cumulative += t.amount
      return { timestamp: t.timestamp, cumulative, description: t.description, agentId: t.agentId, amount: t.amount }
    })
  }, [state.transactions])

  const maxCumulative = timeline.length > 0 ? timeline[timeline.length - 1].cumulative : 1

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Overlay */}
          <motion.div
            key="overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 1000,
              background: 'rgba(0,0,0,0.6)',
              backdropFilter: 'blur(6px)',
              WebkitBackdropFilter: 'blur(6px)',
            }}
          />

          {/* Modal */}
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 1001,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '24px',
              pointerEvents: 'none',
            }}
          >
            <div
              style={{
                width: '80vw',
                maxWidth: 900,
                maxHeight: '85vh',
                overflowY: 'auto',
                background: 'rgba(10,14,28,0.95)',
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                border: `1px solid ${ACCENT},0.25)`,
                borderRadius: 12,
                boxShadow: `0 0 60px ${ACCENT},0.1), 0 20px 60px rgba(0,0,0,0.5)`,
                padding: 32,
                pointerEvents: 'all',
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28 }}>
                <div>
                  <div style={{ fontFamily: "'Orbitron', sans-serif", fontWeight: 700, fontSize: 22, color: '#ffffff', letterSpacing: '0.05em', marginBottom: 6 }}>
                    STRIPE SUMMARY
                  </div>
                  <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 13, color: '#8B95A5' }}>
                    {state.mission || 'Transaction overview'}
                  </div>
                </div>
                <button
                  onClick={onClose}
                  style={{ ...BTN_BASE, background: 'none', color: '#6B7A8A', fontSize: 20, lineHeight: 1, padding: '4px 8px', borderRadius: 4 }}
                  onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = '#ffffff' }}
                  onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = '#6B7A8A' }}
                >
                  ✕
                </button>
              </div>

              {/* Stat cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }}>
                {[
                  { label: 'TOTAL SPENT', value: `$${stats.totalSpent.toLocaleString()}` },
                  { label: 'TRANSACTIONS', value: String(stats.count) },
                  { label: 'AVG TRANSACTION', value: `$${stats.avgTx.toFixed(0)}` },
                  { label: 'REMAINING', value: `$${(state.totalBudget - state.spentBudget).toLocaleString()}` },
                ].map((card) => (
                  <div
                    key={card.label}
                    style={{
                      background: `${ACCENT},0.08)`,
                      border: `1px solid ${ACCENT},0.15)`,
                      borderRadius: 8,
                      padding: 16,
                    }}
                  >
                    <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 9, color: '#8B95A5', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: 8 }}>
                      {card.label}
                    </div>
                    <div style={{ fontFamily: "'VT323', monospace", fontSize: 32, color: '#ffffff', lineHeight: 1 }}>
                      {card.value}
                    </div>
                  </div>
                ))}
              </div>

              {/* Spending by agent — horizontal bar chart */}
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 10, color: '#8B95A5', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: 12 }}>
                  SPENDING BY AGENT
                </div>
                <div
                  style={{
                    background: 'rgba(20,25,45,0.5)',
                    border: `1px solid ${ACCENT},0.12)`,
                    borderRadius: 8,
                    padding: '20px 24px',
                  }}
                >
                  {agentSpending.map((agent) => (
                    <div key={agent.id} style={{ marginBottom: 14 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6 }}>
                        <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 10, color: agent.color, letterSpacing: '0.1em' }}>
                          {agent.name}
                        </span>
                        <span style={{ fontFamily: "'VT323', monospace", fontSize: 18, color: '#ffffff' }}>
                          ${agent.spent.toLocaleString()}
                        </span>
                      </div>
                      {/* Bar */}
                      <div style={{ height: 6, background: 'rgba(255,255,255,0.04)', borderRadius: 3, overflow: 'hidden' }}>
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${(agent.spent / maxSpend) * 100}%` }}
                          transition={{ duration: 0.8, ease: 'easeOut' }}
                          style={{
                            height: '100%',
                            background: `linear-gradient(90deg, ${agent.color}cc, ${agent.color})`,
                            borderRadius: 3,
                            boxShadow: `0 0 8px ${agent.color}55`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cumulative spend chart */}
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 10, color: '#8B95A5', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: 12 }}>
                  CUMULATIVE SPEND
                </div>
                <div
                  style={{
                    background: 'rgba(20,25,45,0.5)',
                    border: `1px solid ${ACCENT},0.12)`,
                    borderRadius: 8,
                    padding: '20px 24px',
                    height: 180,
                    position: 'relative',
                  }}
                >
                  {timeline.length === 0 ? (
                    <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 13, color: '#4A5568' }}>
                        No transactions recorded yet
                      </span>
                    </div>
                  ) : (
                    <>
                      {/* Y-axis labels */}
                      <div style={{ position: 'absolute', left: 0, top: 20, bottom: 28, width: 50, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                        <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 9, color: '#4A5568' }}>${maxCumulative.toLocaleString()}</span>
                        <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 9, color: '#4A5568' }}>$0</span>
                      </div>

                      {/* Chart area */}
                      <div style={{ marginLeft: 54, height: '100%', position: 'relative', display: 'flex', alignItems: 'flex-end', gap: 2 }}>
                        {/* Grid lines */}
                        {[0.25, 0.5, 0.75].map(pct => (
                          <div
                            key={pct}
                            style={{
                              position: 'absolute',
                              left: 0,
                              right: 0,
                              bottom: `${pct * 100}%`,
                              borderBottom: '1px dashed rgba(100,200,255,0.06)',
                            }}
                          />
                        ))}

                        {/* Bars */}
                        {timeline.map((point, i) => {
                          const heightPct = (point.cumulative / maxCumulative) * 100
                          const barColor = AGENT_COLORS[point.agentId as AgentId] ?? '#8b5cf6'
                          return (
                            <div
                              key={i}
                              title={`${point.description}: $${point.amount} (total: $${point.cumulative})`}
                              style={{
                                flex: 1,
                                maxWidth: 40,
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'flex-end',
                                height: '85%',
                              }}
                            >
                              <motion.div
                                initial={{ height: 0 }}
                                animate={{ height: `${heightPct}%` }}
                                transition={{ duration: 0.6, delay: i * 0.08 }}
                                style={{
                                  background: `linear-gradient(180deg, ${barColor}, ${barColor}88)`,
                                  borderRadius: '2px 2px 0 0',
                                  minHeight: 3,
                                  boxShadow: `0 0 6px ${barColor}44`,
                                }}
                              />
                              {/* Label */}
                              <div style={{
                                fontFamily: "'Share Tech Mono', monospace",
                                fontSize: 8,
                                color: '#4A5568',
                                textAlign: 'center',
                                marginTop: 4,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}>
                                #{i + 1}
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Transaction list */}
              <div style={{ marginBottom: 28 }}>
                <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 10, color: '#8B95A5', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: 12 }}>
                  TRANSACTIONS ({state.transactions.length})
                </div>
                {state.transactions.length === 0 ? (
                  <div
                    style={{
                      background: 'rgba(20,25,45,0.4)',
                      border: `1px solid ${ACCENT},0.1)`,
                      borderRadius: 8,
                      padding: 24,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 13, color: '#4A5568' }}>
                      No transactions yet — waiting for agent proposals
                    </span>
                  </div>
                ) : (
                  <div
                    style={{
                      background: 'rgba(20,25,45,0.4)',
                      border: `1px solid ${ACCENT},0.1)`,
                      borderRadius: 8,
                      overflow: 'hidden',
                    }}
                  >
                    {/* Table header */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '80px 1fr 90px 80px',
                      gap: 8,
                      padding: '10px 16px',
                      borderBottom: `1px solid ${ACCENT},0.08)`,
                    }}>
                      {['AGENT', 'DESCRIPTION', 'AMOUNT', 'STATUS'].map(h => (
                        <span key={h} style={{ fontFamily: "'Space Mono', monospace", fontSize: 8, color: '#4A5568', letterSpacing: '0.15em' }}>
                          {h}
                        </span>
                      ))}
                    </div>

                    {/* Rows */}
                    {state.transactions.map((tx) => {
                      const agentDef = AGENTS.find(a => a.id === tx.agentId)
                      const color = AGENT_COLORS[tx.agentId] ?? '#8b5cf6'
                      return (
                        <div
                          key={tx.id}
                          style={{
                            display: 'grid',
                            gridTemplateColumns: '80px 1fr 90px 80px',
                            gap: 8,
                            padding: '10px 16px',
                            borderBottom: '1px solid rgba(100,200,255,0.03)',
                            transition: 'background 0.15s',
                          }}
                          onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.background = 'rgba(139,92,246,0.04)' }}
                          onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.background = 'transparent' }}
                        >
                          {/* Agent */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <div style={{ width: 6, height: 6, borderRadius: '50%', background: color, boxShadow: `0 0 6px ${color}88`, flexShrink: 0 }} />
                            <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 9, color: color, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                              {agentDef?.name.split(' ')[0] ?? tx.agentId}
                            </span>
                          </div>
                          {/* Description */}
                          <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 12, color: '#C0C8D4', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {tx.description}
                          </span>
                          {/* Amount */}
                          <span style={{ fontFamily: "'VT323', monospace", fontSize: 18, color: '#ffffff', textAlign: 'right' }}>
                            ${tx.amount.toLocaleString()}
                          </span>
                          {/* Status */}
                          <span style={{
                            fontFamily: "'Space Mono', monospace",
                            fontSize: 9,
                            letterSpacing: '0.1em',
                            color: tx.status === 'approved' ? '#34d399' : tx.status === 'blocked' ? '#fb7185' : '#f59e0b',
                            textAlign: 'right',
                            textTransform: 'uppercase',
                          }}>
                            {tx.status}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>

              {/* Budget bar at bottom */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 9, color: '#6B7A8A', letterSpacing: '0.1em' }}>BUDGET UTILIZATION</span>
                  <span style={{ fontFamily: "'VT323', monospace", fontSize: 16, color: '#ffffff' }}>
                    {state.totalBudget > 0 ? Math.round((state.spentBudget / state.totalBudget) * 100) : 0}%
                  </span>
                </div>
                <div style={{ height: 8, background: 'rgba(255,255,255,0.04)', borderRadius: 4, overflow: 'hidden' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${state.totalBudget > 0 ? (state.spentBudget / state.totalBudget) * 100 : 0}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                    style={{
                      height: '100%',
                      background: state.dangerMode
                        ? 'linear-gradient(90deg, #ef4444, #f97316)'
                        : 'linear-gradient(90deg, #8b5cf6, #a78bfa)',
                      borderRadius: 4,
                      boxShadow: state.dangerMode
                        ? '0 0 12px rgba(239,68,68,0.4)'
                        : '0 0 12px rgba(139,92,246,0.3)',
                    }}
                  />
                </div>
              </div>

              {/* Footer */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                <button
                  onClick={onClose}
                  style={{
                    ...BTN_BASE,
                    background: 'none',
                    color: '#6B7A8A',
                    padding: '4px 0',
                    textDecoration: 'underline',
                    textUnderlineOffset: 3,
                  }}
                  onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = '#ffffff' }}
                  onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = '#6B7A8A' }}
                >
                  CLOSE
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
