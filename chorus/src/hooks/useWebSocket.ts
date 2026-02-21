import { useEffect, useRef, useState } from 'react'
import { useSimulation } from '../context/SimulationContext'
import { type AgentId, type SimulationStage } from '../types'

interface WSEvent {
  type: string
  [key: string]: unknown
}

export function useWebSocket(url: string | null) {
  const {
    state,
    setAgentStatus,
    setAgentThought,
    clearAgentThought,
    addActivity,
    addTransaction,
    updateBudget,
    setStage,
    setRunning,
  } = useSimulation()

  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    if (!url) return

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      setRunning(true)
      ws.send(JSON.stringify({
        idea: state.mission,
        budget: state.totalBudget,
      }))
    }
    ws.onclose = () => {
      setConnected(false)
      setRunning(false)
    }
    ws.onerror = () => setConnected(false)

    ws.onmessage = (event) => {
      try {
        const data: WSEvent = JSON.parse(event.data as string)

        switch (data.type) {
          case 'agent_thinking': {
            const agentId = data.agentId as AgentId
            const fragments = data.fragments as string[]
            setAgentStatus(agentId, 'thinking')
            setAgentThought(agentId, fragments)
            addActivity({ agentId, message: fragments[fragments.length - 1] ?? '', timestamp: Date.now(), type: 'thought' })
            break
          }
          case 'agent_acting': {
            const agentId = data.agentId as AgentId
            setAgentStatus(agentId, 'acting')
            clearAgentThought(agentId)
            addActivity({ agentId, message: data.action as string, timestamp: Date.now(), type: 'action' })
            break
          }
          case 'agent_complete': {
            const agentId = data.agentId as AgentId
            setAgentStatus(agentId, 'complete')
            clearAgentThought(agentId)
            addActivity({ agentId, message: data.summary as string, timestamp: Date.now(), type: 'complete' })
            break
          }
          case 'transaction': {
            addTransaction({
              agentId: data.agentId as AgentId,
              description: data.description as string,
              amount: data.amount as number,
              status: data.status as 'approved' | 'blocked',
              timestamp: Date.now(),
            })
            break
          }
          case 'budget_update': {
            updateBudget(data.spent as number, data.total as number | undefined)
            break
          }
          case 'stage_change': {
            setStage(data.stage as SimulationStage)
            break
          }
        }
      } catch {
        // non-JSON message, ignore
      }
    }

    return () => {
      ws.close()
    }
  }, [url]) // eslint-disable-line react-hooks/exhaustive-deps

  return { connected }
}
