"""align models with enhanced booking/admin features

Revision ID: 0012_model_alignment_fields
Revises: 0011_user_booking_overlap_rule
Create Date: 2026-03-18 10:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0012_model_alignment_fields"
down_revision: str | None = "0011_user_booking_overlap_rule"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def _has_fk(table_name: str, fk_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    foreign_keys = inspector.get_foreign_keys(table_name)
    return any(fk.get("name") == fk_name for fk in foreign_keys)


def upgrade() -> None:
    if not _has_column("stores", "contact_phone"):
        op.add_column("stores", sa.Column("contact_phone", sa.String(length=30), nullable=True))
    if not _has_column("stores", "description"):
        op.add_column("stores", sa.Column("description", sa.Text(), nullable=True))

    if not _has_column("areas", "sort_order"):
        op.add_column("areas", sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")))
    if not _has_index("areas", "idx_areas_store_sort_order"):
        op.create_index("idx_areas_store_sort_order", "areas", ["store_id", "sort_order"], unique=False)

    if not _has_index("seats", "idx_seats_store_area_status"):
        op.create_index("idx_seats_store_area_status", "seats", ["store_id", "area_id", "seat_status"], unique=False)

    if not _has_column("pricing_plans", "min_minutes"):
        op.add_column(
            "pricing_plans",
            sa.Column("min_minutes", sa.Integer(), nullable=False, server_default=sa.text("30")),
        )
    if not _has_column("pricing_plans", "max_minutes"):
        op.add_column(
            "pricing_plans",
            sa.Column("max_minutes", sa.Integer(), nullable=False, server_default=sa.text("720")),
        )

    if not _has_column("bookings", "store_id"):
        op.add_column("bookings", sa.Column("store_id", sa.BigInteger(), nullable=True))
        op.execute(
            """
            UPDATE bookings b
            SET store_id = s.store_id
            FROM seats s
            WHERE b.seat_id = s.id AND b.store_id IS NULL
            """
        )
        op.alter_column("bookings", "store_id", nullable=False)
    if not _has_fk("bookings", "fk_bookings_store_id_stores"):
        op.create_foreign_key(
            "fk_bookings_store_id_stores",
            "bookings",
            "stores",
            ["store_id"],
            ["id"],
            ondelete="RESTRICT",
        )
    if not _has_column("bookings", "sign_in_time"):
        op.add_column("bookings", sa.Column("sign_in_time", sa.DateTime(timezone=True), nullable=True))
    if not _has_column("bookings", "cancel_reason"):
        op.add_column("bookings", sa.Column("cancel_reason", sa.String(length=255), nullable=True))
    if not _has_column("bookings", "expire_reason"):
        op.add_column("bookings", sa.Column("expire_reason", sa.String(length=255), nullable=True))
    if not _has_index("bookings", "idx_bookings_user_status"):
        op.create_index("idx_bookings_user_status", "bookings", ["user_id", "status"], unique=False)
    if not _has_index("bookings", "idx_bookings_store_start_time"):
        op.create_index("idx_bookings_store_start_time", "bookings", ["store_id", "start_time"], unique=False)

    if not _has_column("booking_blacklists", "start_at"):
        op.add_column(
            "booking_blacklists",
            sa.Column("start_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
    if not _has_column("booking_blacklists", "end_at"):
        op.add_column("booking_blacklists", sa.Column("end_at", sa.DateTime(timezone=True), nullable=True))
    if not _has_column("booking_blacklists", "is_active"):
        op.add_column(
            "booking_blacklists",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )


def downgrade() -> None:
    if _has_column("booking_blacklists", "is_active"):
        op.drop_column("booking_blacklists", "is_active")
    if _has_column("booking_blacklists", "end_at"):
        op.drop_column("booking_blacklists", "end_at")
    if _has_column("booking_blacklists", "start_at"):
        op.drop_column("booking_blacklists", "start_at")

    if _has_index("bookings", "idx_bookings_store_start_time"):
        op.drop_index("idx_bookings_store_start_time", table_name="bookings")
    if _has_index("bookings", "idx_bookings_user_status"):
        op.drop_index("idx_bookings_user_status", table_name="bookings")
    if _has_column("bookings", "expire_reason"):
        op.drop_column("bookings", "expire_reason")
    if _has_column("bookings", "cancel_reason"):
        op.drop_column("bookings", "cancel_reason")
    if _has_column("bookings", "sign_in_time"):
        op.drop_column("bookings", "sign_in_time")
    if _has_fk("bookings", "fk_bookings_store_id_stores"):
        op.drop_constraint("fk_bookings_store_id_stores", "bookings", type_="foreignkey")
    if _has_column("bookings", "store_id"):
        op.drop_column("bookings", "store_id")

    if _has_column("pricing_plans", "max_minutes"):
        op.drop_column("pricing_plans", "max_minutes")
    if _has_column("pricing_plans", "min_minutes"):
        op.drop_column("pricing_plans", "min_minutes")

    if _has_index("seats", "idx_seats_store_area_status"):
        op.drop_index("idx_seats_store_area_status", table_name="seats")

    if _has_index("areas", "idx_areas_store_sort_order"):
        op.drop_index("idx_areas_store_sort_order", table_name="areas")
    if _has_column("areas", "sort_order"):
        op.drop_column("areas", "sort_order")

    if _has_column("stores", "description"):
        op.drop_column("stores", "description")
    if _has_column("stores", "contact_phone"):
        op.drop_column("stores", "contact_phone")
