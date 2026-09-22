from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AdminOperationLog(Base):
    __tablename__ = "admin_operation_logs"
    __table_args__ = (
        Index("idx_admin_operation_logs_created_at", "created_at"),
        Index("idx_admin_operation_logs_module", "module"),
        Index("idx_admin_operation_logs_operator_id", "operator_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    operator_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    operator_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    operator_role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    request_method: Mapped[str] = mapped_column(String(10), nullable=False)
    request_path: Mapped[str] = mapped_column(String(255), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
