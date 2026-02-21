import { cn } from '../../lib/utils'

interface TerminalTextProps {
  children: React.ReactNode
  className?: string
  dim?: boolean
  size?: 'xs' | 'sm' | 'base'
}

export function TerminalText({ children, className, dim, size = 'sm' }: TerminalTextProps) {
  return (
    <span
      className={cn(
        'font-mono leading-relaxed',
        size === 'xs' && 'text-xs',
        size === 'sm' && 'text-sm',
        size === 'base' && 'text-base',
        dim ? 'text-[#64748b]' : 'text-[#94a3b8]',
        className
      )}
    >
      {children}
    </span>
  )
}
