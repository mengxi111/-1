"""add draft status for notices

Revision ID: 0014_notice_draft_status
Revises: 0013_system_settings_table
Create Date: 2026-03-24 11:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0014_notice_draft_status"
down_revision: str | None = "0013_system_settings_table"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _has_check_constraint(table_name: str, constraint_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    constraints = inspector.get_check_constraints(table_name)
    return any(item.get("name") == constraint_name for item in constraints)


def upgrade() -> None:
    if _has_check_constraint("notices", "ck_notices_status"):
        op.drop_constraint("ck_notices_status", "notices", type_="check")
    op.create_check_constraint(
        "ck_notices_status",
        "notices",
        "status IN ('draft','published','offline')",
    )
    op.alter_column(
        "notices",
        "status",
        existing_type=sa.String(length=20),
        existing_nullable=False,
        server_default=sa.text("'draft'"),
    )


def downgrade() -> None:
    op.execute("UPDATE notices SET status = 'offline' WHERE status = 'draft'")
    if _has_check_constraint("notices", "ck_notices_status"):
        op.drop_constraint("ck_notices_status", "notices", type_="check")
    op.create_check_constraint(
        "ck_notices_status",
        "notices",
        "status IN ('published','offline')",
    )
    op.alter_column(
        "notices",
        "status",
        existing_type=sa.String(length=20),
        existing_nullable=False,
        server_default=sa.text("'offline'"),
    )
