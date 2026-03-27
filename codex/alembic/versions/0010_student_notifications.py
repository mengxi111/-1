"""student notifications and email queue

Revision ID: 0010_student_notifications
Revises: 0009_booking_flow_rules
Create Date: 2026-03-09 14:20:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0010_student_notifications"
down_revision: str | None = "0009_booking_flow_rules"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "student_notifications",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("notification_type", sa.String(length=20), server_default=sa.text("'system'"), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_status", sa.String(length=20), server_default=sa.text("'skipped'"), nullable=False),
        sa.Column("email_error", sa.Text(), nullable=True),
        sa.Column("emailed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("related_type", sa.String(length=50), nullable=True),
        sa.Column("related_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "notification_type IN ('booking','notice','violation','system')",
            name="ck_student_notifications_type",
        ),
        sa.CheckConstraint(
            "email_status IN ('pending','sent','failed','skipped')",
            name="ck_student_notifications_email_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_student_notifications_user_read_created",
        "student_notifications",
        ["user_id", "is_read", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_student_notifications_email_status_created",
        "student_notifications",
        ["email_status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_student_notifications_email_status_created", table_name="student_notifications")
    op.drop_index("idx_student_notifications_user_read_created", table_name="student_notifications")
    op.drop_table("student_notifications")
