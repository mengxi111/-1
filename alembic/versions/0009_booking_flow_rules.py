"""booking flow rules and store business hours

Revision ID: 0009_booking_flow_rules
Revises: 0008_qr_checkin_and_records
Create Date: 2026-03-05 10:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0009_booking_flow_rules"
down_revision: str | None = "0008_qr_checkin_and_records"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "stores",
        sa.Column("open_time", sa.Time(), server_default=sa.text("'08:00:00'"), nullable=False),
    )
    op.add_column(
        "stores",
        sa.Column("close_time", sa.Time(), server_default=sa.text("'23:00:00'"), nullable=False),
    )

    op.drop_constraint("ck_bookings_status", "bookings", type_="check")
    op.create_check_constraint(
        "ck_bookings_status",
        "bookings",
        "status IN ('confirmed','booked','checked_in','cancelled','expired','completed')",
    )

    op.execute("UPDATE bookings SET status='booked' WHERE status='confirmed'")

    op.drop_constraint("ck_bookings_status", "bookings", type_="check")
    op.drop_index("idx_bookings_active_seat_time", table_name="bookings")
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS ex_bookings_active_seat_time")
    op.create_check_constraint(
        "ck_bookings_status",
        "bookings",
        "status IN ('booked','checked_in','cancelled','expired','completed')",
    )
    op.create_index(
        "idx_bookings_active_seat_time",
        "bookings",
        ["seat_id", "start_time", "end_time"],
        unique=False,
        postgresql_where=sa.text("status IN ('booked','checked_in')"),
    )
    op.create_index("idx_bookings_status_start_time", "bookings", ["status", "start_time"], unique=False)

    op.execute(
        """
        ALTER TABLE bookings
        ADD CONSTRAINT ex_bookings_active_seat_time
        EXCLUDE USING gist (
            seat_id WITH =,
            tstzrange(start_time, end_time, '[)') WITH &&
        )
        WHERE (status IN ('booked','checked_in'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS ex_bookings_active_seat_time")
    op.drop_index("idx_bookings_status_start_time", table_name="bookings")
    op.drop_index("idx_bookings_active_seat_time", table_name="bookings")
    op.drop_constraint("ck_bookings_status", "bookings", type_="check")
    op.create_check_constraint(
        "ck_bookings_status",
        "bookings",
        "status IN ('confirmed','checked_in','cancelled','expired','completed')",
    )
    op.create_index(
        "idx_bookings_active_seat_time",
        "bookings",
        ["seat_id", "start_time", "end_time"],
        unique=False,
        postgresql_where=sa.text("status IN ('confirmed','checked_in')"),
    )
    op.execute("UPDATE bookings SET status='confirmed' WHERE status='booked'")
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

    op.drop_column("stores", "close_time")
    op.drop_column("stores", "open_time")
