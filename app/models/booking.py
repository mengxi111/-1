from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_bookings_time_window"),
        CheckConstraint(
            "status IN ('booked','checked_in','cancelled','expired','completed')",
            name="ck_bookings_status",
        ),
        Index("idx_bookings_seat_time", "seat_id", "start_time", "end_time"),
        Index("idx_bookings_user_time", "user_id", "start_time"),
        Index("idx_bookings_status_start_time", "status", "start_time"),
        Index("idx_bookings_user_status", "user_id", "status"),
        Index("idx_bookings_store_start_time", "store_id", "start_time"),
        Index(
            "idx_bookings_active_seat_time",
            "seat_id",
            "start_time",
            "end_time",
            postgresql_where=text("status IN ('booked','checked_in')"),
        ),
        ExcludeConstraint(
            ("seat_id", "="),
            (text("tstzrange(start_time, end_time, '[)')"), "&&"),
            where=text("status IN ('booked','checked_in')"),
            using="gist",
            name="ex_bookings_active_seat_time",
        ),
        ExcludeConstraint(
            ("user_id", "="),
            (text("tstzrange(start_time, end_time, '[)')"), "&&"),
            where=text("status IN ('booked','checked_in')"),
            using="gist",
            name="ex_bookings_active_user_time",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    store_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("stores.id", ondelete="RESTRICT"),
        nullable=False,
    )
    seat_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("seats.id", ondelete="RESTRICT"),
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="booked",
        server_default=text("'booked'"),
    )
    checkin_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    checkin_code_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sign_in_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expire_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    qr_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    qr_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
