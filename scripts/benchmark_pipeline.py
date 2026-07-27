"""
scripts/benchmark_pipeline.py
------------------------------
Runs the existing ABSA pipeline on real Amazon review data and reports:
- Accuracy vs ground-truth sentiment_label (POSITIVE/NEGATIVE/NEUTRAL)
- Throughput (reviews/sec)
- Aspect distribution across a sample
- Any failure modes (crashes, empty results)

Usage:
    python scripts/benchmark_pipeline.py --sample 200
    python scripts/benchmark_pipeline.py --sample 1000
    python scripts/benchmark_pipeline.py --full   (all 28k rows)
"""
import argparse
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

CSV_PATH = PROJECT_ROOT / "data" / "raw" / "amazon_reviews_nlp_ready-1.csv"


def load_data(sample: int | None) -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=["reviews.text", "sentiment_label"])
    df["reviews.text"] = df["reviews.text"].astype(str).str.strip()
    df = df[df["reviews.text"].str.len() > 5]
    if sample:
        # Stratified sample to preserve sentiment distribution
        pos = df[df["sentiment_label"] == "positive"].head(sample // 3)
        neg = df[df["sentiment_label"] == "negative"].head(sample // 3)
        neu = df[df["sentiment_label"] == "neutral"].head(sample // 3)
        df = pd.concat([pos, neg, neu]).reset_index(drop=True)
    return df


def map_model_label(label: str) -> str:
    """Map POSITIVE/NEGATIVE (model output) → positive/negative/neutral (ground truth labels)."""
    # The model is binary (SST-2) — no neutral class.
    # We compare POSITIVE→positive, NEGATIVE→negative, ignoring neutral ground truth rows
    return label.lower() if label.upper() in {"POSITIVE", "NEGATIVE"} else "neutral"


def run_sentiment_benchmark(df: pd.DataFrame) -> dict:
    """Runs the existing DistilBERT sentiment pipeline against the data."""
    from transformers import pipeline as hf_pipeline

    print(f"\n[benchmark] Loading DistilBERT model...")
    model = hf_pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
        device=-1,  # CPU
        truncation=True,
        max_length=512,
    )

    texts = df["reviews.text"].tolist()
    ground_truths = df["sentiment_label"].tolist()

    print(f"[benchmark] Running on {len(texts)} reviews...")
    t0 = time.time()

    # Batch process
    BATCH = 32
    predictions = []
    for i in range(0, len(texts), BATCH):
        batch = texts[i:i+BATCH]
        try:
            results = model(batch)
            predictions.extend([map_model_label(r["label"]) for r in results])
        except Exception as exc:
            print(f"  [warn] batch {i//BATCH} failed: {exc}")
            predictions.extend(["error"] * len(batch))

    elapsed = time.time() - t0

    # Compute accuracy (exclude neutral ground truth since SST-2 is binary)
    binary_mask = [gt in {"positive", "negative"} for gt in ground_truths]
    binary_gt = [gt for gt, m in zip(ground_truths, binary_mask) if m]
    binary_pred = [pr for pr, m in zip(predictions, binary_mask) if m]

    correct = sum(p == g for p, g in zip(binary_pred, binary_gt))
    accuracy = correct / len(binary_gt) if binary_gt else 0

    # Per-class breakdown
    from collections import Counter
    pred_counter = Counter(predictions)
    gt_counter = Counter(ground_truths)

    return {
        "total_reviews": len(texts),
        "elapsed_seconds": round(elapsed, 2),
        "reviews_per_second": round(len(texts) / elapsed, 1),
        "binary_accuracy": round(accuracy * 100, 2),
        "binary_evaluated": len(binary_gt),
        "prediction_distribution": dict(pred_counter),
        "ground_truth_distribution": dict(gt_counter),
        "errors": predictions.count("error"),
    }


def run_aspect_benchmark(df: pd.DataFrame, sample: int = 100) -> dict:
    """Runs aspect extractor on a smaller slice (aspect extraction is slower)."""
    from backend.app.ml.absa.aspect_extractor import AspectSentimentAnalyzer

    texts = df["reviews.text"].head(sample).tolist()
    print(f"\n[benchmark] Running aspect extractor on {len(texts)} reviews...")
    t0 = time.time()
    analyzer = AspectSentimentAnalyzer()
    try:
        aspect_df = analyzer.analyze_aspect_sentiment(texts)
        elapsed = time.time() - t0
        return {
            "reviewed": len(texts),
            "elapsed_seconds": round(elapsed, 2),
            "aspects_found": aspect_df.to_dict("records"),
        }
    except Exception as exc:
        return {"error": str(exc)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=200)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--skip-aspect", action="store_true")
    args = parser.parse_args()

    sample = None if args.full else args.sample

    print(f"\n{'='*60}")
    print(f"BrandGuard Pipeline Benchmark")
    print(f"{'='*60}")
    print(f"Dataset: {CSV_PATH}")

    df = load_data(sample)
    print(f"Loaded: {len(df)} rows | Sentiment dist: {df['sentiment_label'].value_counts().to_dict()}")

    # --- Sentiment benchmark ---
    results = run_sentiment_benchmark(df)
    print(f"\n[SENTIMENT RESULTS]")
    print(f"  Total reviews      : {results['total_reviews']}")
    print(f"  Time               : {results['elapsed_seconds']}s")
    print(f"  Throughput         : {results['reviews_per_second']} reviews/sec")
    print(f"  Binary accuracy    : {results['binary_accuracy']}% (on {results['binary_evaluated']} pos/neg reviews)")
    print(f"  Prediction dist    : {results['prediction_distribution']}")
    print(f"  Ground truth dist  : {results['ground_truth_distribution']}")
    print(f"  Errors             : {results['errors']}")

    # --- Aspect benchmark ---
    if not args.skip_aspect:
        aspect_results = run_aspect_benchmark(df, sample=min(100, len(df)))
        print(f"\n[ASPECT RESULTS]")
        if "error" in aspect_results:
            print(f"  ERROR: {aspect_results['error']}")
        else:
            print(f"  Reviewed  : {aspect_results['reviewed']} reviews")
            print(f"  Time      : {aspect_results['elapsed_seconds']}s")
            print(f"  Aspects:")
            for a in aspect_results.get("aspects_found", []):
                print(f"    {a['aspect']:12s} — mentions: {a['mention_count']:4d} | pos: {a['positive_count']:3d} | neg: {a['negative_count']:3d} | score: {a['sentiment_score']:+.3f}")

    print(f"\n{'='*60}")
    print("Benchmark complete.")


if __name__ == "__main__":
    main()
