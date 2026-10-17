"use client";

import React, { useRef, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Sparkles,
  Cpu,
  Database,
  ChevronDown,
  Upload,
  Plus,
  Check,
  ShoppingBag,
} from "lucide-react";
import { useDashboardStore } from "../../store/useDashboardStore";
import { KPIRibbon } from "./KPIRibbon";
import { AspectMatrixChart } from "./AspectMatrixChart";
import { EWMAControlChart } from "./EWMAControlChart";
import { ReviewStreamTable } from "./ReviewStreamTable";
import { CopilotDrawer } from "./CopilotDrawer";
import { ReviewIngestionLab } from "./ReviewIngestionLab";

export const DashboardView: React.FC = () => {
  const {
    products,
    activeProductId,
    setActiveProduct,
    returnToLanding,
    toggleCopilot,
    openIngestModal,
  } = useDashboardStore();

  const dataset = products[activeProductId] || products["prod-sony-xm5"] || Object.values(products)[0];
  const timelineRef = useRef<HTMLDivElement>(null);
  const [isProductDropdownOpen, setIsProductDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsProductDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const scrollToTimeline = () => {
    timelineRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-[#181210]/95 text-[#FFF8E7] pt-24 pb-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Top Workspace Header Bar in Mocha Cream & Cosmic Slate */}
      <motion.div
        initial={{ opacity: 0, y: -15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-5 p-6 rounded-3xl bg-[#2A211D]/90 border border-[#4A3831] backdrop-blur-xl shadow-2xl"
      >
        <div className="flex flex-wrap items-center gap-4">
          <button
            onClick={returnToLanding}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white/5 border border-white/10 hover:border-[#FF5A36]/60 text-xs font-mono text-[#EADBC8] hover:text-white transition-all group cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5 transition-transform group-hover:-translate-x-0.5 text-[#FF5A36]" />
            <span>EDITORIAL VIEW</span>
          </button>

          <div className="h-6 w-px bg-white/10 hidden sm:block" />

          {/* Interactive Multi-Product Switcher */}
          <div className="relative" ref={dropdownRef}>
            <button
              type="button"
              onClick={() => setIsProductDropdownOpen(!isProductDropdownOpen)}
              className="flex items-center gap-3 p-2.5 sm:px-4 sm:py-2 rounded-2xl bg-black/40 hover:bg-black/60 border border-white/10 hover:border-[#FF5A36]/40 transition-all text-left cursor-pointer group"
            >
              <div className="w-8 h-8 rounded-xl bg-[#FF5A36]/15 border border-[#FF5A36]/30 flex items-center justify-center text-[#FF5A36] shrink-0 group-hover:scale-105 transition-transform">
                <ShoppingBag className="w-4 h-4" />
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.2 rounded text-[9px] font-mono font-semibold tracking-wider bg-[#9CAF88]/20 text-[#9CAF88] border border-[#9CAF88]/40">
                    ACTIVE AUDIT SKU
                  </span>
                  <span className="text-[11px] font-mono text-[#EADBC8]/70">
                    {dataset.brand} • {dataset.category}
                  </span>
                </div>
                <h1 className="text-base sm:text-lg font-black tracking-tight text-[#FFF8E7] font-sans group-hover:text-[#FF5A36] transition-colors flex items-center gap-2">
                  <span>{dataset.name}</span>
                  <ChevronDown className="w-4 h-4 text-[#8A8F9E] group-hover:text-white transition-transform" />
                </h1>
              </div>
            </button>

            {/* Product Switcher Dropdown */}
            <AnimatePresence>
              {isProductDropdownOpen && (
                <motion.div
                  initial={{ opacity: 0, y: 10, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.96 }}
                  transition={{ duration: 0.2 }}
                  className="absolute left-0 mt-2 w-80 sm:w-96 rounded-2xl backdrop-blur-2xl bg-[#0A1128]/95 border border-white/15 p-3 shadow-2xl z-50 space-y-1.5"
                >
                  <div className="px-3 py-2 flex items-center justify-between text-[11px] font-mono text-[#8A8F9E] border-b border-white/10">
                    <span className="uppercase tracking-wider">Switch Product Telemetry</span>
                    <span>{Object.keys(products).length} Available SKUs</span>
                  </div>

                  <div className="max-h-72 overflow-y-auto space-y-1 py-1">
                    {Object.values(products).map((prod) => (
                      <button
                        key={prod.id}
                        type="button"
                        onClick={() => {
                          setActiveProduct(prod.id);
                          setIsProductDropdownOpen(false);
                        }}
                        className={`w-full p-2.5 rounded-xl text-left transition-all flex items-center justify-between cursor-pointer ${
                          activeProductId === prod.id
                            ? "bg-[#FF5A36]/20 border border-[#FF5A36]/60 text-white"
                            : "hover:bg-white/5 border border-transparent text-[#FAF6F0]"
                        }`}
                      >
                        <div className="min-w-0 pr-2">
                          <div className="text-[10px] font-mono text-[#8A8F9E] uppercase">
                            {prod.brand} • {prod.category}
                          </div>
                          <div className="text-xs font-bold truncate text-white">
                            {prod.name}
                          </div>
                          <div className="text-[10px] font-mono text-[#9CAF88] mt-0.5">
                            Health: {prod.kpis.brandHealthScore} | Net Sent: {prod.kpis.netSentiment}% | {prod.reviews.length} reviews
                          </div>
                        </div>

                        {activeProductId === prod.id && (
                          <Check className="w-4 h-4 text-[#FF5A36] shrink-0" />
                        )}
                      </button>
                    ))}
                  </div>

                  <div className="pt-2 border-t border-white/10">
                    <button
                      type="button"
                      onClick={() => {
                        setIsProductDropdownOpen(false);
                        openIngestModal();
                      }}
                      className="w-full py-2.5 px-3 rounded-xl bg-white/5 hover:bg-[#FF5A36]/20 border border-white/10 hover:border-[#FF5A36]/50 text-xs font-mono text-white flex items-center justify-center gap-2 transition-all cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5 text-[#FF5A36]" />
                      <span>Ingest Reviews / Create Custom Product</span>
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Action Controls & Engine Trigger */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Engine Status Indicators */}
          <div className="hidden xl:flex items-center gap-4 px-3.5 py-2 rounded-xl bg-black/40 border border-white/5 text-[11px] font-mono text-[#94A3B8]">
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-[#9CAF88]" />
              <span>ONNX ABSA: <strong className="text-white">v3.2</strong></span>
            </div>
            <div className="w-1 h-1 rounded-full bg-white/20" />
            <div className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-[#EADBC8]" />
              <span>Vector DB: <strong className="text-white">1,536d</strong></span>
            </div>
          </div>

          {/* Primary Action 1: Upload CSV / Test Engine Button */}
          <button
            onClick={() => openIngestModal()}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#0E1833] hover:bg-[#14234b] text-[#FAF6F0] hover:text-white border border-white/15 hover:border-[#FF5A36]/60 font-mono font-bold text-xs tracking-wider uppercase transition-all shadow-lg hover:shadow-[0_0_25px_rgba(255,90,54,0.3)] cursor-pointer hover:scale-[1.02] active:scale-[0.98]"
          >
            <Upload className="w-3.5 h-3.5 text-[#FF5A36]" />
            <span>UPLOAD REVIEWS / RUN ENGINE</span>
          </button>

          {/* Primary Action 2: Ask BrandGuard Copilot */}
          <button
            onClick={() => toggleCopilot(true)}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#FF5A36] to-[#DC2626] text-white font-mono font-bold text-xs tracking-wider uppercase hover:shadow-[0_0_30px_rgba(255,90,54,0.4)] transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
          >
            <Sparkles className="w-4 h-4 fill-white" />
            <span>COPILOT RAG</span>
          </button>
        </div>
      </motion.div>

      {/* 1. Executive KPI Ribbon in Cosmic Latte & Burgundy */}
      <section aria-label="Executive KPI Overview">
        <KPIRibbon dataset={dataset} onScrollToTimeline={scrollToTimeline} />
      </section>

      {/* 2. Visual Analytics Section: Aspect Matrix & EWMA Control Charts */}
      <section aria-label="Deep Analytics" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          key={`aspect-${dataset.id}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="h-full"
        >
          <AspectMatrixChart aspects={dataset.aspects} />
        </motion.div>

        <motion.div
          key={`timeline-${dataset.id}`}
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
          key={`reviews-${dataset.id}-${dataset.reviews.length}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <ReviewStreamTable reviews={dataset.reviews} />
        </motion.div>
      </section>

      {/* 4. RAG Copilot Slide-over Drawer */}
      <CopilotDrawer dataset={dataset} />

      {/* 5. Review Ingestion Lab Modal */}
      <ReviewIngestionLab />
    </div>
  );
};
