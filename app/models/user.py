from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, Integer, SmallInteger, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('student','staff','admin','super_admin')", name="ck_users_role"),
        CheckConstraint("no_show_count >= 0", name="ck_users_no_show_count"),
        Index("idx_users_role", "role"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, server_default=text("1"))
    no_show_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
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
