from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notice import Notice
from app.models.student_notification import StudentNotification
from app.models.user import User
from app.services.email_sender import EmailDeliveryError, send_email


NOTIFICATION_TYPE_TEXT = {
    "booking": "预约通知",
    "notice": "系统公告",
    "violation": "违规提醒",
    "system": "系统通知",
}

EMAIL_STATUS_TEXT = {
    "pending": "待发送",
    "sent": "已发送",
    "failed": "发送失败",
    "skipped": "未发送",
}


@dataclass
class NotificationEmailJobResult:
    pending_count: int = 0
    sent_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0


def _initial_email_status(email: str | None) -> str:
    if not settings.email_enabled:
        return "skipped"
    if not email:
        return "skipped"
    return "pending"


def queue_student_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    content: str,
    notification_type: str,
    related_type: str | None = None,
    related_id: int | None = None,
    commit: bool = True,
) -> StudentNotification:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("用户不存在")

    notification = StudentNotification(
        user_id=user_id,
        title=title,
        content=content,
        notification_type=notification_type,
        related_type=related_type,
        related_id=related_id,
        email_status=_initial_email_status(user.email),
    )
    db.add(notification)
    if commit:
        db.commit()
        db.refresh(notification)
    else:
        db.flush()
    return notification


def queue_notice_notifications_for_students(
    db: Session,
    *,
    notice: Notice,
    commit: bool = True,
) -> int:
    rows = db.execute(
        select(User.id, User.email)
        .where(User.role == "student", User.status == 1)
        .order_by(User.id)
    ).all()

    if not rows:
        return 0

    notifications = [
        StudentNotification(
            user_id=row.id,
            title=f"公告通知：{notice.title}",
            content=notice.content,
            notification_type="notice",
            related_type="notice",
            related_id=notice.id,
            email_status=_initial_email_status(row.email),
        )
        for row in rows
    ]
    db.add_all(notifications)
    if commit:
        db.commit()
    else:
        db.flush()
    return len(notifications)


def list_student_notifications(
    db: Session,
    *,
    user_id: int,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 20,
) -> tuple[int, int, list[StudentNotification]]:
    base_stmt = select(StudentNotification).where(StudentNotification.user_id == user_id)
    total_stmt = select(func.count(StudentNotification.id)).where(StudentNotification.user_id == user_id)
    unread_count_stmt = select(func.count(StudentNotification.id)).where(
        StudentNotification.user_id == user_id,
        StudentNotification.is_read.is_(False),
    )

    if unread_only:
        base_stmt = base_stmt.where(StudentNotification.is_read.is_(False))
        total_stmt = total_stmt.where(StudentNotification.is_read.is_(False))

    items = list(
        db.scalars(
            base_stmt.order_by(StudentNotification.id.desc()).offset(skip).limit(limit)
        ).all()
    )
    total = int(db.execute(total_stmt).scalar_one() or 0)
    unread_count = int(db.execute(unread_count_stmt).scalar_one() or 0)
    return total, unread_count, items


def get_student_notification(db: Session, notification_id: int, user_id: int) -> StudentNotification | None:
    return db.execute(
        select(StudentNotification).where(
            StudentNotification.id == notification_id,
            StudentNotification.user_id == user_id,
        )
    ).scalar_one_or_none()


def mark_student_notification_read(
    db: Session,
    *,
    notification: StudentNotification,
) -> StudentNotification:
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.add(notification)
        db.commit()
        db.refresh(notification)
    return notification


def mark_all_student_notifications_read(db: Session, *, user_id: int) -> int:
    now = datetime.now(timezone.utc)
    result = db.execute(
        update(StudentNotification)
        .where(StudentNotification.user_id == user_id, StudentNotification.is_read.is_(False))
        .values(is_read=True, read_at=now, updated_at=now)
    )
    db.commit()
    return int(result.rowcount or 0)


def _build_email_subject(notification: StudentNotification) -> str:
    return f"[自习室管理系统] {notification.title}"


def _build_email_text(notification: StudentNotification, user_name: str | None) -> str:
    return (
        f"{user_name or '同学'}，您好：\n\n"
        f"{notification.title}\n\n"
        f"{notification.content}\n\n"
        "请登录自习室管理系统查看详情。"
    )


def _build_email_html(notification: StudentNotification, user_name: str | None) -> str:
    safe_title = notification.title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_content = (
        notification.content.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )
    return (
        "<div style='font-family:Segoe UI,Microsoft YaHei,sans-serif;color:#1f2937;'>"
        f"<p>{user_name or '同学'}，您好：</p>"
        f"<h3 style='margin:0 0 12px 0;color:#111827;'>{safe_title}</h3>"
        f"<p style='line-height:1.7;'>{safe_content}</p>"
        "<p style='margin-top:16px;color:#6b7280;'>请登录自习室管理系统查看详情。</p>"
        "</div>"
    )


def send_pending_notification_emails(db: Session, *, limit: int | None = None) -> NotificationEmailJobResult:
    batch_limit = max(1, limit or settings.email_send_batch_size)
    rows = db.execute(
        select(StudentNotification, User.email, User.name)
        .join(User, User.id == StudentNotification.user_id)
        .where(StudentNotification.email_status == "pending")
        .order_by(StudentNotification.id.asc())
        .limit(batch_limit)
    ).all()

    result = NotificationEmailJobResult(pending_count=len(rows))
    if not rows:
        return result

    now = datetime.now(timezone.utc)
    for notification, email, user_name in rows:
        if not email:
            notification.email_status = "skipped"
            notification.email_error = "用户未配置邮箱"
            notification.updated_at = now
            db.add(notification)
            db.commit()
            result.skipped_count += 1
            continue

        try:
            send_email(
                recipient=email,
                subject=_build_email_subject(notification),
                text_content=_build_email_text(notification, user_name),
                html_content=_build_email_html(notification, user_name),
            )
        except EmailDeliveryError as exc:
            notification.email_status = "failed"
            notification.email_error = str(exc)
            notification.updated_at = now
            db.add(notification)
            db.commit()
            result.failed_count += 1
            continue

        notification.email_status = "sent"
        notification.emailed_at = now
        notification.email_error = None
        notification.updated_at = now
        db.add(notification)
        db.commit()
        result.sent_count += 1

    return result
