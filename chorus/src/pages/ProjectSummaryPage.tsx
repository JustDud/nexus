import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSimulation } from '../context/SimulationContext'
import { StatusBar } from '../components/simulation/StatusBar'
import { useAudioPlayer } from '../hooks/useAudioPlayer'
import LetterGlitch from '../components/simulation/LetterGlitch'
import AgentShape from '../components/simulation/shapes/AgentShape'
import type { AgentId } from '../types'

// ─── Agent data ──────────────────────────────────────────────────────────────
interface AgentData {
  id: AgentId
  name: string
  role: string
  color: string
  metrics: { tasks: number; time: string; cost: string; findings: number }
  findings: string[]
  recommendations: string[]
}

const AGENT_DATA: AgentData[] = [
  {
    id: 'product',
    name: 'PRODUCT + MARKETING',
    role: 'Market research, competitive analysis & go-to-market strategy',
    color: '#F59E0B',
    metrics: { tasks: 14, time: '6:18', cost: '$243', findings: 11 },
    findings: [
      'Target market estimated at $2.4B with 23% YoY growth concentrated in the SMB segment',
      'Primary competitor gap: no current solution offers real-time multi-agent coordination at this price point',
      'Early adopter persona: Series A–B startups (20–80 employees) actively replacing manual workflows',
      'Recommended positioning: "AI-native operations layer" outperforms "automation tool" in messaging tests',
    ],
    recommendations: [
      'Launch with a freemium tier capped at 3 agents to reduce adoption friction significantly',
      'Prioritize integrations with Linear, Notion, and Slack for the initial product launch',
      'Content strategy: behind-the-scenes build journey resonates strongly with the ICP on LinkedIn',
    ],
  },
  {
    id: 'tech',
    name: 'TECH',
    role: 'Architecture decisions, tech stack & implementation planning',
    color: '#10B981',
    metrics: { tasks: 18, time: '8:44', cost: '$318', findings: 9 },
    findings: [
      'FastAPI + WebSocket architecture supports sub-200ms agent response latency at production scale',
      'Vector DB (Pinecone) outperforms pgvector for semantic search on agent memory above 10k entries',
      'Multi-agent orchestration layer needs circuit-breaker pattern to prevent cascade failures under load',
      'TypeScript strict mode adoption reduces runtime errors by ~40% based on comparable production codebases',
    ],
    recommendations: [
      'Implement Redis pub/sub for agent-to-agent messaging before WebSocket connections exceed 1k concurrent',
      'Adopt trunk-based development with feature flags to enable daily deployments safely',
      'Prioritize observability (traces, metrics, logs) before scaling past 100 active simulations',
    ],
  },
  {
    id: 'ops',
    name: 'OPERATIONS',
    role: 'Workflow optimization, resource allocation & process design',
    color: '#8B5CF6',
    metrics: { tasks: 11, time: '4:52', cost: '$178', findings: 7 },
    findings: [
      'Agent idle time averages 34% — primary bottleneck is sequential handoff rather than compute limits',
      'Approval gate latency is the highest variable cost driver across all measured simulation runs',
      'Most efficient configurations use parallel task execution across product and tech agents simultaneously',
      'Human-in-the-loop interventions correlate with 28% higher output quality scores across all runs',
    ],
    recommendations: [
      'Introduce async approval queues to eliminate blocking on non-critical CEO decisions',
      'Build agent performance dashboards before onboarding the first enterprise customers',
      'Define SLAs per agent role to set expectations and enable SLA-based enterprise pricing tiers',
    ],
  },
  {
    id: 'finance',
    name: 'FINANCE',
    role: 'Budget analysis, cost projections & financial modeling',
    color: '#EF4444',
    metrics: { tasks: 9, time: '3:27', cost: '$134', findings: 6 },
    findings: [
      'Blended LLM cost per simulation run averages $0.87 — favorable unit economics for the $29/mo entry tier',
      'Break-even at 340 paying customers given current infrastructure cost structure and burn rate',
      'GPU inference costs projected to fall 60% over the next 18 months based on current market trajectory',
      'Enterprise tier ($499/mo) required to sustain R&D velocity without raising additional capital',
    ],
    recommendations: [
      'Implement per-agent cost caps to prevent runaway spend on complex simulation runs',
      'Negotiate annual prepay discounts with LLM providers before reaching $10k/month in spend',
      'Model a usage-based pricing option — it converts 22% better in PLG SaaS at this growth stage',
    ],
  },
]

// ─── Corner bracket ───────────────────────────────────────────────────────────
function Corner({
  pos, color, size = 12, offset = 0,
}: { pos: 'tl' | 'tr' | 'bl' | 'br'; color: string; size?: number; offset?: number }) {
  const top  = pos === 'tl' || pos === 'tr'
  const left = pos === 'tl' || pos === 'bl'
  return (
    <div
      style={{
        position: 'absolute',
        width: size, height: size,
        top:    top  ? offset  : undefined,
        bottom: !top ? offset  : undefined,
        left:   left  ? offset : undefined,
        right:  !left ? offset : undefined,
        borderTop:    top    ? `1px solid ${color}` : undefined,
        borderBottom: !top   ? `1px solid ${color}` : undefined,
        borderLeft:   left   ? `1px solid ${color}` : undefined,
        borderRight:  !left  ? `1px solid ${color}` : undefined,
        pointerEvents: 'none',
        zIndex: 2,
      }}
    />
  )
}

// ─── Carousel card ────────────────────────────────────────────────────────────
function CarouselCard({ agent, offset, onClick }: { agent: AgentData; offset: number; onClick: () => void }) {
  const isActive = offset === 0

  const positions: Record<number, React.CSSProperties> = {
    0: { transform: 'translateZ(200px) translateX(0px) scale(1)',                         opacity: 1,    zIndex: 4, filter: 'brightness(1)' },
    1: { transform: 'translateZ(-50px) translateX(280px) scale(0.75) rotateY(-15deg)',    opacity: 0.6,  zIndex: 2, filter: 'brightness(0.5)' },
    2: { transform: 'translateZ(-200px) translateX(0px) scale(0.6)',                      opacity: 0.25, zIndex: 1, filter: 'brightness(0.3)' },
    3: { transform: 'translateZ(-50px) translateX(-280px) scale(0.75) rotateY(15deg)',    opacity: 0.6,  zIndex: 2, filter: 'brightness(0.5)' },
  }

  return (
    <div
      onClick={onClick}
      style={{
        position: 'absolute',
        top: '50%', left: '50%',
        marginLeft: -140, marginTop: -170,
        width: 280, height: 340,
        cursor: 'pointer',
        transition: 'all 0.7s cubic-bezier(0.25, 0.1, 0.25, 1)',
        willChange: 'transform, opacity',
        background: isActive
          ? `linear-gradient(180deg, rgba(10,15,30,0.92) 50%, rgba(${hexToRgbStr(agent.color)}, 0.08) 100%)`
          : 'rgba(10, 15, 30, 0.92)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: `1px solid ${agent.color}${isActive ? '55' : '22'}`,
        boxShadow: isActive
          ? `0 0 40px ${agent.color}30, 0 0 80px ${agent.color}14, inset 0 0 20px ${agent.color}08`
          : 'none',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 12,
        padding: '20px 20px',
        ...(positions[offset] ?? positions[2]),
      }}
    >
      <Corner pos="tl" color={`${agent.color}${isActive ? 'cc' : '55'}`} size={14} />
      <Corner pos="tr" color={`${agent.color}${isActive ? 'cc' : '55'}`} size={14} />
      <Corner pos="bl" color={`${agent.color}${isActive ? 'cc' : '55'}`} size={14} />
      <Corner pos="br" color={`${agent.color}${isActive ? 'cc' : '55'}`} size={14} />

      {/* 3D Agent Shape */}
      <div style={{
        width: 120, height: 120,
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        position: 'relative',
      }}>
        <AgentShape agentId={agent.id} state={isActive ? 'thinking' : 'idle'} size={120} bloom={false} />
      </div>

      {/* Name */}
      <div style={{ fontFamily: "'Space Mono', monospace", fontWeight: 700, fontSize: 11, color: isActive ? '#F0F4FF' : '#8B95A5', letterSpacing: '0.12em', textTransform: 'uppercase', textAlign: 'center', lineHeight: 1.4 }}>
        {agent.name}
      </div>

      {/* Role */}
      <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 10, color: '#5A6474', textAlign: 'center', lineHeight: 1.5, padding: '0 8px' }}>
        {agent.role}
      </div>

      {/* Mini metrics */}
      <div style={{ display: 'flex', gap: 8, width: '100%' }}>
        {[{ label: 'TASKS', value: agent.metrics.tasks }, { label: 'FINDINGS', value: agent.metrics.findings }].map(m => (
          <div key={m.label} style={{ flex: 1, background: `${agent.color}0a`, border: `1px solid ${agent.color}20`, padding: '8px 4px', textAlign: 'center' }}>
            <div style={{ fontFamily: "'VT323', monospace", fontSize: 22, color: agent.color, lineHeight: 1 }}>{m.value}</div>
            <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 8, color: '#4A5568', letterSpacing: '0.1em', marginTop: 2 }}>{m.label}</div>
          </div>
        ))}
      </div>

      {/* Bottom accent line */}
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, transparent, ${agent.color}${isActive ? 'cc' : '44'}, transparent)` }} />
    </div>
  )
}

// ─── Hex to RGB string helper ──────────────────────────────────────────────────
function hexToRgbStr(hex: string): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `${r}, ${g}, ${b}`
}

// ─── Main page ────────────────────────────────────────────────────────────────
export function ProjectSummaryPage() {
  const navigate                  = useNavigate()
  const { state }                 = useSimulation()
  const { isMuted, setIsMuted }   = useAudioPlayer()

  const [activeIndex, setActiveIndex] = useState(0)
  const [panelIndex,  setPanelIndex]  = useState(0)
  const [panelFading, setPanelFading] = useState(false)

  const handleChange = (newIndex: number) => {
    if (newIndex === activeIndex) return
    setActiveIndex(newIndex)
    setPanelFading(true)
    setTimeout(() => {
      setPanelIndex(newIndex)
      setPanelFading(false)
    }, 220)
  }

  const agent = AGENT_DATA[panelIndex]

  return (
    <div style={{ minHeight: '100vh', background: '#05050a', display: 'flex', flexDirection: 'column', position: 'relative' }}>

      {/* LetterGlitch fixed background */}
      <div style={{ position: 'fixed', inset: 0, zIndex: 0, opacity: 0.18, pointerEvents: 'none' }}>
        <LetterGlitch glitchSpeed={50} centerVignette outerVignette smooth />
      </div>

      {/* Center-darkening overlay — keeps glitch visible on edges/header, subdued behind content */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
        background: 'radial-gradient(ellipse 60% 70% at 50% 45%, rgba(8,12,24,0.72) 0%, transparent 100%)',
      }} />

      {/* Navbar */}
      <div style={{ position: 'sticky', top: 0, zIndex: 20 }}>
        <StatusBar isMuted={isMuted} onToggleMute={() => setIsMuted(!isMuted)} onStop={() => navigate('/')} />
      </div>

      {/* Scrollable content */}
      <div style={{ position: 'relative', zIndex: 1, flex: 1, overflowY: 'auto' }}>

        {/* Back */}
        <div style={{ padding: '16px 24px' }}>
          <button
            onClick={() => navigate('/simulation')}
            style={{ fontFamily: "'Space Mono', monospace", fontSize: 11, color: '#5A6A7A', background: 'none', border: 'none', cursor: 'pointer', letterSpacing: '0.1em', textTransform: 'uppercase', transition: 'color 0.2s, transform 0.2s', padding: 0, display: 'inline-block' }}
            onMouseEnter={e => {
              const el = e.currentTarget as HTMLButtonElement
              el.style.color     = '#4AE8C0'
              el.style.transform = 'translateX(-4px)'
            }}
            onMouseLeave={e => {
              const el = e.currentTarget as HTMLButtonElement
              el.style.color     = '#5A6A7A'
              el.style.transform = 'translateX(0)'
            }}
          >
            ← BACK TO DASHBOARD
          </button>
        </div>

        {/* Hero */}
        <div style={{ textAlign: 'center', paddingBottom: 48 }}>
          <div
            style={{
              fontFamily: "'Orbitron', sans-serif",
              fontWeight: 900,
              fontSize: 'clamp(48px, 7vw, 72px)',
              letterSpacing: '0.3em',
              lineHeight: 1,
              marginBottom: 12,
              background: 'linear-gradient(90deg, #7ECFDF 0%, #5CE0D0 25%, #3DE8E0 50%, #20E8D0 75%, #00F0C8 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              animation: 'titleGlow 4s ease-in-out infinite',
            }}
          >
            NEXUS
          </div>
          <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 13, letterSpacing: '0.25em', color: '#6B7A8A', textTransform: 'uppercase', marginBottom: 6 }}>
            PROJECT SUMMARY
          </div>
          {state.mission && (
            <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 13, color: '#4AE8C0', letterSpacing: '0.1em', opacity: 0.85 }}>
              // {state.mission}
            </div>
          )}
        </div>

        {/* 3D Carousel */}
        <div style={{ width: '100%', maxWidth: 900, margin: '0 auto', padding: '0 24px', position: 'relative', display: 'flex', alignItems: 'center', gap: 8 }}>

          {/* Left arrow */}
          <button
            onClick={() => handleChange((activeIndex - 1 + AGENT_DATA.length) % AGENT_DATA.length)}
            style={{
              flexShrink: 0, background: 'rgba(100,200,255,0.06)', border: '1px solid rgba(100,200,255,0.12)',
              cursor: 'pointer', padding: '12px 16px', color: 'rgba(100,200,255,0.4)',
              transition: 'all 0.2s', fontSize: 32, lineHeight: 1, fontFamily: 'sans-serif',
              borderRadius: 4,
            }}
            onMouseEnter={e => {
              const el = e.currentTarget as HTMLButtonElement
              el.style.color       = '#FFFFFF'
              el.style.background  = 'rgba(100,200,255,0.12)'
              el.style.borderColor = 'rgba(100,200,255,0.3)'
            }}
            onMouseLeave={e => {
              const el = e.currentTarget as HTMLButtonElement
              el.style.color       = 'rgba(100,200,255,0.4)'
              el.style.background  = 'rgba(100,200,255,0.06)'
              el.style.borderColor = 'rgba(100,200,255,0.12)'
            }}
          >
            ‹
          </button>

          {/* Carousel viewport */}
          <div style={{ flex: 1, height: 380, position: 'relative', perspective: '1200px' }}>
            <div style={{ width: '100%', height: '100%', position: 'relative', transformStyle: 'preserve-3d' }}>
              {AGENT_DATA.map((ag, i) => {
                const total  = AGENT_DATA.length
                const offset = ((i - activeIndex) % total + total) % total
                return (
                  <CarouselCard key={ag.id} agent={ag} offset={offset} onClick={() => handleChange(i)} />
                )
              })}
            </div>
          </div>

          {/* Right arrow */}
          <button
            onClick={() => handleChange((activeIndex + 1) % AGENT_DATA.length)}
            style={{
              flexShrink: 0, background: 'rgba(100,200,255,0.06)', border: '1px solid rgba(100,200,255,0.12)',
              cursor: 'pointer', padding: '12px 16px', color: 'rgba(100,200,255,0.4)',
              transition: 'all 0.2s', fontSize: 32, lineHeight: 1, fontFamily: 'sans-serif',
              borderRadius: 4,
            }}
            onMouseEnter={e => {
              const el = e.currentTarget as HTMLButtonElement
              el.style.color       = '#FFFFFF'
              el.style.background  = 'rgba(100,200,255,0.12)'
              el.style.borderColor = 'rgba(100,200,255,0.3)'
            }}
            onMouseLeave={e => {
              const el = e.currentTarget as HTMLButtonElement
              el.style.color       = 'rgba(100,200,255,0.4)'
              el.style.background  = 'rgba(100,200,255,0.06)'
              el.style.borderColor = 'rgba(100,200,255,0.12)'
            }}
          >
            ›
          </button>
        </div>

        {/* Dot indicators */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 20 }}>
          {AGENT_DATA.map((ag, i) => (
            <button
              key={ag.id}
              onClick={() => handleChange(i)}
              style={{
                width: i === activeIndex ? 24 : 8,
                height: 8,
                borderRadius: 4,
                border: 'none', cursor: 'pointer', padding: 0,
                background: i === activeIndex ? ag.color : 'rgba(100, 200, 255, 0.15)',
                boxShadow: i === activeIndex ? `0 0 10px ${ag.color}88` : 'none',
                transition: 'all 0.3s ease',
              }}
            />
          ))}
        </div>

        {/* Summary panel */}
        <div style={{ maxWidth: 800, margin: '32px auto 60px', padding: '0 24px' }}>
          <div
            style={{
              position: 'relative',
              padding: 32,
              background: 'rgba(10, 15, 30, 0.85)',
              backdropFilter: 'blur(16px)',
              WebkitBackdropFilter: 'blur(16px)',
              border: `1px solid ${agent.color}18`,
              borderTop: `1px solid ${agent.color}44`,
              opacity: panelFading ? 0 : 1,
              transform: panelFading ? 'translateY(10px)' : 'translateY(0)',
              transition: 'opacity 0.2s ease, transform 0.2s ease',
            }}
          >
            <Corner pos="tl" color={`${agent.color}88`} size={16} />
            <Corner pos="tr" color={`${agent.color}88`} size={16} />
            <Corner pos="bl" color={`${agent.color}44`} size={16} />
            <Corner pos="br" color={`${agent.color}44`} size={16} />

            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24, gap: 16 }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: agent.color, boxShadow: `0 0 8px ${agent.color}88`, flexShrink: 0 }} />
                  <span style={{ fontFamily: "'Space Mono', monospace", fontWeight: 700, fontSize: 16, color: '#F0F4FF', letterSpacing: '0.1em' }}>
                    {agent.name}
                  </span>
                </div>
                <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 12, color: '#5A6474', paddingLeft: 18 }}>
                  {agent.role}
                </div>
              </div>
              <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 9, letterSpacing: '0.15em', color: '#34d399', border: '1px solid rgba(52,211,153,0.35)', padding: '4px 10px', flexShrink: 0 }}>
                COMPLETE
              </div>
            </div>

            {/* Metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 28 }}>
              {[
                { label: 'TASKS',    value: String(agent.metrics.tasks) },
                { label: 'TIME',     value: agent.metrics.time },
                { label: 'COST',     value: agent.metrics.cost },
                { label: 'FINDINGS', value: String(agent.metrics.findings) },
              ].map(m => (
                <div key={m.label} style={{ background: `${agent.color}06`, border: `1px solid ${agent.color}18`, padding: '16px 12px', textAlign: 'center' }}>
                  <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 9, color: '#6B7A8A', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: 8 }}>{m.label}</div>
                  <div style={{ fontFamily: "'VT323', monospace", fontSize: 28, color: agent.color, lineHeight: 1, textShadow: `0 0 12px ${agent.color}55` }}>{m.value}</div>
                </div>
              ))}
            </div>

            {/* Key findings */}
            <div style={{ marginBottom: 28 }}>
              <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 9, color: agent.color, letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 16, borderBottom: `1px solid ${agent.color}20`, paddingBottom: 8, opacity: 0.7 }}>
                KEY FINDINGS
              </div>
              {agent.findings.map((finding, i) => (
                <div key={i} style={{ display: 'flex', gap: 16, padding: '12px 0', borderBottom: '1px solid rgba(100, 200, 255, 0.04)' }}>
                  <span style={{ fontFamily: "'VT323', monospace", fontSize: 20, color: agent.color, lineHeight: 1.4, flexShrink: 0, minWidth: 24 }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 13, color: '#C0C8D4', lineHeight: 1.6 }}>
                    {finding}
                  </span>
                </div>
              ))}
            </div>

            {/* Recommendations */}
            <div>
              <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 9, color: agent.color, letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 16, borderBottom: `1px solid ${agent.color}20`, paddingBottom: 8, opacity: 0.7 }}>
                RECOMMENDATIONS
              </div>
              {agent.recommendations.map((rec, i) => (
                <div key={i} style={{ display: 'flex', gap: 16, padding: '12px 0', borderBottom: '1px solid rgba(100, 200, 255, 0.04)' }}>
                  <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 14, color: agent.color, lineHeight: 1.4, flexShrink: 0 }}>→</span>
                  <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 13, color: '#D0D8E4', lineHeight: 1.6 }}>{rec}</span>
                </div>
              ))}
            </div>

            {/* Agent accent line */}
            <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 1, background: `linear-gradient(90deg, transparent, ${agent.color}66, transparent)`, transition: 'background 0.3s ease' }} />
          </div>
        </div>
      </div>

      {/* Title glow keyframes — uses filter: drop-shadow for gradient text */}
      <style>{`
        @keyframes titleGlow {
          0%, 100% { filter: drop-shadow(0 0 18px rgba(0,240,200,0.35)) drop-shadow(0 0 40px rgba(0,240,200,0.15)); }
          50%       { filter: drop-shadow(0 0 28px rgba(0,240,200,0.55)) drop-shadow(0 0 60px rgba(0,240,200,0.25)); }
        }
      `}</style>
    </div>
  )
}
