"""
rag/gemini_client.py
--------------------
Thin wrapper around the Google GenAI SDK (google-genai, not the deprecated
google-generativeai package).

Responsibilities:
  1. Classify query intent (routing) → RouteDecision
  2. Generate final answer with citations → ChatResponse

Both calls use structured outputs (response_schema + response_mime_type) so
the response is always machine-parseable — no regex or text parsing.

IMPORTANT: This module never sends any review data across user boundaries.
All context is assembled by the caller (ChatService) and passed in here.
"""
from __future__ import annotations

import json
import os
from typing import Optional

from backend.app.rag.schemas import ChatResponse, QueryType, RouteDecision

# ---------------------------------------------------------------------------
# API key — loaded from environment
# ---------------------------------------------------------------------------

_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = "gemini-2.0-flash"


def _get_client():
    """Lazy-init the GenAI client with the API key."""
    from google import genai
    return genai.Client(api_key=_API_KEY)


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

ROUTER_SYSTEM_PROMPT = """
You are BrandGuard's internal query router. Your ONLY job is to classify the
user's question into one of three retrieval strategies:

- PURE_VECTOR: Question is about themes, opinions, complaints, or examples
  from reviews (semantic meaning matters). Use for "what do customers say about X?"
- SQL_AGGREGATE: Question is about metrics, trends, counts, or time-based
  comparisons. Use for "has sentiment improved?", "how many negative reviews?"
- HYBRID: Question needs both — e.g. "why did my score drop last week?"

Output ONLY valid JSON matching the schema. No prose.
""".strip()

ANALYST_SYSTEM_PROMPT = """
You are BrandGuard, an AI brand intelligence analyst. You answer questions
about a business's product reviews with precision and brevity.

Rules:
- Answer in 2–4 sentences maximum. Be direct and data-backed.
- Never add conversational filler ("Great question!", "Sure!", "Certainly!").
- Every claim must be grounded in the provided review chunks.
- Do not invent data that is not in the context.
- Citations must be exact review IDs from the context, not guessed.
- Confidence must be "high" (8+ strong evidence reviews), "medium" (3–7),
  or "low" (fewer than 3 or mixed signals).
""".strip()


# ---------------------------------------------------------------------------
# Route decision schema (for structured output)
# ---------------------------------------------------------------------------

_ROUTE_SCHEMA = {
    "type": "object",
    "properties": {
        "query_type": {
            "type": "string",
            "enum": ["PURE_VECTOR", "SQL_AGGREGATE", "HYBRID"],
        },
        "needs_time_filter": {"type": "boolean"},
        "aspect_focus": {"type": "string", "nullable": True},
        "reasoning": {"type": "string"},
    },
    "required": ["query_type", "needs_time_filter", "reasoning"],
}

_ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "review_id": {"type": "string"},
                    "excerpt": {"type": "string"},
                },
                "required": ["review_id", "excerpt"],
            },
        },
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "query_type_used": {"type": "string"},
    },
    "required": ["answer", "citations", "confidence", "query_type_used"],
}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def classify_query(question: str) -> RouteDecision:
    """
    Classify query intent using Gemini structured output.
    Falls back to PURE_VECTOR if API key is missing or call fails.
    """
    if not _API_KEY:
        return RouteDecision(
            query_type=QueryType.PURE_VECTOR,
            reasoning="No GEMINI_API_KEY — defaulting to PURE_VECTOR",
        )

    try:
        from google import genai
        from google.genai import types

        client = _get_client()
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=ROUTER_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=_ROUTE_SCHEMA,
                temperature=0.0,
            ),
        )
        data = json.loads(response.text)
        return RouteDecision(**data)
    except Exception as exc:
        return RouteDecision(
            query_type=QueryType.PURE_VECTOR,
            reasoning=f"Router error — defaulting to PURE_VECTOR: {exc}",
        )


def generate_answer(
    question: str,
    context_markdown: str,
    sql_summary: Optional[dict] = None,
    query_type: QueryType = QueryType.PURE_VECTOR,
) -> ChatResponse:
    """
    Generate a structured brand intelligence answer using Gemini 2.0 Flash.

    Args:
        question:         The user's original question.
        context_markdown: Formatted review chunks assembled by ContextBuilder.
        sql_summary:      Optional SQL aggregation dict (for metric routes).
        query_type:       Which retrieval path was used.

    Returns:
        ChatResponse with answer, citations, confidence, query_type_used.
    """
    if not _API_KEY:
        return ChatResponse(
            answer=(
                "Gemini API key not configured. "
                "Set GEMINI_API_KEY in your .env to enable Ask BrandGuard."
            ),
            citations=[],
            confidence="low",
            query_type_used=query_type.value,
        )

    sql_block = ""
    if sql_summary:
        sql_block = (
            f"\n\n### Aggregated Metrics\n"
            f"```json\n{json.dumps(sql_summary, indent=2)}\n```"
        )

    prompt = (
        f"### User Question\n{question}\n\n"
        f"{context_markdown}"
        f"{sql_block}\n\n"
        f"### Your Task\n"
        f"Answer the question using ONLY the evidence above. "
        f"Return JSON with: answer, citations (list of review_id + excerpt), "
        f"confidence (high/medium/low), query_type_used."
    )

    try:
        from google import genai
        from google.genai import types

        client = _get_client()
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=ANALYST_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=_ANSWER_SCHEMA,
                temperature=0.2,
                max_output_tokens=800,
            ),
        )
        data = json.loads(response.text)
        data["query_type_used"] = query_type.value  # enforce ground truth
        return ChatResponse(**data)
    except Exception as exc:
        return ChatResponse(
            answer=f"Analysis error: {exc}",
            citations=[],
            confidence="low",
            query_type_used=query_type.value,
        )
