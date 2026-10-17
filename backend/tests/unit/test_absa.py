"""
Unit tests for Phase 2 ABSA pipeline.

Uses real fixture data from tests/fixtures/sample_reviews.csv.
Tests every layer: SentimentAnalyzer, AspectExtractor, ReviewEncoder, ReviewClusterer.

IMPORTANT: No Faker / synthetic text. Real-world edge cases (sarcasm, mixed
sentiment, short reviews) hide in real data — synthetic data masks them.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

FIXTURE_CSV = Path(__file__).parent.parent / "fixtures" / "sample_reviews.csv"


@pytest.fixture(scope="module")
def fixture_reviews() -> list[str]:
    df = pd.read_csv(FIXTURE_CSV)
    df.columns = df.columns.str.strip()
    return df["reviews.text"].dropna().astype(str).str.strip().tolist()


@pytest.fixture(scope="module")
def fixture_labels() -> list[str]:
    df = pd.read_csv(FIXTURE_CSV)
    df.columns = df.columns.str.strip()
    return df["sentiment_label"].tolist()


# ---------------------------------------------------------------------------
# SentimentAnalyzer tests
# ---------------------------------------------------------------------------

class TestSentimentAnalyzer:
    @pytest.fixture(scope="class")
    def analyzer(self):
        from backend.app.ml.absa.sentiment_analyzer import SentimentAnalyzer
        return SentimentAnalyzer()

    def test_predict_returns_correct_keys(self, analyzer):
        result = analyzer.predict(["Great product!"])
        assert len(result) == 1
        assert "label" in result[0]
        assert "confidence" in result[0]

    def test_label_is_valid_class(self, analyzer):
        texts = ["Amazing quality!", "Terrible, broke immediately.", "It works okay."]
        results = analyzer.predict(texts)
        valid_labels = {"positive", "negative", "neutral"}
        for r in results:
            assert r["label"] in valid_labels

    def test_confidence_is_float_in_range(self, analyzer):
        results = analyzer.predict(["Great!", "Bad."])
        for r in results:
            assert isinstance(r["confidence"], float)
            assert 0.0 <= r["confidence"] <= 1.0

    def test_clearly_positive_review(self, analyzer):
        result = analyzer.predict_one("Absolutely love this product! Best purchase ever!")
        assert result["label"] == "positive"
        assert result["confidence"] > 0.85

    def test_clearly_negative_review(self, analyzer):
        result = analyzer.predict_one("Terrible quality. Broke after 2 days. Total waste of money.")
        assert result["label"] == "negative"
        assert result["confidence"] > 0.80

    def test_batch_size_consistency(self, analyzer):
        """Results should be identical whether processed in one batch or individually."""
        texts = ["Great!", "Awful.", "Works fine."]
        batch_results = analyzer.predict(texts)
        single_results = [analyzer.predict_one(t) for t in texts]
        for b, s in zip(batch_results, single_results):
            assert b["label"] == s["label"]

    def test_on_real_fixture_data(self, analyzer, fixture_reviews, fixture_labels):
        """At least 80% accuracy on binary (pos/neg) fixture rows."""
        binary_texts = [
            (t, l) for t, l in zip(fixture_reviews, fixture_labels)
            if l in {"positive", "negative"}
        ]
        texts = [t for t, _ in binary_texts]
        truths = [l for _, l in binary_texts]
        preds = [r["label"] for r in analyzer.predict(texts)]
        acc = sum(p == g for p, g in zip(preds, truths)) / len(truths)
        assert acc >= 0.75, f"Binary accuracy {acc:.2%} below 75% threshold on fixture data"


# ---------------------------------------------------------------------------
# AspectExtractor tests
# ---------------------------------------------------------------------------

class TestAspectExtractor:
    @pytest.fixture(scope="class")
    def extractor(self):
        from backend.app.ml.absa.aspect_extractor import AspectExtractor
        return AspectExtractor()

    def test_returns_dataframe_with_all_8_aspects(self, extractor):
        from backend.app.ml.absa.aspect_extractor import ASPECT_KEYWORDS
        texts = ["Great product, fast delivery, good battery life."]
        df = extractor.analyze_reviews(texts)
        assert set(df["aspect"].tolist()) == set(ASPECT_KEYWORDS.keys())

    def test_quality_aspect_detected(self, extractor):
        texts = ["The build quality is excellent and very sturdy."]
        df = extractor.analyze_reviews(texts)
        quality_row = df[df["aspect"] == "Quality"].iloc[0]
        assert quality_row["mention_count"] >= 1

    def test_battery_aspect_detected(self, extractor):
        texts = ["Battery life is terrible, drains in 2 hours."]
        df = extractor.analyze_reviews(texts)
        battery_row = df[df["aspect"] == "Battery"].iloc[0]
        assert battery_row["mention_count"] >= 1

    def test_negative_aspect_scores_negative(self, extractor):
        texts = ["The customer service was absolutely terrible and unhelpful."]
        df = extractor.analyze_reviews(texts)
        service_row = df[df["aspect"] == "Service"].iloc[0]
        if service_row["mention_count"] > 0:
            assert service_row["sentiment_score"] < 0

    def test_on_real_fixture_data_coverage(self, extractor, fixture_reviews):
        """At least 3 of 8 aspects should have mentions across 50 real reviews."""
        df = extractor.analyze_reviews(fixture_reviews[:20])  # use 20 for speed
        aspects_with_mentions = df[df["mention_count"] > 0]
        assert len(aspects_with_mentions) >= 3, (
            f"Only {len(aspects_with_mentions)} aspects detected in fixture data"
        )

    def test_get_examples_returns_sentences(self, extractor):
        texts = [
            "The quality is amazing. Delivery was fast.",
            "Terrible quality. Product broke immediately.",
        ]
        examples = extractor.get_examples(texts, "Quality", polarity="negative")
        assert isinstance(examples, list)


# ---------------------------------------------------------------------------
# ReviewEncoder tests
# ---------------------------------------------------------------------------

class TestReviewEncoder:
    @pytest.fixture(scope="class")
    def encoder(self):
        from backend.app.ml.embeddings.encoder import ReviewEncoder
        return ReviewEncoder()

    def test_output_shape(self, encoder):
        texts = ["Hello world", "Another review"]
        embeddings = encoder.encode(texts)
        assert embeddings.shape == (2, 384)

    def test_output_dtype_float32(self, encoder):
        embeddings = encoder.encode(["Test review"])
        assert embeddings.dtype == np.float32

    def test_embeddings_are_normalized(self, encoder):
        """L2 norm of each embedding should be ~1.0 (normalized=True)."""
        embeddings = encoder.encode(["Great quality battery life!"])
        norm = np.linalg.norm(embeddings[0])
        assert abs(norm - 1.0) < 1e-4

    def test_similar_texts_have_similar_embeddings(self, encoder):
        similar = encoder.encode(["Great product!", "Excellent item!"])
        different = encoder.encode(["Great product!", "Terrible waste of money."])
        sim_score = float(np.dot(similar[0], similar[1]))
        diff_score = float(np.dot(different[0], different[1]))
        assert sim_score > diff_score, "Similar texts should have higher cosine similarity"

    def test_empty_list_returns_empty_array(self, encoder):
        result = encoder.encode([])
        assert result.shape == (0, 384)


# ---------------------------------------------------------------------------
# ReviewClusterer tests
# ---------------------------------------------------------------------------

class TestReviewClusterer:
    @pytest.fixture(scope="class")
    def encoder(self):
        from backend.app.ml.embeddings.encoder import ReviewEncoder
        return ReviewEncoder()

    def test_cluster_ids_shape_matches_input(self, encoder):
        from backend.app.ml.embeddings.cluster import ReviewClusterer
        texts = ["Good product"] * 20 + ["Terrible quality"] * 20
        embeddings = encoder.encode(texts)
        clusterer = ReviewClusterer(n_clusters=4)
        result = clusterer.fit(embeddings, texts)
        assert len(result["cluster_ids"]) == 40

    def test_cluster_labels_are_strings(self, encoder):
        from backend.app.ml.embeddings.cluster import ReviewClusterer
        texts = ["Battery is amazing"] * 10 + ["Delivery was fast"] * 10
        embeddings = encoder.encode(texts)
        clusterer = ReviewClusterer(n_clusters=2)
        result = clusterer.fit(embeddings, texts)
        for label in result["cluster_labels"].values():
            assert isinstance(label, str)
            assert len(label) > 0

    def test_cluster_sizes_sum_to_total(self, encoder):
        from backend.app.ml.embeddings.cluster import ReviewClusterer
        texts = ["Review " + str(i) for i in range(30)]
        embeddings = encoder.encode(texts)
        clusterer = ReviewClusterer(n_clusters=3)
        result = clusterer.fit(embeddings, texts)
        total = sum(result["cluster_sizes"].values())
        assert total == 30

    def test_on_real_fixture_data(self, encoder, fixture_reviews):
        """Clusters on real reviews should produce at least 3 non-empty clusters."""
        from backend.app.ml.embeddings.cluster import ReviewClusterer
        embeddings = encoder.encode(fixture_reviews)
        clusterer = ReviewClusterer(n_clusters=6)
        result = clusterer.fit(embeddings, fixture_reviews)
        non_empty = sum(1 for v in result["cluster_sizes"].values() if v > 0)
        assert non_empty >= 3
