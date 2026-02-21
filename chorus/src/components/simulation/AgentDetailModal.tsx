import { AnimatePresence, motion } from 'framer-motion'
import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { useSimulation } from '../../context/SimulationContext'
import { AGENTS, type AgentId } from '../../types'
import { AgentShape } from './AgentShape'
import { formatElapsed } from '../../lib/utils'

interface AgentDetailModalProps {
  agentId: AgentId | null
  onClose: () => void
}

export function AgentDetailModal({ agentId, onClose }: AgentDetailModalProps) {
  const { state } = useSimulation()

  const def = agentId ? AGENTS.find((a) => a.id === agentId) : null
  const agentState = agentId ? state.agents.find((a) => a.id === agentId) : null
  const logs = state.activityLog.filter((e) => e.agentId === agentId)
  const startTs = state.activityLog[0]?.timestamp ?? Date.now()

  return (
    <Dialog.Root open={!!agentId} onOpenChange={(open) => !open && onClose()}>
      <AnimatePresence>
        {agentId && def && agentState && (
          <Dialog.Portal forceMount>
            {/* Backdrop */}
            <Dialog.Overlay asChild>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-40"
                style={{ background: 'rgba(8,8,16,0.85)', backdropFilter: 'blur(8px)' }}
              />
            </Dialog.Overlay>

            {/* Panel */}
            <Dialog.Content asChild>
              <motion.div
                initial={{ opacity: 0, y: 40, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 24, scale: 0.97 }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
                className="fixed inset-x-0 bottom-0 z-50 max-w-2xl mx-auto rounded-t-2xl border-t border-x
                  overflow-hidden"
                style={{
                  background: '#0f0f1a',
                  borderColor: `${def.color}30`,
                  maxHeight: '80vh',
                }}
              >
                {/* Header */}
                <div
                  className="flex items-center justify-between px-6 py-4 border-b"
                  style={{ borderColor: `${def.color}20` }}
                >
                  <div className="flex items-center gap-4">
                    <AgentShape shape={def.shape} color={def.color} status={agentState.status} size={60} />
                    <div>
                      <div
                        className="font-bold text-sm tracking-widest uppercase"
                        style={{ color: def.color, fontFamily: 'Space Grotesk, sans-serif' }}
                      >
                        {def.name}
                      </div>
                      <div className="font-mono text-[11px] text-[#64748b] mt-0.5">{def.role}</div>
                    </div>
                  </div>
                  <Dialog.Close asChild>
                    <button className="text-[#64748b] hover:text-[#f8fafc] transition-colors p-2 rounded-lg hover:bg-[#1a1a2e]">
                      <X size={18} />
                    </button>
                  </Dialog.Close>
                </div>

                <div className="overflow-y-auto" style={{ maxHeight: 'calc(80vh - 80px)' }}>
                  {/* Stats row */}
                  <div className="grid grid-cols-3 gap-px bg-[#1a1a2e] border-b border-[#1a1a2e]">
                    {[
                      { label: 'STATUS', value: agentState.status.toUpperCase() },
                      { label: 'SPENT', value: `$${agentState.totalSpent}` },
                      { label: 'ACTIONS', value: String(agentState.completedActions.length) },
                    ].map(({ label, value }) => (
                      <div key={label} className="bg-[#0f0f1a] px-4 py-3">
                        <div className="font-mono text-[9px] text-[#64748b] uppercase tracking-widest">{label}</div>
                        <div
                          className="font-bold text-sm mt-0.5"
                          style={{
                            color: label === 'STATUS' && agentState.status === 'blocked'
                              ? '#ef4444'
                              : '#f8fafc',
                            fontFamily: 'Space Grotesk, sans-serif',
                          }}
                        >
                          {value}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Completed actions */}
                  {agentState.completedActions.length > 0 && (
                    <div className="px-6 py-4">
                      <div className="font-mono text-[10px] text-[#64748b] uppercase tracking-widest mb-3">
                        Completed Actions
                      </div>
                      <div className="space-y-2">
                        {agentState.completedActions.map((action) => (
                          <div
                            key={action.id}
                            className="flex items-center gap-3 py-2 border-b border-[#1a1a2e]"
                          >
                            <span
                              className="font-mono text-[10px] font-bold flex-shrink-0"
                              style={{ color: action.status === 'approved' ? '#22c55e' : '#ef4444' }}
                            >
                              {action.status === 'approved' ? '✓' : '✗'}
                            </span>
                            <span className="font-mono text-xs text-[#94a3b8] flex-1">{action.description}</span>
                            {action.cost > 0 && (
                              <span className="font-mono text-[10px] text-[#f59e0b]">
                                ${action.cost}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Full reasoning log */}
                  <div className="px-6 py-4">
                    <div className="font-mono text-[10px] text-[#64748b] uppercase tracking-widest mb-3">
                      Reasoning Log
                    </div>
                    <div className="space-y-1">
                      {logs.length === 0 && (
                        <span className="font-mono text-[10px] text-[#1a1a2e]">No log entries yet.</span>
                      )}
                      {logs.map((entry) => (
                        <div key={entry.id} className="flex items-start gap-2">
                          <span className="font-mono text-[9px] text-[#64748b] flex-shrink-0 mt-0.5 tabular-nums">
                            {formatElapsed(Math.floor((entry.timestamp - startTs) / 1000))}
                          </span>
                          <span
                            className="font-mono text-[10px] leading-relaxed"
                            style={{
                              color:
                                entry.type === 'block'
                                  ? '#ef4444'
                                  : entry.type === 'complete'
                                  ? '#22c55e'
                                  : entry.type === 'action'
                                  ? def.color
                                  : '#64748b',
                            }}
                          >
                            {entry.message}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            </Dialog.Content>
          </Dialog.Portal>
        )}
      </AnimatePresence>
    </Dialog.Root>
  )
}
