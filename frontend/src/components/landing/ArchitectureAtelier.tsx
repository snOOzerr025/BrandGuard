"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Cpu, Network, Activity, Database, CheckCircle2, Sliders, ArrowRight } from "lucide-react";
import { useDashboardStore } from "../../store/useDashboardStore";

const PIPELINE_STAGES = [
  {
    step: "01",
    name: "DeBERTa-v3 ABSA",
    subtitle: "Clause-Level Multi-Label Extraction",
    tag: "ONNX Runtime • 8.4ms",
    desc: "Deconstructs compound sentences into distinct aspect-sentiment tuples across 8 dimensions (Quality, Price, Battery, Service, Delivery, Performance, Design, Packaging) with sub-clause resolution.",
    metrics: "F1: 86.4% • Clause Precision: 91.2%",
    color: "#9CAF88",
  },
  {
    step: "02",
    name: "BGE-Small + HDBSCAN",
    subtitle: "Unsupervised Micro-Theme Induction",
    tag: "c-TF-IDF Topic Synthesis",
    desc: "Transforms review representations into 384-dimensional dense embeddings, projected via UMAP into hierarchical density clusters. Uncovers organic defects like 'friction hinge shear' without pre-defined taxonomies.",
    metrics: "Cluster Stability: 0.88 • Outlier Rejection: 94%",
    color: "#D2DCB6",
  },
  {
    step: "03",
    name: "STL + EWMA SPC",
    subtitle: "Deseasonalized Statistical Quality Control",
    tag: "Lucas-Saccucci λ = 0.2",
    desc: "Decomposes seasonal review volume spikes (Prime Day, Black Friday) via Loess smoothing, running continuous Exponentially Weighted Moving Average control charts with strict ±3σ failure tripwires.",
    metrics: "False Alarm Rate: < 0.05% • 3σ Detection",
    color: "#FFA6B6",
  },
  {
    step: "04",
    name: "Grounded Hybrid RAG",
    subtitle: "Reciprocal Rank Fusion & Cross-Encoder",
    tag: "pgvector HNSW + tsvector",
    desc: "Combines exact keyword BM25 retrieval with cosine similarity vector search, reranked by Cross-Encoder. Delivers mathematically audited answers with verifiable, clickable review citation cards.",
    metrics: "Hallucination Rate: 0.00% • Ragas Grounding: 98.4%",
    color: "#84CC16",
  },
];

export const ArchitectureAtelier: React.FC = () => {
  const { launchDashboard } = useDashboardStore();
  const [activeClause, setActiveClause] = useState<number | null>(null);

  return (
    <section
      id="architecture"
      className="relative py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto overflow-hidden rounded-[2.5rem] bg-[#181E13] border border-[#3B4530] shadow-2xl"
    >
      {/* Precision Soft White in Light Grey Architectural Grid in Background */}
      <div className="absolute inset-0 bg-editorial-grid-light opacity-35 pointer-events-none" />

      {/* Deep Olive and Sage Ambient Vignette */}
      <div className="absolute -top-32 -left-32 w-96 h-96 bg-[#9CAF88]/15 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute -bottom-32 -right-32 w-96 h-96 bg-[#242C1D]/60 rounded-full blur-[140px] pointer-events-none" />

      {/* Frame 2 Editorial Header with Shift Balance */}
      <div className="relative z-10 flex flex-col lg:flex-row lg:items-end justify-between gap-8 pb-16 border-b border-white/10">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#9CAF88]/15 border border-[#9CAF88]/30 text-[#9CAF88] text-xs font-mono tracking-widest uppercase mb-4">
            <span>FRAME 02 // ARCHITECTURAL BLUEPRINT</span>
          </div>
          <h2 className="text-3xl sm:text-5xl lg:text-6xl font-black tracking-[-0.04em] text-white">
            THE 4-STAGE{" "}
            <span className="font-serif italic font-normal text-[#9CAF88]">
              inference atelier.
            </span>
          </h2>
        </div>
        <p className="text-sm font-mono text-[#D2DCB6]/80 max-w-md leading-relaxed">
          Subjective 5-star ratings create cognitive bias. Our deterministic pipeline computes
          mathematical accountability through clause decomposition and statistical process control.
        </p>
      </div>

      {/* Shift Balance Interactive Demo & Grid Layout */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 pt-12 items-start">
        {/* Left Sticky Column: Clause-Level Decomposition Auditor (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="p-6 rounded-3xl bg-[#242C1D]/80 border border-[#9CAF88]/30 backdrop-blur-xl space-y-5 shadow-xl">
            <div className="flex items-center justify-between text-xs font-mono text-[#9CAF88]">
              <span className="flex items-center gap-1.5 font-bold uppercase tracking-wider">
                <Sliders className="w-3.5 h-3.5 text-[#9CAF88]" />
                LIVE CLAUSE ISOLATION
              </span>
              <span className="text-white/60">SAMPLE #402</span>
            </div>

            <div className="p-4 rounded-2xl bg-black/50 border border-white/10 text-sm font-sans leading-relaxed text-white space-y-3">
              <p className="text-xs font-mono text-[#8A8F9E]">Hover to simulate DeBERTa extraction:</p>
              <div className="text-sm leading-relaxed">
                <span
                  onMouseEnter={() => setActiveClause(1)}
                  onMouseLeave={() => setActiveClause(null)}
                  className={`cursor-pointer px-1.5 py-0.5 rounded transition-colors ${
                    activeClause === 1
                      ? "bg-[#84CC16]/30 text-[#84CC16] font-semibold"
                      : "bg-white/5 hover:bg-white/15"
                  }`}
                >
                  &ldquo;The active noise cancellation completely silences jet engine roar,
                </span>{" "}
                <span
                  onMouseEnter={() => setActiveClause(2)}
                  onMouseLeave={() => setActiveClause(null)}
                  className={`cursor-pointer px-1.5 py-0.5 rounded transition-colors ${
                    activeClause === 2
                      ? "bg-[#DC2626]/30 text-[#FFA6B6] font-semibold"
                      : "bg-white/5 hover:bg-white/15"
                  }`}
                >
                  however the plastic right swivel hinge feels fragile and cracked after two weeks.&rdquo;
                </span>
              </div>
            </div>

            {/* Dynamic Telemetry Feedback on Hover */}
            <div className="p-4 rounded-2xl bg-black/30 border border-white/5 space-y-2 text-xs font-mono">
              <div className="flex items-center justify-between">
                <span className="text-[#8A8F9E]">Overall Star Rating:</span>
                <span className="text-[#F59E0B] font-bold">5.0 ★★★★★</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#8A8F9E]">Extracted Polarities:</span>
                <span className="text-white">
                  {activeClause === 1 ? (
                    <strong className="text-[#84CC16]">Quality: Positive (+1.0)</strong>
                  ) : activeClause === 2 ? (
                    <strong className="text-[#DC2626]">Build: Negative (-1.0)</strong>
                  ) : (
                    "Multi-Label Compound"
                  )}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#8A8F9E]">Leave-One-Out Impact:</span>
                <span className="text-[#FF5A36] font-bold">-0.42★ Drag on Brand</span>
              </div>
            </div>

            <button
              onClick={() => launchDashboard("Why is Service & Build Quality dragging down overall rating?")}
              className="w-full py-3 rounded-xl bg-[#9CAF88] hover:bg-[#849871] text-black font-mono font-bold text-xs tracking-wider uppercase transition-all shadow-[0_0_20px_rgba(156,175,136,0.3)] flex items-center justify-center gap-2"
            >
              <span>AUDIT CLAUSE IN COPILOT</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Right Column: 4 Architecture Cards (7 cols) */}
        <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-5">
          {PIPELINE_STAGES.map((stage) => (
            <div
              key={stage.step}
              className="p-6 rounded-3xl bg-[#242C1D]/60 border border-white/10 hover:border-[#9CAF88]/50 backdrop-blur-xl transition-all duration-300 group hover:-translate-y-1 shadow-xl flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span
                    className="text-2xl font-black font-mono transition-transform group-hover:scale-110"
                    style={{ color: stage.color }}
                  >
                    {stage.step}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-white/5 text-[#8A8F9E] border border-white/10">
                    {stage.tag}
                  </span>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-white font-sans">{stage.name}</h3>
                  <div className="text-xs font-mono text-[#9CAF88] mb-2">{stage.subtitle}</div>
                  <p className="text-xs text-[#FAF6F0]/70 leading-relaxed font-sans">{stage.desc}</p>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-white/10 text-[11px] font-mono text-[#D2DCB6] flex items-center justify-between">
                <span>{stage.metrics}</span>
                <CheckCircle2 className="w-3.5 h-3.5 text-[#84CC16]" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
