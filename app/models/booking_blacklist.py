from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BookingBlacklist(Base):
    __tablename__ = "booking_blacklists"
    __table_args__ = (
        CheckConstraint("source IN ('auto_no_show','manual')", name="ck_booking_blacklists_source"),
        Index("idx_booking_blacklists_user_id", "user_id", unique=True),
        Index("idx_booking_blacklists_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="manual",
        server_default=text("'manual'"),
    )
    no_show_count_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
