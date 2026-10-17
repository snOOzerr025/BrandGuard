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
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 w-full">
      {/* 1. Brand Health Score (Sage Green & Cosmic Latte) */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="p-6 rounded-3xl bg-[#2A211D]/85 border border-[#4A3831] hover:border-[#9CAF88]/60 backdrop-blur-xl relative overflow-hidden group shadow-2xl transition-all"
      >
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#9CAF88] to-emerald-300" />
        <div className="flex items-center justify-between text-xs font-mono tracking-widest text-[#EADBC8]/70 uppercase mb-3">
          <span>Brand Health Index</span>
          <span className="p-1.5 rounded-lg bg-[#9CAF88]/15 text-[#9CAF88]">
            <Activity className="w-3.5 h-3.5" />
          </span>
        </div>

        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-4xl font-black font-mono tracking-tight text-[#FFF8E7]">
            {kpis.brandHealthScore.toFixed(1)}
          </span>
          <span className="text-xs font-mono text-[#EADBC8]/60">/ 100</span>
        </div>

        {/* Progress Bar Reveal */}
        <div className="w-full h-1.5 bg-black/40 rounded-full overflow-hidden mb-3">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${kpis.brandHealthScore}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="h-full bg-gradient-to-r from-[#9CAF88] to-emerald-400 rounded-full"
          />
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-2 py-0.5 rounded-full bg-[#9CAF88]/15 border border-[#9CAF88]/30 text-[#9CAF88] font-bold">
            ▲ +{kpis.brandHealthDelta.toFixed(1)}%
          </span>
          <span className="text-[#94A3B8] text-[11px]">vs 30d baseline</span>
        </div>
      </motion.div>

      {/* 2. Net Sentiment (Cosmic Latte & Mocha Cream) */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.08 }}
        className="p-6 rounded-3xl bg-[#2A211D]/85 border border-[#4A3831] hover:border-[#EADBC8]/60 backdrop-blur-xl relative overflow-hidden group shadow-2xl transition-all"
      >
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#EADBC8] to-[#9CAF88]" />
        <div className="flex items-center justify-between text-xs font-mono tracking-widest text-[#EADBC8]/70 uppercase mb-3">
          <span>Net Sentiment (NSS)</span>
          <span className="p-1.5 rounded-lg bg-[#EADBC8]/15 text-[#EADBC8]">
            <TrendingUp className="w-3.5 h-3.5" />
          </span>
        </div>

        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-4xl font-black font-mono tracking-tight text-[#FFF8E7]">
            +{kpis.netSentiment.toFixed(1)}
          </span>
          <span className="text-xs font-mono text-[#EADBC8]/60">pts</span>
        </div>

        {/* Polarity Bar */}
        <div className="w-full h-1.5 bg-black/40 rounded-full overflow-hidden mb-3">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, Math.max(10, kpis.netSentiment + 50))}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="h-full bg-gradient-to-r from-[#EADBC8] to-[#9CAF88] rounded-full"
          />
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-[#94A3B8] text-[11px]">Chattermill [-100, +100] scale</span>
        </div>
      </motion.div>

      {/* 3. Top Rating Drag Card (Deep Burgundy & Coral) */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.16 }}
        onClick={() => setSelectedAspect(kpis.topDragAspect)}
        className="p-6 rounded-3xl bg-[#3B151C]/90 border border-[#581825] hover:border-[#DC2626]/60 backdrop-blur-xl relative overflow-hidden group shadow-2xl cursor-pointer transition-all"
      >
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#DC2626] to-[#FF5A36]" />
        <div className="flex items-center justify-between text-xs font-mono tracking-widest text-[#FFA6B6] uppercase mb-3">
          <span>Top Rating Drag</span>
          <span className="px-2 py-0.5 rounded-full bg-[#DC2626]/20 border border-[#DC2626]/40 text-[#FFA6B6] font-bold text-[10px]">
            LEAVE-ONE-OUT
          </span>
        </div>

        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-4xl font-black font-mono tracking-tight text-[#FFA6B6]">
            {kpis.topDragImpact.toFixed(2)}★
          </span>
          <span className="text-xs font-mono text-white/80 truncate font-semibold">
            on {kpis.topDragAspect}
          </span>
        </div>

        <p className="text-[11px] text-[#FFA6B6]/70 font-sans mb-3">
          Counterfactual star drag directly isolating hinge failure negative volume.
        </p>

        <div className="flex items-center justify-between text-xs font-mono text-[#FFA6B6] group-hover:underline">
          <span>Filter review stream</span>
          <ArrowUpRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
        </div>
      </motion.div>

      {/* 4. Active 3-Sigma Anomalies (Deep Burgundy & Amber) */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.24 }}
        onClick={() => {
          if (onScrollToTimeline) onScrollToTimeline();
          else toggleCopilot(true, "Why did Service & Build Quality trigger a 3-sigma control breach?");
        }}
        className="p-6 rounded-3xl bg-[#3B151C]/90 border border-[#581825] hover:border-[#FF5A36]/60 backdrop-blur-xl relative overflow-hidden group shadow-2xl cursor-pointer transition-all"
      >
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#FF5A36] to-[#DC2626]" />
        <div className="flex items-center justify-between text-xs font-mono tracking-widest text-[#FFA6B6] uppercase mb-3">
          <span>Active 3σ Anomalies</span>
          <span className="p-1.5 rounded-lg bg-[#DC2626]/20 text-[#FFA6B6]">
            <AlertTriangle className="w-3.5 h-3.5" />
          </span>
        </div>

        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-4xl font-black font-mono tracking-tight text-[#FFA6B6]">
            {kpis.activeAnomaliesCount}
          </span>
          <span className="text-xs font-mono text-[#FF7A5C] font-bold uppercase">
            HIGH SEVERITY BREACHES
          </span>
        </div>

        <p className="text-[11px] text-[#FFA6B6]/70 font-sans mb-3">
          STL deseasonalized statistical control limits breached on Oct 08 & Oct 12.
        </p>

        <div className="flex items-center justify-between text-xs font-mono text-[#FF7A5C] group-hover:underline">
          <span>Launch diagnostic triage</span>
          <ArrowUpRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
        </div>
      </motion.div>
    </div>
  );
};
