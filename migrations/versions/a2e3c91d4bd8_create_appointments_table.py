"""create_appointments_table

Revision ID: a2e3c91d4bd8
Revises: s1t2u3v4w5x6
Create Date: 2026-04-21 08:42:52.004842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a2e3c91d4bd8'
down_revision: Union[str, Sequence[str], None] = 's1t2u3v4w5x6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('appointments',
    sa.Column('id_appointment', sa.UUID(), nullable=False),
    sa.Column('id_ticket', sa.UUID(), nullable=False),
    sa.Column('id_customer', sa.UUID(), nullable=False),
    sa.Column('id_employee', sa.UUID(), nullable=False),
    sa.Column('scheduled_at', sa.DateTime(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('rejection_reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_customer'], ['customers.id_customer'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['id_employee'], ['employees.id_employee'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['id_ticket'], ['tickets.id_ticket'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id_appointment')
    )
    op.create_index(op.f('ix_appointments_id_appointment'), 'appointments', ['id_appointment'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_appointments_id_appointment'), table_name='appointments')
    op.drop_table('appointments')