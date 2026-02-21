import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, Zap, Loader2 } from 'lucide-react'
import { useSimulation } from '../../context/SimulationContext'
import { GlassPanel } from '../shared/GlassPanel'
import { formatCurrency } from '../../lib/utils'

const MIN_BUDGET = 500
const MAX_BUDGET = 5000

export function MissionInput() {
  const { setMission } = useSimulation()
  const navigate = useNavigate()

  const [idea, setIdea] = useState('')
  const [budget, setBudget] = useState(1000)
  const [file, setFile] = useState<{ name: string; content: string } | null>(null)
  const [dropFlash, setDropFlash] = useState(false)
  const [loading, setLoading] = useState(false)

  const onDrop = useCallback((accepted: File[]) => {
    const f = accepted[0]
    if (!f) return
    const reader = new FileReader()
    reader.onload = (e) => {
      setFile({ name: f.name, content: e.target?.result as string })
      setDropFlash(true)
      setTimeout(() => setDropFlash(false), 800)
    }
    reader.readAsText(f)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/plain': ['.txt'], 'text/markdown': ['.md'], 'application/pdf': ['.pdf'] },
    maxFiles: 1,
  })

  const handleSubmit = () => {
    if (!idea.trim()) return
    setLoading(true)
    setMission(idea.trim(), budget, file?.content ?? null)
    setTimeout(() => navigate('/simulation'), 1200)
  }

  const budgetPct = ((budget - MIN_BUDGET) / (MAX_BUDGET - MIN_BUDGET)) * 100

  return (
    <motion.div
      initial={{ opacity: 0, y: 32 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, delay: 0.4, ease: 'easeOut' }}
    >
      <GlassPanel className="w-full max-w-2xl mx-auto p-8 space-y-6">
        {/* Idea textarea */}
        <div>
          <textarea
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            placeholder="Describe your startup idea or paste your business plan..."
            rows={5}
            className="w-full bg-transparent border border-[#1a1a2e] rounded-lg p-4 text-sm text-[#f8fafc]
              placeholder:text-[#64748b] font-mono resize-none outline-none
              focus:border-[#3b82f6] focus:shadow-[0_0_0_1px_rgba(59,130,246,0.3)]
              transition-all duration-200"
          />
        </div>

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all duration-200
            ${isDragActive ? 'border-[#3b82f6] bg-[rgba(59,130,246,0.05)]' : 'border-[#1a1a2e] hover:border-[rgba(59,130,246,0.4)]'}
            ${dropFlash ? 'border-[#22c55e] bg-[rgba(34,197,94,0.06)]' : ''}
          `}
        >
          <input {...getInputProps()} />
          {file ? (
            <div className="flex items-center justify-center gap-2 text-[#22c55e]">
              <FileText size={16} />
              <span className="font-mono text-sm font-medium">LOADED — {file.name}</span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 text-[#64748b]">
              <Upload size={20} />
              <span className="font-mono text-xs">
                {isDragActive ? 'DROP IT.' : 'drag + drop  ·  .txt  .md  .pdf'}
              </span>
            </div>
          )}
        </div>

        {/* Budget slider */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs text-[#64748b] uppercase tracking-widest">Budget</span>
            <span className="font-mono text-sm font-bold text-[#3b82f6]">{formatCurrency(budget)}</span>
          </div>
          <div className="relative">
            {/* Track */}
            <div className="h-1 rounded-full bg-[#1a1a2e] relative overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-[#3b82f6] to-[#60a5fa]"
                style={{ width: `${budgetPct}%` }}
                layout
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              />
            </div>
            <input
              type="range"
              min={MIN_BUDGET}
              max={MAX_BUDGET}
              step={100}
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value))}
              className="absolute inset-0 w-full opacity-0 cursor-pointer h-1"
            />
            {/* Glowing thumb */}
            <div
              className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-[#3b82f6]
                shadow-[0_0_10px_rgba(59,130,246,0.8)] border-2 border-white pointer-events-none transition-all"
              style={{ left: `calc(${budgetPct}% - 8px)` }}
            />
          </div>
          <div className="flex justify-between">
            <span className="font-mono text-xs text-[#64748b]">{formatCurrency(MIN_BUDGET)}</span>
            <span className="font-mono text-xs text-[#64748b]">{formatCurrency(MAX_BUDGET)}</span>
          </div>
        </div>

        {/* Submit */}
        <motion.button
          onClick={handleSubmit}
          disabled={!idea.trim() || loading}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          className="relative w-full py-4 rounded-lg font-bold text-sm tracking-widest uppercase
            bg-[#3b82f6] text-white overflow-hidden
            disabled:opacity-40 disabled:cursor-not-allowed
            transition-all duration-200"
          style={{ fontFamily: 'Space Grotesk, sans-serif' }}
        >
          {/* Pulse ring */}
          {!loading && idea.trim() && (
            <motion.span
              className="absolute inset-0 rounded-lg bg-[#3b82f6]"
              initial={{ opacity: 0.3, scale: 1 }}
              animate={{ opacity: 0, scale: 1.05 }}
              transition={{ duration: 1.5, repeat: Infinity, ease: 'easeOut' }}
            />
          )}
          <span className="relative flex items-center justify-center gap-2">
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                INITIALISING AGENTS...
              </>
            ) : (
              <>
                <Zap size={16} />
                LAUNCH SIMULATION
              </>
            )}
          </span>
        </motion.button>
      </GlassPanel>
    </motion.div>
  )
}
