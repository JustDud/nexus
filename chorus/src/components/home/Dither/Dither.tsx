import { useEffect, useRef } from 'react'
import './Dither.css'

interface DitherProps {
  waveColor?: [number, number, number]
  colorNum?: number
  pixelSize?: number
  waveSpeed?: number
  waveFrequency?: number
  waveAmplitude?: number
  enableMouseInteraction?: boolean
  mouseRadius?: number
}

const VERT_SRC = `#version 300 es
in vec2 a_pos;
void main() {
  gl_Position = vec4(a_pos, 0.0, 1.0);
}`

const FRAG_SRC = `#version 300 es
precision mediump float;

uniform vec2  u_res;
uniform float u_time;
uniform vec3  u_color;
uniform float u_colorNum;
uniform float u_pixelSize;
uniform float u_waveSpeed;
uniform float u_waveFreq;
uniform float u_waveAmp;
uniform vec2  u_mouse;
uniform float u_mouseRadius;
uniform int   u_mouseInteraction;

out vec4 fragColor;

float bayerThreshold(vec2 gridPos) {
  int x = int(mod(gridPos.x, 4.0));
  int y = int(mod(gridPos.y, 4.0));
  int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
  return float(m[y * 4 + x]) / 16.0;
}

void main() {
  // Snap to pixel grid
  vec2 gridPos = floor(gl_FragCoord.xy / u_pixelSize);
  vec2 centerPos = gridPos * u_pixelSize + u_pixelSize * 0.5;
  vec2 uv = centerPos / u_res;

  // Mouse ripple distortion
  if (u_mouseInteraction == 1) {
    vec2 mUV = u_mouse / u_res;
    float dist = distance(uv, mUV);
    float falloff = max(0.0, 1.0 - dist / u_mouseRadius);
    if (falloff > 0.0 && dist > 0.001) {
      float ripple = sin(dist * 40.0 - u_time * 8.0) * 0.012 * falloff;
      uv += normalize(uv - mUV) * ripple;
    }
  }

  // Animated multi-directional waves
  float w1 = sin(uv.x * u_waveFreq + u_time * u_waveSpeed) * u_waveAmp;
  float w2 = sin(uv.y * u_waveFreq * 0.7 - u_time * u_waveSpeed * 0.6) * u_waveAmp * 0.6;
  float w3 = sin((uv.x * 0.7 + uv.y * 1.3) * u_waveFreq * 0.45 + u_time * u_waveSpeed * 0.8) * u_waveAmp * 0.4;
  float wave = w1 + w2 + w3;

  // Radial vignette gradient with wave modulation
  float centerDist = length(uv - vec2(0.5, 0.5));
  float brightness = 0.55 - centerDist * 0.85 + wave;
  brightness = clamp(brightness, 0.0, 1.0);

  // Ordered dithering
  float threshold = bayerThreshold(gridPos);
  float levels = max(u_colorNum - 1.0, 1.0);
  float quantized = floor(brightness * levels + threshold) / levels;

  // Mix near-black base with wave color
  vec3 darkBase = vec3(0.02, 0.02, 0.05);
  vec3 col = mix(darkBase, u_color, quantized);

  fragColor = vec4(col, 1.0);
}`

export default function Dither({
  waveColor = [0.23, 0.51, 0.96],
  colorNum = 4,
  pixelSize = 4,
  waveSpeed = 0.8,
  waveFrequency = 5.0,
  waveAmplitude = 0.28,
  enableMouseInteraction = true,
  mouseRadius = 0.3,
}: DitherProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mouseRef = useRef({ x: 0, y: 0 })
  const rafRef = useRef<number>(0)

  // Use refs so the effect only runs once
  const propsRef = useRef({ waveColor, colorNum, pixelSize, waveSpeed, waveFrequency, waveAmplitude, enableMouseInteraction, mouseRadius })
  propsRef.current = { waveColor, colorNum, pixelSize, waveSpeed, waveFrequency, waveAmplitude, enableMouseInteraction, mouseRadius }

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const gl = canvas.getContext('webgl2')
    if (!gl) return

    function compileShader(type: number, src: string): WebGLShader {
      const s = gl!.createShader(type)!
      gl!.shaderSource(s, src)
      gl!.compileShader(s)
      return s
    }

    const vert = compileShader(gl.VERTEX_SHADER, VERT_SRC)
    const frag = compileShader(gl.FRAGMENT_SHADER, FRAG_SRC)
    const prog = gl.createProgram()!
    gl.attachShader(prog, vert)
    gl.attachShader(prog, frag)
    gl.linkProgram(prog)
    gl.useProgram(prog)

    // Full-screen quad (triangle strip)
    const buf = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW)
    const aPos = gl.getAttribLocation(prog, 'a_pos')
    gl.enableVertexAttribArray(aPos)
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0)

    // Uniform locations
    const uRes    = gl.getUniformLocation(prog, 'u_res')
    const uTime   = gl.getUniformLocation(prog, 'u_time')
    const uColor  = gl.getUniformLocation(prog, 'u_color')
    const uColNum = gl.getUniformLocation(prog, 'u_colorNum')
    const uPixel  = gl.getUniformLocation(prog, 'u_pixelSize')
    const uWSpeed = gl.getUniformLocation(prog, 'u_waveSpeed')
    const uWFreq  = gl.getUniformLocation(prog, 'u_waveFreq')
    const uWAmp   = gl.getUniformLocation(prog, 'u_waveAmp')
    const uMouse  = gl.getUniformLocation(prog, 'u_mouse')
    const uMRad   = gl.getUniformLocation(prog, 'u_mouseRadius')
    const uMInter = gl.getUniformLocation(prog, 'u_mouseInteraction')

    function applyProps() {
      const p = propsRef.current
      gl!.uniform3f(uColor, p.waveColor[0], p.waveColor[1], p.waveColor[2])
      gl!.uniform1f(uColNum, p.colorNum)
      gl!.uniform1f(uWSpeed, p.waveSpeed)
      gl!.uniform1f(uWFreq, p.waveFrequency)
      gl!.uniform1f(uWAmp, p.waveAmplitude)
      gl!.uniform1f(uMRad, p.mouseRadius)
      gl!.uniform1i(uMInter, p.enableMouseInteraction ? 1 : 0)
    }
    applyProps()

    // Resize handler — accounts for device pixel ratio
    function resize() {
      if (!canvas || !gl) return
      const dpr = window.devicePixelRatio || 1
      const w = canvas.offsetWidth * dpr
      const h = canvas.offsetHeight * dpr
      canvas.width = w
      canvas.height = h
      gl.viewport(0, 0, w, h)
      gl.uniform2f(uRes, w, h)
      gl.uniform1f(uPixel, propsRef.current.pixelSize * dpr)
      // Seed mouse at center
      mouseRef.current = { x: w / 2, y: h / 2 }
      gl.uniform2f(uMouse, w / 2, h / 2)
    }
    resize()

    const ro = new ResizeObserver(resize)
    ro.observe(canvas)

    // Mouse tracking (flip Y for WebGL coord system)
    const onMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      const dpr = window.devicePixelRatio || 1
      mouseRef.current = {
        x: (e.clientX - rect.left) * dpr,
        y: canvas.height - (e.clientY - rect.top) * dpr,
      }
    }
    canvas.addEventListener('mousemove', onMouseMove)

    // Render loop
    const startTime = performance.now()
    function render() {
      const t = (performance.now() - startTime) / 1000
      gl!.uniform1f(uTime, t)
      gl!.uniform2f(uMouse, mouseRef.current.x, mouseRef.current.y)
      applyProps()
      gl!.drawArrays(gl!.TRIANGLE_STRIP, 0, 4)
      rafRef.current = requestAnimationFrame(render)
    }
    render()

    return () => {
      cancelAnimationFrame(rafRef.current)
      ro.disconnect()
      canvas.removeEventListener('mousemove', onMouseMove)
      gl.deleteProgram(prog)
      gl.deleteShader(vert)
      gl.deleteShader(frag)
      gl.deleteBuffer(buf)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return <canvas ref={canvasRef} className="dither-canvas" />
}
