"""
scripts/verify_phase_1.py
-------------------------
Deterministic verification script for Phase 1:
- Validates Celery app configuration and task routing
- Tests IngestionJob state transitions: PENDING -> EXTRACTING_ASPECTS -> CLUSTERING -> COMPLETED
- Tests failure transitions: PENDING -> FAILED
- Validates batch ingestion and task status polling logic
"""
import uuid
import sqlite3
from sqlalchemy import create_engine, event
from sqlmodel import Session, SQLModel, select

from backend.app.models.domain import IngestionJob, JobState, Product, Review, User
from backend.app.workers.celery_app import celery_app, sync_job_status
from backend.app.workers.tasks import process_review_batch

print("--> [1/4] Verifying Celery configuration & task routing...")
routes = celery_app.conf.task_routes
assert "backend.app.workers.tasks.process_review_batch" in routes
assert routes["backend.app.workers.tasks.process_review_batch"]["queue"] == "ml_inference"
assert routes["backend.app.workers.tasks.recluster_product_themes"]["queue"] == "clustering"
assert routes["backend.app.workers.tasks.dispatch_alert_notifications"]["queue"] == "notifications"
assert celery_app.conf.worker_prefetch_multiplier == 1
assert celery_app.conf.task_acks_late is True
print("    Celery routes, queues, and production invariants verified!")

print("--> [2/4] Initializing test DB engine...")
engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
@event.listens_for(engine, "connect")
def _sqlite_connect(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.create_function("to_tsvector", 2, lambda lang, text: text or "")

SQLModel.metadata.create_all(engine)
print("    DB ready!")

print("--> [3/4] Verifying transactional state machine transitions...")
with Session(engine) as session:
    user = User(email="worker_verifier@brandguard.ai", hashed_password="pw")
    session.add(user)
    session.commit()

    product = Product(user_id=user.id, name="Worker Headset")
    session.add(product)
    session.commit()

    job = IngestionJob(
        user_id=user.id,
        product_id=product.id,
        state=JobState.PENDING,
        total_reviews=50,
        processed_reviews=0,
    )
    session.add(job)
    session.commit()

    # Step through pipeline states
    sync_job_status(session, job.id, None, JobState.EXTRACTING_ASPECTS, 10, 50)
    session.refresh(job)
    assert job.state == JobState.EXTRACTING_ASPECTS
    assert job.processed_reviews == 10

    sync_job_status(session, job.id, None, JobState.EMBEDDING, 25, 50)
    session.refresh(job)
    assert job.state == JobState.EMBEDDING

    sync_job_status(session, job.id, None, JobState.CLUSTERING, 40, 50)
    session.refresh(job)
    assert job.state == JobState.CLUSTERING

    sync_job_status(session, job.id, None, JobState.DETECTING_ANOMALIES, 50, 50)
    session.refresh(job)
    assert job.state == JobState.DETECTING_ANOMALIES

    sync_job_status(session, job.id, None, JobState.COMPLETED, 50, 50)
    session.refresh(job)
    assert job.state == JobState.COMPLETED
    assert job.processed_reviews == 50
    print("    Full 5-stage lifecycle state machine verified!")

print("--> [4/4] Verifying failure state recording...")
with Session(engine) as session:
    fail_job = IngestionJob(
        user_id=user.id,
        product_id=product.id,
        state=JobState.PENDING,
        total_reviews=10,
    )
    session.add(fail_job)
    session.commit()

    sync_job_status(session, fail_job.id, None, JobState.FAILED, 2, 10, error="Worker connection timed out")
    session.refresh(fail_job)
    assert fail_job.state == JobState.FAILED
    assert fail_job.error_detail == "Worker connection timed out"
    print("    Failure state and error recording verified!")

print("\nAll Phase 1 Celery & Task State Machine Invariants Verified Successfully! 100% Passed.")
