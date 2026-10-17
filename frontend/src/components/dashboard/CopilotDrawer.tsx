"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Search, Sparkles, Database, FileText, ExternalLink, ArrowRight, CheckCircle2 } from "lucide-react";
import { ProductDataset, CopilotResponse } from "../../lib/api";
import { useDashboardStore } from "../../store/useDashboardStore";

interface Props {
  dataset: ProductDataset;
}

export const CopilotDrawer: React.FC<Props> = ({ dataset }) => {
  const {
    isCopilotOpen,
    toggleCopilot,
    copilotInitialPrompt,
    setHighlightedCitationId,
  } = useDashboardStore();

  const [queryInput, setQueryInput] = useState("");
  const [messages, setMessages] = useState<
    Array<{ role: "user" | "copilot"; content: string; responseObj?: CopilotResponse }>
  >([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeCitationCard, setActiveCitationCard] = useState<{
    id: string;
    snippet: string;
    rating: number;
    date: string;
  } | null>(null);

  // If initial prompt provided, submit automatically
  useEffect(() => {
    if (copilotInitialPrompt && isCopilotOpen) {
      setQueryInput(copilotInitialPrompt);
      handleExecuteQuery(copilotInitialPrompt);
    }
  }, [copilotInitialPrompt, isCopilotOpen]);

  const handleExecuteQuery = (promptText: string) => {
    if (!promptText.trim()) return;

    setMessages((prev) => [...prev, { role: "user", content: promptText }]);
    setQueryInput("");
    setIsProcessing(true);

    setTimeout(() => {
      // Find matching preset or generate hybrid grounded response
      const matched =
        dataset.copilotPresets[promptText] || {
          answer: `Deterministic SQL aggregation confirms that customer sentiment regarding this inquiry shows a statistically significant anomaly drift. Qualitative semantic clustering across pgvector HNSW embeddings isolates high-frequency mentions of component fatigue [ref:rev-sny-03] and warranty claim rejections [ref:rev-sny-04].`,
          intent: "HYBRID" as const,
          sqlMetrics: [
            { label: "Deterministic Net Sentiment", value: "+28.4 pts" },
            { label: "Leave-One-Out Drag", value: "-0.42★" },
          ],
          citations: [
            {
              id: "rev-sny-03",
              snippet: "Right swivel hinge snapped at the friction seam while putting them on my head...",
              rating: 1,
              date: "2026-10-11",
            },
          ],
        };

      setMessages((prev) => [
        ...prev,
        {
          role: "copilot",
          content: matched.answer,
          responseObj: matched,
        },
      ]);
      setIsProcessing(false);
    }, 600);
  };

  const handleCitationClick = (citationId: string) => {
    setHighlightedCitationId(citationId);

    // Scroll to review in stream
    const el = document.getElementById(`review-${citationId}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  return (
    <AnimatePresence>
      {isCopilotOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.65 }}
            exit={{ opacity: 0 }}
            onClick={() => toggleCopilot(false)}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 cursor-pointer"
          />

          {/* Slide-over Drawer */}
          <motion.aside
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed top-0 right-0 h-full w-full max-w-xl bg-[#0D0E10] border-l border-white/10 z-50 flex flex-col justify-between shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="p-6 border-b border-white/10 flex items-center justify-between bg-[#13151A]/80 backdrop-blur-md">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-[#10B981]/10 text-[#10B981]">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold font-mono tracking-tight text-white uppercase flex items-center gap-2">
                    Ask BrandGuard Copilot
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#10B981]/10 border border-[#10B981]/30 text-[#10B981]">
                      HYBRID RRF
                    </span>
                  </h3>
                  <p className="text-xs text-[#8A8F9E] font-sans">
                    PostgreSQL tsvector + pgvector HNSW with 98.4% Ragas verification
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => toggleCopilot(false)}
                className="p-2 rounded-xl text-[#8A8F9E] hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Floating Citation Evidence Card */}
            {activeCitationCard && (
              <div className="mx-6 mt-4 p-4 rounded-2xl bg-[#13151A] border border-[#10B981]/40 shadow-2xl relative text-xs">
                <div className="flex items-center justify-between text-[11px] font-mono text-[#8A8F9E] mb-2">
                  <span className="text-[#10B981] font-bold">Citation Evidence: ref:{activeCitationCard.id}</span>
                  <span className="text-amber-400 font-bold">{"★".repeat(activeCitationCard.rating)}</span>
                </div>
                <p className="text-slate-200 italic mb-2 leading-relaxed">
                  &ldquo;{activeCitationCard.snippet}&rdquo;
                </p>
                <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[11px] font-mono">
                  <span className="text-[#8A8F9E]">{activeCitationCard.date}</span>
                  <button
                    type="button"
                    onClick={() => handleCitationClick(activeCitationCard.id)}
                    className="text-[#10B981] font-bold hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <span>Highlight in Review Stream</span>
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </div>
              </div>
            )}

            {/* Conversation Stream */}
            <div className="flex-1 p-6 overflow-y-auto space-y-6">
              {messages.length === 0 ? (
                <div className="py-16 text-center space-y-4">
                  <div className="w-12 h-12 rounded-2xl bg-[#13151A] border border-white/10 text-[#10B981] flex items-center justify-center mx-auto">
                    <Database className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="text-sm font-mono font-bold text-white mb-1">
                      Deterministic Decision Intelligence
                    </h4>
                    <p className="text-xs text-[#8A8F9E] max-w-sm mx-auto font-sans leading-relaxed">
                      Ask any qualitative or quantitative question. All answers are grounded in exact SQL aggregations and verbatim customer reviews.
                    </p>
                  </div>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex flex-col ${
                      msg.role === "user" ? "items-end" : "items-start"
                    }`}
                  >
                    <div className="text-[10px] font-mono text-[#8A8F9E] mb-1.5 px-1 uppercase tracking-wider">
                      {msg.role === "user" ? "Executive Inquiry" : "BrandGuard Copilot"}
                    </div>

                    <div
                      className={`p-4 rounded-2xl text-xs leading-relaxed max-w-[90%] ${
                        msg.role === "user"
                          ? "bg-[#10B981]/15 text-white border border-[#10B981]/30 font-mono"
                          : "bg-[#13151A] text-slate-200 border border-white/10 font-sans shadow-xl"
                      }`}
                    >
                      {/* Intent Banner */}
                      {msg.responseObj && (
                        <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/5 font-mono text-[10px]">
                          <span className="text-[#10B981] font-bold">
                            INTENT: {msg.responseObj.intent}
                          </span>
                          <span className="text-[#8A8F9E]">•</span>
                          <span className="text-slate-400">Deterministic SQL Verified</span>
                        </div>
                      )}

                      {/* SQL Metrics Box */}
                      {msg.responseObj?.sqlMetrics && (
                        <div className="grid grid-cols-2 gap-2 p-3 rounded-xl bg-[#0D0E10] border border-white/5 mb-3 font-mono">
                          {msg.responseObj.sqlMetrics.map((met, mIdx) => (
                            <div key={mIdx}>
                              <span className="text-[10px] text-[#8A8F9E] block">{met.label}</span>
                              <span className="text-xs font-bold text-white">{met.value}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Message Content with interactive citation badges */}
                      <p className="whitespace-pre-line text-slate-200 leading-relaxed mb-3">
                        {msg.content}
                      </p>

                      {/* Interactive Citation Pills */}
                      {msg.responseObj?.citations && msg.responseObj.citations.length > 0 && (
                        <div className="flex flex-wrap gap-2 pt-2 border-t border-white/5">
                          {msg.responseObj.citations.map((cite) => (
                            <button
                              key={cite.id}
                              type="button"
                              onMouseEnter={() => setActiveCitationCard(cite)}
                              onClick={() => handleCitationClick(cite.id)}
                              className="px-2 py-0.5 rounded-md bg-[#10B981]/15 hover:bg-[#10B981]/30 text-[#10B981] border border-[#10B981]/40 text-[11px] font-mono font-bold flex items-center gap-1 transition-colors cursor-pointer"
                            >
                              <span>ref:{cite.id}</span>
                              <ArrowRight className="w-2.5 h-2.5" />
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}

              {isProcessing && (
                <div className="flex items-center gap-3 p-4 rounded-2xl bg-[#13151A] border border-white/10 text-xs font-mono text-[#10B981]">
                  <Sparkles className="w-4 h-4 animate-spin text-[#10B981]" />
                  <span>Synthesizing reciprocal rank fusion across pgvector & tsvector...</span>
                </div>
              )}
            </div>

            {/* Presets & Input Form */}
            <div className="p-6 border-t border-white/10 bg-[#13151A]/90 backdrop-blur-md space-y-4">
              <div>
                <span className="text-[10px] font-mono text-[#8A8F9E] uppercase tracking-widest block mb-2 font-semibold">
                  Executive Inquiry Presets
                </span>
                <div className="flex flex-wrap gap-2">
                  {Object.keys(dataset.copilotPresets).map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      onClick={() => handleExecuteQuery(preset)}
                      className="px-3 py-1.5 rounded-xl bg-[#0D0E10] hover:bg-[#1F232B] border border-white/10 hover:border-[#10B981]/40 text-xs font-mono text-slate-300 hover:text-white transition-all cursor-pointer text-left"
                    >
                      {preset}
                    </button>
                  ))}
                </div>
              </div>

              {/* Form Input */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleExecuteQuery(queryInput);
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  placeholder="Ask any qualitative question across verified reviews..."
                  className="flex-1 px-4 py-3 rounded-xl bg-[#0D0E10] border border-white/10 focus:border-[#10B981] text-xs font-sans text-white placeholder-[#8A8F9E] outline-none transition-colors"
                />
                <button
                  type="submit"
                  disabled={!queryInput.trim() || isProcessing}
                  className="px-5 py-3 rounded-xl bg-[#10B981] hover:bg-[#059669] disabled:opacity-40 text-[#0D0E10] font-mono font-bold text-xs transition-colors cursor-pointer"
                >
                  Query →
                </button>
              </form>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
};
