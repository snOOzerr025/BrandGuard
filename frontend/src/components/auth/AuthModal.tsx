"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Lock,
  Mail,
  User,
  Building,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  Eye,
  EyeOff,
  CheckCircle2,
} from "lucide-react";
import { useAuthStore } from "../../store/useAuthStore";
import { ShaderGradient } from "../canvas/ShaderGradient";

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, authModalMode, closeAuthModal, login, signup } = useAuthStore();
  const [mode, setMode] = useState<"login" | "signup">(authModalMode);
  
  // Form states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("Principal Brand Strategist");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Sync mode with store when opened
  React.useEffect(() => {
    if (isAuthModalOpen) {
      setMode(authModalMode);
      setSuccessMessage(null);
    }
  }, [isAuthModalOpen, authModalMode]);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (mode === "login") {
        await login(email || "analyst@brandguard.ai", password);
        setSuccessMessage("Authentication verified. Loading workspace telemetry...");
      } else {
        await signup(
          fullName || "Enterprise Analyst",
          email || "enterprise.user@brandguard.ai",
          role,
          company || "Global Consumer Brands"
        );
        setSuccessMessage("Account provisioned. Initializing neural models...");
      }

      setTimeout(() => {
        setIsLoading(false);
        closeAuthModal();
      }, 700);
    } catch (err) {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async (demoEmail: string, demoRole: string) => {
    setIsLoading(true);
    setEmail(demoEmail);
    setPassword("••••••••••••");
    setTimeout(async () => {
      await login(demoEmail);
      setSuccessMessage(`Authorized as ${demoRole}`);
      setTimeout(() => {
        setIsLoading(false);
        closeAuthModal();
      }, 600);
    }, 400);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
        {/* Backdrop overlay */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={closeAuthModal}
          className="fixed inset-0 bg-black/70 backdrop-blur-md transition-opacity"
        />

        {/* Modal Card with Shader Gradient Background Only */}
        <motion.div
          initial={{ opacity: 0, scale: 0.94, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
          className="relative w-full max-w-lg rounded-3xl overflow-hidden border border-white/15 shadow-[0_25px_70px_rgba(0,0,0,0.8)] z-10"
        >
          {/* Integrated Shader Gradient Canvas */}
          <div className="absolute inset-0 z-0">
            <ShaderGradient />
          </div>

          {/* Frosted Glass Overlay Content */}
          <div className="relative z-10 p-6 sm:p-8 backdrop-blur-2xl bg-[#0A1128]/85 text-[#FAF6F0]">
            {/* Close button */}
            <button
              onClick={closeAuthModal}
              className="absolute top-5 right-5 p-2 rounded-full bg-white/5 hover:bg-white/10 text-[#8A8F9E] hover:text-white transition-colors cursor-pointer border border-white/10"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Brand Header */}
            <div className="text-center space-y-2 mb-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FF5A36]/15 border border-[#FF5A36]/30 text-[#FF5A36] text-[11px] font-mono font-medium tracking-wider">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>ENTERPRISE GATEWAY v2.4</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
                {mode === "login" ? "AUTHENTICATE TELEMETRY" : "PROVISION ACCESS"}
              </h2>
              <p className="text-xs font-mono text-[#8A8F9E]">
                {mode === "login"
                  ? "Access multi-product ABSA dashboards and real user review engines."
                  : "Register your enterprise workspace for deterministic NLP audit."}
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
                NEW ACCOUNT
              </button>
            </div>

            {/* Quick Demo Credentials */}
            <div className="mb-6 space-y-2">
              <div className="text-[10px] font-mono text-[#8A8F9E] uppercase tracking-wider">
                Instant One-Click Demo Access
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => handleDemoLogin("analyst@brandguard.ai", "Senior Analyst")}
                  className="px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-[11px] font-mono text-left text-[#FAF6F0] flex items-center justify-between group transition-all cursor-pointer"
                >
                  <div>
                    <div className="font-semibold text-white">Product Analyst</div>
                    <div className="text-[9px] text-[#8A8F9E]">Sony / Apple SKU Access</div>
                  </div>
                  <Sparkles className="w-3.5 h-3.5 text-[#FF5A36] group-hover:scale-110 transition-transform" />
                </button>
                <button
                  type="button"
                  onClick={() => handleDemoLogin("director@brandguard.ai", "VP Brand Intelligence")}
                  className="px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-[11px] font-mono text-left text-[#FAF6F0] flex items-center justify-between group transition-all cursor-pointer"
                >
                  <div>
                    <div className="font-semibold text-white">Executive Director</div>
                    <div className="text-[9px] text-[#8A8F9E]">Full Audit Clearance</div>
                  </div>
                  <Sparkles className="w-3.5 h-3.5 text-[#9CAF88] group-hover:scale-110 transition-transform" />
                </button>
              </div>
            </div>

            <div className="relative flex items-center justify-center my-4">
              <div className="border-t border-white/10 w-full" />
              <span className="bg-[#0A1128] px-3 text-[10px] font-mono text-[#8A8F9E] absolute uppercase">
                Or with Enterprise SSO
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
                        placeholder="Elena Rostova"
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-xs text-white placeholder:text-[#8A8F9E]/50 focus:outline-none focus:border-[#FF5A36] transition-colors"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-mono text-[#8A8F9E] uppercase tracking-wider mb-1">
                        Company / Brand
                      </label>
                      <div className="relative">
                        <Building className="w-4 h-4 text-[#8A8F9E] absolute left-3 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          value={company}
                          onChange={(e) => setCompany(e.target.value)}
                          placeholder="Acme Electronics"
                          className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-xs text-white placeholder:text-[#8A8F9E]/50 focus:outline-none focus:border-[#FF5A36] transition-colors"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-[11px] font-mono text-[#8A8F9E] uppercase tracking-wider mb-1">
                        Workspace Role
                      </label>
                      <select
                        value={role}
                        onChange={(e) => setRole(e.target.value)}
                        className="w-full px-3 py-2.5 rounded-xl bg-[#0E1833] border border-white/10 text-xs text-white focus:outline-none focus:border-[#FF5A36] transition-colors"
                      >
                        <option value="Product Intelligence Lead">Product Lead</option>
                        <option value="VP Brand Strategy">VP Brand</option>
                        <option value="ML Data Scientist">ML Engineer</option>
                        <option value="Customer Insights Manager">Insights Mgr</option>
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
                    placeholder="analyst@enterprise.com"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-xs text-white placeholder:text-[#8A8F9E]/50 focus:outline-none focus:border-[#FF5A36] transition-colors"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[11px] font-mono text-[#8A8F9E] uppercase tracking-wider">
                    Password
                  </label>
                  {mode === "login" && (
                    <span className="text-[10px] font-mono text-[#FF5A36] hover:underline cursor-pointer">
                      Forgot Access Key?
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

              {successMessage && (
                <div className="flex items-center gap-2 p-3 rounded-xl bg-[#9CAF88]/15 border border-[#9CAF88]/30 text-xs font-mono text-[#9CAF88]">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{successMessage}</span>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 py-3 px-4 rounded-xl bg-gradient-to-r from-[#FF5A36] to-[#DC2626] hover:from-[#FF451D] hover:to-[#B91C1C] text-white font-mono font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-[0_0_25px_rgba(255,90,54,0.4)] hover:shadow-[0_0_35px_rgba(255,90,54,0.6)] cursor-pointer disabled:opacity-50"
              >
                {isLoading ? (
                  <span className="inline-flex items-center gap-2">
                    <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>VERIFYING CRYPTOGRAPHIC TOKEN...</span>
                  </span>
                ) : (
                  <>
                    <span>{mode === "login" ? "ENTER EXECUTIVE WORKSPACE" : "CREATE WORKSPACE ACCOUNT"}</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-5 text-center text-[10px] font-mono text-[#8A8F9E]">
              Protected by 256-bit TLS • Zero Data Retention Model • SOC2 Type II Certified
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
