from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BookingReleaseLog(Base):
    __tablename__ = "booking_release_logs"
    __table_args__ = (
        Index("idx_booking_release_logs_booking_id", "booking_id"),
        Index("idx_booking_release_logs_released_at", "released_at"),
        Index("idx_booking_release_logs_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    seat_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("seats.id", ondelete="CASCADE"),
        nullable=False,
    )
    release_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="auto_timeout",
        server_default=text("'auto_timeout'"),
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    released_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
