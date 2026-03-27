"""add redis/exclusion support and checkin fields

Revision ID: 0002_booking_lock_checkin_stats
Revises: 0001_init_mvp
Create Date: 2026-03-02 18:10:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_booking_lock_checkin_stats"
down_revision: str | None = "0001_init_mvp"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    op.drop_constraint("ck_bookings_status", "bookings", type_="check")
    op.create_check_constraint(
        "ck_bookings_status",
        "bookings",
        "status IN ('confirmed','checked_in','cancelled','expired','completed')",
    )

    op.add_column("bookings", sa.Column("checkin_code", sa.String(length=6), nullable=True))
    op.add_column("bookings", sa.Column("checkin_code_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bookings", sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True))

    op.drop_index("idx_bookings_active_seat_time", table_name="bookings")
    op.create_index(
        "idx_bookings_active_seat_time",
        "bookings",
        ["seat_id", "start_time", "end_time"],
        unique=False,
        postgresql_where=sa.text("status IN ('confirmed','checked_in')"),
    )

    op.execute(
        """
        ALTER TABLE bookings
        ADD CONSTRAINT ex_bookings_active_seat_time
        EXCLUDE USING gist (
            seat_id WITH =,
            tstzrange(start_time, end_time, '[)') WITH &&
        )
        WHERE (status IN ('confirmed','checked_in'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS ex_bookings_active_seat_time")

    op.drop_index("idx_bookings_active_seat_time", table_name="bookings")
    op.create_index(
        "idx_bookings_active_seat_time",
        "bookings",
        ["seat_id", "start_time", "end_time"],
        unique=False,
        postgresql_where=sa.text("status = 'confirmed'"),
    )

    op.drop_column("bookings", "checked_in_at")
    op.drop_column("bookings", "checkin_code_expires_at")
    op.drop_column("bookings", "checkin_code")

    op.drop_constraint("ck_bookings_status", "bookings", type_="check")
    op.create_check_constraint(
        "ck_bookings_status",
        "bookings",
        "status IN ('confirmed','cancelled','expired','completed')",
    )
