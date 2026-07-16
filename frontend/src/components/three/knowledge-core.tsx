"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

/**
 * "Lõi tri thức" — vật thể 3D thật (WebGL qua React Three Fiber), không
 * phải ảnh tĩnh: vỏ icosahedron wireframe (ranh giới hệ thống / "the
 * gate"), lõi phát sáng bên trong (tri thức đã index), đám hạt quanh lõi
 * (222 chunk thật của corpus) và 3 vành đai quỹ đạo (vòng đời data →
 * eval → feedback).
 *
 * Tương tác: tự xoay chậm + nghiêng theo con trỏ (parallax). Toàn bộ
 * animation chạy trong useFrame (ngoài React render cycle) — không
 * setState mỗi frame.
 */

const ACCENT = "#5eead4"; // xấp xỉ oklch(0.83 0.138 172) — teal accent duy nhất
const ACCENT_DIM = "#2dd4bf";

function seededRandom(seed: number) {
  // LCG nhỏ gọn — kết quả ổn định giữa các lần render (tránh hydration lệch)
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };
}

function ChunkParticles({ count = 500 }: { count?: number }) {
  const ref = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const rand = seededRandom(20260715);
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      // phân bố trong vỏ cầu bán kính 2.05–3.1 (ngoài lõi, quanh vỏ)
      const r = 2.05 + rand() * 1.05;
      const theta = rand() * Math.PI * 2;
      const phi = Math.acos(2 * rand() - 1);
      arr[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      arr[i * 3 + 2] = r * Math.cos(phi);
    }
    return arr;
  }, [count]);

  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y -= delta * 0.03;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.02} color={ACCENT} transparent opacity={0.55} sizeAttenuation depthWrite={false} />
    </points>
  );
}

function OrbitRing({ radius, tiltX, tiltZ, speed }: { radius: number; tiltX: number; tiltZ: number; speed: number }) {
  const ref = useRef<THREE.Mesh>(null);
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += delta * speed;
  });
  return (
    <mesh ref={ref} rotation={[tiltX, 0, tiltZ]}>
      <torusGeometry args={[radius, 0.006, 8, 128]} />
      <meshBasicMaterial color={ACCENT_DIM} transparent opacity={0.28} />
    </mesh>
  );
}

function CoreScene({ animate }: { animate: boolean }) {
  const tilt = useRef<THREE.Group>(null);
  const spin = useRef<THREE.Group>(null);
  const core = useRef<THREE.Mesh>(null);
  const coreMat = useRef<THREE.MeshStandardMaterial>(null);

  useFrame((state, delta) => {
    if (!animate) return;
    const t = state.clock.elapsedTime;
    if (spin.current) spin.current.rotation.y += delta * 0.12;
    if (tilt.current) {
      // nghiêng nhẹ theo con trỏ, lerp cho mượt — không giật theo pixel
      tilt.current.rotation.x = THREE.MathUtils.lerp(tilt.current.rotation.x, state.pointer.y * -0.22, 0.04);
      tilt.current.rotation.z = THREE.MathUtils.lerp(tilt.current.rotation.z, state.pointer.x * 0.12, 0.04);
      tilt.current.position.y = Math.sin(t * 0.6) * 0.08; // float chậm
    }
    if (core.current) {
      const pulse = 1 + Math.sin(t * 1.4) * 0.045;
      core.current.scale.setScalar(pulse);
    }
    if (coreMat.current) {
      coreMat.current.emissiveIntensity = 1.05 + Math.sin(t * 1.4) * 0.25;
    }
  });

  return (
    <group ref={tilt}>
      <group ref={spin}>
        {/* Vỏ hệ thống — wireframe */}
        <lineSegments>
          <edgesGeometry args={[new THREE.IcosahedronGeometry(2, 1)]} />
          <lineBasicMaterial color={ACCENT} transparent opacity={0.32} />
        </lineSegments>

        {/* Lõi phát sáng */}
        <mesh ref={core}>
          <icosahedronGeometry args={[0.85, 1]} />
          <meshStandardMaterial
            ref={coreMat}
            color="#0a1614"
            emissive={ACCENT_DIM}
            emissiveIntensity={1.05}
            roughness={0.35}
            metalness={0.2}
            flatShading
          />
        </mesh>

        <ChunkParticles />
        <OrbitRing radius={1.45} tiltX={Math.PI / 2.6} tiltZ={0.4} speed={0.35} />
        <OrbitRing radius={1.75} tiltX={Math.PI / 1.9} tiltZ={-0.5} speed={-0.22} />
        <OrbitRing radius={2.35} tiltX={Math.PI / 2.15} tiltZ={1.1} speed={0.14} />
      </group>
    </group>
  );
}

export default function KnowledgeCore({ animate = true }: { animate?: boolean }) {
  return (
    <Canvas
      dpr={[1, 1.75]}
      camera={{ position: [0, 0, 6.4], fov: 42 }}
      gl={{ antialias: true, alpha: true }}
      frameloop={animate ? "always" : "demand"}
      style={{ background: "transparent" }}
      aria-hidden
    >
      <ambientLight intensity={0.5} />
      <pointLight position={[4, 4, 5]} intensity={40} color={ACCENT} />
      <pointLight position={[-4, -2, -4]} intensity={12} color="#ffffff" />
      <CoreScene animate={animate} />
    </Canvas>
  );
}
