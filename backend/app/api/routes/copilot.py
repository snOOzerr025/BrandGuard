"""
api/routes/copilot.py — Production RAG Copilot Endpoint
-------------------------------------------------------
POST /api/v1/copilot/ask
Executes Intent Router -> SQL Aggregator + Hybrid RRF (pgvector + tsvector) ->
Cross-Encoder -> Gemini 2.0 Flash -> Post-generation Citation & Claim Verifier.
Response SLA: <1,250ms (p95).
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from backend.app.auth.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models.domain import Product, User
from backend.app.rag.rag_copilot import RAGCopilotEngine
from backend.app.rag.schemas import CopilotAskRequest, CopilotStructuredResponse

router = APIRouter(prefix="/copilot", tags=["copilot"])

_copilot_engine: Optional[RAGCopilotEngine] = None


def get_copilot_engine() -> RAGCopilotEngine:
    global _copilot_engine
    if _copilot_engine is None:
        _copilot_engine = RAGCopilotEngine()
    return _copilot_engine


@router.post("/ask", response_model=CopilotStructuredResponse, status_code=status.HTTP_200_OK)
def ask_copilot(
    payload: CopilotAskRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    engine: RAGCopilotEngine = Depends(get_copilot_engine),
) -> CopilotStructuredResponse:
    """
    Submits a query to the BrandGuard Copilot.
    Enforces tenant isolation, intent routing, hybrid search, and citation verification.
    """
    # 1. Verify product ownership
    product = session.exec(
        select(Product).where(
            Product.id == payload.product_id,
            Product.user_id == current_user.id,
        )
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {payload.product_id} not found or not owned by user.",
        )

    # 2. Execute RAG Copilot query pipeline
    response = engine.answer_query(
        product_id=payload.product_id,
        user_id=current_user.id,
        query=payload.query,
        session=session,
        filters=payload.filters,
    )

    return response
