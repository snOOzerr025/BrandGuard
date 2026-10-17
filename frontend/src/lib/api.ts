// Type Definitions as per BrandGuard Master Architecture
export interface AspectSentiment {
  aspect: string;
  positive: number;
  neutral: number;
  negative: number;
  looImpact: number; // Leave-one-out star impact (e.g., -0.42)
}

export interface ReviewRecord {
  id: string;
  rating: number;
  title: string;
  reviewText: string;
  reviewDate: string;
  aspect: string;
  hasDiscrepancy: boolean;
  verifiedPurchase: boolean;
  highlightSpans: { text: string; sentiment: "positive" | "negative" }[];
}

export interface AnomalyPoint {
  date: string;
  sentiment: number;
  upperBound: number; // +3 sigma
  lowerBound: number; // -3 sigma
  isBreach: boolean;
  triggerReason?: string;
  zScore?: number;
}

export interface CopilotResponse {
  answer: string;
  intent: "SQL_AGGREGATE" | "PURE_VECTOR" | "HYBRID";
  sqlMetrics?: { label: string; value: string }[];
  citations: { id: string; snippet: string; rating: number; date: string }[];
}

export interface ProductDataset {
  id: string;
  name: string;
  brand: string;
  category: string;
  kpis: {
    brandHealthScore: number;
    brandHealthDelta: number;
    netSentiment: number;
    netSentimentDelta: number;
    topDragAspect: string;
    topDragImpact: number;
    activeAnomaliesCount: number;
  };
  aspects: AspectSentiment[];
  timeline: AnomalyPoint[];
  reviews: ReviewRecord[];
  copilotPresets: Record<string, CopilotResponse>;
}

export const MOCK_DATASETS: Record<string, ProductDataset> = {
  "prod-sony-xm5": {
    id: "prod-sony-xm5",
    name: "WH-1000XM5 Noise-Canceling Headphones",
    brand: "Sony",
    category: "Consumer Audio",
    kpis: {
      brandHealthScore: 84.2,
      brandHealthDelta: 2.4,
      netSentiment: 28.4,
      netSentimentDelta: -3.8,
      topDragAspect: "Build Quality",
      topDragImpact: -0.42,
      activeAnomaliesCount: 2,
    },
    aspects: [
      { aspect: "Quality", positive: 78, neutral: 12, negative: 10, looImpact: 0.34 },
      { aspect: "Battery", positive: 74, neutral: 17, negative: 9, looImpact: 0.28 },
      { aspect: "Performance", positive: 68, neutral: 18, negative: 14, looImpact: 0.22 },
      { aspect: "Design", positive: 65, neutral: 20, negative: 15, looImpact: 0.16 },
      { aspect: "Price", positive: 49, neutral: 26, negative: 25, looImpact: -0.14 },
      { aspect: "Delivery", positive: 58, neutral: 22, negative: 20, looImpact: -0.12 },
      { aspect: "Packaging", positive: 62, neutral: 25, negative: 13, looImpact: 0.08 },
      { aspect: "Service", positive: 28, neutral: 19, negative: 53, looImpact: -0.42 },
    ],
    timeline: [
      { date: "Sep 18", sentiment: 0.82, upperBound: 0.88, lowerBound: 0.28, isBreach: false },
      { date: "Sep 22", sentiment: 0.80, upperBound: 0.88, lowerBound: 0.28, isBreach: false },
      { date: "Sep 26", sentiment: 0.76, upperBound: 0.88, lowerBound: 0.28, isBreach: false },
      { date: "Sep 30", sentiment: 0.74, upperBound: 0.88, lowerBound: 0.28, isBreach: false },
      { date: "Oct 04", sentiment: 0.68, upperBound: 0.88, lowerBound: 0.28, isBreach: false },
      { date: "Oct 08", sentiment: 0.22, upperBound: 0.88, lowerBound: 0.28, isBreach: true, triggerReason: "Right hinge friction seam fatigue failure reported in batch #402", zScore: -3.24 },
      { date: "Oct 12", sentiment: 0.18, upperBound: 0.88, lowerBound: 0.28, isBreach: true, triggerReason: "Customer service classified hinge shear fractures as customer abuse", zScore: -3.85 },
      { date: "Oct 16", sentiment: 0.26, upperBound: 0.88, lowerBound: 0.28, isBreach: true, triggerReason: "Firmware v2.0.2 Bluetooth stuttering reported on iOS 18", zScore: -3.02 },
    ],
    reviews: [
      {
        id: "rev-sny-01",
        rating: 5,
        title: "Spectacular noise cancelling and marathon battery life",
        reviewText: "The active noise cancellation completely silences turbine roar on long haul transpacific flights. Battery life consistently hit 31 hours with LDAC on.",
        reviewDate: "2026-10-14",
        aspect: "Quality",
        hasDiscrepancy: false,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "completely silences turbine roar", sentiment: "positive" },
          { text: "consistently hit 31 hours with LDAC on", sentiment: "positive" },
        ],
      },
      {
        id: "rev-sny-02",
        rating: 2,
        title: "Bluetooth audio stuttering in congested subway stations",
        reviewText: "Love the ergonomics, but firmware update 2.0.2 introduced sporadic audio stuttering when commuting through busy subway platforms.",
        reviewDate: "2026-10-12",
        aspect: "Performance",
        hasDiscrepancy: false,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "sporadic audio stuttering when commuting", sentiment: "negative" },
        ],
      },
      {
        id: "rev-sny-03",
        rating: 1,
        title: "Hinge arm snapped after three months of desk use",
        reviewText: "I treated these headphones with extreme care inside the hard case. Last Tuesday the right swivel hinge snapped at the friction seam while putting them on my head. Unacceptable structural plastic for a $399 product.",
        reviewDate: "2026-10-11",
        aspect: "Service",
        hasDiscrepancy: false,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "right swivel hinge snapped at the friction seam", sentiment: "negative" },
          { text: "Unacceptable structural plastic for a $399 product", sentiment: "negative" },
        ],
      },
      {
        id: "rev-sny-04",
        rating: 1,
        title: "Authorized support rejected warranty claim as abuse",
        reviewText: "When the hinge cracked on week 14, authorized Sony support classified it as physical damage and demanded $185 plus shipping. Multiple forum threads confirm this exact stress failure point.",
        reviewDate: "2026-10-09",
        aspect: "Service",
        hasDiscrepancy: false,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "classified it as physical damage and demanded $185", sentiment: "negative" },
        ],
      },
      {
        id: "rev-sny-05",
        rating: 5,
        title: "5 star rating given but hinge already loose",
        reviewText: "ANC is truly top tier. However, the plastic swivel joint is wobbling and feels very fragile, which is dangerous. I am terrified it will break soon.",
        reviewDate: "2026-10-08",
        aspect: "Quality",
        hasDiscrepancy: true, // 5 stars with severe structural warning
        verifiedPurchase: true,
        highlightSpans: [
          { text: "ANC is truly top tier", sentiment: "positive" },
          { text: "plastic swivel joint is wobbling and feels very fragile", sentiment: "negative" },
        ],
      },
      {
        id: "rev-sny-06",
        rating: 5,
        title: "Crystal clear conference audio and instant multipoint pairing",
        reviewText: "Multipoint switching between MacBook and iPhone is instantaneous. Callers reported zero background street noise even during windy downtown strolls.",
        reviewDate: "2026-10-06",
        aspect: "Performance",
        hasDiscrepancy: false,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "Multipoint switching between MacBook and iPhone is instantaneous", sentiment: "positive" },
          { text: "zero background street noise", sentiment: "positive" },
        ],
      },
    ],
    copilotPresets: {
      "Why is Service & Build Quality dragging down overall rating?": {
        answer: "Deterministic SQL metrics indicate that Service (-0.42★ impact) and Build Quality are responsible for the severe 3σ control breach on Oct 08. HDBSCAN theme decomposition isolates 142 reviews citing hairline fractures along the right swivel friction seam [ref:rev-sny-03]. Compounding this, authorized warranty claims were systematically rejected as customer physical damage [ref:rev-sny-04].",
        intent: "HYBRID",
        sqlMetrics: [
          { label: "Star Drag Impact", value: "-0.42★" },
          { label: "Negative Mentions", value: "53.2%" },
          { label: "Z-Score Drift", value: "-3.85σ" },
        ],
        citations: [
          { id: "rev-sny-03", snippet: "Right swivel hinge snapped at the friction seam while putting them on my head...", rating: 1, date: "2026-10-11" },
          { id: "rev-sny-04", snippet: "Authorized Sony support classified it as physical damage and demanded $185 plus shipping...", rating: 1, date: "2026-10-09" },
        ],
      },
      "Explain the battery overheating anomaly on Oct 14": {
        answer: "Reciprocal Rank Fusion across pgvector and tsvector isolates customer feedback reporting heat accumulation during fast charging when using third-party 65W USB-PD bricks. Battery runtime remains stellar at 31 hours [ref:rev-sny-01], but thermal throttling activates after 25 minutes of continuous high-wattage charging.",
        intent: "PURE_VECTOR",
        sqlMetrics: [
          { label: "Aspect Affected", value: "Battery" },
          { label: "NSS Impact", value: "+28.4 pts" },
        ],
        citations: [
          { id: "rev-sny-01", snippet: "Battery life consistently hit 31 hours with LDAC on. Easily the best in class...", rating: 5, date: "2026-10-14" },
        ],
      },
    },
  },
};
