"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { ArrowUpRight, BarChart3, ShieldCheck } from "lucide-react";
import { useDashboardStore } from "../../store/useDashboardStore";

const NAV_LINKS = [
  { label: "01. Capabilities", href: "#capabilities" },
  { label: "02. Architecture", href: "#architecture" },
  { label: "03. Benchmarks", href: "#benchmarks" },
];

export const Navbar: React.FC = () => {
  const [hoveredLink, setHoveredLink] = useState<string | null>(null);
  const { currentView, launchDashboard, returnToLanding } = useDashboardStore();

  const handleScrollTo = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault();
    if (currentView !== "landing") {
      returnToLanding();
      setTimeout(() => {
        const el = document.querySelector(href);
        el?.scrollIntoView({ behavior: "smooth" });
      }, 700);
      return;
    }
    const el = document.querySelector(href);
    el?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-[#0D0E10]/80 border-b border-white/10 transition-colors">
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Left: Brand Identity */}
        <div
          onClick={returnToLanding}
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <div className="flex items-center">
            <span className="text-xl sm:text-2xl font-black tracking-tighter text-white">
              BRANDGUARD
            </span>
            <span className="w-2 h-2 rounded-full bg-[#10B981] ml-0.5 shadow-[0_0_12px_#10B981] animate-pulse" />
          </div>

          <span className="hidden sm:inline-block font-mono text-[10px] tracking-widest text-[#8A8F9E] bg-[#13151A] px-2.5 py-1 rounded-full border border-white/10">
            B2B ARCHITECTURE v2.4
          </span>
        </div>

        {/* Center: Navigation Links (on landing view) */}
        <nav className="hidden md:flex items-center gap-8">
          {NAV_LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              onClick={(e) => handleScrollTo(e, link.href)}
              onMouseEnter={() => setHoveredLink(link.label)}
              onMouseLeave={() => setHoveredLink(null)}
              className="relative py-2 text-xs font-mono tracking-widest text-[#8A8F9E] hover:text-white transition-colors"
            >
              {link.label}
              {hoveredLink === link.label && (
                <motion.div
                  layoutId="nav-underline"
                  className="absolute bottom-0 left-0 right-0 h-[2px] bg-[#10B981] shadow-[0_0_8px_#10B981]"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
            </a>
          ))}
        </nav>

        {/* Right: Actions */}
        <div className="flex items-center gap-4">
          {currentView === "landing" ? (
            <button
              type="button"
              onClick={() => launchDashboard()}
              className="relative group px-5 py-2.5 rounded-full bg-[#10B981]/10 hover:bg-[#10B981] text-[#10B981] hover:text-[#0D0E10] border border-[#10B981]/30 hover:border-[#10B981] text-xs font-mono font-bold tracking-wider flex items-center gap-2.5 transition-all duration-300 shadow-[0_0_20px_rgba(16,185,129,0.15)] hover:shadow-[0_0_30px_rgba(16,185,129,0.4)] cursor-pointer"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#10B981] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#10B981]"></span>
              </span>
              <span>Launch Executive Dashboard</span>
              <ArrowUpRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </button>
          ) : (
            <button
              type="button"
              onClick={returnToLanding}
              className="px-4 py-2 rounded-full bg-[#13151A] hover:bg-[#1F232B] text-[#8A8F9E] hover:text-white border border-white/10 text-xs font-mono transition-all cursor-pointer flex items-center gap-2"
            >
              <span>← Editorial Overview</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
