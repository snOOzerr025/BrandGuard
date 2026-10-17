"""
rag/intent_router.py — Deterministic Intent Router
---------------------------------------------------
Classifies user queries into:
  - SQL_AGGREGATE: Quantitative metrics, percentages, star impact, volume counts
  - PURE_VECTOR: Qualitative semantic discovery, quotes, specific product parts
  - HYBRID: Executive diagnostic questions requiring both deterministic SQL facts
            and verified qualitative review citations.
Enforces Invariant #2 (Zero Hallucinated Metrics).
"""
import re
from typing import Optional
from backend.app.rag.schemas import QueryType, RouteDecision

QUANTITATIVE_PATTERNS = [
    r"\bhow many\b", r"\bpercentage\b", r"\bpercent\b", r"\b%\b",
    r"\brate\b", r"\brating\b", r"\bdrop\b", r"\bincrease\b",
    r"\bcount\b", r"\baverage\b", r"\bimpact\b", r"\bstar\b",
    r"\btrend\b", r"\bnet sentiment\b", r"\bvolume\b", r"\bbreakdown\b",
    r"\bdistribution\b", r"\bmore than\b", r"\bless than\b",
]

QUALITATIVE_PATTERNS = [
    r"\bwhat specific\b", r"\bwhy are users\b", r"\bwhat are customers saying\b",
    r"\bquote\b", r"\bexact\b", r"\bexample\b", r"\bwhat is wrong with\b",
    r"\bdescribe\b", r"\bexplain why\b", r"\bwhich part\b",
]


class IntentRouter:
    """
    Routes copilot questions to prevent LLMs from hallucinating calculations.
    """

    @staticmethod
    def route(query: str, aspect_focus: Optional[str] = None) -> RouteDecision:
        q_lower = query.lower()

        has_quant = any(re.search(pat, q_lower) for pat in QUANTITATIVE_PATTERNS)
        has_qual = any(re.search(pat, q_lower) for pat in QUALITATIVE_PATTERNS)

        # Detect aspect focus if not explicitly passed
        detected_aspect = aspect_focus
        if not detected_aspect:
            aspects = ["Quality", "Price", "Service", "Delivery", "Battery", "Performance", "Design", "Packaging"]
            for a in aspects:
                if a.lower() in q_lower:
                    detected_aspect = a
                    break

        if has_quant and has_qual:
            return RouteDecision(
                query_type=QueryType.HYBRID,
                needs_time_filter=("last" in q_lower or "past" in q_lower or "month" in q_lower or "days" in q_lower),
                aspect_focus=detected_aspect,
                reasoning="Query asks for diagnostic reasoning connecting quantitative metric shift to qualitative customer claims.",
            )
        elif has_quant:
            return RouteDecision(
                query_type=QueryType.SQL_AGGREGATE,
                needs_time_filter=("last" in q_lower or "past" in q_lower or "month" in q_lower or "days" in q_lower),
                aspect_focus=detected_aspect,
                reasoning="Purely quantitative question requiring deterministic database aggregation.",
            )
        else:
            return RouteDecision(
                query_type=QueryType.PURE_VECTOR,
                needs_time_filter=False,
                aspect_focus=detected_aspect,
                reasoning="Qualitative discovery question requiring semantic retrieval and evidence synthesis.",
            )
