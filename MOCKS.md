# Active Mocks Tracker

| Mock | Location | Removes In |
|---|---|---|
| `POST /products/{id}/analyze` runs background task but has no job-tracking ID or status poll endpoint | `backend/app/api/routes/insights.py` | Phase 7 (Celery + Redis job queue) |
