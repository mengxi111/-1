"""init mvp schema

Revision ID: 0001_init_mvp
Revises:
Create Date: 2026-03-02 17:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_init_mvp"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("status", sa.SmallInteger(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_stores_status", "stores", ["status"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("status", sa.SmallInteger(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("role IN ('student','admin')", name="ck_users_role"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone"),
    )
    op.create_index("idx_users_role", "users", ["role"], unique=False)

    op.create_table(
        "seats",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.BigInteger(), nullable=False),
        sa.Column("seat_no", sa.String(length=30), nullable=False),
        sa.Column("seat_type", sa.String(length=20), server_default=sa.text("'normal'"), nullable=False),
        sa.Column("is_available", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "seat_no", name="uq_seats_store_seat_no"),
    )
    op.create_index("idx_seats_store_id", "seats", ["store_id"], unique=False)
    op.create_index("idx_seats_store_available", "seats", ["store_id", "is_available"], unique=False)

    op.create_table(
        "member_cards",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("card_name", sa.String(length=50), nullable=False),
        sa.Column("card_type", sa.String(length=20), nullable=False),
        sa.Column("balance_minutes", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("balance_times", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("expire_at", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("card_type IN ('time','times')", name="ck_member_cards_card_type"),
        sa.CheckConstraint("status IN ('active','expired','disabled')", name="ck_member_cards_status"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_member_cards_user_status", "member_cards", ["user_id", "status"], unique=False)

    op.create_table(
        "bookings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("seat_id", sa.BigInteger(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'confirmed'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("end_time > start_time", name="ck_bookings_time_window"),
        sa.CheckConstraint(
            "status IN ('confirmed','cancelled','expired','completed')",
            name="ck_bookings_status",
        ),
        sa.ForeignKeyConstraint(["seat_id"], ["seats.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_bookings_seat_time", "bookings", ["seat_id", "start_time", "end_time"], unique=False)
    op.create_index("idx_bookings_user_time", "bookings", ["user_id", "start_time"], unique=False)
    op.create_index(
        "idx_bookings_active_seat_time",
        "bookings",
        ["seat_id", "start_time", "end_time"],
        unique=False,
        postgresql_where=sa.text("status = 'confirmed'"),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("booking_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('pending','paid','cancelled','refunded')", name="ck_orders_status"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_id"),
    )


def downgrade() -> None:
    op.drop_table("orders")

    op.drop_index("idx_bookings_active_seat_time", table_name="bookings")
    op.drop_index("idx_bookings_user_time", table_name="bookings")
    op.drop_index("idx_bookings_seat_time", table_name="bookings")
    op.drop_table("bookings")

    op.drop_index("idx_member_cards_user_status", table_name="member_cards")
    op.drop_table("member_cards")

    op.drop_index("idx_seats_store_available", table_name="seats")
    op.drop_index("idx_seats_store_id", table_name="seats")
    op.drop_table("seats")

    op.drop_index("idx_users_role", table_name="users")
    op.drop_table("users")

    op.drop_index("idx_stores_status", table_name="stores")
    op.drop_table("stores")
