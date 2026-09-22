from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint("store_id", "seat_no", name="uq_seats_store_seat_no"),
        CheckConstraint(
            "seat_status IN ('available','maintenance','disabled')",
            name="ck_seats_status",
        ),
        Index("idx_seats_store_id", "store_id"),
        Index("idx_seats_store_available", "store_id", "is_available"),
        Index("idx_seats_store_status", "store_id", "seat_status"),
        Index("idx_seats_area_id", "area_id"),
        Index("idx_seats_store_area_status", "store_id", "area_id", "seat_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
    )
    area_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("areas.id", ondelete="SET NULL"),
        nullable=True,
    )
    seat_no: Mapped[str] = mapped_column(String(30), nullable=False)
    seat_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="normal",
        server_default=text("'normal'"),
    )
    seat_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="available",
        server_default=text("'available'"),
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
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
