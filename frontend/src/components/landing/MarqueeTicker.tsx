"use client";

import React from "react";

const CAPABILITIES = [
  "DEBERTA-V3 ABSA ENGINE",
  "ZERO-HALLUCINATION RAG",
  "HDBSCAN MICRO-CLUSTERING",
  "STL + EWMA CONTROL CHARTS",
  "PGVECTOR HNSW ISOLATION",
  "ONNX INT8 QUANTIZATION",
  "LEAVE-ONE-OUT STAR IMPACT",
  "RAGAS NLI VERIFICATION",
  "CLAUSE-LEVEL POLARITY AUDIT",
];

export const MarqueeTicker: React.FC = () => {
  return (
    <div className="w-full py-6 bg-[#080D1A] border-y border-white/10 overflow-hidden relative select-none">
      {/* Side gradient fades */}
      <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-[#080D1A] to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-[#080D1A] to-transparent z-10 pointer-events-none" />

      <div className="animate-marquee whitespace-nowrap flex items-center gap-14 font-mono text-xs tracking-[0.25em] text-[#8A8F9E]">
        {CAPABILITIES.concat(CAPABILITIES).map((item, idx) => (
          <div key={idx} className="flex items-center gap-14 hover:text-[#FF5A36] transition-colors">
            <span className="text-[#FAF6F0]/80 hover:text-white">{item}</span>
            <span className="text-[#FF5A36] text-base">✦</span>
          </div>
        ))}
      </div>
    </div>
  );
};
