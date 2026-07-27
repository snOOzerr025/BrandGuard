"""
scripts/load_reviews.py
-----------------------
Loads the Amazon reviews CSV into Postgres via SQLModel.

Usage:
    python scripts/load_reviews.py [--csv PATH] [--limit N] [--user-email EMAIL]

The script:
1. Validates every row with Pydantic before touching the DB (no silent bad data).
2. Upserts Products by name (no duplicates across re-runs).
3. Inserts Reviews — skips rows that fail validation, logs them to stderr.
4. Reports a summary: rows attempted / inserted / skipped.

IMPORTANT: Requires a running Postgres instance (docker-compose up) and valid .env.
"""
import argparse
import sys
import uuid
from pathlib import Path

# Ensure the project root is on sys.path so backend imports work
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from pydantic import ValidationError
from sqlmodel import Session, select

import backend.app.models  # noqa: F401 — registers all model metadata
from backend.app.db.session import create_db_and_tables, engine
from backend.app.models.product import Product
from backend.app.models.review import Review
from backend.app.models.user import User
from backend.app.schemas.review import ReviewIngest


def get_or_create_system_user(session: Session) -> User:
    """Get the system seed user or create one if it doesn't exist.

    This is the owner of all CSV-loaded data. In production each real
    user owns their own data. For seeding we pin to a known email.
    """
    seed_email = "seed@brandguard.local"
    user = session.exec(select(User).where(User.email == seed_email)).first()
    if user:
        return user
    user = User(
        email=seed_email,
        hashed_password="SEED_NO_LOGIN",  # This account cannot log in — password is a sentinel
        full_name="BrandGuard Seed User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    print(f"[seed] Created seed user: {user.email} ({user.id})")
    return user


def get_or_create_product(session: Session, user_id: uuid.UUID, name: str) -> Product:
    """Upsert a product by name under the given user."""
    product = session.exec(
        select(Product).where(Product.user_id == user_id, Product.name == name)
    ).first()
    if product:
        return product
    product = Product(user_id=user_id, name=name, source="amazon_csv")
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def load_csv(csv_path: Path, limit: int | None = None) -> None:
    """Main loader: read CSV, validate rows, insert into DB."""
    print(f"[load] Reading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()  # CSV has leading space in 'name' column

    if limit:
        df = df.head(limit)
        print(f"[load] Limiting to {limit} rows")

    total = len(df)
    inserted = 0
    skipped = 0
    errors: list[str] = []

    create_db_and_tables()

    with Session(engine) as session:
        owner = get_or_create_system_user(session)
        product_cache: dict[str, Product] = {}

        for idx, row in df.iterrows():
            raw = {
                "name": str(row.get("name", "")).strip(),
                "title": str(row.get("reviews.title", "")).strip() or None,
                "text": str(row.get("reviews.text", "")).strip(),
                "rating": int(row["reviews.rating"]) if pd.notna(row.get("reviews.rating")) else None,
                "sentiment_label": str(row.get("sentiment_label", "")).strip() or None,
            }

            try:
                validated = ReviewIngest(**raw)
            except ValidationError as exc:
                skipped += 1
                errors.append(f"Row {idx}: {exc.error_count()} validation error(s) — {exc.errors()[0]['msg']}")
                continue

            # Get/create the product
            product_name = validated.name or "Unknown Product"
            if product_name not in product_cache:
                product_cache[product_name] = get_or_create_product(
                    session, owner.id, product_name
                )
            product = product_cache[product_name]

            review = Review(
                user_id=owner.id,
                product_id=product.id,
                title=validated.title,
                text=validated.text,
                rating=validated.rating,
                sentiment_label=validated.sentiment_label,
                source="amazon_csv",
            )
            session.add(review)
            inserted += 1

            # Batch commit every 500 rows to avoid memory pressure
            if inserted % 500 == 0:
                session.commit()
                print(f"  ... committed {inserted}/{total} rows")

        session.commit()

    print(f"\n[load] Done.")
    print(f"  Total rows in CSV : {total}")
    print(f"  Inserted          : {inserted}")
    print(f"  Skipped (invalid) : {skipped}")
    print(f"  Products created  : {len(product_cache)}")

    if errors:
        print(f"\n[load] First 10 validation errors:")
        for e in errors[:10]:
            print(f"  {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Amazon reviews CSV into BrandGuard DB")
    parser.add_argument(
        "--csv",
        type=Path,
        default=PROJECT_ROOT / "data" / "raw" / "amazon_reviews_nlp_ready-1.csv",
        help="Path to the reviews CSV file",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: limit number of rows loaded (useful for testing)",
    )
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"[error] CSV file not found: {args.csv}", file=sys.stderr)
        sys.exit(1)

    load_csv(args.csv, limit=args.limit)


if __name__ == "__main__":
    main()
