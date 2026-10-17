"use client";

import React from "react";

const CAPABILITIES = [
  "DEBERTA-V3 ABSA ENGINE",
  "ZERO-HALLUCINATION RAG",
  "HDBSCAN MICRO-CLUSTERING",
  "STL + EWMA CONTROL CHARTS",
  "PGVECTOR HNSW ISOLATION",
  "ONNX QUANTIZATION RUNTIME",
  "LEAVE-ONE-OUT STAR IMPACT",
  "RAGAS NLI VERIFICATION",
];

export const MarqueeTicker: React.FC = () => {
  return (
    <div className="w-full py-6 bg-[#0D0E10] border-y border-white/10 overflow-hidden relative select-none">
      {/* Side gradient fades */}
      <div className="absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-[#0D0E10] to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-[#0D0E10] to-transparent z-10 pointer-events-none" />

      <div className="animate-marquee whitespace-nowrap flex items-center gap-12 font-mono text-xs tracking-[0.25em] text-[#8A8F9E]">
        {CAPABILITIES.concat(CAPABILITIES).map((item, idx) => (
          <div key={idx} className="flex items-center gap-12 hover:text-[#10B981] transition-colors">
            <span>{item}</span>
            <span className="text-[#10B981] text-base">✦</span>
          </div>
        ))}
      </div>
    </div>
  );
};
