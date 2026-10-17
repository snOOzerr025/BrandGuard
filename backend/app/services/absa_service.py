"""
services/absa_service.py — SOTA Aspect-Based Sentiment Analysis Orchestrator
----------------------------------------------------------------------------
Orchestrates the two-stage decoupled ABSA pipeline:
  Stage 1: Multi-Label Aspect Category Detection (ACDEngine)
           Detects explicit and implicit product aspects across 8 canonical dimensions
           plus General, routing novel/unmatched complaints to Miscellaneous nursery.
  Stage 2: Aspect-Guided Polarity Classification (ONNXABSAEngine)
           Disentangles clause-level sentiment across contrastive boundaries.

Persists SentimentResult rows (insert-only) and flags star-vs-text rating discrepancies.
"""
from __future__ import annotations

import re
import uuid
from typing import List, Optional

from sqlmodel import Session, select

from backend.app.ml.absa.acd_engine import ACDEngine, AspectActivation
from backend.app.ml.absa.onnx_engine import AspectSentimentOutput, ONNXABSAEngine
from backend.app.models.domain import Review, SentimentResult

MODEL_VERSION = "v3-deberta-absa-onnx-int8"


class ABSAService:
    """
    Two-stage SOTA ABSA pipeline service.
    Orchestrates aspect extraction and polarity classification for reviews.
    """

    def __init__(self):
        self._acd_engine: Optional[ACDEngine] = None
        self._asc_engine: Optional[ONNXABSAEngine] = None

    def _get_acd_engine(self) -> ACDEngine:
        if self._acd_engine is None:
            self._acd_engine = ACDEngine()
        return self._acd_engine

    def _get_asc_engine(self) -> ONNXABSAEngine:
        if self._asc_engine is None:
            self._asc_engine = ONNXABSAEngine()
        return self._asc_engine

    @classmethod
    def analyze_and_store(
        cls,
        review_id: uuid.UUID,
        text: str,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        session: Session,
    ) -> List[SentimentResult]:
        """Convenience class method to analyze a single review and persist results."""
        service = cls()
        return service.process_review(review_id, text, user_id, product_id, session)

    def process_review(
        self,
        review_id: uuid.UUID,
        text: str,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        session: Session,
    ) -> List[SentimentResult]:
        """
        Processes review text through sentence-level ACD and ASC pipelines,
        writing SentimentResult rows to the database and checking for star rating discrepancy.
        """
        if not text or not text.strip():
            return []

        acd = self._get_acd_engine()
        asc = self._get_asc_engine()

        # Split review into sentences
        sentences = self._split_sentences(text)
        created_results: List[SentimentResult] = []
        numeric_scores: List[float] = []

        for sent in sentences:
            if not sent.strip():
                continue

            # Stage 1: Detect all explicit and implicit aspect categories
            activations: List[AspectActivation] = acd.detect_aspects(sent)

            # Stage 2: Classify aspect-conditioned sentiment for each detected category
            for act in activations:
                res: AspectSentimentOutput = asc.classify_aspect_polarity(
                    sentence=sent,
                    aspect=act.aspect,
                    extracted_span=act.extracted_span,
                    is_implicit=act.is_implicit,
                )

                row = SentimentResult(
                    review_id=review_id,
                    user_id=user_id,
                    product_id=product_id,
                    aspect_category=res.aspect,
                    extracted_span=res.extracted_span,
                    is_implicit=res.is_implicit,
                    polarity=res.polarity,
                    confidence=res.confidence,
                    numeric_score=res.numeric_score,
                    model_version=MODEL_VERSION,
                )
                session.add(row)
                created_results.append(row)
                numeric_scores.append(res.numeric_score)

        session.commit()

        # Check Star-vs-Text Rating Discrepancy
        review = session.get(Review, review_id)
        if review and numeric_scores:
            mean_score = sum(numeric_scores) / len(numeric_scores)
            # High star rating (>=4) with strongly negative text (<=-0.5)
            # Low star rating (<=2) with strongly positive text (>=+0.5)
            if (review.rating >= 4 and mean_score <= -0.5) or (review.rating <= 2 and mean_score >= 0.5):
                review.has_rating_discrepancy = True
                session.add(review)
                session.commit()

        for r in created_results:
            session.refresh(r)

        return created_results

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Splits review body into sentence segments using regex delimiters."""
        raw_sents = re.split(r"(?<=[.!?])\s+|\n+", text)
        return [s.strip() for s in raw_sents if s.strip()]

    def run_pipeline(self, reviews: List[Review], session: Session) -> List[SentimentResult]:
        """Process a list of reviews and write SentimentResults."""
        all_results: List[SentimentResult] = []
        for r in reviews:
            body = r.body if hasattr(r, "body") and r.body else r.text
            res = self.process_review(
                review_id=r.id,
                text=body,
                user_id=r.user_id,
                product_id=r.product_id,
                session=session,
            )
            all_results.extend(res)
        return all_results


absa_service = ABSAService()
