import { useEffect, useRef, useCallback, useState } from 'react'

interface AudioEvent {
  audio_base64: string
  content_type: string
  text: string
  agentName: string
}

export function useAudioPlayer() {
  const [isMuted, setIsMuted] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const queueRef = useRef<AudioEvent[]>([])
  const playingRef = useRef(false)

  const playNext = useCallback(async () => {
    if (playingRef.current || queueRef.current.length === 0) return
    playingRef.current = true
    setIsPlaying(true)

    const item = queueRef.current.shift()!
    const bytes = Uint8Array.from(atob(item.audio_base64), c => c.charCodeAt(0))
    const blob = new Blob([bytes], { type: item.content_type })
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)

    audio.onended = () => {
      URL.revokeObjectURL(url)
      playingRef.current = false
      setIsPlaying(false)
      playNext()
    }
    audio.onerror = () => {
      URL.revokeObjectURL(url)
      playingRef.current = false
      setIsPlaying(false)
      playNext()
    }

    try { await audio.play() } catch { playingRef.current = false; setIsPlaying(false) }
  }, [])

  useEffect(() => {
    const handler = (e: Event) => {
      if (isMuted) return
      const detail = (e as CustomEvent).detail as AudioEvent
      queueRef.current.push(detail)
      playNext()
    }
    window.addEventListener('sim-audio', handler)
    return () => window.removeEventListener('sim-audio', handler)
  }, [isMuted, playNext])

  return { isMuted, setIsMuted, isPlaying }
}
