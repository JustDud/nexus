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
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.25, ease: 'easeOut' }}
          className="w-full mb-1"
          style={{ zIndex: 10 }}
        >
          <div
            className="w-full rounded-lg px-3 py-2 space-y-1"
            style={{
              background: 'rgba(8,8,16,0.88)',
              border: `1px solid ${color}28`,
              boxShadow: `0 0 16px ${color}12`,
            }}
          >
            <motion.div
              variants={{ show: { transition: { staggerChildren: 0.08 } } }}
              initial="hidden"
              animate="show"
              className="space-y-0.5"
            >
              {visibleFragments.map((frag, i) => {
                const isCurrent = i === visibleFragments.length - 1
                return (
                  <motion.div
                    key={`${frag}-${i}`}
                    variants={{
                      hidden: { opacity: 0, y: 4 },
                      show:   { opacity: isCurrent ? 0.85 : 0.35, y: 0 },
                    }}
                    className="text-[10px] leading-relaxed"
                    style={{
                      fontFamily: 'JetBrains Mono, monospace',
                      color: isCurrent ? color : '#64748b',
                    }}
                  >
                    {isCurrent ? (
                      <TypeAnimation
                        key={frag}
                        sequence={[frag]}
                        speed={72}
                        cursor={false}
                        wrapper="span"
                      />
                    ) : (
                      <span>{frag}</span>
                    )}
                  </motion.div>
                )
              })}
            </motion.div>

            {/* Blinking cursor */}
            <motion.span
              className="inline-block w-[6px] h-[11px] align-middle"
              style={{ background: color, borderRadius: 1 }}
              animate={{ opacity: [1, 0, 1] }}
              transition={{ duration: 0.75, repeat: Infinity }}
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
