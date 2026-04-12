"""modify ticket description to custom_fields

Revision ID: h1i2j3k4l5m6
Revises: f7g8h9i0j1k2
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'h1i2j3k4l5m6'
down_revision: Union[str, Sequence[str], None] = 'f7g8h9i0j1k2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('tickets', 'description')
    op.add_column('tickets', sa.Column('custom_fields', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('tickets', 'custom_fields')
    op.add_column('tickets', sa.Column('description', sa.Text(), nullable=True))