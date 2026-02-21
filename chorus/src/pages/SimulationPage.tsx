import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSimulation } from '../context/SimulationContext'
import { useMockSimulation } from '../hooks/useMockSimulation'
import { useWebSocket } from '../hooks/useWebSocket'
import { AgentStage } from '../components/simulation/AgentStage'
import { ActivityFeed } from '../components/simulation/ActivityFeed'
import { BudgetBar } from '../components/simulation/BudgetBar'
import { StatusBar } from '../components/simulation/StatusBar'
import Prism from '../components/simulation/Prism/Prism'

const WS_URL: string | null = null

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
  const { connected } = useWebSocket(WS_URL)

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
        minHeight: '100vh',
        background: '#05050a',
        position: 'relative',
      }}
    >
      <PrismBackground danger={state.dangerMode} />

      {/* Status bar */}
      <div className="sticky top-0 z-20">
        <StatusBar />
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

      {/* Budget bar */}
      <div className="flex-shrink-0" style={{ position: 'relative', zIndex: 1 }}>
        <BudgetBar />
      </div>
    </div>
  )
}
