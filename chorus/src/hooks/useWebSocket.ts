import { useEffect, useRef, useState, useCallback } from 'react'
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
    setPendingApproval,
    resolveApproval,
    setOpsRound,
  } = useSimulation()

  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)

  // Track whether simulation already finished so we don't reconnect on remount
  const alreadyComplete = state.stage === 'complete'

  const sendDecision = useCallback((approved: boolean, reason?: string) => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'decision', approved, reason: reason ?? '' }))
    }
  }, [])

  const stopSimulation = useCallback(() => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'stop_simulation' }))
    }
  }, [])

  useEffect(() => {
    if (!url || alreadyComplete) return

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
          case 'approval_required': {
            setPendingApproval({
              proposalId: data.proposalId as string,
              title: data.title as string,
              cost: data.cost as number,
              description: data.description as string,
              agentId: data.agentId as AgentId,
              agentName: data.agentName as string,
              timestamp: Date.now(),
            })
            addActivity({ agentId: data.agentId as AgentId, message: `PROPOSAL: ${data.title} — $${data.cost}`, timestamp: Date.now(), type: 'action' })
            break
          }
          case 'approval_resolved': {
            resolveApproval(data.proposalId as string, data.approved as boolean)
            const status = data.approved ? 'APPROVED' : 'REJECTED'
            addActivity({ agentId: 'finance' as AgentId, message: `CEO ${status}: ${data.proposalId}`, timestamp: Date.now(), type: data.approved ? 'action' : 'block' })
            break
          }
          case 'ops_round': {
            setOpsRound(data.round as number)
            addActivity({ agentId: 'product' as AgentId, message: `Operations Week ${data.round} — ${data.label}`, timestamp: Date.now(), type: 'thought' })
            break
          }
          case 'set_running': {
            setRunning(data.running as boolean)
            break
          }
          case 'simulation_complete': {
            setRunning(false)
            const status = data.status as string
            const spent = data.totalSpent as number
            const remaining = data.remaining as number
            const conclusion = status === 'failed'
              ? `SIMULATION FAILED — $${spent.toLocaleString()} spent, $${remaining.toLocaleString()} remaining. Budget exhausted before completion.`
              : `SIMULATION COMPLETE — All phases finished. $${spent.toLocaleString()} spent, $${remaining.toLocaleString()} remaining.`
            addActivity({ agentId: 'product' as AgentId, message: conclusion, timestamp: Date.now(), type: 'conclusion' })
            break
          }
          case 'audio_narration': {
            window.dispatchEvent(new CustomEvent('sim-audio', { detail: data }))
            break
          }
          case 'error': {
            const errorMsg = data.message as string || 'Unknown error'
            addActivity({ agentId: (data.agentId as AgentId) || 'finance', message: `ERROR: ${errorMsg}`, timestamp: Date.now(), type: 'block' })
            if (data.fatal) {
              setRunning(false)
              setStage('complete')
            }
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

  return { connected, sendDecision, stopSimulation }
}
