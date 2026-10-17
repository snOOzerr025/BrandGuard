"use client";

import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import { Cpu, Search, Activity, Network, ArrowUpRight, Sparkles } from "lucide-react";
import { useDashboardStore } from "../../store/useDashboardStore";

interface TiltCardProps {
  title: string;
  badge: string;
  desc: string;
  specs: string[];
  icon: React.ReactNode;
  prompt: string;
  accentColor: string;
  badgeBg: string;
  borderHover: string;
}

const TiltCard: React.FC<TiltCardProps> = ({
  title,
  badge,
  desc,
  specs,
  icon,
  prompt,
  accentColor,
  badgeBg,
  borderHover,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);
  const { launchDashboard } = useDashboardStore();

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotX = -((y - centerY) / centerY) * 10;
    const rotY = ((x - centerX) / centerX) * 10;

    setRotateX(rotX);
    setRotateY(rotY);
  };

  const handleMouseLeave = () => {
    setRotateX(0);
    setRotateY(0);
  };

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        transformStyle: "preserve-3d",
        transform: `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`,
        transition: "transform 0.15s ease-out",
      }}
      className={`p-8 rounded-3xl bg-[#0E1833]/80 border border-white/10 hover:${borderHover} backdrop-blur-xl shadow-2xl relative group overflow-hidden flex flex-col justify-between transition-colors duration-300`}
    >
      {/* Subtle corner light accent */}
      <div
        className="absolute top-0 right-0 w-36 h-36 rounded-full blur-3xl pointer-events-none opacity-20"
        style={{ backgroundColor: accentColor }}
      />

      <div>
        <div className="flex items-center justify-between mb-6">
          <div
            className="p-3.5 rounded-2xl bg-[#0A1128] border border-white/10 group-hover:scale-110 transition-all duration-300"
            style={{ color: accentColor }}
          >
            {icon}
          </div>
          <span
            className="font-mono text-[10px] tracking-widest px-3 py-1 rounded-full border font-bold uppercase"
            style={{
              color: accentColor,
              backgroundColor: badgeBg,
              borderColor: `${accentColor}40`,
            }}
          >
            {badge}
          </span>
        </div>

        <h3 className="text-xl sm:text-2xl font-black uppercase tracking-tight text-white mb-3 font-sans group-hover:text-white transition-colors">
          {title}
        </h3>

        <p className="text-sm text-[#FAF6F0]/75 leading-relaxed mb-6 font-sans">
          {desc}
        </p>

        <div className="space-y-2.5 mb-8 border-t border-white/10 pt-4">
          {specs.map((spec, i) => (
            <div key={i} className="flex items-center gap-2 text-xs font-mono text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: accentColor }} />
              <span>{spec}</span>
            </div>
          ))}
        </div>
      </div>

      <button
        type="button"
        onClick={() => launchDashboard(prompt)}
        className="w-full py-3.5 px-4 rounded-xl bg-[#0A1128] hover:bg-white/10 text-xs font-mono text-[#FAF6F0] font-bold border border-white/10 hover:border-white/30 flex items-center justify-between transition-all cursor-pointer group/btn"
      >
        <span className="group-hover/btn:text-white">Audit Live Telemetry In Dashboard</span>
        <ArrowUpRight className="w-4 h-4 transition-transform group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5" style={{ color: accentColor }} />
      </button>
    </motion.div>
  );
};

export const CapabilitiesGrid: React.FC = () => {
  return (
    <section id="capabilities" className="py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      <div className="mb-16 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 font-mono text-xs text-[#FFA6B6] tracking-widest uppercase mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>04 / VERIFICATION MATRIX</span>
          </div>
          <h2 className="text-3xl sm:text-5xl lg:text-6xl font-black uppercase tracking-tight text-white">
            DECISION-GRADE{" "}
            <span className="font-serif italic font-normal text-[#FFA6B6]">
              intelligence layer.
            </span>
          </h2>
        </div>
        <p className="text-sm font-mono text-[#8A8F9E] max-w-md">
          Engineered to isolate structural product defects from logistical noise using multi-label
          clause parsing and statistical control limits.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <TiltCard
          title="Multi-Label DeBERTa-v3 ABSA"
          badge="86.4% F1 SOTA"
          desc="Fine-tuned multi-head transformer that extracts clause-level aspect mentions and assigns positive, neutral, or negative polarities across 8 core enterprise dimensions."
          specs={[
            "8 Canonical Aspect Dimensions",
            "ONNX Runtime INT8 Quantization (<8.4ms)",
            "Leave-One-Out (LOO) Star Drag Formula",
          ]}
          icon={<Cpu className="w-6 h-6" />}
          prompt="Why is Service & Build Quality dragging down overall rating?"
          accentColor="#DC2626"
          badgeBg="rgba(220, 38, 38, 0.15)"
          borderHover="border-[#DC2626]/50"
        />

        <TiltCard
          title="Grounded Hybrid RAG Copilot"
          badge="98.4% RAGAS ACCURACY"
          desc="Reciprocal Rank Fusion (RRF) combining PostgreSQL tsvector full-text keyword retrieval with pgvector HNSW dense embeddings, reranked by Cross-Encoder."
          specs={[
            "Exact SQL Deterministic Aggregates",
            "Zero-Hallucination NLI Verification",
            "Verifiable [ref:uuid] Citation Evidence",
          ]}
          icon={<Search className="w-6 h-6" />}
          prompt="Explain the battery overheating anomaly on Oct 14"
          accentColor="#84CC16"
          badgeBg="rgba(132, 204, 22, 0.15)"
          borderHover="border-[#84CC16]/50"
        />

        <TiltCard
          title="STL + EWMA Anomaly Control"
          badge="3σ STATISTICAL BOUNDS"
          desc="De-seasonalizes review volume trends using Seasonal-Trend Decomposition by Loess (STL) and applies Lucas-Saccucci EWMA weighting to eliminate false alarms."
          specs={[
            "Dynamic Lucas-Saccucci Weighting (λ=0.2)",
            "±2σ Warning & ±3σ Statistical Bounds",
            "Root-Cause Medoid Triage Attribution",
          ]}
          icon={<Activity className="w-6 h-6" />}
          prompt="Why is Service & Build Quality dragging down overall rating?"
          accentColor="#FFA6B6"
          badgeBg="rgba(255, 166, 182, 0.15)"
          borderHover="border-[#FFA6B6]/50"
        />

        <TiltCard
          title="Dynamic Micro-Theme Induction"
          badge="UNSUPERVISED DISCOVERY"
          desc="Dense embeddings via BGE-Small reduced through UMAP manifold projection and clustered with HDBSCAN density clustering, labeled via class-based c-TF-IDF."
          specs={[
            "Unsupervised Sub-Cluster Emergence",
            "c-TF-IDF Salient Keyword Tagging",
            "Density-Based Noise Isolation (-1)",
          ]}
          icon={<Network className="w-6 h-6" />}
          prompt="Why is Service & Build Quality dragging down overall rating?"
          accentColor="#A3E635"
          badgeBg="rgba(163, 230, 53, 0.15)"
          borderHover="border-[#A3E635]/50"
        />
      </div>
    </section>
  );
};
