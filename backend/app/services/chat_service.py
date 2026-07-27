"""
services/chat_service.py
-------------------------
Orchestrates the full RAG pipeline for a single chat turn.

Pipeline order (do NOT reorder — each step feeds the next):
  1. Classify intent → RouteDecision (Gemini structured output)
  2. Retrieve context → list[ReviewChunk] (pgvector or SQL fallback)
  3. SQL aggregation → dict (only for SQL_AGGREGATE / HYBRID routes)
  4. Build context block → Markdown string
  5. Generate answer → ChatResponse (Gemini structured output)
  6. Persist QueryLog → async background task (non-blocking)

GUARANTEES:
  - Every retrieval call is scoped by user_id + product_id
  - QueryLog insert never blocks the response path
  - If Gemini is unavailable, a structured fallback is returned (no 500 errors)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from backend.app.ml.embeddings.encoder import ReviewEncoder
from backend.app.models.product import Product
from backend.app.models.query_log import QueryLog
from backend.app.models.user import User
from backend.app.rag import gemini_client
from backend.app.rag.context_builder import build_context
from backend.app.rag.retriever import get_retriever
from backend.app.rag.schemas import ChatResponse, QueryType, RouteDecision
from backend.app.services.insight_service import InsightService

_encoder: Optional[ReviewEncoder] = None


def _get_encoder() -> ReviewEncoder:
    global _encoder
    if _encoder is None:
        _encoder = ReviewEncoder()
    return _encoder


def _sql_aggregate(
    product_id: uuid.UUID,
    user: User,
    session: Session,
) -> dict:
    """
    Pull pre-computed aggregated metrics from SentimentResult rows.
    Never recalculates sentiment — reads stored results only.
    """
    summary = InsightService.get_overall_sentiment(product_id, user, session)
    aspect_data = InsightService.get_aspect_summary(product_id, user, session)
    top_aspects = sorted(aspect_data, key=lambda x: -abs(x["sentiment_score"]))[:3]
    return {
        "total_mentions": summary["total"],
        "positive_ratio_pct": summary.get("positive_ratio", 0.0),
        "negative_ratio_pct": summary.get("negative_ratio", 0.0),
        "sentiment_score": summary.get("sentiment_score", 0.0),
        "top_aspects": [
            {"aspect": a["aspect"], "score": a["sentiment_score"]}
            for a in top_aspects
        ],
    }


def run_chat(
    question: str,
    product_id: uuid.UUID,
    user: User,
    session: Session,
    background_log_fn,   # callable — injected by route to run async
) -> ChatResponse:
    """
    Full RAG pipeline for one chat turn.

    Args:
        question:          User's natural language question.
        product_id:        Product being queried (scopes all retrieval).
        user:              Authenticated user (scopes all retrieval).
        session:           DB session.
        background_log_fn: BackgroundTasks.add_task — used for async QueryLog.

    Returns:
        ChatResponse with answer, citations, confidence, query_type_used.
    """
    import time
    t_start = time.monotonic()

    # 1. Classify intent
    route: RouteDecision = gemini_client.classify_query(question)

    # 2. Embed query for vector retrieval
    chunks = []
    if route.query_type in (QueryType.PURE_VECTOR, QueryType.HYBRID):
        encoder = _get_encoder()
        query_vec = encoder.encode([question])[0].tolist()
        retriever = get_retriever(session)
        chunks = retriever.retrieve(
            query_embedding=query_vec,
            user_id=user.id,
            product_id=product_id,
            top_k=15,
            aspect_focus=route.aspect_focus,
        )

    # 3. SQL aggregation (for metric/trend questions)
    sql_summary: Optional[dict] = None
    if route.query_type in (QueryType.SQL_AGGREGATE, QueryType.HYBRID):
        sql_summary = _sql_aggregate(product_id, user, session)

    # 4. Pre-computed aspect summary (always included as context)
    aspect_summary = InsightService.get_aspect_summary(product_id, user, session)

    # Fetch product name for context header
    product = session.exec(
        select(Product).where(Product.id == product_id, Product.user_id == user.id)
    ).first()
    product_name = product.name if product else str(product_id)

    # 5. Build Markdown context
    context_md = build_context(
        chunks=chunks,
        product_name=product_name,
        aspect_summary=aspect_summary or None,
        sql_summary=sql_summary,
    )

    # 6. Generate answer via Gemini
    response: ChatResponse = gemini_client.generate_answer(
        question=question,
        context_markdown=context_md,
        sql_summary=sql_summary,
        query_type=route.query_type,
    )

    latency_ms = int((time.monotonic() - t_start) * 1000)

    # 7. Async QueryLog insert — does NOT block the response
    def _log():
        import json
        from sqlmodel import Session as S
        from backend.app.db.session import engine

        with S(engine) as bg_session:
            log = QueryLog(
                user_id=user.id,
                product_id=product_id,
                question=question,
                answer=response.answer,
                source_review_ids=json.dumps(
                    [c.review_id for c in response.citations]
                ),
                model_used=gemini_client.MODEL_NAME,
                latency_ms=latency_ms,
            )
            bg_session.add(log)
            bg_session.commit()

    background_log_fn(_log)

    return response
