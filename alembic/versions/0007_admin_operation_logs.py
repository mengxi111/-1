"""add admin operation logs table

Revision ID: 0007_admin_operation_logs
Revises: 0006_booking_release_logs
Create Date: 2026-03-04 18:10:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0007_admin_operation_logs"
down_revision: str | None = "0006_booking_release_logs"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admin_operation_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("operator_id", sa.BigInteger(), nullable=True),
        sa.Column("operator_name", sa.String(length=50), nullable=True),
        sa.Column("operator_role", sa.String(length=20), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=False),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("request_method", sa.String(length=10), nullable=False),
        sa.Column("request_path", sa.String(length=255), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_admin_operation_logs_created_at", "admin_operation_logs", ["created_at"], unique=False)
    op.create_index("idx_admin_operation_logs_module", "admin_operation_logs", ["module"], unique=False)
    op.create_index("idx_admin_operation_logs_operator_id", "admin_operation_logs", ["operator_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_admin_operation_logs_operator_id", table_name="admin_operation_logs")
    op.drop_index("idx_admin_operation_logs_module", table_name="admin_operation_logs")
    op.drop_index("idx_admin_operation_logs_created_at", table_name="admin_operation_logs")
    op.drop_table("admin_operation_logs")
