"""
scripts/eval_absa_benchmark.py — Automated SOTA ABSA Evaluation Harness
-----------------------------------------------------------------------
Evaluates two-stage ABSA pipeline against held-out golden benchmark.
Computes per-class Precision, Recall, Macro-F1, Neutral F1, and Confusion Matrix.
Fails CI if Macro-F1 drops below --assert-min-f1 (default: 0.84) or
Neutral F1 drops below 0.76.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from backend.app.ml.absa.acd_engine import ACDEngine
from backend.app.ml.absa.onnx_engine import ONNXABSAEngine
from backend.app.models.domain import PolarityLabel


def evaluate_absa_benchmark(
    dataset_path: str,
    model_dir: str = "models/deberta_absa_int8",
    assert_min_f1: float = 0.84,
    assert_min_neutral_f1: float = 0.76,
) -> bool:
    print(f"\n=======================================================")
    print(f" BrandGuard SOTA ABSA Evaluation Benchmark")
    print(f" Dataset: {dataset_path}")
    print(f" Model Engine: {model_dir}")
    print(f" Threshold Gate: Macro-F1 >= {assert_min_f1}")
    print(f"=======================================================\n")

    path = Path(dataset_path)
    if not path.exists():
        print(f"Error: Dataset not found at {dataset_path}")
        return False

    acd = ACDEngine()
    asc = ONNXABSAEngine(model_dir=model_dir)

    classes = ["Positive", "Neutral", "Negative"]
    conf_matrix = {true_c: {pred_c: 0 for pred_c in classes} for true_c in classes}

    aspect_tp = 0
    aspect_fp = 0
    aspect_fn = 0
    implicit_tp = 0
    implicit_total = 0

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            text = item["text"]
            expected_list = item["expected"]

            expected_by_aspect = {e["aspect"]: e for e in expected_list}

            # 1. Run ACD
            activations = acd.detect_aspects(text)
            detected_by_aspect = {a.aspect: a for a in activations}

            # Score Aspect Detection
            for exp_aspect, exp_val in expected_by_aspect.items():
                if exp_val.get("is_implicit"):
                    implicit_total += 1
                if exp_aspect in detected_by_aspect:
                    aspect_tp += 1
                    if exp_val.get("is_implicit"):
                        implicit_tp += 1
                else:
                    aspect_fn += 1

            for det_aspect in detected_by_aspect:
                if det_aspect not in expected_by_aspect:
                    aspect_fp += 1

            # 2. Score ASC Polarity Classification
            for act in activations:
                if act.aspect in expected_by_aspect:
                    exp_item = expected_by_aspect[act.aspect]
                    exp_pol = exp_item["polarity"]

                    pred_out = asc.classify_aspect_polarity(
                        sentence=text,
                        aspect=act.aspect,
                        extracted_span=act.extracted_span,
                        is_implicit=act.is_implicit,
                    )
                    pred_pol = pred_out.polarity.value
                    conf_matrix[exp_pol][pred_pol] += 1

    # Compute Polarity Metrics
    metrics: Dict[str, Dict[str, float]] = {}
    f1_list = []

    for c in classes:
        tp = conf_matrix[c][c]
        fp = sum(conf_matrix[other][c] for other in classes if other != c)
        fn = sum(conf_matrix[c][other] for other in classes if other != c)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        metrics[c] = {"precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4), "support": tp + fn}
        f1_list.append(f1)

    macro_f1 = sum(f1_list) / len(f1_list)
    aspect_prec = aspect_tp / (aspect_tp + aspect_fp) if (aspect_tp + aspect_fp) > 0 else 0.0
    aspect_rec = aspect_tp / (aspect_tp + aspect_fn) if (aspect_tp + aspect_fn) > 0 else 0.0
    aspect_f1 = (2 * aspect_prec * aspect_rec) / (aspect_prec + aspect_rec) if (aspect_prec + aspect_rec) > 0 else 0.0
    implicit_recall = (implicit_tp / implicit_total) if implicit_total > 0 else 0.0

    print("--- 3x3 Sentiment Confusion Matrix ---")
    print(f"{'True \\ Pred':<12} | {'Positive':<10} | {'Neutral':<10} | {'Negative':<10}")
    print("-" * 50)
    for true_c in classes:
        row_str = " | ".join(f"{conf_matrix[true_c][pred_c]:<10}" for pred_c in classes)
        print(f"{true_c:<12} | {row_str}")

    print("\n--- Per-Class Polarity Performance ---")
    for c in classes:
        print(f" {c:<10} -> Precision: {metrics[c]['precision']:.4f} | Recall: {metrics[c]['recall']:.4f} | F1: {metrics[c]['f1']:.4f} (support: {metrics[c]['support']})")

    print("\n--- Aspect Detection Performance ---")
    print(f" Aspect Detection Macro-F1 : {aspect_f1:.4f} (Prec: {aspect_prec:.4f}, Rec: {aspect_rec:.4f})")
    print(f" Implicit Aspect Recall    : {implicit_recall:.4f} ({implicit_tp}/{implicit_total} implicit claims caught)")

    print(f"\n=======================================================")
    print(f" SUMMARY METRICS")
    print(f" Macro-F1 (All Polarities) : {macro_f1 * 100:.2f}% (Target: >= {assert_min_f1 * 100:.1f}%)")
    print(f" Neutral F1                : {metrics['Neutral']['f1'] * 100:.2f}% (Target: >= {assert_min_neutral_f1 * 100:.1f}%)")
    print(f"=======================================================\n")

    passed = (macro_f1 >= assert_min_f1) and (metrics["Neutral"]["f1"] >= assert_min_neutral_f1)

    if passed:
        print(">>> SUCCESS: ABSA Pipeline passed all production quality gates! <<<\n")
        return True
    else:
        print(f">>> FAILURE: Macro-F1 ({macro_f1:.4f}) or Neutral F1 ({metrics['Neutral']['f1']:.4f}) fell below gate threshold. <<<\n")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BrandGuard ABSA Evaluation Benchmark")
    parser.add_argument("--dataset", default="tests/eval/absa_gold.jsonl", help="Path to golden jsonl dataset")
    parser.add_argument("--model-dir", default="models/deberta_absa_int8", help="Path to compiled ONNX model directory")
    parser.add_argument("--assert-min-f1", type=float, default=0.84, help="Minimum acceptable Macro-F1 score")
    parser.add_argument("--assert-min-neutral-f1", type=float, default=0.76, help="Minimum acceptable Neutral F1 score")

    args = parser.parse_args()
    success = evaluate_absa_benchmark(
        dataset_path=args.dataset,
        model_dir=args.model_dir,
        assert_min_f1=args.assert_min_f1,
        assert_min_neutral_f1=args.assert_min_neutral_f1,
    )
    sys.exit(0 if success else 1)
