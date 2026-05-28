"""align ticket template schema with model

Revision ID: 4ce1faf3bfe0
Revises: b2c3d4e5f6a7
Create Date: 2026-05-28 10:28:33.223841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4ce1faf3bfe0'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        'uq_ticket_template_id_version',
        'ticket_templates',
        ['id_template', 'version'],
    )
    op.drop_constraint('fk_tickets_template_version', 'tickets', type_='foreignkey')
    op.create_foreign_key(
        'fk_tickets_id_template',
        'tickets',
        'ticket_templates',
        ['id_template'],
        ['id_template'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_tickets_id_template', 'tickets', type_='foreignkey')
    op.create_foreign_key(
        'fk_tickets_template_version',
        'tickets',
        'ticket_templates',
        ['id_template', 'template_version'],
        ['id_template', 'version'],
        ondelete='SET NULL',
    )
    op.drop_constraint('uq_ticket_template_id_version', 'ticket_templates', type_='unique')
