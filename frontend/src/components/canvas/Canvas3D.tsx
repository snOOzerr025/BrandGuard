"use client";

import React, { useRef, useMemo, useEffect, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { useDashboardStore } from "../../store/useDashboardStore";

function ParticleLattice() {
  const pointsRef = useRef<THREE.Points>(null!);
  const linesRef = useRef<THREE.LineSegments>(null!);
  const mouse = useRef({ x: 0, y: 0, targetX: 0, targetY: 0 });
  const { currentView, isTransitioning } = useDashboardStore();
  const { camera } = useThree();

  const particleCount = 650;
  const maxDistance = 4.2;

  // Generate particle positions in a 3D volume
  const [positions, velocities] = useMemo(() => {
    const pos = new Float32Array(particleCount * 3);
    const vel = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 35;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 25;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 35;

      vel[i * 3] = (Math.random() - 0.5) * 0.015;
      vel[i * 3 + 1] = (Math.random() - 0.5) * 0.015;
      vel[i * 3 + 2] = (Math.random() - 0.5) * 0.015;
    }

    return [pos, vel];
  }, [particleCount]);

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
      camera.position.z = THREE.MathUtils.lerp(camera.position.z, -15, 0.04);
      camera.rotation.z += 0.002;
    } else if (currentView === "dashboard") {
      // Stationary elevated cockpit view
      camera.position.z = THREE.MathUtils.lerp(camera.position.z, 8, 0.05);
      camera.position.x = THREE.MathUtils.lerp(camera.position.x, mouse.current.x * 1.5, 0.03);
      camera.position.y = THREE.MathUtils.lerp(camera.position.y, mouse.current.y * 1.2 + 2, 0.03);
    } else {
      // Editorial Landing View with reactive parallax
      camera.position.z = THREE.MathUtils.lerp(camera.position.z, 22, 0.05);
      camera.position.x = THREE.MathUtils.lerp(camera.position.x, mouse.current.x * 3.5, 0.03);
      camera.position.y = THREE.MathUtils.lerp(camera.position.y, mouse.current.y * 2.5, 0.03);
    }

    // Update particles
    if (pointsRef.current) {
      const posAttr = pointsRef.current.geometry.attributes.position as THREE.BufferAttribute;
      const posArr = posAttr.array as Float32Array;

      for (let i = 0; i < particleCount; i++) {
        posArr[i * 3] += velocities[i * 3];
        posArr[i * 3 + 1] += velocities[i * 3 + 1];
        posArr[i * 3 + 2] += velocities[i * 3 + 2];

        // Boundary reflection
        if (Math.abs(posArr[i * 3]) > 18) velocities[i * 3] *= -1;
        if (Math.abs(posArr[i * 3 + 1]) > 14) velocities[i * 3 + 1] *= -1;
        if (Math.abs(posArr[i * 3 + 2]) > 18) velocities[i * 3 + 2] *= -1;
      }
      posAttr.needsUpdate = true;
    }

    // Gentle global lattice rotation
    if (pointsRef.current) {
      pointsRef.current.rotation.y += delta * 0.02;
      pointsRef.current.rotation.x = mouse.current.y * 0.1;
    }
  });

  return (
    <group>
      {/* 3D Neural Particles */}
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[positions, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.16}
          color="#10B981"
          transparent
          opacity={0.75}
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
    return <div className="fixed inset-0 bg-[#0D0E10] -z-10" />;
  }

  return (
    <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden bg-[#0D0E10]">
      {/* Ambient Radial Vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(16,185,129,0.12),transparent_70%)] z-0" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_right,rgba(16,185,129,0.06),transparent_60%)] z-0" />

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
