import { useRef, useEffect } from 'react'

interface LetterCell {
  char: string
  color: string
  targetColor: string
  colorProgress: number
}

interface RgbColor {
  r: number
  g: number
  b: number
}

interface LetterGlitchProps {
  glitchColors?: string[]
  glitchSpeed?: number
  centerVignette?: boolean
  outerVignette?: boolean
  smooth?: boolean
  characters?: string
}

const LetterGlitch = ({
  glitchColors = ['#1a1535', '#0e1a30', '#141020'],
  glitchSpeed = 50,
  centerVignette = false,
  outerVignette = false,
  smooth = true,
  characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$&*()-_+=/[]{};:<>.,0123456789',
}: LetterGlitchProps) => {
  const canvasRef    = useRef<HTMLCanvasElement>(null)
  const animRef      = useRef<number>(0)
  const letters      = useRef<LetterCell[]>([])
  const grid         = useRef({ columns: 0, rows: 0 })
  const ctx          = useRef<CanvasRenderingContext2D | null>(null)
  const lastGlitch   = useRef(Date.now())

  const lettersAndSymbols = Array.from(characters)

  const fontSize  = 16
  const charWidth = 10
  const charHeight = 20

  const getRandomChar  = () => lettersAndSymbols[Math.floor(Math.random() * lettersAndSymbols.length)]
  const getRandomColor = () => glitchColors[Math.floor(Math.random() * glitchColors.length)]

  const hexToRgb = (hex: string): RgbColor | null => {
    const shorthand = /^#?([a-f\d])([a-f\d])([a-f\d])$/i
    hex = hex.replace(shorthand, (_m, r, g, b) => r + r + g + g + b + b)
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    return result
      ? { r: parseInt(result[1], 16), g: parseInt(result[2], 16), b: parseInt(result[3], 16) }
      : null
  }

  const interpolateColor = (start: RgbColor, end: RgbColor, factor: number): string => {
    const r = Math.round(start.r + (end.r - start.r) * factor)
    const g = Math.round(start.g + (end.g - start.g) * factor)
    const b = Math.round(start.b + (end.b - start.b) * factor)
    return `rgb(${r}, ${g}, ${b})`
  }

  const initGrid = (columns: number, rows: number) => {
    grid.current = { columns, rows }
    letters.current = Array.from({ length: columns * rows }, () => ({
      char: getRandomChar(),
      color: getRandomColor(),
      targetColor: getRandomColor(),
      colorProgress: 1,
    }))
  }

  const drawLetters = () => {
    const c = ctx.current
    const canvas = canvasRef.current
    if (!c || !canvas || letters.current.length === 0) return
    const { width, height } = canvas.getBoundingClientRect()
    c.clearRect(0, 0, width, height)
    c.font = `${fontSize}px monospace`
    c.textBaseline = 'top'
    letters.current.forEach((letter, i) => {
      c.fillStyle = letter.color
      c.fillText(letter.char, (i % grid.current.columns) * charWidth, Math.floor(i / grid.current.columns) * charHeight)
    })
  }

  const updateLetters = () => {
    if (!letters.current.length) return
    const count = Math.max(1, Math.floor(letters.current.length * 0.05))
    for (let i = 0; i < count; i++) {
      const idx = Math.floor(Math.random() * letters.current.length)
      const cell = letters.current[idx]
      if (!cell) continue
      cell.char = getRandomChar()
      cell.targetColor = getRandomColor()
      if (!smooth) {
        cell.color = cell.targetColor
        cell.colorProgress = 1
      } else {
        cell.colorProgress = 0
      }
    }
  }

  const handleSmooth = () => {
    let needsRedraw = false
    letters.current.forEach((cell) => {
      if (cell.colorProgress < 1) {
        cell.colorProgress = Math.min(1, cell.colorProgress + 0.05)
        const startRgb = hexToRgb(cell.color)
        const endRgb   = hexToRgb(cell.targetColor)
        if (startRgb && endRgb) {
          cell.color = interpolateColor(startRgb, endRgb, cell.colorProgress)
          needsRedraw = true
        }
      }
    })
    if (needsRedraw) drawLetters()
  }

  const resizeCanvas = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const parent = canvas.parentElement
    if (!parent) return
    const dpr  = window.devicePixelRatio || 1
    const rect = parent.getBoundingClientRect()
    canvas.width  = rect.width  * dpr
    canvas.height = rect.height * dpr
    canvas.style.width  = `${rect.width}px`
    canvas.style.height = `${rect.height}px`
    if (ctx.current) ctx.current.setTransform(dpr, 0, 0, dpr, 0, 0)
    initGrid(
      Math.ceil(rect.width  / charWidth),
      Math.ceil(rect.height / charHeight),
    )
    drawLetters()
  }

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    ctx.current = canvas.getContext('2d')
    resizeCanvas()

    function animate() {
      const now = Date.now()
      if (now - lastGlitch.current >= glitchSpeed) {
        updateLetters()
        drawLetters()
        lastGlitch.current = now
      }
      if (smooth) handleSmooth()
      animRef.current = requestAnimationFrame(animate)
    }
    animate()

    let resizeTimer: ReturnType<typeof setTimeout>
    const onResize = () => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(() => {
        cancelAnimationFrame(animRef.current)
        resizeCanvas()
        animate()
      }, 100)
    }
    window.addEventListener('resize', onResize)

    return () => {
      cancelAnimationFrame(animRef.current)
      window.removeEventListener('resize', onResize)
    }
  }, [glitchSpeed, smooth]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
      <canvas ref={canvasRef} style={{ display: 'block', width: '100%', height: '100%' }} />
      {outerVignette && (
        <div style={{
          position: 'absolute', inset: 0, pointerEvents: 'none',
          background: 'radial-gradient(circle, rgba(0,0,0,0) 60%, rgba(0,0,0,1) 100%)',
        }} />
      )}
      {centerVignette && (
        <div style={{
          position: 'absolute', inset: 0, pointerEvents: 'none',
          background: 'radial-gradient(circle, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0) 60%)',
        }} />
      )}
    </div>
  )
}

export default LetterGlitch
