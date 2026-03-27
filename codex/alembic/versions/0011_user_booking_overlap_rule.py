"""user booking overlap exclusion constraint

Revision ID: 0011_user_booking_overlap_rule
Revises: 0010_student_notifications
Create Date: 2026-03-10 10:40:00
"""

from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision: str = "0011_user_booking_overlap_rule"
down_revision: str | None = "0010_student_notifications"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _resolve_existing_user_conflicts() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT id, user_id, start_time, end_time
            FROM bookings
            WHERE status IN ('booked', 'checked_in')
            ORDER BY user_id, start_time, id
            """
        )
    ).mappings()

    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[int(row["user_id"])].append(
            {
                "id": int(row["id"]),
                "start_time": row["start_time"],
                "end_time": row["end_time"],
            }
        )

    now = datetime.now(timezone.utc)
    cancelled_ids: list[int] = []

    for _, bookings in grouped.items():
        accepted: list[dict] = []
        for booking in bookings:
            conflict = any(
                existing["start_time"] < booking["end_time"]
                and existing["end_time"] > booking["start_time"]
                for existing in accepted
            )
            if conflict:
                cancelled_ids.append(booking["id"])
                continue
            accepted.append(booking)

    if cancelled_ids:
        bind.execute(
            sa.text(
                """
                UPDATE bookings
                SET status = 'cancelled',
                    checkin_code = NULL,
                    checkin_code_expires_at = NULL,
                    qr_token = NULL,
                    qr_token_expires_at = NULL,
                    updated_at = :updated_at
                WHERE id = ANY(:booking_ids)
                """
            ),
            {"updated_at": now, "booking_ids": cancelled_ids},
        )


def upgrade() -> None:
    _resolve_existing_user_conflicts()
    op.execute(
        """
        ALTER TABLE bookings
        ADD CONSTRAINT ex_bookings_active_user_time
        EXCLUDE USING gist (
            user_id WITH =,
            tstzrange(start_time, end_time, '[)') WITH &&
        )
        WHERE (status IN ('booked','checked_in'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS ex_bookings_active_user_time")
