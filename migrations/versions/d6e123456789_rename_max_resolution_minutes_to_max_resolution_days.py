"""rename max_resolution_minutes to max_resolution_days in sla_policies

Revision ID: d6e123456789
Revises: 21a778cc1f4f
Create Date: 2026-04-11 00:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6e123456789'
down_revision: Union[str, Sequence[str], None] = '21a778cc1f4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('sla_policies', 'max_resolution_minutes',
                    new_column_name='max_resolution_days')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('sla_policies', 'max_resolution_days',
                    new_column_name='max_resolution_minutes')
