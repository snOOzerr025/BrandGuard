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


# ---------------------------------------------------------------------------
# Section 6.3 Keyset-Paginated Review Stream
# GET /api/v1/reviews
# ---------------------------------------------------------------------------
import base64
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import and_, or_
from backend.app.models.domain import Review, SentimentResult

stream_router = APIRouter(prefix="/reviews", tags=["reviews"])


class AspectSpanDetail(BaseModel):
    aspect_category: str
    polarity: str
    confidence: float
    extracted_span: Optional[str] = None


class ReviewDetail(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    rating: int
    title: Optional[str] = None
    body: str
    sentiment_label: Optional[str] = None
    has_rating_discrepancy: bool
    reviewed_at: datetime
    source_channel: str
    micro_cluster_id: Optional[uuid.UUID] = None
    aspects: list[AspectSpanDetail] = []


class ReviewStreamResponse(BaseModel):
    items: list[ReviewDetail]
    next_cursor: Optional[str] = None
    has_more: bool
    total: int


@stream_router.get("", response_model=ReviewStreamResponse)
def stream_reviews(
    product_id: Optional[uuid.UUID] = None,
    discrepancy_only: bool = Query(default=False),
    review_ids: Optional[list[str]] = Query(default=None),
    aspect: Optional[str] = Query(default=None),
    micro_cluster_id: Optional[uuid.UUID] = Query(default=None),
    cursor: Optional[str] = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Keyset-paginated review stream supporting filters:
    - product_id
    - discrepancy_only
    - review_ids (e.g. from copilot citations)
    - aspect
    - micro_cluster_id
    """
    from sqlmodel import select

    query = select(Review).where(Review.user_id == current_user.id)

    if product_id:
        query = query.where(Review.product_id == product_id)

    if discrepancy_only:
        query = query.where(Review.has_rating_discrepancy == True)  # noqa: E712

    if micro_cluster_id:
        query = query.where(Review.micro_cluster_id == micro_cluster_id)

    if review_ids:
        parsed_uuids = []
        for rid in review_ids:
            try:
                parsed_uuids.append(uuid.UUID(rid))
            except ValueError:
                pass
        if parsed_uuids:
            query = query.where(Review.id.in_(parsed_uuids))

    if aspect:
        matching_subquery = select(SentimentResult.review_id).where(
            SentimentResult.user_id == current_user.id,
            SentimentResult.aspect_category == aspect,
        )
        query = query.where(Review.id.in_(matching_subquery))

    # Cursor-based keyset pagination: cursor = base64(iso_reviewed_at + "||" + uuid_str)
    if cursor:
        try:
            raw_str = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
            dt_str, id_str = raw_str.split("||")
            cursor_dt = datetime.fromisoformat(dt_str)
            if cursor_dt.tzinfo is None:
                cursor_dt = cursor_dt.replace(tzinfo=timezone.utc)
            cursor_id = uuid.UUID(id_str)
            query = query.where(
                or_(
                    Review.reviewed_at < cursor_dt,
                    and_(Review.reviewed_at == cursor_dt, Review.id < cursor_id),
                )
            )
        except Exception:
            pass

    query = query.order_by(Review.reviewed_at.desc(), Review.id.desc())

    # Fetch limit + 1 to detect has_more
    raw_results = session.exec(query.limit(limit + 1)).all()
    results = [r if isinstance(r, Review) else r[0] for r in raw_results]

    has_more = len(results) > limit
    page_items = results[:limit]

    # Query aspect spans for these reviews
    item_ids = [r.id for r in page_items]
    aspect_map: dict[uuid.UUID, list[AspectSpanDetail]] = {rid: [] for rid in item_ids}
    if item_ids:
        sentiments = session.exec(
            select(SentimentResult).where(
                SentimentResult.review_id.in_(item_ids),
                SentimentResult.user_id == current_user.id,
            )
        ).all()
        for s in sentiments:
            aspect_map[s.review_id].append(
                AspectSpanDetail(
                    aspect_category=s.aspect_category,
                    polarity=s.polarity.value if hasattr(s.polarity, "value") else str(s.polarity),
                    confidence=s.confidence,
                    extracted_span=s.extracted_span,
                )
            )

    next_cursor = None
    if has_more and page_items:
        last = page_items[-1]
        raw_cur = f"{last.reviewed_at.isoformat()}||{str(last.id)}"
        next_cursor = base64.urlsafe_b64encode(raw_cur.encode("utf-8")).decode("utf-8")

    review_details = [
        ReviewDetail(
            id=r.id,
            product_id=r.product_id,
            rating=r.rating,
            title=r.title,
            body=r.body,
            sentiment_label=r.sentiment_label,
            has_rating_discrepancy=r.has_rating_discrepancy,
            reviewed_at=r.reviewed_at,
            source_channel=r.source_channel,
            micro_cluster_id=r.micro_cluster_id,
            aspects=aspect_map.get(r.id, []),
        )
        for r in page_items
    ]

    return ReviewStreamResponse(
        items=review_details,
        next_cursor=next_cursor,
        has_more=has_more,
        total=len(review_details),
    )

