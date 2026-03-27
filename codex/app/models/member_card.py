from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MemberCard(Base):
    __tablename__ = "member_cards"
    __table_args__ = (
        CheckConstraint("card_type IN ('time','times')", name="ck_member_cards_card_type"),
        CheckConstraint("status IN ('active','expired','disabled')", name="ck_member_cards_status"),
        Index("idx_member_cards_user_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    card_name: Mapped[str] = mapped_column(String(50), nullable=False)
    card_type: Mapped[str] = mapped_column(String(20), nullable=False)
    balance_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    balance_times: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    expire_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default=text("'active'"),
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
