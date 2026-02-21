import { motion } from 'framer-motion'

export function HeroSection() {
  return (
    <div className="text-center mb-12 select-none">
      <motion.h1
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: 'easeOut' }}
        className="text-5xl md:text-7xl font-bold tracking-tight leading-none mb-6"
        style={{ fontFamily: 'Space Grotesk, sans-serif' }}
      >
        <span
          className="inline-block bg-gradient-to-r from-white via-blue-200 to-white bg-clip-text text-transparent
            hover:from-[#3b82f6] hover:via-white hover:to-[#3b82f6] transition-all duration-700"
        >
          YOUR STARTUP.
        </span>
        <br />
        <span className="text-white">BUILT BY MACHINES.</span>
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.2, ease: 'easeOut' }}
        className="font-mono text-[#64748b] text-sm md:text-base tracking-widest uppercase"
      >
        drop your idea. watch four agents build it.
      </motion.p>
    </div>
  )
}
