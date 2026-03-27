"""add qr checkin fields and checkin records

Revision ID: 0008_qr_checkin_and_records
Revises: 0007_admin_operation_logs
Create Date: 2026-03-04 20:10:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0008_qr_checkin_and_records"
down_revision: str | None = "0007_admin_operation_logs"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("qr_token", sa.String(length=64), nullable=True))
    op.add_column("bookings", sa.Column("qr_token_expires_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "booking_checkin_records",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("booking_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("seat_id", sa.BigInteger(), nullable=False),
        sa.Column("store_id", sa.BigInteger(), nullable=True),
        sa.Column("checkin_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checkin_method", sa.String(length=20), nullable=False),
        sa.Column("qr_token", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("checkin_method IN ('code','qr_simulated')", name="ck_booking_checkin_records_method"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seat_id"], ["seats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_id", name="uq_booking_checkin_records_booking_id"),
    )
    op.create_index(
        "idx_booking_checkin_records_store_time",
        "booking_checkin_records",
        ["store_id", "checkin_time"],
        unique=False,
    )
    op.create_index(
        "idx_booking_checkin_records_user_time",
        "booking_checkin_records",
        ["user_id", "checkin_time"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_booking_checkin_records_user_time", table_name="booking_checkin_records")
    op.drop_index("idx_booking_checkin_records_store_time", table_name="booking_checkin_records")
    op.drop_table("booking_checkin_records")

    op.drop_column("bookings", "qr_token_expires_at")
    op.drop_column("bookings", "qr_token")
