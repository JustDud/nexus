import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSimulation } from '../context/SimulationContext'
import { useMockSimulation } from '../hooks/useMockSimulation'
import { useWebSocket } from '../hooks/useWebSocket'
import { AgentStage } from '../components/simulation/AgentStage'
import { ActivityFeed } from '../components/simulation/ActivityFeed'
import { BudgetBar } from '../components/simulation/BudgetBar'
import { StatusBar } from '../components/simulation/StatusBar'
import { ApprovalDialog } from '../components/simulation/ApprovalDialog'
import { StripeModal } from '../components/simulation/StripeModal'
import { useAudioPlayer } from '../hooks/useAudioPlayer'
import Prism from '../components/simulation/Prism/Prism'

// Change this to your backend WS URL, or null to always use mock
const WS_URL: string | null = `ws://${window.location.host}/ws/simulation`

/* ── Corner accent for buttons ─────────────────────────────────────── */
function BtnCorner({ pos, color }: { pos: 'tl' | 'tr' | 'bl' | 'br'; color: string }) {
  const top  = pos === 'tl' || pos === 'tr'
  const left = pos === 'tl' || pos === 'bl'
  return (
    <div
      style={{
        position: 'absolute',
        width: 10,
        height: 10,
        top:    top  ? 5 : undefined,
        bottom: !top ? 5 : undefined,
        left:   left  ? 5 : undefined,
        right:  !left ? 5 : undefined,
        borderTop:    top    ? `1px solid ${color}` : undefined,
        borderBottom: !top   ? `1px solid ${color}` : undefined,
        borderLeft:   left   ? `1px solid ${color}` : undefined,
        borderRight:  !left  ? `1px solid ${color}` : undefined,
        pointerEvents: 'none',
      }}
    />
  )
}

function PrismBackground({ danger }: { danger: boolean }) {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
      {/* Prism WebGL layer */}
      <div style={{ position: 'absolute', inset: 0 }}>
        <Prism
          animationType="rotate"
          timeScale={0.3}
          height={3.5}
          baseWidth={5.5}
          scale={3.6}
          hueShift={0}
          colorFrequency={1}
          noise={0.3}
          glow={0.6}
          bloom={0.5}
          transparent={true}
        />
      </div>

      {/* Dark overlay — keeps content legible */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: danger
            ? 'rgba(4,2,10,0.72)'
            : 'rgba(5,3,12,0.76)',
          transition: 'background 800ms ease',
        }}
      />

      {/* Grid overlay */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.012) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.012) 1px, transparent 1px)
          `,
          backgroundSize: '32px 32px',
        }}
      />
    </div>
  )
}

export function SimulationPage() {
  const { state, tickElapsed } = useSimulation()
  const navigate = useNavigate()
  const { connected, sendDecision, stopSimulation } = useWebSocket(WS_URL)
  const { isMuted, setIsMuted, isPlaying, stopAll } = useAudioPlayer()
  const [stripeOpen, setStripeOpen] = useState(false)

  useEffect(() => {
    if (!state.mission) navigate('/')
  }, [state.mission, navigate])

  useMockSimulation(!connected)

  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null)
  useEffect(() => {
    if (!state.isRunning) return
    tickRef.current = setInterval(tickElapsed, 1000)
    return () => { if (tickRef.current) clearInterval(tickRef.current) }
  }, [state.isRunning, tickElapsed])

  return (
    <div
      className="flex flex-col"
      data-danger={String(state.dangerMode)}
      style={{
        height: '100vh',
        overflow: 'hidden',
        background: '#05050a',
        position: 'relative',
      }}
    >
      <PrismBackground danger={state.dangerMode} />

      {/* Status bar */}
      <div className="sticky top-0 z-20">
        <StatusBar
          isMuted={isMuted}
          onToggleMute={() => setIsMuted(!isMuted)}
          onStop={() => { stopAll(); stopSimulation(); navigate('/') }}
        />
      </div>

      {/* Main */}
      <div className="flex flex-1 overflow-hidden" style={{ minHeight: 0, position: 'relative', zIndex: 1 }}>
        <div className="flex-1 p-4 overflow-hidden" style={{ minHeight: 0 }}>
          <AgentStage />
        </div>
        <div className="w-[360px] flex-shrink-0 p-4 pl-0 overflow-hidden" style={{ minHeight: 0 }}>
          <ActivityFeed />
        </div>
      </div>

      {/* Action buttons row — mirrors main flex layout so buttons align with card grid */}
      <div
        className="flex-shrink-0"
        style={{ position: 'relative', zIndex: 1, display: 'flex' }}
      >
        {/* Flex-1 container matches the card area width exactly */}
        <div
          className="flex-1"
          style={{
            display: 'flex',
            gap: 16,
            padding: '10px 16px',
            borderTop: '1px solid rgba(100, 200, 255, 0.06)',
          }}
        >
          {/* Stripe Summary */}
          <button
            className="nexus-btn"
            onClick={() => setStripeOpen(true)}
            style={{
              flex: 1,
              position: 'relative',
              overflow: 'hidden',
              padding: '18px 32px',
              fontFamily: "'Space Mono', monospace",
              fontSize: 14,
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              color: '#C4B5FD',
              background: 'rgba(99, 91, 255, 0.06)',
              border: '1px solid rgba(139, 92, 246, 0.2)',
              borderRadius: 0,
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)',
              textAlign: 'center',
            }}
            onMouseEnter={e => {
              const el = e.currentTarget
              el.style.background   = 'rgba(99, 91, 255, 0.14)'
              el.style.borderColor  = 'rgba(139, 92, 246, 0.5)'
              el.style.boxShadow    = '0 0 30px rgba(139, 92, 246, 0.1), inset 0 0 30px rgba(139, 92, 246, 0.05)'
              el.style.color        = '#DDD6FE'
            }}
            onMouseLeave={e => {
              const el = e.currentTarget
              el.style.background   = 'rgba(99, 91, 255, 0.06)'
              el.style.borderColor  = 'rgba(139, 92, 246, 0.2)'
              el.style.boxShadow    = 'none'
              el.style.color        = '#C4B5FD'
            }}
          >
            <BtnCorner pos="tl" color="rgba(139,92,246,0.55)" />
            <BtnCorner pos="tr" color="rgba(139,92,246,0.55)" />
            <BtnCorner pos="bl" color="rgba(139,92,246,0.55)" />
            <BtnCorner pos="br" color="rgba(139,92,246,0.55)" />
            STRIPE SUMMARY
          </button>

          {/* Project Summary */}
          <button
            className="nexus-btn"
            onClick={() => navigate('/summary')}
            style={{
              flex: 1,
              position: 'relative',
              overflow: 'hidden',
              padding: '18px 32px',
              fontFamily: "'Space Mono', monospace",
              fontSize: 14,
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              color: '#7DD3FC',
              background: 'rgba(56, 189, 248, 0.06)',
              border: '1px solid rgba(56, 189, 248, 0.2)',
              borderRadius: 0,
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)',
              textAlign: 'center',
            }}
            onMouseEnter={e => {
              const el = e.currentTarget
              el.style.background   = 'rgba(56, 189, 248, 0.14)'
              el.style.borderColor  = 'rgba(56, 189, 248, 0.5)'
              el.style.boxShadow    = '0 0 30px rgba(56, 189, 248, 0.1), inset 0 0 30px rgba(56, 189, 248, 0.05)'
              el.style.color        = '#BAE6FD'
            }}
            onMouseLeave={e => {
              const el = e.currentTarget
              el.style.background   = 'rgba(56, 189, 248, 0.06)'
              el.style.borderColor  = 'rgba(56, 189, 248, 0.2)'
              el.style.boxShadow    = 'none'
              el.style.color        = '#7DD3FC'
            }}
          >
            <BtnCorner pos="tl" color="rgba(56,189,248,0.55)" />
            <BtnCorner pos="tr" color="rgba(56,189,248,0.55)" />
            <BtnCorner pos="bl" color="rgba(56,189,248,0.55)" />
            <BtnCorner pos="br" color="rgba(56,189,248,0.55)" />
            PROJECT SUMMARY →
          </button>
        </div>

        {/* Spacer — matches ActivityFeed column width so buttons don't bleed under it */}
        <div style={{ width: 360, flexShrink: 0 }} />
      </div>

      {/* Budget bar */}
      <div className="flex-shrink-0" style={{ position: 'relative', zIndex: 1 }}>
        <BudgetBar />
      </div>

      <ApprovalDialog onDecide={sendDecision} />
      <StripeModal open={stripeOpen} onClose={() => setStripeOpen(false)} />
    </div>
  )
}
