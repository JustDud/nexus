import { type ReactNode } from 'react'
import { cn } from '../../lib/utils'

interface GlassPanelProps {
  children: ReactNode
  className?: string
  danger?: boolean
  onClick?: () => void
}

export function GlassPanel({ children, className, danger, onClick }: GlassPanelProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'rounded-xl border backdrop-blur-md transition-all duration-700',
        'bg-[rgba(15,15,26,0.7)]',
        danger
          ? 'border-[rgba(239,68,68,0.4)] shadow-[0_0_20px_rgba(239,68,68,0.1)]'
          : 'border-[#1a1a2e] shadow-[0_0_20px_rgba(0,0,0,0.3)]',
        onClick && 'cursor-pointer hover:border-[rgba(59,130,246,0.4)] hover:shadow-[0_0_24px_rgba(59,130,246,0.1)]',
        className
      )}
    >
      {children}
    </div>
  )
}
