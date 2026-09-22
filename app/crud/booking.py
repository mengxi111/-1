import random
import secrets
from collections import Counter
from dataclasses import dataclass
from datetime import date as date_type
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from redis import Redis
from sqlalchemy import Select, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.booking_blacklist import add_user_to_blacklist, is_user_blacklisted
from app.crud.system_setting import get_setting_int
from app.crud.student_notification import queue_student_notification
from app.models.booking import Booking
from app.models.booking_checkin_record import BookingCheckinRecord
from app.models.booking_release_log import BookingReleaseLog
from app.models.student_notification import StudentNotification
from app.models.seat import Seat
from app.models.store import Store
from app.models.user import User
from app.schemas.booking import BookingCheckinRequest, BookingCreate
from app.services.booking_lock import (
    RedisLockBusyError,
    RedisUnavailableError,
    build_booking_lock_key,
    redis_booking_lock,
)

POSTGRES_EXCLUSION_VIOLATION = "23P01"
ACTIVE_BOOKING_STATUSES = ("booked", "checked_in")
USER_TIME_CONFLICT_CONSTRAINT = "ex_bookings_active_user_time"
STATUS_TRANSITIONS: dict[str, set[str]] = {
    "booked": {"checked_in", "cancelled", "expired"},
    "checked_in": {"completed"},
    "completed": set(),
    "cancelled": set(),
    "expired": set(),
}


def _rule_min_booking_minutes(db: Session) -> int:
    return max(1, get_setting_int(db, "min_booking_minutes", settings.min_booking_minutes))


def _rule_max_booking_hours(db: Session) -> int:
    return max(1, get_setting_int(db, "max_booking_hours", settings.max_booking_hours))


def _rule_cancel_before_minutes(db: Session) -> int:
    return max(0, get_setting_int(db, "cancel_before_minutes", settings.cancel_before_minutes))


def _rule_reschedule_before_minutes(db: Session) -> int:
    return max(0, get_setting_int(db, "reschedule_before_minutes", settings.reschedule_before_minutes))


def _rule_checkin_grace_minutes(db: Session) -> int:
    return max(1, get_setting_int(db, "checkin_grace_minutes", settings.checkin_grace_minutes))


def _rule_no_show_blacklist_threshold(db: Session) -> int:
    return max(1, get_setting_int(db, "no_show_blacklist_threshold", settings.no_show_blacklist_threshold))


def _rule_blacklist_effective_days(db: Session) -> int:
    return max(1, get_setting_int(db, "blacklist_effective_days", settings.blacklist_effective_days))


class BookingConflictError(Exception):
    pass


class UserBookingConflictError(Exception):
    pass


class SeatNotFoundError(Exception):
    pass


class SeatUnavailableError(Exception):
    pass


class StoreBusinessHourError(Exception):
    pass


class BookingNotFoundError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserBlacklistedError(Exception):
    pass


class SeatLockBusyError(Exception):
    pass


class LockServiceUnavailableError(Exception):
    pass


class BookingStateError(Exception):
    pass


class BookingPermissionError(Exception):
    pass


class BookingValidationError(Exception):
    pass


class VerificationCodeError(Exception):
    pass


class QRCodeInvalidError(Exception):
    pass


class QRCodeExpiredError(Exception):
    pass


@dataclass
class ExpireJobResult:
    expired_count: int = 0
    users_incremented: int = 0
    auto_blacklisted_count: int = 0
    release_log_count: int = 0


@dataclass
class CompleteJobResult:
    completed_count: int = 0


def _format_notification_time(value: datetime) -> str:
    local_value = _normalize_to_utc(value).astimezone(ZoneInfo(settings.timezone))
    return local_value.strftime("%Y-%m-%d %H:%M")


def _normalize_to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _normalize_time_window(start_time: datetime, end_time: datetime) -> tuple[datetime, datetime]:
    start_at = _normalize_to_utc(start_time)
    end_at = _normalize_to_utc(end_time)
    if end_at <= start_at:
        raise BookingValidationError("开始时间必须早于结束时间")
    return start_at, end_at


def _ensure_booking_rule_time_window(
    db: Session,
    start_time: datetime,
    end_time: datetime,
    now: datetime,
) -> None:
    start_at, end_at = _normalize_time_window(start_time, end_time)
    min_booking_minutes = _rule_min_booking_minutes(db)
    max_booking_hours = _rule_max_booking_hours(db)

    duration_minutes = (end_at - start_at).total_seconds() / 60
    if duration_minutes < min_booking_minutes:
        raise BookingValidationError(f"预约时长不能少于{min_booking_minutes}分钟")
    if duration_minutes > max_booking_hours * 60:
        raise BookingValidationError(f"预约时长不能超过{max_booking_hours}小时")
    if not settings.allow_booking_start_in_past and start_at < now:
        raise BookingValidationError("开始时间不得早于当前时间")


def _is_exclusion_violation(error: IntegrityError) -> bool:
    code = getattr(error.orig, "pgcode", None) or getattr(error.orig, "sqlstate", None)
    return code == POSTGRES_EXCLUSION_VIOLATION


def _is_user_time_conflict_violation(error: IntegrityError) -> bool:
    return USER_TIME_CONFLICT_CONSTRAINT in str(error.orig)


def _gen_checkin_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def _gen_qr_token() -> str:
    return secrets.token_urlsafe(24)


def _transition_status(booking: Booking, target_status: str) -> None:
    if booking.status == target_status:
        return
    allowed_targets = STATUS_TRANSITIONS.get(booking.status, set())
    if target_status not in allowed_targets:
        raise BookingStateError("当前预约状态不可执行该操作")
    booking.status = target_status


def _ensure_checkin_allowed_status(booking: Booking) -> None:
    if booking.status == "checked_in":
        raise BookingStateError("预约已签到，请勿重复签到")
    if booking.status == "expired":
        raise BookingStateError("预约已超时未签到，系统已自动取消")
    if booking.status == "cancelled":
        raise BookingStateError("预约已取消，无法签到")
    if booking.status == "completed":
        raise BookingStateError("预约已完成，无法签到")
    if booking.status != "booked":
        raise BookingStateError("当前预约状态不可签到")


def _ensure_checkin_time_window(db: Session, booking: Booking, now: datetime) -> None:
    if now < booking.start_time or now > booking.end_time:
        raise BookingStateError("当前时间不在预约范围内")
    if now > booking.start_time + timedelta(minutes=_rule_checkin_grace_minutes(db)):
        raise BookingStateError("签到时间已超时")


def _is_time_in_business_window(
    current_time,
    open_time,
    close_time,
    *,
    include_right: bool,
) -> bool:
    if open_time < close_time:
        if include_right:
            return open_time <= current_time <= close_time
        return open_time <= current_time < close_time

    # 跨天营业（例如 22:00-06:00）
    if include_right:
        return current_time >= open_time or current_time <= close_time
    return current_time >= open_time or current_time < close_time


def _ensure_store_open_for_period(store: Store, start_time: datetime, end_time: datetime) -> None:
    if store.status != 1:
        raise StoreBusinessHourError("所选时间不在门店营业时间内")

    zone = ZoneInfo(settings.timezone)
    local_start = start_time.astimezone(zone)
    local_end = end_time.astimezone(zone)

    if store.open_time < store.close_time and local_start.date() != local_end.date():
        raise StoreBusinessHourError("所选时间不在门店营业时间内")

    if not _is_time_in_business_window(
        local_start.time(),
        store.open_time,
        store.close_time,
        include_right=False,
    ):
        raise StoreBusinessHourError("所选时间不在门店营业时间内")

    if not _is_time_in_business_window(
        local_end.time(),
        store.open_time,
        store.close_time,
        include_right=True,
    ):
        raise StoreBusinessHourError("所选时间不在门店营业时间内")


def _ensure_seat_store_bookable(seat: Seat, store: Store, start_time: datetime, end_time: datetime) -> None:
    if not seat.is_available or seat.seat_status != "available":
        raise SeatUnavailableError("该座位当前不可用，请选择其他座位")
    _ensure_store_open_for_period(store, start_time, end_time)


def _build_booking_overlap_stmt(
    *,
    seat_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: int | None = None,
) -> Select:
    stmt = (
        select(Booking.id)
        .where(
            Booking.seat_id == seat_id,
            Booking.status.in_(ACTIVE_BOOKING_STATUSES),
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )
        .limit(1)
    )
    if exclude_booking_id is not None:
        stmt = stmt.where(Booking.id != exclude_booking_id)
    return stmt


def _build_user_booking_overlap_stmt(
    *,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: int | None = None,
) -> Select:
    stmt = (
        select(Booking.id)
        .where(
            Booking.user_id == user_id,
            Booking.status.in_(ACTIVE_BOOKING_STATUSES),
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )
        .limit(1)
    )
    if exclude_booking_id is not None:
        stmt = stmt.where(Booking.id != exclude_booking_id)
    return stmt


def _ensure_booking_not_conflict(
    db: Session,
    *,
    seat_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: int | None = None,
) -> None:
    overlap_exists = db.execute(
        _build_booking_overlap_stmt(
            seat_id=seat_id,
            start_time=start_time,
            end_time=end_time,
            exclude_booking_id=exclude_booking_id,
        )
    ).scalar_one_or_none()
    if overlap_exists is not None:
        raise BookingConflictError("该座位在所选时间段已被预约，请更换时间或座位")


def _ensure_user_booking_not_conflict(
    db: Session,
    *,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: int | None = None,
) -> None:
    overlap_exists = db.execute(
        _build_user_booking_overlap_stmt(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            exclude_booking_id=exclude_booking_id,
        )
    ).scalar_one_or_none()
    if overlap_exists is not None:
        raise UserBookingConflictError("您在该时间段内已有其他预约，不能重复预约多个座位")


def _get_store_id_by_seat(db: Session, seat_id: int) -> int | None:
    return db.execute(select(Seat.store_id).where(Seat.id == seat_id)).scalar_one_or_none()


def _business_window_for_date(store: Store, target_date: date_type, zone: ZoneInfo) -> tuple[datetime, datetime]:
    local_start = datetime.combine(target_date, store.open_time, tzinfo=zone)
    local_end = datetime.combine(target_date, store.close_time, tzinfo=zone)
    if store.open_time >= store.close_time:
        local_end += timedelta(days=1)
    return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)


def _ceil_to_next_minute(value: datetime) -> datetime:
    normalized = value.replace(second=0, microsecond=0)
    if normalized < value:
        normalized += timedelta(minutes=1)
    return normalized


def get_seat_available_slots_for_date(
    db: Session,
    *,
    seat_id: int,
    target_date: date_type | None = None,
    now: datetime | None = None,
) -> dict:
    seat_store_row = db.execute(
        select(Seat, Store)
        .join(Store, Store.id == Seat.store_id)
        .where(Seat.id == seat_id)
    ).first()
    if seat_store_row is None:
        raise SeatNotFoundError("座位不存在")

    seat, store = seat_store_row
    if not seat.is_available or seat.seat_status != "available":
        raise SeatUnavailableError("该座位当前不可用，请选择其他座位")
    if store.status != 1:
        raise StoreBusinessHourError("门店当前不可用")

    zone = ZoneInfo(settings.timezone)
    reference_now = _normalize_to_utc(now or datetime.now(timezone.utc))
    local_now = reference_now.astimezone(zone)
    slot_date = target_date or local_now.date()

    business_start, business_end = _business_window_for_date(store, slot_date, zone)
    if slot_date == local_now.date():
        business_start = max(business_start, _ceil_to_next_minute(reference_now))

    available_slots: list[dict] = []
    min_booking_minutes = _rule_min_booking_minutes(db)
    min_duration = timedelta(minutes=min_booking_minutes)

    if business_start < business_end:
        active_bookings = list(
            db.scalars(
                select(Booking)
                .where(
                    Booking.seat_id == seat.id,
                    Booking.status.in_(ACTIVE_BOOKING_STATUSES),
                    Booking.start_time < business_end,
                    Booking.end_time > business_start,
                )
                .order_by(Booking.start_time.asc())
            ).all()
        )

        cursor = business_start
        for booking in active_bookings:
            if booking.start_time > cursor:
                gap_end = min(booking.start_time, business_end)
                if gap_end - cursor >= min_duration:
                    slot_start = cursor.astimezone(zone)
                    slot_end = gap_end.astimezone(zone)
                    available_slots.append(
                        {
                            "start_time": slot_start,
                            "end_time": slot_end,
                            "duration_minutes": int((slot_end - slot_start).total_seconds() // 60),
                        }
                    )
            cursor = max(cursor, booking.end_time)
            if cursor >= business_end:
                break

        if business_end - cursor >= min_duration:
            slot_start = cursor.astimezone(zone)
            slot_end = business_end.astimezone(zone)
            available_slots.append(
                {
                    "start_time": slot_start,
                    "end_time": slot_end,
                    "duration_minutes": int((slot_end - slot_start).total_seconds() // 60),
                }
            )

    return {
        "seat_id": seat.id,
        "seat_no": seat.seat_no,
        "store_id": store.id,
        "store_name": store.name,
        "date": slot_date.isoformat(),
        "timezone": settings.timezone,
        "open_time": store.open_time.isoformat(),
        "close_time": store.close_time.isoformat(),
        "business_start": business_start.astimezone(zone),
        "business_end": business_end.astimezone(zone),
        "min_booking_minutes": min_booking_minutes,
        "available_slots": available_slots,
    }


def _reset_no_show_count(db: Session, user_id: int, now: datetime) -> None:
    db.execute(
        update(User)
        .where(User.id == user_id, User.no_show_count > 0)
        .values(no_show_count=0, updated_at=now)
    )


def _create_checkin_record(
    db: Session,
    *,
    booking: Booking,
    checkin_time: datetime,
    method: str,
    qr_token: str | None = None,
) -> None:
    store_id = _get_store_id_by_seat(db, booking.seat_id)
    db.add(
        BookingCheckinRecord(
            booking_id=booking.id,
            user_id=booking.user_id,
            seat_id=booking.seat_id,
            store_id=store_id,
            checkin_time=checkin_time,
            checkin_method=method,
            qr_token=qr_token,
        )
    )


def can_checkin_now(booking: Booking, now: datetime | None = None) -> bool:
    check_time = _normalize_to_utc(now or datetime.now(timezone.utc))
    if booking.status != "booked":
        return False
    if check_time < booking.start_time or check_time > booking.end_time:
        return False
    if check_time > booking.start_time + timedelta(minutes=settings.checkin_grace_minutes):
        return False
    return True


def _get_store_id_for_seat_lock(db: Session, seat_id: int) -> int:
    store_id = db.execute(
        select(Seat.store_id).where(Seat.id == seat_id).limit(1)
    ).scalar_one_or_none()
    if store_id is None:
        raise SeatNotFoundError("座位不存在")
    return int(store_id)


def _create_booking_transaction(
    db: Session,
    *,
    seat_id: int,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
) -> Booking:
    seat_store_row = db.execute(
        select(Seat, Store)
        .join(Store, Store.id == Seat.store_id)
        .where(Seat.id == seat_id)
        .with_for_update()
    ).first()
    if seat_store_row is None:
        raise SeatNotFoundError("座位不存在")
    seat, store = seat_store_row
    _ensure_seat_store_bookable(seat, store, start_time, end_time)

    user_exists = db.execute(
        select(User.id).where(User.id == user_id).with_for_update()
    ).scalar_one_or_none()
    if user_exists is None:
        raise UserNotFoundError("用户不存在")
    if is_user_blacklisted(db, user_id):
        raise UserBlacklistedError("黑名单用户禁止预约")

    _ensure_user_booking_not_conflict(
        db,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
    )
    _ensure_booking_not_conflict(
        db,
        seat_id=seat_id,
        start_time=start_time,
        end_time=end_time,
    )

    booking = Booking(
        seat_id=seat_id,
        user_id=user_id,
        store_id=seat.store_id,
        start_time=start_time,
        end_time=end_time,
        status="booked",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def create_booking_with_lock(db: Session, redis_client: Redis, payload: BookingCreate) -> Booking:
    if payload.user_id is None:
        raise UserNotFoundError("用户不存在")

    now = datetime.now(timezone.utc)
    start_time, end_time = _normalize_time_window(payload.start_time, payload.end_time)
    _ensure_booking_rule_time_window(db, start_time, end_time, now)
    store_id = _get_store_id_for_seat_lock(db, payload.seat_id)
    lock_key = build_booking_lock_key(store_id, payload.seat_id)

    try:
        with redis_booking_lock(redis_client, lock_key, settings.redis_lock_ttl_ms):
            return _create_booking_transaction(
                db,
                seat_id=payload.seat_id,
                user_id=payload.user_id,
                start_time=start_time,
                end_time=end_time,
            )
    except RedisLockBusyError as exc:
        raise SeatLockBusyError("座位正在被其他用户预约，请稍后重试") from exc
    except RedisUnavailableError as exc:
        if settings.redis_lock_required:
            raise LockServiceUnavailableError("预约锁服务不可用，请稍后重试") from exc
        try:
            return _create_booking_transaction(
                db,
                seat_id=payload.seat_id,
                user_id=payload.user_id,
                start_time=start_time,
                end_time=end_time,
            )
        except IntegrityError as fallback_exc:
            db.rollback()
            if _is_exclusion_violation(fallback_exc):
                if _is_user_time_conflict_violation(fallback_exc):
                    raise UserBookingConflictError("您在该时间段内已有其他预约，不能重复预约多个座位") from fallback_exc
                raise BookingConflictError("该座位在所选时间段已被预约，请更换时间或座位") from fallback_exc
            raise
        except Exception:
            db.rollback()
            raise
    except IntegrityError as exc:
        db.rollback()
        if _is_exclusion_violation(exc):
            if _is_user_time_conflict_violation(exc):
                raise UserBookingConflictError("您在该时间段内已有其他预约，不能重复预约多个座位") from exc
            raise BookingConflictError("该座位在所选时间段已被预约，请更换时间或座位") from exc
        raise
    except Exception:
        db.rollback()
        raise


def list_bookings(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
) -> list[Booking]:
    stmt = select(Booking)
    if user_id is not None:
        stmt = stmt.where(Booking.user_id == user_id)
    stmt = stmt.offset(skip).limit(limit).order_by(Booking.id.desc())
    return list(db.scalars(stmt).all())


def list_admin_bookings(
    db: Session,
    *,
    booking_status: str | None = None,
    store_id: int | None = None,
    user_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Booking]:
    stmt = select(Booking)
    if booking_status:
        stmt = stmt.where(Booking.status == booking_status)
    if store_id is not None:
        stmt = stmt.where(Booking.store_id == store_id)
    if user_id is not None:
        stmt = stmt.where(Booking.user_id == user_id)
    if start_from is not None:
        stmt = stmt.where(Booking.start_time >= _normalize_to_utc(start_from))
    if start_to is not None:
        stmt = stmt.where(Booking.start_time <= _normalize_to_utc(start_to))
    stmt = stmt.offset(skip).limit(limit).order_by(Booking.id.desc())
    return list(db.scalars(stmt).all())


def get_booking(db: Session, booking_id: int) -> Booking | None:
    return db.get(Booking, booking_id)


def cancel_booking(db: Session, booking: Booking) -> Booking:
    now = datetime.now(timezone.utc)
    if booking.status != "booked":
        raise BookingStateError("当前预约状态不可取消")
    deadline = booking.start_time - timedelta(minutes=_rule_cancel_before_minutes(db))
    if now > deadline:
        raise BookingStateError("已超过可取消时间，无法取消预约")

    _transition_status(booking, "cancelled")
    booking.cancel_reason = "学生主动取消"
    booking.checkin_code = None
    booking.checkin_code_expires_at = None
    booking.qr_token = None
    booking.qr_token_expires_at = None
    _reset_no_show_count(db, booking.user_id, now)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def checkin_booking(db: Session, booking_id: int, payload: BookingCheckinRequest) -> tuple[Booking, str, str | None]:
    now = datetime.now(timezone.utc)
    try:
        booking = db.execute(
            select(Booking).where(Booking.id == booking_id).with_for_update()
        ).scalar_one_or_none()
        if booking is None:
            raise BookingNotFoundError("预约不存在")

        if is_user_blacklisted(db, booking.user_id):
            raise UserBlacklistedError("黑名单用户禁止签到")

        if booking.status == "checked_in":
            db.commit()
            return booking, "already_checked_in", None

        _ensure_checkin_allowed_status(booking)
        _ensure_checkin_time_window(db, booking, now)

        if payload.verification_code is None:
            code = _gen_checkin_code()
            booking.checkin_code = code
            booking.checkin_code_expires_at = now + timedelta(minutes=settings.checkin_code_expire_minutes)
            db.add(booking)
            db.commit()
            db.refresh(booking)
            return booking, "code_generated", code

        if booking.checkin_code is None or booking.checkin_code_expires_at is None:
            raise VerificationCodeError("请先获取签到验证码")
        if booking.checkin_code_expires_at <= now:
            raise VerificationCodeError("签到验证码已过期")
        if payload.verification_code != booking.checkin_code:
            raise VerificationCodeError("签到验证码错误")

        _transition_status(booking, "checked_in")
        booking.checked_in_at = now
        booking.sign_in_time = now
        booking.checkin_code = None
        booking.checkin_code_expires_at = None
        booking.qr_token = None
        booking.qr_token_expires_at = None
        db.add(booking)
        _reset_no_show_count(db, booking.user_id, now)
        _create_checkin_record(db, booking=booking, checkin_time=now, method="code")
        db.commit()
        db.refresh(booking)
        return booking, "checked_in", None
    except Exception:
        db.rollback()
        raise


def generate_qr_checkin_token(db: Session, booking_id: int, user_id: int) -> tuple[Booking, str]:
    now = datetime.now(timezone.utc)
    try:
        booking = db.execute(
            select(Booking).where(Booking.id == booking_id).with_for_update()
        ).scalar_one_or_none()
        if booking is None:
            raise BookingNotFoundError("预约不存在")
        if booking.user_id != user_id:
            raise BookingPermissionError("无权操作此预约")
        if is_user_blacklisted(db, booking.user_id):
            raise UserBlacklistedError("黑名单用户禁止签到")

        _ensure_checkin_allowed_status(booking)
        _ensure_checkin_time_window(db, booking, now)

        token = _gen_qr_token()
        booking.qr_token = token
        booking.qr_token_expires_at = now + timedelta(minutes=settings.checkin_qr_expire_minutes)
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking, token
    except Exception:
        db.rollback()
        raise


def checkin_with_qr_token(db: Session, booking_id: int, user_id: int, qr_token: str) -> Booking:
    now = datetime.now(timezone.utc)
    try:
        booking = db.execute(
            select(Booking).where(Booking.id == booking_id).with_for_update()
        ).scalar_one_or_none()
        if booking is None:
            raise BookingNotFoundError("预约不存在")
        if booking.user_id != user_id:
            raise BookingPermissionError("无权操作此预约")
        if is_user_blacklisted(db, booking.user_id):
            raise UserBlacklistedError("黑名单用户禁止签到")

        _ensure_checkin_allowed_status(booking)
        _ensure_checkin_time_window(db, booking, now)

        if not booking.qr_token or not booking.qr_token_expires_at:
            raise QRCodeInvalidError("二维码无效，请重新获取")
        if booking.qr_token_expires_at < now:
            raise QRCodeExpiredError("二维码已过期，请重新获取")
        if booking.qr_token != qr_token:
            raise QRCodeInvalidError("二维码无效，请重新获取")

        _transition_status(booking, "checked_in")
        booking.checked_in_at = now
        booking.sign_in_time = now
        booking.checkin_code = None
        booking.checkin_code_expires_at = None
        booking.qr_token = None
        booking.qr_token_expires_at = None
        db.add(booking)
        _reset_no_show_count(db, booking.user_id, now)
        _create_checkin_record(db, booking=booking, checkin_time=now, method="qr_simulated", qr_token=qr_token)
        db.commit()
        db.refresh(booking)
        return booking
    except Exception:
        db.rollback()
        raise


def signin_booking_now(db: Session, booking_id: int, user_id: int) -> Booking:
    now = datetime.now(timezone.utc)
    try:
        booking = db.execute(
            select(Booking).where(Booking.id == booking_id).with_for_update()
        ).scalar_one_or_none()
        if booking is None:
            raise BookingNotFoundError("预约不存在")
        if booking.user_id != user_id:
            raise BookingPermissionError("无权操作此预约")
        if is_user_blacklisted(db, booking.user_id):
            raise UserBlacklistedError("黑名单用户禁止签到")

        _ensure_checkin_allowed_status(booking)
        _ensure_checkin_time_window(db, booking, now)

        _transition_status(booking, "checked_in")
        booking.checked_in_at = now
        booking.sign_in_time = now
        booking.checkin_code = None
        booking.checkin_code_expires_at = None
        booking.qr_token = None
        booking.qr_token_expires_at = None
        db.add(booking)
        _reset_no_show_count(db, booking.user_id, now)
        _create_checkin_record(db, booking=booking, checkin_time=now, method="code")
        db.commit()
        db.refresh(booking)
        return booking
    except Exception:
        db.rollback()
        raise


def _reschedule_booking_transaction(
    db: Session,
    *,
    booking: Booking,
    target_seat_id: int,
    normalized_start: datetime,
    normalized_end: datetime,
) -> Booking:
    seat_store_row = db.execute(
        select(Seat, Store)
        .join(Store, Store.id == Seat.store_id)
        .where(Seat.id == target_seat_id)
        .with_for_update()
    ).first()
    if seat_store_row is None:
        raise SeatNotFoundError("座位不存在")
    seat, store = seat_store_row
    _ensure_seat_store_bookable(seat, store, normalized_start, normalized_end)
    _ensure_user_booking_not_conflict(
        db,
        user_id=booking.user_id,
        start_time=normalized_start,
        end_time=normalized_end,
        exclude_booking_id=booking.id,
    )
    _ensure_booking_not_conflict(
        db,
        seat_id=target_seat_id,
        start_time=normalized_start,
        end_time=normalized_end,
        exclude_booking_id=booking.id,
    )

    booking.seat_id = target_seat_id
    booking.store_id = seat.store_id
    booking.start_time = normalized_start
    booking.end_time = normalized_end
    booking.checkin_code = None
    booking.checkin_code_expires_at = None
    booking.qr_token = None
    booking.qr_token_expires_at = None
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def reschedule_booking_with_lock(
    db: Session,
    redis_client: Redis,
    *,
    booking_id: int,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
    seat_id: int | None = None,
) -> Booking:
    now = datetime.now(timezone.utc)
    normalized_start, normalized_end = _normalize_time_window(start_time, end_time)
    _ensure_booking_rule_time_window(db, normalized_start, normalized_end, now)

    try:
        booking = db.execute(
            select(Booking).where(Booking.id == booking_id).with_for_update()
        ).scalar_one_or_none()
        if booking is None:
            raise BookingNotFoundError("预约不存在")
        if booking.user_id != user_id:
            raise BookingPermissionError("无权操作此预约")
        if booking.status != "booked":
            raise BookingStateError("当前预约状态不可改期")

        deadline = booking.start_time - timedelta(minutes=_rule_reschedule_before_minutes(db))
        if now > deadline:
            raise BookingStateError("已超过可改期时间，无法改期")
        if is_user_blacklisted(db, booking.user_id):
            raise UserBlacklistedError("黑名单用户禁止预约")
        user_exists = db.execute(
            select(User.id).where(User.id == booking.user_id).with_for_update()
        ).scalar_one_or_none()
        if user_exists is None:
            raise UserNotFoundError("用户不存在")

        target_seat_id = seat_id or booking.seat_id
        target_store_id = booking.store_id if target_seat_id == booking.seat_id else _get_store_id_for_seat_lock(db, target_seat_id)
        lock_key = build_booking_lock_key(target_store_id, target_seat_id)

        with redis_booking_lock(redis_client, lock_key, settings.redis_lock_ttl_ms):
            return _reschedule_booking_transaction(
                db,
                booking=booking,
                target_seat_id=target_seat_id,
                normalized_start=normalized_start,
                normalized_end=normalized_end,
            )
    except RedisLockBusyError as exc:
        raise SeatLockBusyError("座位正在被其他用户预约，请稍后重试") from exc
    except RedisUnavailableError as exc:
        if settings.redis_lock_required:
            raise LockServiceUnavailableError("预约锁服务不可用，请稍后重试") from exc
        try:
            booking = db.execute(
                select(Booking).where(Booking.id == booking_id).with_for_update()
            ).scalar_one_or_none()
            if booking is None:
                raise BookingNotFoundError("预约不存在")
            if booking.user_id != user_id:
                raise BookingPermissionError("无权操作此预约")
            if booking.status != "booked":
                raise BookingStateError("当前预约状态不可改期")

            deadline = booking.start_time - timedelta(minutes=_rule_reschedule_before_minutes(db))
            if now > deadline:
                raise BookingStateError("已超过可改期时间，无法改期")
            if is_user_blacklisted(db, booking.user_id):
                raise UserBlacklistedError("黑名单用户禁止预约")

            target_seat_id = seat_id or booking.seat_id
            return _reschedule_booking_transaction(
                db,
                booking=booking,
                target_seat_id=target_seat_id,
                normalized_start=normalized_start,
                normalized_end=normalized_end,
            )
        except IntegrityError as fallback_exc:
            db.rollback()
            if _is_exclusion_violation(fallback_exc):
                if _is_user_time_conflict_violation(fallback_exc):
                    raise UserBookingConflictError("您在该时间段内已有其他预约，不能重复预约多个座位") from fallback_exc
                raise BookingConflictError("该座位在所选时间段已被预约，请更换时间或座位") from fallback_exc
            raise
        except Exception:
            db.rollback()
            raise
    except IntegrityError as exc:
        db.rollback()
        if _is_exclusion_violation(exc):
            if _is_user_time_conflict_violation(exc):
                raise UserBookingConflictError("您在该时间段内已有其他预约，不能重复预约多个座位") from exc
            raise BookingConflictError("该座位在所选时间段已被预约，请更换时间或座位") from exc
        raise
    except Exception:
        db.rollback()
        raise


def expire_unchecked_bookings(db: Session) -> ExpireJobResult:
    now = datetime.now(timezone.utc)
    expire_cutoff = now - timedelta(minutes=_rule_checkin_grace_minutes(db))
    result = ExpireJobResult()

    try:
        bookings = list(
            db.scalars(
                select(Booking)
                .where(
                    Booking.status == "booked",
                    Booking.start_time <= expire_cutoff,
                    Booking.checked_in_at.is_(None),
                )
                .with_for_update(skip_locked=True)
            ).all()
        )

        if not bookings:
            return result

        no_show_counter: Counter[int] = Counter()
        for booking in bookings:
            _transition_status(booking, "expired")
            booking.expire_reason = "超时未签到自动过期"
            booking.checkin_code = None
            booking.checkin_code_expires_at = None
            booking.qr_token = None
            booking.qr_token_expires_at = None
            booking.updated_at = now
            db.add(booking)
            db.add(
                BookingReleaseLog(
                    booking_id=booking.id,
                    user_id=booking.user_id,
                    seat_id=booking.seat_id,
                    release_type="auto_timeout",
                    reason="超时未签到自动过期",
                    remark="定时任务自动执行",
                    released_at=now,
                )
            )
            queue_student_notification(
                db,
                user_id=booking.user_id,
                title="预约已过期",
                content=(
                    f"您在 {_format_notification_time(booking.start_time)} 开始的座位预约，"
                    "因超时未签到已自动过期。"
                ),
                notification_type="booking",
                related_type="booking",
                related_id=booking.id,
                commit=False,
            )
            no_show_counter[booking.user_id] += 1

        result.expired_count = len(bookings)
        result.release_log_count = len(bookings)

        for user_id, increment in no_show_counter.items():
            db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    no_show_count=User.no_show_count + increment,
                    updated_at=now,
                )
            )
        result.users_incremented = len(no_show_counter)

        threshold = _rule_no_show_blacklist_threshold(db)
        blacklist_effective_days = _rule_blacklist_effective_days(db)
        for user_id in no_show_counter.keys():
            user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
            if user is None or user.no_show_count < threshold:
                continue
            _, created = add_user_to_blacklist(
                db,
                user_id=user.id,
                reason=f"连续爽约达到{threshold}次，系统自动拉黑",
                source="auto_no_show",
                duration_days=blacklist_effective_days,
                no_show_count_snapshot=user.no_show_count,
                created_by=None,
                commit=False,
            )
            if created:
                queue_student_notification(
                    db,
                    user_id=user.id,
                    title="已加入黑名单",
                    content=f"由于连续爽约达到{threshold}次，系统已自动将您加入黑名单，请联系管理员处理。",
                    notification_type="violation",
                    related_type="blacklist",
                    related_id=user.id,
                    commit=False,
                )
                result.auto_blacklisted_count += 1

        db.commit()
    except Exception:
        db.rollback()
        raise

    return result


def complete_finished_bookings(db: Session) -> CompleteJobResult:
    now = datetime.now(timezone.utc)
    result = CompleteJobResult()

    try:
        bookings = list(
            db.scalars(
                select(Booking)
                .where(
                    Booking.status == "checked_in",
                    Booking.end_time <= now,
                )
                .with_for_update(skip_locked=True)
            ).all()
        )

        if not bookings:
            return result

        for booking in bookings:
            _transition_status(booking, "completed")
            booking.updated_at = now
            db.add(booking)
            queue_student_notification(
                db,
                user_id=booking.user_id,
                title="预约已完成",
                content=(
                    f"您在 {_format_notification_time(booking.start_time)} 开始的预约已自动完成，"
                    "感谢使用自习室。"
                ),
                notification_type="booking",
                related_type="booking",
                related_id=booking.id,
                commit=False,
            )

        result.completed_count = len(bookings)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return result


def admin_cancel_booking(db: Session, *, booking_id: int, reason: str = "管理员手动取消预约") -> Booking:
    now = datetime.now(timezone.utc)
    booking = db.execute(select(Booking).where(Booking.id == booking_id).with_for_update()).scalar_one_or_none()
    if booking is None:
        raise BookingNotFoundError("预约不存在")
    if booking.status != "booked":
        raise BookingStateError("当前预约状态不可取消")

    _transition_status(booking, "cancelled")
    booking.cancel_reason = reason
    booking.checkin_code = None
    booking.checkin_code_expires_at = None
    booking.qr_token = None
    booking.qr_token_expires_at = None
    booking.updated_at = now
    _reset_no_show_count(db, booking.user_id, now)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def admin_force_checkin_booking(db: Session, *, booking_id: int) -> Booking:
    now = datetime.now(timezone.utc)
    booking = db.execute(select(Booking).where(Booking.id == booking_id).with_for_update()).scalar_one_or_none()
    if booking is None:
        raise BookingNotFoundError("预约不存在")
    if booking.status != "booked":
        raise BookingStateError("当前预约状态不可强制签到")

    _transition_status(booking, "checked_in")
    booking.checked_in_at = now
    booking.sign_in_time = now
    booking.checkin_code = None
    booking.checkin_code_expires_at = None
    booking.qr_token = None
    booking.qr_token_expires_at = None
    booking.updated_at = now
    _create_checkin_record(db, booking=booking, checkin_time=now, method="code")
    _reset_no_show_count(db, booking.user_id, now)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def admin_complete_booking(db: Session, *, booking_id: int) -> Booking:
    now = datetime.now(timezone.utc)
    booking = db.execute(select(Booking).where(Booking.id == booking_id).with_for_update()).scalar_one_or_none()
    if booking is None:
        raise BookingNotFoundError("预约不存在")
    if booking.status != "checked_in":
        raise BookingStateError("当前预约状态不可标记完成")

    _transition_status(booking, "completed")
    booking.updated_at = now
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def send_upcoming_booking_reminders(db: Session) -> int:
    now = datetime.now(timezone.utc)
    window_start = now + timedelta(minutes=settings.reminder_minutes_before_start)
    window_end = window_start + timedelta(minutes=5)

    bookings = list(
        db.scalars(
            select(Booking).where(
                Booking.status == "booked",
                Booking.start_time >= window_start,
                Booking.start_time < window_end,
            )
        ).all()
    )
    if not bookings:
        return 0

    sent = 0
    for booking in bookings:
        exists = db.execute(
            select(StudentNotification.id).where(
                StudentNotification.user_id == booking.user_id,
                StudentNotification.related_type == "booking_reminder",
                StudentNotification.related_id == booking.id,
            )
        ).scalar_one_or_none()
        if exists is not None:
            continue

        queue_student_notification(
            db,
            user_id=booking.user_id,
            title="预约即将开始提醒",
            content=(
                f"您的预约将在 {_format_notification_time(booking.start_time)} 开始，"
                "请按时到店签到。"
            ),
            notification_type="booking",
            related_type="booking_reminder",
            related_id=booking.id,
            commit=False,
        )
        sent += 1

    if sent > 0:
        db.commit()
    return sent
