"use client";

import React from "react";
import { motion } from "framer-motion";
import { Activity, AlertTriangle, ArrowUpRight, TrendingUp, ShieldAlert, Sparkles } from "lucide-react";
import { ProductDataset } from "../../lib/api";
import { useDashboardStore } from "../../store/useDashboardStore";

interface Props {
  dataset: ProductDataset;
  onScrollToTimeline?: () => void;
}

export const KPIRibbon: React.FC<Props> = ({ dataset, onScrollToTimeline }) => {
  const { setSelectedAspect, toggleCopilot } = useDashboardStore();
  const { kpis } = dataset;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
      {/* 1. Brand Health Score */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="p-5 rounded-2xl bg-[#13151A]/80 border border-white/10 hover:border-[#10B981]/40 backdrop-blur-xl relative overflow-hidden group shadow-xl"
      >
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-[#10B981] to-emerald-300" />
        <div className="flex items-center justify-between text-xs font-mono tracking-widest text-[#8A8F9E] uppercase mb-3">
          <span>Brand Health Index</span>
          <span className="p-1.5 rounded-lg bg-[#10B981]/10 text-[#10B981]">
            <Activity className="w-3.5 h-3.5" />
          </span>
        </div>

        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-4xl font-black font-mono tracking-tight text-white">
            {kpis.brandHealthScore.toFixed(1)}
          </span>
          <span className="text-xs font-mono text-[#8A8F9E]">/ 100</span>
        </div>

        {/* Progress Bar Reveal */}
        <div className="w-full h-1.5 bg-[#0D0E10] rounded-full overflow-hidden mb-3">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${kpis.brandHealthScore}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="h-full bg-gradient-to-r from-[#10B981] to-emerald-400 rounded-full"
          />
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-2 py-0.5 rounded-full bg-[#10B981]/10 border border-[#10B981]/30 text-[#10B981] font-bold">
            ▲ +{kpis.brandHealthDelta.toFixed(1)}%
          </span>
          <span className="text-[#8A8F9E] text-[11px]">vs 30d window</span>
        </div>
      </motion.div>

      {/* 2. Net Sentiment */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.08 }}
        className="p-5 rounded-2xl bg-[#13151A]/80 border border-white/10 hover:border-[#10B981]/40 backdrop-blur-xl relative overflow-hidden group shadow-xl"
      >
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-emerald-400 to-teal-400" />
        <div className="flex items-center justify-between text-xs font-mono tracking-widest text-[#8A8F9E] uppercase mb-3">
          <span>Net Sentiment (NSS)</span>
          <span className="p-1.5 rounded-lg bg-[#10B981]/10 text-[#10B981]">
            <TrendingUp className="w-3.5 h-3.5" />
          </span>
        </div>

        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-4xl font-black font-mono tracking-tight text-[#10B981]">
            +{kpis.netSentiment.toFixed(1)}
          </span>
          <span className="text-xs font-mono text-[#8A8F9E]">pts</span>
        </div>

        {/* Polarity Bar */}
        <div className="w-full h-1.5 bg-[#0D0E10] rounded-full overflow-hidden mb-3">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, Math.max(10, kpis.netSentiment + 50))}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="h-full bg-gradient-to-r from-[#10B981] to-teal-300 rounded-full"
          />
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-[#8A8F9E] text-[11px]">Chattermill [-100, +100] scale</span>
        </div>
      </motion.div>

      {/* 3. Top Rating Drag Card */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.16 }}
        onClick={() => setSelectedAspect(kpis.topDragAspect)}
        className="p-5 rounded-2xl bg-[#13151A]/80 border border-white/10 hover:border-[#EF4444]/50 backdrop-blur-xl relative overflow-hidden group shadow-xl cursor-pointer transition-all"
      >
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-[#EF4444] to-amber-500" />
        <div className="flex items-center justify-between text-xs font-mono tracking-widest text-[#8A8F9E] uppercase mb-3">
          <span>Top Rating Drag</span>
          <span className="px-2 py-0.5 rounded-full bg-[#EF4444]/15 border border-[#EF4444]/30 text-[#EF4444] font-bold text-[10px]">
            LEAVE-ONE-OUT
          </span>
        </div>

        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-4xl font-black font-mono tracking-tight text-[#EF4444]">
            {kpis.topDragImpact.toFixed(2)}★
          </span>
          <span className="text-xs font-mono text-slate-300 truncate font-semibold">
            on {kpis.topDragAspect}
          </span>
        </div>

        <p className="text-[11px] text-[#8A8F9E] font-sans mb-3">
          Counterfactual star drag delta directly isolating negative volume.
        </p>

        <div className="flex items-center justify-between text-xs font-mono text-[#10B981] group-hover:underline">
          <span>Filter review stream</span>
          <ArrowUpRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
        </div>
      </motion.div>

      {/* 4. Active 3-Sigma Anomalies */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.24 }}
        onClick={() => {
          if (onScrollToTimeline) onScrollToTimeline();
          else toggleCopilot(true, "Why did Service & Build Quality trigger a 3-sigma control breach?");
        }}
        className="p-5 rounded-2xl bg-[#13151A]/80 border border-white/10 hover:border-[#F59E0B]/50 backdrop-blur-xl relative overflow-hidden group shadow-xl cursor-pointer transition-all"
      >
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-[#F59E0B] to-[#EF4444]" />
        <div className="flex items-center justify-between text-xs font-mono tracking-widest text-[#8A8F9E] uppercase mb-3">
          <span>Active 3σ Anomalies</span>
          <span className="p-1.5 rounded-lg bg-[#F59E0B]/10 text-[#F59E0B]">
            <AlertTriangle className="w-3.5 h-3.5" />
          </span>
        </div>

        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-4xl font-black font-mono tracking-tight text-[#F59E0B]">
            {kpis.activeAnomaliesCount}
          </span>
          <span className="text-xs font-mono text-amber-300 font-bold uppercase">
            HIGH SEVERITY BREACHES
          </span>
        </div>

        <p className="text-[11px] text-[#8A8F9E] font-sans mb-3">
          STL deseasonalized statistical control limits breached on Oct 08 & Oct 12.
        </p>

        <div className="flex items-center justify-between text-xs font-mono text-[#F59E0B] group-hover:underline">
          <span>Launch diagnostic triage</span>
          <ArrowUpRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
        </div>
      </motion.div>
    </div>
  );
};
