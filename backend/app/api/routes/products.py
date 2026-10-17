"""
api/routes/products.py
-----------------------
Product management endpoints — create, list, get.
All routes require authentication and are scoped to the authenticated user.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from backend.app.auth.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models.product import Product
from backend.app.models.user import User
from backend.app.schemas.product import ProductCreate, ProductRead

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Product:
    """Create a new product/brand to track reviews for."""
    product = Product(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        source=payload.source,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.get("", response_model=list[ProductRead])
def list_products(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[Product]:
    """List all products owned by the authenticated user."""
    return session.exec(
        select(Product).where(Product.user_id == current_user.id)
    ).all()


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Product:
    """Get a specific product. Returns 404 if not found or not owned by user."""
    product = session.exec(
        select(Product).where(
            Product.id == product_id,
            Product.user_id == current_user.id,
        )
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


@router.get("/{product_id}/kpis")
def get_product_kpis(
    product_id: uuid.UUID,
    window_days: int = 30,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Returns executive KPIs, Net Sentiment (Chattermill formula), Brand Health Score,
    and 8-dimension diverging aspect matrix with Leave-One-Out star impact.
    """
    get_product(product_id, session, current_user)
    from backend.app.services.product_kpi_service import ProductKpiService
    return ProductKpiService.get_product_kpis(
        product_id=product_id,
        user=current_user,
        session=session,
        window_days=window_days,
    )


@router.get("/{product_id}/themes")
def get_product_themes(
    product_id: uuid.UUID,
    macro_aspect: str = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Returns HDBSCAN emergent micro-themes sorted by negative Star Impact drag.
    """
    get_product(product_id, session, current_user)
    from backend.app.services.product_kpi_service import ProductKpiService
    return ProductKpiService.get_product_themes(
        product_id=product_id,
        user=current_user,
        session=session,
        macro_aspect=macro_aspect,
    )


@router.get("/{product_id}/anomalies")
def get_product_anomalies(
    product_id: uuid.UUID,
    window_days: int = 90,
    severity: str = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Returns daily deseasonalized EWMA series with 2-sigma and 3-sigma bands,
    plus click-to-triage anomaly alerts with medoid evidence.
    """
    get_product(product_id, session, current_user)
    from backend.app.services.product_kpi_service import ProductKpiService
    return ProductKpiService.get_product_anomalies(
        product_id=product_id,
        user=current_user,
        session=session,
        window_days=window_days,
        severity=severity,
    )

