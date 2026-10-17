"use client";

import React, { useState } from "react";
import { Check, X, ShieldAlert, Sparkles, ArrowRight } from "lucide-react";
import { useDashboardStore } from "../../store/useDashboardStore";

interface RowData {
  dimension: string;
  brandGuard: string;
  competitors: string;
  impact: string;
}

const MATRIX_ROWS: RowData[] = [
  {
    dimension: "Aspect Granularity",
    brandGuard: "Clause-level multi-label DeBERTa-v3 ACD with span boundary extraction",
    competitors: "Document-level sentiment or coarse sentence averages (Enterpret / Chattermill)",
    impact: "Captures opposing sentiments within the same review sentence (e.g., great ANC, terrible hinge)",
  },
  {
    dimension: "Statistical Anomaly Bounds",
    brandGuard: "Deseasonalized STL decomposition + Lucas-Saccucci EWMA ±3σ control limits",
    competitors: "Static percentage thresholds triggering rampant false positives (Thematic / Viable)",
    impact: "Zero false alarm fatigue for engineering and executive product leadership",
  },
  {
    dimension: "Star Impact Causality",
    brandGuard: "Leave-One-Out (LOO) counterfactual Δ★ mathematical rating attribution",
    competitors: "Correlation heatmaps without counterfactual star degradation modeling",
    impact: "Directly quantifies exact star rating lost per defect (e.g. -0.42★ due to hinge shear)",
  },
  {
    dimension: "Copilot Grounding & Verification",
    brandGuard: "Deterministic SQL metrics + Hybrid RRF with Ragas NLI verification (98.4%)",
    competitors: "Pure LLM semantic RAG prone to hallucinated aggregations and false metrics",
    impact: "Guaranteed verifiable [ref:uuid] citations backed by exact PostgreSQL counts",
  },
  {
    dimension: "Theme Induction",
    brandGuard: "Unsupervised BGE-Small + UMAP + HDBSCAN density clustering with c-TF-IDF",
    competitors: "Pre-defined fixed taxonomies requiring weeks of manual customer training",
    impact: "Discovers zero-day manufacturing defects automatically without prior keyword labeling",
  },
];

export const CompetitiveMatrix: React.FC = () => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const { launchDashboard } = useDashboardStore();

  return (
    <section id="benchmarks" className="py-28 px-6 max-w-7xl mx-auto">
      <div className="mb-16 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 font-mono text-xs text-[#10B981] tracking-widest uppercase mb-3">
            <span>03 / ARCHITECTURAL TEARDOWN</span>
          </div>
          <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-white max-w-xl">
            COMPETITIVE BENCHMARK MATRIX
          </h2>
        </div>
        <p className="text-sm font-mono text-[#8A8F9E] max-w-sm">
          BrandGuard is engineered to replace legacy blackbox NLP platforms with deterministic, decision-grade mathematical precision.
        </p>
      </div>

      <div className="border border-white/10 rounded-3xl overflow-hidden bg-[#13151A]/80 backdrop-blur-xl shadow-2xl">
        <div className="grid grid-cols-12 p-6 border-b border-white/10 text-xs font-mono tracking-widest text-[#8A8F9E] uppercase bg-[#0D0E10]/70">
          <div className="col-span-3">Architectural Dimension</div>
          <div className="col-span-5 text-[#10B981] font-bold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#10B981]" />
            BrandGuard Platform
          </div>
          <div className="col-span-4 text-slate-400">Legacy Competitors</div>
        </div>

        <div className="divide-y divide-white/5">
          {MATRIX_ROWS.map((row, idx) => {
            const isHovered = hoveredIdx === idx;
            return (
              <div
                key={idx}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                className={`grid grid-cols-12 p-6 transition-all duration-200 items-center gap-4 cursor-default ${
                  isHovered
                    ? "bg-[#10B981]/5 border-l-4 border-l-[#10B981]"
                    : "hover:bg-white/[0.02]"
                }`}
              >
                {/* Dimension */}
                <div className="col-span-12 md:col-span-3">
                  <span className="text-sm font-bold text-white uppercase tracking-tight block">
                    {row.dimension}
                  </span>
                  <span className="text-xs text-[#8A8F9E] mt-1 block font-sans">
                    {row.impact}
                  </span>
                </div>

                {/* BrandGuard */}
                <div className="col-span-12 md:col-span-5">
                  <div className="p-3.5 rounded-xl bg-[#0D0E10] border border-[#10B981]/30 text-xs font-mono text-slate-100 flex items-start gap-3 shadow-inner">
                    <Check className="w-4 h-4 text-[#10B981] shrink-0 mt-0.5" />
                    <span className="leading-relaxed">{row.brandGuard}</span>
                  </div>
                </div>

                {/* Legacy Competitors */}
                <div className="col-span-12 md:col-span-4">
                  <div className="p-3.5 rounded-xl bg-[#0D0E10]/40 border border-white/5 text-xs text-[#8A8F9E] flex items-start gap-3">
                    <X className="w-4 h-4 text-[#EF4444] shrink-0 mt-0.5" />
                    <span className="leading-relaxed">{row.competitors}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer Banner */}
        <div className="p-6 bg-[#0D0E10] border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Sparkles className="w-5 h-5 text-[#10B981]" />
            <span className="text-xs font-mono text-[#8A8F9E]">
              Ready to verify against live review datasets?
            </span>
          </div>
          <button
            type="button"
            onClick={() => launchDashboard()}
            className="px-6 py-2.5 rounded-full bg-[#10B981] hover:bg-[#059669] text-[#0D0E10] text-xs font-mono font-bold tracking-wider flex items-center gap-2 transition-all cursor-pointer"
          >
            <span>Launch Live Dashboard</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </section>
  );
};
