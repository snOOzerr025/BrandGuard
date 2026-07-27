"""
services/review_service.py
---------------------------
Business logic for review ingestion and retrieval.
One concern: this module handles review CRUD only — no ML inference.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlmodel import Session, select

from backend.app.models.product import Product
from backend.app.models.review import Review
from backend.app.models.user import User
from backend.app.schemas.review import ReviewCreate


class ReviewService:

    @staticmethod
    def get_product_or_404(
        product_id: uuid.UUID,
        user: User,
        session: Session,
    ) -> Product:
        """
        Fetch a product that belongs to the authenticated user.
        Raises ValueError (→ 404) if not found or not owned by this user.
        """
        product = session.exec(
            select(Product).where(
                Product.id == product_id,
                Product.user_id == user.id,
            )
        ).first()
        if not product:
            raise ValueError(f"Product {product_id} not found.")
        return product

    @staticmethod
    def create_review(
        payload: ReviewCreate,
        user: User,
        session: Session,
    ) -> Review:
        """Ingest a single review. Validates product ownership first."""
        # Verify the product belongs to this user
        product = session.exec(
            select(Product).where(
                Product.id == payload.product_id,
                Product.user_id == user.id,
            )
        ).first()
        if not product:
            raise ValueError(f"Product {payload.product_id} not found.")

        review = Review(
            user_id=user.id,
            product_id=payload.product_id,
            title=payload.title,
            text=payload.text,
            rating=payload.rating,
            sentiment_label=payload.sentiment_label,
            source=payload.source,
        )
        session.add(review)
        session.commit()
        session.refresh(review)
        return review

    @staticmethod
    def list_reviews(
        product_id: uuid.UUID,
        user: User,
        session: Session,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Review]:
        """List reviews for a product, scoped to the authenticated user."""
        return session.exec(
            select(Review)
            .where(Review.product_id == product_id, Review.user_id == user.id)
            .offset(offset)
            .limit(limit)
        ).all()

    @staticmethod
    def bulk_ingest(
        reviews_data: list[ReviewCreate],
        user: User,
        session: Session,
    ) -> dict:
        """Bulk ingest a list of reviews. Returns summary counts."""
        inserted = 0
        skipped = 0
        errors: list[str] = []

        # Pre-validate all product IDs belong to this user
        product_ids = {r.product_id for r in reviews_data}
        owned_products = {
            p.id
            for p in session.exec(
                select(Product).where(
                    Product.id.in_(list(product_ids)),
                    Product.user_id == user.id,
                )
            ).all()
        }

        for r in reviews_data:
            if r.product_id not in owned_products:
                skipped += 1
                errors.append(f"Product {r.product_id} not found.")
                continue
            review = Review(
                user_id=user.id,
                product_id=r.product_id,
                title=r.title,
                text=r.text,
                rating=r.rating,
                sentiment_label=r.sentiment_label,
                source=r.source,
            )
            session.add(review)
            inserted += 1

        session.commit()
        return {"inserted": inserted, "skipped": skipped, "errors": errors[:10]}
