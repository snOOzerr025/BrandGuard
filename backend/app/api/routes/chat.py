"""
api/routes/chat.py
-------------------
POST /products/{product_id}/chat — Ask BrandGuard endpoint.

Single endpoint, single purpose: receive a question, run the RAG pipeline,
return a structured answer with citations.

QueryLog insert happens in a BackgroundTask — response is never held waiting
for the DB write to complete.
"""
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlmodel import Session, select

from backend.app.auth.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models.product import Product
from backend.app.models.user import User
from backend.app.rag.schemas import ChatRequest, ChatResponse
from backend.app.services.chat_service import run_chat

router = APIRouter(prefix="/products/{product_id}/chat", tags=["ask-brandguard"])


@router.post("", response_model=ChatResponse)
def ask_brandguard(
    product_id: uuid.UUID,
    payload: ChatRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """
    Ask BrandGuard a natural language question about a product's reviews.

    Routes to the correct retrieval path automatically:
    - Semantic questions → pgvector similarity search
    - Metric/trend questions → SQL aggregation on stored SentimentResult rows
    - Mixed questions → both

    Returns a structured response with answer, review citations, and confidence.
    QueryLog is persisted asynchronously — this endpoint never blocks on DB writes.
    """
    # Verify product ownership
    product = session.exec(
        select(Product).where(
            Product.id == product_id,
            Product.user_id == current_user.id,
        )
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    response = run_chat(
        question=payload.question,
        product_id=product_id,
        user=current_user,
        session=session,
        background_log_fn=background_tasks.add_task,
    )
    return response
