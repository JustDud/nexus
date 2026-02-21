import { motion, AnimatePresence } from 'framer-motion'

interface StripeModalProps {
  open: boolean
  onClose: () => void
}

const STAT_CARDS = [
  { label: 'TOTAL SPENT',       value: '$0.00' },
  { label: 'TRANSACTIONS',      value: '0'     },
  { label: 'AVG TRANSACTION',   value: '$0.00' },
]

const BTN_BASE: React.CSSProperties = {
  fontFamily: "'Space Mono', monospace",
  fontSize: 10,
  letterSpacing: '0.08em',
  cursor: 'pointer',
  border: 'none',
  transition: 'all 0.2s ease',
}

export function StripeModal({ open, onClose }: StripeModalProps) {
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
                border: '1px solid rgba(139,92,246,0.25)',
                borderRadius: 12,
                boxShadow: '0 0 60px rgba(139,92,246,0.1), 0 20px 60px rgba(0,0,0,0.5)',
                padding: 32,
                pointerEvents: 'all',
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28 }}>
                <div>
                  <div
                    style={{
                      fontFamily: "'Orbitron', sans-serif",
                      fontWeight: 700,
                      fontSize: 22,
                      color: '#ffffff',
                      letterSpacing: '0.05em',
                      marginBottom: 6,
                    }}
                  >
                    ⚡ STRIPE SUMMARY
                  </div>
                  <div
                    style={{
                      fontFamily: "'Share Tech Mono', monospace",
                      fontSize: 13,
                      color: '#8B95A5',
                    }}
                  >
                    Transaction overview for this project
                  </div>
                </div>
                <button
                  onClick={onClose}
                  style={{
                    ...BTN_BASE,
                    background: 'none',
                    color: '#6B7A8A',
                    fontSize: 20,
                    lineHeight: 1,
                    padding: '4px 8px',
                    borderRadius: 4,
                  }}
                  onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = '#ffffff' }}
                  onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = '#6B7A8A' }}
                >
                  ✕
                </button>
              </div>

              {/* Stat cards row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
                {STAT_CARDS.map((card) => (
                  <div
                    key={card.label}
                    style={{
                      background: 'rgba(139,92,246,0.08)',
                      border: '1px solid rgba(139,92,246,0.15)',
                      borderRadius: 8,
                      padding: 16,
                    }}
                  >
                    <div
                      style={{
                        fontFamily: "'Space Mono', monospace",
                        fontSize: 9,
                        color: '#8B95A5',
                        letterSpacing: '0.15em',
                        textTransform: 'uppercase',
                        marginBottom: 8,
                      }}
                    >
                      {card.label}
                    </div>
                    <div
                      style={{
                        fontFamily: "'VT323', monospace",
                        fontSize: 32,
                        color: '#ffffff',
                        lineHeight: 1,
                      }}
                    >
                      {card.value}
                    </div>
                  </div>
                ))}
              </div>

              {/* Chart placeholder */}
              <div
                style={{
                  height: 200,
                  background: 'rgba(20,25,45,0.5)',
                  border: '1px dashed rgba(139,92,246,0.2)',
                  borderRadius: 8,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 10,
                  marginBottom: 24,
                }}
              >
                <span style={{ fontSize: 28, opacity: 0.35 }}>📈</span>
                <span
                  style={{
                    fontFamily: "'Share Tech Mono', monospace",
                    fontSize: 13,
                    color: '#4A5568',
                    textAlign: 'center',
                  }}
                >
                  Chart will be available when Stripe is connected
                </span>
              </div>

              {/* Transaction list */}
              <div style={{ marginBottom: 28 }}>
                <div
                  style={{
                    fontFamily: "'Space Mono', monospace",
                    fontSize: 10,
                    color: '#8B95A5',
                    letterSpacing: '0.15em',
                    textTransform: 'uppercase',
                    marginBottom: 12,
                  }}
                >
                  RECENT TRANSACTIONS
                </div>
                <div
                  style={{
                    background: 'rgba(20,25,45,0.4)',
                    border: '1px solid rgba(139,92,246,0.1)',
                    borderRadius: 8,
                    padding: 24,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  <span style={{ fontSize: 24, opacity: 0.35 }}>📋</span>
                  <span
                    style={{
                      fontFamily: "'Share Tech Mono', monospace",
                      fontSize: 13,
                      color: '#4A5568',
                      textAlign: 'center',
                    }}
                  >
                    No transactions yet — connect Stripe to start tracking
                  </span>
                </div>
              </div>

              {/* Footer */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <button
                  style={{
                    ...BTN_BASE,
                    fontFamily: "'Space Mono', monospace",
                    fontSize: 10,
                    letterSpacing: '0.08em',
                    color: '#ffffff',
                    background: 'linear-gradient(135deg, rgba(99,91,255,0.4) 0%, rgba(139,92,246,0.4) 100%)',
                    border: '1px solid rgba(139,92,246,0.5)',
                    borderRadius: 6,
                    padding: '10px 20px',
                    opacity: 0.5,
                    cursor: 'not-allowed',
                  }}
                  disabled
                >
                  CONNECT STRIPE
                </button>
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
