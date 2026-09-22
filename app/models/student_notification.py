from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudentNotification(Base):
    __tablename__ = "student_notifications"
    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('booking','notice','violation','system')",
            name="ck_student_notifications_type",
        ),
        CheckConstraint(
            "email_status IN ('pending','sent','failed','skipped')",
            name="ck_student_notifications_email_status",
        ),
        Index("idx_student_notifications_user_read_created", "user_id", "is_read", "created_at"),
        Index("idx_student_notifications_email_status_created", "email_status", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="system",
        server_default=text("'system'"),
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="skipped",
        server_default=text("'skipped'"),
    )
    email_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    emailed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    related_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
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
