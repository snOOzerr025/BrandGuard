"use client";

import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SmoothScrollProvider } from "../components/providers/SmoothScrollProvider";
import { Canvas3D } from "../components/canvas/Canvas3D";
import { Navbar } from "../components/navigation/Navbar";
import { HeroSection } from "../components/landing/HeroSection";
import { MarqueeTicker } from "../components/landing/MarqueeTicker";
import { CapabilitiesGrid } from "../components/landing/CapabilitiesGrid";
import { CompetitiveMatrix } from "../components/landing/CompetitiveMatrix";
import { DashboardView } from "../components/dashboard/DashboardView";
import { useDashboardStore } from "../store/useDashboardStore";
import { ArrowUpRight, Cpu, Database, ShieldCheck, Terminal } from "lucide-react";

export default function Home() {
  const { currentView, launchDashboard } = useDashboardStore();

  return (
    <SmoothScrollProvider>
      <main className="relative min-h-screen bg-[#0D0E10] text-white selection:bg-[#10B981]/30 selection:text-white">
        {/* 1. 3D WebGL Neural Particle Lattice Canvas */}
        <div className="fixed inset-0 z-0 pointer-events-none">
          <Canvas3D />
        </div>

        {/* 2. Fixed Top Glass Navigation */}
        <Navbar />

        {/* 3. Main Dynamic Content (Landing vs. Dashboard with Zero-Reload Camera Zoom) */}
        <div className="relative z-10">
          <AnimatePresence mode="wait">
            {currentView === "landing" ? (
              <motion.div
                key="landing-view"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                className="space-y-24 sm:space-y-36 pb-24"
              >
                {/* Hero Section */}
                <HeroSection />

                {/* Infinite Technical Marquee */}
                <MarqueeTicker />

                {/* Editorial Capabilities Bento Grid */}
                <div id="capabilities">
                  <CapabilitiesGrid />
                </div>

                {/* Architecture Invariants Breakdown */}
                <section
                  id="architecture"
                  className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12"
                >
                  <div className="border-t border-white/10 pt-16 flex flex-col md:flex-row md:items-end justify-between gap-6">
                    <div>
                      <div className="text-xs font-mono tracking-widest text-[#10B981] uppercase mb-2">
                        02 / DETERMINISTIC PIPELINE
                      </div>
                      <h2 className="text-3xl sm:text-5xl font-black tracking-tight text-white">
                        THE 4-STAGE INFERENCE ARCHITECTURE.
                      </h2>
                    </div>
                    <p className="text-sm font-mono text-[#8A8F9E] max-w-md">
                      Eliminating subjective reviewer bias via multi-label aspect decomposition,
                      HNSW vector indexing, and statistical process control.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    {[
                      {
                        step: "01",
                        name: "DeBERTa-v3 ABSA",
                        tag: "ONNX Runtime",
                        desc: "Multi-label classification identifying 8 aspect dimensions and polarity at clause level with sub-millisecond execution.",
                      },
                      {
                        step: "02",
                        name: "BGE-Small + HDBSCAN",
                        tag: "Micro-Themes",
                        desc: "Dynamic topic induction clustering latent complaints without pre-defined taxonomies or hallucinations.",
                      },
                      {
                        step: "03",
                        name: "STL + EWMA SPC",
                        tag: "3σ Control",
                        desc: "Deseasonalized control charts with Lucas-Saccucci weighting eliminating false positive alarm fatigue.",
                      },
                      {
                        step: "04",
                        name: "Grounded RAG",
                        tag: "Reciprocal Rank",
                        desc: "Hybrid BM25 + pgvector fusion with exact review UUID citation evidence cards for instant triage.",
                      },
                    ].map((pipe) => (
                      <div
                        key={pipe.step}
                        className="p-6 rounded-2xl bg-[#13151A]/60 border border-white/10 hover:border-[#10B981]/40 backdrop-blur-xl transition-all duration-300 group hover:-translate-y-1"
                      >
                        <div className="text-3xl font-black font-mono text-[#10B981] mb-3 group-hover:scale-105 transition-transform">
                          {pipe.step}
                        </div>
                        <div className="text-xs font-mono text-[#8A8F9E] mb-1">{pipe.tag}</div>
                        <h3 className="text-lg font-bold text-white mb-2">{pipe.name}</h3>
                        <p className="text-xs text-[#8A8F9E] leading-relaxed">{pipe.desc}</p>
                      </div>
                    ))}
                  </div>
                </section>

                {/* Competitive Teardown Matrix */}
                <div id="benchmarks">
                  <CompetitiveMatrix />
                </div>

                {/* Bottom High-Fashion CTA Strip */}
                <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                  <div className="relative rounded-3xl p-8 sm:p-14 bg-gradient-to-br from-[#13151A] via-[#0D0E10] to-[#13151A] border border-[#10B981]/30 overflow-hidden shadow-2xl">
                    <div className="absolute -right-20 -top-20 w-96 h-96 bg-[#10B981]/10 rounded-full blur-3xl pointer-events-none" />
                    <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-8">
                      <div className="space-y-4 max-w-2xl">
                        <span className="inline-block px-3 py-1 rounded-full text-xs font-mono font-medium tracking-wider bg-[#10B981]/10 text-[#10B981] border border-[#10B981]/30">
                          ENTERPRISE DECISION PLATFORM
                        </span>
                        <h2 className="text-3xl sm:text-5xl font-black tracking-tight text-white leading-tight">
                          READY TO AUDIT YOUR PRODUCT INTELLIGENCE?
                        </h2>
                        <p className="text-sm font-mono text-[#8A8F9E] leading-relaxed">
                          Explore live Sony WH-1000XM5 telemetry, drill into 3σ EWMA statistical
                          anomalies, and query the zero-hallucination RAG Copilot.
                        </p>
                      </div>

                      <button
                        onClick={() => launchDashboard()}
                        className="inline-flex items-center justify-center gap-3 px-8 py-5 rounded-2xl bg-[#10B981] hover:bg-[#059669] text-black font-mono font-bold text-sm tracking-wider uppercase transition-all duration-300 shadow-[0_0_30px_rgba(16,185,129,0.3)] hover:shadow-[0_0_50px_rgba(16,185,129,0.5)] hover:scale-[1.02] active:scale-[0.98] group whitespace-nowrap"
                      >
                        <span>LAUNCH LIVE WORKSPACE</span>
                        <ArrowUpRight className="w-5 h-5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                      </button>
                    </div>
                  </div>
                </section>

                {/* High-Fashion Editorial Footer */}
                <footer className="border-t border-white/10 pt-12 pb-16 text-center text-xs font-mono text-[#8A8F9E]">
                  <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                      <span className="font-black text-white tracking-widest">BRANDGUARD.</span>
                      <span>HIGH-FASHION B2B REVIEW INTELLIGENCE</span>
                    </div>
                    <div>
                      <span>ENGINEERED ON NEXT.JS 15 • THREE.JS • TAILWIND CSS • CHARTS.JS</span>
                    </div>
                    <div className="text-[#10B981]">
                      <span>SYS STAT: ONLINE (100% DETERMINISTIC)</span>
                    </div>
                  </div>
                </footer>
              </motion.div>
            ) : (
              <motion.div
                key="dashboard-view"
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              >
                <DashboardView />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </SmoothScrollProvider>
  );
}
