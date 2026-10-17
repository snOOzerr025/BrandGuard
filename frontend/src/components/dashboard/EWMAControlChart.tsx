"use client";

import React, { useMemo } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { AnomalyPoint } from "../../lib/api";
import { useDashboardStore } from "../../store/useDashboardStore";
import { Activity, AlertTriangle, ArrowUpRight } from "lucide-react";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface Props {
  points: AnomalyPoint[];
}

export const EWMAControlChart: React.FC<Props> = ({ points }) => {
  const { toggleCopilot } = useDashboardStore();

  const labels = points.map((p) => p.date);

  const data = useMemo(() => {
    return {
      labels,
      datasets: [
        {
          label: "+3σ Upper Control Limit (UCL)",
          data: points.map((p) => p.upperBound),
          borderColor: "rgba(239, 68, 68, 0.4)",
          borderDash: [5, 5],
          borderWidth: 1,
          pointRadius: 0,
          fill: false,
        },
        {
          label: "Deseasonalized EWMA Sentiment",
          data: points.map((p) => p.sentiment),
          borderColor: "#10B981",
          borderWidth: 2.5,
          pointBackgroundColor: points.map((p) => (p.isBreach ? "#EF4444" : "#10B981")),
          pointBorderColor: points.map((p) => (p.isBreach ? "#FFFFFF" : "#0D0E10")),
          pointBorderWidth: points.map((p) => (p.isBreach ? 2 : 1)),
          pointRadius: points.map((p) => (p.isBreach ? 6 : 3.5)),
          pointHoverRadius: 8,
          tension: 0.3,
          fill: {
            target: "origin",
            above: "rgba(16, 185, 129, 0.05)",
          },
        },
        {
          label: "-3σ Lower Control Limit (LCL)",
          data: points.map((p) => p.lowerBound),
          borderColor: "rgba(239, 68, 68, 0.7)",
          borderDash: [5, 5],
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
        },
      ],
    };
  }, [points, labels]);

  const options: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        grid: {
          color: "rgba(255, 255, 255, 0.05)",
        },
        ticks: {
          color: "#8A8F9E",
          font: { family: "JetBrains Mono", size: 10 },
        },
      },
      y: {
        min: 0,
        max: 1.0,
        grid: {
          color: "rgba(255, 255, 255, 0.05)",
        },
        ticks: {
          color: "#8A8F9E",
          font: { family: "JetBrains Mono", size: 10 },
          callback: (value) => Number(value).toFixed(2),
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: "#13151A",
        borderColor: "rgba(239, 68, 68, 0.4)",
        borderWidth: 1,
        titleColor: "#FFFFFF",
        bodyColor: "#8A8F9E",
        titleFont: { family: "JetBrains Mono", size: 12, weight: "bold" },
        bodyFont: { family: "JetBrains Mono", size: 11 },
        padding: 12,
        callbacks: {
          afterBody: (context) => {
            const index = context[0].dataIndex;
            const pt = points[index];
            if (pt.isBreach && pt.triggerReason) {
              return `\n⚠️ 3σ CONTROL BREACH\nRoot Cause: ${pt.triggerReason}\nClick to triage with RAG Copilot`;
            }
            return "";
          },
        },
      },
    },
    onClick: (_event, elements) => {
      if (elements && elements.length > 0) {
        const index = elements[0].index;
        const pt = points[index];
        if (pt.isBreach) {
          toggleCopilot(
            true,
            `Explain the anomaly on ${pt.date}: ${pt.triggerReason || "Statistical breach"}`
          );
        }
      }
    },
  };

  return (
    <div id="anomaly-timeline" className="p-6 rounded-3xl bg-[#13151A]/80 border border-white/10 backdrop-blur-xl shadow-2xl flex flex-col justify-between">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-[#F59E0B]/10 text-[#F59E0B]">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-white">
              STL + EWMA 3σ Statistical Control Chart
            </h3>
            <p className="text-xs text-[#8A8F9E] font-sans">
              Lucas-Saccucci daily weighting (λ=0.2) with dynamic ±3σ anomaly control bounds
            </p>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2.5 h-0.5 bg-emerald-400" />
            <span>EWMA Sentiment</span>
          </div>
          <div className="flex items-center gap-1.5 text-rose-400">
            <span className="w-2.5 h-0.5 bg-rose-400 border-dashed" />
            <span>±3σ Threshold</span>
          </div>
        </div>
      </div>

      {/* Chart.js Container strictly constrained to max-h-[380px] */}
      <div className="chart-container h-[280px] max-h-[380px] w-full">
        <Line data={data} options={options} />
      </div>

      {/* Breaches Notification Strip */}
      <div className="mt-4 pt-3 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs font-mono text-amber-400">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          <span>Click any red breach point to open RAG diagnostic attribution</span>
        </div>
        <button
          type="button"
          onClick={() => toggleCopilot(true, "Why is Service & Build Quality dragging down overall rating?")}
          className="text-xs font-mono text-[#10B981] hover:underline flex items-center gap-1 cursor-pointer"
        >
          <span>Triage All Breaches</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
