"""add_chatbot_tables

Revision ID: j1k2l3m4n5o6
Revises: 7afa281e6f9f
Create Date: 2026-04-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'j1k2l3m4n5o6'
down_revision: Union[str, Sequence[str], None] = '7afa281e6f9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id_session', sa.UUID(), primary_key=True),
        sa.Column('customer_id', sa.UUID(), sa.ForeignKey('customers.id_customer', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_chat_sessions_customer_id', 'chat_sessions', ['customer_id'])

    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id_message', sa.UUID(), primary_key=True),
        sa.Column('session_id', sa.UUID(), sa.ForeignKey('chat_sessions.id_session', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])


def downgrade() -> None:
    op.drop_index('ix_chat_messages_session_id')
    op.drop_table('chat_messages')
    op.drop_index('ix_chat_sessions_customer_id')
    op.drop_table('chat_sessions')
