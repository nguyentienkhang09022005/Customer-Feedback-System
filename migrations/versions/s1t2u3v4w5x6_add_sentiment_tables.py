"""add_sentiment_tables

Revision ID: s1t2u3v4w5x6
Revises: p1q2r3s4t5u6
Create Date: 2026-04-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


revision: str = 's1t2u3v4w5x6'
down_revision: Union[str, Sequence[str], None] = 'p1q2r3s4t5u6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sentiment_reports',
        sa.Column('id_report', postgresql.UUID(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('scope', sa.String(length=20), nullable=False),
        sa.Column('id_department', postgresql.UUID(), nullable=True),
        sa.Column('positive_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('neutral_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('negative_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('avg_sentiment_score', sa.Float(), nullable=True),
        sa.Column('message_positive', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('message_neutral', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('message_negative', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('evaluation_positive', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('evaluation_neutral', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('evaluation_negative', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('comment_positive', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('comment_neutral', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('comment_negative', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_interactions', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('avg_response_time_hours', sa.Float(), nullable=True),
        sa.Column('resolution_rate', sa.Float(), nullable=True),
        sa.Column('sentiment_change', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id_report'),
        sa.ForeignKeyConstraint(['id_department'], ['departments.id_department'], ondelete='SET NULL')
    )
    op.create_index('ix_sentiment_reports_year_month_scope', 'sentiment_reports', ['year', 'month', 'scope'], unique=False)
    op.create_index('ix_sentiment_reports_department', 'sentiment_reports', ['id_department'], unique=False)
    op.create_unique_constraint('uq_sentiment_report', 'sentiment_reports', ['year', 'month', 'scope', 'id_department'])

    op.create_table(
        'sentiment_details',
        sa.Column('id_detail', postgresql.UUID(), nullable=False),
        sa.Column('id_report', postgresql.UUID(), nullable=False),
        sa.Column('source_type', sa.String(length=20), nullable=False),
        sa.Column('source_id', postgresql.UUID(), nullable=False),
        sa.Column('sentiment_label', sa.String(length=20), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('id_customer', postgresql.UUID(), nullable=False),
        sa.Column('id_ticket', postgresql.UUID(), nullable=True),
        sa.Column('id_department', postgresql.UUID(), nullable=False),
        sa.Column('original_content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id_detail'),
        sa.ForeignKeyConstraint(['id_report'], ['sentiment_reports.id_report'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_customer'], ['customers.id_customer'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_ticket'], ['tickets.id_ticket'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['id_department'], ['departments.id_department'], ondelete='CASCADE')
    )
    op.create_index('ix_sentiment_details_report', 'sentiment_details', ['id_report'], unique=False)
    op.create_index('ix_sentiment_details_source', 'sentiment_details', ['source_type', 'source_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_sentiment_details_source', table_name='sentiment_details')
    op.drop_index('ix_sentiment_details_report', table_name='sentiment_details')
    op.drop_table('sentiment_details')
    op.drop_constraint('uq_sentiment_report', 'sentiment_reports', type_='unique')
    op.drop_index('ix_sentiment_reports_department', table_name='sentiment_reports')
    op.drop_index('ix_sentiment_reports_year_month_scope', table_name='sentiment_reports')
    op.drop_table('sentiment_reports')