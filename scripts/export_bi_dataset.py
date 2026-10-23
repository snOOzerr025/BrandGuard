"""
scripts/export_bi_dataset.py
----------------------------
Exports BrandGuard operational telemetry into Power BI-ready CSV files:
1. products.csv
2. reviews.csv
3. sentiment_results.csv
4. alerts.csv (left-joined with jira_issues)

Usage:
    python scripts/export_bi_dataset.py [--output-dir powerbi/data] [--seed-if-empty]
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session, select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import TSVECTOR

from backend.app.core.database import SyncSessionLocal, create_db_and_tables
from backend.app.models.domain import (
    Alert,
    JiraIssue,
    PolarityLabel,
    Product,
    Review,
    SentimentResult,
    SeverityTier,
    User,
    Vector,
)


@compiles(TSVECTOR, "sqlite")
def compile_tsvector_sqlite(type_, compiler, **kw):
    return "TEXT"


@compiles(Vector, "sqlite")
def compile_vector_sqlite(type_, compiler, **kw):
    return "TEXT"


logger = logging.getLogger("export_bi_dataset")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "powerbi" / "data"


def seed_demo_telemetry_if_needed(session: Session, force: bool = False) -> None:
    """
    Populates rich demo telemetry based on standard demo products if the database is empty.
    Provides data across products, reviews, sentiment_results, alerts, and JIRA issues.
    """
    existing_products = session.exec(select(Product)).all()
    if existing_products and not force:
        logger.info("Database already contains %d products; skipping demo seed.", len(existing_products))
        return

    logger.info("Seeding realistic demo telemetry into database...")
    now = datetime.now(timezone.utc)

    # 1. Seed User
    user = session.exec(select(User).where(User.email == "demo_analyst@brandguard.ai")).first()
    if not user:
        user = User(
            email="demo_analyst@brandguard.ai",
            hashed_password="demo_password_hash",
            full_name="Axis BSG Demo Analyst",
            organization_name="Axis Bank BSG",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

    # 2. Seed Products
    products_data = [
        {
            "name": "Sony WH-1000XM5 Noise-Canceling Headphones",
            "category": "Consumer Audio",
            "source": "amazon_verified",
            "review_count": 850,
            "brand_health_score": 84.2,
            "net_sentiment": 28.4,
        },
        {
            "name": "Apple AirPods Pro (2nd Gen)",
            "category": "Consumer Audio",
            "source": "apple_store",
            "review_count": 1240,
            "brand_health_score": 89.1,
            "net_sentiment": 44.6,
        },
        {
            "name": "Dyson Airwrap Multi-Styler Complete",
            "category": "Hair Care / Beauty Tech",
            "source": "direct_retail",
            "review_count": 620,
            "brand_health_score": 79.5,
            "net_sentiment": 18.2,
        },
    ]

    created_products: List[Product] = []
    for p_info in products_data:
        p = Product(
            user_id=user.id,
            name=p_info["name"],
            category=p_info["category"],
            source=p_info["source"],
            review_count=p_info["review_count"],
            brand_health_score=p_info["brand_health_score"],
            net_sentiment=p_info["net_sentiment"],
            created_at=now - timedelta(days=60),
        )
        session.add(p)
        session.commit()
        session.refresh(p)
        created_products.append(p)

    primary_product = created_products[0]  # Sony XM5

    # 3. Seed Reviews & Sentiment Results
    aspect_samples = [
        ("Quality", "The build quality feels flimsy and the right hinge cracked after 3 months.", 1, PolarityLabel.NEGATIVE, -1.0, 0.95),
        ("Battery", "Marathon battery life easily exceeds 30 hours on a single charge.", 5, PolarityLabel.POSITIVE, 1.0, 0.98),
        ("Performance", "Active noise cancellation completely silences turbine roar on long flights.", 5, PolarityLabel.POSITIVE, 1.0, 0.96),
        ("Design", "Ergonomics are sleek and lightweight, though non-folding arms are bulky.", 4, PolarityLabel.POSITIVE, 1.0, 0.88),
        ("Price", "At 400 dollars it feels significantly overpriced compared to previous generation.", 2, PolarityLabel.NEGATIVE, -1.0, 0.92),
        ("Service", "Customer support claimed hinge fracture was customer abuse and refused warranty.", 1, PolarityLabel.NEGATIVE, -1.0, 0.97),
        ("Delivery", "Delivered within 2 days in pristine packaging with tracking.", 5, PolarityLabel.POSITIVE, 1.0, 0.90),
        ("Packaging", "Protective hardshell case protects headphones well during travel.", 4, PolarityLabel.POSITIVE, 1.0, 0.85),
    ]

    # Generate 40 reviews across past 30 days
    review_ids_quality_neg = []
    review_ids_service_neg = []

    for idx in range(40):
        asp, text_sample, rating, polarity, score, conf = aspect_samples[idx % len(aspect_samples)]
        rev_dt = now - timedelta(days=(idx % 30), hours=(idx * 3 % 24))
        has_disc = (rating >= 4 and polarity == PolarityLabel.NEGATIVE) or (rating <= 2 and polarity == PolarityLabel.POSITIVE)

        rev = Review(
            user_id=user.id,
            product_id=primary_product.id,
            rating=rating,
            title=f"{asp} Feedback #{idx + 1}",
            body=text_sample,
            source_channel="CSV_UPLOAD",
            verified_purchase=True,
            has_rating_discrepancy=has_disc,
            reviewed_at=rev_dt,
            ingested_at=rev_dt,
        )
        session.add(rev)
        session.commit()
        session.refresh(rev)

        if asp == "Quality" and polarity == PolarityLabel.NEGATIVE:
            review_ids_quality_neg.append(str(rev.id))
        elif asp == "Service" and polarity == PolarityLabel.NEGATIVE:
            review_ids_service_neg.append(str(rev.id))

        sent = SentimentResult(
            review_id=rev.id,
            user_id=user.id,
            product_id=primary_product.id,
            aspect_category=asp,
            extracted_span=asp.lower(),
            is_implicit=False,
            polarity=polarity,
            confidence=conf,
            numeric_score=score,
            created_at=rev_dt,
        )
        session.add(sent)

    session.commit()

    # 4. Seed Alerts (Breaches)
    alerts_data = [
        {
            "aspect": "Quality",
            "severity": SeverityTier.CRITICAL,
            "type": "EWMA_DRIFT",
            "z_score": -3.24,
            "mu0": 0.45,
            "curr": -0.68,
            "star_impact": -0.42,
            "support": 42,
            "msg": "Right hinge friction seam fatigue failure reported in batch #402 (z=-3.24)",
            "evidence": review_ids_quality_neg[:3],
            "dt": now - timedelta(days=5),
            "jira_key": "AXIS-101",
            "jira_status": "In Progress",
        },
        {
            "aspect": "Service",
            "severity": SeverityTier.CRITICAL,
            "type": "EWMA_DRIFT",
            "z_score": -3.85,
            "mu0": 0.30,
            "curr": -0.75,
            "star_impact": -0.42,
            "support": 38,
            "msg": "Customer service classified hinge shear fractures as customer abuse (z=-3.85)",
            "evidence": review_ids_service_neg[:3],
            "dt": now - timedelta(days=3),
            "jira_key": "AXIS-102",
            "jira_status": "To Do",
        },
        {
            "aspect": "Performance",
            "severity": SeverityTier.HIGH,
            "type": "RATING_IMPACT",
            "z_score": -2.62,
            "mu0": 0.55,
            "curr": -0.20,
            "star_impact": -0.18,
            "support": 25,
            "msg": "Firmware v2.0.2 Bluetooth stuttering reported on iOS 18 (z=-2.62)",
            "evidence": [],
            "dt": now - timedelta(days=1),
            "jira_key": "AXIS-103",
            "jira_status": "Done",
        },
        {
            "aspect": "Price",
            "severity": SeverityTier.MEDIUM,
            "type": "EWMA_DRIFT",
            "z_score": -2.10,
            "mu0": 0.20,
            "curr": -0.15,
            "star_impact": -0.10,
            "support": 20,
            "msg": "Price perception negative drift following holiday price hike",
            "evidence": [],
            "dt": now - timedelta(days=7),
            "jira_key": None,
            "jira_status": None,
        },
    ]

    for a_info in alerts_data:
        fingerprint = f"{user.id}|{primary_product.id}|{a_info['aspect']}|{a_info['dt'].strftime('%Y-%m-%d')}"
        alert = Alert(
            user_id=user.id,
            product_id=primary_product.id,
            aspect_category=a_info["aspect"],
            severity=a_info["severity"],
            alert_type=a_info["type"],
            z_score=a_info["z_score"],
            baseline_mean=a_info["mu0"],
            current_value=a_info["curr"],
            star_impact=a_info["star_impact"],
            support_count=a_info["support"],
            message=a_info["msg"],
            evidence_review_ids=a_info["evidence"],
            dedup_fingerprint=fingerprint,
            is_acknowledged=False,
            created_at=a_info["dt"],
        )
        session.add(alert)
        session.commit()
        session.refresh(alert)

        if a_info["jira_key"]:
            j_rec = JiraIssue(
                alert_id=alert.id,
                product_id=primary_product.id,
                jira_key=a_info["jira_key"],
                status=a_info["jira_status"],
                summary=a_info["msg"],
                created_at=a_info["dt"],
            )
            session.add(j_rec)
            session.commit()

    logger.info("Demo telemetry seeding successfully completed.")


def export_bi_datasets(
    session: Optional[Session] = None,
    output_dir: Optional[Path] = None,
    seed_if_empty: bool = True,
) -> Dict[str, Path]:
    """
    Exports products, reviews, sentiment_results, and alerts (left-joined with jira_issues)
    into CSV files in output_dir. Returns a dictionary mapping table name to exported file path.
    """
    out_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    def _run_export(db: Session) -> Dict[str, Path]:
        if seed_if_empty:
            seed_demo_telemetry_if_needed(db)

        exported_files: Dict[str, Path] = {}

        # 1. Export products.csv
        products_file = out_dir / "products.csv"
        products = db.exec(select(Product).order_by(Product.name)).all()
        with open(products_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "product_id",
                "name",
                "category",
                "source",
                "review_count",
                "brand_health_score",
                "net_sentiment",
                "created_at",
            ])
            for p in products:
                writer.writerow([
                    str(p.id),
                    p.name,
                    getattr(p, "category", "General"),
                    p.source,
                    p.review_count,
                    round(p.brand_health_score, 2),
                    round(p.net_sentiment, 2),
                    p.created_at.isoformat() if p.created_at else "",
                ])
        exported_files["products"] = products_file
        logger.info("Exported %d products to %s", len(products), products_file)

        # 2. Export reviews.csv
        reviews_file = out_dir / "reviews.csv"
        reviews = db.exec(select(Review).order_by(Review.reviewed_at.desc())).all()
        with open(reviews_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "review_id",
                "product_id",
                "rating",
                "title",
                "body",
                "source_channel",
                "verified_purchase",
                "has_rating_discrepancy",
                "reviewed_at",
            ])
            for r in reviews:
                writer.writerow([
                    str(r.id),
                    str(r.product_id),
                    r.rating,
                    r.title or "",
                    r.body or "",
                    r.source_channel,
                    r.verified_purchase,
                    r.has_rating_discrepancy,
                    r.reviewed_at.isoformat() if r.reviewed_at else "",
                ])
        exported_files["reviews"] = reviews_file
        logger.info("Exported %d reviews to %s", len(reviews), reviews_file)

        # 3. Export sentiment_results.csv
        sentiments_file = out_dir / "sentiment_results.csv"
        sentiments = db.exec(select(SentimentResult).order_by(SentimentResult.created_at.desc())).all()
        with open(sentiments_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "sentiment_id",
                "review_id",
                "product_id",
                "aspect_category",
                "extracted_span",
                "is_implicit",
                "polarity",
                "numeric_score",
                "confidence",
                "created_at",
            ])
            for s in sentiments:
                pol_str = s.polarity.value if hasattr(s.polarity, "value") else str(s.polarity)
                writer.writerow([
                    str(s.id),
                    str(s.review_id),
                    str(s.product_id),
                    s.aspect_category,
                    s.extracted_span or "",
                    s.is_implicit,
                    pol_str,
                    round(s.numeric_score, 2),
                    round(s.confidence, 4),
                    s.created_at.isoformat() if s.created_at else "",
                ])
        exported_files["sentiment_results"] = sentiments_file
        logger.info("Exported %d sentiment records to %s", len(sentiments), sentiments_file)

        # 4. Export alerts.csv (LEFT-JOINED with jira_issues)
        alerts_file = out_dir / "alerts.csv"
        alert_jira_rows = db.exec(
            select(Alert, JiraIssue)
            .outerjoin(JiraIssue, Alert.id == JiraIssue.alert_id)
            .order_by(Alert.created_at.desc())
        ).all()

        with open(alerts_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "alert_id",
                "product_id",
                "aspect_category",
                "severity",
                "alert_type",
                "z_score",
                "baseline_mean",
                "current_value",
                "star_impact",
                "support_count",
                "message",
                "is_acknowledged",
                "created_at",
                "jira_key",
                "jira_status",
                "jira_created_at",
            ])
            for alert, jira_issue in alert_jira_rows:
                sev_str = alert.severity.value if hasattr(alert.severity, "value") else str(alert.severity)
                writer.writerow([
                    str(alert.id),
                    str(alert.product_id),
                    alert.aspect_category,
                    sev_str,
                    alert.alert_type,
                    round(alert.z_score, 2),
                    round(alert.baseline_mean, 2),
                    round(alert.current_value, 2),
                    round(alert.star_impact, 2),
                    alert.support_count,
                    alert.message or "",
                    alert.is_acknowledged,
                    alert.created_at.isoformat() if alert.created_at else "",
                    jira_issue.jira_key if jira_issue else "",
                    jira_issue.status if jira_issue else "",
                    jira_issue.created_at.isoformat() if jira_issue and jira_issue.created_at else "",
                ])
        exported_files["alerts"] = alerts_file
        logger.info("Exported %d alerts (with JIRA join) to %s", len(alert_jira_rows), alerts_file)

        return exported_files

    if session is not None:
        return _run_export(session)

    try:
        with SyncSessionLocal() as db_session:
            return _run_export(db_session)
    except Exception as exc:
        logger.warning("PostgreSQL connection unavailable (%s); falling back to local SQLite engine for export.", exc)
        import sqlite3
        from sqlalchemy import event
        from sqlmodel import create_engine
        from backend.app.models.domain import SQLModel

        sqlite_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})

        @event.listens_for(sqlite_engine, "connect")
        def _sqlite_connect(dbapi_connection, connection_record):
            if isinstance(dbapi_connection, sqlite3.Connection):
                dbapi_connection.create_function("to_tsvector", 2, lambda lang, text: text or "", deterministic=True)

        SQLModel.metadata.create_all(sqlite_engine)
        with Session(sqlite_engine) as local_session:
            return _run_export(local_session)



def main():
    parser = argparse.ArgumentParser(description="Export BrandGuard telemetry datasets for Power BI.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Directory to write CSV files (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--seed-if-empty",
        action="store_true",
        default=True,
        help="Seed demo products, reviews, and alerts if database is currently empty",
    )
    args = parser.parse_args()

    out_path = Path(args.output_dir)
    export_bi_datasets(output_dir=out_path, seed_if_empty=args.seed_if_empty)
    print(f"\n[OK] Power BI export complete. Files written to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
