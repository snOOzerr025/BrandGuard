"use client";

import React from "react";
import { motion, Variants } from "framer-motion";
import { ArrowRight, Sparkles, Activity, ShieldCheck, Zap, Database, ArrowUpRight } from "lucide-react";
import { useDashboardStore } from "../../store/useDashboardStore";

const STATS = [
  { value: "86.4%", label: "SOTA ABSA F1-SCORE", sub: "DeBERTa-v3 ACD pipeline", color: "#FF5A36" },
  { value: "215", label: "REV / SECOND", sub: "Distributed Celery throughput", color: "#FAF6F0" },
  { value: "98.4%", label: "CITATION ACCURACY", sub: "Grounded Ragas benchmark", color: "#9CAF88" },
  { value: "3σ", label: "STATISTICAL BOUNDS", sub: "Deseasonalized EWMA SPC", color: "#FFA6B6" },
];

export const HeroSection: React.FC = () => {
  const { launchDashboard } = useDashboardStore();

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.04,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 25 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] as const },
    },
  };

  return (
    <section className="relative min-h-[95vh] flex flex-col justify-center pt-28 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto overflow-hidden">
      {/* Background Subtle Watermark Layers for Architectural Depth */}
      <div className="absolute top-12 right-0 text-[12rem] md:text-[18rem] font-serif italic text-white/[0.025] select-none pointer-events-none leading-none -z-10">
        Veritas
      </div>
      <div className="absolute -bottom-8 left-0 text-[8rem] md:text-[12rem] font-mono text-white/[0.018] select-none pointer-events-none uppercase -z-10">
        SPC-3σ
      </div>

      {/* Frame 1 Top Metadata Bar */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-4 mb-10 text-xs font-mono text-[#8A8F9E]"
      >
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#FF5A36] shadow-[0_0_10px_#FF5A36]" />
          <span className="text-[#FAF6F0] font-semibold tracking-widest uppercase">
            FRAME 01 // EDITORIAL OVERTURE
          </span>
          <span className="text-white/20">•</span>
          <span className="text-[#FF5A36]">DEBERTA-V3 ENGINE</span>
        </div>
        <div className="hidden sm:flex items-center gap-6">
          <span>LAT: 37.7749° N</span>
          <span>DETERMINISTIC LEVEL: 100%</span>
          <span className="text-[#FAF6F0]">LATENCY: 8.4ms</span>
        </div>
      </motion.div>

      {/* Main Shift-Balance 2-Column Hero Composition */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center mb-16">
        {/* Left Column: Typographical Powerhouse (7 cols) */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="lg:col-span-7 space-y-6"
        >
          {/* Subheading pill with Coral Orange accent */}
          <motion.div variants={itemVariants}>
            <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-[#0F1A38] border border-[#FF5A36]/30 shadow-[0_0_20px_rgba(255,90,54,0.15)]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#FF5A36] shadow-[0_0_8px_#FF5A36]" />
              <span className="font-mono text-xs font-semibold tracking-widest text-[#FAF6F0] uppercase">
                ✦ DETERMINISTIC AUDIT PLATFORM
              </span>
            </div>
          </motion.div>

          {/* Brutalist + High-Fashion Serif Italic Typographical Contrast */}
          <motion.div variants={itemVariants} className="space-y-1">
            <h1 className="text-5xl sm:text-7xl lg:text-[5.8rem] font-black tracking-[-0.05em] uppercase text-[#FAF6F0] leading-[0.92]">
              STAR RATINGS
            </h1>
            <h1 className="text-4xl sm:text-6xl lg:text-[5.2rem] font-serif italic font-normal text-[#FF5A36] leading-[0.95]">
              are fundamentally flawed.
            </h1>
            <h1 className="text-5xl sm:text-7xl lg:text-[5.8rem] font-black tracking-[-0.05em] uppercase text-[#FAF6F0] leading-[0.92]">
              WE PROVE WHY<span className="text-[#FF5A36]">.</span>
            </h1>
          </motion.div>

          {/* Editorial Thesis Statement */}
          <motion.p
            variants={itemVariants}
            className="text-base sm:text-lg text-[#FAF6F0]/80 font-sans max-w-2xl leading-relaxed pt-2"
          >
            Averaged 4.6★ scores conceal catastrophic batch defects. BrandGuard unifies{" "}
            <strong className="text-white font-semibold">DeBERTa-v3 multi-label ABSA</strong>,{" "}
            <strong className="text-white font-semibold">HDBSCAN theme induction</strong>, and{" "}
            <strong className="text-white font-semibold">3σ EWMA control charts</strong> into an
            uncompromising decision intelligence engine.
          </motion.p>

          {/* CTAs with Coral Orange Glow & Shift Balance */}
          <motion.div
            variants={itemVariants}
            className="flex flex-wrap items-center gap-4 pt-4"
          >
            <button
              onClick={() => launchDashboard()}
              className="group relative inline-flex items-center gap-3 px-8 py-4 rounded-2xl bg-[#FF5A36] hover:bg-[#FF451D] text-white font-mono font-bold text-xs sm:text-sm tracking-wider uppercase transition-all duration-300 shadow-[0_0_35px_rgba(255,90,54,0.4)] hover:shadow-[0_0_55px_rgba(255,90,54,0.6)] hover:scale-[1.02] active:scale-[0.98]"
            >
              <span>EXPLORE LIVE DASHBOARD</span>
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </button>

            <a
              href="#architecture"
              className="inline-flex items-center gap-2 px-6 py-4 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-[#FF5A36]/40 text-[#FAF6F0] font-mono text-xs tracking-wider uppercase transition-all duration-300"
            >
              <span>ARCHITECTURAL BENCHMARKS</span>
              <ArrowUpRight className="w-3.5 h-3.5 text-[#FF5A36]" />
            </a>
          </motion.div>
        </motion.div>

        {/* Right Column: Floating High-Fashion Product Artifact & Live Telemetry (5 cols) */}
        <motion.div
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.9, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="lg:col-span-5 relative"
        >
          {/* Ambient Glow */}
          <div className="absolute -inset-4 bg-gradient-to-r from-[#FF5A36]/20 via-[#FFA6B6]/15 to-transparent rounded-3xl blur-2xl pointer-events-none" />

          {/* Main Editorial Card with Generated Image */}
          <div className="relative rounded-3xl bg-[#0E1833]/90 border border-white/15 p-4 shadow-2xl backdrop-blur-xl group hover:border-[#FF5A36]/60 transition-all duration-500">
            <div className="relative aspect-[3/4] rounded-2xl overflow-hidden mb-4 bg-[#0A1128]">
              <img
                src="/images/product_pedestal.jpg"
                alt="Sony WH-1000XM5 Hardware Audit"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />

              {/* Top Glass Badge */}
              <div className="absolute top-4 left-4 right-4 flex items-center justify-between pointer-events-none">
                <span className="px-3 py-1 rounded-full bg-black/75 backdrop-blur-md border border-white/20 text-[11px] font-mono font-medium text-white flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#FF5A36] animate-pulse" />
                  SONY WH-1000XM5
                </span>
                <span className="px-2.5 py-1 rounded-full bg-[#DC2626]/80 text-white font-mono text-[10px] font-bold">
                  3σ BREACH
                </span>
              </div>

              {/* Bottom Hologram Telemetry Overlay */}
              <div className="absolute bottom-4 left-4 right-4 p-3.5 rounded-xl bg-[#0A1128]/85 backdrop-blur-md border border-white/15 text-xs font-mono space-y-1.5">
                <div className="flex items-center justify-between text-[#8A8F9E]">
                  <span>DISCREPANCY DETECTED</span>
                  <span className="text-[#FF5A36] font-bold">-0.42★ STAR DRAG</span>
                </div>
                <div className="text-white text-[11px] line-clamp-1 font-sans">
                  &ldquo;ANC is truly top tier, but hinge swivel snapped on day 12...&rdquo;
                </div>
                <div className="flex items-center gap-2 pt-1 border-t border-white/10 text-[10px] text-[#9CAF88]">
                  <span>Aspect: Quality</span>
                  <span>•</span>
                  <span>Polarity: Negative</span>
                  <span>•</span>
                  <span>Confidence: 99.2%</span>
                </div>
              </div>
            </div>

            {/* Sub-card Shift Balance Tag */}
            <div className="flex items-center justify-between px-2 pt-1 text-xs font-mono text-[#8A8F9E]">
              <span>SAMPLE SIZE: 1,420 REVIEWS</span>
              <span className="text-[#FAF6F0] font-semibold">LEAVE-ONE-OUT ATTRIBUTION</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Hero Stats Ribbon in Warm Ivory, Coral, and Sage */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.4 }}
        className="grid grid-cols-2 lg:grid-cols-4 gap-4 p-6 rounded-3xl bg-[#0F1A38]/70 border border-white/10 backdrop-blur-xl shadow-xl"
      >
        {STATS.map((stat, i) => (
          <div
            key={stat.label}
            className={`space-y-1 p-3 ${
              i !== STATS.length - 1 ? "lg:border-r lg:border-white/10" : ""
            }`}
          >
            <div
              className="text-3xl sm:text-4xl font-black font-mono tracking-tight"
              style={{ color: stat.color }}
            >
              {stat.value}
            </div>
            <div className="text-xs font-mono font-semibold tracking-wider text-[#FAF6F0] uppercase">
              {stat.label}
            </div>
            <div className="text-[11px] font-mono text-[#8A8F9E]">{stat.sub}</div>
          </div>
        ))}
      </motion.div>
    </section>
  );
};
