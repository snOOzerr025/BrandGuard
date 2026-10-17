"""
rag/schemas.py
--------------
All Pydantic schemas for the RAG pipeline — input, internal, and output.
Strict typing prevents Gemini hallucinating structure.
"""
from __future__ import annotations

import uuid
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
# SOTA Copilot Structured Response & Post-Generation Verification Schemas
# ---------------------------------------------------------------------------

class CitedClaim(BaseModel):
    statement: str = Field(description="Single factual claim synthesized from evidence.")
    cited_review_ids: list[str] = Field(
        description="Exact UUIDs from <verified_review_evidence> supporting this claim."
    )
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)


class CopilotStructuredResponse(BaseModel):
    executive_summary: str = Field(
        description="Concise 2-4 sentence executive diagnosis strictly grounded in evidence."
    )
    quantitative_metrics_used: list[str] = Field(
        default_factory=list,
        description="Deterministic metrics injected from <deterministic_sql_facts>.",
    )
    claims: list[CitedClaim] = Field(
        default_factory=list,
        description="Claims verified with exact source review UUID citations.",
    )
    insufficient_evidence_warning: bool = Field(
        default=False,
        description="True if available reviews do not provide sufficient evidence.",
    )
    latency_ms: float = Field(default=0.0)


class CopilotAskFilters(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    aspect: Optional[str] = None


class CopilotAskRequest(BaseModel):
    product_id: uuid.UUID
    query: str = Field(min_length=3, max_length=1000)
    filters: Optional[CopilotAskFilters] = None


# ---------------------------------------------------------------------------
# Chat request (Legacy API layer compatibility)
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
