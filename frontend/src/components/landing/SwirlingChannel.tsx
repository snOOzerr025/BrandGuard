"use client";

import React, { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { Star, ShieldAlert, CheckCircle, ArrowDownRight, Sparkles } from "lucide-react";

interface FloatingItem {
  type: "image" | "review";
  src?: string;
  title: string;
  rating?: number;
  badge: string;
  badgeColor: string;
  quote?: string;
  author?: string;
  aspect?: string;
  impact?: string;
  xOffset: number;
  rotationInit: number;
}

export const SwirlingChannel: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });

  // Transform scroll progress into dynamic swirls and rotations
  const rotateVortex = useTransform(scrollYProgress, [0, 1], [-18, 22]);
  const yShift1 = useTransform(scrollYProgress, [0, 1], [140, -160]);
  const yShift2 = useTransform(scrollYProgress, [0, 1], [220, -220]);
  const yShift3 = useTransform(scrollYProgress, [0, 1], [80, -260]);
  const yShift4 = useTransform(scrollYProgress, [0, 1], [280, -180]);
  const scaleVortex = useTransform(scrollYProgress, [0, 0.5, 1], [0.88, 1.04, 0.9]);
  const opacityFade = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0.3, 1, 1, 0.4]);

  return (
    <section
      ref={containerRef}
      className="relative min-h-[170vh] py-32 overflow-hidden bg-gradient-to-b from-[#0A1128] via-[#121E36] to-[#0A1128] border-y border-white/10"
    >
      {/* Precision architectural background grid with soft grey/white crosshairs */}
      <div className="absolute inset-0 bg-editorial-grid-light opacity-30 pointer-events-none" />

      {/* Atmospheric ambient glows in soft strawberry pink, lime, and coral */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#FFA6B6]/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-1/2 right-1/4 w-[420px] h-[420px] bg-[#84CC16]/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-[#FF5A36]/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Sticky Editorial Heading & Thesis */}
      <div className="sticky top-28 z-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pointer-events-none mb-16">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 backdrop-blur-md bg-[#0A1128]/70 p-8 rounded-3xl border border-white/10 shadow-2xl">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FFA6B6]/15 border border-[#FFA6B6]/30 text-[#FFA6B6] text-xs font-mono tracking-widest uppercase mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>03 / THE SWIRLING COMMERCE CHANNEL</span>
            </div>
            <h2 className="text-3xl sm:text-5xl lg:text-6xl font-black tracking-[-0.04em] text-white">
              WHAT RATINGS PROMISE.{" "}
              <span className="font-serif italic font-normal text-[#FFA6B6]">
                What reality delivers.
              </span>
            </h2>
          </div>
          <div className="max-w-md text-xs sm:text-sm font-mono text-[#FAF6F0]/70 leading-relaxed">
            Every second, thousands of reviews fall across global shopping platforms. Star ratings
            flatten complex sentiment into deceptive averages. BrandGuard extracts the verified truth.
          </div>
        </div>
      </div>

      {/* Swirling 3D Stream of Floating Product, Consumer, and Shopping Artifacts */}
      <motion.div
        style={{
          rotateZ: rotateVortex,
          scale: scaleVortex,
          opacity: opacityFade,
        }}
        className="relative max-w-6xl mx-auto px-4 perspective-[1400px] z-10"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 items-start pt-12">
          {/* Card 1: AI Generated Product Audio Pedestal */}
          <motion.div
            style={{ y: yShift1 }}
            className="group relative rounded-3xl overflow-hidden bg-[#0F1A38] border border-white/15 p-3 shadow-[0_20px_50px_rgba(0,0,0,0.6)] hover:border-[#FF5A36]/60 transition-all duration-500 hover:rotate-1"
          >
            <div className="relative aspect-[3/4] rounded-2xl overflow-hidden mb-3">
              <img
                src="/images/product_pedestal.jpg"
                alt="BrandGuard Hardware Verification"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-black/70 backdrop-blur-md border border-white/20 text-[10px] font-mono text-[#FAF6F0] flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#FF5A36] animate-pulse" />
                <span>SKU TELEMETRY</span>
              </div>
            </div>
            <div className="p-2 space-y-1">
              <div className="flex items-center justify-between text-xs font-mono text-[#8A8F9E]">
                <span>SONY WH-1000XM5</span>
                <span className="text-[#FF5A36] font-bold">142 COMPLAINTS</span>
              </div>
              <p className="text-xs text-[#FAF6F0]/80 font-sans leading-tight">
                Friction hinge seam fatigue identified in Batch #402.
              </p>
            </div>
          </motion.div>

          {/* Card 2: Floating E-Commerce Deception Review (Amazon Verified) */}
          <motion.div
            style={{ y: yShift2 }}
            className="relative rounded-3xl bg-[#131E3D]/90 backdrop-blur-xl border border-[#FFA6B6]/30 p-6 shadow-2xl space-y-4 hover:border-[#DC2626] transition-all duration-300"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1 text-[#F59E0B]">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-[#F59E0B]" />
                ))}
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#DC2626]/20 text-[#DC2626] border border-[#DC2626]/40 flex items-center gap-1">
                <ShieldAlert className="w-3 h-3" />
                DISCREPANCY
              </span>
            </div>

            <div className="space-y-1">
              <span className="text-[11px] font-mono text-[#FFA6B6]">
                Amazon Verified • 2 days ago
              </span>
              <p className="text-sm font-sans text-white leading-relaxed">
                &ldquo;Giving 5 stars because noise cancellation is magnificent.{" "}
                <mark className="bg-[#DC2626]/30 text-[#FFA6B6] px-1 py-0.5 rounded font-semibold">
                  However the right earcup snapped off while adjusting on my commute.
                </mark>{" "}
                Terrified to use the warranty.&rdquo;
              </p>
            </div>

            <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[11px] font-mono text-[#8A8F9E]">
              <span>Extracted Clause: Build Quality</span>
              <span className="text-[#DC2626] font-bold">-0.42★ Drag</span>
            </div>
          </motion.div>

          {/* Card 3: AI Generated Consumer Editorial Portrait */}
          <motion.div
            style={{ y: yShift3 }}
            className="group relative rounded-3xl overflow-hidden bg-[#0F1A38] border border-white/15 p-3 shadow-[0_20px_50px_rgba(0,0,0,0.6)] hover:border-[#84CC16]/60 transition-all duration-500 hover:-rotate-1"
          >
            <div className="relative aspect-[3/4] rounded-2xl overflow-hidden mb-3">
              <img
                src="/images/consumer_editorial.jpg"
                alt="Consumer Experience Editorial"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-black/70 backdrop-blur-md border border-white/20 text-[10px] font-mono text-[#FAF6F0] flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#84CC16] animate-pulse" />
                <span>EXPERIENCE AUDIT</span>
              </div>
            </div>
            <div className="p-2 space-y-1">
              <div className="flex items-center justify-between text-xs font-mono text-[#8A8F9E]">
                <span>FIELD RESEARCH</span>
                <span className="text-[#84CC16] font-bold">98.4% CITATION</span>
              </div>
              <p className="text-xs text-[#FAF6F0]/80 font-sans leading-tight">
                Isolating genuine acoustic satisfaction from logistical frustrations.
              </p>
            </div>
          </motion.div>

          {/* Card 4: AI Generated Shopping Site Packaging & Unboxing */}
          <motion.div
            style={{ y: yShift4 }}
            className="group relative rounded-3xl overflow-hidden bg-[#0F1A38] border border-white/15 p-3 shadow-[0_20px_50px_rgba(0,0,0,0.6)] hover:border-[#FFA6B6]/60 transition-all duration-500 hover:rotate-1"
          >
            <div className="relative aspect-[3/4] rounded-2xl overflow-hidden mb-3">
              <img
                src="/images/unboxing_packaging.jpg"
                alt="Luxury E-Commerce Unboxing Review"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-black/70 backdrop-blur-md border border-white/20 text-[10px] font-mono text-[#FAF6F0] flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#FFA6B6] animate-pulse" />
                <span>UNBOXING TRUTH</span>
              </div>
            </div>
            <div className="p-2 space-y-1">
              <div className="flex items-center justify-between text-xs font-mono text-[#8A8F9E]">
                <span>PACKAGING & PERCEPTION</span>
                <span className="text-[#FFA6B6] font-bold">+18.2 NSS</span>
              </div>
              <p className="text-xs text-[#FAF6F0]/80 font-sans leading-tight">
                Embossed presentation masks customer support post-purchase friction.
              </p>
            </div>
          </motion.div>
        </div>

        {/* Lower Row: Retail Market Display & False-Negative Logistical Card */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center mt-12">
          {/* AI Generated Retail Market Flagship */}
          <div className="relative rounded-3xl overflow-hidden bg-[#0F1A38] border border-white/15 p-4 shadow-2xl flex flex-col md:flex-row gap-6 items-center">
            <div className="relative w-full md:w-1/2 aspect-[3/4] rounded-2xl overflow-hidden flex-shrink-0">
              <img
                src="/images/retail_market_display.jpg"
                alt="Avant-Garde Flagship Market"
                className="w-full h-full object-cover"
              />
            </div>
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#84CC16]/15 border border-[#84CC16]/30 text-[#84CC16] text-xs font-mono">
                <span>FLAGSHIP STORE PILOT</span>
              </div>
              <h3 className="text-2xl font-black text-white font-sans">
                Real-Time Physical & Digital Shelf Attribution
              </h3>
              <p className="text-xs text-[#8A8F9E] leading-relaxed font-mono">
                Connecting online review complaints directly to physical SKU batch returns, warranty
                denials, and retail shelf placement velocity.
              </p>
              <div className="flex gap-4 pt-2">
                <div>
                  <div className="text-lg font-black text-white font-mono">31,400+</div>
                  <div className="text-[10px] font-mono text-[#8A8F9E]">REVIEWS PROCESSED</div>
                </div>
                <div className="w-px h-8 bg-white/10" />
                <div>
                  <div className="text-lg font-black text-[#84CC16] font-mono">-3.85σ</div>
                  <div className="text-[10px] font-mono text-[#8A8F9E]">Z-SCORE ATTRIBUTED</div>
                </div>
              </div>
            </div>
          </div>

          {/* False Negative Logistical Noise Card */}
          <div className="relative rounded-3xl bg-[#18233C]/90 backdrop-blur-xl border border-[#84CC16]/30 p-8 shadow-2xl space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1 text-[#F59E0B]">
                <Star className="w-4 h-4 fill-[#F59E0B]" />
                <Star className="w-4 h-4 text-white/20" />
                <Star className="w-4 h-4 text-white/20" />
                <Star className="w-4 h-4 text-white/20" />
                <Star className="w-4 h-4 text-white/20" />
              </div>
              <span className="px-2.5 py-1 rounded text-[10px] font-mono font-bold bg-[#84CC16]/20 text-[#84CC16] border border-[#84CC16]/40 flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" />
                FILTERED NOISE
              </span>
            </div>

            <div className="space-y-2">
              <span className="text-xs font-mono text-[#84CC16]">
                Target Verified • Delivery Aspect Isolated
              </span>
              <p className="text-sm font-sans text-white leading-relaxed">
                &ldquo;1-Star review left: &lsquo;Courier left the package in the rain outside my garage.&rsquo;{" "}
                <mark className="bg-[#84CC16]/20 text-white px-1 py-0.5 rounded font-mono text-xs">
                  [ABSA Engine isolated aspect to Delivery; Product Quality score preserved at 100%]
                </mark>
                &rdquo;
              </p>
            </div>

            <div className="pt-4 border-t border-white/10 flex items-center justify-between text-xs font-mono">
              <span className="text-[#8A8F9E]">Standard Star Rating: 1.0★</span>
              <span className="text-[#84CC16] font-bold">BrandGuard Normalized: 4.8★</span>
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
};
