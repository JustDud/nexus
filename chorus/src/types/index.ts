export type AgentId = 'product' | 'tech' | 'ops' | 'finance'

export type AgentStatus = 'idle' | 'thinking' | 'acting' | 'blocked' | 'complete'

export type SimulationStage =
  | 'research'
  | 'proposal'
  | 'debate'
  | 'decision'
  | 'execution'
  | 'complete'

export type ActivityType = 'thought' | 'action' | 'block' | 'complete' | 'debate' | 'conclusion'

export type TransactionStatus = 'approved' | 'blocked' | 'pending'

export type AgentShape = 'icosahedron' | 'torusKnot' | 'dodecahedron' | 'octahedron'

export interface PendingApproval {
  proposalId: string
  title: string
  cost: number
  description: string
  agentId: AgentId
  agentName: string
  timestamp: number
}

export interface Action {
  id: string
  description: string
  cost: number
  timestamp: number
  status: TransactionStatus
}

export interface AgentState {
  id: AgentId
  status: AgentStatus
  currentThought: string[]
  completedActions: Action[]
  totalSpent: number
}

export interface ActivityEntry {
  id: string
  agentId: AgentId
  message: string
  timestamp: number
  type: ActivityType
}

export interface Transaction {
  id: string
  agentId: AgentId
  description: string
  amount: number
  status: TransactionStatus
  timestamp: number
}

export interface SimulationState {
  mission: string
  projectTitle: string
  fileContent: string | null
  totalBudget: number
  spentBudget: number
  dangerMode: boolean
  stage: SimulationStage
  elapsedSeconds: number
  agents: AgentState[]
  activityLog: ActivityEntry[]
  transactions: Transaction[]
  isRunning: boolean
  pendingApproval: PendingApproval | null
  operationsRound: number
  isPaused: boolean
  isDebating: boolean
  isEavesdropping: boolean
}

export interface AgentDefinition {
  id: AgentId
  name: string
  role: string
  personality: string
  color: string
  shape: AgentShape
  position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'
}

export const AGENTS: AgentDefinition[] = [
  {
    id: 'product',
    name: 'Product + Marketing',
    role: 'Market research, ICP, MVP scope, ad campaigns',
    personality: 'Visionary, fast-talking, always wants more features and bigger reach',
    color: '#f59e0b',
    shape: 'icosahedron',
    position: 'top-left',
  },
  {
    id: 'tech',
    name: 'Tech',
    role: 'Architecture, infrastructure, feasibility, deployment',
    personality: 'Pragmatic, conservative, warns about complexity, finds free alternatives',
    color: '#22c55e',
    shape: 'torusKnot',
    position: 'top-right',
  },
  {
    id: 'ops',
    name: 'Operations',
    role: 'Execution, vendor management, legal, compliance',
    personality: 'Process-driven, thorough, flags risks before acting',
    color: '#8b5cf6',
    shape: 'dodecahedron',
    position: 'bottom-left',
  },
  {
    id: 'finance',
    name: 'Finance',
    role: 'Budget tracking, burn rate, blocking overspend',
    personality: 'Blunt, dry, blocks anything that threatens runway',
    color: '#ef4444',
    shape: 'octahedron',
    position: 'bottom-right',
  },
]
