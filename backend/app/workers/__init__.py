"""
workers — Distributed Celery task execution plane.
"""
from backend.app.workers.celery_app import celery_app

__all__ = ["celery_app"]
