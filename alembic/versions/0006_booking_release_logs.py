"""add booking release logs table

Revision ID: 0006_booking_release_logs
Revises: 0005_blacklist_no_show
Create Date: 2026-03-04 17:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0006_booking_release_logs"
down_revision: str | None = "0005_blacklist_no_show"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "booking_release_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("booking_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("seat_id", sa.BigInteger(), nullable=False),
        sa.Column("release_type", sa.String(length=30), server_default=sa.text("'auto_timeout'"), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seat_id"], ["seats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_booking_release_logs_booking_id", "booking_release_logs", ["booking_id"], unique=False)
    op.create_index("idx_booking_release_logs_released_at", "booking_release_logs", ["released_at"], unique=False)
    op.create_index("idx_booking_release_logs_user_id", "booking_release_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_booking_release_logs_user_id", table_name="booking_release_logs")
    op.drop_index("idx_booking_release_logs_released_at", table_name="booking_release_logs")
    op.drop_index("idx_booking_release_logs_booking_id", table_name="booking_release_logs")
    op.drop_table("booking_release_logs")
