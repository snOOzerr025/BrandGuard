"""
ml/absa/aspect_extractor.py  (Phase 2 upgrade)
-----------------------------------------------
Upgraded aspect-based sentiment extractor with:
  1. 8 aspects (up from 4) — Battery, Performance, Design, Packaging added
  2. 3x expanded keyword lists per aspect including synonyms
  3. Sentence-level isolation: sentiment is scored on the sentence
     mentioning the aspect, not the whole review (fixes polarity attribution)
  4. Reuses SentimentAnalyzer for all inference (single model load)
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Optional

import pandas as pd

from backend.app.ml.absa.sentiment_analyzer import SentimentAnalyzer

# ---------------------------------------------------------------------------
# Aspect keyword dictionary — 8 aspects, expanded for broad coverage
# ---------------------------------------------------------------------------
ASPECT_KEYWORDS: dict[str, list[str]] = {
    "Quality": [
        "quality", "good", "excellent", "great", "amazing", "perfect",
        "poor", "bad", "terrible", "awful", "defective", "broken",
        "sturdy", "durable", "flimsy", "cheap", "well-made", "poorly-made",
        "craftsmanship", "build", "material", "construction", "premium",
        "solid", "lasting", "fails", "defect", "fell apart", "cheap feel",
        "well built", "reliable", "unreliable", "inferior", "substandard",
    ],
    "Price": [
        "price", "expensive", "cheap", "affordable", "value", "cost",
        "worth", "money", "overpriced", "budget", "deal", "bargain",
        "pricey", "costly", "reasonable", "economical", "pricing",
        "overcharged", "rip-off", "markup", "discount", "sale", "fee",
        "paid", "spent", "refund", "return policy", "waste of money",
        "great price", "best deal", "too much", "not worth",
    ],
    "Service": [
        "service", "support", "help", "customer", "response", "staff",
        "assistance", "helpful", "unhelpful", "rude", "friendly",
        "professional", "representative", "agent", "team", "care",
        "attention", "refund", "return", "warranty", "exchange",
        "complaint", "wait", "response time", "resolved", "ignored",
        "contacted", "reached out", "called", "emailed", "chat",
        "seller", "vendor", "store", "amazon",
    ],
    "Delivery": [
        "delivery", "shipping", "arrived", "package", "late", "fast",
        "quick", "slow", "damaged", "box", "courier", "dispatch",
        "tracking", "packaging", "ship", "received", "delivered",
        "on time", "delayed", "missing", "lost", "wrong item",
        "days", "weeks", "early", "expected", "transit",
    ],
    "Battery": [
        "battery", "charge", "charging", "battery life", "drain",
        "runtime", "hours", "lasts", "last", "power", "mah",
        "dead", "dies", "holds charge", "fast charging", "overnight",
        "capacity", "standby", "unplugged",
    ],
    "Performance": [
        "performance", "speed", "fast", "slow", "lag", "works",
        "crashes", "freezes", "responsive", "smooth", "sluggish",
        "processor", "performance mode", "efficient", "powerful",
        "processing", "handles", "runs", "boots", "starts",
        "lags", "hangs", "stutters", "glitches",
    ],
    "Design": [
        "design", "look", "looks", "feel", "feels", "size", "color",
        "weight", "compact", "bulky", "sleek", "stylish", "ugly",
        "beautiful", "aesthetic", "appearance", "shape", "form factor",
        "lightweight", "heavy", "portable", "slim", "thick",
    ],
    "Packaging": [
        "packaging", "unboxing", "wrapped", "box", "packing",
        "bubble wrap", "protected", "presentation", "arrived in",
        "opened", "sealed", "damaged box", "plastic wrap",
        "eco-friendly", "excessive packaging", "minimal packaging",
    ],
}


def _split_sentences(text: str) -> list[str]:
    """Split review text into sentences for granular aspect matching."""
    sentences = re.split(r"[.!?\n]+", text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]


class AspectExtractor:
    """
    Sentence-level aspect extractor.

    For each review:
      1. Split into sentences
      2. Match each sentence against 8 aspect keyword sets
      3. Run SentimentAnalyzer on the matching SENTENCE (not whole review)
      4. Return per-aspect polarity with confidence

    Usage:
        extractor = AspectExtractor(analyzer)
        results = extractor.analyze_reviews(texts)
        # DataFrame: aspect | mention_count | positive | negative | neutral | sentiment_score
    """

    def __init__(self, analyzer: Optional[SentimentAnalyzer] = None):
        # Accept injected analyzer (for testing) or create one
        self._analyzer = analyzer or SentimentAnalyzer()

    def extract_mentions(
        self, reviews: list[str]
    ) -> dict[str, list[tuple[int, str]]]:
        """
        Extract which sentences mention each aspect.

        Returns:
            {aspect: [(review_idx, sentence_text), ...]}
        """
        mentions: dict[str, list[tuple[int, str]]] = defaultdict(list)

        for idx, review in enumerate(reviews):
            sentences = _split_sentences(review)
            matched_aspects: set[str] = set()

            for sentence in sentences:
                sentence_lower = sentence.lower()
                for aspect, keywords in ASPECT_KEYWORDS.items():
                    if aspect in matched_aspects:
                        continue  # One mention per aspect per review
                    if any(kw in sentence_lower for kw in keywords):
                        mentions[aspect].append((idx, sentence))
                        matched_aspects.add(aspect)

        return dict(mentions)

    def analyze_reviews(self, reviews: list[str]) -> pd.DataFrame:
        """
        Run full aspect-sentiment analysis on a list of reviews.

        Returns:
            DataFrame with columns:
            aspect | mention_count | positive_count | negative_count |
            neutral_count | positive_ratio | sentiment_score
        """
        print(f"[AspectExtractor] Analyzing {len(reviews)} reviews across {len(ASPECT_KEYWORDS)} aspects...")
        mentions = self.extract_mentions(reviews)

        rows = []
        for aspect in ASPECT_KEYWORDS:
            aspect_mentions = mentions.get(aspect, [])
            if not aspect_mentions:
                rows.append({
                    "aspect": aspect,
                    "mention_count": 0,
                    "positive_count": 0,
                    "negative_count": 0,
                    "neutral_count": 0,
                    "positive_ratio": 0.0,
                    "sentiment_score": 0.0,
                })
                continue

            sentences = [sent for _, sent in aspect_mentions]

            # Batch sentiment on SENTENCES (not full reviews)
            try:
                results = self._analyzer.predict(sentences)
            except Exception as exc:
                print(f"[AspectExtractor] Warning: inference failed for '{aspect}': {exc}")
                results = [{"label": "neutral", "confidence": 0.5}] * len(sentences)

            pos = sum(1 for r in results if r["label"] == "positive")
            neg = sum(1 for r in results if r["label"] == "negative")
            neu = sum(1 for r in results if r["label"] == "neutral")
            total = len(results)

            positive_ratio = round((pos / total) * 100, 1) if total else 0.0
            sentiment_score = round(
                sum(
                    r["confidence"] if r["label"] == "positive"
                    else -r["confidence"] if r["label"] == "negative"
                    else 0.0
                    for r in results
                ) / total if total else 0.0,
                3,
            )

            rows.append({
                "aspect": aspect,
                "mention_count": len(aspect_mentions),
                "positive_count": pos,
                "negative_count": neg,
                "neutral_count": neu,
                "positive_ratio": positive_ratio,
                "sentiment_score": sentiment_score,
            })

        df = pd.DataFrame(rows).sort_values("mention_count", ascending=False).reset_index(drop=True)
        print("[AspectExtractor] Done.")
        return df

    def get_examples(
        self,
        reviews: list[str],
        aspect: str,
        polarity: str = "negative",
        limit: int = 5,
    ) -> list[str]:
        """Get example sentences for a given aspect and polarity."""
        mentions = self.extract_mentions(reviews)
        sentences = [s for _, s in mentions.get(aspect, [])]
        if not sentences:
            return []
        results = self._analyzer.predict(sentences)
        return [
            s for s, r in zip(sentences, results)
            if r["label"] == polarity
        ][:limit]
