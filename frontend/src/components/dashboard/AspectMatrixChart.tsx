"use client";

import React, { useMemo } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import { AspectSentiment } from "../../lib/api";
import { useDashboardStore } from "../../store/useDashboardStore";
import { SlidersHorizontal, ArrowUpRight } from "lucide-react";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface Props {
  aspects: AspectSentiment[];
}

export const AspectMatrixChart: React.FC<Props> = ({ aspects }) => {
  const { selectedAspect, setSelectedAspect } = useDashboardStore();

  const labels = aspects.map((a) => a.aspect);

  const data = useMemo(() => {
    return {
      labels,
      datasets: [
        {
          label: "Positive %",
          data: aspects.map((a) => a.positive),
          backgroundColor: "#10B981",
          borderRadius: 4,
          stack: "stack0",
        },
        {
          label: "Neutral %",
          data: aspects.map((a) => a.neutral),
          backgroundColor: "#4B5563",
          borderRadius: 4,
          stack: "stack0",
        },
        {
          label: "Negative %",
          data: aspects.map((a) => a.negative),
          backgroundColor: "#EF4444",
          borderRadius: 4,
          stack: "stack0",
        },
      ],
    };
  }, [aspects, labels]);

  const options: ChartOptions<"bar"> = {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        stacked: true,
        max: 100,
        grid: {
          color: "rgba(255, 255, 255, 0.05)",
        },
        ticks: {
          color: "#8A8F9E",
          font: { family: "JetBrains Mono", size: 10 },
          callback: (value) => `${value}%`,
        },
      },
      y: {
        stacked: true,
        grid: { display: false },
        ticks: {
          color: "#FFFFFF",
          font: { family: "Inter", size: 12, weight: 600 },
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: "#13151A",
        borderColor: "rgba(16, 185, 129, 0.4)",
        borderWidth: 1,
        titleColor: "#FFFFFF",
        bodyColor: "#8A8F9E",
        titleFont: { family: "JetBrains Mono", size: 12, weight: "bold" },
        bodyFont: { family: "JetBrains Mono", size: 11 },
        padding: 12,
        callbacks: {
          afterTitle: (context) => {
            const aspectName = context[0].label;
            const item = aspects.find((a) => a.aspect === aspectName);
            return item ? `LOO Star Drag: ${item.looImpact >= 0 ? "+" : ""}${item.looImpact.toFixed(2)}★` : "";
          },
        },
      },
    },
    onClick: (_event, elements) => {
      if (elements && elements.length > 0) {
        const index = elements[0].index;
        const clickedAspect = labels[index];
        setSelectedAspect(clickedAspect === selectedAspect ? null : clickedAspect);
      }
    },
  };

  return (
    <div className="p-6 rounded-3xl bg-[#13151A]/80 border border-white/10 backdrop-blur-xl shadow-2xl flex flex-col justify-between">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-[#10B981]/10 text-[#10B981]">
            <SlidersHorizontal className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
              Aspect Sentiment & Impact Matrix
            </h3>
            <p className="text-xs text-[#8A8F9E] font-sans">
              Horizontal stacked decomposition with Leave-One-Out (LOO) Star Drag
            </p>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
            <span className="text-slate-300">Positive</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#4B5563]" />
            <span className="text-slate-300">Neutral</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444]" />
            <span className="text-slate-300">Negative</span>
          </div>
        </div>
      </div>

      {/* Chart.js Container strictly constrained to max-h-[380px] */}
      <div className="chart-container h-[320px] max-h-[380px] w-full">
        <Bar data={data} options={options} />
      </div>

      {/* Interactive Aspect Pills & LOO Drag Badges */}
      <div className="mt-6 pt-4 border-t border-white/5 flex flex-wrap items-center justify-between gap-2">
        <span className="text-[11px] font-mono text-[#8A8F9E]">
          Click any aspect bar to cross-filter review stream:
        </span>
        <div className="flex flex-wrap gap-2">
          {aspects.slice(0, 4).map((a) => (
            <button
              key={a.aspect}
              type="button"
              onClick={() => setSelectedAspect(selectedAspect === a.aspect ? null : a.aspect)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all flex items-center gap-1.5 cursor-pointer ${
                selectedAspect === a.aspect
                  ? "bg-[#10B981] text-[#0D0E10] font-bold"
                  : "bg-[#0D0E10] text-[#8A8F9E] hover:text-white border border-white/10"
              }`}
            >
              <span>{a.aspect}</span>
              <span className={a.looImpact >= 0 ? "text-emerald-400" : "text-rose-400"}>
                {a.looImpact >= 0 ? "+" : ""}{a.looImpact.toFixed(2)}★
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
