import { useRef, useMemo, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Environment } from '@react-three/drei'
import { EffectComposer, Bloom } from '@react-three/postprocessing'
import * as THREE from 'three'
import type { AgentId, AgentStatus } from '../../../types'

// ─── PRODUCT: Particle Data Burst ────────────────────────────────────
function ProductShape({ state }: { state: AgentStatus }) {
  const pointsRef  = useRef<THREE.Points>(null)
  const isThinking = state === 'thinking'
  const isActing   = state === 'acting'
  const COUNT = 3000

  const positions = useMemo(() => {
    const pos = new Float32Array(COUNT * 3)
    for (let i = 0; i < COUNT; i++) {
      const phi   = Math.acos(1 - 2 * (i / COUNT))
      const theta = Math.PI * (1 + Math.sqrt(5)) * i
      const r     = 1.0 + (Math.random() - 0.5) * 0.3
      pos[i * 3]     = r * Math.sin(phi) * Math.cos(theta)
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta)
      pos[i * 3 + 2] = r * Math.cos(phi)
    }
    return pos
  }, [])

  const originalPositions = useMemo(() => positions.slice(), [positions])

  useFrame(({ clock }) => {
    if (!pointsRef.current) return
    const t     = clock.getElapsedTime()
    const speed = isThinking ? 1.5 : 0.4
    const arr   = pointsRef.current.geometry.attributes.position.array as Float32Array

    for (let i = 0; i < COUNT; i++) {
      const i3 = i * 3
      const pulse = 1 + Math.sin(t * speed + i * 0.01) * (isThinking ? 0.3 : 0.08)
      arr[i3]     = originalPositions[i3]     * pulse
      arr[i3 + 1] = originalPositions[i3 + 1] * pulse
      arr[i3 + 2] = originalPositions[i3 + 2] * pulse
    }

    pointsRef.current.geometry.attributes.position.needsUpdate = true
    pointsRef.current.rotation.y = t * 0.15
    pointsRef.current.rotation.x = t * 0.05
  })

  return (
    <>
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={COUNT}
            array={positions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          color={isThinking || isActing ? '#fbbf24' : '#f59e0b'}
          size={isThinking ? 0.025 : 0.018}
          sizeAttenuation
          transparent
          opacity={0.85}
        />
      </points>
      {/* Glowing core */}
      <mesh>
        <sphereGeometry args={[0.3, 16, 16]} />
        <meshStandardMaterial
          color="#f59e0b"
          emissive="#f59e0b"
          emissiveIntensity={isThinking ? 3 : 1}
          transparent
          opacity={0.6}
        />
      </mesh>
      <EffectComposer>
        <Bloom intensity={isThinking ? 3 : 1.2} luminanceThreshold={0.1} luminanceSmoothing={0.9} />
      </EffectComposer>
    </>
  )
}

// ─── TECH: Holographic Neural Mesh ───────────────────────────────────
function TechShape({ state }: { state: AgentStatus }) {
  const meshRef    = useRef<THREE.Mesh>(null)
  const wireRef    = useRef<THREE.Mesh>(null)
  const isThinking = state === 'thinking'

  const uniformsRef = useRef({
    uTime:      { value: 0 },
    uIntensity: { value: 0.3 },
    uColor:     { value: new THREE.Color('#22c55e') },
  })

  const vertexShader = /* glsl */ `
    uniform float uTime;
    uniform float uIntensity;
    varying vec3 vNormal;
    varying vec3 vPosition;

    float noise(vec3 p) {
      return sin(p.x * 3.0 + uTime) * sin(p.y * 3.0 + uTime * 0.7) * sin(p.z * 3.0 + uTime * 0.5);
    }

    void main() {
      vNormal = normal;
      vPosition = position;
      vec3 newPosition = position + normal * noise(position) * uIntensity;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
    }
  `

  const fragmentShader = /* glsl */ `
    uniform vec3 uColor;
    uniform float uTime;
    varying vec3 vNormal;
    varying vec3 vPosition;

    void main() {
      float fresnel   = pow(1.0 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 3.0);
      vec3 color      = mix(uColor * 0.3, uColor, fresnel);
      float scanLine  = step(0.98, sin(vPosition.y * 20.0 + uTime * 2.0));
      color += vec3(scanLine) * 0.3;
      gl_FragColor = vec4(color, 0.85);
    }
  `

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime()
    uniformsRef.current.uTime.value      = t
    uniformsRef.current.uIntensity.value = isThinking
      ? 0.6 + Math.sin(t * 3) * 0.2
      : 0.2

    if (meshRef.current) {
      meshRef.current.rotation.y = t * 0.3
      meshRef.current.rotation.x = Math.sin(t * 0.2) * 0.2
    }
    if (wireRef.current) {
      wireRef.current.rotation.y = meshRef.current?.rotation.y ?? 0
      wireRef.current.rotation.x = meshRef.current?.rotation.x ?? 0
    }
  })

  return (
    <>
      <mesh ref={meshRef}>
        <icosahedronGeometry args={[1.0, 4]} />
        <shaderMaterial
          vertexShader={vertexShader}
          fragmentShader={fragmentShader}
          uniforms={uniformsRef.current}
          transparent
          side={THREE.DoubleSide}
        />
      </mesh>
      <mesh ref={wireRef}>
        <icosahedronGeometry args={[1.02, 2]} />
        <meshBasicMaterial
          color="#22c55e"
          wireframe
          transparent
          opacity={isThinking ? 0.5 : 0.2}
        />
      </mesh>
      <EffectComposer>
        <Bloom intensity={isThinking ? 2.5 : 0.8} luminanceThreshold={0.1} luminanceSmoothing={0.9} />
      </EffectComposer>
    </>
  )
}

// ─── OPS: Orbital Ring Planet ─────────────────────────────────────────
function OpsShape({ state }: { state: AgentStatus }) {
  const groupRef      = useRef<THREE.Group>(null)
  const ring1Ref      = useRef<THREE.Mesh>(null)
  const ring2Ref      = useRef<THREE.Mesh>(null)
  const particlesRef  = useRef<THREE.Points>(null)
  const isThinking    = state === 'thinking'

  const orbitParticles = useMemo(() => {
    const count = 200
    const pos   = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      const angle  = (i / count) * Math.PI * 2
      const radius = 1.2 + (Math.random() - 0.5) * 0.4
      const spread = (Math.random() - 0.5) * 0.1
      pos[i * 3]     = Math.cos(angle) * radius
      pos[i * 3 + 1] = spread
      pos[i * 3 + 2] = Math.sin(angle) * radius
    }
    return pos
  }, [])

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime()
    if (ring1Ref.current) ring1Ref.current.rotation.z = t * (isThinking ? 0.8 : 0.3)
    if (ring2Ref.current) {
      ring2Ref.current.rotation.z = -t * (isThinking ? 0.5 : 0.2)
      ring2Ref.current.rotation.x = Math.PI / 3
    }
    if (particlesRef.current) particlesRef.current.rotation.y = t * (isThinking ? 0.6 : 0.2)
    if (groupRef.current) groupRef.current.rotation.y = t * 0.1
  })

  return (
    <group ref={groupRef}>
      {/* Core sphere */}
      <mesh>
        <sphereGeometry args={[0.6, 32, 32]} />
        <meshStandardMaterial
          color="#8b5cf6"
          emissive="#8b5cf6"
          emissiveIntensity={isThinking ? 1.5 : 0.4}
          roughness={0.0}
          metalness={1.0}
        />
      </mesh>

      {/* Ring 1 — equatorial */}
      <mesh ref={ring1Ref} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.1, 0.04, 8, 80]} />
        <meshStandardMaterial
          color="#a78bfa"
          emissive="#8b5cf6"
          emissiveIntensity={isThinking ? 2 : 0.6}
          transparent
          opacity={0.9}
        />
      </mesh>

      {/* Ring 2 — tilted */}
      <mesh ref={ring2Ref} rotation={[Math.PI / 3, 0, Math.PI / 6]}>
        <torusGeometry args={[1.4, 0.025, 8, 80]} />
        <meshStandardMaterial
          color="#7c3aed"
          emissive="#8b5cf6"
          emissiveIntensity={isThinking ? 1.5 : 0.4}
          transparent
          opacity={0.6}
        />
      </mesh>

      {/* Orbital particles */}
      <points ref={particlesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={200}
            array={orbitParticles}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          color="#c4b5fd"
          size={0.025}
          sizeAttenuation
          transparent
          opacity={0.8}
        />
      </points>

      <EffectComposer>
        <Bloom intensity={isThinking ? 3 : 1.5} luminanceThreshold={0.1} luminanceSmoothing={0.9} />
      </EffectComposer>
    </group>
  )
}

// ─── FINANCE: Shattered Crystal ──────────────────────────────────────
function FinanceShape({ state }: { state: AgentStatus }) {
  const groupRef      = useRef<THREE.Group>(null)
  const isThinking    = state === 'thinking'

  const fragments = useMemo(() => (
    Array.from({ length: 18 }, () => ({
      position: [
        (Math.random() - 0.5) * 1.8,
        (Math.random() - 0.5) * 1.8,
        (Math.random() - 0.5) * 1.8,
      ] as [number, number, number],
      rotation: [
        Math.random() * Math.PI * 2,
        Math.random() * Math.PI * 2,
        Math.random() * Math.PI * 2,
      ] as [number, number, number],
      scale:        0.15 + Math.random() * 0.35,
      speed:        (Math.random() - 0.5) * 0.5,
      orbitOffset:  Math.random() * Math.PI * 2,
    }))
  ), [])

  const fragmentRefs = useRef<(THREE.Mesh | null)[]>([])

  useFrame(({ clock }) => {
    const t           = clock.getElapsedTime()
    const expandSpeed = isThinking ? 1.2 : 0.4

    fragmentRefs.current.forEach((mesh, i) => {
      if (!mesh) return
      const f = fragments[i]
      mesh.rotation.x += f.speed * 0.01 * (isThinking ? 2 : 1)
      mesh.rotation.y += f.speed * 0.015 * (isThinking ? 2 : 1)
      const breathe = 1 + Math.sin(t * expandSpeed + f.orbitOffset) * 0.15
      mesh.position.set(
        f.position[0] * breathe,
        f.position[1] * breathe,
        f.position[2] * breathe,
      )
    })
    if (groupRef.current) groupRef.current.rotation.y = t * 0.2
  })

  return (
    <group ref={groupRef}>
      {fragments.map((f, i) => (
        <mesh
          key={i}
          ref={el => { fragmentRefs.current[i] = el }}
          position={f.position}
          rotation={f.rotation}
          scale={f.scale}
        >
          <tetrahedronGeometry args={[1, 0]} />
          <meshStandardMaterial
            color="#ef4444"
            emissive="#ef4444"
            emissiveIntensity={isThinking ? 0.8 : 0.2}
            metalness={0.95}
            roughness={0.05}
            transparent
            opacity={0.9}
          />
        </mesh>
      ))}
      {/* Central red core */}
      <mesh>
        <sphereGeometry args={[0.15, 8, 8]} />
        <meshStandardMaterial
          color="#ef4444"
          emissive="#ef4444"
          emissiveIntensity={isThinking ? 4 : 1.5}
        />
      </mesh>
      <EffectComposer>
        <Bloom intensity={isThinking ? 2.5 : 0.8} luminanceThreshold={0.1} luminanceSmoothing={0.9} />
      </EffectComposer>
    </group>
  )
}

// ─── SCENE LIGHTS ─────────────────────────────────────────────────────
const AGENT_COLORS: Record<string, string> = {
  product: '#f59e0b',
  tech:    '#22c55e',
  ops:     '#8b5cf6',
  finance: '#ef4444',
}

function SceneLights({ agentId }: { agentId: string }) {
  const color = AGENT_COLORS[agentId] ?? '#ffffff'
  return (
    <>
      <ambientLight intensity={0.05} />
      <pointLight position={[3, 3, 3]} intensity={2} color={color} />
      <pointLight position={[-3, -3, -3]} intensity={0.5} color={color} />
    </>
  )
}

// ─── MAIN EXPORT ──────────────────────────────────────────────────────
interface AgentShapeProps {
  agentId: AgentId
  state: AgentStatus
  size?: number
}

export default function AgentShape({ agentId, state, size = 180 }: AgentShapeProps) {
  const visualState: AgentStatus = state === 'blocked' ? 'thinking' : state

  return (
    <div style={{ width: size, height: size, overflow: 'visible' }}>
      <Canvas
        gl={{
          alpha: true,
          antialias: true,
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1.5,
        }}
        camera={{ position: [0, 0, 3.5], fov: 45 }}
        style={{ width: size, height: size, background: 'transparent', overflow: 'visible' }}
        dpr={[1, 2]}
      >
        <SceneLights agentId={agentId} />
        <Environment preset="night" />

        {agentId === 'product' && <ProductShape state={visualState} />}
        {agentId === 'tech'    && <TechShape    state={visualState} />}
        {agentId === 'ops'     && <OpsShape     state={visualState} />}
        {agentId === 'finance' && <FinanceShape state={visualState} />}
      </Canvas>
    </div>
  )
}
