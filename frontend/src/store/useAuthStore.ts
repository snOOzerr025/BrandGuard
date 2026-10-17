"use client";

import { create } from "zustand";

export interface UserProfile {
  id: string;
  email: string;
  fullName: string;
  role: string;
  company?: string;
  avatarInitials: string;
}

interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isAuthModalOpen: boolean;
  authModalMode: "login" | "signup";
  
  // Actions
  login: (email: string, password?: string) => Promise<boolean>;
  signup: (fullName: string, email: string, role: string, company?: string) => Promise<boolean>;
  logout: () => void;
  openAuthModal: (mode?: "login" | "signup") => void;
  closeAuthModal: () => void;
}

const STORAGE_KEY = "brandguard_auth_user";

const getInitialUser = (): UserProfile | null => {
  if (typeof window === "undefined") return null;
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (e) {
    console.error("Failed to parse saved user", e);
  }
  return null;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: getInitialUser(),
  isAuthenticated: Boolean(getInitialUser()),
  isAuthModalOpen: false,
  authModalMode: "login",

  login: async (email: string, _password?: string) => {
    // Generate profile based on email or demo presets
    let fullName = "Executive Analyst";
    let role = "Principal Brand Strategist";
    let company = "OmniGlobal Consumer Corp";

    if (email.includes("director") || email.includes("admin")) {
      fullName = "Sarah Jenkins";
      role = "Global VP of Product Quality";
      company = "Sony Global Electronics";
    } else if (email.includes("engineer") || email.includes("ml")) {
      fullName = "Dr. Marcus Vance";
      role = "Lead ABSA NLP Researcher";
      company = "BrandGuard AI Labs";
    } else if (email.includes("@")) {
      const namePart = email.split("@")[0].replace(/[._]/g, " ");
      fullName = namePart
        .split(" ")
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(" ");
    }

    const initials = fullName
      .split(" ")
      .map((n) => n[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();

    const user: UserProfile = {
      id: `usr-${Date.now()}`,
      email,
      fullName,
      role,
      company,
      avatarInitials: initials || "BG",
    };

    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    }

    set({ user, isAuthenticated: true, isAuthModalOpen: false });
    return true;
  },

  signup: async (fullName: string, email: string, role: string, company?: string) => {
    const initials = fullName
      .split(" ")
      .map((n) => n[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();

    const user: UserProfile = {
      id: `usr-${Date.now()}`,
      email,
      fullName,
      role: role || "Product Quality Analyst",
      company: company || "Enterprise Intelligence",
      avatarInitials: initials || "BG",
    };

    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    }

    set({ user, isAuthenticated: true, isAuthModalOpen: false });
    return true;
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(STORAGE_KEY);
    }
    set({ user: null, isAuthenticated: false });
  },

  openAuthModal: (mode = "login") => set({ isAuthModalOpen: true, authModalMode: mode }),
  closeAuthModal: () => set({ isAuthModalOpen: false }),
}));
