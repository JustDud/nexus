import { useEffect, useRef } from 'react'
import { useSimulation } from '../context/SimulationContext'
import { type AgentId } from '../types'

interface SimEvent {
  at: number // seconds from start
  fn: () => void
}

export function useMockSimulation(enabled: boolean) {
  const {
    state,
    setStage,
    setRunning,
    setAgentStatus,
    setAgentThought,
    clearAgentThought,
    addActivity,
    addTransaction,
  } = useSimulation()

  const startedRef = useRef(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const elapsed = useRef(0)
  const eventsRef = useRef<SimEvent[]>([])

  const emit = (
    agentId: AgentId,
    message: string,
    type: 'thought' | 'action' | 'block' | 'complete'
  ) => {
    addActivity({ agentId, message, timestamp: Date.now(), type })
  }

  const think = (agentId: AgentId, fragments: string[]) => {
    setAgentStatus(agentId, 'thinking')
    setAgentThought(agentId, fragments)
    emit(agentId, fragments[fragments.length - 1] ?? '...', 'thought')
  }

  const act = (agentId: AgentId, description: string, amount: number, blocked = false) => {
    setAgentStatus(agentId, blocked ? 'blocked' : 'acting')
    clearAgentThought(agentId)
    const status = blocked ? 'blocked' : 'approved'
    addTransaction({
      agentId,
      description,
      amount,
      status,
      timestamp: Date.now(),
    })
    emit(agentId, `${blocked ? 'BLOCKED' : '✓'} ${description}${amount > 0 ? ` — $${amount}` : ''}`, blocked ? 'block' : 'action')
    setTimeout(() => setAgentStatus(agentId, 'idle'), 1500)
  }

  const complete = (agentId: AgentId, summary: string) => {
    setAgentStatus(agentId, 'complete')
    clearAgentThought(agentId)
    emit(agentId, summary, 'complete')
  }

  useEffect(() => {
    if (!enabled || startedRef.current) return
    startedRef.current = true

    const budget = state.totalBudget

    // Build event timeline
    eventsRef.current = [
      // t=1 — RESEARCHING kicks off
      { at: 1, fn: () => setStage('researching') },
      {
        at: 2, fn: () => think('product', [
          'analysing market landscape...',
          `total addressable market: $4.2B`,
          'ICP: SMBs with <50 employees',
          'top competitors: 3 main players, fragmented market',
        ])
      },
      {
        at: 3, fn: () => think('tech', [
          'scanning tech stack requirements...',
          'API-first architecture recommended',
          'estimated infra cost: $40/mo on free tier',
        ])
      },
      {
        at: 4, fn: () => think('finance', [
          `total budget: $${budget}`,
          'setting burn rate targets...',
          'max single spend: $200',
        ])
      },
      {
        at: 5, fn: () => think('ops', [
          'checking compliance requirements...',
          'GDPR relevant — data processing agreement needed',
          'estimated legal cost: $50',
        ])
      },
      { at: 6, fn: () => act('product', 'Market research dataset pull — SEMrush', 80) },
      { at: 7, fn: () => act('ops', 'Legal entity check — Companies House API', 0) },
      {
        at: 8, fn: () => think('tech', [
          'evaluating stack: Next.js + Supabase',
          'free tier covers 0–500 users',
          'CI/CD: GitHub Actions — free',
        ])
      },

      // t=10 — PLANNING
      { at: 10, fn: () => setStage('planning') },
      {
        at: 11, fn: () => think('product', [
          'defining MVP scope...',
          'feature 1: core symptom checker',
          'feature 2: user onboarding flow',
          'feature 3: email digest',
          'trimming: no mobile app in v1',
        ])
      },
      { at: 12, fn: () => act('product', 'Domain registered — startupcheck.io', 12) },
      {
        at: 13, fn: () => think('finance', [
          '$92 spent so far',
          `${Math.round(((budget - 92) / budget) * 100)}% budget remaining`,
          'flagging: ad spend request incoming...',
        ])
      },
      {
        at: 15, fn: () => think('product', [
          'proposing ad campaign — Instagram + Google',
          'budget ask: $300',
        ])
      },
      {
        at: 16, fn: () => {
          // Finance blocks the big ad request
          setAgentStatus('finance', 'blocked')
          emit('finance', 'BLOCKED: Ad campaign $300 — exceeds single-spend limit', 'block')
          addTransaction({
            agentId: 'finance',
            description: 'Ad campaign $300 — exceeds single-spend limit',
            amount: 300,
            status: 'blocked',
            timestamp: Date.now(),
          })
          setTimeout(() => setAgentStatus('finance', 'idle'), 2000)
        }
      },
      {
        at: 17, fn: () => think('product', [
          'finance blocked $300 ads...',
          'adjusting: split campaign — $100 now, scale later',
        ])
      },
      { at: 18, fn: () => act('product', 'Instagram ad campaign — Phase 1', 100) },
      { at: 19, fn: () => act('ops', 'Vendor contract — design agency Figma file', 0) },

      // t=25 — BUILDING
      { at: 25, fn: () => setStage('building') },
      {
        at: 26, fn: () => think('tech', [
          'scaffolding Next.js project...',
          'initialising Supabase schema',
          'auth: magic link via Resend — free tier',
          'estimated deploy time: 4 hours',
        ])
      },
      { at: 27, fn: () => act('tech', 'GitHub repo + CI pipeline', 0) },
      { at: 28, fn: () => act('tech', 'Supabase project provisioned', 0) },
      {
        at: 30, fn: () => think('ops', [
          'preparing SLA with design vendor...',
          'compliance: Privacy Policy generated',
          'cookie banner: implemented via Cookiebot free tier',
        ])
      },
      { at: 31, fn: () => act('ops', 'Privacy policy + cookie consent live', 0) },
      {
        at: 33, fn: () => think('tech', [
          'MVP features: 3/3 implemented',
          'running Lighthouse audit...',
          'performance: 94, a11y: 89',
          'fixing: aria-label on CTAs',
        ])
      },
      { at: 35, fn: () => act('tech', 'MVP deployed to Vercel — free tier', 0) },
      { at: 36, fn: () => act('product', 'Landing page copy + hero image', 45) },
      {
        at: 38, fn: () => think('finance', [
          `$249 spent of $${budget}`,
          `burn rate: $3.2/min`,
          'on track — 75% budget remaining',
        ])
      },

      // t=45 — approaching danger depending on budget
      {
        at: 45, fn: () => {
          const highSpend = budget < 600
          if (highSpend) {
            think('finance', [
              'WARNING: approaching 30% threshold',
              'recommend halting discretionary spend',
            ])
          }
        }
      },

      // t=50 — DEPLOYING
      { at: 50, fn: () => setStage('deploying') },
      {
        at: 51, fn: () => think('ops', [
          'running pre-launch checklist...',
          'SSL: ✓  DNS: ✓  Backups: ✓',
          'GDPR consent flow: ✓',
          'uptime monitor: Freshping free tier',
        ])
      },
      { at: 52, fn: () => act('ops', 'Uptime monitoring configured', 0) },
      {
        at: 54, fn: () => think('tech', [
          'setting up error tracking — Sentry free tier',
          'logging: Logtail free tier',
          'alerts: PagerDuty — free for 1 user',
        ])
      },
      { at: 55, fn: () => act('tech', 'Sentry + Logtail error tracking', 0) },
      { at: 56, fn: () => act('product', 'Email waitlist campaign — Mailchimp', 29) },
      {
        at: 58, fn: () => think('product', [
          'waitlist: 0 signups so far',
          'launching social posts...',
          'Twitter/X thread: scheduled',
          'LinkedIn post: scheduled',
          'HN "Show HN": drafting...',
        ])
      },
      { at: 60, fn: () => act('product', 'Social media launch posts', 0) },
      {
        at: 62, fn: () => think('finance', [
          `$282 of $${budget} spent`,
          `${Math.round(((budget - 282) / budget) * 100)}% remaining`,
          'burn rate slowing — runway healthy',
        ])
      },

      // t=70 — final sprint
      { at: 70, fn: () => act('ops', 'Customer support Crisp.chat widget — free', 0) },
      { at: 71, fn: () => act('product', 'Product Hunt launch listing — free', 0) },
      {
        at: 73, fn: () => think('tech', [
          'post-launch: 12 users onboarded',
          'no critical errors in Sentry',
          'DB queries avg 42ms — healthy',
          'next sprint: mobile PWA wrapper',
        ])
      },
      { at: 75, fn: () => act('tech', 'Performance monitoring dashboard', 0) },

      // t=80 — wrap up
      { at: 80, fn: () => complete('ops', 'All operations complete — compliance verified') },
      { at: 82, fn: () => complete('tech', 'MVP live — 12 users, 0 critical errors') },
      { at: 84, fn: () => complete('product', 'Launch complete — waitlist active, ads running') },
      { at: 86, fn: () => complete('finance', `Final spend: $${Math.min(282, budget)} of $${budget} — ${Math.round(((budget - Math.min(282, budget)) / budget) * 100)}% runway remaining`) },
      { at: 88, fn: () => setStage('complete') },
    ]

    setRunning(true)

    timerRef.current = setInterval(() => {
      elapsed.current += 1

      const due = eventsRef.current.filter((e) => e.at === elapsed.current)
      due.forEach((e) => e.fn())

      if (elapsed.current >= 90) {
        if (timerRef.current) clearInterval(timerRef.current)
        setRunning(false)
      }
    }, 1000)

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [enabled]) // eslint-disable-line react-hooks/exhaustive-deps
}
