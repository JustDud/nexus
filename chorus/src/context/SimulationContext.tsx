import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  type ReactNode,
} from 'react'
import {
  type SimulationState,
  type AgentId,
  type AgentStatus,
  type ActivityEntry,
  type Transaction,
  type SimulationStage,
  AGENTS,
} from '../types'
import { generateId } from '../lib/utils'

const initialAgents = AGENTS.map((def) => ({
  id: def.id,
  status: 'idle' as AgentStatus,
  currentThought: [] as string[],
  completedActions: [],
  totalSpent: 0,
}))

const initialState: SimulationState = {
  mission: '',
  fileContent: null,
  totalBudget: 1000,
  spentBudget: 0,
  dangerMode: false,
  stage: 'researching',
  elapsedSeconds: 0,
  agents: initialAgents,
  activityLog: [],
  transactions: [],
  isRunning: false,
}

type Action =
  | { type: 'SET_MISSION'; payload: { mission: string; budget: number; fileContent: string | null } }
  | { type: 'SET_STAGE'; payload: SimulationStage }
  | { type: 'SET_RUNNING'; payload: boolean }
  | { type: 'TICK_ELAPSED' }
  | { type: 'SET_AGENT_STATUS'; payload: { agentId: AgentId; status: AgentStatus } }
  | { type: 'SET_AGENT_THOUGHT'; payload: { agentId: AgentId; fragments: string[] } }
  | { type: 'CLEAR_AGENT_THOUGHT'; payload: AgentId }
  | { type: 'ADD_ACTIVITY'; payload: Omit<ActivityEntry, 'id'> }
  | { type: 'ADD_TRANSACTION'; payload: Omit<Transaction, 'id'> }
  | { type: 'UPDATE_BUDGET'; payload: { spent: number; total?: number } }
  | { type: 'RESET' }

function reducer(state: SimulationState, action: Action): SimulationState {
  switch (action.type) {
    case 'SET_MISSION':
      return {
        ...initialState,
        mission: action.payload.mission,
        totalBudget: action.payload.budget,
        fileContent: action.payload.fileContent,
        agents: initialAgents.map((a) => ({ ...a })),
      }

    case 'SET_STAGE':
      return { ...state, stage: action.payload }

    case 'SET_RUNNING':
      return { ...state, isRunning: action.payload }

    case 'TICK_ELAPSED':
      return { ...state, elapsedSeconds: state.elapsedSeconds + 1 }

    case 'SET_AGENT_STATUS':
      return {
        ...state,
        agents: state.agents.map((a) =>
          a.id === action.payload.agentId
            ? { ...a, status: action.payload.status }
            : a
        ),
      }

    case 'SET_AGENT_THOUGHT':
      return {
        ...state,
        agents: state.agents.map((a) =>
          a.id === action.payload.agentId
            ? { ...a, currentThought: action.payload.fragments }
            : a
        ),
      }

    case 'CLEAR_AGENT_THOUGHT':
      return {
        ...state,
        agents: state.agents.map((a) =>
          a.id === action.payload ? { ...a, currentThought: [] } : a
        ),
      }

    case 'ADD_ACTIVITY':
      return {
        ...state,
        activityLog: [
          ...state.activityLog,
          { ...action.payload, id: generateId() },
        ],
      }

    case 'ADD_TRANSACTION': {
      const tx: Transaction = { ...action.payload, id: generateId() }
      const spent =
        tx.status === 'approved' ? state.spentBudget + tx.amount : state.spentBudget
      const remaining = state.totalBudget - spent
      const dangerMode = remaining / state.totalBudget < 0.3
      return {
        ...state,
        spentBudget: spent,
        dangerMode,
        transactions: [...state.transactions, tx],
        agents: state.agents.map((a) =>
          a.id === tx.agentId && tx.status === 'approved'
            ? {
                ...a,
                totalSpent: a.totalSpent + tx.amount,
                completedActions: [
                  ...a.completedActions,
                  {
                    id: tx.id,
                    description: tx.description,
                    cost: tx.amount,
                    timestamp: tx.timestamp,
                    status: tx.status,
                  },
                ],
              }
            : a
        ),
      }
    }

    case 'UPDATE_BUDGET': {
      const spent = action.payload.spent
      const total = action.payload.total ?? state.totalBudget
      const remaining = total - spent
      return {
        ...state,
        spentBudget: spent,
        totalBudget: total,
        dangerMode: remaining / total < 0.3,
      }
    }

    case 'RESET':
      return { ...initialState }

    default:
      return state
  }
}

interface SimulationContextValue {
  state: SimulationState
  setMission: (mission: string, budget: number, fileContent: string | null) => void
  setStage: (stage: SimulationStage) => void
  setRunning: (running: boolean) => void
  tickElapsed: () => void
  setAgentStatus: (agentId: AgentId, status: AgentStatus) => void
  setAgentThought: (agentId: AgentId, fragments: string[]) => void
  clearAgentThought: (agentId: AgentId) => void
  addActivity: (entry: Omit<ActivityEntry, 'id'>) => void
  addTransaction: (tx: Omit<Transaction, 'id'>) => void
  updateBudget: (spent: number, total?: number) => void
  reset: () => void
}

const SimulationContext = createContext<SimulationContextValue | null>(null)

export function SimulationProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  const setMission = useCallback(
    (mission: string, budget: number, fileContent: string | null) =>
      dispatch({ type: 'SET_MISSION', payload: { mission, budget, fileContent } }),
    []
  )
  const setStage = useCallback(
    (stage: SimulationStage) => dispatch({ type: 'SET_STAGE', payload: stage }),
    []
  )
  const setRunning = useCallback(
    (running: boolean) => dispatch({ type: 'SET_RUNNING', payload: running }),
    []
  )
  const tickElapsed = useCallback(() => dispatch({ type: 'TICK_ELAPSED' }), [])
  const setAgentStatus = useCallback(
    (agentId: AgentId, status: AgentStatus) =>
      dispatch({ type: 'SET_AGENT_STATUS', payload: { agentId, status } }),
    []
  )
  const setAgentThought = useCallback(
    (agentId: AgentId, fragments: string[]) =>
      dispatch({ type: 'SET_AGENT_THOUGHT', payload: { agentId, fragments } }),
    []
  )
  const clearAgentThought = useCallback(
    (agentId: AgentId) => dispatch({ type: 'CLEAR_AGENT_THOUGHT', payload: agentId }),
    []
  )
  const addActivity = useCallback(
    (entry: Omit<ActivityEntry, 'id'>) =>
      dispatch({ type: 'ADD_ACTIVITY', payload: entry }),
    []
  )
  const addTransaction = useCallback(
    (tx: Omit<Transaction, 'id'>) =>
      dispatch({ type: 'ADD_TRANSACTION', payload: tx }),
    []
  )
  const updateBudget = useCallback(
    (spent: number, total?: number) =>
      dispatch({ type: 'UPDATE_BUDGET', payload: { spent, total } }),
    []
  )
  const reset = useCallback(() => dispatch({ type: 'RESET' }), [])

  return (
    <SimulationContext.Provider
      value={{
        state,
        setMission,
        setStage,
        setRunning,
        tickElapsed,
        setAgentStatus,
        setAgentThought,
        clearAgentThought,
        addActivity,
        addTransaction,
        updateBudget,
        reset,
      }}
    >
      {children}
    </SimulationContext.Provider>
  )
}

export function useSimulation() {
  const ctx = useContext(SimulationContext)
  if (!ctx) throw new Error('useSimulation must be used within SimulationProvider')
  return ctx
}
