"""
rag/retriever.py
----------------
Review retrieval layer — two implementations:

  PgVectorRetriever  : Production. Uses pgvector cosine similarity.
                       Every query has a hard WHERE user_id + product_id clause.

  FallbackRetriever  : Tests / SQLite. Returns recent reviews ordered by
                       ingested_at DESC. No vector ops — SQLite can't do them.

The `get_retriever()` factory auto-detects the dialect and returns the right one.

ARCHITECTURAL RULE: Vector similarity is NEVER used for time-series metrics.
  Time-based questions must go through SQLRetriever (see retriever.py).
  Only this module handles semantic retrieval.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlmodel import Session, select, text

from backend.app.models.review import Review
from backend.app.models.sentiment_result import SentimentResult
from backend.app.rag.schemas import ReviewChunk


class PgVectorRetriever:
    """
    Production retriever using pgvector's <=> cosine distance operator.
    Strict user + product scoping enforced at the SQL level — not in Python.
    """

    def __init__(self, session: Session):
        self.session = session

    def retrieve(
        self,
        query_embedding: list[float],
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        top_k: int = 15,
        aspect_focus: Optional[str] = None,
    ) -> list[ReviewChunk]:
        """
        Find top-k reviews most similar to the query embedding.
        Hard WHERE user_id + product_id — no data leaks across users.

        If aspect_focus is set, filter SentimentResult rows to only reviews
        that have a mention of that aspect (improves relevance precision).
        """
        vec_str = f"[{','.join(str(x) for x in query_embedding)}]"

        if aspect_focus:
            # Narrow to reviews that mention the target aspect
            aspect_review_ids = self.session.exec(
                select(SentimentResult.review_id)
                .where(
                    SentimentResult.user_id == user_id,
                    SentimentResult.product_id == product_id,
                    SentimentResult.aspect == aspect_focus,
                )
                .limit(100)
            ).all()

            if not aspect_review_ids:
                aspect_focus = None  # fall through to unrestricted search

        base_sql = f"""
            SELECT
                id::text          AS review_id,
                text              AS text,
                rating            AS rating,
                sentiment_label   AS sentiment_label,
                1 - (embedding <=> '{vec_str}') AS similarity
            FROM reviews
            WHERE user_id = '{user_id}'
              AND product_id = '{product_id}'
              AND embedding IS NOT NULL
            {"AND id = ANY(ARRAY[" + ",".join(f"'{r}'::uuid" for r in aspect_review_ids) + "])" if aspect_focus and aspect_review_ids else ""}
            ORDER BY embedding <=> '{vec_str}'
            LIMIT {top_k}
        """

        rows = self.session.exec(text(base_sql)).all()
        return [
            ReviewChunk(
                review_id=str(row.review_id),
                text=row.text,
                rating=row.rating,
                sentiment_label=row.sentiment_label,
                similarity=round(float(row.similarity), 4),
            )
            for row in rows
        ]


class FallbackRetriever:
    """
    SQLite-compatible retriever for tests.
    Returns recent reviews for the product — no vector ops.
    Similarity is set to None (not a vector retrieval).
    """

    def __init__(self, session: Session):
        self.session = session

    def retrieve(
        self,
        query_embedding: list[float],  # ignored
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        top_k: int = 15,
        aspect_focus: Optional[str] = None,
    ) -> list[ReviewChunk]:
        query = (
            select(Review)
            .where(Review.user_id == user_id, Review.product_id == product_id)
            .order_by(Review.ingested_at.desc())
            .limit(top_k)
        )
        reviews = self.session.exec(query).all()
        return [
            ReviewChunk(
                review_id=str(r.id),
                text=r.text,
                rating=r.rating,
                sentiment_label=r.sentiment_label,
                similarity=None,
            )
            for r in reviews
        ]


def get_retriever(session: Session) -> PgVectorRetriever | FallbackRetriever:
    """
    Factory: returns PgVectorRetriever for Postgres, FallbackRetriever for SQLite.
    Detection is based on the engine dialect name — no config flag needed.
    """
    dialect = session.get_bind().dialect.name
    if dialect == "postgresql":
        return PgVectorRetriever(session)
    return FallbackRetriever(session)
