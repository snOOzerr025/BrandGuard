"""
api/routes/tasks.py — Real-Time Task Progress Polling
-----------------------------------------------------
GET /api/v1/tasks/{task_id}
Reads real-time state and progress from Celery Redis AsyncResult,
falling back to the IngestionJob database record.
Enforces tenant isolation by verifying the authenticated user owns the job.
"""
import uuid
from typing import Optional
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.app.auth.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models.domain import IngestionJob, User
from backend.app.workers.celery_app import celery_app

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskProgressResponse(BaseModel):
    job_id: str
    celery_task_id: Optional[str] = None
    state: str
    current: int
    total: int
    progress_pct: float
    error: Optional[str] = None


@router.get("/{task_id}", response_model=TaskProgressResponse)
def get_task_progress(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TaskProgressResponse:
    """
    Polls task progress for an ingestion job.
    task_id can be either the IngestionJob UUID or the Celery task ID string.
    """
    job: Optional[IngestionJob] = None

    # Check if task_id is a valid UUID
    try:
        job_uuid = uuid.UUID(task_id)
        job = session.exec(
            select(IngestionJob).where(
                IngestionJob.id == job_uuid,
                IngestionJob.user_id == current_user.id,
            )
        ).first()
    except ValueError:
        # Not a UUID, search by celery_task_id
        pass

    if not job:
        job = session.exec(
            select(IngestionJob).where(
                IngestionJob.celery_task_id == task_id,
                IngestionJob.user_id == current_user.id,
            )
        ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task or job {task_id} not found.",
        )

    state = job.state.value if hasattr(job.state, "value") else str(job.state)
    current = job.processed_reviews
    total = job.total_reviews
    error = job.error_detail

    # 1. Try reading live status from Redis AsyncResult with DB fallback
    try:
        celery_id = job.celery_task_id or task_id
        res = AsyncResult(celery_id, app=celery_app)
        if res and res.state:
            # If Celery has custom meta progress stored in Redis
            if isinstance(res.info, dict):
                state = res.info.get("state", res.state)
                current = res.info.get("current", current)
                total = res.info.get("total", total)
                error = res.info.get("error", error)
            elif res.state in ("SUCCESS", "FAILURE"):
                state = "COMPLETED" if res.state == "SUCCESS" else "FAILED"
                if res.state == "FAILURE":
                    error = str(res.result)
    except Exception:
        pass

    progress_pct = round((current / max(total, 1)) * 100.0, 1)

    return TaskProgressResponse(
        job_id=str(job.id),
        celery_task_id=job.celery_task_id,
        state=state,
        current=current,
        total=total,
        progress_pct=min(progress_pct, 100.0),
        error=error,
    )
