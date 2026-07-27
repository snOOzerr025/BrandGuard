from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str = "ok"
    environment: str
    debug: bool


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Verify that the API server is healthy and running"""
    from backend.app.core.config import settings

    return HealthResponse(
        status="ok", environment=settings.ENVIRONMENT, debug=settings.DEBUG
    )
