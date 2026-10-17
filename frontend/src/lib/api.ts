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

  "prod-apple-iphone15pro": {
    id: "prod-apple-iphone15pro",
    name: "iPhone 15 Pro Max (Titanium Natural)",
    brand: "Apple",
    category: "Smartphones & Mobile",
    kpis: {
      brandHealthScore: 91.8,
      brandHealthDelta: 4.1,
      netSentiment: 64.5,
      netSentimentDelta: 5.2,
      topDragAspect: "Thermal Throttling",
      topDragImpact: -0.28,
      activeAnomaliesCount: 1,
    },
    aspects: [
      { aspect: "Quality", positive: 92, neutral: 5, negative: 3, looImpact: 0.45 },
      { aspect: "Performance", positive: 88, neutral: 7, negative: 5, looImpact: 0.40 },
      { aspect: "Design", positive: 86, neutral: 9, negative: 5, looImpact: 0.32 },
      { aspect: "Battery", positive: 79, neutral: 12, negative: 9, looImpact: 0.24 },
      { aspect: "Packaging", positive: 82, neutral: 14, negative: 4, looImpact: 0.12 },
      { aspect: "Service", positive: 74, neutral: 16, negative: 10, looImpact: 0.08 },
      { aspect: "Price", positive: 38, neutral: 28, negative: 34, looImpact: -0.22 },
      { aspect: "Delivery", positive: 65, neutral: 22, negative: 13, looImpact: -0.15 },
    ],
    timeline: [
      { date: "Sep 20", sentiment: 0.88, upperBound: 0.92, lowerBound: 0.45, isBreach: false },
      { date: "Sep 25", sentiment: 0.84, upperBound: 0.92, lowerBound: 0.45, isBreach: false },
      { date: "Sep 30", sentiment: 0.42, upperBound: 0.92, lowerBound: 0.45, isBreach: true, triggerReason: "A17 Pro thermal throttling & rear glass surface temp reaches 47°C during 4K ProRes capture", zScore: -3.12 },
      { date: "Oct 05", sentiment: 0.65, upperBound: 0.92, lowerBound: 0.45, isBreach: false },
      { date: "Oct 10", sentiment: 0.82, upperBound: 0.92, lowerBound: 0.45, isBreach: false, triggerReason: "iOS 17.0.3 thermal optimization update mitigated peak heat dissipation by 4.2°C" },
      { date: "Oct 15", sentiment: 0.89, upperBound: 0.92, lowerBound: 0.45, isBreach: false },
    ],
    reviews: [
      {
        id: "rev-apl-01",
        rating: 5,
        title: "5x Tetraprism telephoto camera is unmatched for concerts",
        reviewText: "The 120mm focal length optical zoom produces incredibly sharp portraits in low light. Titanium grade 5 frame makes this noticeably lighter in hand than the 14 Pro Max.",
        reviewDate: "2026-10-15",
        aspect: "Quality",
        hasDiscrepancy: false,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "incredibly sharp portraits in low light", sentiment: "positive" },
          { text: "Titanium grade 5 frame makes this noticeably lighter", sentiment: "positive" },
        ],
      },
      {
        id: "rev-apl-02",
        rating: 2,
        title: "Phone becomes uncomfortably hot during fast charge and CarPlay",
        reviewText: "Whenever I run Apple Maps on wireless CarPlay while fast charging with a 30W brick, the phone stops charging due to high temperature and screen dims.",
        reviewDate: "2026-10-12",
        aspect: "Performance",
        hasDiscrepancy: false,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "stops charging due to high temperature and screen dims", sentiment: "negative" },
        ],
      },
      {
        id: "rev-apl-03",
        rating: 5,
        title: "Phenomenal device but rear frosted glass scratches too easily",
        reviewText: "Blazing fast A17 Pro chip and USB-C at 10Gbps is a game changer for photographers. Yet the natural titanium bezel showed hairline scuffs after just one pocket slip.",
        reviewDate: "2026-10-10",
        aspect: "Design",
        hasDiscrepancy: true,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "Blazing fast A17 Pro chip and USB-C at 10Gbps is a game changer", sentiment: "positive" },
          { text: "natural titanium bezel showed hairline scuffs", sentiment: "negative" },
        ],
      },
    ],
    copilotPresets: {
      "What triggered the thermal anomaly on Sep 30?": {
        answer: "Hardware telemetry and user review synthesis isolate an unconstrained background thread in Instagram v302 together with A17 Pro high-frequency burst states during simultaneous 4K 60fps ProRes recording and USB-PD charging. iOS 17.0.3 successfully normalized temperature limits without degrading synthetic Geekbench compute scores.",
        intent: "HYBRID",
        sqlMetrics: [
          { label: "Peak Temp Reported", value: "47.3°C" },
          { label: "Z-Score Drop", value: "-3.12σ" },
          { label: "Resolution SLA", value: "6 Days" },
        ],
        citations: [
          { id: "rev-apl-02", snippet: "Whenever I run Apple Maps on wireless CarPlay while fast charging with a 30W brick...", rating: 2, date: "2026-10-12" },
        ],
      },
    },
  },

  "prod-samsung-s24ultra": {
    id: "prod-samsung-s24ultra",
    name: "Galaxy S24 Ultra (Titanium Gray)",
    brand: "Samsung",
    category: "Smartphones & Mobile",
    kpis: {
      brandHealthScore: 89.4,
      brandHealthDelta: 1.8,
      netSentiment: 58.2,
      netSentimentDelta: 3.4,
      topDragAspect: "Display Mura & Grain",
      topDragImpact: -0.31,
      activeAnomaliesCount: 1,
    },
    aspects: [
      { aspect: "Performance", positive: 91, neutral: 6, negative: 3, looImpact: 0.42 },
      { aspect: "Quality", positive: 85, neutral: 8, negative: 7, looImpact: 0.36 },
      { aspect: "Battery", positive: 84, neutral: 10, negative: 6, looImpact: 0.30 },
      { aspect: "Design", positive: 81, neutral: 12, negative: 7, looImpact: 0.22 },
      { aspect: "Packaging", positive: 76, neutral: 18, negative: 6, looImpact: 0.10 },
      { aspect: "Delivery", positive: 68, neutral: 20, negative: 12, looImpact: -0.06 },
      { aspect: "Service", positive: 54, neutral: 22, negative: 24, looImpact: -0.18 },
      { aspect: "Price", positive: 42, neutral: 26, negative: 32, looImpact: -0.26 },
    ],
    timeline: [
      { date: "Feb 01", sentiment: 0.85, upperBound: 0.90, lowerBound: 0.40, isBreach: false },
      { date: "Feb 08", sentiment: 0.83, upperBound: 0.90, lowerBound: 0.40, isBreach: false },
      { date: "Feb 15", sentiment: 0.38, upperBound: 0.90, lowerBound: 0.40, isBreach: true, triggerReason: "Corning Gorilla Armor anti-reflective coating praised, but low-brightness subpixel grain (mura effect) reported in Reddit r/GalaxyS24", zScore: -3.15 },
      { date: "Feb 22", sentiment: 0.62, upperBound: 0.90, lowerBound: 0.40, isBreach: false },
      { date: "Mar 01", sentiment: 0.78, upperBound: 0.90, lowerBound: 0.40, isBreach: false },
    ],
    reviews: [
      {
        id: "rev-sam-01",
        rating: 5,
        title: "Gorilla Armor anti-reflective glass is pure magic under direct sun",
        reviewText: "I can sit by the pool at noon and read without straining my eyes. The flat screen also makes writing with the S-Pen so much better than previous curved edges.",
        reviewDate: "2026-03-01",
        aspect: "Design",
        hasDiscrepancy: false,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "read without straining my eyes under direct sun", sentiment: "positive" },
          { text: "flat screen makes writing with S-Pen so much better", sentiment: "positive" },
        ],
      },
      {
        id: "rev-sam-02",
        rating: 2,
        title: "Grainy display at low brightness in dark rooms",
        reviewText: "In pitch black with brightness below 15%, solid dark grey colors appear like denim fabric texture. Several users on forums have the exact same hardware panel issue.",
        reviewDate: "2026-02-16",
        aspect: "Quality",
        hasDiscrepancy: false,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "solid dark grey colors appear like denim fabric texture", sentiment: "negative" },
        ],
      },
    ],
    copilotPresets: {
      "What is the source of the display mura defect?": {
        answer: "Spectral variance and user image telemetry correlate the grain complaints to M13 OLED organic material subpixel driving variance under 120Hz refresh rates at sub-10 nit pulse-width modulation (PWM) levels. Subsequent batch revisions showed 78% reduction in mura perception.",
        intent: "HYBRID",
        sqlMetrics: [
          { label: "Subpixel Defect Rate", value: "3.4%" },
          { label: "Affected Brightness", value: "<15%" },
          { label: "Community Signal", value: "High (Reddit/XDA)" },
        ],
        citations: [
          { id: "rev-sam-02", snippet: "In pitch black with brightness below 15%, solid dark grey colors appear like denim fabric...", rating: 2, date: "2026-02-16" },
        ],
      },
    },
  },

  "prod-bose-qcultra": {
    id: "prod-bose-qcultra",
    name: "QuietComfort Ultra Earbuds",
    brand: "Bose",
    category: "Consumer Audio",
    kpis: {
      brandHealthScore: 86.7,
      brandHealthDelta: 2.9,
      netSentiment: 52.0,
      netSentimentDelta: 1.6,
      topDragAspect: "Connection Stability & Wind Noise",
      topDragImpact: -0.34,
      activeAnomaliesCount: 1,
    },
    aspects: [
      { aspect: "Quality", positive: 88, neutral: 6, negative: 6, looImpact: 0.44 },
      { aspect: "Design", positive: 83, neutral: 11, negative: 6, looImpact: 0.31 },
      { aspect: "Battery", positive: 72, neutral: 16, negative: 12, looImpact: 0.20 },
      { aspect: "Packaging", positive: 78, neutral: 15, negative: 7, looImpact: 0.11 },
      { aspect: "Performance", positive: 65, neutral: 15, negative: 20, looImpact: -0.18 },
      { aspect: "Service", positive: 60, neutral: 21, negative: 19, looImpact: -0.14 },
      { aspect: "Delivery", positive: 70, neutral: 18, negative: 12, looImpact: -0.08 },
      { aspect: "Price", positive: 45, neutral: 25, negative: 30, looImpact: -0.25 },
    ],
    timeline: [
      { date: "Jan 10", sentiment: 0.81, upperBound: 0.89, lowerBound: 0.35, isBreach: false },
      { date: "Jan 18", sentiment: 0.79, upperBound: 0.89, lowerBound: 0.35, isBreach: false },
      { date: "Jan 25", sentiment: 0.28, upperBound: 0.89, lowerBound: 0.35, isBreach: true, triggerReason: "Left earbud mosquito hum / high pitched feedback when cycling in windy conditions", zScore: -3.42 },
      { date: "Feb 02", sentiment: 0.68, upperBound: 0.89, lowerBound: 0.35, isBreach: false },
    ],
    reviews: [
      {
        id: "rev-bse-01",
        rating: 5,
        title: "Immersive Audio makes studio recordings feel like live acoustics",
        reviewText: "The spatial audio head tracking is eerie in its accuracy. ANC wipes out the screeching metal rails of the NYC subway with zero ear pressure.",
        reviewDate: "2026-02-01",
        aspect: "Quality",
        hasDiscrepancy: false,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "spatial audio head tracking is eerie in its accuracy", sentiment: "positive" },
          { text: "wipes out screeching metal rails with zero ear pressure", sentiment: "positive" },
        ],
      },
      {
        id: "rev-bse-02",
        rating: 2,
        title: "Annoying buzzing sound in left earbud during calls",
        reviewText: "Every time a phone call connects, there is a faint mechanical buzzing in the left bud that never goes away until I put it back in the case to restart.",
        reviewDate: "2026-01-26",
        aspect: "Performance",
        hasDiscrepancy: false,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "faint mechanical buzzing in left bud that never goes away", sentiment: "negative" },
        ],
      },
    ],
    copilotPresets: {
      "Why are users complaining about left earbud acoustic buzz?": {
        answer: "Acoustic feedback analysis identifies an overcompensated microphone gain calibration in firmware 1.3.1 when switching from Immersive Audio DSP mode to Wideband Telephony mode.",
        intent: "PURE_VECTOR",
        sqlMetrics: [
          { label: "Bug Recurrence", value: "18.2%" },
          { label: "Firmware Target", value: "v1.3.1" },
        ],
        citations: [
          { id: "rev-bse-02", snippet: "faint mechanical buzzing in the left bud that never goes away...", rating: 2, date: "2026-01-26" },
        ],
      },
    },
  },

  "prod-dyson-airwrap": {
    id: "prod-dyson-airwrap",
    name: "Airwrap Multi-Styler Complete Long",
    brand: "Dyson",
    category: "Personal Tech & Care",
    kpis: {
      brandHealthScore: 88.0,
      brandHealthDelta: 3.2,
      netSentiment: 61.5,
      netSentimentDelta: 4.0,
      topDragAspect: "Learning Curve & Barrel Attachment",
      topDragImpact: -0.32,
      activeAnomaliesCount: 0,
    },
    aspects: [
      { aspect: "Design", positive: 94, neutral: 4, negative: 2, looImpact: 0.48 },
      { aspect: "Quality", positive: 91, neutral: 6, negative: 3, looImpact: 0.42 },
      { aspect: "Performance", positive: 86, neutral: 8, negative: 6, looImpact: 0.35 },
      { aspect: "Packaging", positive: 88, neutral: 9, negative: 3, looImpact: 0.22 },
      { aspect: "Delivery", positive: 74, neutral: 18, negative: 8, looImpact: 0.05 },
      { aspect: "Service", positive: 65, neutral: 20, negative: 15, looImpact: -0.12 },
      { aspect: "Price", positive: 36, neutral: 24, negative: 40, looImpact: -0.35 },
      { aspect: "Battery", positive: 50, neutral: 35, negative: 15, looImpact: -0.10 },
    ],
    timeline: [
      { date: "May 01", sentiment: 0.88, upperBound: 0.94, lowerBound: 0.50, isBreach: false },
      { date: "May 10", sentiment: 0.85, upperBound: 0.94, lowerBound: 0.50, isBreach: false },
      { date: "May 20", sentiment: 0.82, upperBound: 0.94, lowerBound: 0.50, isBreach: false },
      { date: "May 30", sentiment: 0.89, upperBound: 0.94, lowerBound: 0.50, isBreach: false },
    ],
    reviews: [
      {
        id: "rev-dys-01",
        rating: 5,
        title: "Salon quality blowout with zero heat damage",
        reviewText: "The Coanda aerodynamic airflow naturally wraps hair around the barrel without singeing or burning split ends. Hair stays glossy and bouncy all day.",
        reviewDate: "2026-05-28",
        aspect: "Quality",
        hasDiscrepancy: false,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "naturally wraps hair without singeing or burning split ends", sentiment: "positive" },
          { text: "stays glossy and bouncy all day", sentiment: "positive" },
        ],
      },
      {
        id: "rev-dys-02",
        rating: 3,
        title: "Steep learning curve and heavy for small hands",
        reviewText: "Takes at least 3 weeks of practice to get curls to hold properly. At nearly 600 dollars, wish the storage case wasn't so ridiculously massive.",
        reviewDate: "2026-05-18",
        aspect: "Design",
        hasDiscrepancy: false,
        verifiedPurchase: true,
        highlightSpans: [
          { text: "Takes at least 3 weeks of practice to get curls to hold", sentiment: "negative" },
          { text: "storage case wasn't so ridiculously massive", sentiment: "negative" },
        ],
      },
    ],
    copilotPresets: {
      "What drives high customer satisfaction for Dyson Airwrap?": {
        answer: "Coanda airflow technology and thermal sensor regulation (never exceeding 150°C) achieve 94% positive sentiment in hair protection and styling shine, offsetting the high price perception.",
        intent: "PURE_VECTOR",
        sqlMetrics: [
          { label: "Heat Protection Positivity", value: "94.2%" },
          { label: "Style Longevity", value: "88.6%" },
        ],
        citations: [
          { id: "rev-dys-01", snippet: "naturally wraps hair around the barrel without singeing or burning split ends...", rating: 5, date: "2026-05-28" },
        ],
      },
    },
  },
};

// Helper function to synthesize / recalculate dataset when reviews are added
export function recalculateProductDataset(
  dataset: ProductDataset,
  newReviews: ReviewRecord[]
): ProductDataset {
  const combinedReviews = [...newReviews, ...dataset.reviews];
  
  // Calculate average rating and sentiment
  const totalReviews = combinedReviews.length;
  const avgRating = combinedReviews.reduce((sum, r) => sum + r.rating, 0) / (totalReviews || 1);
  
  const positiveReviews = combinedReviews.filter((r) => r.rating >= 4).length;
  const negativeReviews = combinedReviews.filter((r) => r.rating <= 2).length;
  const neutralReviews = totalReviews - positiveReviews - negativeReviews;

  // Net Sentiment = % Positive - % Negative
  const netSentiment = totalReviews > 0 
    ? Math.round(((positiveReviews - negativeReviews) / totalReviews) * 100 * 10) / 10 
    : dataset.kpis.netSentiment;

  // Brand Health Score (0-100) derived from rating, net sentiment & discrepancy
  const discrepancyCount = combinedReviews.filter((r) => r.hasDiscrepancy).length;
  const discPenalty = (discrepancyCount / totalReviews) * 20;
  const brandHealthScore = Math.max(
    10,
    Math.min(99.5, Math.round(((avgRating / 5) * 60 + ((netSentiment + 100) / 200) * 40 - discPenalty) * 10) / 10)
  );

  // Re-aggregate aspects
  const aspectCounts: Record<string, { pos: number; neu: number; neg: number }> = {};
  for (const r of combinedReviews) {
    const asp = r.aspect || "Quality";
    if (!aspectCounts[asp]) {
      aspectCounts[asp] = { pos: 0, neu: 0, neg: 0 };
    }
    if (r.rating >= 4) aspectCounts[asp].pos += 1;
    else if (r.rating <= 2) aspectCounts[asp].neg += 1;
    else aspectCounts[asp].neu += 1;
  }

  const updatedAspects: AspectSentiment[] = dataset.aspects.map((original) => {
    const counts = aspectCounts[original.aspect];
    if (!counts) return original;
    const aspTotal = counts.pos + counts.neu + counts.neg;
    if (aspTotal === 0) return original;
    const posPct = Math.round((counts.pos / aspTotal) * 100);
    const negPct = Math.round((counts.neg / aspTotal) * 100);
    const neuPct = 100 - posPct - negPct;
    return {
      ...original,
      positive: posPct,
      neutral: neuPct,
      negative: negPct,
    };
  });

  return {
    ...dataset,
    kpis: {
      ...dataset.kpis,
      brandHealthScore,
      netSentiment,
    },
    aspects: updatedAspects,
    reviews: combinedReviews,
  };
}
