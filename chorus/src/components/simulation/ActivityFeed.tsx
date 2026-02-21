import { useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useSimulation } from '../../context/SimulationContext'
import { AGENTS } from '../../types'
import { GlassPanel } from '../shared/GlassPanel'
import { formatElapsed } from '../../lib/utils'

function agentColor(agentId: string): string {
  return AGENTS.find((a) => a.id === agentId)?.color ?? '#94a3b8'
}

function agentLabel(agentId: string): string {
  const map: Record<string, string> = {
    product: 'PRODUCT',
    tech: 'TECH   ',
    ops: 'OPS    ',
    finance: 'FINANCE',
  }
  return map[agentId] ?? agentId.toUpperCase()
}

export function ActivityFeed() {
  const { state } = useSimulation()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.activityLog.length])

  return (
    <GlassPanel className="flex flex-col h-full overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-[#1a1a2e] flex-shrink-0">
        <span className="w-2 h-2 rounded-full bg-[#3b82f6] animate-pulse" />
        <span className="font-bold text-xs tracking-widest uppercase text-[#f8fafc]"
          style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
          Live Feed
        </span>
        <span className="ml-auto font-mono text-[10px] text-[#64748b]">
          {state.activityLog.length} events
        </span>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-1 min-h-0">
        <AnimatePresence initial={false}>
          {state.activityLog.map((entry) => (
            <motion.div
              key={entry.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="flex items-start gap-2 py-1.5 group"
            >
              {/* Agent bracket */}
              <span
                className="font-mono text-[10px] font-bold flex-shrink-0 leading-relaxed"
                style={{ color: agentColor(entry.agentId) }}
              >
                [{agentLabel(entry.agentId)}]
              </span>

              {/* Message */}
              <span className="font-mono text-[10px] text-[#94a3b8] leading-relaxed flex-1 min-w-0">
                {entry.message}
              </span>

              {/* Timestamp */}
              <span className="font-mono text-[9px] text-[#1a1a2e] group-hover:text-[#64748b]
                flex-shrink-0 transition-colors leading-relaxed">
                {formatElapsed(Math.floor((entry.timestamp - (state.activityLog[0]?.timestamp ?? entry.timestamp)) / 1000))}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>
    </GlassPanel>
  )
}
