"""
ml/absa/acd_engine.py — Stage 1: Aspect Category Detection (ACD)
----------------------------------------------------------------
Detects explicit and implicit product aspects across the 8 canonical dimensions
plus General and routes low-confidence/novel feedback to Miscellaneous.
Captures implicit functional complaints without per-review LLM calls.
"""
import re
from dataclasses import dataclass
from typing import List, Optional

from backend.app.ml.absa.canonical_aspects import (
    ASPECT_KEYWORDS,
    CANONICAL_ASPECTS,
    IMPLICIT_PATTERNS,
    MISCELLANEOUS_THRESHOLD,
)


@dataclass
class AspectActivation:
    aspect: str
    confidence: float
    is_implicit: bool
    extracted_span: Optional[str] = None


class ACDEngine:
    """
    Stage 1: Multi-Label Aspect Category Detection engine.
    Analyzes sentence-level clauses to identify both explicit mentions
    and implicit functional complaints.
    """

    def __init__(self, threshold: float = MISCELLANEOUS_THRESHOLD):
        self.threshold = threshold
        # Precompile regex boundaries for explicit keywords
        self._keyword_patterns = {
            aspect: [
                re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
                for kw in keywords
            ]
            for aspect, keywords in ASPECT_KEYWORDS.items()
        }
        # Precompile lowercase implicit patterns
        self._implicit_patterns = {
            aspect: [pat.lower() for pat in patterns]
            for aspect, patterns in IMPLICIT_PATTERNS.items()
        }

    def detect_aspects(self, sentence: str) -> List[AspectActivation]:
        """
        Classifies an individual sentence into one or more aspect activations.
        If no canonical aspect exceeds the confidence threshold, routes to Miscellaneous.
        """
        text_clean = sentence.strip()
        if not text_clean:
            return []

        text_lower = text_clean.lower()
        activations: List[AspectActivation] = []
        aspect_scores: dict[str, float] = {}

        # 1. Scan for implicit functional complaints (high precision on unmentioned attributes)
        for aspect, patterns in self._implicit_patterns.items():
            for pat in patterns:
                if pat in text_lower:
                    # Found implicit pattern
                    span_match = pat
                    conf = 0.94
                    activations.append(
                        AspectActivation(
                            aspect=aspect,
                            confidence=conf,
                            is_implicit=True,
                            extracted_span=span_match,
                        )
                    )
                    aspect_scores[aspect] = max(aspect_scores.get(aspect, 0.0), conf)
                    break

        # 2. Scan for explicit domain keywords
        for aspect, regexes in self._keyword_patterns.items():
            # Skip if already detected via implicit pattern with high confidence
            if aspect in aspect_scores and aspect_scores[aspect] >= 0.90:
                continue

            for reg in regexes:
                match = reg.search(text_clean)
                if match:
                    span_match = match.group(0)
                    conf = 0.96 if aspect != "General" else 0.82
                    activations.append(
                        AspectActivation(
                            aspect=aspect,
                            confidence=conf,
                            is_implicit=False,
                            extracted_span=span_match,
                        )
                    )
                    aspect_scores[aspect] = max(aspect_scores.get(aspect, 0.0), conf)
                    break

        # 3. Handle Miscellaneous nursery routing:
        # If no aspect was detected or max score < threshold
        max_score = max(aspect_scores.values()) if aspect_scores else 0.0
        if max_score < self.threshold or len(activations) == 0:
            # Check if sentence is general praise or complaint
            words = set(re.findall(r"\w+", text_lower))
            general_tokens = {"good", "great", "bad", "terrible", "awesome", "horrible", "love", "hate", "nice"}
            if words.intersection(general_tokens):
                return [
                    AspectActivation(
                        aspect="General",
                        confidence=0.75,
                        is_implicit=False,
                        extracted_span=text_clean[:64],
                    )
                ]
            else:
                return [
                    AspectActivation(
                        aspect="Miscellaneous",
                        confidence=0.50,
                        is_implicit=True,
                        extracted_span=text_clean[:64],
                    )
                ]

        # Deduplicate multiple activations for the same aspect (keep highest confidence)
        unique_activations: dict[str, AspectActivation] = {}
        for act in activations:
            if act.aspect not in unique_activations or act.confidence > unique_activations[act.aspect].confidence:
                unique_activations[act.aspect] = act

        return list(unique_activations.values())
