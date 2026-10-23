"""add_jira_issues

Revision ID: 0002_jira_issues
Revises: 0001_initial
Create Date: 2026-10-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002_jira_issues'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'jira_issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('alert_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('alerts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('jira_key', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False, server_default='To Do'),
        sa.Column('summary', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('alert_id', name='uq_jira_issues_alert_id'),
    )
    op.create_index('ix_jira_issues_alert_id', 'jira_issues', ['alert_id'], unique=True)
    op.create_index('ix_jira_issues_product_id', 'jira_issues', ['product_id'])
    op.create_index('ix_jira_issues_jira_key', 'jira_issues', ['jira_key'])


def downgrade() -> None:
    op.drop_index('ix_jira_issues_jira_key', table_name='jira_issues')
    op.drop_index('ix_jira_issues_product_id', table_name='jira_issues')
    op.drop_index('ix_jira_issues_alert_id', table_name='jira_issues')
    op.drop_table('jira_issues')
