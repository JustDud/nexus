import { useState } from 'react'
import { motion } from 'framer-motion'
import { AGENTS } from '../../types'
import { useSimulation } from '../../context/SimulationContext'
import AgentShape from './shapes/AgentShape'
import { TerminalPanel } from './TerminalPanel'
import { AgentDetailModal } from './AgentDetailModal'
import type { AgentId, AgentStatus } from '../../types'

// Holographic palette — overrides raw agent colors for card chrome
const CARD_COLORS: Record<AgentId, string> = {
  product: '#a78bfa', // soft violet
  tech:    '#67e8f9', // soft cyan
  ops:     '#e879f9', // soft magenta
  finance: '#fda4af', // soft rose
}

/* ── Corner bracket ───────────────────────────────────────────── */
function Corner({ pos, color }: { pos: 'tl' | 'tr' | 'bl' | 'br'; color: string }) {
  const top  = pos === 'tl' || pos === 'tr'
  const left = pos === 'tl' || pos === 'bl'
  return (
    <div
      style={{
        position: 'absolute',
        width: 16,
        height: 16,
        top:    top  ? 0 : undefined,
        bottom: !top ? 0 : undefined,
        left:   left  ? 0 : undefined,
        right:  !left ? 0 : undefined,
        borderTop:    top    ? `2px solid ${color}99` : undefined,
        borderBottom: !top   ? `2px solid ${color}99` : undefined,
        borderLeft:   left   ? `2px solid ${color}99` : undefined,
        borderRight:  !left  ? `2px solid ${color}99` : undefined,
        pointerEvents: 'none',
        zIndex: 3,
      }}
    />
  )
}

/* ── Status dot ───────────────────────────────────────────────── */
const STATUS_TEXT: Record<AgentStatus, string> = {
  idle:     'standing by',
  thinking: 'processing...',
  acting:   'executing',
  blocked:  'BLOCKED',
  complete: 'complete ✓',
}

function StatusDot({ status, color }: { status: AgentStatus; color: string }) {
  const base: React.CSSProperties = {
    width: 8,
    height: 8,
    borderRadius: '50%',
    flexShrink: 0,
  }
  if (status === 'idle')     return <div style={{ ...base, background: '#1e293b' }} />
  if (status === 'thinking') return <div className="dot-thinking" style={{ ...base, background: color, boxShadow: `0 0 8px ${color}80` }} />
  if (status === 'acting')   return <div className="dot-acting"   style={{ ...base, background: '#2dd4bf', boxShadow: '0 0 8px rgba(45,212,191,0.6)' }} />
  if (status === 'blocked')  return <div style={{ ...base, background: '#fb7185', boxShadow: '0 0 8px rgba(251,113,133,0.7)' }} />
  if (status === 'complete') return <div style={{ ...base, background: '#34d399', boxShadow: '0 0 8px rgba(52,211,153,0.5)' }} />
  return null
}

/* ── Agent card ───────────────────────────────────────────────── */
function AgentCard({ agentId, onOpen }: { agentId: AgentId; onOpen: () => void }) {
  const { state } = useSimulation()
  const def        = AGENTS.find((a) => a.id === agentId)!
  const agentState = state.agents.find((a) => a.id === agentId)!
  const isBlocked  = agentState.status === 'blocked'

  // Holographic card color — overrides raw def.color for chrome elements
  const cardColor = CARD_COLORS[agentId]

  const borderColor = isBlocked
    ? 'rgba(251,113,133,0.45)'
    : `${cardColor}2e`

  const hoverBorder = isBlocked
    ? 'rgba(251,113,133,0.75)'
    : `${cardColor}70`

  const hoverShadow = isBlocked
    ? '0 0 24px rgba(251,113,133,0.12)'
    : `0 0 24px ${cardColor}10`

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="relative h-full"
      style={{ cursor: 'pointer' }}
      onClick={onOpen}
      whileHover={{ scale: 1.008 }}
    >
      {/* Card shell */}
      <div
        className="relative h-full overflow-hidden"
        style={{
          background: 'rgba(10,8,22,0.82)',
          border: `1px solid ${borderColor}`,
          borderRadius: 0,
          display: 'flex',
          flexDirection: 'row',
          transition: 'border-color 200ms ease, box-shadow 200ms ease',
        }}
        onMouseEnter={e => {
          const el = e.currentTarget as HTMLDivElement
          el.style.borderColor = hoverBorder
          el.style.boxShadow   = hoverShadow
        }}
        onMouseLeave={e => {
          const el = e.currentTarget as HTMLDivElement
          el.style.borderColor = borderColor
          el.style.boxShadow   = 'none'
        }}
      >
        {/* Corner brackets use holographic color */}
        <Corner pos="tl" color={cardColor} />
        <Corner pos="tr" color={cardColor} />
        <Corner pos="bl" color={cardColor} />
        <Corner pos="br" color={cardColor} />

        {/* Scanline */}
        <div
          className="nexus-scanline"
          style={{
            background: `linear-gradient(90deg, transparent, ${cardColor} 40%, transparent)`,
            opacity: 0.1,
          }}
        />

        {/* LEFT PANEL — 40% */}
        <div
          style={{
            width: '40%',
            flexShrink: 0,
            background: `linear-gradient(160deg, rgba(${hexToRgb(cardColor)},0.04) 0%, rgba(0,0,0,0.25) 100%)`,
            borderRight: `1px solid ${cardColor}20`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
            padding: '16px 8px',
            position: 'relative',
            zIndex: 1,
          }}
        >
          {/* 3D shape */}
          <AgentShape
            agentId={def.id}
            state={agentState.status}
            size={180}
          />

          {/* Agent name */}
          <div
            style={{
              fontFamily: "'Space Mono', monospace",
              fontWeight: 700,
              fontSize: 11,
              color: cardColor,
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              textAlign: 'center',
              textShadow: `0 0 12px ${cardColor}60`,
            }}
          >
            {def.name}
          </div>

          {/* Status row */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <StatusDot status={agentState.status} color={cardColor} />
            <span
              style={{
                fontFamily: "'Share Tech Mono', monospace",
                fontSize: 12,
                color: isBlocked ? '#fb7185' : 'rgba(148,163,184,0.75)',
              }}
            >
              {STATUS_TEXT[agentState.status]}
            </span>
          </div>
        </div>

        {/* RIGHT PANEL — 60% */}
        <div
          style={{
            flex: 1,
            overflow: 'hidden',
            position: 'relative',
            zIndex: 1,
          }}
        >
          <TerminalPanel
            agentId={agentId}
            status={agentState.status}
            color={cardColor}
          />
        </div>
      </div>
    </motion.div>
  )
}

// Converts a 6-digit hex color to "r,g,b" for use in rgba()
function hexToRgb(hex: string): string {
  const h = hex.replace('#', '')
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return `${r},${g},${b}`
}

/* ── 2×2 grid ─────────────────────────────────────────────────── */
export function AgentStage() {
  const [openAgent, setOpenAgent] = useState<AgentId | null>(null)

  return (
    <>
      <div className="grid grid-cols-2 grid-rows-2 gap-3 h-full">
        {AGENTS.map((def) => (
          <AgentCard
            key={def.id}
            agentId={def.id}
            onOpen={() => setOpenAgent(def.id)}
          />
        ))}
      </div>
      <AgentDetailModal agentId={openAgent} onClose={() => setOpenAgent(null)} />
    </>
  )
}
