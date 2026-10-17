import { create } from "zustand";
import { MOCK_DATASETS, ProductDataset, ReviewRecord, recalculateProductDataset } from "../lib/api";

interface DashboardState {
  currentView: "landing" | "dashboard";
  isTransitioning: boolean;
  
  // Product state
  products: Record<string, ProductDataset>;
  activeProductId: string;
  
  // Copilot and filters
  isCopilotOpen: boolean;
  copilotInitialPrompt: string | null;
  selectedAspect: string | null;
  discrepancyOnly: boolean;
  highlightedCitationId: string | null;
  
  // Review Ingestion Lab modal
  isIngestModalOpen: boolean;
  
  // Actions
  launchDashboard: (prompt?: string) => void;
  returnToLanding: () => void;
  setActiveProduct: (productId: string) => void;
  addProduct: (product: ProductDataset) => void;
  addReviewsToProduct: (productId: string, newReviews: ReviewRecord[]) => void;
  toggleCopilot: (open?: boolean, prompt?: string) => void;
  setSelectedAspect: (aspect: string | null) => void;
  setDiscrepancyOnly: (val: boolean) => void;
  setHighlightedCitationId: (id: string | null) => void;
  openIngestModal: () => void;
  closeIngestModal: () => void;
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  currentView: "landing",
  isTransitioning: false,
  products: { ...MOCK_DATASETS },
  activeProductId: "prod-sony-xm5",
  isCopilotOpen: false,
  copilotInitialPrompt: null,
  selectedAspect: null,
  discrepancyOnly: false,
  highlightedCitationId: null,
  isIngestModalOpen: false,

  launchDashboard: (prompt?: string) => {
    set({ isTransitioning: true });
    setTimeout(() => {
      set({
        currentView: "dashboard",
        isTransitioning: false,
        copilotInitialPrompt: prompt || null,
        isCopilotOpen: Boolean(prompt),
      });
      if (typeof window !== "undefined") {
        window.scrollTo({ top: 0, behavior: "instant" });
      }
    }, 700);
  },

  returnToLanding: () => {
    set({ isTransitioning: true });
    setTimeout(() => {
      set({ currentView: "landing", isTransitioning: false });
      if (typeof window !== "undefined") {
        window.scrollTo({ top: 0, behavior: "instant" });
      }
    }, 500);
  },

  setActiveProduct: (productId: string) => {
    set({ activeProductId: productId, selectedAspect: null, discrepancyOnly: false });
  },

  addProduct: (product: ProductDataset) => {
    set((state) => ({
      products: {
        ...state.products,
        [product.id]: product,
      },
      activeProductId: product.id,
    }));
  },

  addReviewsToProduct: (productId: string, newReviews: ReviewRecord[]) => {
    const currentProducts = get().products;
    const target = currentProducts[productId] || currentProducts["prod-sony-xm5"];
    if (!target) return;

    const updated = recalculateProductDataset(target, newReviews);
    set({
      products: {
        ...currentProducts,
        [productId]: updated,
      },
    });
  },

  toggleCopilot: (open, prompt) =>
    set((state) => ({
      isCopilotOpen: open !== undefined ? open : !state.isCopilotOpen,
      copilotInitialPrompt: prompt || state.copilotInitialPrompt,
    })),

  setSelectedAspect: (aspect) => set({ selectedAspect: aspect }),
  setDiscrepancyOnly: (val) => set({ discrepancyOnly: val }),
  setHighlightedCitationId: (id) => set({ highlightedCitationId: id }),

  openIngestModal: () => set({ isIngestModalOpen: true }),
  closeIngestModal: () => set({ isIngestModalOpen: false }),
}));
