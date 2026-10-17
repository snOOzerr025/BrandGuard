"""
api/routes/alerts.py
---------------------
Alerts endpoints:
  POST  /products/{id}/alerts/scan        — trigger anomaly detection
  GET   /products/{id}/alerts             — list alerts (filterable)
  PATCH /products/{id}/alerts/{alert_id}/acknowledge — mark as resolved
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.app.auth.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models.alert import Alert
from backend.app.models.product import Product
from backend.app.models.user import User
from backend.app.services.alert_service import AlertService

router = APIRouter(prefix="/products/{product_id}/alerts", tags=["alerts"])


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class AlertRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    alert_type: str
    severity: str
    aspect: Optional[str]
    message: str
    is_acknowledged: bool
    triggered_at: str  # ISO string

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, alert: Alert) -> "AlertRead":
        return cls(
            id=alert.id,
            product_id=alert.product_id,
            alert_type=alert.alert_type,
            severity=alert.severity.value.lower() if hasattr(alert.severity, "value") else str(alert.severity).lower(),
            aspect=alert.aspect,
            message=alert.message,
            is_acknowledged=alert.is_acknowledged,
            triggered_at=alert.triggered_at.isoformat(),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_product_or_404(
    product_id: uuid.UUID,
    user: User,
    session: Session,
) -> Product:
    product = session.exec(
        select(Product).where(
            Product.id == product_id,
            Product.user_id == user.id,
        )
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/scan", status_code=status.HTTP_200_OK)
def scan_for_anomalies(
    product_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Run anomaly detection on stored SentimentResult rows for this product.
    Returns list of newly created alerts. If no anomalies found, returns empty list.

    Dedup-safe: calling scan multiple times will not create duplicate alerts
    for the same (aspect, alert_type) within a 24-hour window.
    """
    _get_product_or_404(product_id, current_user, session)

    new_alerts = AlertService.scan(product_id, current_user, session)
    return {
        "product_id": str(product_id),
        "new_alerts": len(new_alerts),
        "alerts": [AlertRead.from_orm(a) for a in new_alerts],
    }


@router.get("", response_model=list[AlertRead])
def list_alerts(
    product_id: uuid.UUID,
    severity: Optional[str] = Query(default=None, pattern="^(high|medium|low)$"),
    unacknowledged_only: bool = Query(default=False),
    limit: int = Query(default=50, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    List alerts for a product. Optionally filter by severity or acknowledgement status.
    Results are ordered by triggered_at DESC (newest first).
    """
    _get_product_or_404(product_id, current_user, session)
    alerts = AlertService.list_alerts(
        product_id, current_user, session, severity, unacknowledged_only, limit
    )
    return [AlertRead.from_orm(a) for a in alerts]


@router.patch("/{alert_id}/acknowledge", response_model=AlertRead)
def acknowledge_alert(
    product_id: uuid.UUID,
    alert_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Mark an alert as acknowledged (resolved). Idempotent — safe to call twice."""
    _get_product_or_404(product_id, current_user, session)
    try:
        alert = AlertService.acknowledge(alert_id, product_id, current_user, session)
        return AlertRead.from_orm(alert)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
