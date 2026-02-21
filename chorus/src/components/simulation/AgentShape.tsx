import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { MeshDistortMaterial } from '@react-three/drei'
import * as THREE from 'three'
import { type AgentShape as AgentShapeType, type AgentStatus } from '../../types'

interface ShapeMeshProps {
  shape: AgentShapeType
  color: string
  status: AgentStatus
}

function Icosahedron({ color, status }: Omit<ShapeMeshProps, 'shape'>) {
  const meshRef = useRef<THREE.Mesh>(null)
  const baseSpeed = status === 'thinking' ? 0.025 : status === 'acting' ? 0.05 : 0.008
  const scale = status === 'acting' ? 1.15 : status === 'blocked' ? 0.9 : 1

  useFrame((_, delta) => {
    if (!meshRef.current) return
    meshRef.current.rotation.x += delta * baseSpeed * 60 * 0.6
    meshRef.current.rotation.y += delta * baseSpeed * 60
    const targetScale = scale
    meshRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.05)
    if (status === 'blocked') {
      meshRef.current.rotation.z = Math.sin(Date.now() * 0.02) * 0.15
    }
  })

  const emissiveIntensity = status === 'thinking' ? 0.6 : status === 'acting' ? 1.2 : 0.3

  return (
    <mesh ref={meshRef}>
      <icosahedronGeometry args={[1, 1]} />
      <meshStandardMaterial
        color={color}
        emissive={status === 'blocked' ? '#ffffff' : color}
        emissiveIntensity={emissiveIntensity}
        roughness={0.3}
        metalness={0.6}
        wireframe={false}
      />
    </mesh>
  )
}

function TorusKnot({ color, status }: Omit<ShapeMeshProps, 'shape'>) {
  const meshRef = useRef<THREE.Mesh>(null)
  const speed = status === 'thinking' ? 0.04 : status === 'acting' ? 0.07 : 0.018

  useFrame((state, delta) => {
    if (!meshRef.current) return
    meshRef.current.rotation.x += delta * speed * 60 * 0.5
    meshRef.current.rotation.y += delta * speed * 60
    // Glitchy flicker for tech agent
    if (status === 'thinking' && Math.random() < 0.005) {
      meshRef.current.visible = false
      setTimeout(() => { if (meshRef.current) meshRef.current.visible = true }, 80)
    }
    if (status === 'blocked') {
      meshRef.current.position.x = Math.sin(state.clock.elapsedTime * 30) * 0.06
    } else {
      meshRef.current.position.x = 0
    }
  })

  return (
    <mesh ref={meshRef}>
      <torusKnotGeometry args={[0.7, 0.22, 128, 16]} />
      <meshStandardMaterial
        color={color}
        emissive={status === 'blocked' ? '#ffffff' : color}
        emissiveIntensity={status === 'thinking' ? 0.7 : status === 'acting' ? 1.2 : 0.25}
        roughness={0.15}
        metalness={0.7}
        wireframe={status === 'thinking'}
      />
    </mesh>
  )
}

function Dodecahedron({ color, status }: Omit<ShapeMeshProps, 'shape'>) {
  const meshRef = useRef<THREE.Mesh>(null)
  const speed = status === 'thinking' ? 0.015 : status === 'acting' ? 0.03 : 0.006

  useFrame((state, delta) => {
    if (!meshRef.current) return
    meshRef.current.rotation.y += delta * speed * 60
    meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.4) * 0.15
    const pulse = status === 'thinking' ? Math.sin(state.clock.elapsedTime * 4) * 0.04 + 1 : 1
    meshRef.current.scale.setScalar(pulse)
    if (status === 'blocked') {
      meshRef.current.rotation.z = Math.sin(Date.now() * 0.02) * 0.2
    }
  })

  return (
    <mesh ref={meshRef}>
      <dodecahedronGeometry args={[1, 0]} />
      <meshStandardMaterial
        color={color}
        emissive={status === 'blocked' ? '#ffffff' : color}
        emissiveIntensity={status === 'thinking' ? 0.5 : status === 'acting' ? 1.0 : 0.2}
        roughness={0.4}
        metalness={0.5}
      />
    </mesh>
  )
}

function Octahedron({ color, status }: Omit<ShapeMeshProps, 'shape'>) {
  const meshRef = useRef<THREE.Mesh>(null)
  const speed = status === 'acting' ? 0.0 : 0.008
  const lastBlink = useRef(0)

  useFrame((state, delta) => {
    if (!meshRef.current) return
    // Finance: rigid, minimal motion — freezes on block
    if (status !== 'blocked') {
      meshRef.current.rotation.y += delta * speed * 60
      meshRef.current.rotation.x += delta * speed * 60 * 0.3
    } else {
      // Flash white periodically
      if (state.clock.elapsedTime - lastBlink.current > 0.4) {
        lastBlink.current = state.clock.elapsedTime
      }
      meshRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 25) * 0.08
    }
  })

  return (
    <mesh ref={meshRef}>
      <octahedronGeometry args={[1.1, 0]} />
      <meshStandardMaterial
        color={status === 'blocked' ? '#ffffff' : color}
        emissive={status === 'blocked' ? '#ef4444' : color}
        emissiveIntensity={status === 'blocked' ? 1.5 : status === 'thinking' ? 0.4 : 0.2}
        roughness={0.1}
        metalness={0.9}
      />
    </mesh>
  )
}

function DistortSphere({ color, status }: Omit<ShapeMeshProps, 'shape'>) {
  // Fallback
  return (
    <mesh>
      <sphereGeometry args={[1, 32, 32]} />
      <MeshDistortMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.3}
        distort={status === 'thinking' ? 0.5 : 0.2}
        speed={2}
        roughness={0.4}
      />
    </mesh>
  )
}

function Scene({ shape, color, status }: ShapeMeshProps) {
  const lightColor = color

  return (
    <>
      <ambientLight intensity={0.3} />
      <pointLight position={[3, 3, 3]} intensity={1.2} color={lightColor} />
      <pointLight position={[-3, -2, -2]} intensity={0.4} color="#3b82f6" />
      {shape === 'icosahedron' && <Icosahedron color={color} status={status} />}
      {shape === 'torusKnot' && <TorusKnot color={color} status={status} />}
      {shape === 'dodecahedron' && <Dodecahedron color={color} status={status} />}
      {shape === 'octahedron' && <Octahedron color={color} status={status} />}
      {!['icosahedron','torusKnot','dodecahedron','octahedron'].includes(shape) && (
        <DistortSphere color={color} status={status} />
      )}
    </>
  )
}

interface AgentShapeProps {
  shape: AgentShapeType
  color: string
  status: AgentStatus
  size?: number
}

export function AgentShape({ shape, color, status, size = 140 }: AgentShapeProps) {
  return (
    <div style={{ width: size, height: size }} className="mx-auto">
      <Canvas
        camera={{ position: [0, 0, 3.5], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <Scene shape={shape} color={color} status={status} />
      </Canvas>
    </div>
  )
}
