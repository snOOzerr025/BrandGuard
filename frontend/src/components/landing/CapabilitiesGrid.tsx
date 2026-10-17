"use client";

import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import { Cpu, Search, Activity, Network, ArrowUpRight } from "lucide-react";
import { useDashboardStore } from "../../store/useDashboardStore";

interface TiltCardProps {
  title: string;
  badge: string;
  desc: string;
  specs: string[];
  icon: React.ReactNode;
  prompt: string;
}

const TiltCard: React.FC<TiltCardProps> = ({ title, badge, desc, specs, icon, prompt }) => {
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
      className="p-8 rounded-3xl bg-[#13151A]/80 border border-white/10 hover:border-[#10B981]/40 backdrop-blur-xl shadow-2xl relative group overflow-hidden flex flex-col justify-between"
    >
      {/* Subtle corner light accent */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,0.15),transparent_70%)] pointer-events-none" />

      <div>
        <div className="flex items-center justify-between mb-6">
          <div className="p-3.5 rounded-2xl bg-[#0D0E10] border border-white/10 text-[#10B981] group-hover:scale-110 group-hover:border-[#10B981]/50 transition-all duration-300">
            {icon}
          </div>
          <span className="font-mono text-[10px] tracking-widest text-[#10B981] bg-[#10B981]/10 px-3 py-1 rounded-full border border-[#10B981]/20 font-bold uppercase">
            {badge}
          </span>
        </div>

        <h3 className="text-xl sm:text-2xl font-black uppercase tracking-tight text-white mb-3 group-hover:text-[#10B981] transition-colors">
          {title}
        </h3>

        <p className="text-sm text-[#8A8F9E] leading-relaxed mb-6">
          {desc}
        </p>

        <div className="space-y-2 mb-8 border-t border-white/5 pt-4">
          {specs.map((spec, i) => (
            <div key={i} className="flex items-center gap-2 text-xs font-mono text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
              <span>{spec}</span>
            </div>
          ))}
        </div>
      </div>

      <button
        type="button"
        onClick={() => launchDashboard(prompt)}
        className="w-full py-3 px-4 rounded-xl bg-[#0D0E10] hover:bg-[#10B981] text-xs font-mono text-[#8A8F9E] hover:text-[#0D0E10] font-bold border border-white/10 hover:border-[#10B981] flex items-center justify-between transition-all cursor-pointer"
      >
        <span>Inspect Telemetry In Dashboard</span>
        <ArrowUpRight className="w-4 h-4" />
      </button>
    </motion.div>
  );
};

export const CapabilitiesGrid: React.FC = () => {
  return (
    <section id="capabilities" className="py-28 px-6 max-w-7xl mx-auto">
      <div className="mb-16">
        <div className="inline-flex items-center gap-2 font-mono text-xs text-[#10B981] tracking-widest uppercase mb-3">
          <span>01 / EDITORIAL CAPABILITIES</span>
        </div>
        <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-white max-w-xl">
          DECISION-GRADE INTELLIGENCE LAYER
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <TiltCard
          title="Multi-Label DeBERTa-v3 ABSA"
          badge="86.4% F1 SOTA"
          desc="Fine-tuned multi-head transformer that extracts clause-level aspect mentions and assigns positive, neutral, or negative polarities across 8 core enterprise dimensions."
          specs={[
            "8 Canonical Aspect Dimensions",
            "ONNX Runtime INT8 Quantization (<15ms)",
            "Leave-One-Out (LOO) Star Impact Formula",
          ]}
          icon={<Cpu className="w-6 h-6" />}
          prompt="Why is Service & Build Quality dragging down overall rating?"
        />

        <TiltCard
          title="Grounded Hybrid RAG Copilot"
          badge="98.4% RAGAS ACCURACY"
          desc="Reciprocal Rank Fusion (RRF) combining PostgreSQL tsvector full-text keyword retrieval with pgvector HNSW dense embeddings, reranked by Cross-Encoder."
          specs={[
            "Exact SQL Deterministic Aggregates",
            "Zero-Hallucination NLI Verification",
            "Verifiable [ref:uuid] Citation Pills",
          ]}
          icon={<Search className="w-6 h-6" />}
          prompt="Explain the battery overheating anomaly on Oct 14"
        />

        <TiltCard
          title="STL + EWMA Anomaly Control"
          badge="3σ STATISTICAL BOUNDS"
          desc="De-seasonalizes review volume trends using Seasonal-Trend Decomposition by Loess (STL) and applies Lucas-Saccucci EWMA weighting to eliminate false alarms."
          specs={[
            "Dynamic Lucas-Saccucci Weighting (λ=0.2)",
            "±2σ Warning & ±3σ Control Limits",
            "Root-Cause Medoid Triage Attribution",
          ]}
          icon={<Activity className="w-6 h-6" />}
          prompt="Why is Service & Build Quality dragging down overall rating?"
        />

        <TiltCard
          title="Dynamic Micro-Theme Induction"
          badge="UNSUPERVISED DISCOVERY"
          desc="Dense embeddings via BGE-Small reduced through UMAP manifold projection and clustered with HDBSCAN density clustering, labeled via class-based c-TF-IDF."
          specs={[
            "Unsupervised Sub-Cluster Emergence",
            "c-TF-IDF Salient Keyword Tagging",
            "Noise Isolation (Cluster -1)",
          ]}
          icon={<Network className="w-6 h-6" />}
          prompt="Why is Service & Build Quality dragging down overall rating?"
        />
      </div>
    </section>
  );
};
