"""
rag/context_builder.py
-----------------------
Assembles the Markdown context block passed to Gemini.

ARCHITECTURAL RULE: Context is assembled here — Gemini never sees raw SQL
results or Python dicts. Everything is formatted with clear Markdown
delimiters so Gemini can parse structure without guessing.

Format example:
  ### Product Overview
  ...

  ### Aggregated Sentiment
  ...

  ### Retrieved Review Chunks
  [1] review_id=abc... | rating=2 | label=negative
  "The battery drained in 2 hours..."
  ...
"""
from __future__ import annotations

from typing import Optional

from backend.app.rag.schemas import ReviewChunk


MAX_CHUNK_CHARS = 300  # truncate very long reviews to keep context tight


def build_context(
    chunks: list[ReviewChunk],
    product_name: str,
    aspect_summary: Optional[list[dict]] = None,
    sql_summary: Optional[dict] = None,
) -> str:
    """
    Assemble Markdown context for Gemini from retrieval results.

    Args:
        chunks:          Retrieved review chunks (from vector or fallback retriever).
        product_name:    Name of the product being analysed.
        aspect_summary:  Optional pre-computed aspect breakdown from InsightService.
        sql_summary:     Optional SQL aggregation metrics (for trend / count queries).

    Returns:
        Formatted Markdown string ready to inject into the Gemini prompt.
    """
    sections: list[str] = []

    # 1. Product header
    sections.append(f"### Product Under Analysis\n**{product_name}**")

    # 2. Aspect summary (pre-computed — no recomputation at chat time)
    if aspect_summary:
        lines = ["### Pre-Computed Aspect Summary"]
        for asp in aspect_summary[:8]:  # cap at 8 aspects
            score = asp.get("sentiment_score", 0.0)
            sign = "+" if score >= 0 else ""
            lines.append(
                f"- **{asp['aspect']}**: {asp['mention_count']} mentions | "
                f"score {sign}{score:.2f} | "
                f"{asp['positive_count']}P / {asp['negative_count']}N / {asp['neutral_count']}Neu"
            )
        sections.append("\n".join(lines))

    # 3. SQL metrics (for trend / aggregate queries)
    if sql_summary:
        lines = ["### Aggregated Metrics (SQL)"]
        for k, v in sql_summary.items():
            lines.append(f"- **{k}**: {v}")
        sections.append("\n".join(lines))

    # 4. Retrieved review chunks — the core evidence
    if chunks:
        lines = ["### Retrieved Review Chunks"]
        for i, chunk in enumerate(chunks, start=1):
            text = chunk.text[:MAX_CHUNK_CHARS]
            if len(chunk.text) > MAX_CHUNK_CHARS:
                text += "…"
            sim_str = f" | similarity={chunk.similarity:.3f}" if chunk.similarity is not None else ""
            rating_str = f" | rating={chunk.rating}/5" if chunk.rating else ""
            label_str = f" | label={chunk.sentiment_label}" if chunk.sentiment_label else ""
            lines.append(
                f"[{i}] review_id={chunk.review_id}{rating_str}{label_str}{sim_str}\n"
                f'"{text}"'
            )
        sections.append("\n\n".join(lines))
    else:
        sections.append(
            "### Retrieved Review Chunks\n"
            "_No reviews found for this query scope. "
            "Ingest and analyze reviews first._"
        )

    return "\n\n---\n\n".join(sections)
