import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Core Invariants
        "brand-black": "#0D0E10",
        "brand-card": "#13151A",
        "brand-border": "rgba(255, 255, 255, 0.08)",
        "brand-emerald": "#10B981",
        "brand-emerald-dark": "#059669",
        "brand-emerald-glow": "rgba(16, 185, 129, 0.18)",
        "brand-amber": "#F59E0B",
        "brand-crimson": "#EF4444",
        "brand-muted": "#8A8F9E",
        "brand-text": "#FFFFFF",

        // Frame 1 Palette: Warm Ivory & Deep Editorial Blue & Coral Orange
        "ivory-base": "#FAF6F0",
        "ivory-warm": "#F5ECE1",
        "ivory-cream": "#EFE4D4",
        "editorial-blue": "#0A1128",
        "editorial-blue-deep": "#050914",
        "editorial-blue-card": "#0F1A38",
        "editorial-blue-border": "rgba(255, 255, 255, 0.12)",
        "coral-orange": "#FF5A36",
        "coral-light": "#FF7A5C",
        "coral-glow": "rgba(255, 90, 54, 0.28)",

        // Frame 2 & Secondary Palette: Sage Green & Deep Olive & Soft Grids
        "sage-base": "#9CAF88",
        "sage-soft": "#D2DCB6",
        "sage-muted": "#7C8E68",
        "olive-deep": "#242C1D",
        "olive-dark": "#181E13",
        "olive-card": "#2C3524",
        "concrete-grey": "#64748B",
        "concrete-light": "#94A3B8",
        "concrete-dark": "#1E293B",

        // Frame 3 & 4 Palette: Soft Strawberry Pink & Vibrant Crimson & Lime Green
        "strawberry-soft": "#FDE2E4",
        "strawberry-pink": "#FFA6B6",
        "strawberry-deep": "#F4708A",
        "crimson-vibrant": "#DC2626",
        "crimson-deep": "#991B1B",
        "lime-vibrant": "#84CC16",
        "lime-electric": "#A3E635",

        // Dashboard Palette: Cosmic Latte, Mocha Cream, Deep Burgundy & Concrete
        "cosmic-latte": "#FFF8E7",
        "mocha-cream": "#EADBC8",
        "mocha-soft": "#DAC7B3",
        "mocha-dark": "#251D1A",
        "mocha-card": "#332723",
        "burgundy-deep": "#4A0E17",
        "burgundy-dark": "#2B070D",
        "burgundy-card": "#380B12",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "sans-serif"],
        serif: ["var(--font-playfair)", "Playfair Display", "serif"],
        mono: ["var(--font-jetbrains-mono)", "JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
