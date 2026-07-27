"""
api/routes/insights.py
-----------------------
Insights endpoints — aspect summaries, historical records, overall sentiment.

KEY DESIGN INVARIANT:
  GET /products/{id}/insights returns STORED SentimentResult rows, ordered by
  computed_at. It never recomputes on the fly. This is what makes trend charts
  honest — each bar/point in the chart maps to a real timestamped DB row.

  POST /products/{id}/analyze triggers the ABSA pipeline, which INSERTS new
  SentimentResult rows. On the next GET, the new rows appear alongside old ones.
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from backend.app.auth.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models.review import Review
from backend.app.models.user import User
from backend.app.services.insight_service import InsightService
from backend.app.services.review_service import ReviewService

router = APIRouter(prefix="/products/{product_id}", tags=["insights"])


@router.get("/insights/summary")
def get_insight_summary(
    product_id: uuid.UUID,
    from_dt: Optional[datetime] = Query(default=None, alias="from"),
    to_dt: Optional[datetime] = Query(default=None, alias="to"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Aggregated aspect-level sentiment summary for a product.
    Optionally scoped to a time window with ?from=&to= ISO datetime params.
    """
    try:
        ReviewService.get_product_or_404(product_id, current_user, session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    summary = InsightService.get_aspect_summary(
        product_id, current_user, session, from_dt, to_dt
    )
    return {"product_id": str(product_id), "aspects": summary}


@router.get("/insights")
def get_insights_history(
    product_id: uuid.UUID,
    from_dt: Optional[datetime] = Query(default=None, alias="from"),
    to_dt: Optional[datetime] = Query(default=None, alias="to"),
    limit: int = Query(default=200, le=500),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Historical SentimentResult rows for a product, ordered by computed_at ASC.

    This is the "trend over time" data source. Each record represents a real
    pipeline run at a specific timestamp — not a recomputed snapshot.
    Use ?from= and ?to= (ISO 8601 datetimes) to filter by time window.
    """
    try:
        ReviewService.get_product_or_404(product_id, current_user, session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    history = InsightService.get_history(
        product_id, current_user, session, from_dt, to_dt, limit
    )
    return {
        "product_id": str(product_id),
        "count": len(history),
        "results": history,
    }


@router.get("/insights/overall")
def get_overall_sentiment(
    product_id: uuid.UUID,
    from_dt: Optional[datetime] = Query(default=None, alias="from"),
    to_dt: Optional[datetime] = Query(default=None, alias="to"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Overall product sentiment roll-up: total, positive%, negative%, score."""
    try:
        ReviewService.get_product_or_404(product_id, current_user, session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return InsightService.get_overall_sentiment(
        product_id, current_user, session, from_dt, to_dt
    )


@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
def trigger_analysis(
    product_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger the ABSA pipeline on all reviews for this product.
    Runs as a background task — returns 202 immediately.

    The pipeline inserts new SentimentResult rows. After completion,
    GET /insights will show the new results alongside historical ones.

    NOTE: In v1 this runs synchronously in a BackgroundTask (FastAPI built-in).
    Phase 7 can upgrade to Celery + Redis if volume demands it.

    # MOCK — analyze endpoint queues work but doesn't await ML pipeline in this
    # response. ML runs async. Use GET /insights to retrieve results.
    # Full async job tracking is a Phase 7 enhancement.
    """
    try:
        product = ReviewService.get_product_or_404(product_id, current_user, session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    # Count reviews to analyze
    reviews = session.exec(
        select(Review).where(
            Review.product_id == product_id,
            Review.user_id == current_user.id,
        )
    ).all()

    if not reviews:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="No reviews found for this product. Ingest reviews first.",
        )

    def _run_pipeline():
        """Background task: runs ABSA and commits results."""
        from backend.app.db.session import engine
        from backend.app.services.absa_service import absa_service
        from sqlmodel import Session as S

        with S(engine) as bg_session:
            bg_reviews = bg_session.exec(
                select(Review).where(
                    Review.product_id == product_id,
                    Review.user_id == current_user.id,
                )
            ).all()
            absa_service.run_pipeline(bg_reviews, bg_session)
            bg_session.commit()

    background_tasks.add_task(_run_pipeline)

    return {
        "status": "queued",
        "product_id": str(product_id),
        "reviews_queued": len(reviews),
        "message": "ABSA pipeline started. Poll GET /insights to retrieve results.",
    }


@router.get("/clusters")
def get_clusters(
    product_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Return theme clusters discovered in this product's reviews."""
    try:
        ReviewService.get_product_or_404(product_id, current_user, session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    clusters = InsightService.get_clusters(product_id, current_user, session)
    return {"product_id": str(product_id), "clusters": clusters}
