"use client";

import React, { useState, useMemo } from "react";
import { ReviewRecord } from "../../lib/api";
import { useDashboardStore } from "../../store/useDashboardStore";
import { Search, Filter, AlertTriangle, ShieldCheck, CheckCircle2, ChevronLeft, ChevronRight } from "lucide-react";

interface Props {
  reviews: ReviewRecord[];
}

export const ReviewStreamTable: React.FC<Props> = ({ reviews }) => {
  const {
    selectedAspect,
    setSelectedAspect,
    discrepancyOnly,
    setDiscrepancyOnly,
    highlightedCitationId,
  } = useDashboardStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 4;

  // Filter reviews
  const filteredReviews = useMemo(() => {
    return reviews.filter((rev) => {
      // Aspect filter
      if (selectedAspect && rev.aspect.toLowerCase() !== selectedAspect.toLowerCase()) {
        return false;
      }

      // Discrepancy filter
      if (discrepancyOnly && !rev.hasDiscrepancy) {
        return false;
      }

      // Search query filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesTitle = rev.title.toLowerCase().includes(query);
        const matchesBody = rev.reviewText.toLowerCase().includes(query);
        const matchesAspect = rev.aspect.toLowerCase().includes(query);
        if (!matchesTitle && !matchesBody && !matchesAspect) return false;
      }

      return true;
    });
  }, [reviews, selectedAspect, discrepancyOnly, searchQuery]);

  // Pagination
  const totalPages = Math.ceil(filteredReviews.length / pageSize) || 1;
  const paginatedReviews = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredReviews.slice(start, start + pageSize);
  }, [filteredReviews, currentPage, pageSize]);

  // Unique aspects for dropdown
  const uniqueAspects = useMemo(() => {
    return Array.from(new Set(reviews.map((r) => r.aspect)));
  }, [reviews]);

  return (
    <div id="review-stream" className="p-6 rounded-3xl bg-[#13151A]/80 border border-white/10 backdrop-blur-xl shadow-2xl flex flex-col justify-between">
      {/* Header and Filter Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6 pb-4 border-b border-white/5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
              Live Review Stream & Inline Sentiment Spans
            </h3>
            <span className="font-mono text-xs text-[#8A8F9E]">
              ({filteredReviews.length} records)
            </span>
          </div>
          <p className="text-xs text-[#8A8F9E] font-sans">
            Clause-level DeBERTa-v3 sentiment span highlights and rating anomaly detection
          </p>
        </div>

        {/* Filter Controls Cluster */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Search Input */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#8A8F9E] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search verbatim text..."
              className="pl-9 pr-3 py-1.5 rounded-xl bg-[#0D0E10] border border-white/10 focus:border-[#10B981] text-xs font-mono text-white placeholder-[#8A8F9E] outline-none transition-colors w-44 sm:w-56"
            />
          </div>

          {/* Aspect Filter Dropdown */}
          <select
            value={selectedAspect || ""}
            onChange={(e) => {
              setSelectedAspect(e.target.value || null);
              setCurrentPage(1);
            }}
            className="px-3 py-1.5 rounded-xl bg-[#0D0E10] border border-white/10 focus:border-[#10B981] text-xs font-mono text-slate-200 outline-none cursor-pointer"
          >
            <option value="">All Aspects</option>
            {uniqueAspects.map((asp) => (
              <option key={asp} value={asp}>
                {asp}
              </option>
            ))}
          </select>

          {/* Discrepancy Toggle Button */}
          <button
            type="button"
            onClick={() => {
              setDiscrepancyOnly(!discrepancyOnly);
              setCurrentPage(1);
            }}
            className={`px-3 py-1.5 rounded-xl font-mono text-xs border transition-all flex items-center gap-1.5 cursor-pointer ${
              discrepancyOnly
                ? "bg-[#F59E0B]/20 border-[#F59E0B] text-[#F59E0B] font-bold shadow-[0_0_12px_rgba(245,158,11,0.2)]"
                : "bg-[#0D0E10] border-white/10 text-[#8A8F9E] hover:text-white hover:border-white/20"
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Discrepancy Only</span>
          </button>
        </div>
      </div>

      {/* Review Table / Feed */}
      <div className="divide-y divide-white/5 space-y-3">
        {paginatedReviews.length === 0 ? (
          <div className="py-16 text-center text-xs font-mono text-[#8A8F9E]">
            No reviews match your selected aspect or search criteria.
          </div>
        ) : (
          paginatedReviews.map((rev) => {
            const isHighlighted = highlightedCitationId === rev.id;

            return (
              <article
                key={rev.id}
                id={`review-${rev.id}`}
                className={`p-4 rounded-2xl transition-all duration-300 ${
                  isHighlighted
                    ? "bg-[#10B981]/15 border-2 border-[#10B981] shadow-[0_0_25px_rgba(16,185,129,0.25)]"
                    : "bg-[#0D0E10]/50 hover:bg-[#0D0E10] border border-white/5"
                }`}
              >
                {/* Meta Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    {/* Stars */}
                    <div className="flex items-center text-amber-400 font-mono font-bold text-xs">
                      {"★".repeat(rev.rating)}
                      <span className="text-slate-700">{"☆".repeat(5 - rev.rating)}</span>
                    </div>

                    {/* ID */}
                    <span className="font-mono text-[11px] text-[#8A8F9E] bg-[#13151A] px-2 py-0.5 rounded border border-white/5">
                      {rev.id}
                    </span>

                    {/* Verified Badge */}
                    {rev.verifiedPurchase && (
                      <span className="text-[10px] font-mono text-[#10B981] bg-[#10B981]/10 px-2 py-0.5 rounded-full border border-[#10B981]/30 flex items-center gap-1 font-semibold">
                        <CheckCircle2 className="w-3 h-3" />
                        VERIFIED
                      </span>
                    )}

                    {/* Aspect Badge */}
                    <span className="text-[10px] font-mono text-slate-300 bg-white/5 px-2 py-0.5 rounded-full border border-white/10 uppercase">
                      {rev.aspect}
                    </span>
                  </div>

                  {/* Discrepancy Alert Tag */}
                  <div className="flex items-center gap-2">
                    {rev.hasDiscrepancy && (
                      <span className="text-[10px] font-mono font-bold text-[#F59E0B] bg-[#F59E0B]/15 px-2 py-0.5 rounded-full border border-[#F59E0B]/40 flex items-center gap-1 shadow-sm">
                        <AlertTriangle className="w-3 h-3 text-[#F59E0B]" />
                        RATING DISCREPANCY
                      </span>
                    )}

                    <span className="text-[11px] font-mono text-[#8A8F9E]">
                      {rev.reviewDate}
                    </span>
                  </div>
                </div>

                {/* Review Title */}
                <h4 className="text-sm font-bold text-white mb-2">
                  {rev.title}
                </h4>

                {/* Review Body with Rendered Highlight Spans */}
                <p className="text-xs text-slate-300 leading-relaxed mb-3 font-sans">
                  {rev.reviewText}
                </p>

                {/* Extracted Clause Spans Ribbon */}
                {rev.highlightSpans && rev.highlightSpans.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-2 border-t border-white/5">
                    {rev.highlightSpans.map((span, sIdx) => (
                      <span
                        key={sIdx}
                        className={`text-[11px] font-mono px-2.5 py-1 rounded-lg border flex items-center gap-1.5 ${
                          span.sentiment === "positive"
                            ? "bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30"
                            : "bg-[#EF4444]/15 text-[#EF4444] border-[#EF4444]/30"
                        }`}
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-current" />
                        <span className="italic">&ldquo;{span.text}&rdquo;</span>
                      </span>
                    ))}
                  </div>
                )}
              </article>
            );
          })
        )}
      </div>

      {/* Pagination Footer */}
      <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between text-xs font-mono text-[#8A8F9E]">
        <span>
          Page {currentPage} of {totalPages}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={currentPage <= 1}
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            className="p-1.5 rounded-lg bg-[#0D0E10] border border-white/10 text-white disabled:opacity-40 hover:bg-[#10B981] hover:text-[#0D0E10] transition-colors cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            type="button"
            disabled={currentPage >= totalPages}
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            className="p-1.5 rounded-lg bg-[#0D0E10] border border-white/10 text-white disabled:opacity-40 hover:bg-[#10B981] hover:text-[#0D0E10] transition-colors cursor-pointer"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
