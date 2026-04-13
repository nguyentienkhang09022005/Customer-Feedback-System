"""add_survey_sent_and_resolved_at_to_tickets

Revision ID: p1q2r3s4t5u6
Revises: j1k2l3m4n5o6
Create Date: 2026-04-13 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'p1q2r3s4t5u6'
down_revision: Union[str, Sequence[str], None] = 'j1k2l3m4n5o6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tickets', sa.Column('survey_sent', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('tickets', sa.Column('resolved_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('tickets', 'resolved_at')
    op.drop_column('tickets', 'survey_sent')