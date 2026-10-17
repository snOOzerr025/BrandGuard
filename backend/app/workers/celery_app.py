"""
workers/celery_app.py — Distributed Celery 5.4 + Redis Worker Configuration
---------------------------------------------------------------------------
Enforces production task settings:
- Late acknowledgments (task_acks_late=True) so dropped worker restarts requeue jobs
- Worker prefetch = 1 (prevents one worker from hogging large ML batches)
- Dedicated queues: ml_inference, clustering, notifications
- Transactional state synchronization between PostgreSQL IngestionJob and Redis AsyncResult
"""
import os
import uuid
from typing import Optional

from celery import Celery, Task
from celery.utils.log import get_task_logger
from sqlmodel import Session

from backend.app.core.config import settings
from backend.app.core.database import SyncSessionLocal
from backend.app.models.domain import IngestionJob, JobState

logger = get_task_logger(__name__)

celery_app = Celery(
    "brandguard_worker",
    broker=settings.broker_url,
    backend=settings.result_backend_url,
    include=["backend.app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    broker_connection_timeout=1.0,
    broker_connection_max_retries=1,
    broker_connection_retry_on_startup=False,
    worker_prefetch_multiplier=1,  # Prevent 1 worker from hogging heavy ML batches
    task_routes={
        "backend.app.workers.tasks.process_review_batch": {"queue": "ml_inference"},
        "backend.app.workers.tasks.recluster_product_themes": {"queue": "clustering"},
        "backend.app.workers.tasks.dispatch_alert_notifications": {"queue": "notifications"},
    },
)


def sync_job_status(
    db: Session,
    job_id: uuid.UUID,
    task_instance: Optional[Task],
    state: JobState,
    processed: int,
    total: int,
    error: Optional[str] = None,
) -> None:
    """
    Synchronizes pipeline state transition:
    1. Transactional update to PostgreSQL IngestionJob table (survives worker crashes).
    2. Real-time update to Redis backend via Celery update_state (for <12ms polling).
    """
    job = db.get(IngestionJob, job_id)
    if job:
        job.state = state
        job.processed_reviews = processed
        job.total_reviews = total
        if error:
            job.error_detail = error
        db.add(job)
        db.commit()

    if task_instance:
        try:
            task_instance.update_state(
                state=state.value,
                meta={
                    "job_id": str(job_id),
                    "state": state.value,
                    "current": processed,
                    "total": total,
                    "progress_pct": round((processed / max(total, 1)) * 100, 1),
                    "error": error,
                },
            )
        except Exception as exc:
            logger.warning("Could not update Redis task state: %s", exc)
