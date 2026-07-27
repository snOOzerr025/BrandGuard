"""
rag/schemas.py
--------------
All Pydantic schemas for the RAG pipeline — input, internal, and output.
Strict typing prevents Gemini hallucinating structure.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Query routing
# ---------------------------------------------------------------------------

class QueryType(str, Enum):
    PURE_VECTOR   = "PURE_VECTOR"    # semantic search in review text
    SQL_AGGREGATE = "SQL_AGGREGATE"  # trend / count / ratio over time
    HYBRID        = "HYBRID"         # both: vector for context + SQL for metrics


class RouteDecision(BaseModel):
    query_type: QueryType
    needs_time_filter: bool = False
    aspect_focus: Optional[str] = None  # e.g. "Battery", "Delivery"
    reasoning: str = ""                 # Gemini's one-line reasoning (for logs)


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

class ReviewChunk(BaseModel):
    review_id: str
    text: str
    rating: Optional[int] = None
    sentiment_label: Optional[str] = None
    similarity: Optional[float] = None   # cosine similarity score (None for SQL fallback)


# ---------------------------------------------------------------------------
# Response — strict schema enforced via Gemini response_schema
# ---------------------------------------------------------------------------

class Citation(BaseModel):
    review_id: str = Field(description="UUID of the source review in the database")
    excerpt: str   = Field(description="Verbatim excerpt (max 120 chars) from the review")


class ChatResponse(BaseModel):
    answer: str = Field(
        description=(
            "Concise, data-backed answer in 2–4 sentences. "
            "No conversational filler. Reference specific aspects and metrics."
        )
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="Reviews that directly support this answer. Min 1, max 5.",
    )
    confidence: str = Field(
        description="'high' | 'medium' | 'low' — based on evidence quality and count"
    )
    query_type_used: str = Field(
        description="Which retrieval path was used: PURE_VECTOR | SQL_AGGREGATE | HYBRID"
    )


# ---------------------------------------------------------------------------
# Chat request (API layer)
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str = Field(min_length=5, max_length=1000)
