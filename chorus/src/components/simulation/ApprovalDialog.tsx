import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useSimulation } from '../../context/SimulationContext'
import { AGENTS } from '../../types'

interface ApprovalDialogProps {
  onDecide: (approved: boolean, reason?: string) => void
}

export function ApprovalDialog({ onDecide }: ApprovalDialogProps) {
  const { state } = useSimulation()
  const [reason, setReason] = useState('')

  const pending = state.pendingApproval
  if (!pending) return null

  const agentDef = AGENTS.find((a) => a.id === pending.agentId)
  const agentColor = agentDef?.color ?? '#94a3b8'

  const afterBudget = state.totalBudget - state.spentBudget - pending.cost
  const afterPercent = afterBudget / state.totalBudget
  const isAfterDanger = afterPercent < 0.3

  const handleApprove = () => {
    onDecide(true)
    setReason('')
  }

  const handleReject = () => {
    onDecide(false, reason || undefined)
    setReason('')
  }

  return (
    <AnimatePresence>
      {pending && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50"
            style={{ background: 'rgba(8,8,16,0.85)', backdropFilter: 'blur(8px)' }}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, y: 40, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.97 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div
              className="w-full max-w-lg rounded-2xl border overflow-hidden"
              style={{
                background: '#0f0f1a',
                borderColor: 'rgba(239,68,68,0.3)',
              }}
            >
              {/* Header */}
              <div className="px-6 py-4 border-b" style={{ borderColor: 'rgba(239,68,68,0.2)' }}>
                <div className="flex items-center gap-2">
                  <span
                    className="w-2 h-2 rounded-full bg-[#ef4444] flex-shrink-0"
                    style={{ animation: 'pulse 1.5s ease-in-out infinite' }}
                  />
                  <span
                    className="font-bold text-xs tracking-[0.2em] text-[#ef4444]"
                    style={{ fontFamily: 'Space Grotesk, sans-serif' }}
                  >
                    CEO APPROVAL REQUIRED
                  </span>
                </div>
              </div>

              {/* Body */}
              <div className="px-6 py-5 space-y-5">
                {/* Agent */}
                <div className="flex items-center gap-2">
                  <span
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ background: agentColor }}
                  />
                  <span
                    className="font-mono text-xs"
                    style={{ color: agentColor }}
                  >
                    {pending.agentName}
                  </span>
                </div>

                {/* Proposal title */}
                <div>
                  <h2
                    className="font-bold text-lg text-[#f8fafc] leading-tight"
                    style={{ fontFamily: 'Space Grotesk, sans-serif' }}
                  >
                    {pending.title}
                  </h2>
                  <p className="font-mono text-xs text-[#64748b] mt-2 leading-relaxed">
                    {pending.description}
                  </p>
                </div>

                {/* Cost impact grid */}
                <div className="grid grid-cols-3 gap-px bg-[#1a1a2e] rounded-lg overflow-hidden">
                  <div className="bg-[#0f0f1a] px-4 py-3">
                    <div className="font-mono text-[9px] text-[#64748b] uppercase tracking-widest">
                      Cost
                    </div>
                    <div
                      className="font-bold text-sm mt-0.5 text-[#f59e0b]"
                      style={{ fontFamily: 'Space Grotesk, sans-serif' }}
                    >
                      ${pending.cost.toLocaleString()}
                    </div>
                  </div>
                  <div className="bg-[#0f0f1a] px-4 py-3">
                    <div className="font-mono text-[9px] text-[#64748b] uppercase tracking-widest">
                      Current Budget
                    </div>
                    <div
                      className="font-bold text-sm mt-0.5 text-[#f8fafc]"
                      style={{ fontFamily: 'Space Grotesk, sans-serif' }}
                    >
                      ${(state.totalBudget - state.spentBudget).toLocaleString()}
                    </div>
                  </div>
                  <div className="bg-[#0f0f1a] px-4 py-3">
                    <div className="font-mono text-[9px] text-[#64748b] uppercase tracking-widest">
                      After Approval
                    </div>
                    <div
                      className="font-bold text-sm mt-0.5"
                      style={{
                        fontFamily: 'Space Grotesk, sans-serif',
                        color: isAfterDanger ? '#ef4444' : '#f8fafc',
                      }}
                    >
                      ${afterBudget.toLocaleString()}
                    </div>
                  </div>
                </div>

                {/* Reason textarea */}
                <div>
                  <label className="font-mono text-[9px] text-[#64748b] uppercase tracking-widest block mb-1.5">
                    Rejection reason (optional)
                  </label>
                  <textarea
                    className="w-full bg-[#1a1a2e] border border-[#2a2a3e] rounded-lg px-3 py-2 font-mono text-xs text-[#f8fafc] placeholder-[#3a3a5e] resize-none focus:outline-none focus:border-[#64748b] transition-colors"
                    rows={2}
                    placeholder="Why are you rejecting this proposal?"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </div>

                {/* Buttons */}
                <div className="flex gap-3">
                  <button
                    onClick={handleApprove}
                    className="flex-1 py-2.5 rounded-lg font-bold text-xs tracking-widest transition-all duration-200 hover:brightness-110"
                    style={{
                      fontFamily: 'Space Grotesk, sans-serif',
                      background: 'rgba(34,197,94,0.15)',
                      color: '#22c55e',
                      border: '1px solid rgba(34,197,94,0.3)',
                    }}
                  >
                    APPROVE
                  </button>
                  <button
                    onClick={handleReject}
                    className="flex-1 py-2.5 rounded-lg font-bold text-xs tracking-widest transition-all duration-200 hover:brightness-110"
                    style={{
                      fontFamily: 'Space Grotesk, sans-serif',
                      background: 'rgba(239,68,68,0.15)',
                      color: '#ef4444',
                      border: '1px solid rgba(239,68,68,0.3)',
                    }}
                  >
                    REJECT
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
