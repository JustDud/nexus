import { ParticleBackground } from '../components/home/ParticleBackground'
import { HeroSection } from '../components/home/HeroSection'
import { MissionInput } from '../components/home/MissionInput'

export function HomePage() {
  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center px-4 py-16 overflow-hidden"
      style={{ background: '#080810' }}>
      <ParticleBackground />
      <div className="relative z-10 w-full max-w-2xl mx-auto flex flex-col items-center">
        <HeroSection />
        <MissionInput />
      </div>
    </div>
  )
}
