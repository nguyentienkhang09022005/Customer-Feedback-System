"""create_escalation_rules_table

Revision ID: y2z3a4b5c6d7
Revises: x1y2z3a4b5c6_create_tags_table
Create Date: 2026-05-08 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'y2z3a4b5c6d7'
down_revision: Union[str, Sequence[str], None] = 'x1y2z3a4b5c6_create_tags_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'escalation_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('priority', sa.String(50), nullable=True),
        sa.Column('condition_type', sa.String(50), nullable=False),
        sa.Column('condition_value', sa.String(255), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('action_target', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        'ix_escalation_rules_id',
        'escalation_rules',
        ['id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_escalation_rules_id', table_name='escalation_rules')
    op.drop_table('escalation_rules')
