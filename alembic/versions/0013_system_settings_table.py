"""add system settings table

Revision ID: 0013_system_settings_table
Revises: 0012_model_alignment_fields
Create Date: 2026-03-18 11:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0013_system_settings_table"
down_revision: str | None = "0012_model_alignment_fields"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("system_settings")
