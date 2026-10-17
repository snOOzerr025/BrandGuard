"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ShieldCheck,
  Lock,
  Mail,
  User,
  Building,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Eye,
  EyeOff,
  CheckCircle2,
} from "lucide-react";
import { ShaderGradient } from "../../components/canvas/ShaderGradient";
import { useAuthStore } from "../../store/useAuthStore";
import { useDashboardStore } from "../../store/useDashboardStore";

export default function LoginPage() {
  const router = useRouter();
  const { login, signup, isAuthenticated, user } = useAuthStore();
  const { launchDashboard } = useDashboardStore();

  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("Principal Brand Strategist");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (mode === "login") {
        await login(email || "analyst@brandguard.ai", password);
        setStatusMsg("Credentials verified. Routing to Live Dashboard...");
      } else {
        await signup(
          fullName || "Enterprise Analyst",
          email || "enterprise.user@brandguard.ai",
          role,
          company || "Global Consumer Brands"
        );
        setStatusMsg("Account initialized. Setting up telemetry...");
      }

      setTimeout(() => {
        setIsLoading(false);
        launchDashboard();
        router.push("/");
      }, 700);
    } catch {
      setIsLoading(false);
    }
  };

  const handleDemo = async (demoEmail: string, demoRole: string) => {
    setIsLoading(true);
    setEmail(demoEmail);
    setPassword("••••••••••••");
    setTimeout(async () => {
      await login(demoEmail);
      setStatusMsg(`Authorized as ${demoRole}. Launching...`);
      setTimeout(() => {
        setIsLoading(false);
        launchDashboard();
        router.push("/");
      }, 600);
    }, 400);
  };

  return (
    <main className="relative min-h-screen w-full flex items-center justify-center p-4 sm:p-6 bg-[#0A1128] text-[#FAF6F0] overflow-hidden selection:bg-[#FF5A36]/30">
      {/* Background in Shader Gradient ONLY as requested */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <ShaderGradient />
      </div>

      {/* Return to Landing overview button */}
      <div className="fixed top-6 left-6 z-20">
        <button
          onClick={() => router.push("/")}
          className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#0A1128]/70 hover:bg-white/10 text-xs font-mono text-[#FAF6F0] border border-white/10 backdrop-blur-xl transition-all cursor-pointer group"
        >
          <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform text-[#FF5A36]" />
          <span>RETURN TO OVERVIEW</span>
        </button>
      </div>

      {/* Central Glassmorphic Card */}
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-10 w-full max-w-md rounded-3xl p-8 sm:p-10 backdrop-blur-2xl bg-[#0A1128]/80 border border-white/15 shadow-[0_30px_90px_rgba(0,0,0,0.7)]"
      >
        {/* Brand identity */}
        <div className="text-center space-y-3 mb-8">
          <div className="flex items-center justify-center gap-2">
            <span className="text-2xl font-black tracking-tighter text-[#FAF6F0]">
              BRANDGUARD
            </span>
            <span className="w-2 h-2 rounded-full bg-[#FF5A36] shadow-[0_0_12px_#FF5A36] animate-pulse" />
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FF5A36]/15 border border-[#FF5A36]/30 text-[#FF5A36] text-[10px] font-mono font-medium tracking-wider">
            <ShieldCheck className="w-3 h-3" />
            <span>ENTERPRISE AUTHENTICATION PORTAL</span>
          </div>

          <p className="text-xs font-mono text-[#8A8F9E]">
            {mode === "login"
              ? "Access deterministic multi-product ABSA telemetry & review pipelines."
              : "Provision high-throughput review intelligence workspace."}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex p-1 rounded-xl bg-white/5 border border-white/10 mb-6">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`flex-1 py-2 text-xs font-mono font-bold tracking-wider rounded-lg transition-all ${
              mode === "login"
                ? "bg-[#FF5A36] text-white shadow-[0_0_20px_rgba(255,90,54,0.35)]"
                : "text-[#8A8F9E] hover:text-white"
            }`}
          >
            SIGN IN
          </button>
          <button
            type="button"
            onClick={() => setMode("signup")}
            className={`flex-1 py-2 text-xs font-mono font-bold tracking-wider rounded-lg transition-all ${
              mode === "signup"
                ? "bg-[#FF5A36] text-white shadow-[0_0_20px_rgba(255,90,54,0.35)]"
                : "text-[#8A8F9E] hover:text-white"
            }`}
          >
            REGISTER
          </button>
        </div>

        {/* One Click Instant Demo Logins */}
        <div className="mb-6 space-y-2">
          <div className="text-[10px] font-mono text-[#8A8F9E] uppercase tracking-wider flex items-center justify-between">
            <span>Instant Demo Access</span>
            <span className="text-[#9CAF88]">1-Click Login</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleDemo("analyst@brandguard.ai", "Lead Product Analyst")}
              className="px-3 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-[11px] font-mono text-left text-[#FAF6F0] flex items-center justify-between group transition-all cursor-pointer"
            >
              <div>
                <div className="font-semibold text-white">Product Analyst</div>
                <div className="text-[9px] text-[#8A8F9E]">Sony & Apple SKUs</div>
              </div>
              <Sparkles className="w-3.5 h-3.5 text-[#FF5A36] group-hover:scale-110 transition-transform" />
            </button>
            <button
              type="button"
              onClick={() => handleDemo("director@brandguard.ai", "VP Brand Strategy")}
              className="px-3 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-[11px] font-mono text-left text-[#FAF6F0] flex items-center justify-between group transition-all cursor-pointer"
            >
              <div>
                <div className="font-semibold text-white">Executive Director</div>
                <div className="text-[9px] text-[#8A8F9E]">Full Audit Clearance</div>
              </div>
              <Sparkles className="w-3.5 h-3.5 text-[#9CAF88] group-hover:scale-110 transition-transform" />
            </button>
          </div>
        </div>

        <div className="relative flex items-center justify-center my-5">
          <div className="border-t border-white/10 w-full" />
          <span className="bg-[#0A1128] px-3 text-[10px] font-mono text-[#8A8F9E] absolute uppercase tracking-widest">
            Or Standard Credentials
          </span>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "signup" && (
            <>
              <div>
                <label className="block text-[11px] font-mono text-[#8A8F9E] uppercase tracking-wider mb-1">
                  Full Name
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-[#8A8F9E] absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Marcus Vance"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-xs text-white placeholder:text-[#8A8F9E]/50 focus:outline-none focus:border-[#FF5A36] transition-colors"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-mono text-[#8A8F9E] uppercase tracking-wider mb-1">
                    Company
                  </label>
                  <div className="relative">
                    <Building className="w-4 h-4 text-[#8A8F9E] absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                      placeholder="Omni Corp"
                      className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-xs text-white placeholder:text-[#8A8F9E]/50 focus:outline-none focus:border-[#FF5A36] transition-colors"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-[11px] font-mono text-[#8A8F9E] uppercase tracking-wider mb-1">
                    Role
                  </label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl bg-[#0E1833] border border-white/10 text-xs text-white focus:outline-none focus:border-[#FF5A36] transition-colors"
                  >
                    <option value="Principal Brand Strategist">Brand Lead</option>
                    <option value="VP Product Quality">VP Quality</option>
                    <option value="ML Research Scientist">ML Engineer</option>
                  </select>
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-[11px] font-mono text-[#8A8F9E] uppercase tracking-wider mb-1">
              Corporate Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-[#8A8F9E] absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@brandguard.ai"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-xs text-white placeholder:text-[#8A8F9E]/50 focus:outline-none focus:border-[#FF5A36] transition-colors"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-[11px] font-mono text-[#8A8F9E] uppercase tracking-wider">
                Access Key / Password
              </label>
              {mode === "login" && (
                <span className="text-[10px] font-mono text-[#FF5A36] hover:underline cursor-pointer">
                  Reset
                </span>
              )}
            </div>
            <div className="relative">
              <Lock className="w-4 h-4 text-[#8A8F9E] absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-10 py-2.5 rounded-xl bg-white/5 border border-white/10 text-xs text-white placeholder:text-[#8A8F9E]/50 focus:outline-none focus:border-[#FF5A36] transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#8A8F9E] hover:text-white"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {statusMsg && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-[#9CAF88]/15 border border-[#9CAF88]/30 text-xs font-mono text-[#9CAF88]">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{statusMsg}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full mt-4 py-3.5 px-4 rounded-xl bg-gradient-to-r from-[#FF5A36] to-[#DC2626] hover:from-[#FF451D] hover:to-[#B91C1C] text-white font-mono font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-[0_0_30px_rgba(255,90,54,0.4)] hover:shadow-[0_0_40px_rgba(255,90,54,0.6)] cursor-pointer disabled:opacity-50"
          >
            {isLoading ? (
              <span className="inline-flex items-center gap-2">
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>AUTHORIZING...</span>
              </span>
            ) : (
              <>
                <span>{mode === "login" ? "ENTER EXECUTIVE DASHBOARD" : "INITIALIZE ACCOUNT"}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-[10px] font-mono text-[#8A8F9E]">
          Deterministic NLP • HNSW 1536d Vector Embeddings • FIPS 140-2 Compliant
        </div>
      </motion.div>
    </main>
  );
}
