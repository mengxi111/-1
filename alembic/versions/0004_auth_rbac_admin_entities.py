"""add auth/rbac tables and admin entities

Revision ID: 0004_auth_rbac_admin_entities
Revises: 0003_user_password_hash
Create Date: 2026-03-03 11:20:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_auth_rbac_admin_entities"
down_revision: str | None = "0003_user_password_hash"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "areas",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "code", name="uq_areas_store_code"),
    )
    op.create_index("idx_areas_store_id", "areas", ["store_id"], unique=False)

    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.alter_column("users", "phone", existing_type=sa.String(length=20), nullable=True)
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('student','staff','admin','super_admin')",
    )

    op.add_column("seats", sa.Column("area_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "seats",
        sa.Column("seat_status", sa.String(length=20), server_default=sa.text("'available'"), nullable=False),
    )
    op.create_foreign_key("fk_seats_area_id", "seats", "areas", ["area_id"], ["id"], ondelete="SET NULL")
    op.create_check_constraint("ck_seats_status", "seats", "seat_status IN ('available','maintenance','disabled')")
    op.create_index("idx_seats_store_status", "seats", ["store_id", "seat_status"], unique=False)
    op.create_index("idx_seats_area_id", "seats", ["area_id"], unique=False)

    op.create_table(
        "pricing_plans",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("billing_type", sa.String(length=20), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("billing_type IN ('hour','day','month')", name="ck_pricing_plans_billing_type"),
        sa.CheckConstraint("status IN ('active','inactive')", name="ck_pricing_plans_status"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_pricing_plans_store_id", "pricing_plans", ["store_id"], unique=False)

    op.create_table(
        "notices",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'offline'"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('published','offline')", name="ck_notices_status"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_notices_store_id", "notices", ["store_id"], unique=False)
    op.create_index("idx_notices_status", "notices", ["status"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)
    op.create_index("idx_refresh_tokens_jti", "refresh_tokens", ["jti"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_refresh_tokens_jti", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("idx_notices_status", table_name="notices")
    op.drop_index("idx_notices_store_id", table_name="notices")
    op.drop_table("notices")

    op.drop_index("idx_pricing_plans_store_id", table_name="pricing_plans")
    op.drop_table("pricing_plans")

    op.drop_index("idx_seats_area_id", table_name="seats")
    op.drop_index("idx_seats_store_status", table_name="seats")
    op.drop_constraint("ck_seats_status", "seats", type_="check")
    op.drop_constraint("fk_seats_area_id", "seats", type_="foreignkey")
    op.drop_column("seats", "seat_status")
    op.drop_column("seats", "area_id")

    op.drop_constraint("ck_users_role", "users", type_="check")
    op.create_check_constraint("ck_users_role", "users", "role IN ('student','admin')")
    op.alter_column("users", "phone", existing_type=sa.String(length=20), nullable=False)
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.drop_column("users", "email")

    op.drop_index("idx_areas_store_id", table_name="areas")
    op.drop_table("areas")
