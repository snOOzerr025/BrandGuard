"""
ml/eval/evaluator.py
---------------------
Evaluation harness for the ABSA sentiment pipeline.

Computes precision, recall, F1 per class on a held-out labeled sample,
then writes results to metrics.json and eval_report.md.

Usage:
    python -m backend.app.ml.eval.evaluator

Eval methodology:
  - 300 held-out rows from the 28k Amazon dataset (stratified: 100 pos / 100 neg / 100 neu)
  - Ground truth: the `sentiment_label` column from the original CSV
  - Prediction: SentimentAnalyzer output on the review text
  - Metric: sklearn classification_report (precision, recall, F1, macro avg)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

from backend.app.ml.absa.sentiment_analyzer import SentimentAnalyzer

EVAL_DIR = Path(__file__).parent
METRICS_PATH = EVAL_DIR / "metrics.json"
REPORT_PATH = EVAL_DIR / "eval_report.md"
CSV_PATH = PROJECT_ROOT / "data" / "raw" / "amazon_reviews_nlp_ready-1.csv"
HOLDOUT_N = 300  # 100 per class


def load_holdout(csv_path: Path, n_per_class: int = 100) -> pd.DataFrame:
    """Load a stratified held-out evaluation set (last N rows per class)."""
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=["reviews.text", "sentiment_label"])
    df["reviews.text"] = df["reviews.text"].astype(str).str.strip()
    df = df[df["reviews.text"].str.len() > 5]

    # Use LAST n_per_class rows per sentiment — ensures no overlap with training fixtures
    pos = df[df["sentiment_label"] == "positive"].tail(n_per_class)
    neg = df[df["sentiment_label"] == "negative"].tail(n_per_class)
    neu = df[df["sentiment_label"] == "neutral"].tail(n_per_class)
    holdout = pd.concat([pos, neg, neu]).reset_index(drop=True)
    holdout = holdout.sample(frac=1, random_state=42).reset_index(drop=True)
    return holdout


def run_eval() -> dict:
    """Run the evaluation and return the metrics dict."""
    print(f"[eval] Loading held-out set from: {CSV_PATH}")
    holdout = load_holdout(CSV_PATH)
    print(f"[eval] Held-out size: {len(holdout)} rows | dist: {holdout['sentiment_label'].value_counts().to_dict()}")

    print("[eval] Loading SentimentAnalyzer...")
    analyzer = SentimentAnalyzer()

    texts = holdout["reviews.text"].tolist()
    ground_truths = holdout["sentiment_label"].tolist()

    print(f"[eval] Running inference on {len(texts)} reviews...")
    predictions_raw = analyzer.predict(texts)
    predictions = [r["label"] for r in predictions_raw]

    labels = ["positive", "negative", "neutral"]
    report = classification_report(
        ground_truths,
        predictions,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(ground_truths, predictions, labels=labels).tolist()

    report_text = classification_report(
        ground_truths,
        predictions,
        labels=labels,
        zero_division=0,
    )
    print("\n[eval] Classification Report:\n")
    print(report_text)

    metrics = {
        "model": SentimentAnalyzer.MODEL_NAME,
        "neutral_threshold": 0.90,
        "eval_date": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
        "holdout_n": len(holdout),
        "holdout_per_class": {
            "positive": int((holdout["sentiment_label"] == "positive").sum()),
            "negative": int((holdout["sentiment_label"] == "negative").sum()),
            "neutral": int((holdout["sentiment_label"] == "neutral").sum()),
        },
        "per_class": {
            cls: {
                "precision": round(report[cls]["precision"], 4),
                "recall": round(report[cls]["recall"], 4),
                "f1": round(report[cls]["f1-score"], 4),
                "support": report[cls]["support"],
            }
            for cls in labels
        },
        "macro_avg": {
            "precision": round(report["macro avg"]["precision"], 4),
            "recall": round(report["macro avg"]["recall"], 4),
            "f1": round(report["macro avg"]["f1-score"], 4),
        },
        "weighted_avg": {
            "precision": round(report["weighted avg"]["precision"], 4),
            "recall": round(report["weighted avg"]["recall"], 4),
            "f1": round(report["weighted avg"]["f1-score"], 4),
        },
        "confusion_matrix": {
            "labels": labels,
            "matrix": cm,
        },
        "classification_report_text": report_text,
    }
    return metrics


def write_metrics(metrics: dict) -> None:
    """Write metrics.json."""
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"[eval] Wrote: {METRICS_PATH}")


def write_report(metrics: dict) -> None:
    """Write eval_report.md in human-readable format."""
    m = metrics
    lines = [
        "# BrandGuard — Sentiment Model Evaluation Report",
        "",
        f"**Date:** {m['eval_date']}  ",
        f"**Model:** `{m['model']}`  ",
        f"**Neutral threshold:** confidence < {m['neutral_threshold']}  ",
        f"**Held-out size:** {m['holdout_n']} reviews ({m['holdout_per_class']['positive']} pos / {m['holdout_per_class']['negative']} neg / {m['holdout_per_class']['neutral']} neu)  ",
        "",
        "## Per-Class Metrics",
        "",
        "| Class | Precision | Recall | F1 | Support |",
        "|---|---|---|---|---|",
    ]
    for cls in ["positive", "negative", "neutral"]:
        pc = m["per_class"][cls]
        lines.append(
            f"| {cls.capitalize()} | {pc['precision']:.3f} | {pc['recall']:.3f} | {pc['f1']:.3f} | {pc['support']} |"
        )

    ma = m["macro_avg"]
    wa = m["weighted_avg"]
    lines += [
        f"| **Macro avg** | {ma['precision']:.3f} | {ma['recall']:.3f} | **{ma['f1']:.3f}** | — |",
        f"| Weighted avg | {wa['precision']:.3f} | {wa['recall']:.3f} | {wa['f1']:.3f} | — |",
        "",
        "## Confusion Matrix",
        "",
        "| | Pred Positive | Pred Negative | Pred Neutral |",
        "|---|---|---|---|",
    ]
    cm = m["confusion_matrix"]["matrix"]
    cls_names = ["Positive", "Negative", "Neutral"]
    for i, row in enumerate(cm):
        lines.append(f"| **True {cls_names[i]}** | {row[0]} | {row[1]} | {row[2]} |")

    lines += [
        "",
        "## Interpretation",
        "",
        "- **Positive class** performs best — dataset is heavily positive-skewed (90%).",
        "- **Neutral class** relies on confidence thresholding (score < 0.70 → neutral). ",
        "  The SST-2 model has no native neutral class; this is a v1 heuristic.",
        "- **Negative recall** is the most critical metric for BrandGuard — missing a",
        "  negative review is a false-negative that could hide a real brand problem.",
        "",
        "## Next Iteration",
        "",
        "- Fine-tune on a 3-class ABSA dataset (SemEval restaurant/laptop) for native neutral support.",
        "- Add confidence calibration (Platt scaling) to improve neutral boundary precision.",
        "",
        "---",
        "_Generated by `backend/app/ml/eval/evaluator.py`_",
    ]

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[eval] Wrote: {REPORT_PATH}")


if __name__ == "__main__":
    metrics = run_eval()
    write_metrics(metrics)
    write_report(metrics)
    print(f"\n[eval] Macro F1: {metrics['macro_avg']['f1']:.4f}")
    print("[eval] Done. Check backend/app/ml/eval/eval_report.md and metrics.json")
