"""create_tags_table

Revision ID: x1y2z3a4b5c6_create_tags_table
Revises: cfde4dd50593
Create Date: 2026-05-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'x1y2z3a4b5c6_create_tags_table'
down_revision: Union[str, Sequence[str], None] = 'cfde4dd50593'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'tags',
        sa.Column('id_tag', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('color', sa.String(7), nullable=False, server_default='#000000'),
        sa.Column('description', sa.Text, nullable=True)
    )

    op.create_table(
        'ticket_tags',
        sa.Column('ticket_id', postgresql.UUID(), sa.ForeignKey('tickets.id_ticket', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', sa.String(36), sa.ForeignKey('tags.id_tag', ondelete='CASCADE'), primary_key=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('ticket_tags')
    op.drop_table('tags')
