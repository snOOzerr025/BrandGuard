"""
services/absa_service.py
-------------------------
ABSA pipeline orchestrator — ties together:
  1. SentimentAnalyzer    → overall review-level sentiment
  2. AspectExtractor      → sentence-level per-aspect polarity
  3. ReviewEncoder        → 384-dim embeddings for pgvector + clustering
  4. ReviewClusterer      → KMeans theme discovery

Writes SentimentResult rows to the database (insert-only — never update).
This is the service the API layer (Phase 3) will call.

One concern = one module. This service does orchestration only; it does not
contain ML model code or DB connection logic.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session

from backend.app.ml.absa.aspect_extractor import AspectExtractor
from backend.app.ml.absa.sentiment_analyzer import SentimentAnalyzer
from backend.app.ml.embeddings.cluster import ReviewClusterer
from backend.app.ml.embeddings.encoder import ReviewEncoder
from backend.app.models.review import Review
from backend.app.models.sentiment_result import SentimentResult

MODEL_VERSION = "v2-distilbert-threshold-0.70-sentence-level"


class ABSAService:
    """
    Runs the full ABSA pipeline for a set of reviews and persists results.

    Lazy-loads ML models on first call (not on import) to avoid
    slow startup in the API server for unrelated requests.
    """

    def __init__(self):
        self._analyzer: Optional[SentimentAnalyzer] = None
        self._extractor: Optional[AspectExtractor] = None
        self._encoder: Optional[ReviewEncoder] = None
        self._clusterer: Optional[ReviewClusterer] = None

    # -----------------------------------------------------------------------
    # Lazy model loaders
    # -----------------------------------------------------------------------

    def _get_analyzer(self) -> SentimentAnalyzer:
        if self._analyzer is None:
            self._analyzer = SentimentAnalyzer()
        return self._analyzer

    def _get_extractor(self) -> AspectExtractor:
        if self._extractor is None:
            self._extractor = AspectExtractor(self._get_analyzer())
        return self._extractor

    def _get_encoder(self) -> ReviewEncoder:
        if self._encoder is None:
            self._encoder = ReviewEncoder()
        return self._encoder

    def _get_clusterer(self) -> ReviewClusterer:
        if self._clusterer is None:
            self._clusterer = ReviewClusterer(n_clusters=8)
        return self._clusterer

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def run_pipeline(
        self,
        reviews: list[Review],
        session: Session,
        run_clustering: bool = True,
    ) -> list[SentimentResult]:
        """
        Full pipeline: sentiment + aspects + embeddings + clusters → DB rows.

        Args:
            reviews:         List of Review ORM objects with text populated.
            session:         SQLModel DB session (caller manages commit).
            run_clustering:  Whether to compute embeddings + clusters this run.

        Returns:
            List of inserted SentimentResult rows.
        """
        if not reviews:
            return []

        texts = [r.text for r in reviews]
        analyzer = self._get_analyzer()
        extractor = self._get_extractor()

        print(f"[ABSAService] Running pipeline on {len(reviews)} reviews...")

        # 1. Overall review-level sentiment
        overall_sentiments = analyzer.predict(texts)

        # 2. Aspect-level sentence extraction + sentiment
        aspect_df = extractor.analyze_reviews(texts)
        aspect_mentions = extractor.extract_mentions(texts)

        # 3. Embeddings + clustering
        cluster_results: dict = {}
        if run_clustering:
            encoder = self._get_encoder()
            embeddings = encoder.encode(texts, show_progress=False)
            clusterer = self._get_clusterer()
            cluster_results = clusterer.fit(embeddings, texts)

        cluster_ids = cluster_results.get("cluster_ids", [])
        cluster_labels = cluster_results.get("cluster_labels", {})

        # 4. Build SentimentResult rows — one per review × aspect that has a mention
        result_rows: list[SentimentResult] = []
        computed_at = datetime.now(tz=timezone.utc)

        for review_idx, review in enumerate(reviews):
            overall = overall_sentiments[review_idx]
            cluster_id = int(cluster_ids[review_idx]) if len(cluster_ids) > review_idx else None
            cluster_label = cluster_labels.get(cluster_id) if cluster_id is not None else None

            # Aspects that mention this specific review
            review_aspects: list[tuple[str, str]] = []
            for aspect, mentions in aspect_mentions.items():
                for ridx, sentence in mentions:
                    if ridx == review_idx:
                        review_aspects.append((aspect, sentence))

            if not review_aspects:
                # No specific aspect found — store overall sentiment under "General"
                review_aspects = [("General", review.text[:200])]

            for aspect, span in review_aspects:
                # Get aspect-level sentiment from the sentence span
                aspect_result = analyzer.predict_one(span)

                row = SentimentResult(
                    user_id=review.user_id,
                    review_id=review.id,
                    product_id=review.product_id,
                    aspect=aspect,
                    polarity=aspect_result["label"],
                    confidence=aspect_result["confidence"],
                    aspect_text_span=span[:500],  # truncate long spans
                    cluster_id=cluster_id,
                    cluster_label=cluster_label,
                    model_version=MODEL_VERSION,
                    computed_at=computed_at,
                )
                session.add(row)
                result_rows.append(row)

        print(f"[ABSAService] Inserting {len(result_rows)} SentimentResult rows...")
        return result_rows

    def get_aspect_summary(
        self, reviews: list[Review]
    ) -> list[dict]:
        """
        Lightweight aspect summary without DB writes — used by the API
        for on-demand analysis of a small batch.

        Returns list of {aspect, mention_count, positive_count, negative_count,
                         neutral_count, positive_ratio, sentiment_score}
        """
        texts = [r.text for r in reviews]
        extractor = self._get_extractor()
        df = extractor.analyze_reviews(texts)
        return df.to_dict("records")


# Module-level singleton — shared across requests in the same process
absa_service = ABSAService()
