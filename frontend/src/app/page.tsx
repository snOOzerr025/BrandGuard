"use client";

import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SmoothScrollProvider } from "../components/providers/SmoothScrollProvider";
import { Canvas3D } from "../components/canvas/Canvas3D";
import { Navbar } from "../components/navigation/Navbar";
import { HeroSection } from "../components/landing/HeroSection";
import { MarqueeTicker } from "../components/landing/MarqueeTicker";
import { ArchitectureAtelier } from "../components/landing/ArchitectureAtelier";
import { SwirlingChannel } from "../components/landing/SwirlingChannel";
import { CapabilitiesGrid } from "../components/landing/CapabilitiesGrid";
import { CompetitiveMatrix } from "../components/landing/CompetitiveMatrix";
import { DashboardView } from "../components/dashboard/DashboardView";
import { AuthModal } from "../components/auth/AuthModal";
import { useDashboardStore } from "../store/useDashboardStore";
import { ArrowUpRight, Sparkles } from "lucide-react";

export default function Home() {
  const { currentView, launchDashboard } = useDashboardStore();

  return (
    <SmoothScrollProvider>
      <main className="relative min-h-screen bg-[#0A1128] text-[#FAF6F0] selection:bg-[#FF5A36]/30 selection:text-white">
        {/* 1. 3D WebGL Neural Particle Lattice Canvas with Multidimensional Particles */}
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
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] as const }}
                className="space-y-24 sm:space-y-36 pb-24"
              >
                {/* FRAME 01: The Editorial Overture & Shift-Balance Hero */}
                <HeroSection />

                {/* Technical Capability Continuous Running Ticker */}
                <MarqueeTicker />

                {/* FRAME 02: The 4-Stage Inference Atelier & Architectural Blueprint */}
                <ArchitectureAtelier />

                {/* FRAME 03: The Swirling 3D Channel of Product, Market & Consumer Culture */}
                <div id="swirling-channel">
                  <SwirlingChannel />
                </div>

                {/* FRAME 04: The Capabilities Verification Bento Grid */}
                <CapabilitiesGrid />

                {/* FRAME 05: The Competitive Benchmark Matrix */}
                <CompetitiveMatrix />

                {/* FRAME 06 / PRE-LAUNCH STRIP: Executive Call to Action */}
                <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                  <div className="relative rounded-[2.5rem] p-8 sm:p-14 bg-gradient-to-br from-[#0E1833] via-[#0A1128] to-[#141C38] border border-[#FF5A36]/35 overflow-hidden shadow-2xl">
                    <div className="absolute -right-20 -top-20 w-96 h-96 bg-[#FF5A36]/15 rounded-full blur-3xl pointer-events-none" />
                    <div className="absolute -left-20 -bottom-20 w-80 h-80 bg-[#FFA6B6]/10 rounded-full blur-3xl pointer-events-none" />

                    <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-8">
                      <div className="space-y-4 max-w-2xl">
                        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-medium tracking-wider bg-[#FF5A36]/15 text-[#FF5A36] border border-[#FF5A36]/30">
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>EXECUTIVE DECISION WORKSPACE</span>
                        </span>
                        <h2 className="text-3xl sm:text-5xl font-black tracking-tight text-white leading-tight">
                          AUDIT LIVE PRODUCT SENTIMENT WITH{" "}
                          <span className="font-serif italic font-normal text-[#FF5A36]">
                            mathematical certainty.
                          </span>
                        </h2>
                        <p className="text-sm font-mono text-[#FAF6F0]/75 leading-relaxed">
                          Transition seamlessly into the executive workspace to audit multi-product
                          telemetry (Sony WH-1000XM5, Apple iPhone 15 Pro, Samsung S24 Ultra, Bose, Dyson),
                          inspect 3σ EWMA anomaly bounds, and ingest custom CSV review datasets.
                        </p>
                      </div>

                      <button
                        onClick={() => launchDashboard()}
                        className="inline-flex items-center justify-center gap-3 px-8 py-5 rounded-2xl bg-[#FF5A36] hover:bg-[#FF451D] text-white font-mono font-bold text-sm tracking-wider uppercase transition-all duration-300 shadow-[0_0_35px_rgba(255,90,54,0.4)] hover:shadow-[0_0_55px_rgba(255,90,54,0.6)] hover:scale-[1.02] active:scale-[0.98] group whitespace-nowrap cursor-pointer"
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
                      <span className="font-black text-[#FAF6F0] tracking-widest">BRANDGUARD.</span>
                      <span>HIGH-FASHION B2B REVIEW INTELLIGENCE</span>
                    </div>
                    <div>
                      <span>ENGINEERED ON NEXT.JS 15 • THREE.JS • TAILWIND CSS • CHARTS.JS</span>
                    </div>
                    <div className="text-[#9CAF88]">
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
                transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] as const }}
              >
                <DashboardView />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Global Glassmorphic Auth Modal */}
        <AuthModal />
      </main>
    </SmoothScrollProvider>
  );
}
