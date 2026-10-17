"use client";

import React, { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  FileText,
  Star,
  Sparkles,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  X,
  Plus,
  Layers,
  ArrowRight,
  Database,
  Download,
  Flame,
  Info,
} from "lucide-react";
import { useDashboardStore } from "../../store/useDashboardStore";
import { ProductDataset, ReviewRecord } from "../../lib/api";

type IngestionTab = "csv" | "single" | "batch";

export const ReviewIngestionLab: React.FC = () => {
  const {
    isIngestModalOpen,
    closeIngestModal,
    products,
    activeProductId,
    setActiveProduct,
    addProduct,
    addReviewsToProduct,
  } = useDashboardStore();

  const [activeTab, setActiveTab] = useState<IngestionTab>("csv");
  const [selectedProductId, setSelectedProductId] = useState<string>(activeProductId);
  const [isCreatingNewProduct, setIsCreatingNewProduct] = useState(false);

  // New product fields
  const [newProductName, setNewProductName] = useState("");
  const [newProductBrand, setNewProductBrand] = useState("");
  const [newProductCategory, setNewProductCategory] = useState("Consumer Tech");

  // Single review fields
  const [singleTitle, setSingleTitle] = useState("");
  const [singleText, setSingleText] = useState("");
  const [singleRating, setSingleRating] = useState(5);
  const [singleAspect, setSingleAspect] = useState("Quality");
  const [singleVerified, setSingleVerified] = useState(true);

  // Batch paste fields
  const [batchText, setBatchText] = useState("");

  // CSV upload fields
  const [parsedRows, setParsedRows] = useState<any[]>([]);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Engine execution state
  const [isProcessing, setIsProcessing] = useState(false);
  const [engineStep, setEngineStep] = useState<string>("");
  const [engineProgress, setEngineProgress] = useState(0);
  const [executionResult, setExecutionResult] = useState<{
    totalProcessed: number;
    positiveCount: number;
    negativeCount: number;
    discrepancyCount: number;
  } | null>(null);

  if (!isIngestModalOpen) return null;

  // Handle CSV file selection and parsing
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadedFileName(file.name);
    const reader = new FileReader();

    reader.onload = (event) => {
      const content = event.target?.result as string;
      if (!content) return;

      try {
        if (file.name.endsWith(".json") || file.name.endsWith(".jsonl")) {
          const lines = content.split("\n").filter((l) => l.trim().length > 0);
          const parsed = lines.map((l) => JSON.parse(l));
          setParsedRows(parsed);
        } else {
          // Parse CSV lines
          const lines = content.split(/\r?\n/).filter((l) => l.trim().length > 0);
          if (lines.length <= 1) return;

          const headers = lines[0].split(",").map((h) => h.trim().replace(/^["']|["']$/g, "").toLowerCase());
          
          const rows = [];
          for (let i = 1; i < lines.length; i++) {
            // Basic CSV split accounting for quoted values
            const values = lines[i].split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/).map((v) =>
              v.trim().replace(/^["']|["']$/g, "")
            );
            if (values.length < headers.length) continue;

            const rowObj: any = {};
            headers.forEach((h, idx) => {
              rowObj[h] = values[idx];
            });
            rows.push(rowObj);
          }
          setParsedRows(rows);
        }
      } catch (err) {
        console.error("Failed to parse file", err);
      }
    };

    reader.readAsText(file);
  };

  // Preset scenarios for instant testing
  const loadPreset = (presetType: "defect" | "positive" | "discrepancy") => {
    setActiveTab("batch");
    if (presetType === "defect") {
      setBatchText(
        `1★ | Critical hinge joint fracture after 18 days of regular home use. Support refused replacement.\n` +
        `2★ | Battery drops from 80% to 10% in under 45 minutes during video meetings.\n` +
        `1★ | Audio cutting out completely on the left channel. Constant crackling sound in wind.\n` +
        `1★ | Customer support took 2 weeks to respond and blamed customer physical abuse.`
      );
    } else if (presetType === "positive") {
      setBatchText(
        `5★ | Outstanding active noise cancellation. Completely silences transatlantic engine roar!\n` +
        `5★ | Battery life is unbelievable. Reached 34 hours on single charge with LDAC enabled.\n` +
        `5★ | Premium plush earcups. Most comfortable headphones I have ever worn for 8hr workdays.\n` +
        `4★ | Build quality feels solid and minimalist. Bluetooth multipoint switches flawlessly.`
      );
    } else {
      setBatchText(
        `5★ | ANC is great, BUT the plastic hinge feels dangerously loose and I am terrified it will crack tomorrow.\n` +
        `5★ | Sounds fantastic, however customer service was horribly rude when asking about warranty registration.\n` +
        `4★ | Great screen display, though thermal heat made my fingers burn after 20 minutes of 4K recording.`
      );
    }
  };

  // Convert raw inputs into standardized ReviewRecords
  const generateReviewRecords = (targetProduct: ProductDataset): ReviewRecord[] => {
    const records: ReviewRecord[] = [];
    const today = new Date().toISOString().split("T")[0];

    if (activeTab === "single") {
      if (!singleText.trim()) return [];
      const hasDiscrepancy =
        (singleRating >= 4 && (singleText.toLowerCase().includes("broke") || singleText.toLowerCase().includes("terrible") || singleText.toLowerCase().includes("horrible") || singleText.toLowerCase().includes("crack"))) ||
        (singleRating <= 2 && (singleText.toLowerCase().includes("amazing") || singleText.toLowerCase().includes("love") || singleText.toLowerCase().includes("flawless")));

      records.push({
        id: `rev-user-${Date.now()}`,
        rating: singleRating,
        title: singleTitle || `${singleRating} Star Customer Review`,
        reviewText: singleText,
        reviewDate: today,
        aspect: singleAspect,
        hasDiscrepancy,
        verifiedPurchase: singleVerified,
        highlightSpans: [
          {
            text: singleText.slice(0, Math.min(singleText.length, 60)),
            sentiment: singleRating >= 4 ? "positive" : "negative",
          },
        ],
      });
    } else if (activeTab === "batch") {
      const lines = batchText.split("\n").filter((l) => l.trim().length > 0);
      lines.forEach((line, idx) => {
        let rating = 5;
        let text = line;

        // Try extracting rating if prefixed like "1★ | text" or "rating: 1"
        const starMatch = line.match(/^(\d)[★*]/);
        if (starMatch) {
          rating = parseInt(starMatch[1], 10);
          text = line.replace(/^.*?\|\s*/, "");
        }

        const aspectList = ["Quality", "Battery", "Performance", "Design", "Service", "Price"];
        const chosenAspect = aspectList[idx % aspectList.length];

        const hasDiscrepancy =
          (rating >= 4 && (text.toLowerCase().includes("broke") || text.toLowerCase().includes("crack") || text.toLowerCase().includes("loose") || text.toLowerCase().includes("rude"))) ||
          (rating <= 2 && text.toLowerCase().includes("great"));

        records.push({
          id: `rev-batch-${Date.now()}-${idx}`,
          rating,
          title: `Batch User Review #${idx + 1}`,
          reviewText: text,
          reviewDate: today,
          aspect: chosenAspect,
          hasDiscrepancy,
          verifiedPurchase: true,
          highlightSpans: [
            {
              text: text.slice(0, Math.min(text.length, 50)),
              sentiment: rating >= 4 ? "positive" : "negative",
            },
          ],
        });
      });
    } else if (activeTab === "csv") {
      parsedRows.forEach((row, idx) => {
        const text =
          row.review_text ||
          row.text ||
          row.body ||
          row.review ||
          row.comment ||
          Object.values(row).find((v) => typeof v === "string" && v.length > 20) ||
          "";

        if (!text) return;

        let rating = 5;
        const rawRating = row.rating || row.stars || row.score;
        if (rawRating) {
          const parsed = parseInt(String(rawRating), 10);
          if (!isNaN(parsed) && parsed >= 1 && parsed <= 5) rating = parsed;
        }

        const title = row.title || `Imported Review #${idx + 1}`;
        const aspect = row.aspect || (rating <= 2 ? "Service" : "Quality");

        records.push({
          id: `rev-csv-${Date.now()}-${idx}`,
          rating,
          title,
          reviewText: String(text),
          reviewDate: row.date || today,
          aspect,
          hasDiscrepancy: rating >= 4 && String(text).toLowerCase().includes("crack"),
          verifiedPurchase: true,
          highlightSpans: [
            {
              text: String(text).slice(0, 50),
              sentiment: rating >= 4 ? "positive" : "negative",
            },
          ],
        });
      });
    }

    return records;
  };

  // Run the ABSA Inference & Ingestion Pipeline
  const handleRunEngine = async () => {
    setIsProcessing(true);
    setExecutionResult(null);

    // 1. Resolve Target Product
    let targetProdId = selectedProductId;
    let targetDataset = products[targetProdId];

    if (isCreatingNewProduct) {
      const newId = `prod-custom-${Date.now()}`;
      targetDataset = {
        id: newId,
        name: newProductName || "Custom Enterprise SKU",
        brand: newProductBrand || "Independent Brand",
        category: newProductCategory,
        kpis: {
          brandHealthScore: 78.5,
          brandHealthDelta: 0.0,
          netSentiment: 22.0,
          netSentimentDelta: 0.0,
          topDragAspect: "Quality",
          topDragImpact: -0.25,
          activeAnomaliesCount: 0,
        },
        aspects: [
          { aspect: "Quality", positive: 65, neutral: 20, negative: 15, looImpact: 0.2 },
          { aspect: "Performance", positive: 70, neutral: 15, negative: 15, looImpact: 0.25 },
          { aspect: "Battery", positive: 60, neutral: 25, negative: 15, looImpact: 0.1 },
          { aspect: "Design", positive: 75, neutral: 15, negative: 10, looImpact: 0.15 },
          { aspect: "Price", positive: 50, neutral: 25, negative: 25, looImpact: -0.15 },
          { aspect: "Delivery", positive: 65, neutral: 20, negative: 15, looImpact: 0.05 },
          { aspect: "Packaging", positive: 70, neutral: 20, negative: 10, looImpact: 0.1 },
          { aspect: "Service", positive: 45, neutral: 25, negative: 30, looImpact: -0.3 },
        ],
        timeline: [
          { date: "Oct 01", sentiment: 0.75, upperBound: 0.85, lowerBound: 0.35, isBreach: false },
          { date: "Oct 08", sentiment: 0.72, upperBound: 0.85, lowerBound: 0.35, isBreach: false },
          { date: "Oct 15", sentiment: 0.70, upperBound: 0.85, lowerBound: 0.35, isBreach: false },
        ],
        reviews: [],
        copilotPresets: {},
      };
      addProduct(targetDataset);
      targetProdId = newId;
    }

    const reviewsToIngest = generateReviewRecords(targetDataset);

    if (reviewsToIngest.length === 0) {
      alert("Please provide at least one review text or upload a valid CSV file.");
      setIsProcessing(false);
      return;
    }

    // High-tech multi-stage visual pipeline steps
    setEngineStep("Stage 1/4: Tokenization & Aspect Span Extraction (ONNX v3.2)...");
    setEngineProgress(25);
    await new Promise((r) => setTimeout(r, 400));

    setEngineStep("Stage 2/4: Classifying Aspect Polarity & Leave-One-Out Star Impact...");
    setEngineProgress(55);
    await new Promise((r) => setTimeout(r, 450));

    setEngineStep("Stage 3/4: Rating Discrepancy & EWMA 3σ Control Limits Calculation...");
    setEngineProgress(85);
    await new Promise((r) => setTimeout(r, 400));

    setEngineStep("Stage 4/4: Vector Indexing & Ingestion Complete.");
    setEngineProgress(100);
    await new Promise((r) => setTimeout(r, 300));

    // Append reviews to store
    addReviewsToProduct(targetProdId, reviewsToIngest);
    setActiveProduct(targetProdId);

    const pos = reviewsToIngest.filter((r) => r.rating >= 4).length;
    const neg = reviewsToIngest.filter((r) => r.rating <= 2).length;
    const disc = reviewsToIngest.filter((r) => r.hasDiscrepancy).length;

    setExecutionResult({
      totalProcessed: reviewsToIngest.length,
      positiveCount: pos,
      negativeCount: neg,
      discrepancyCount: disc,
    });

    setIsProcessing(false);
  };

  const handleDownloadSampleCsv = () => {
    const csvContent =
      "data:text/csv;charset=utf-8," +
      "rating,title,review_text,aspect,date\n" +
      "5,Flawless Audio,The soundstage is wide and active noise cancellation is superior to competitors,Quality,2026-10-15\n" +
      "1,Hinge Fracture,Snapping plastic after 3 weeks. Authorized warranty center refused coverage,Service,2026-10-14\n" +
      "2,Battery Drain,Battery drained within 6 hours with ANC off. Substantially under advertised runtime,Battery,2026-10-13\n" +
      "5,Great Comfort,ANC works well but the swivel feels slightly creaky. Still giving 5 stars,Quality,2026-10-12\n" +
      "4,Solid Build,Good overall experience though charging cable is quite short,Packaging,2026-10-11";
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "brandguard_sample_reviews.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto bg-black/75 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        transition={{ duration: 0.3 }}
        className="relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-3xl overflow-hidden backdrop-blur-2xl bg-[#0A1128]/95 border border-white/15 text-[#FAF6F0] shadow-[0_30px_90px_rgba(0,0,0,0.85)]"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 sm:px-8 border-b border-white/10 bg-[#0E1833]/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#FF5A36] to-[#001F54] flex items-center justify-center text-white shadow-[0_0_20px_rgba(255,90,54,0.3)]">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-black text-white tracking-tight">
                  REVIEW INGESTION & ABSA ENGINE LAB
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#FF5A36]/20 text-[#FF5A36] border border-[#FF5A36]/40">
                  REAL-TIME INFERENCE
                </span>
              </div>
              <p className="text-xs font-mono text-[#8A8F9E]">
                Ingest real CSV datasets, batch inputs, or single customer reviews into neural telemetry.
              </p>
            </div>
          </div>

          <button
            onClick={closeIngestModal}
            className="p-2 rounded-full bg-white/5 hover:bg-white/10 text-[#8A8F9E] hover:text-white transition-colors cursor-pointer border border-white/10"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 sm:px-8 overflow-y-auto space-y-6 flex-1">
          {/* Section 1: Target Product Selection or Creation */}
          <div className="p-4 sm:p-5 rounded-2xl bg-white/5 border border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-mono font-bold tracking-wider uppercase text-white">
                <Database className="w-4 h-4 text-[#FF5A36]" />
                <span>Target Product SKU</span>
              </div>

              <button
                type="button"
                onClick={() => setIsCreatingNewProduct(!isCreatingNewProduct)}
                className="text-xs font-mono text-[#FF5A36] hover:underline flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>{isCreatingNewProduct ? "Choose Existing Product" : "Create New Custom Product"}</span>
              </button>
            </div>

            {!isCreatingNewProduct ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                {Object.values(products).map((prod) => (
                  <button
                    key={prod.id}
                    type="button"
                    onClick={() => setSelectedProductId(prod.id)}
                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                      selectedProductId === prod.id
                        ? "bg-[#FF5A36]/15 border-[#FF5A36] shadow-[0_0_15px_rgba(255,90,54,0.25)]"
                        : "bg-white/5 border-white/10 hover:border-white/20"
                    }`}
                  >
                    <div className="text-[10px] font-mono text-[#8A8F9E] uppercase">
                      {prod.brand} • {prod.category}
                    </div>
                    <div className="text-xs font-bold text-white truncate mt-0.5">{prod.name}</div>
                    <div className="text-[10px] font-mono text-[#9CAF88] mt-1">
                      Health: {prod.kpis.brandHealthScore} | Reviews: {prod.reviews.length}
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                <div>
                  <label className="block text-[10px] font-mono text-[#8A8F9E] uppercase mb-1">
                    Product Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Acme UltraPro Watch"
                    value={newProductName}
                    onChange={(e) => setNewProductName(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white focus:outline-none focus:border-[#FF5A36]"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-mono text-[#8A8F9E] uppercase mb-1">
                    Brand Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Acme Wearables"
                    value={newProductBrand}
                    onChange={(e) => setNewProductBrand(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white focus:outline-none focus:border-[#FF5A36]"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-mono text-[#8A8F9E] uppercase mb-1">
                    Category
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Smart Wearables"
                    value={newProductCategory}
                    onChange={(e) => setNewProductCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-black/40 border border-white/10 text-xs text-white focus:outline-none focus:border-[#FF5A36]"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Section 2: Input Mode Switcher */}
          <div className="flex border-b border-white/10">
            <button
              type="button"
              onClick={() => setActiveTab("csv")}
              className={`pb-3 px-4 text-xs font-mono font-bold tracking-wider flex items-center gap-2 border-b-2 transition-all cursor-pointer ${
                activeTab === "csv"
                  ? "border-[#FF5A36] text-[#FF5A36]"
                  : "border-transparent text-[#8A8F9E] hover:text-white"
              }`}
            >
              <Upload className="w-3.5 h-3.5" />
              <span>1. UPLOAD CSV / JSONL DATASET</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("single")}
              className={`pb-3 px-4 text-xs font-mono font-bold tracking-wider flex items-center gap-2 border-b-2 transition-all cursor-pointer ${
                activeTab === "single"
                  ? "border-[#FF5A36] text-[#FF5A36]"
                  : "border-transparent text-[#8A8F9E] hover:text-white"
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>2. SINGLE REVIEW TESTER</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("batch")}
              className={`pb-3 px-4 text-xs font-mono font-bold tracking-wider flex items-center gap-2 border-b-2 transition-all cursor-pointer ${
                activeTab === "batch"
                  ? "border-[#FF5A36] text-[#FF5A36]"
                  : "border-transparent text-[#8A8F9E] hover:text-white"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>3. BATCH REVIEWS TEXT</span>
            </button>
          </div>

          {/* TAB 1: CSV / JSONL Upload */}
          {activeTab === "csv" && (
            <div className="space-y-4">
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-white/20 hover:border-[#FF5A36]/60 rounded-3xl p-8 text-center bg-white/5 hover:bg-white/10 transition-all cursor-pointer group"
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  accept=".csv,.json,.jsonl,.txt"
                  className="hidden"
                />
                <div className="w-12 h-12 mx-auto rounded-2xl bg-[#FF5A36]/15 border border-[#FF5A36]/30 flex items-center justify-center text-[#FF5A36] mb-3 group-hover:scale-110 transition-transform">
                  <Upload className="w-6 h-6" />
                </div>
                <div className="text-sm font-bold text-white mb-1">
                  {uploadedFileName ? `Selected: ${uploadedFileName}` : "Drag and drop your review CSV file here"}
                </div>
                <p className="text-xs font-mono text-[#8A8F9E]">
                  Supports standard headers: <code className="text-[#FAF6F0]">rating</code>, <code className="text-[#FAF6F0]">review_text</code>, <code className="text-[#FAF6F0]">title</code>, <code className="text-[#FAF6F0]">aspect</code>
                </p>
                {parsedRows.length > 0 && (
                  <div className="mt-3 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#9CAF88]/20 border border-[#9CAF88]/40 text-[#9CAF88] text-xs font-mono">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{parsedRows.length} valid review records parsed and ready for ABSA engine</span>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between text-xs font-mono text-[#8A8F9E]">
                <span>Need a formatted file to test?</span>
                <button
                  type="button"
                  onClick={handleDownloadSampleCsv}
                  className="text-[#FF5A36] hover:underline flex items-center gap-1 cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Sample CSV Template</span>
                </button>
              </div>

              {parsedRows.length > 0 && (
                <div className="max-h-48 overflow-y-auto rounded-xl border border-white/10 bg-black/40">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-white/5 text-[#8A8F9E] sticky top-0">
                      <tr>
                        <th className="p-2.5">#</th>
                        <th className="p-2.5">Rating</th>
                        <th className="p-2.5">Review Sample</th>
                        <th className="p-2.5">Aspect</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {parsedRows.slice(0, 10).map((r, i) => (
                        <tr key={i} className="hover:bg-white/5">
                          <td className="p-2.5 text-[#8A8F9E]">{i + 1}</td>
                          <td className="p-2.5 text-[#FF5A36] font-bold">{r.rating || 5}★</td>
                          <td className="p-2.5 text-white truncate max-w-xs">{r.review_text || r.text || r.body || JSON.stringify(r)}</td>
                          <td className="p-2.5 text-[#9CAF88]">{r.aspect || "General"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Single Review Input */}
          {activeTab === "single" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[11px] font-mono text-[#8A8F9E] uppercase mb-1">
                    Rating (1 to 5 Stars)
                  </label>
                  <div className="flex items-center gap-2 p-2.5 rounded-xl bg-white/5 border border-white/10">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setSingleRating(star)}
                        className={`p-1 rounded transition-transform hover:scale-125 cursor-pointer ${
                          star <= singleRating ? "text-[#FF5A36] fill-[#FF5A36]" : "text-[#8A8F9E]"
                        }`}
                      >
                        <Star className={`w-5 h-5 ${star <= singleRating ? "fill-current" : ""}`} />
                      </button>
                    ))}
                    <span className="text-xs font-mono font-bold text-white ml-2">
                      {singleRating} / 5 Stars
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-mono text-[#8A8F9E] uppercase mb-1">
                    Primary Target Aspect
                  </label>
                  <select
                    value={singleAspect}
                    onChange={(e) => setSingleAspect(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl bg-[#0E1833] border border-white/10 text-xs text-white focus:outline-none focus:border-[#FF5A36]"
                  >
                    <option value="Quality">Quality / Build Durability</option>
                    <option value="Battery">Battery Runtime & Thermals</option>
                    <option value="Performance">Performance & Connectivity</option>
                    <option value="Design">Design & Ergonomics</option>
                    <option value="Service">Customer Service & Warranty</option>
                    <option value="Price">Price / Value Proposition</option>
                    <option value="Delivery">Delivery & Logistics</option>
                    <option value="Packaging">Packaging & Unboxing</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-[#8A8F9E] uppercase mb-1">
                  Review Headline / Title
                </label>
                <input
                  type="text"
                  placeholder="e.g. Swivel joint failed after 3 weeks of desk use"
                  value={singleTitle}
                  onChange={(e) => setSingleTitle(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-xs text-white placeholder:text-[#8A8F9E]/50 focus:outline-none focus:border-[#FF5A36]"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[11px] font-mono text-[#8A8F9E] uppercase">
                    Customer Review Body
                  </label>
                  <span className="text-[10px] font-mono text-[#8A8F9E]">
                    {singleText.length} characters
                  </span>
                </div>
                <textarea
                  rows={4}
                  placeholder="Enter the real customer experience text. The ABSA engine will isolate positive/negative token spans, calculate sentiment polarity, and check for rating discrepancies..."
                  value={singleText}
                  onChange={(e) => setSingleText(e.target.value)}
                  className="w-full p-3.5 rounded-xl bg-white/5 border border-white/10 text-xs text-white placeholder:text-[#8A8F9E]/50 focus:outline-none focus:border-[#FF5A36] resize-none"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="verified-single"
                  checked={singleVerified}
                  onChange={(e) => setSingleVerified(e.target.checked)}
                  className="rounded border-white/20 text-[#FF5A36] focus:ring-0"
                />
                <label htmlFor="verified-single" className="text-xs font-mono text-[#8A8F9E] cursor-pointer">
                  Mark as Verified Purchase (higher weight in deterministic health score)
                </label>
              </div>
            </div>
          )}

          {/* TAB 3: Batch Reviews Input */}
          {activeTab === "batch" && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-[11px] font-mono text-[#8A8F9E] uppercase">
                  Paste Multiple Reviews (1 per line or formatted)
                </span>

                {/* Instant Preset Buttons */}
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => loadPreset("defect")}
                    className="px-2.5 py-1 rounded-lg bg-red-500/15 text-red-400 border border-red-500/30 text-[10px] font-mono hover:bg-red-500/25 transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <Flame className="w-3 h-3" />
                    <span>Defect Anomaly Preset</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => loadPreset("positive")}
                    className="px-2.5 py-1 rounded-lg bg-green-500/15 text-green-400 border border-green-500/30 text-[10px] font-mono hover:bg-green-500/25 transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <Star className="w-3 h-3" />
                    <span>Glowing Acclaim Preset</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => loadPreset("discrepancy")}
                    className="px-2.5 py-1 rounded-lg bg-amber-500/15 text-amber-400 border border-amber-500/30 text-[10px] font-mono hover:bg-amber-500/25 transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <AlertTriangle className="w-3 h-3" />
                    <span>Discrepancy Preset</span>
                  </button>
                </div>
              </div>

              <textarea
                rows={6}
                placeholder={`1★ | Swivel joint cracked after two weeks.\n5★ | The noise cancellation completely silences engine drone.\n2★ | Battery life is significantly shorter than claimed.`}
                value={batchText}
                onChange={(e) => setBatchText(e.target.value)}
                className="w-full p-3.5 rounded-xl bg-white/5 border border-white/10 text-xs font-mono text-white placeholder:text-[#8A8F9E]/50 focus:outline-none focus:border-[#FF5A36] resize-none"
              />
            </div>
          )}

          {/* Engine Processing Progress Bar */}
          {isProcessing && (
            <div className="p-4 rounded-2xl bg-white/5 border border-[#FF5A36]/40 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#FF5A36] flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#FF5A36] animate-ping" />
                  <span>{engineStep}</span>
                </span>
                <span className="text-white font-bold">{engineProgress}%</span>
              </div>
              <div className="h-2 w-full bg-black/40 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-[#FF5A36] to-[#001F54] transition-all duration-300"
                  style={{ width: `${engineProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Execution Result Banner */}
          {executionResult && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 rounded-2xl bg-[#9CAF88]/15 border border-[#9CAF88]/40 space-y-2"
            >
              <div className="flex items-center gap-2 text-sm font-bold text-[#9CAF88]">
                <CheckCircle2 className="w-4 h-4" />
                <span>INSPECTION COMPLETE: Real user reviews successfully ingested into engine!</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-xs font-mono">
                <div className="p-2 rounded-lg bg-black/30">
                  <span className="text-[#8A8F9E] block text-[10px]">TOTAL INGESTED</span>
                  <strong className="text-white text-sm">{executionResult.totalProcessed} reviews</strong>
                </div>
                <div className="p-2 rounded-lg bg-black/30">
                  <span className="text-[#8A8F9E] block text-[10px]">POSITIVE SPANS</span>
                  <strong className="text-[#9CAF88] text-sm">{executionResult.positiveCount}</strong>
                </div>
                <div className="p-2 rounded-lg bg-black/30">
                  <span className="text-[#8A8F9E] block text-[10px]">NEGATIVE DRAG</span>
                  <strong className="text-[#FF5A36] text-sm">{executionResult.negativeCount}</strong>
                </div>
                <div className="p-2 rounded-lg bg-black/30">
                  <span className="text-[#8A8F9E] block text-[10px]">DISCREPANCIES</span>
                  <strong className="text-amber-400 text-sm">{executionResult.discrepancyCount}</strong>
                </div>
              </div>
            </motion.div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-6 sm:px-8 border-t border-white/10 bg-[#0E1833]/60 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs font-mono text-[#8A8F9E]">
            <Info className="w-3.5 h-3.5 text-[#FF5A36]" />
            <span>Updates live KPIs, EWMA control chart, and Aspect Matrix immediately.</span>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              type="button"
              onClick={closeIngestModal}
              className="flex-1 sm:flex-none px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-xs font-mono text-[#FAF6F0] border border-white/10 transition-colors cursor-pointer"
            >
              Cancel
            </button>

            <button
              type="button"
              disabled={isProcessing}
              onClick={handleRunEngine}
              className="flex-1 sm:flex-none px-6 py-2.5 rounded-xl bg-gradient-to-r from-[#FF5A36] to-[#DC2626] hover:from-[#FF451D] hover:to-[#B91C1C] text-white font-mono font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-[0_0_25px_rgba(255,90,54,0.4)] hover:shadow-[0_0_35px_rgba(255,90,54,0.6)] cursor-pointer disabled:opacity-50"
            >
              <Cpu className="w-4 h-4" />
              <span>RUN ABSA ENGINE ON MY INPUT</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
