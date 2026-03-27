from datetime import datetime, time

from sqlalchemy import BigInteger, DateTime, Index, SmallInteger, String, Text, Time, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Store(Base):
    __tablename__ = "stores"
    __table_args__ = (Index("idx_stores_status", "status"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, server_default=text("1"))
    open_time: Mapped[time] = mapped_column(
        Time(),
        nullable=False,
        server_default=text("'08:00:00'"),
    )
    close_time: Mapped[time] = mapped_column(
        Time(),
        nullable=False,
        server_default=text("'23:00:00'"),
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
