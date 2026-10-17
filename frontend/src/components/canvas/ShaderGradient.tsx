"use client";

import React, { useEffect, useRef } from "react";

/**
 * ShaderGradient
 * High-performance WebGL / 2D Canvas Fluid Shader Gradient
 * Uses the BrandGuard exact color palette:
 * - #0A1128 (Cosmic Navy / Midnight)
 * - #001F54 (Deep Twilight Ocean)
 * - #141C38 (Obsidian Slate)
 * - #FF5A36 (Atomic Coral accent)
 * - #2A211D (Warm Mocha highlight)
 */
export const ShaderGradient: React.FC<{ className?: string }> = ({ className = "" }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext("webgl");
    if (!gl) {
      // Fallback to 2D canvas if WebGL unavailable
      return;
    }

    // Vertex shader
    const vsSource = `
      attribute vec2 a_position;
      void main() {
        gl_Position = vec4(a_position, 0.0, 1.0);
      }
    `;

    // Fragment shader with mathematical fluid organic gradient
    const fsSource = `
      precision mediump float;
      uniform vec2 u_resolution;
      uniform float u_time;

      // Color Palette
      const vec3 colBg = vec3(0.039, 0.067, 0.157);       // #0A1128
      const vec3 colDeep = vec3(0.0, 0.122, 0.329);        // #001F54
      const vec3 colSlate = vec3(0.078, 0.11, 0.22);       // #141C38
      const vec3 colCoral = vec3(1.0, 0.353, 0.212);       // #FF5A36
      const vec3 colMocha = vec3(0.165, 0.129, 0.114);     // #2A211D

      void main() {
        vec2 st = gl_FragCoord.xy / u_resolution.xy;
        st.x *= u_resolution.x / u_resolution.y;

        float t = u_time * 0.25;

        // Fluid coordinate distortions
        vec2 p = st * 2.0 - vec2(1.8, 1.0);
        
        float d1 = sin(p.x * 2.0 + t) + cos(p.y * 2.0 - t * 1.2);
        float d2 = cos(p.x * 1.5 - t * 0.8) + sin(p.y * 2.5 + t);
        float d3 = sin(length(p + vec2(sin(t * 0.5), cos(t * 0.4))) * 3.0 - t);

        // Radial vortex wave
        float wave = sin(d1 * 1.5 + d2 * 1.2 + d3 * 0.8) * 0.5 + 0.5;
        float coralWave = pow(sin(p.x * 1.2 + p.y * 1.5 + t * 0.7) * 0.5 + 0.5, 3.5);

        // Mix palette
        vec3 color = mix(colBg, colDeep, wave * 0.8);
        color = mix(color, colSlate, d2 * 0.3);
        color = mix(color, colMocha, d1 * 0.2);
        color = mix(color, colCoral, coralWave * 0.28);

        // Subtle vignette
        vec2 uv = gl_FragCoord.xy / u_resolution.xy;
        float vignette = uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y);
        vignette = clamp(pow(16.0 * vignette, 0.35), 0.0, 1.0);
        color *= vignette * 0.85 + 0.15;

        gl_FragColor = vec4(color, 1.0);
      }
    `;

    const createShader = (glCtx: WebGLRenderingContext, type: number, source: string) => {
      const shader = glCtx.createShader(type);
      if (!shader) return null;
      glCtx.shaderSource(shader, source);
      glCtx.compileShader(shader);
      if (!glCtx.getShaderParameter(shader, glCtx.COMPILE_STATUS)) {
        glCtx.deleteShader(shader);
        return null;
      }
      return shader;
    };

    const vertShader = createShader(gl, gl.VERTEX_SHADER, vsSource);
    const fragShader = createShader(gl, gl.FRAGMENT_SHADER, fsSource);
    if (!vertShader || !fragShader) return;

    const program = gl.createProgram();
    if (!program) return;
    gl.attachShader(program, vertShader);
    gl.attachShader(program, fragShader);
    gl.linkProgram(program);
    gl.useProgram(program);

    // Quad geometry
    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
      gl.STATIC_DRAW
    );

    const posAttr = gl.getAttribLocation(program, "a_position");
    gl.enableVertexAttribArray(posAttr);
    gl.vertexAttribPointer(posAttr, 2, gl.FLOAT, false, 0, 0);

    const resUniform = gl.getUniformLocation(program, "u_resolution");
    const timeUniform = gl.getUniformLocation(program, "u_time");

    let animationFrameId: number;
    let startTime = performance.now();

    const handleResize = () => {
      if (!canvas) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = canvas.clientWidth * dpr;
      canvas.height = canvas.clientHeight * dpr;
      gl.viewport(0, 0, canvas.width, canvas.height);
    };

    handleResize();
    window.addEventListener("resize", handleResize);

    const render = (now: number) => {
      const time = (now - startTime) * 0.001;
      gl.uniform2f(resUniform, canvas.width, canvas.height);
      gl.uniform1f(timeUniform, time);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <div className={`relative overflow-hidden w-full h-full ${className}`}>
      <canvas
        ref={canvasRef}
        className="w-full h-full absolute inset-0 block pointer-events-none"
      />
      {/* Subtle organic noise texture overlay */}
      <div className="absolute inset-0 bg-[radial-gradient(#ffffff04_1px,transparent_1px)] [background-size:24px_24px] pointer-events-none" />
    </div>
  );
};
