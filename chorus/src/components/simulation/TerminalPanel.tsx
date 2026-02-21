import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { TypeAnimation } from 'react-type-animation'
import type { AgentStatus } from '../../types'

/* ── per-agent terminal log lines ───────────────────────────────── */

interface TerminalLine {
  tag: string
  content: string
  tagColor: string // 'agent60' | 'agent40' | hex
}

const TERMINAL_LINES: Record<string, TerminalLine[]> = {
  product: [
    { tag: '[INIT]', content: 'loading market intelligence...', tagColor: 'agent60' },
    { tag: '[DATA]', content: 'fetching industry reports...', tagColor: '#3b82f6' },
    { tag: '>',      content: 'TAM analysis: processing...', tagColor: 'agent40' },
    { tag: '[CALC]', content: 'addressable market: $4.2B', tagColor: '#22c55e' },
    { tag: '>',      content: 'filtering by ICP parameters...', tagColor: 'agent40' },
    { tag: '[WARN]', content: 'competitor density: HIGH', tagColor: '#f59e0b' },
    { tag: '>',      content: 'adjusting strategy weighting...', tagColor: 'agent40' },
    { tag: '[OUT]',  content: 'recommendation confidence: 74%', tagColor: '#ffffff' },
  ],
  tech: [
    { tag: '[INIT]', content: 'scanning tech requirements...', tagColor: 'agent60' },
    { tag: '[DATA]', content: 'evaluating stack options...', tagColor: '#3b82f6' },
    { tag: '>',      content: 'API-first: recommended', tagColor: 'agent40' },
    { tag: '[CALC]', content: 'stack: React + FastAPI', tagColor: '#22c55e' },
    { tag: '>',      content: 'checking free tier limits...', tagColor: 'agent40' },
    { tag: '[DATA]', content: 'Railway: 500MB / 100k req/mo', tagColor: '#3b82f6' },
    { tag: '>',      content: 'domain registration: pending...', tagColor: 'agent40' },
    { tag: '[OUT]',  content: 'feasibility: HIGH / $12 total', tagColor: '#ffffff' },
  ],
  ops: [
    { tag: '[INIT]', content: 'GDPR compliance scan...', tagColor: 'agent60' },
    { tag: '[DATA]', content: 'loading legal requirements...', tagColor: '#3b82f6' },
    { tag: '>',      content: 'data processing: required', tagColor: 'agent40' },
    { tag: '[CALC]', content: 'Stripe Atlas: $500 setup', tagColor: '#22c55e' },
    { tag: '>',      content: 'generating legal documents...', tagColor: 'agent40' },
    { tag: '[WARN]', content: 'vendor SLA: review required', tagColor: '#f59e0b' },
    { tag: '>',      content: 'configuring support workflow...', tagColor: 'agent40' },
    { tag: '[OUT]',  content: 'ops readiness: 91%', tagColor: '#ffffff' },
  ],
  finance: [
    { tag: '[INIT]', content: 'budget parameters loaded...', tagColor: 'agent60' },
    { tag: '[DATA]', content: 'total capital: $1,000', tagColor: '#3b82f6' },
    { tag: '>',      content: 'setting burn rate targets...', tagColor: 'agent40' },
    { tag: '[CALC]', content: 'max single spend: $200', tagColor: '#22c55e' },
    { tag: '>',      content: 'monitoring all transactions...', tagColor: 'agent40' },
    { tag: '[WARN]', content: 'ad spend $300: DENIED', tagColor: '#f59e0b' },
    { tag: '>',      content: 'runway projection: calculating...', tagColor: 'agent40' },
    { tag: '[OUT]',  content: 'risk: MEDIUM / 39 days runway', tagColor: '#ffffff' },
  ],
}

/* ── per-agent results ───────────────────────────────────────────── */

interface ResultRow {
  label: string
  value: string
  big?: boolean    // use VT323 20px
  success?: boolean // use #22c55e
}

interface ResultSection {
  header: string
  rows: ResultRow[]
}

const AGENT_RESULTS: Record<string, ResultSection[]> = {
  product: [
    {
      header: 'MARKET ANALYSIS',
      rows: [
        { label: 'TAM',           value: '$4.2B', big: true },
        { label: 'ICP',           value: 'SMBs, 10-50 employees' },
        { label: 'TOP COMPETITOR',value: 'Competitor X ($29/mo)' },
      ],
    },
    {
      header: 'MVP DEFINITION',
      rows: [
        { label: 'CORE FEATURE', value: 'Photo symptom checker' },
        { label: 'DELIVERY',     value: '3 weeks' },
        { label: 'CONFIDENCE',   value: '82%', big: true },
      ],
    },
    {
      header: 'AD CAMPAIGN',
      rows: [
        { label: 'PLATFORM',    value: 'Instagram + Google' },
        { label: 'BUDGET USED', value: '$150', big: true },
        { label: 'STATUS',      value: '✓ LIVE', success: true },
      ],
    },
  ],
  tech: [
    {
      header: 'ARCHITECTURE',
      rows: [
        { label: 'STACK',  value: 'React + FastAPI' },
        { label: 'INFRA',  value: 'Railway (free tier)' },
        { label: 'DOMAIN', value: '✓ registered $12', success: true },
      ],
    },
    {
      header: 'FEASIBILITY',
      rows: [
        { label: 'COMPLEXITY', value: 'MEDIUM' },
        { label: 'TIMELINE',   value: '2 weeks' },
        { label: 'BLOCKERS',   value: 'None (free API)' },
      ],
    },
    {
      header: 'DEPLOYED',
      rows: [
        { label: 'URL',    value: 'app.startup.dev' },
        { label: 'STATUS', value: '✓ LIVE', success: true },
      ],
    },
  ],
  ops: [
    {
      header: 'VENDOR SETUP',
      rows: [
        { label: 'STRIPE ATLAS', value: '✓ initiated $500', success: true },
        { label: 'LEGAL DOCS',   value: '✓ downloaded', success: true },
        { label: 'COMPLIANCE',   value: 'GDPR checked' },
      ],
    },
    {
      header: 'PROCESSES',
      rows: [
        { label: 'ONBOARDING',   value: 'drafted' },
        { label: 'SUPPORT FLOW', value: 'configured' },
        { label: 'STATUS',       value: '✓ OPERATIONAL', success: true },
      ],
    },
  ],
  finance: [
    {
      header: 'BUDGET TRACKING',
      rows: [
        { label: 'TOTAL',     value: '$1,000', big: true },
        { label: 'SPENT',     value: '$674', big: true },
        { label: 'REMAINING', value: '$326', big: true },
        { label: 'BURN RATE', value: '$8.2/day' },
      ],
    },
    {
      header: 'RUNWAY',
      rows: [
        { label: 'PROJECTED', value: '39 days', big: true },
        { label: 'RISK LEVEL',value: 'MEDIUM' },
        { label: 'STATUS',    value: '✓ SOLVENT', success: true },
      ],
    },
  ],
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
  // Flatten for counting
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
  const lines   = TERMINAL_LINES[agentId] ?? []
  const results = AGENT_RESULTS[agentId] ?? []

  const [visibleLines,   setVisibleLines]   = useState(0)
  const [showResults,    setShowResults]    = useState(false)
  const [flashing,       setFlashing]       = useState(false)
  const [visibleResults, setVisibleResults] = useState(0)

  const prevStatus  = useRef<AgentStatus>('idle')
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

  // Stream lines when thinking
  useEffect(() => {
    if (status === 'thinking' && visibleLines < lines.length) {
      const delay = 800 + Math.random() * 400
      lineTimerRef.current = setTimeout(() => {
        setVisibleLines(v => Math.min(v + 1, lines.length))
      }, delay)
      return () => { if (lineTimerRef.current) clearTimeout(lineTimerRef.current) }
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
        setVisibleResults(v => v + 1)
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
