"use client";

import React, { useRef } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Sparkles,
  Layers,
  Cpu,
  Database,
  ShieldCheck,
  RefreshCw,
  Sliders,
  ChevronDown,
} from "lucide-react";
import { MOCK_DATASETS } from "../../lib/api";
import { useDashboardStore } from "../../store/useDashboardStore";
import { KPIRibbon } from "./KPIRibbon";
import { AspectMatrixChart } from "./AspectMatrixChart";
import { EWMAControlChart } from "./EWMAControlChart";
import { ReviewStreamTable } from "./ReviewStreamTable";
import { CopilotDrawer } from "./CopilotDrawer";

export const DashboardView: React.FC = () => {
  const { activeProductId, returnToLanding, toggleCopilot } = useDashboardStore();
  const dataset = MOCK_DATASETS[activeProductId] || MOCK_DATASETS["prod-sony-xm5"];
  const timelineRef = useRef<HTMLDivElement>(null);

  const scrollToTimeline = () => {
    timelineRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-[#0D0E10] text-[#FFFFFF] pt-24 pb-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Top Workspace Header Bar */}
      <motion.div
        initial={{ opacity: 0, y: -15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-[#13151A]/80 border border-white/10 backdrop-blur-xl shadow-2xl"
      >
        <div className="flex items-center gap-4">
          <button
            onClick={returnToLanding}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 border border-white/10 hover:border-[#10B981]/50 text-xs font-mono text-[#8A8F9E] hover:text-white transition-all group"
          >
            <ArrowLeft className="w-3.5 h-3.5 transition-transform group-hover:-translate-x-0.5 text-[#10B981]" />
            <span>EDITORIAL VIEW</span>
          </button>

          <div className="h-6 w-px bg-white/10 hidden sm:block" />

          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold tracking-wider bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30">
                ACTIVE SKU
              </span>
              <span className="text-xs font-mono text-[#8A8F9E]">
                {dataset.brand} • {dataset.category}
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white mt-1">
              {dataset.name}
            </h1>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Engine Status Indicators */}
          <div className="hidden xl:flex items-center gap-4 px-3 py-1.5 rounded-xl bg-black/40 border border-white/5 text-[11px] font-mono text-[#8A8F9E]">
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-[#10B981]" />
              <span>ONNX ABSA: <strong className="text-white">v3.2</strong></span>
            </div>
            <div className="w-1 h-1 rounded-full bg-white/20" />
            <div className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-[#10B981]" />
              <span>HNSW Vector: <strong className="text-white">1,536d</strong></span>
            </div>
            <div className="w-1 h-1 rounded-full bg-white/20" />
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
              <span>Pipeline: <strong className="text-[#10B981]">Healthy</strong></span>
            </div>
          </div>

          {/* Ask Copilot Button */}
          <button
            onClick={() => toggleCopilot(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#10B981] to-emerald-600 text-black font-mono font-semibold text-xs tracking-wider uppercase hover:shadow-[0_0_25px_rgba(16,185,129,0.35)] transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <Sparkles className="w-4 h-4 fill-black" />
            <span>ASK BRANDGUARD COPILOT</span>
          </button>
        </div>
      </motion.div>

      {/* 1. Executive KPI Ribbon */}
      <section aria-label="Executive KPI Overview">
        <KPIRibbon dataset={dataset} onScrollToTimeline={scrollToTimeline} />
      </section>

      {/* 2. Visual Analytics Section: Aspect Matrix & EWMA Control Charts */}
      <section aria-label="Deep Analytics" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="h-full"
        >
          <AspectMatrixChart aspects={dataset.aspects} />
        </motion.div>

        <motion.div
          ref={timelineRef}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="h-full"
        >
          <EWMAControlChart points={dataset.timeline} />
        </motion.div>
      </section>

      {/* 3. Live Review Stream & Inline Highlights */}
      <section aria-label="Live Review Stream">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <ReviewStreamTable reviews={dataset.reviews} />
        </motion.div>
      </section>

      {/* 4. RAG Copilot Slide-over Drawer */}
      <CopilotDrawer dataset={dataset} />
    </div>
  );
};
