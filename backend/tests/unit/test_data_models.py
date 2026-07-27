"""
Unit tests for Phase 1: data models and CSV loader validation.

Uses the real fixture data from tests/fixtures/sample_reviews.csv —
NOT synthetic Faker data — so tests catch real-world edge cases.
"""
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from backend.app.schemas.review import ReviewIngest

FIXTURE_CSV = Path(__file__).parent.parent / "fixtures" / "sample_reviews.csv"


class TestReviewIngestSchema:
    """Validate that ReviewIngest schema correctly validates real fixture rows."""

    def test_fixture_file_exists(self):
        assert FIXTURE_CSV.exists(), f"Fixture not found: {FIXTURE_CSV}"

    def test_fixture_has_expected_columns(self):
        df = pd.read_csv(FIXTURE_CSV)
        df.columns = df.columns.str.strip()
        required = {"name", "reviews.text", "reviews.rating", "sentiment_label"}
        assert required.issubset(set(df.columns)), f"Missing columns: {required - set(df.columns)}"

    def test_all_fixture_rows_pass_validation(self):
        """Every row in the fixture must pass Pydantic validation."""
        df = pd.read_csv(FIXTURE_CSV)
        df.columns = df.columns.str.strip()
        failures = []
        for idx, row in df.iterrows():
            try:
                ReviewIngest(
                    name=str(row.get("name", "")).strip(),
                    title=str(row.get("reviews.title", "")).strip() or None,
                    text=str(row.get("reviews.text", "")).strip(),
                    rating=int(row["reviews.rating"]) if pd.notna(row.get("reviews.rating")) else None,
                    sentiment_label=str(row.get("sentiment_label", "")).strip() or None,
                )
            except ValidationError as exc:
                failures.append(f"Row {idx}: {exc.errors()[0]['msg']}")
        assert not failures, f"Validation failures in fixture:\n" + "\n".join(failures)

    def test_sentiment_distribution_in_fixture(self):
        """Fixture should contain all three sentiment classes."""
        df = pd.read_csv(FIXTURE_CSV)
        df.columns = df.columns.str.strip()
        labels = set(df["sentiment_label"].unique())
        assert "positive" in labels
        assert "negative" in labels
        assert "neutral" in labels

    def test_invalid_rating_rejected(self):
        with pytest.raises(ValidationError):
            ReviewIngest(name="Test", text="Some review", rating=6)

    def test_invalid_sentiment_rejected(self):
        with pytest.raises(ValidationError):
            ReviewIngest(name="Test", text="Some review", sentiment_label="very_bad")

    def test_empty_text_rejected(self):
        with pytest.raises(ValidationError):
            ReviewIngest(name="Test", text="   ")

    def test_valid_minimal_review(self):
        r = ReviewIngest(name="Product A", text="Great product!")
        assert r.name == "Product A"
        assert r.text == "Great product!"
        assert r.rating is None
        assert r.sentiment_label is None

    def test_valid_full_review(self):
        r = ReviewIngest(
            name="AmazonBasics Batteries",
            title="Works perfectly",
            text="These batteries last a long time.",
            rating=5,
            sentiment_label="positive",
        )
        assert r.rating == 5
        assert r.sentiment_label == "positive"
