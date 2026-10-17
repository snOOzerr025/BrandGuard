"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { User, LogIn, LogOut, Shield, ChevronDown, ExternalLink } from "lucide-react";
import Link from "next/link";
import { useDashboardStore } from "../../store/useDashboardStore";
import { useAuthStore } from "../../store/useAuthStore";

const NAV_LINKS = [
  { label: "01. Architecture", href: "#architecture" },
  { label: "02. Commerce Vortex", href: "#swirling-channel" },
  { label: "03. Capabilities", href: "#capabilities" },
  { label: "04. Benchmarks", href: "#benchmarks" },
];

export const Navbar: React.FC = () => {
  const [hoveredLink, setHoveredLink] = useState<string | null>(null);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const { currentView, returnToLanding } = useDashboardStore();
  const { user, isAuthenticated, openAuthModal, logout } = useAuthStore();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

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
    <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-2xl bg-[#0A1128]/80 border-b border-white/10 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Left: Brand Identity */}
        <div
          onClick={returnToLanding}
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <div className="flex items-center">
            <span className="text-xl sm:text-2xl font-black tracking-tighter text-[#FAF6F0]">
              BRANDGUARD
            </span>
            <span className="w-2 h-2 rounded-full bg-[#FF5A36] ml-1 shadow-[0_0_12px_#FF5A36] animate-pulse" />
          </div>

          <span className="hidden sm:inline-block font-mono text-[10px] tracking-widest text-[#8A8F9E] bg-[#0E1833] px-2.5 py-1 rounded-full border border-white/10">
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
              className="relative py-2 text-xs font-mono tracking-widest text-[#FAF6F0]/70 hover:text-white transition-colors"
            >
              {link.label}
              {hoveredLink === link.label && (
                <motion.div
                  layoutId="nav-underline"
                  className="absolute bottom-0 left-0 right-0 h-[2px] bg-[#FF5A36] shadow-[0_0_8px_#FF5A36]"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
            </a>
          ))}
        </nav>

        {/* Right: Glassmorphic Log In / Sign In Action replacing big red launch dashboard */}
        <div className="flex items-center gap-3">
          {currentView === "dashboard" && (
            <button
              type="button"
              onClick={returnToLanding}
              className="px-3.5 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-[#FAF6F0] border border-white/10 text-xs font-mono transition-all cursor-pointer hidden sm:flex items-center gap-1.5"
            >
              <span>← Editorial View</span>
            </button>
          )}

          {isAuthenticated && user ? (
            /* Logged-In Glassmorphic Profile Badge */
            <div className="relative" ref={userMenuRef}>
              <button
                type="button"
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="group flex items-center gap-2.5 px-3.5 py-2 rounded-full backdrop-blur-xl bg-white/5 hover:bg-white/10 border border-white/15 hover:border-[#FF5A36]/40 transition-all cursor-pointer shadow-[0_4px_20px_rgba(0,0,0,0.3)]"
              >
                <div className="relative w-6 h-6 rounded-full bg-gradient-to-tr from-[#FF5A36] to-[#001F54] flex items-center justify-center text-[10px] font-bold text-white shadow-[0_0_10px_rgba(255,90,54,0.3)]">
                  {user.avatarInitials}
                  <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-[#9CAF88] ring-2 ring-[#0A1128]" />
                </div>
                <div className="hidden sm:block text-left">
                  <div className="text-xs font-mono font-medium text-white leading-tight">
                    {user.fullName}
                  </div>
                  <div className="text-[9px] font-mono text-[#8A8F9E] truncate max-w-[120px]">
                    {user.role}
                  </div>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-[#8A8F9E] group-hover:text-white transition-transform" />
              </button>

              <AnimatePresence>
                {isUserMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    transition={{ duration: 0.2 }}
                    className="absolute right-0 mt-2 w-64 rounded-2xl backdrop-blur-2xl bg-[#0A1128]/95 border border-white/15 p-3 shadow-2xl z-50 space-y-2 text-xs font-mono"
                  >
                    <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                      <div className="text-[10px] text-[#8A8F9E] uppercase tracking-wider">
                        Authenticated User
                      </div>
                      <div className="font-bold text-white truncate">{user.fullName}</div>
                      <div className="text-[11px] text-[#FF5A36] truncate">{user.email}</div>
                      {user.company && (
                        <div className="text-[10px] text-[#FAF6F0]/60 mt-1">
                          Org: {user.company}
                        </div>
                      )}
                    </div>

                    <Link
                      href="/login"
                      onClick={() => setIsUserMenuOpen(false)}
                      className="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-white/10 text-[#FAF6F0] transition-colors"
                    >
                      <span className="flex items-center gap-2">
                        <Shield className="w-3.5 h-3.5 text-[#FF5A36]" />
                        <span>Security & Access Key</span>
                      </span>
                      <ExternalLink className="w-3 h-3 text-[#8A8F9E]" />
                    </Link>

                    <button
                      type="button"
                      onClick={() => {
                        logout();
                        setIsUserMenuOpen(false);
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-red-400 hover:bg-red-500/10 transition-colors text-left cursor-pointer"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Log Out Session</span>
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            /* Glassmorphed Log In / Sign In button */
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => openAuthModal("login")}
                className="group relative px-4 sm:px-5 py-2.5 rounded-full backdrop-blur-xl bg-white/5 hover:bg-white/10 text-[#FAF6F0] hover:text-white border border-white/15 hover:border-[#FF5A36]/60 text-xs font-mono font-medium tracking-wider flex items-center gap-2.5 transition-all duration-300 shadow-[0_4px_25px_rgba(0,0,0,0.3)] hover:shadow-[0_0_25px_rgba(255,90,54,0.25)] cursor-pointer hover:scale-[1.02] active:scale-[0.98]"
              >
                {/* Sleek Glassmorphic Icon */}
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-white/10 to-white/5 border border-white/20 flex items-center justify-center text-[#FF5A36] group-hover:scale-110 transition-transform shadow-inner">
                  <User className="w-3.5 h-3.5" />
                </div>
                <span>Log In / Sign In</span>
              </button>

              <Link
                href="/login"
                title="Open Dedicated Full-Screen Login Page"
                className="p-2.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-[#8A8F9E] hover:text-white transition-all hidden sm:flex items-center justify-center"
              >
                <LogIn className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
