import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { TypeAnimation } from 'react-type-animation'
import type { AgentId, AgentStatus } from '../../types'
import { useSimulation } from '../../context/SimulationContext'

/* ── types ──────────────────────────────────────────────────────── */

interface TerminalLine {
  tag: string
  content: string
  tagColor: string // 'agent60' | 'agent40' | hex
}

interface ResultRow {
  label: string
  value: string
  big?: boolean
  success?: boolean
}

interface ResultSection {
  header: string
  rows: ResultRow[]
}

/* ── helpers ────────────────────────────────────────────────────── */

const TAG_CYCLE = [
  { tag: '>', tagColor: 'agent40' },
  { tag: '[DATA]', tagColor: '#3b82f6' },
  { tag: '>', tagColor: 'agent40' },
  { tag: '[CALC]', tagColor: '#22c55e' },
  { tag: '>', tagColor: 'agent40' },
  { tag: '[OUT]', tagColor: '#ffffff' },
]

function thoughtsToLines(fragments: string[]): TerminalLine[] {
  return fragments.map((text, i) => {
    const cycle = TAG_CYCLE[i % TAG_CYCLE.length]
    return { tag: cycle.tag, content: text, tagColor: cycle.tagColor }
  })
}

function buildResults(
  agentId: AgentId,
  totalSpent: number,
  completedActions: { description: string; cost: number; status: string }[],
  totalBudget: number,
  spentBudget: number,
): ResultSection[] {
  if (agentId === 'finance') {
    const remaining = totalBudget - spentBudget
    const solvent = remaining > 0
    return [
      {
        header: 'BUDGET TRACKING',
        rows: [
          { label: 'TOTAL', value: `$${totalBudget.toLocaleString()}`, big: true },
          { label: 'SPENT', value: `$${spentBudget.toLocaleString()}`, big: true },
          { label: 'REMAINING', value: `$${remaining.toLocaleString()}`, big: true },
        ],
      },
      {
        header: 'STATUS',
        rows: [
          { label: 'RISK', value: remaining / totalBudget < 0.3 ? 'HIGH' : remaining / totalBudget < 0.5 ? 'MEDIUM' : 'LOW' },
          { label: 'STATUS', value: solvent ? 'SOLVENT' : 'DEPLETED', success: solvent },
        ],
      },
    ]
  }

  const sections: ResultSection[] = []

  if (completedActions.length > 0) {
    sections.push({
      header: 'COMPLETED ACTIONS',
      rows: completedActions.map((a) => ({
        label: a.description.length > 20 ? a.description.slice(0, 20) + '...' : a.description,
        value: a.cost > 0 ? `$${a.cost.toLocaleString()}` : 'done',
        success: a.status === 'approved',
      })),
    })
  }

  sections.push({
    header: 'SUMMARY',
    rows: [
      { label: 'TOTAL SPENT', value: `$${totalSpent.toLocaleString()}`, big: true },
      { label: 'ACTIONS', value: String(completedActions.length) },
      { label: 'STATUS', value: 'COMPLETE', success: true },
    ],
  })

  return sections
}

function resolveTagColor(tagColor: string, agentColor: string): string {
  if (tagColor === 'agent60') return agentColor + '99'
  if (tagColor === 'agent40') return agentColor + '66'
  return tagColor
}

/* ── sub-states ─────────────────────────────────────────────────── */

function IdleState({ color }: { color: string }) {
  return (
    <div
      style={{
        padding: '16px',
        fontFamily: "'Share Tech Mono', monospace",
        fontSize: 13,
        color: color + '4d',
        height: '100%',
        display: 'flex',
        alignItems: 'flex-start',
        paddingTop: 20,
      }}
    >
      <span>&gt; awaiting task assignment</span>
      <motion.span
        style={{
          display: 'inline-block',
          width: 8,
          height: 13,
          background: color + '4d',
          marginLeft: 4,
          verticalAlign: 'middle',
          borderRadius: 1,
        }}
        animate={{ opacity: [1, 0, 1] }}
        transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }}
      />
    </div>
  )
}

function ThinkingState({
  agentId,
  color,
  lines,
  visibleCount,
}: {
  agentId: string
  color: string
  lines: TerminalLine[]
  visibleCount: number
}) {
  const MAX_VISIBLE = 8
  const shown = lines.slice(Math.max(0, visibleCount - MAX_VISIBLE), visibleCount)

  return (
    <div
      style={{
        padding: '12px 16px',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-end',
        overflow: 'hidden',
      }}
    >
      <AnimatePresence initial={false}>
        {shown.map((line, i) => {
          const isLast = i === shown.length - 1
          const tagColor = resolveTagColor(line.tagColor, color)
          const key = `${agentId}-${visibleCount - shown.length + i}`

          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: isLast ? 1 : 0.45, y: 0 }}
              transition={{ duration: 0.2 }}
              style={{
                display: 'flex',
                gap: 8,
                marginBottom: 4,
                alignItems: 'baseline',
                flexShrink: 0,
              }}
            >
              <span
                style={{
                  fontFamily: "'Space Mono', monospace",
                  fontWeight: 700,
                  fontSize: 10,
                  color: tagColor,
                  minWidth: 52,
                  flexShrink: 0,
                  letterSpacing: '0.02em',
                }}
              >
                {line.tag}
              </span>
              <span
                style={{
                  fontFamily: "'Share Tech Mono', monospace",
                  fontSize: 12,
                  color: isLast ? 'white' : '#64748b',
                  lineHeight: 1.4,
                }}
              >
                {isLast ? (
                  <TypeAnimation
                    key={`${agentId}-type-${visibleCount}`}
                    sequence={[line.content]}
                    speed={72}
                    cursor={false}
                    wrapper="span"
                  />
                ) : (
                  line.content
                )}
              </span>
            </motion.div>
          )
        })}
      </AnimatePresence>

      {/* Blinking cursor */}
      {visibleCount > 0 && (
        <motion.span
          style={{
            display: 'inline-block',
            width: 7,
            height: 12,
            background: color,
            marginLeft: 60,
            verticalAlign: 'middle',
            borderRadius: 1,
            flexShrink: 0,
          }}
          animate={{ opacity: [1, 0, 1] }}
          transition={{ duration: 0.75, repeat: Infinity }}
        />
      )}
    </div>
  )
}

function ResultsState({
  color,
  results,
  visibleRows,
}: {
  color: string
  results: ResultSection[]
  visibleRows: number
}) {
  let idx = 0

  return (
    <div
      style={{
        padding: '12px 16px',
        height: '100%',
        overflowY: 'auto',
      }}
    >
      {/* Header */}
      <div
        style={{
          fontFamily: "'Space Mono', monospace",
          fontWeight: 700,
          color,
          fontSize: 11,
          letterSpacing: '0.1em',
          marginBottom: 10,
        }}
      >
        // TASK COMPLETE ──────────────────
      </div>

      {results.map((section, si) => {
        const headerVisible = idx < visibleRows
        idx++
        return (
          <div key={si} style={{ marginBottom: 10 }}>
            {headerVisible && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={{
                  fontFamily: "'Space Mono', monospace",
                  fontWeight: 700,
                  color,
                  fontSize: 11,
                  letterSpacing: '0.2em',
                  textTransform: 'uppercase',
                  marginBottom: 4,
                }}
              >
                {section.header}
              </motion.div>
            )}
            {section.rows.map((row, ri) => {
              const rowVisible = idx < visibleRows
              const thisIdx = idx
              idx++
              if (!rowVisible) return null
              return (
                <motion.div
                  key={ri}
                  initial={{ opacity: 0, x: -4 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: thisIdx * 0.02 }}
                  style={{
                    display: 'flex',
                    gap: 8,
                    alignItems: 'baseline',
                    marginBottom: 3,
                  }}
                >
                  <span
                    style={{
                      fontFamily: "'Share Tech Mono', monospace",
                      color: '#64748b',
                      fontSize: 12,
                      minWidth: 112,
                      flexShrink: 0,
                    }}
                  >
                    {row.label}
                  </span>
                  <span
                    style={{
                      fontFamily: row.big ? "'VT323', monospace" : "'Space Mono', monospace",
                      fontWeight: row.big ? 400 : 700,
                      fontSize: row.big ? 20 : 12,
                      color: row.success ? '#22c55e' : 'white',
                      lineHeight: row.big ? '1.1' : '1.5',
                    }}
                  >
                    {row.value}
                  </span>
                </motion.div>
              )
            })}
          </div>
        )
      })}
    </div>
  )
}

/* ── main component ──────────────────────────────────────────────── */

interface TerminalPanelProps {
  agentId: string
  status: AgentStatus
  color: string
}

export function TerminalPanel({ agentId, status, color }: TerminalPanelProps) {
  const { state } = useSimulation()
  const agentState = state.agents.find((a) => a.id === agentId)

  // Build terminal lines from real agent thoughts
  const lines = thoughtsToLines(agentState?.currentThought ?? [])

  // Build results from real agent data
  const results = buildResults(
    agentId as AgentId,
    agentState?.totalSpent ?? 0,
    agentState?.completedActions ?? [],
    state.totalBudget,
    state.spentBudget,
  )

  const [visibleLines, setVisibleLines] = useState(0)
  const [showResults, setShowResults] = useState(false)
  const [flashing, setFlashing] = useState(false)
  const [visibleResults, setVisibleResults] = useState(0)

  const prevStatus = useRef<AgentStatus>('idle')
  const lineTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Reset when transitioning to thinking
  useEffect(() => {
    if (status === 'thinking' && prevStatus.current !== 'thinking') {
      setVisibleLines(0)
      setShowResults(false)
      setFlashing(false)
      setVisibleResults(0)
    }
    prevStatus.current = status
  }, [status])

  // When new fragments arrive, reveal them
  useEffect(() => {
    if (status === 'thinking' && visibleLines < lines.length) {
      const delay = 400 + Math.random() * 300
      lineTimerRef.current = setTimeout(() => {
        setVisibleLines((v) => Math.min(v + 1, lines.length))
      }, delay)
      return () => {
        if (lineTimerRef.current) clearTimeout(lineTimerRef.current)
      }
    }
  }, [status, visibleLines, lines.length])

  // Transition to results when complete
  useEffect(() => {
    if (status === 'complete' && !showResults && !flashing) {
      setFlashing(true)
      const t = setTimeout(() => {
        setFlashing(false)
        setShowResults(true)
      }, 350)
      return () => clearTimeout(t)
    }
  }, [status, showResults, flashing])

  // Stream result rows
  const totalResultRows = results.reduce((acc, s) => acc + 1 + s.rows.length, 0)
  useEffect(() => {
    if (showResults && visibleResults < totalResultRows + 1) {
      const t = setTimeout(() => {
        setVisibleResults((v) => v + 1)
      }, 100)
      return () => clearTimeout(t)
    }
  }, [showResults, visibleResults, totalResultRows])

  if (flashing) {
    return (
      <motion.div
        style={{ height: '100%', background: color + '12' }}
        animate={{ opacity: [0.2, 1, 0.1, 1, 0] }}
        transition={{ duration: 0.35 }}
      />
    )
  }

  if (showResults) {
    return (
      <ResultsState
        color={color}
        results={results}
        visibleRows={visibleResults}
      />
    )
  }

  if (status === 'idle') {
    return <IdleState color={color} />
  }

  return (
    <ThinkingState
      agentId={agentId}
      color={color}
      lines={lines}
      visibleCount={visibleLines}
    />
  )
}
