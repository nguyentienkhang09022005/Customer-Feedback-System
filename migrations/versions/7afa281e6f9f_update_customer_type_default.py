"""update_customer_type_default

Revision ID: 7afa281e6f9f
Revises: h1i2j3k4l5m6
Create Date: 2026-04-13 12:13:19.951116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7afa281e6f9f'
down_revision: Union[str, Sequence[str], None] = 'h1i2j3k4l5m6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('customers', 'customer_type', server_default='Starter')


def downgrade() -> None:
    op.alter_column('customers', 'customer_type', server_default=None)