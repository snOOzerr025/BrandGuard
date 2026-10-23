"""
tests/analytics/test_export_bi.py
---------------------------------
Validates BI dataset export pipeline:
- Export of products.csv, reviews.csv, sentiment_results.csv, alerts.csv
- Verification of column schemas and non-empty row counts
- Verification that alerts.csv contains left-joined JIRA issue fields
"""
import csv
from pathlib import Path
import pytest
from sqlmodel import Session

from scripts.export_bi_dataset import export_bi_datasets


def test_export_bi_datasets(tmp_path: Path, session: Session):
    """Verify that export_bi_datasets creates all 4 required CSV files with proper headers."""
    exported = export_bi_datasets(
        session=session,
        output_dir=tmp_path,
        seed_if_empty=True,
    )

    assert "products" in exported
    assert "reviews" in exported
    assert "sentiment_results" in exported
    assert "alerts" in exported

    # 1. Check products.csv
    products_file = exported["products"]
    assert products_file.exists()
    with open(products_file, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        headers = reader[0]
        assert "product_id" in headers
        assert "name" in headers
        assert "brand_health_score" in headers
        assert "net_sentiment" in headers
        assert len(reader) >= 2  # header + at least 1 product

    # 2. Check reviews.csv
    reviews_file = exported["reviews"]
    assert reviews_file.exists()
    with open(reviews_file, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        headers = reader[0]
        assert "review_id" in headers
        assert "product_id" in headers
        assert "rating" in headers
        assert "has_rating_discrepancy" in headers
        assert len(reader) >= 2

    # 3. Check sentiment_results.csv
    sentiments_file = exported["sentiment_results"]
    assert sentiments_file.exists()
    with open(sentiments_file, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        headers = reader[0]
        assert "sentiment_id" in headers
        assert "aspect_category" in headers
        assert "polarity" in headers
        assert "numeric_score" in headers
        assert len(reader) >= 2

    # 4. Check alerts.csv (with JIRA left-join)
    alerts_file = exported["alerts"]
    assert alerts_file.exists()
    with open(alerts_file, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        headers = reader[0]
        assert "alert_id" in headers
        assert "aspect_category" in headers
        assert "severity" in headers
        assert "z_score" in headers
        assert "star_impact" in headers
        assert "jira_key" in headers
        assert "jira_status" in headers
        assert len(reader) >= 2

        # Verify that at least one row has a linked JIRA key (left join demonstration)
        jira_keys = [row[headers.index("jira_key")] for row in reader[1:]]
        assert any(k.startswith("AXIS-") for k in jira_keys if k)
