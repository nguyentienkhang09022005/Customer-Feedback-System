"""add ticket templates with versioning and soft delete

Revision ID: a1b2c3d4e5f6
Revises: d2bafa43cfd0
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd2bafa43cfd0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add soft delete and timestamp columns to tickets_category
    op.add_column('tickets_category', sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('tickets_category', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('tickets_category', sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')))
    op.alter_column('tickets_category', 'is_deleted', server_default=None)

    # 2. Create ticket_templates table with composite PK (id_template + version)
    op.create_table(
        'ticket_templates',
        sa.Column('id_template', sa.UUID(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('fields_config', sa.JSON(), nullable=False),
        sa.Column('id_category', sa.UUID(), sa.ForeignKey("tickets_category.id_category", ondelete="SET NULL"), nullable=True),
        sa.Column('id_author', sa.UUID(), sa.ForeignKey("employees.id_employee", ondelete="SET NULL"), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id_template', 'version')
    )
    op.create_index(op.f('ix_ticket_templates_id_template'), 'ticket_templates', ['id_template'], unique=False)
    op.create_index(op.f('ix_ticket_templates_id_category'), 'ticket_templates', ['id_category'], unique=False)
    op.create_index(op.f('ix_ticket_templates_is_active'), 'ticket_templates', ['is_active'], unique=False)

    # 3. Add unique constraint on id_template alone (for FK reference)
    op.create_unique_constraint('uq_ticket_templates_id_template', 'ticket_templates', ['id_template'])

    # 4. Add template FKs and soft delete columns to tickets
    # Using composite FK: (id_template, template_version) -> (id_template, version)
    op.add_column('tickets', sa.Column('id_template', sa.UUID(), nullable=True))
    op.add_column('tickets', sa.Column('template_version', sa.Integer(), nullable=True))
    op.add_column('tickets', sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('tickets', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.alter_column('tickets', 'is_deleted', server_default=None)
    
    # Create composite FK constraint separately for clarity
    op.create_foreign_key(
        'fk_tickets_template_version',
        'tickets', 'ticket_templates',
        ['id_template', 'template_version'],
        ['id_template', 'version'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop FK first
    op.drop_constraint('fk_tickets_template_version', 'tickets', type_='foreignkey')

    # Drop tickets template columns
    op.drop_column('tickets', 'deleted_at')
    op.drop_column('tickets', 'is_deleted')
    op.drop_column('tickets', 'template_version')
    op.drop_column('tickets', 'id_template')

    # Drop unique constraint
    op.drop_constraint('uq_ticket_templates_id_template', 'ticket_templates', type_='unique')

    # Drop ticket_templates table
    op.drop_index(op.f('ix_ticket_templates_is_active'), table_name='ticket_templates')
    op.drop_index(op.f('ix_ticket_templates_id_category'), table_name='ticket_templates')
    op.drop_index(op.f('ix_ticket_templates_id_template'), table_name='ticket_templates')
    op.drop_table('ticket_templates')

    # Drop tickets_category soft delete columns
    op.drop_column('tickets_category', 'updated_at')
    op.drop_column('tickets_category', 'deleted_at')
    op.drop_column('tickets_category', 'is_deleted')