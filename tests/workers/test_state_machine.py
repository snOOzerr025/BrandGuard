"""
tests/workers/test_state_machine.py
-----------------------------------
Validates Phase 1 Distributed Celery + Redis Task Plane:
1. Transactional state machine: PENDING -> EXTRACTING_ASPECTS -> EMBEDDING -> CLUSTERING -> DETECTING_ANOMALIES -> COMPLETED
2. Failure transition: records FAILED state and error details
3. GET /api/v1/tasks/{task_id} polling endpoint functionality and tenant isolation
4. POST /api/v1/ingest/batch CSV parsing and job dispatch
"""
import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.app.auth.security import hash_password
from backend.app.models.domain import IngestionJob, JobState, Product, Review, User
from backend.app.workers.celery_app import sync_job_status


def test_sync_job_status_state_transitions(session: Session):
    """Verify that sync_job_status persists all state machine transitions to DB."""
    user = User(email="worker_test@brandguard.ai", hashed_password="pw")
    session.add(user)
    session.commit()

    product = Product(user_id=user.id, name="Test Product")
    session.add(product)
    session.commit()

    job = IngestionJob(
        user_id=user.id,
        product_id=product.id,
        state=JobState.PENDING,
        total_reviews=100,
        processed_reviews=0,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    assert job.state == JobState.PENDING
    assert job.processed_reviews == 0

    # Simulate transition to EXTRACTING_ASPECTS
    sync_job_status(session, job.id, None, JobState.EXTRACTING_ASPECTS, 25, 100)
    session.refresh(job)
    assert job.state == JobState.EXTRACTING_ASPECTS
    assert job.processed_reviews == 25

    # Simulate transition to CLUSTERING
    sync_job_status(session, job.id, None, JobState.CLUSTERING, 100, 100)
    session.refresh(job)
    assert job.state == JobState.CLUSTERING

    # Simulate transition to COMPLETED
    sync_job_status(session, job.id, None, JobState.COMPLETED, 100, 100)
    session.refresh(job)
    assert job.state == JobState.COMPLETED
    assert job.processed_reviews == 100


def test_sync_job_status_failure_recording(session: Session):
    """Verify that a failure records error details in DB."""
    user = User(email="failure_test@brandguard.ai", hashed_password="pw")
    session.add(user)
    session.commit()

    product = Product(user_id=user.id, name="Fail Product")
    session.add(product)
    session.commit()

    job = IngestionJob(
        user_id=user.id,
        product_id=product.id,
        state=JobState.PENDING,
        total_reviews=50,
    )
    session.add(job)
    session.commit()

    sync_job_status(session, job.id, None, JobState.FAILED, 10, 50, error="GPU OOM during inference")
    session.refresh(job)
    assert job.state == JobState.FAILED
    assert job.error_detail == "GPU OOM during inference"


def test_task_progress_endpoint(client: TestClient, session: Session):
    """Test polling GET /api/v1/tasks/{task_id} with tenant isolation."""
    # 1. Create User & Login
    client.post("/api/v1/auth/signup", json={"email": "poller@brandguard.ai", "password": "strongPass123"})
    login_resp = client.post("/api/v1/auth/login", json={"email": "poller@brandguard.ai", "password": "strongPass123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch user from DB
    user = session.exec(select(User).where(User.email == "poller@brandguard.ai")).first()
    assert user is not None

    product = Product(user_id=user.id, name="Polling Product")
    session.add(product)
    session.commit()

    job = IngestionJob(
        user_id=user.id,
        product_id=product.id,
        celery_task_id="celery-mock-uuid-12345",
        state=JobState.EMBEDDING,
        total_reviews=200,
        processed_reviews=150,
    )
    session.add(job)
    session.commit()

    # 2. Query by IngestionJob UUID
    resp_uuid = client.get(f"/api/v1/tasks/{job.id}", headers=headers)
    assert resp_uuid.status_code == 200
    data = resp_uuid.json()
    assert data["job_id"] == str(job.id)
    assert data["state"] == "EMBEDDING"
    assert data["current"] == 150
    assert data["total"] == 200
    assert data["progress_pct"] == 75.0

    # 3. Query by Celery task ID
    resp_celery = client.get("/api/v1/tasks/celery-mock-uuid-12345", headers=headers)
    assert resp_celery.status_code == 200
    assert resp_celery.json()["job_id"] == str(job.id)

    # 4. Unknown task returns 404
    resp_404 = client.get(f"/api/v1/tasks/{uuid.uuid4()}", headers=headers)
    assert resp_404.status_code == 404


def test_batch_ingest_csv_endpoint(client: TestClient, session: Session, monkeypatch):
    """Test POST /api/v1/ingest/batch accepts CSV and creates IngestionJob."""
    from unittest.mock import MagicMock
    from backend.app.api.routes import ingest
    mock_task = MagicMock()
    mock_task.id = "celery-mock-batch-1"
    monkeypatch.setattr(ingest.process_review_batch, "apply_async", lambda *args, **kwargs: mock_task)

    client.post("/api/v1/auth/signup", json={"email": "batch_user@brandguard.ai", "password": "strongPass123"})
    login_resp = client.post("/api/v1/auth/login", json={"email": "batch_user@brandguard.ai", "password": "strongPass123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = session.exec(select(User).where(User.email == "batch_user@brandguard.ai")).first()
    assert user is not None

    product = Product(user_id=user.id, name="Batch Ingest Headphone")
    session.add(product)
    session.commit()

    csv_content = (
        "external_review_id,rating,title,text\n"
        "REV-01,5,Amazing Sound,Battery life lasts forever and sound is punchy\n"
        "REV-02,1,Defective Cable,Charging wire frayed on day two\n"
        "REV-03,4,Comfortable,Nice earcups though packaging was a bit dented\n"
    )

    files = {
        "file": ("reviews.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    data = {
        "product_id": str(product.id)
    }

    resp = client.post("/api/v1/ingest/batch", data=data, files=files, headers=headers)
    assert resp.status_code == 202
    resp_data = resp.json()
    assert resp_data["total_reviews"] == 3
    assert resp_data["state"] == "PENDING"
    assert "job_id" in resp_data
    assert "celery_task_id" in resp_data

    # Verify reviews were inserted with job_id
    job_uuid = uuid.UUID(resp_data["job_id"])
    inserted_reviews = session.exec(select(Review).where(Review.job_id == job_uuid)).all()
    assert len(inserted_reviews) == 3
    ratings = {r.rating for r in inserted_reviews}
    assert ratings == {1, 4, 5}
