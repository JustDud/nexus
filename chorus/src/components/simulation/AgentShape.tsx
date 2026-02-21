import { useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { type AgentShape as AgentShapeType, type AgentStatus } from '../../types'

// ── PRODUCT: Icosahedron — amber, MeshPhysicalMaterial ──
function IcosahedronMesh({ status }: { status: AgentStatus }) {
  const meshRef = useRef<THREE.Mesh>(null)
  const t       = useRef(0)

  useFrame((_, delta) => {
    t.current += delta
    if (!meshRef.current) return
    const isThinking = status === 'thinking'
    const isActing   = status === 'acting'

    meshRef.current.rotation.y += delta * 0.3
    meshRef.current.rotation.x += delta * 0.12

    const mat = meshRef.current.material as THREE.MeshPhysicalMaterial
    mat.emissiveIntensity = isThinking
      ? Math.sin(t.current * 3) * 0.3 + 0.3
      : 0.2

    if (isActing) {
      const pulse = Math.sin(t.current * Math.PI * 4) * 0.1 + 1.1
      meshRef.current.scale.setScalar(pulse)
    } else {
      meshRef.current.scale.setScalar(1)
    }
  })

  return (
    <>
      <ambientLight intensity={0.1} />
      <pointLight color="#f59e0b" intensity={3} position={[2, 2, 2]} />
      <mesh ref={meshRef}>
        <icosahedronGeometry args={[1, 0]} />
        <meshPhysicalMaterial
          color="#f59e0b"
          emissive={new THREE.Color('#f59e0b')}
          emissiveIntensity={0.2}
          metalness={0.9}
          roughness={0.1}
        />
      </mesh>
    </>
  )
}

// ── TECH: TorusKnot — green, wireframe + emissive, glitch ──
function TorusKnotMesh({ status }: { status: AgentStatus }) {
  const meshRef   = useRef<THREE.Mesh>(null)
  const t         = useRef(0)
  const glitchAt  = useRef(0)
  const glitching = useRef(false)

  useFrame((_, delta) => {
    t.current += delta
    if (!meshRef.current) return
    const isThinking = status === 'thinking'
    const isActing   = status === 'acting'

    meshRef.current.rotation.y += delta * 0.6
    meshRef.current.rotation.x += delta * 0.3

    // Glitch every ~3s: snap rotation by 0.3rad for 100ms
    if (!glitching.current && t.current - glitchAt.current > 3 + Math.random() * 2) {
      glitchAt.current = t.current
      glitching.current = true
      meshRef.current.rotation.z += (Math.random() - 0.5) * 0.6
      setTimeout(() => { glitching.current = false }, 100)
    }

    const mat = meshRef.current.material as THREE.MeshStandardMaterial
    mat.emissiveIntensity = isThinking
      ? Math.sin(t.current * 3) * 0.3 + 0.3
      : 0.5

    if (isActing) {
      const pulse = Math.sin(t.current * Math.PI * 4) * 0.1 + 1.1
      meshRef.current.scale.setScalar(pulse)
    } else {
      meshRef.current.scale.setScalar(1)
    }
  })

  return (
    <>
      <ambientLight intensity={0.1} />
      <pointLight color="#22c55e" intensity={3} position={[2, 2, 2]} />
      <mesh ref={meshRef}>
        <torusKnotGeometry args={[0.6, 0.2, 128, 16]} />
        <meshStandardMaterial
          color="#22c55e"
          emissive={new THREE.Color('#22c55e')}
          emissiveIntensity={0.5}
          wireframe={true}
        />
      </mesh>
    </>
  )
}

// ── OPS: Octahedron — purple, MeshPhysicalMaterial, all-axis rotation ──
function OctahedronMesh({ status }: { status: AgentStatus }) {
  const meshRef = useRef<THREE.Mesh>(null)
  const t       = useRef(0)

  useFrame((_, delta) => {
    t.current += delta
    if (!meshRef.current) return
    const isThinking = status === 'thinking'
    const isActing   = status === 'acting'

    meshRef.current.rotation.x += delta * 0.24
    meshRef.current.rotation.y += delta * 0.36
    meshRef.current.rotation.z += delta * 0.12

    const mat = meshRef.current.material as THREE.MeshPhysicalMaterial
    mat.emissiveIntensity = isThinking
      ? Math.sin(t.current * 3) * 0.3 + 0.3
      : 0.15

    if (isActing) {
      const pulse = Math.sin(t.current * Math.PI * 4) * 0.1 + 1.1
      meshRef.current.scale.setScalar(pulse)
    } else {
      meshRef.current.scale.setScalar(1)
    }
  })

  return (
    <>
      <ambientLight intensity={0.1} />
      <pointLight color="#8b5cf6" intensity={3} position={[2, 2, 2]} />
      <mesh ref={meshRef}>
        <octahedronGeometry args={[1, 0]} />
        <meshPhysicalMaterial
          color="#8b5cf6"
          emissive={new THREE.Color('#8b5cf6')}
          emissiveIntensity={0.15}
          metalness={0.7}
          roughness={0.2}
        />
      </mesh>
    </>
  )
}

// ── FINANCE: Tetrahedron — red, snapping rotation every 1.5s ──
function TetrahedronMesh({ status }: { status: AgentStatus }) {
  const meshRef   = useRef<THREE.Mesh>(null)
  const t         = useRef(0)
  const snapAngle = useRef(0)
  const nextSnap  = useRef(1.5)

  useFrame((_, delta) => {
    t.current += delta
    if (!meshRef.current) return
    const isThinking = status === 'thinking'
    const isActing   = status === 'acting'

    // Snap to a new rotation every 1.5s
    if (t.current > nextSnap.current) {
      nextSnap.current = t.current + 1.5
      snapAngle.current += (Math.PI / 2) * (Math.random() > 0.5 ? 1 : -1)
    }
    meshRef.current.rotation.y = THREE.MathUtils.lerp(
      meshRef.current.rotation.y,
      snapAngle.current,
      0.12
    )
    meshRef.current.rotation.x = THREE.MathUtils.lerp(
      meshRef.current.rotation.x,
      Math.round(meshRef.current.rotation.x / (Math.PI / 2)) * (Math.PI / 2),
      0.06
    )

    const mat = meshRef.current.material as THREE.MeshStandardMaterial
    mat.emissiveIntensity = isThinking
      ? Math.sin(t.current * 3) * 0.3 + 0.3
      : 0.1

    if (isActing) {
      const pulse = Math.sin(t.current * Math.PI * 4) * 0.1 + 1.1
      meshRef.current.scale.setScalar(pulse)
    } else {
      meshRef.current.scale.setScalar(1)
    }
  })

  return (
    <>
      <ambientLight intensity={0.1} />
      <pointLight color="#ef4444" intensity={3} position={[2, 2, 2]} />
      <mesh ref={meshRef}>
        <tetrahedronGeometry args={[1, 0]} />
        <meshStandardMaterial
          color="#ef4444"
          emissive={new THREE.Color('#ef4444')}
          emissiveIntensity={0.1}
          metalness={0.95}
          roughness={0.05}
        />
      </mesh>
    </>
  )
}

interface AgentShapeProps {
  shape: AgentShapeType
  color: string
  status: AgentStatus
  size?: number
}

export function AgentShape({ shape, status, size = 160 }: AgentShapeProps) {
  return (
    <div style={{ width: size, height: size }} className="mx-auto">
      <Canvas
        camera={{ position: [0, 0, 3.5], fov: 42 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        {shape === 'icosahedron'  && <IcosahedronMesh status={status} />}
        {shape === 'torusKnot'    && <TorusKnotMesh   status={status} />}
        {shape === 'dodecahedron' && <OctahedronMesh  status={status} />}
        {shape === 'octahedron'   && <TetrahedronMesh status={status} />}
      </Canvas>
    </div>
  )
}
