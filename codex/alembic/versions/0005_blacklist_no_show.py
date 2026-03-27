"""add no-show counter and booking blacklist

Revision ID: 0005_blacklist_no_show
Revises: 0004_auth_rbac_admin_entities
Create Date: 2026-03-04 16:40:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0005_blacklist_no_show"
down_revision: str | None = "0004_auth_rbac_admin_entities"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("no_show_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.create_check_constraint("ck_users_no_show_count", "users", "no_show_count >= 0")

    op.create_table(
        "booking_blacklists",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=20), server_default=sa.text("'manual'"), nullable=False),
        sa.Column("no_show_count_snapshot", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("source IN ('auto_no_show','manual')", name="ck_booking_blacklists_source"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_booking_blacklists_user_id", "booking_blacklists", ["user_id"], unique=True)
    op.create_index("idx_booking_blacklists_created_at", "booking_blacklists", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_booking_blacklists_created_at", table_name="booking_blacklists")
    op.drop_index("idx_booking_blacklists_user_id", table_name="booking_blacklists")
    op.drop_table("booking_blacklists")

    op.drop_constraint("ck_users_no_show_count", "users", type_="check")
    op.drop_column("users", "no_show_count")
