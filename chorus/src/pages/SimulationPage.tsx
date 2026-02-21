import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSimulation } from '../context/SimulationContext'
import { useMockSimulation } from '../hooks/useMockSimulation'
import { useWebSocket } from '../hooks/useWebSocket'
import { AgentStage } from '../components/simulation/AgentStage'
import { ActivityFeed } from '../components/simulation/ActivityFeed'
import { BudgetBar } from '../components/simulation/BudgetBar'
import { StatusBar } from '../components/simulation/StatusBar'

// Change this to your backend WS URL, or null to always use mock
const WS_URL: string | null = `ws://${window.location.host}/ws/simulation`

export function SimulationPage() {
  const { state, tickElapsed } = useSimulation()
  const navigate = useNavigate()
  const { connected } = useWebSocket(WS_URL)

  // Redirect if no mission set
  useEffect(() => {
    if (!state.mission) {
      navigate('/')
    }
  }, [state.mission, navigate])

  // Use mock simulation when WS not connected
  useMockSimulation(!connected)

  // Clock tick
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null)
  useEffect(() => {
    if (!state.isRunning) return
    tickRef.current = setInterval(tickElapsed, 1000)
    return () => { if (tickRef.current) clearInterval(tickRef.current) }
  }, [state.isRunning, tickElapsed])

  return (
    <div
      className="flex flex-col min-h-screen"
      data-danger={String(state.dangerMode)}
      style={{
        background: state.dangerMode
          ? 'linear-gradient(180deg, rgba(239,68,68,0.04) 0%, #080810 100%)'
          : '#080810',
        transition: 'background 800ms ease',
      }}
    >
      {/* Status bar — sticky top */}
      <div className="sticky top-0 z-20">
        <StatusBar />
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden" style={{ minHeight: 0 }}>
        {/* Agent stage — 65% */}
        <div className="flex-1 p-4 overflow-hidden" style={{ minHeight: 0 }}>
          <AgentStage />
        </div>

        {/* Activity feed — 35% */}
        <div className="w-[340px] flex-shrink-0 p-4 overflow-hidden" style={{ minHeight: 0 }}>
          <ActivityFeed />
        </div>
      </div>

      {/* Budget bar — sticky bottom */}
      <div className="flex-shrink-0 p-4 pt-0">
        <BudgetBar />
      </div>
    </div>
  )
}
