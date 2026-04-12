"""fix template unique constraint for versioning support

Revision ID: f7g8h9i0j1k2
Revises: e5f6a7b8c9d0
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f7g8h9i0j1k2'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('uq_ticket_templates_id_template', 'ticket_templates', type_='unique')


def downgrade() -> None:
    op.create_unique_constraint('uq_ticket_templates_id_template', 'ticket_templates', ['id_template'])