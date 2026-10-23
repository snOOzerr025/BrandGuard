"""
domain.py — BrandGuard Master Domain Models
-------------------------------------------
Production SQLModel (SQLAlchemy 2.0) schema incorporating:
- Strict multi-tenant foreign keys (users -> products -> reviews / sentiments / alerts)
- pgvector HNSW cosine similarity indexes for dense representations
- PostgreSQL tsvector full-text search with generated columns and GIN indexes
- JSONB storage for terms, citations, and metadata
- Check constraints and tenant isolation indices
"""
import hashlib
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy.types import UserDefinedType

    class Vector(UserDefinedType):  # type: ignore
        cache_ok = True

        def __init__(self, dim: int):
            self.dim = dim

        def get_col_spec(self, **kw: Any) -> str:
            return f"VECTOR({self.dim})"

        def bind_processor(self, dialect: Any) -> Any:
            def process(value: Any) -> Any:
                if isinstance(value, (list, tuple)):
                    import json
                    return json.dumps(value)
                return value
            return process

        def result_processor(self, dialect: Any, coltype: Any) -> Any:
            def process(value: Any) -> Any:
                if isinstance(value, str):
                    import json
                    try:
                        return json.loads(value)
                    except Exception:
                        return value
                return value
            return process


# Cross-dialect JSON: JSONB in Postgres, standard JSON in SQLite
JSONVariant = JSON().with_variant(JSONB, "postgresql")


class PlanTier(str, Enum):
    STARTER = "STARTER"
    GROWTH = "GROWTH"
    ENTERPRISE = "ENTERPRISE"


class JobState(str, Enum):
    PENDING = "PENDING"
    EXTRACTING_ASPECTS = "EXTRACTING_ASPECTS"
    EMBEDDING = "EMBEDDING"
    CLUSTERING = "CLUSTERING"
    DETECTING_ANOMALIES = "DETECTING_ANOMALIES"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PolarityLabel(str, Enum):
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"


class SeverityTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    email: str = Field(index=True, unique=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    organization_name: str = Field(default="Personal", max_length=255)
    plan_tier: PlanTier = Field(default=PlanTier.GROWTH)
    is_active: bool = Field(default=True)
    slack_webhook_url: Optional[str] = Field(default=None, max_length=512)
    alert_email: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )


class Product(SQLModel, table=True):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("user_id", "sku", name="uq_product_tenant_sku"),
        Index("ix_products_user_id", "user_id"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=1024)
    sku: str = Field(
        default_factory=lambda: f"SKU-{uuid.uuid4().hex[:8].upper()}",
        max_length=128,
    )
    source: str = Field(default="csv_upload", max_length=64)
    external_asin: Optional[str] = Field(default=None, max_length=64)
    trustpilot_business_unit_id: Optional[str] = Field(default=None, max_length=64)
    review_count: int = Field(default=0, nullable=False)
    brand_health_score: float = Field(default=100.0, nullable=False)
    net_sentiment: float = Field(default=0.0, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )


class IngestionJob(SQLModel, table=True):
    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        Index("ix_ingestion_jobs_user_product", "user_id", "product_id"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    celery_task_id: Optional[str] = Field(default=None, index=True, max_length=128)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    product_id: uuid.UUID = Field(foreign_key="products.id", nullable=False)
    state: JobState = Field(default=JobState.PENDING, nullable=False)
    total_reviews: int = Field(default=0, nullable=False)
    processed_reviews: int = Field(default=0, nullable=False)
    error_detail: Optional[str] = Field(default=None, sa_column=Column(Text))
    metadata_payload: dict = Field(default_factory=dict, sa_column=Column(JSONVariant))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            onupdate=func.now(),
            server_default=func.now(),
        ),
    )


class Review(SQLModel, table=True):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", "external_review_id", name="uq_review_dedup"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_bounds"),
        Index("ix_reviews_tenant_product_date", "user_id", "product_id", "reviewed_at"),
        Index(
            "ix_reviews_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 128},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "ix_reviews_search_vector_gin",
            "search_vector",
            postgresql_using="gin",
        ),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    product_id: uuid.UUID = Field(foreign_key="products.id", nullable=False)
    job_id: Optional[uuid.UUID] = Field(default=None, foreign_key="ingestion_jobs.id")
    external_review_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        max_length=128,
        nullable=False,
    )
    source_channel: str = Field(default="CSV", max_length=64)
    source: Optional[str] = Field(default=None, max_length=64)
    rating: int = Field(default=5, nullable=False)
    title: Optional[str] = Field(default=None, max_length=512)
    body: str = Field(sa_column=Column(Text, nullable=False))
    sentiment_label: Optional[str] = Field(default=None, max_length=32)
    verified_purchase: bool = Field(default=True)
    has_rating_discrepancy: bool = Field(default=False, index=True)
    micro_cluster_id: Optional[uuid.UUID] = Field(default=None)
    embedding: Optional[list[float]] = Field(
        default=None,
        sa_column=Column(Vector(384)),
    )
    search_vector: Optional[str] = Field(
        default=None,
        sa_column=Column(
            TSVECTOR,
            Computed("to_tsvector('english', coalesce(title, '') || ' ' || body)", persisted=True),
        ),
    )
    reviewed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    def __init__(self, **data: Any):
        if "text" in data and "body" not in data:
            data["body"] = data.pop("text")
        if "source" in data and "source_channel" not in data:
            data["source_channel"] = data["source"]
        if "rating" not in data or data["rating"] is None:
            data["rating"] = 5
        if "external_review_id" not in data:
            data["external_review_id"] = uuid.uuid4().hex
        super().__init__(**data)

    @property
    def text(self) -> str:
        return self.body

    @text.setter
    def text(self, val: str) -> None:
        self.body = val


class SentimentResult(SQLModel, table=True):
    __tablename__ = "sentiment_results"
    __table_args__ = (
        Index("ix_sentiment_tenant_product_aspect", "user_id", "product_id", "aspect_category"),
        Index("ix_sentiment_review_id", "review_id"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    review_id: uuid.UUID = Field(foreign_key="reviews.id", nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    product_id: uuid.UUID = Field(foreign_key="products.id", nullable=False)
    aspect_category: str = Field(max_length=64, nullable=False)
    extracted_span: Optional[str] = Field(default=None, max_length=255)
    is_implicit: bool = Field(default=False, nullable=False)
    polarity: PolarityLabel = Field(nullable=False)
    confidence: float = Field(nullable=False)
    numeric_score: float = Field(nullable=False)  # +1.0 Positive, 0.0 Neutral, -1.0 Negative
    model_version: Optional[str] = Field(default="v2.0", max_length=64)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    def __init__(self, **data: Any):
        if "aspect" in data and "aspect_category" not in data:
            data["aspect_category"] = data.pop("aspect")
        if "polarity" in data and isinstance(data["polarity"], str):
            val = data["polarity"].capitalize()
            try:
                data["polarity"] = PolarityLabel(val)
            except ValueError:
                data["polarity"] = PolarityLabel.NEUTRAL
        if "numeric_score" not in data:
            pol = data.get("polarity")
            if pol == PolarityLabel.POSITIVE or str(pol).lower() == "positive":
                data["numeric_score"] = 1.0
            elif pol == PolarityLabel.NEGATIVE or str(pol).lower() == "negative":
                data["numeric_score"] = -1.0
            else:
                data["numeric_score"] = 0.0
        if "computed_at" in data and "created_at" not in data:
            data["created_at"] = data.pop("computed_at")
        super().__init__(**data)

    @property
    def aspect(self) -> str:
        return self.aspect_category

    @aspect.setter
    def aspect(self, val: str) -> None:
        self.aspect_category = val

    @property
    def computed_at(self) -> datetime:
        return self.created_at

    @computed_at.setter
    def computed_at(self, val: datetime) -> None:
        self.created_at = val


class MicroCluster(SQLModel, table=True):
    __tablename__ = "micro_clusters"
    __table_args__ = (
        Index("ix_micro_clusters_tenant_product", "user_id", "product_id", "macro_aspect"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    product_id: uuid.UUID = Field(foreign_key="products.id", nullable=False)
    macro_aspect: str = Field(max_length=64, nullable=False)
    hdbscan_label: int = Field(nullable=False)
    theme_label: str = Field(max_length=255, nullable=False)
    top_ctfidf_terms: list[str] = Field(default_factory=list, sa_column=Column(JSONVariant))
    evidence_review_ids: list[str] = Field(default_factory=list, sa_column=Column(JSONVariant))
    review_volume: int = Field(default=0, nullable=False)
    net_sentiment: float = Field(default=0.0, nullable=False)
    star_impact_delta: float = Field(default=0.0, nullable=False)
    centroid_embedding: Optional[list[float]] = Field(
        default=None,
        sa_column=Column(Vector(384)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_tenant_product_created", "user_id", "product_id", "created_at"),
        UniqueConstraint("user_id", "product_id", "dedup_fingerprint", name="uq_alert_dedup_window"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    product_id: uuid.UUID = Field(foreign_key="products.id", nullable=False)
    aspect_category: str = Field(max_length=64, nullable=False)
    micro_cluster_id: Optional[uuid.UUID] = Field(default=None)
    severity: SeverityTier = Field(nullable=False)
    alert_type: str = Field(max_length=64, nullable=False)
    z_score: float = Field(default=0.0, nullable=False)
    baseline_mean: float = Field(default=0.0, nullable=False)
    current_value: float = Field(default=0.0, nullable=False)
    star_impact: float = Field(default=0.0, nullable=False)
    support_count: int = Field(default=0, nullable=False)
    message: Optional[str] = Field(default=None, sa_column=Column(Text))
    evidence_review_ids: list[str] = Field(default_factory=list, sa_column=Column(JSONVariant))
    dedup_fingerprint: str = Field(max_length=128, nullable=False)
    is_acknowledged: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    def __init__(self, **data: Any):
        if "aspect" in data and "aspect_category" not in data:
            data["aspect_category"] = data.pop("aspect")
        if "severity" in data and isinstance(data["severity"], str):
            val = data["severity"].upper()
            try:
                data["severity"] = SeverityTier(val)
            except ValueError:
                data["severity"] = SeverityTier.MEDIUM
        if "triggered_at" in data and "created_at" not in data:
            data["created_at"] = data.pop("triggered_at")
        if "dedup_fingerprint" not in data:
            u = str(data.get("user_id", ""))
            p = str(data.get("product_id", ""))
            a = str(data.get("aspect_category", ""))
            t = str(data.get("alert_type", ""))
            d = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            data["dedup_fingerprint"] = hashlib.sha256(f"{u}|{p}|{a}|{t}|{d}".encode()).hexdigest()[:64]
        super().__init__(**data)

    @property
    def aspect(self) -> str:
        return self.aspect_category

    @aspect.setter
    def aspect(self, val: str) -> None:
        self.aspect_category = val

    @property
    def triggered_at(self) -> datetime:
        return self.created_at

    @triggered_at.setter
    def triggered_at(self, val: datetime) -> None:
        self.created_at = val


class QueryLog(SQLModel, table=True):
    __tablename__ = "query_logs"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    product_id: uuid.UUID = Field(foreign_key="products.id", index=True, nullable=False)
    query_text: str = Field(sa_column=Column(Text, nullable=False))
    answer: Optional[str] = Field(default=None, sa_column=Column(Text))
    routed_intent: str = Field(default="HYBRID", max_length=32, nullable=False)
    cited_review_ids: list[str] = Field(default_factory=list, sa_column=Column(JSONVariant))
    source_review_ids: Optional[str] = Field(default=None, sa_column=Column(Text))
    model_used: Optional[str] = Field(default=None, max_length=64)
    faithfulness_score: float = Field(default=1.0, nullable=False)
    latency_ms: float = Field(default=0.0, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    def __init__(self, **data: Any):
        if "question" in data and "query_text" not in data:
            data["query_text"] = data.pop("question")
        super().__init__(**data)

    @property
    def question(self) -> str:
        return self.query_text

    @question.setter
    def question(self, val: str) -> None:
        self.query_text = val


class JiraIssue(SQLModel, table=True):
    __tablename__ = "jira_issues"
    __table_args__ = (
        Index("ix_jira_issues_product_id", "product_id"),
        Index("ix_jira_issues_jira_key", "jira_key"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    alert_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), unique=True, nullable=False),
    )
    product_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
    )
    jira_key: str = Field(max_length=64, nullable=False)
    status: str = Field(default="To Do", max_length=64, nullable=False)
    summary: Optional[str] = Field(default=None, max_length=512)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )
