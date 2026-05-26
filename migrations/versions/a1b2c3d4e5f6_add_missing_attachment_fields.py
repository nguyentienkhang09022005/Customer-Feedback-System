"""add_missing_attachment_fields

Revision ID: b2c3d4e5f6a7
Revises: y2z3a4b5c6d7
Create Date: 2026-05-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'y2z3a4b5c6d7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to attachments table that were missing from model
    op.add_column('attachments', sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('attachments', sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    op.add_column('attachments', sa.Column('is_permanent', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    op.add_column('attachments', sa.Column('reference_type', sa.String(50), nullable=True))
    op.add_column('attachments', sa.Column('storage_type', sa.String(20), nullable=True))
    op.add_column('attachments', sa.Column('public_id', sa.String(255), nullable=True))
    op.add_column('attachments', sa.Column('file_size', sa.Integer(), nullable=True))
    op.add_column('attachments', sa.Column('thumbnail_url', sa.String(500), nullable=True))
    op.add_column('attachments', sa.Column('attach_extension', sa.String(20), nullable=True))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('attachments', 'attach_extension')
    op.drop_column('attachments', 'thumbnail_url')
    op.drop_column('attachments', 'file_size')
    op.drop_column('attachments', 'public_id')
    op.drop_column('attachments', 'storage_type')
    op.drop_column('attachments', 'reference_type')
    op.drop_column('attachments', 'is_permanent')
    op.drop_column('attachments', 'is_deleted')
    op.drop_column('attachments', 'updated_at')