from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BookingCheckinRecord(Base):
    __tablename__ = "booking_checkin_records"
    __table_args__ = (
        UniqueConstraint("booking_id", name="uq_booking_checkin_records_booking_id"),
        CheckConstraint("checkin_method IN ('code','qr_simulated')", name="ck_booking_checkin_records_method"),
        Index("idx_booking_checkin_records_store_time", "store_id", "checkin_time"),
        Index("idx_booking_checkin_records_user_time", "user_id", "checkin_time"),
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
    store_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("stores.id", ondelete="SET NULL"),
        nullable=True,
    )
    checkin_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    checkin_method: Mapped[str] = mapped_column(String(20), nullable=False)
    qr_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
