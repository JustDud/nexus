import { AnimatePresence, motion } from 'framer-motion'
import { TypeAnimation } from 'react-type-animation'

interface ThoughtStreamProps {
  fragments: string[]
  color: string
  visible: boolean
}

export function ThoughtStream({ fragments, color, visible }: ThoughtStreamProps) {
  const MAX_LINES = 3
  const visibleFragments = fragments.slice(-MAX_LINES)

  return (
    <AnimatePresence>
      {visible && visibleFragments.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 8, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -12, scale: 0.95 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="absolute -top-2 left-0 right-0 -translate-y-full pointer-events-none"
          style={{ zIndex: 10 }}
        >
          <div
            className="mx-2 rounded-lg p-3 space-y-1 border backdrop-blur-md"
            style={{
              background: 'rgba(8,8,16,0.85)',
              borderColor: `${color}30`,
              boxShadow: `0 0 20px ${color}15`,
            }}
          >
            {visibleFragments.map((frag, i) => (
              <motion.div
                key={`${frag}-${i}`}
                initial={{ opacity: 0, x: -4 }}
                animate={{ opacity: i === visibleFragments.length - 1 ? 1 : 0.4 }}
                className="font-mono text-[10px] leading-relaxed"
                style={{ color: i === visibleFragments.length - 1 ? color : '#64748b' }}
              >
                {i === visibleFragments.length - 1 ? (
                  <TypeAnimation
                    key={frag}
                    sequence={[frag]}
                    speed={70}
                    cursor={false}
                    wrapper="span"
                  />
                ) : (
                  <span>{frag}</span>
                )}
              </motion.div>
            ))}
            {/* Blinking cursor */}
            <motion.span
              className="inline-block w-1.5 h-3 ml-0.5 align-middle"
              style={{ background: color }}
              animate={{ opacity: [1, 0, 1] }}
              transition={{ duration: 0.8, repeat: Infinity }}
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
