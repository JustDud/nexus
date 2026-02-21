import { useState } from 'react'
import { motion } from 'framer-motion'
import { AGENTS } from '../../types'
import { useSimulation } from '../../context/SimulationContext'
import { AgentShape } from './AgentShape'
import { ThoughtStream } from './ThoughtStream'
import { AgentDetailModal } from './AgentDetailModal'
import { GlassPanel } from '../shared/GlassPanel'
import { cn } from '../../lib/utils'
import type { AgentId } from '../../types'

const STATUS_LABEL: Record<string, string> = {
  idle: 'standing by',
  thinking: 'thinking...',
  acting: 'executing',
  blocked: 'BLOCKED',
  complete: 'complete',
}

const STATUS_DOT: Record<string, string> = {
  idle: 'bg-[#64748b]',
  thinking: 'bg-[#3b82f6] animate-pulse',
  acting: 'bg-[#22c55e] animate-pulse',
  blocked: 'bg-[#ef4444]',
  complete: 'bg-[#22c55e]',
}

function AgentPanel({ agentId, onOpen }: { agentId: AgentId; onOpen: () => void }) {
  const { state } = useSimulation()
  const def = AGENTS.find((a) => a.id === agentId)!
  const agentState = state.agents.find((a) => a.id === agentId)!

  const lastAction = agentState.completedActions[agentState.completedActions.length - 1]

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.92 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="relative"
    >
      <GlassPanel
        onClick={onOpen}
        danger={agentState.status === 'blocked'}
        className="h-full flex flex-col items-center py-6 px-4 gap-3 group"
      >
        {/* Thought stream floats above shape */}
        <div className="relative w-full">
          <div className="absolute inset-x-0 bottom-full">
            <ThoughtStream
              fragments={agentState.currentThought}
              color={def.color}
              visible={agentState.status === 'thinking' && agentState.currentThought.length > 0}
            />
          </div>
          <AgentShape
            shape={def.shape}
            color={def.color}
            status={agentState.status}
            size={130}
          />
        </div>

        {/* Agent label */}
        <div className="text-center space-y-1 w-full">
          <div
            className="text-xs font-bold tracking-widest uppercase"
            style={{ color: def.color, fontFamily: 'Space Grotesk, sans-serif' }}
          >
            {def.name}
          </div>
          <div className="flex items-center justify-center gap-1.5">
            <span className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0', STATUS_DOT[agentState.status])} />
            <span className="font-mono text-[10px] text-[#64748b]">
              {STATUS_LABEL[agentState.status]}
            </span>
          </div>
        </div>

        {/* Last action chip */}
        {lastAction && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full"
          >
            <div
              className="w-full rounded-full px-3 py-1 text-center font-mono text-[9px] truncate border"
              style={{
                borderColor: `${def.color}30`,
                background: `${def.color}10`,
                color: def.color,
              }}
            >
              ✓ {lastAction.description}
              {lastAction.cost > 0 && ` — $${lastAction.cost}`}
            </div>
          </motion.div>
        )}

        {/* Click hint */}
        <div className="absolute inset-0 rounded-xl ring-0 group-hover:ring-1 transition-all duration-200"
          style={{ ringColor: `${def.color}40` } as React.CSSProperties}
        />
      </GlassPanel>
    </motion.div>
  )
}

export function AgentStage() {
  const [openAgent, setOpenAgent] = useState<AgentId | null>(null)

  return (
    <>
      <div className="grid grid-cols-2 grid-rows-2 gap-4 h-full">
        {AGENTS.map((def) => (
          <AgentPanel
            key={def.id}
            agentId={def.id}
            onOpen={() => setOpenAgent(def.id)}
          />
        ))}
      </div>

      <AgentDetailModal
        agentId={openAgent}
        onClose={() => setOpenAgent(null)}
      />
    </>
  )
}
