"""
api/routes/reviews.py
----------------------
Review ingestion endpoints.
All routes require authentication and are scoped to the authenticated user.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models.user import User
from backend.app.schemas.review import ReviewCreate, ReviewRead
from backend.app.services.review_service import ReviewService

router = APIRouter(prefix="/products/{product_id}/reviews", tags=["reviews"])


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def ingest_review(
    product_id: uuid.UUID,
    payload: ReviewCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Ingest a single review for a product."""
    # Override product_id from path (canonical source)
    payload = ReviewCreate(**{**payload.model_dump(), "product_id": product_id})
    try:
        return ReviewService.create_review(payload, current_user, session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("", response_model=list[ReviewRead])
def list_reviews(
    product_id: uuid.UUID,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List reviews for a product (paginated)."""
    try:
        ReviewService.get_product_or_404(product_id, current_user, session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return ReviewService.list_reviews(product_id, current_user, session, limit, offset)


class BulkIngestRequest:
    pass


from pydantic import BaseModel


class BulkIngestPayload(BaseModel):
    reviews: list[ReviewCreate]


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
def bulk_ingest_reviews(
    product_id: uuid.UUID,
    payload: BulkIngestPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Bulk ingest a list of reviews for a product.
    Returns a summary: {inserted, skipped, errors}.
    """
    # Override product_id from path for every review
    reviews = [
        ReviewCreate(**{**r.model_dump(), "product_id": product_id})
        for r in payload.reviews
    ]
    return ReviewService.bulk_ingest(reviews, current_user, session)
