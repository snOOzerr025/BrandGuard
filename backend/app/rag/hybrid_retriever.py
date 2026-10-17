"""
rag/hybrid_retriever.py — Concurrent Dense (pgvector) + Sparse (tsvector) RRF Retrieval
---------------------------------------------------------------------------------------
Implements two-stage candidate generation:
1. Parallel execution of Dense cosine search (top-30) and Full-Text tsvector search (top-30).
2. Adaptive pgvector HNSW iterative scan for large tenants vs B-Tree Materialized CTE for small tenants.
3. Fusion via Reciprocal Rank Fusion (RRF, k=60):
     RRF_Score(r) = 1/(k + rank_dense(r)) + 1/(k + rank_sparse(r))
4. Outputs top-40 deduplicated candidates for Cross-Encoder reranking.
"""
import asyncio
import uuid
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import desc, func, text
from sqlmodel import Session, select

from backend.app.models.domain import Review


class HybridRRFRetriever:
    """
    Executes tenant-isolated concurrent Dense + Sparse search fused via RRF (k=60).
    """

    def __init__(self, k_rrf: int = 60, candidate_limit: int = 30):
        self.k_rrf = k_rrf
        self.candidate_limit = candidate_limit

    def retrieve_sync(
        self,
        session: Session,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        query_text: str,
        query_embedding: list[float],
        tenant_review_count: int,
    ) -> List[Review]:
        """
        Synchronous execution of Dense + Sparse search with RRF fusion.
        """
        dialect = session.bind.dialect.name if session.bind else "sqlite"

        if dialect == "postgresql":
            # 1. Dense search
            dense_hits = self._fetch_dense_sync(
                session, user_id, product_id, query_embedding, tenant_review_count
            )
            # 2. Sparse search
            sparse_hits = self._fetch_sparse_sync(session, user_id, product_id, query_text)

            # 3. Fuse via RRF
            return self._fuse_rrf(dense_hits, sparse_hits)
        else:
            # SQLite fallback for offline tests: filter by tenant and text matches
            stmt = (
                select(Review)
                .where(Review.user_id == user_id, Review.product_id == product_id)
                .order_by(desc(Review.reviewed_at))
                .limit(40)
            )
            raw = list(session.exec(stmt).all())
            return [r if isinstance(r, Review) else r[0] for r in raw]

    async def retrieve_async(
        self,
        session: Any,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        query_text: str,
        query_embedding: list[float],
        tenant_review_count: int,
    ) -> List[Review]:
        """
        Asynchronous concurrent execution of Dense + Sparse search via asyncio.gather.
        """
        dialect = session.bind.dialect.name if session.bind else "postgresql"

        if dialect == "postgresql":
            async def fetch_dense():
                if tenant_review_count < 2000:
                    cte = (
                        select(Review.id)
                        .where(Review.user_id == user_id, Review.product_id == product_id)
                        .cte("tenant_scope", materialized=True)
                    )
                    stmt = (
                        select(Review)
                        .join(cte, Review.id == cte.c.id)
                        .order_by(Review.embedding.cosine_distance(query_embedding))
                        .limit(self.candidate_limit)
                    )
                else:
                    await session.execute(text("SET LOCAL hnsw.iterative_scan = relaxed_order"))
                    await session.execute(text("SET LOCAL hnsw.ef_search = 100"))
                    await session.execute(text("SET LOCAL hnsw.max_scan_tuples = 20000"))
                    inner = (
                        select(
                            Review.id,
                            Review.embedding.cosine_distance(query_embedding).label("dist"),
                        )
                        .where(Review.user_id == user_id, Review.product_id == product_id)
                        .order_by(Review.embedding.cosine_distance(query_embedding))
                        .limit(self.candidate_limit)
                        .subquery()
                    )
                    stmt = select(Review).join(inner, Review.id == inner.c.id).order_by(inner.c.dist + 0)

                res = await session.execute(stmt)
                return res.scalars().all()

            async def fetch_sparse():
                ts_q = func.websearch_to_tsquery("english", query_text)
                stmt = (
                    select(Review)
                    .where(
                        Review.user_id == user_id,
                        Review.product_id == product_id,
                        Review.search_vector.op("@@")(ts_q),
                    )
                    .order_by(desc(func.ts_rank_cd(Review.search_vector, ts_q)))
                    .limit(self.candidate_limit)
                )
                res = await session.execute(stmt)
                return res.scalars().all()

            dense_hits, sparse_hits = await asyncio.gather(fetch_dense(), fetch_sparse())
            return self._fuse_rrf(list(dense_hits), list(sparse_hits))
        else:
            stmt = (
                select(Review)
                .where(Review.user_id == user_id, Review.product_id == product_id)
                .order_by(desc(Review.reviewed_at))
                .limit(40)
            )
            res = await session.execute(stmt)
            return list(res.scalars().all())

    def _fetch_dense_sync(
        self,
        session: Session,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        query_embedding: list[float],
        tenant_review_count: int,
    ) -> List[Review]:
        if tenant_review_count < 2000:
            cte = (
                select(Review.id)
                .where(Review.user_id == user_id, Review.product_id == product_id)
                .cte("tenant_scope")
                .prefix_with("MATERIALIZED")
            )
            stmt = (
                select(Review)
                .join(cte, Review.id == cte.c.id)
                .order_by(Review.embedding.cosine_distance(query_embedding))
                .limit(self.candidate_limit)
            )
        else:
            session.execute(text("SET LOCAL hnsw.iterative_scan = relaxed_order"))
            session.execute(text("SET LOCAL hnsw.ef_search = 100"))
            session.execute(text("SET LOCAL hnsw.max_scan_tuples = 20000"))
            inner = (
                select(
                    Review.id,
                    Review.embedding.cosine_distance(query_embedding).label("dist"),
                )
                .where(Review.user_id == user_id, Review.product_id == product_id)
                .order_by(Review.embedding.cosine_distance(query_embedding))
                .limit(self.candidate_limit)
                .subquery()
            )
            stmt = select(Review).join(inner, Review.id == inner.c.id).order_by(inner.c.dist + 0)

        raw = list(session.exec(stmt).all())
        return [r if isinstance(r, Review) else r[0] for r in raw]

    def _fetch_sparse_sync(
        self,
        session: Session,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        query_text: str,
    ) -> List[Review]:
        try:
            ts_q = func.websearch_to_tsquery("english", query_text)
            stmt = (
                select(Review)
                .where(
                    Review.user_id == user_id,
                    Review.product_id == product_id,
                    Review.search_vector.op("@@")(ts_q),
                )
                .order_by(desc(func.ts_rank_cd(Review.search_vector, ts_q)))
                .limit(self.candidate_limit)
            )
            raw = list(session.exec(stmt).all())
            return [r if isinstance(r, Review) else r[0] for r in raw]
        except Exception:
            # Fallback for empty/special tsquery tokens
            return []

    def _fuse_rrf(self, dense_hits: List[Review], sparse_hits: List[Review]) -> List[Review]:
        """Reciprocal Rank Fusion over dense and sparse candidate lists."""
        rrf_scores: Dict[uuid.UUID, float] = {}
        review_map: Dict[uuid.UUID, Review] = {}

        for rank, rev in enumerate(dense_hits, start=1):
            rrf_scores[rev.id] = rrf_scores.get(rev.id, 0.0) + (1.0 / (self.k_rrf + rank))
            review_map[rev.id] = rev

        for rank, rev in enumerate(sparse_hits, start=1):
            rrf_scores[rev.id] = rrf_scores.get(rev.id, 0.0) + (1.0 / (self.k_rrf + rank))
            review_map[rev.id] = rev

        sorted_uuids = sorted(rrf_scores.keys(), key=lambda uid: rrf_scores[uid], reverse=True)
        return [review_map[uid] for uid in sorted_uuids[:40]]
