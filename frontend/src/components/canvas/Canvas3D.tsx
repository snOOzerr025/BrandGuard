"use client";

import React, { useRef, useMemo, useEffect, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { useDashboardStore } from "../../store/useDashboardStore";

function ParticleLattice() {
  const pointsRef = useRef<THREE.Points>(null!);
  const secondaryPointsRef = useRef<THREE.Points>(null!);
  const mouse = useRef({ x: 0, y: 0, targetX: 0, targetY: 0 });
  const { currentView, isTransitioning } = useDashboardStore();
  const { camera } = useThree();

  const particleCount = 480;
  const secondaryCount = 260;

  // Primary warm ivory & coral particles
  const [positions, velocities] = useMemo(() => {
    const pos = new Float32Array(particleCount * 3);
    const vel = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 36;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 26;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 36;

      vel[i * 3] = (Math.random() - 0.5) * 0.012;
      vel[i * 3 + 1] = (Math.random() - 0.5) * 0.012;
      vel[i * 3 + 2] = (Math.random() - 0.5) * 0.012;
    }

    return [pos, vel];
  }, [particleCount]);

  // Secondary coral accent particles
  const [secPositions, secVelocities] = useMemo(() => {
    const pos = new Float32Array(secondaryCount * 3);
    const vel = new Float32Array(secondaryCount * 3);

    for (let i = 0; i < secondaryCount; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 32;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 22;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 32;

      vel[i * 3] = (Math.random() - 0.5) * 0.016;
      vel[i * 3 + 1] = (Math.random() - 0.5) * 0.016;
      vel[i * 3 + 2] = (Math.random() - 0.5) * 0.016;
    }

    return [pos, vel];
  }, [secondaryCount]);

  // Track mouse coordinates
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      mouse.current.targetX = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.current.targetY = -(e.clientY / window.innerHeight) * 2 + 1;
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  useFrame((state, delta) => {
    // Smooth lerp mouse
    mouse.current.x += (mouse.current.targetX - mouse.current.x) * 0.05;
    mouse.current.y += (mouse.current.targetY - mouse.current.y) * 0.05;

    // Camera zoom transition physics
    if (isTransitioning) {
      // Zoom through the particle mesh
      camera.position.z = THREE.MathUtils.lerp(camera.position.z, -16, 0.045);
      camera.rotation.z += 0.003;
    } else if (currentView === "dashboard") {
      // Stationary elevated cockpit view
      camera.position.z = THREE.MathUtils.lerp(camera.position.z, 9, 0.05);
      camera.position.x = THREE.MathUtils.lerp(camera.position.x, mouse.current.x * 1.5, 0.03);
      camera.position.y = THREE.MathUtils.lerp(camera.position.y, mouse.current.y * 1.2 + 2, 0.03);
    } else {
      // Editorial Landing View with reactive parallax
      camera.position.z = THREE.MathUtils.lerp(camera.position.z, 22, 0.05);
      camera.position.x = THREE.MathUtils.lerp(camera.position.x, mouse.current.x * 3.2, 0.03);
      camera.position.y = THREE.MathUtils.lerp(camera.position.y, mouse.current.y * 2.2, 0.03);
    }

    // Update primary particles
    if (pointsRef.current) {
      const posAttr = pointsRef.current.geometry.attributes.position as THREE.BufferAttribute;
      const posArr = posAttr.array as Float32Array;

      for (let i = 0; i < particleCount; i++) {
        posArr[i * 3] += velocities[i * 3];
        posArr[i * 3 + 1] += velocities[i * 3 + 1];
        posArr[i * 3 + 2] += velocities[i * 3 + 2];

        // Boundary reflection
        if (Math.abs(posArr[i * 3]) > 18) velocities[i * 3] *= -1;
        if (Math.abs(posArr[i * 3 + 1]) > 13) velocities[i * 3 + 1] *= -1;
        if (Math.abs(posArr[i * 3 + 2]) > 18) velocities[i * 3 + 2] *= -1;
      }
      posAttr.needsUpdate = true;
      pointsRef.current.rotation.y += delta * 0.015;
    }

    // Update secondary particles
    if (secondaryPointsRef.current) {
      const secAttr = secondaryPointsRef.current.geometry.attributes.position as THREE.BufferAttribute;
      const secArr = secAttr.array as Float32Array;

      for (let i = 0; i < secondaryCount; i++) {
        secArr[i * 3] += secVelocities[i * 3];
        secArr[i * 3 + 1] += secVelocities[i * 3 + 1];
        secArr[i * 3 + 2] += secVelocities[i * 3 + 2];

        if (Math.abs(secArr[i * 3]) > 16) secVelocities[i * 3] *= -1;
        if (Math.abs(secArr[i * 3 + 1]) > 11) secVelocities[i * 3 + 1] *= -1;
        if (Math.abs(secArr[i * 3 + 2]) > 16) secVelocities[i * 3 + 2] *= -1;
      }
      secAttr.needsUpdate = true;
      secondaryPointsRef.current.rotation.y -= delta * 0.02;
    }
  });

  return (
    <group>
      {/* Primary Warm Ivory & Soft Gold Particles */}
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        </bufferGeometry>
        <pointsMaterial
          size={0.14}
          color="#FAF6F0"
          transparent
          opacity={0.65}
          blending={THREE.AdditiveBlending}
        />
      </points>

      {/* Secondary Coral Orange Glowing Particles */}
      <points ref={secondaryPointsRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[secPositions, 3]} />
        </bufferGeometry>
        <pointsMaterial
          size={0.18}
          color="#FF5A36"
          transparent
          opacity={0.8}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </group>
  );
}

export const Canvas3D: React.FC = () => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="fixed inset-0 bg-[#0A1128] -z-10" />;
  }

  return (
    <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden bg-[#0A1128]">
      {/* Deep Editorial Blue and Coral Ambient Vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(255,90,54,0.14),transparent_65%)] z-0" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(10,17,40,0.9),transparent_70%)] z-0" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_right,rgba(156,175,136,0.08),transparent_60%)] z-0" />

      <Canvas
        camera={{ position: [0, 0, 22], fov: 60 }}
        gl={{ antialias: true, alpha: true }}
        className="w-full h-full"
      >
        <ParticleLattice />
      </Canvas>
    </div>
  );
};
