"""drop id_category from tickets table

Revision ID: e5f6a7b8c9d0
Revises: a1b2c3d4e5f6
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('tickets', 'id_category')


def downgrade() -> None:
    op.add_column('tickets', sa.Column('id_category', sa.UUID(), sa.ForeignKey("tickets_category.id_category", ondelete="SET NULL"), nullable=True))