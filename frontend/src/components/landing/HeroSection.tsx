"use client";

import React from "react";
import { motion, Variants } from "framer-motion";
import { ArrowRight, Sparkles, Activity, ShieldCheck, Zap, Database } from "lucide-react";
import { useDashboardStore } from "../../store/useDashboardStore";

const HEADLINE_LINE_1 = "STAR RATINGS ARE LIES.";
const HEADLINE_LINE_2 = "WE PROVE WHY.";

const STATS = [
  { value: "86.4%", label: "SOTA ABSA F1-SCORE", sub: "DeBERTa-v3 ACD pipeline" },
  { value: "215", label: "REV / SECOND", sub: "Distributed Celery throughput" },
  { value: "98.4%", label: "CITATION ACCURACY", sub: "Grounded Ragas benchmark" },
  { value: "3σ", label: "STATISTICAL BOUNDS", sub: "Deseasonalized EWMA SPC" },
];

export const HeroSection: React.FC = () => {
  const { launchDashboard } = useDashboardStore();

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.03,
      },
    },
  };

  const letterVariants: Variants = {
    hidden: { opacity: 0, y: 35, rotateX: 45 },
    visible: {
      opacity: 1,
      y: 0,
      rotateX: 0,
      transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] as const },
    },
  };

  return (
    <section className="relative min-h-[90vh] flex flex-col justify-center pt-32 pb-20 px-6 max-w-7xl mx-auto">
      {/* Subheading pill */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-[#13151A] border border-white/10 w-fit mb-8 shadow-inner"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] shadow-[0_0_8px_#10B981]" />
        <span className="font-mono text-xs font-semibold tracking-widest text-[#10B981] uppercase">
          ✦ DETERMINISTIC REVIEW INTELLIGENCE ENGINE
        </span>
      </motion.div>

      {/* Massive Brutalist Kinetic Headline */}
      <div className="space-y-1 mb-8 overflow-hidden select-none">
        <motion.h1
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="text-4xl sm:text-6xl md:text-8xl lg:text-[6.5rem] font-black tracking-[-0.05em] uppercase text-white leading-[0.92] flex flex-wrap"
        >
          {HEADLINE_LINE_1.split("").map((char, index) => (
            <motion.span
              key={index}
              variants={letterVariants}
              className={char === " " ? "inline-block w-4 sm:w-6" : "inline-block"}
            >
              {char}
            </motion.span>
          ))}
        </motion.h1>

        <motion.h1
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="text-4xl sm:text-6xl md:text-8xl lg:text-[6.5rem] font-black tracking-[-0.05em] uppercase bg-gradient-to-r from-white via-slate-200 to-[#10B981] bg-clip-text text-transparent leading-[0.92] flex flex-wrap"
        >
          {HEADLINE_LINE_2.split("").map((char, index) => (
            <motion.span
              key={index}
              variants={letterVariants}
              className={char === " " ? "inline-block w-4 sm:w-6" : "inline-block"}
            >
              {char}
            </motion.span>
          ))}
        </motion.h1>
      </div>

      {/* Editorial Description */}
      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.5 }}
        className="text-base sm:text-xl text-[#8A8F9E] max-w-2xl font-normal leading-relaxed mb-12"
      >
        Enterprise ABSA intelligence powered by DeBERTa-v3 multi-label aspect decomposition,
        HDBSCAN unsupervised micro-theme clustering, and zero-hallucination hybrid RAG
        grounded in deterministic SQL metrics.
      </motion.p>

      {/* Call to Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.65 }}
        className="flex flex-col sm:flex-row items-stretch sm:items-center gap-5 mb-20"
      >
        <motion.button
          type="button"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => launchDashboard()}
          className="px-8 py-4 rounded-full bg-[#10B981] hover:bg-[#059669] text-[#0D0E10] font-mono font-bold text-sm tracking-wider flex items-center justify-center gap-3 transition-colors shadow-[0_0_35px_rgba(16,185,129,0.35)] cursor-pointer"
        >
          <span>EXPLORE LIVE DASHBOARD</span>
          <span>▶</span>
        </motion.button>

        <a
          href="#benchmarks"
          className="px-8 py-4 rounded-full bg-[#13151A] hover:bg-[#1A1D24] text-white border border-white/10 hover:border-white/20 font-mono text-sm tracking-wider flex items-center justify-center gap-2.5 transition-colors cursor-pointer"
        >
          <span>ARCHITECTURAL BENCHMARKS</span>
          <span>❖</span>
        </a>
      </motion.div>

      {/* Hero Stats Ribbon */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.8 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-10 border-t border-white/10"
      >
        {STATS.map((stat, idx) => (
          <div
            key={idx}
            className="p-5 rounded-2xl bg-[#13151A]/60 border border-white/5 backdrop-blur-md hover:border-[#10B981]/30 transition-colors group"
          >
            <div className="text-3xl sm:text-4xl font-black font-mono tracking-tight text-white group-hover:text-[#10B981] transition-colors mb-1">
              {stat.value}
            </div>
            <div className="text-xs font-mono font-bold tracking-wider text-slate-300 uppercase mb-0.5">
              {stat.label}
            </div>
            <div className="text-[11px] text-[#8A8F9E] font-sans">
              {stat.sub}
            </div>
          </div>
        ))}
      </motion.div>
    </section>
  );
};
