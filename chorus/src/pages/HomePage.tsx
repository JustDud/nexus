import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { FileText, Upload } from 'lucide-react'
import { useSimulation } from '../context/SimulationContext'
import { formatCurrency } from '../lib/utils'
import Dither from '../components/home/Dither/Dither'

const MIN_BUDGET = 500
const MAX_BUDGET = 5000

export function HomePage() {
  const { setMission } = useSimulation()
  const navigate = useNavigate()

  const [idea, setIdea] = useState('')
  const [budget, setBudget] = useState(1000)
  const [file, setFile] = useState<{ name: string; content: string } | null>(null)
  const [isDragFlash, setIsDragFlash] = useState(false)
  const [isLaunching, setIsLaunching] = useState(false)

  const onDrop = useCallback((accepted: File[]) => {
    const f = accepted[0]
    if (!f) return
    const reader = new FileReader()
    reader.onload = (e) => {
      setFile({ name: f.name, content: e.target?.result as string })
      setIsDragFlash(true)
      setTimeout(() => setIsDragFlash(false), 600)
    }
    reader.readAsText(f)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/plain': ['.txt'], 'text/markdown': ['.md'], 'application/pdf': ['.pdf'] },
    maxFiles: 1,
  })

  const handleLaunch = () => {
    if (!idea.trim() || isLaunching) return
    setIsLaunching(true)
    setMission(idea.trim(), budget, file?.content ?? null)
    setTimeout(() => navigate('/simulation'), 900)
  }

  const budgetPct = ((budget - MIN_BUDGET) / (MAX_BUDGET - MIN_BUDGET)) * 100

  return (
    <div
      style={{
        position: 'relative',
        minHeight: '100vh',
        background: '#080810',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '32px 16px',
      }}
    >
      {/* Dither background */}
      <motion.div
        style={{ position: 'absolute', inset: 0, zIndex: 0 }}
        animate={isLaunching ? { scale: 1.08 } : { scale: 1 }}
        transition={{ duration: 0.9, ease: [0.4, 0, 1, 1] }}
      >
        <Dither
          waveColor={[0.23, 0.51, 0.96]}
          colorNum={4}
          pixelSize={4}
          waveSpeed={0.8}
          waveFrequency={5}
          waveAmplitude={0.28}
          enableMouseInteraction={true}
          mouseRadius={0.3}
        />
      </motion.div>

      {/* Glassmorphism card */}
      <motion.div
        initial={{ opacity: 0, y: 32 }}
        animate={
          isLaunching
            ? { opacity: 0, y: -20, scale: 0.97 }
            : { opacity: 1, y: 0, scale: 1 }
        }
        transition={
          isLaunching
            ? { duration: 0.4, ease: 'easeIn' }
            : { duration: 0.7, delay: 0.1, ease: 'easeOut' }
        }
        style={{
          position: 'relative',
          zIndex: 1,
          width: '100%',
          maxWidth: 780,
          background: 'rgba(8,8,16,0.78)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid rgba(59,130,246,0.22)',
          padding: '40px 40px 32px',
        }}
      >
        {/* Header */}
        <div style={{ marginBottom: 28, textAlign: 'center' }}>
          <div
            style={{
              fontFamily: "'Orbitron', sans-serif",
              fontWeight: 900,
              fontSize: 'clamp(42px, 8vw, 68px)',
              color: '#f8fafc',
              letterSpacing: '-0.02em',
              lineHeight: 1,
              marginBottom: 10,
            }}
          >
            NEXUS
          </div>
          <div
            style={{
              fontFamily: "'Share Tech Mono', monospace",
              fontSize: 12,
              color: 'rgba(100,116,139,0.85)',
              letterSpacing: '0.22em',
              textTransform: 'uppercase',
            }}
          >
            autonomous multi-agent startup simulator
          </div>
        </div>

        {/* Textarea */}
        <textarea
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          placeholder="describe your startup idea..."
          rows={3}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = 'rgba(59,130,246,0.55)'
            e.currentTarget.style.boxShadow = '0 0 0 1px rgba(59,130,246,0.18), 0 0 18px rgba(59,130,246,0.08)'
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = 'rgba(59,130,246,0.15)'
            e.currentTarget.style.boxShadow = 'none'
          }}
          style={{
            display: 'block',
            width: '100%',
            minHeight: 82,
            background: 'rgba(0,0,8,0.5)',
            border: '1px solid rgba(59,130,246,0.15)',
            padding: '12px 16px',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 14,
            color: '#f8fafc',
            resize: 'vertical',
            outline: 'none',
            boxSizing: 'border-box',
            marginBottom: 16,
            transition: 'border-color 200ms, box-shadow 200ms',
            lineHeight: 1.6,
          }}
        />

        {/* Bottom 3-col grid: dropzone | budget slider | launch */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr auto',
            gap: 14,
            alignItems: 'stretch',
          }}
        >
          {/* Dropzone */}
          <div
            {...getRootProps()}
            style={{
              border: `1px dashed ${
                isDragFlash
                  ? 'rgba(34,197,94,0.7)'
                  : isDragActive
                  ? 'rgba(59,130,246,0.7)'
                  : 'rgba(59,130,246,0.22)'
              }`,
              background: isDragFlash
                ? 'rgba(34,197,94,0.05)'
                : isDragActive
                ? 'rgba(59,130,246,0.06)'
                : 'rgba(0,0,8,0.35)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 6,
              padding: '14px 10px',
              minHeight: 80,
              transition: 'border-color 150ms, background 150ms',
            }}
          >
            <input {...getInputProps()} />
            {file ? (
              <>
                <FileText size={15} color="#22c55e" />
                <span
                  style={{
                    fontFamily: "'Space Mono', monospace",
                    fontSize: 9,
                    color: '#22c55e',
                    letterSpacing: '0.08em',
                    textAlign: 'center',
                    wordBreak: 'break-all',
                    lineHeight: 1.3,
                  }}
                >
                  {file.name}
                </span>
              </>
            ) : (
              <>
                <Upload size={15} color="rgba(100,116,139,0.6)" />
                <span
                  style={{
                    fontFamily: "'Space Mono', monospace",
                    fontSize: 9,
                    color: 'rgba(100,116,139,0.6)',
                    letterSpacing: '0.1em',
                    textAlign: 'center',
                  }}
                >
                  {isDragActive ? 'DROP' : '.txt  .md  .pdf'}
                </span>
              </>
            )}
          </div>

          {/* Budget slider */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              gap: 10,
              padding: '12px 4px',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'baseline',
              }}
            >
              <span
                style={{
                  fontFamily: "'Space Mono', monospace",
                  fontSize: 9,
                  color: 'rgba(100,116,139,0.65)',
                  letterSpacing: '0.18em',
                  textTransform: 'uppercase',
                }}
              >
                BUDGET
              </span>
              <span
                style={{
                  fontFamily: "'VT323', monospace",
                  fontSize: 24,
                  color: '#3b82f6',
                  lineHeight: 1,
                }}
              >
                {formatCurrency(budget)}
              </span>
            </div>

            {/* Slider track */}
            <div style={{ position: 'relative' }}>
              <div
                style={{
                  height: 3,
                  background: 'rgba(59,130,246,0.1)',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${budgetPct}%`,
                    background: 'linear-gradient(90deg, #1d4ed8, #3b82f6)',
                    transition: 'width 100ms',
                  }}
                />
              </div>
              <input
                type="range"
                min={MIN_BUDGET}
                max={MAX_BUDGET}
                step={100}
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                style={{
                  position: 'absolute',
                  inset: 0,
                  width: '100%',
                  height: '100%',
                  opacity: 0,
                  cursor: 'pointer',
                  margin: 0,
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 8, color: 'rgba(100,116,139,0.4)' }}>
                $500
              </span>
              <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 8, color: 'rgba(100,116,139,0.4)' }}>
                $5k
              </span>
            </div>
          </div>

          {/* Launch button */}
          <motion.button
            onClick={handleLaunch}
            disabled={!idea.trim() || isLaunching}
            whileHover={idea.trim() && !isLaunching ? { scale: 1.03 } : {}}
            whileTap={idea.trim() && !isLaunching ? { scale: 0.97 } : {}}
            style={{
              fontFamily: "'Orbitron', sans-serif",
              fontWeight: 700,
              fontSize: 11,
              letterSpacing: '0.12em',
              color: idea.trim() && !isLaunching ? '#f8fafc' : 'rgba(100,116,139,0.4)',
              background:
                idea.trim() && !isLaunching
                  ? 'rgba(59,130,246,0.14)'
                  : 'rgba(0,0,0,0.2)',
              border: `1px solid ${
                idea.trim() && !isLaunching
                  ? 'rgba(59,130,246,0.45)'
                  : 'rgba(100,116,139,0.15)'
              }`,
              padding: '0 28px',
              minWidth: 130,
              cursor: idea.trim() && !isLaunching ? 'pointer' : 'not-allowed',
              height: '100%',
              minHeight: 80,
              whiteSpace: 'nowrap',
              transition: 'all 180ms',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {isLaunching ? 'LAUNCHING...' : 'LAUNCH →'}
          </motion.button>
        </div>
      </motion.div>
    </div>
  )
}
