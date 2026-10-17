"""
ml/eval/drift_monitor.py — Soft-Output Statistical Drift & Miscellaneous Nursery Monitor
----------------------------------------------------------------------------------------
Monitors production ABSA distributions without ground-truth labels:
1. Jensen-Shannon Divergence (JSD) between baseline and rolling class probabilities.
2. Population Stability Index (PSI) over sentiment distribution.
3. Miscellaneous nursery growth rate: triggers drift warning if Miscellaneous volume >= 12%.
"""
import math
from typing import Any, Dict, List


def calculate_psi(baseline_dist: List[float], current_dist: List[float], epsilon: float = 1e-4) -> float:
    """
    Computes Population Stability Index (PSI) between baseline and current distributions:
      PSI = SUM( (Actual_i - Expected_i) * ln(Actual_i / Expected_i) )
    Interpretation:
      PSI < 0.10: No significant distribution change.
      0.10 <= PSI < 0.25: Moderate shift; monitoring recommended.
      PSI >= 0.25: Significant drift; model recalibration needed.
    """
    psi = 0.0
    for exp, act in zip(baseline_dist, current_dist):
        exp_adj = max(exp, epsilon)
        act_adj = max(act, epsilon)
        psi += (act_adj - exp_adj) * math.log(act_adj / exp_adj)
    return round(psi, 4)


def calculate_jsd(p: List[float], q: List[float], epsilon: float = 1e-4) -> float:
    """
    Computes symmetric Jensen-Shannon Divergence (JSD) bounded in [0, 1]:
      JSD(P || Q) = 0.5 * KL(P || M) + 0.5 * KL(Q || M), where M = 0.5 * (P + Q)
    """
    m = [0.5 * (pi + qi) for pi, qi in zip(p, q)]

    def kl_div(dist, ref):
        kl = 0.0
        for d, r in zip(dist, ref):
            d_adj = max(d, epsilon)
            r_adj = max(r, epsilon)
            kl += d_adj * math.log(d_adj / r_adj, 2)
        return kl

    jsd = 0.5 * kl_div(p, m) + 0.5 * kl_div(q, m)
    return round(math.sqrt(max(jsd, 0.0)), 4)


class ABSADriftMonitor:
    """
    Production drift monitoring harness for aspect predictions and nursery growth.
    """

    def __init__(self, misc_threshold_pct: float = 12.0):
        self.misc_threshold_pct = misc_threshold_pct

    def check_nursery_growth(self, aspect_counts: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculates the percentage of reviews routed to the Miscellaneous nursery bucket.
        Triggers drift alert if Miscellaneous share >= 12%.
        """
        total = sum(aspect_counts.values())
        if total == 0:
            return {"misc_percentage": 0.0, "is_drift_detected": False}

        misc_count = aspect_counts.get("Miscellaneous", 0)
        misc_pct = round((misc_count / total) * 100.0, 2)
        drift_detected = misc_pct >= self.misc_threshold_pct

        return {
            "total_aspect_mentions": total,
            "misc_count": misc_count,
            "misc_percentage": misc_pct,
            "is_drift_detected": drift_detected,
            "threshold_pct": self.misc_threshold_pct,
            "recommendation": (
                "Trigger active learning / taxonomy expansion"
                if drift_detected
                else "Distribution stable"
            ),
        }
