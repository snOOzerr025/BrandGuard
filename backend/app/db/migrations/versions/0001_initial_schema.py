"""initial_schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-10-16 23:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('organization_name', sa.String(length=255), nullable=False, server_default='Personal'),
        sa.Column('plan_tier', sa.String(length=32), nullable=False, server_default='GROWTH'),
        sa.Column('slack_webhook_url', sa.String(length=512), nullable=True),
        sa.Column('alert_email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 3. Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1024), nullable=True),
        sa.Column('sku', sa.String(length=128), nullable=False),
        sa.Column('source', sa.String(length=64), nullable=False, server_default='csv_upload'),
        sa.Column('external_asin', sa.String(length=64), nullable=True),
        sa.Column('trustpilot_business_unit_id', sa.String(length=64), nullable=True),
        sa.Column('review_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('brand_health_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('net_sentiment', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'sku', name='uq_product_tenant_sku'),
    )
    op.create_index('ix_products_user_id', 'products', ['user_id'])

    # 4. Create ingestion_jobs table
    op.create_table(
        'ingestion_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('celery_task_id', sa.String(length=128), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('state', sa.String(length=64), nullable=False, server_default='PENDING'),
        sa.Column('total_reviews', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_reviews', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_detail', sa.Text(), nullable=True),
        sa.Column('metadata_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_ingestion_jobs_user_product', 'ingestion_jobs', ['user_id', 'product_id'])
    op.create_index('ix_ingestion_jobs_celery_task_id', 'ingestion_jobs', ['celery_task_id'])

    # 5. Create micro_clusters table
    op.create_table(
        'micro_clusters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('macro_aspect', sa.String(length=64), nullable=False),
        sa.Column('hdbscan_label', sa.Integer(), nullable=False),
        sa.Column('theme_label', sa.String(length=255), nullable=False),
        sa.Column('top_ctfidf_terms', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('evidence_review_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('review_volume', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('net_sentiment', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('star_impact_delta', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('centroid_embedding', Vector(384), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_micro_clusters_tenant_product', 'micro_clusters', ['user_id', 'product_id', 'macro_aspect'])

    # 6. Create reviews table
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ingestion_jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('external_review_id', sa.String(length=128), nullable=False),
        sa.Column('source_channel', sa.String(length=64), nullable=False, server_default='CSV'),
        sa.Column('source', sa.String(length=64), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('sentiment_label', sa.String(length=32), nullable=True),
        sa.Column('verified_purchase', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('has_rating_discrepancy', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('micro_cluster_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('micro_clusters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column(
            'search_vector',
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', coalesce(title, '') || ' ' || body)", persisted=True),
            nullable=True,
        ),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'product_id', 'external_review_id', name='uq_review_dedup'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_review_rating_bounds'),
    )
    op.create_index('ix_reviews_tenant_product_date', 'reviews', ['user_id', 'product_id', 'reviewed_at'])
    op.create_index('ix_reviews_discrepancy', 'reviews', ['has_rating_discrepancy'])

    # HNSW Index with vector_cosine_ops
    op.execute(
        "CREATE INDEX ix_reviews_embedding_hnsw ON reviews "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 128);"
    )
    # GIN index on tsvector
    op.create_index('ix_reviews_search_vector_gin', 'reviews', ['search_vector'], postgresql_using='gin')

    # 7. Create sentiment_results table
    op.create_table(
        'sentiment_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('review_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reviews.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('aspect_category', sa.String(length=64), nullable=False),
        sa.Column('extracted_span', sa.String(length=255), nullable=True),
        sa.Column('is_implicit', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('polarity', sa.String(length=32), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('numeric_score', sa.Float(), nullable=False),
        sa.Column('model_version', sa.String(length=64), nullable=True, server_default='v2.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_sentiment_tenant_product_aspect', 'sentiment_results', ['user_id', 'product_id', 'aspect_category'])
    op.create_index('ix_sentiment_review_id', 'sentiment_results', ['review_id'])

    # 8. Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('aspect_category', sa.String(length=64), nullable=False),
        sa.Column('micro_cluster_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('micro_clusters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('severity', sa.String(length=32), nullable=False),
        sa.Column('alert_type', sa.String(length=64), nullable=False),
        sa.Column('z_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('baseline_mean', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('current_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('star_impact', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('support_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('evidence_review_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('dedup_fingerprint', sa.String(length=128), nullable=False),
        sa.Column('is_acknowledged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'product_id', 'dedup_fingerprint', name='uq_alert_dedup_window'),
    )
    op.create_index('ix_alerts_tenant_product_created', 'alerts', ['user_id', 'product_id', 'created_at'])

    # 9. Create query_logs table
    op.create_table(
        'query_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('routed_intent', sa.String(length=32), nullable=False, server_default='HYBRID'),
        sa.Column('cited_review_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('source_review_ids', sa.Text(), nullable=True),
        sa.Column('model_used', sa.String(length=64), nullable=True),
        sa.Column('faithfulness_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('latency_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_query_logs_user_id', 'query_logs', ['user_id'])
    op.create_index('ix_query_logs_product_id', 'query_logs', ['product_id'])

    # 10. PostgreSQL Row-Level Security (RLS) Policies
    for tbl in ['products', 'reviews', 'sentiment_results', 'micro_clusters', 'alerts']:
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"CREATE POLICY {tbl}_tenant_isolation_policy ON {tbl} "
            f"USING (user_id = coalesce(nullif(current_setting('app.current_user_id', true), ''), '00000000-0000-0000-0000-000000000000')::uuid);"
        )


def downgrade() -> None:
    for tbl in ['alerts', 'sentiment_results', 'reviews', 'micro_clusters', 'products']:
        op.execute(f"DROP POLICY IF EXISTS {tbl}_tenant_isolation_policy ON {tbl};")
        op.execute(f"ALTER TABLE {tbl} DISABLE ROW LEVEL SECURITY;")

    op.drop_table('query_logs')
    op.drop_table('alerts')
    op.drop_table('sentiment_results')
    op.drop_table('reviews')
    op.drop_table('micro_clusters')
    op.drop_table('ingestion_jobs')
    op.drop_table('products')
    op.drop_table('users')
