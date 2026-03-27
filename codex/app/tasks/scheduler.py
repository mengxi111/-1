import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.crud.booking import complete_finished_bookings, expire_unchecked_bookings, send_upcoming_booking_reminders
from app.crud.student_notification import send_pending_notification_emails
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def run_expire_job() -> None:
    db = SessionLocal()
    try:
        result = expire_unchecked_bookings(db)
        if result.expired_count > 0 or result.auto_blacklisted_count > 0:
            logger.info(
                "自动过期任务完成: 自动取消=%s, 释放日志=%s, 爽约用户数=%s, 自动拉黑=%s",
                result.expired_count,
                result.release_log_count,
                result.users_incremented,
                result.auto_blacklisted_count,
            )
    finally:
        db.close()


def run_complete_job() -> None:
    db = SessionLocal()
    try:
        result = complete_finished_bookings(db)
        if result.completed_count > 0:
            logger.info("自动完成任务完成: 已完成=%s", result.completed_count)
    finally:
        db.close()


def run_notification_email_job() -> None:
    if not settings.email_enabled:
        return

    db = SessionLocal()
    try:
        result = send_pending_notification_emails(db, limit=settings.email_send_batch_size)
        if result.pending_count > 0:
            logger.info(
                "通知邮件任务完成: 待处理=%s, 发送成功=%s, 发送失败=%s, 跳过=%s",
                result.pending_count,
                result.sent_count,
                result.failed_count,
                result.skipped_count,
            )
    finally:
        db.close()


def run_booking_reminder_job() -> None:
    db = SessionLocal()
    try:
        sent_count = send_upcoming_booking_reminders(db)
        if sent_count > 0:
            logger.info("预约提醒任务完成: 发送提醒=%s", sent_count)
    finally:
        db.close()


scheduler = BackgroundScheduler(timezone=settings.timezone)
scheduler.add_job(
    run_expire_job,
    trigger="interval",
    seconds=settings.expire_job_interval_seconds,
    id="expire_unchecked_bookings",
    replace_existing=True,
    coalesce=True,
    max_instances=1,
)
scheduler.add_job(
    run_complete_job,
    trigger="interval",
    seconds=settings.expire_job_interval_seconds,
    id="complete_finished_bookings",
    replace_existing=True,
    coalesce=True,
    max_instances=1,
)
scheduler.add_job(
    run_notification_email_job,
    trigger="interval",
    seconds=settings.email_job_interval_seconds,
    id="send_notification_emails",
    replace_existing=True,
    coalesce=True,
    max_instances=1,
)
scheduler.add_job(
    run_booking_reminder_job,
    trigger="interval",
    seconds=settings.expire_job_interval_seconds,
    id="send_booking_reminders",
    replace_existing=True,
    coalesce=True,
    max_instances=1,
)
