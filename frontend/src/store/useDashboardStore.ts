import { create } from "zustand";

interface DashboardState {
  currentView: "landing" | "dashboard";
  isTransitioning: boolean;
  activeProductId: string;
  isCopilotOpen: boolean;
  copilotInitialPrompt: string | null;
  selectedAspect: string | null;
  discrepancyOnly: boolean;
  highlightedCitationId: string | null;
  
  // Actions
  launchDashboard: (prompt?: string) => void;
  returnToLanding: () => void;
  toggleCopilot: (open?: boolean, prompt?: string) => void;
  setSelectedAspect: (aspect: string | null) => void;
  setDiscrepancyOnly: (val: boolean) => void;
  setHighlightedCitationId: (id: string | null) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  currentView: "landing",
  isTransitioning: false,
  activeProductId: "prod-sony-xm5",
  isCopilotOpen: false,
  copilotInitialPrompt: null,
  selectedAspect: null,
  discrepancyOnly: false,
  highlightedCitationId: null,

  launchDashboard: (prompt?: string) => {
    set({ isTransitioning: true });
    setTimeout(() => {
      set({
        currentView: "dashboard",
        isTransitioning: false,
        copilotInitialPrompt: prompt || null,
        isCopilotOpen: Boolean(prompt),
      });
      // Scroll to top of dashboard view
      window.scrollTo({ top: 0, behavior: "instant" });
    }, 900); // 900ms cinematic camera zoom
  },

  returnToLanding: () => {
    set({ isTransitioning: true });
    setTimeout(() => {
      set({ currentView: "landing", isTransitioning: false });
      window.scrollTo({ top: 0, behavior: "instant" });
    }, 600);
  },

  toggleCopilot: (open, prompt) =>
    set((state) => ({
      isCopilotOpen: open !== undefined ? open : !state.isCopilotOpen,
      copilotInitialPrompt: prompt || state.copilotInitialPrompt,
    })),

  setSelectedAspect: (aspect) => set({ selectedAspect: aspect }),
  setDiscrepancyOnly: (val) => set({ discrepancyOnly: val }),
  setHighlightedCitationId: (id) => set({ highlightedCitationId: id }),
}));
