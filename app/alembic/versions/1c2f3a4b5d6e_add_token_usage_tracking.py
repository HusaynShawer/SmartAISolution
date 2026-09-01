"""add token usage tracking

Revision ID: 1c2f3a4b5d6e
Revises: 8aea626349df
Create Date: 2026-09-01 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1c2f3a4b5d6e"
down_revision: str | None = "8aea626349df"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "token_usage",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("conversation_id", sa.String(length=36), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_token_usage_user_id"), "token_usage", ["user_id"]
    )
    op.create_index(
        op.f("ix_token_usage_conversation_id"), "token_usage", ["conversation_id"]
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_token_usage_conversation_id"), table_name="token_usage"
    )
    op.drop_index(op.f("ix_token_usage_user_id"), table_name="token_usage")
    op.drop_table("token_usage")