from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PricingPlan(Base):
    __tablename__ = "pricing_plans"
    __table_args__ = (
        CheckConstraint("billing_type IN ('hour','day','month')", name="ck_pricing_plans_billing_type"),
        CheckConstraint("status IN ('active','inactive')", name="ck_pricing_plans_status"),
        Index("idx_pricing_plans_store_id", "store_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    billing_type: Mapped[str] = mapped_column(String(20), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    min_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30, server_default=text("30"))
    max_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=720, server_default=text("720"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'active'"), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
