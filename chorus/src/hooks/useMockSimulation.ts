import { useEffect, useRef } from 'react'
import { useSimulation } from '../context/SimulationContext'
import { type AgentId } from '../types'

interface SimEvent {
  at: number // seconds from start
  fn: () => void
}

export function useMockSimulation(enabled: boolean) {
  const {
    state,
    setStage,
    setRunning,
    setAgentStatus,
    setAgentThought,
    clearAgentThought,
    addActivity,
    addTransaction,
  } = useSimulation()

  const startedRef = useRef(false)
  const timerRef   = useRef<ReturnType<typeof setInterval> | null>(null)
  const elapsed    = useRef(0)
  const eventsRef  = useRef<SimEvent[]>([])

  useEffect(() => {
    if (!enabled || startedRef.current) return
    startedRef.current = true

    eventsRef.current = [
      // ── t=1: research stage begins, PRODUCT starts thinking ──────
      {
        at: 1,
        fn: () => {
          setStage('researching')
          setAgentStatus('product', 'thinking')
          setAgentThought('product', ['loading market intelligence...'])
        },
      },

      // ── t=2: TECH starts thinking ─────────────────────────────────
      {
        at: 2,
        fn: () => {
          setAgentStatus('tech', 'thinking')
          setAgentThought('tech', ['scanning tech requirements...'])
        },
      },

      // ── t=3: PRODUCT first activity ──────────────────────────────
      {
        at: 3,
        fn: () => {
          addActivity({
            agentId: 'product',
            message: 'Pulling market data from SEMrush...',
            timestamp: Date.now(),
            type: 'thought',
          })
        },
      },

      // ── t=4: TECH first activity ──────────────────────────────────
      {
        at: 4,
        fn: () => {
          addActivity({
            agentId: 'tech',
            message: 'Evaluating stack: React + FastAPI',
            timestamp: Date.now(),
            type: 'thought',
          })
        },
      },

      // ── t=5: PRODUCT research transaction ────────────────────────
      {
        at: 5,
        fn: () => {
          addTransaction({
            agentId: 'product',
            description: 'Market research tool (SEMrush)',
            amount: 40,
            status: 'approved',
            timestamp: Date.now(),
          })
          addActivity({
            agentId: 'product',
            message: '✓ Research tool purchased — $40',
            timestamp: Date.now(),
            type: 'action',
          })
        },
      },

      // ── t=6: OPS starts thinking ──────────────────────────────────
      {
        at: 6,
        fn: () => {
          setAgentStatus('ops', 'thinking')
          setAgentThought('ops', ['GDPR compliance scan...'])
        },
      },

      // ── t=8: FINANCE starts thinking ─────────────────────────────
      {
        at: 8,
        fn: () => {
          setAgentStatus('finance', 'thinking')
          setAgentThought('finance', [`total budget: $${state.totalBudget}`])
        },
      },

      // ── t=10: TECH domain transaction ────────────────────────────
      {
        at: 10,
        fn: () => {
          addTransaction({
            agentId: 'tech',
            description: 'Domain registration',
            amount: 12,
            status: 'approved',
            timestamp: Date.now(),
          })
          addActivity({
            agentId: 'tech',
            message: '✓ Domain registered — $12',
            timestamp: Date.now(),
            type: 'action',
          })
        },
      },

      // ── t=12: PRODUCT → acting ───────────────────────────────────
      {
        at: 12,
        fn: () => {
          setAgentStatus('product', 'acting')
          clearAgentThought('product')
          addActivity({
            agentId: 'product',
            message: 'Market analysis complete — TAM $4.2B confirmed',
            timestamp: Date.now(),
            type: 'action',
          })
        },
      },

      // ── t=15: TECH → acting ───────────────────────────────────────
      {
        at: 15,
        fn: () => {
          setAgentStatus('tech', 'acting')
          clearAgentThought('tech')
          addActivity({
            agentId: 'tech',
            message: 'Tech stack decided — deploying infra',
            timestamp: Date.now(),
            type: 'action',
          })
        },
      },

      // ── t=18: OPS legal transaction ───────────────────────────────
      {
        at: 18,
        fn: () => {
          addTransaction({
            agentId: 'ops',
            description: 'Legal docs + compliance setup',
            amount: 80,
            status: 'approved',
            timestamp: Date.now(),
          })
          addActivity({
            agentId: 'ops',
            message: '✓ Legal documents downloaded — $80',
            timestamp: Date.now(),
            type: 'action',
          })
        },
      },

      // ── t=20: OPS → complete ──────────────────────────────────────
      {
        at: 20,
        fn: () => {
          setAgentStatus('ops', 'complete')
          clearAgentThought('ops')
          addActivity({
            agentId: 'ops',
            message: 'All ops systems operational ✓',
            timestamp: Date.now(),
            type: 'complete',
          })
        },
      },

      // ── t=22: PRODUCT → complete ──────────────────────────────────
      {
        at: 22,
        fn: () => {
          setAgentStatus('product', 'complete')
          clearAgentThought('product')
          addActivity({
            agentId: 'product',
            message: 'Launch complete — ads live, TAM $4.2B',
            timestamp: Date.now(),
            type: 'complete',
          })
        },
      },

      // ── t=25: TECH → complete ─────────────────────────────────────
      {
        at: 25,
        fn: () => {
          setAgentStatus('tech', 'complete')
          clearAgentThought('tech')
          addActivity({
            agentId: 'tech',
            message: 'App deployed — app.startup.dev is live',
            timestamp: Date.now(),
            type: 'complete',
          })
        },
      },

      // ── t=28: PRODUCT ads transaction ────────────────────────────
      {
        at: 28,
        fn: () => {
          addTransaction({
            agentId: 'product',
            description: 'Instagram + Google ad campaign',
            amount: 150,
            status: 'approved',
            timestamp: Date.now(),
          })
          addActivity({
            agentId: 'product',
            message: '✓ Ad campaign live — $150',
            timestamp: Date.now(),
            type: 'action',
          })
        },
      },

      // ── t=30: FINANCE → complete ──────────────────────────────────
      {
        at: 30,
        fn: () => {
          setAgentStatus('finance', 'complete')
          clearAgentThought('finance')
          addActivity({
            agentId: 'finance',
            message: 'Budget audit complete — $326 remaining',
            timestamp: Date.now(),
            type: 'complete',
          })
        },
      },

      // ── t=35: advance to PLANNING stage ──────────────────────────
      {
        at: 35,
        fn: () => {
          setStage('planning')
          addActivity({
            agentId: 'product' as AgentId,
            message: 'Entering planning phase — sprint 2',
            timestamp: Date.now(),
            type: 'thought',
          })
        },
      },

      // ── t=40: dangerMode demo — big infra spend ───────────────────
      {
        at: 40,
        fn: () => {
          addTransaction({
            agentId: 'finance' as AgentId,
            description: 'Infrastructure scaling (emergency)',
            amount: 500,
            status: 'approved',
            timestamp: Date.now(),
          })
          addActivity({
            agentId: 'finance' as AgentId,
            message: '⚠ Emergency infra spend — $500',
            timestamp: Date.now(),
            type: 'block',
          })
        },
      },
    ]

    setRunning(true)

    timerRef.current = setInterval(() => {
      elapsed.current += 1

      const due = eventsRef.current.filter((e) => e.at === elapsed.current)
      due.forEach((e) => e.fn())

      if (elapsed.current >= 45) {
        if (timerRef.current) clearInterval(timerRef.current)
        setRunning(false)
      }
    }, 1000)

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [enabled]) // eslint-disable-line react-hooks/exhaustive-deps
}
