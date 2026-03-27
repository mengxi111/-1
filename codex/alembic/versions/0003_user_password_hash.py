"""add user password hash

Revision ID: 0003_user_password_hash
Revises: 0002_booking_lock_checkin_stats
Create Date: 2026-03-03 10:20:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_user_password_hash"
down_revision: str | None = "0002_booking_lock_checkin_stats"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
