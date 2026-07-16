"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

/**
 * "Cuốn sổ tay quy chế" — vật thể 3D thật (WebGL/R3F) gắn với đời sống
 * sinh viên thay vì hình khối trừu tượng: một cuốn sách đang mở (chính
 * là corpus 10 văn bản IUH của hệ thống), vài trang giấy bay lơ lửng
 * phía trên và cột hạt tri thức bốc lên từ gáy sách.
 *
 * Theme-aware: nhận bảng màu theo light/dark từ HeroVisual. Toàn bộ
 * animation trong useFrame (không setState mỗi frame).
 */

import { DARK_COLORS, type CoreColors } from "./core-colors";

function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };
}

/** Cột hạt "tri thức" bốc lên từ gáy sách, lặp vô tận. */
function RisingKnowledge({ color, count = 220 }: { color: string; count?: number }) {
  const ref = useRef<THREE.Points>(null);
  const data = useMemo(() => {
    const rand = seededRandom(20260716);
    const positions = new Float32Array(count * 3);
    const speeds = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      const r = Math.sqrt(rand()) * 1.3;
      const theta = rand() * Math.PI * 2;
      positions[i * 3] = Math.cos(theta) * r;
      positions[i * 3 + 1] = rand() * 2.6 - 0.2; // từ mặt sách lên
      positions[i * 3 + 2] = Math.sin(theta) * r * 0.7;
      speeds[i] = 0.25 + rand() * 0.5;
    }
    return { positions, speeds };
  }, [count]);

  useFrame((_, delta) => {
    const pts = ref.current;
    if (!pts) return;
    const pos = pts.geometry.attributes.position as THREE.BufferAttribute;
    const arr = pos.array as Float32Array;
    for (let i = 0; i < count; i++) {
      arr[i * 3 + 1] += data.speeds[i] * delta;
      if (arr[i * 3 + 1] > 2.4) arr[i * 3 + 1] = -0.2;
    }
    pos.needsUpdate = true;
  });

  return (
    <points ref={ref} position={[0, 0.1, 0]}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[data.positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.022} color={color} transparent opacity={0.5} sizeAttenuation depthWrite={false} />
    </points>
  );
}

/** Một trang giấy bay lơ lửng — nghiêng nhẹ, dập dềnh theo pha riêng. */
function FloatingPage({
  color,
  position,
  phase,
  rotY,
}: {
  color: string;
  position: [number, number, number];
  phase: number;
  rotY: number;
}) {
  const ref = useRef<THREE.Group>(null);
  useFrame((state) => {
    const g = ref.current;
    if (!g) return;
    const t = state.clock.elapsedTime;
    g.position.y = position[1] + Math.sin(t * 0.9 + phase) * 0.12;
    g.rotation.z = Math.sin(t * 0.7 + phase) * 0.1;
    g.rotation.y = rotY + Math.sin(t * 0.5 + phase) * 0.15;
  });
  return (
    <group ref={ref} position={position} rotation={[0.15, rotY, 0]}>
      <mesh>
        <planeGeometry args={[0.62, 0.84]} />
        <meshStandardMaterial color={color} side={THREE.DoubleSide} roughness={0.9} metalness={0} />
      </mesh>
      {/* các "dòng chữ" trên trang — thanh mảnh tối màu */}
      {[0.26, 0.14, 0.02, -0.1, -0.22].map((y, i) => (
        <mesh key={i} position={[0, y, 0.002]}>
          <planeGeometry args={[i % 3 === 2 ? 0.3 : 0.44, 0.025]} />
          <meshBasicMaterial color="#94a3b8" transparent opacity={0.55} side={THREE.DoubleSide} />
        </mesh>
      ))}
    </group>
  );
}

/** Nửa cuốn sách (bìa + chồng trang), hinge tại gáy (x=0). */
function BookHalf({ side, colors }: { side: 1 | -1; colors: CoreColors }) {
  const openAngle = 0.38; // rad
  return (
    <group rotation={[0, 0, side * openAngle]}>
      {/* bìa */}
      <mesh position={[side * 0.78, -0.07, 0]}>
        <boxGeometry args={[1.56, 0.07, 2.15]} />
        <meshStandardMaterial color={colors.cover} roughness={0.6} metalness={0.1} />
      </mesh>
      {/* chồng trang */}
      <mesh position={[side * 0.75, 0.015, 0]}>
        <boxGeometry args={[1.44, 0.1, 2.02]} />
        <meshStandardMaterial color={colors.page} roughness={0.95} />
      </mesh>
    </group>
  );
}

function BookScene({ animate, colors }: { animate: boolean; colors: CoreColors }) {
  const tilt = useRef<THREE.Group>(null);
  const spin = useRef<THREE.Group>(null);
  const glowMat = useRef<THREE.MeshBasicMaterial>(null);

  useFrame((state, delta) => {
    if (!animate) return;
    const t = state.clock.elapsedTime;
    if (spin.current) spin.current.rotation.y += delta * 0.16;
    if (tilt.current) {
      tilt.current.rotation.x = THREE.MathUtils.lerp(tilt.current.rotation.x, 0.42 + state.pointer.y * -0.14, 0.04);
      tilt.current.rotation.z = THREE.MathUtils.lerp(tilt.current.rotation.z, state.pointer.x * 0.08, 0.04);
      tilt.current.position.y = Math.sin(t * 0.6) * 0.09 - 0.15;
    }
    if (glowMat.current) {
      glowMat.current.opacity = 0.5 + Math.sin(t * 1.6) * 0.18;
    }
  });

  return (
    <group ref={tilt} rotation={[0.42, 0, 0]} position={[0, -0.15, 0]}>
      <group ref={spin}>
        {/* thân sách mở */}
        <BookHalf side={-1} colors={colors} />
        <BookHalf side={1} colors={colors} />
        {/* gáy sách */}
        <mesh position={[0, -0.09, 0]}>
          <boxGeometry args={[0.14, 0.09, 2.15]} />
          <meshStandardMaterial color={colors.coverEdge} roughness={0.6} />
        </mesh>
        {/* vệt sáng tri thức dọc gáy */}
        <mesh position={[0, 0.09, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[0.5, 2.0]} />
          <meshBasicMaterial ref={glowMat} color={colors.glow} transparent opacity={0.5} depthWrite={false} />
        </mesh>

        {/* trang giấy bay lơ lửng */}
        <FloatingPage color={colors.page} position={[-0.85, 1.15, 0.15]} phase={0} rotY={0.5} />
        <FloatingPage color={colors.page} position={[0.15, 1.55, -0.25]} phase={2.1} rotY={-0.3} />
        <FloatingPage color={colors.page} position={[0.95, 1.05, 0.3]} phase={4.2} rotY={0.9} />

        <RisingKnowledge color={colors.particle} />
      </group>
    </group>
  );
}

export default function KnowledgeCore({
  animate = true,
  colors = DARK_COLORS,
}: {
  animate?: boolean;
  colors?: CoreColors;
}) {
  return (
    <Canvas
      dpr={[1, 1.75]}
      camera={{ position: [0, 0.7, 5.6], fov: 40 }}
      gl={{ antialias: true, alpha: true }}
      frameloop={animate ? "always" : "demand"}
      style={{ background: "transparent" }}
      aria-hidden
    >
      <ambientLight intensity={colors.ambient} />
      <directionalLight position={[3, 5, 4]} intensity={2.2} />
      <pointLight position={[0, 1.2, 0.5]} intensity={6} color={colors.glow} />
      <BookScene animate={animate} colors={colors} />
    </Canvas>
  );
}
