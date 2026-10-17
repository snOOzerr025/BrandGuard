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
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
