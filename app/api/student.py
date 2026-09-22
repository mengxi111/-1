import logging
from datetime import date as date_type
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, Request, status
from redis import Redis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.api_response import error_response, success_response
from app.core.config import settings
from app.crud.admin_operation_log import create_admin_operation_log
from app.crud.booking import (
    BookingConflictError,
    BookingNotFoundError,
    BookingPermissionError,
    BookingStateError,
    UserBookingConflictError,
    BookingValidationError,
    LockServiceUnavailableError,
    QRCodeExpiredError,
    QRCodeInvalidError,
    SeatLockBusyError,
    SeatNotFoundError,
    SeatUnavailableError,
    StoreBusinessHourError,
    UserBlacklistedError,
    UserNotFoundError,
    cancel_booking,
    checkin_with_qr_token,
    create_booking_with_lock,
    generate_qr_checkin_token,
    get_booking,
    get_seat_available_slots_for_date,
    list_bookings,
    reschedule_booking_with_lock,
    signin_booking_now,
)
from app.crud.order import create_order, get_order_by_booking_id
from app.crud.system_setting import get_setting_int
from app.crud.notice import get_published_notice, list_notices
from app.crud.student_notification import (
    EMAIL_STATUS_TEXT,
    NOTIFICATION_TYPE_TEXT,
    get_student_notification,
    list_student_notifications,
    mark_all_student_notifications_read,
    mark_student_notification_read,
    queue_student_notification,
)
from app.crud.store import get_store
from app.db.session import get_db
from app.deps import CurrentAuthUser, get_redis_client, require_student_token_user
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.student_notification import StudentNotification
from app.models.store import Store
from app.schemas.booking import BookingCreate
from app.schemas.student_api import StudentBookingCreateIn, StudentBookingRescheduleIn, StudentQrCheckinConfirmIn

router = APIRouter(dependencies=[Depends(require_student_token_user)])
logger = logging.getLogger(__name__)


STATUS_TEXT_MAP = {
    "booked": "已预约",
    "checked_in": "已签到",
    "completed": "已完成",
    "cancelled": "已取消",
    "expired": "已过期",
}


def _status_text(status_value: str) -> str:
    return STATUS_TEXT_MAP.get(status_value, status_value)


def _write_student_operation_log(
    db: Session,
    *,
    request: Request,
    user: CurrentAuthUser,
    module: str,
    request_method: str,
    request_path: str,
    content: str,
) -> None:
    ip = request.client.host if request.client else "0.0.0.0"
    create_admin_operation_log(
        db,
        operator_id=user.id,
        operator_name=user.name,
        operator_role=user.role,
        ip=ip,
        module=module,
        request_method=request_method,
        request_path=request_path,
        status_code=200,
        content=content,
    )


def _booking_to_me_item(item: Booking, *, checkin_grace_minutes: int) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    can_checkin = (
        item.status == "booked"
        and item.start_time <= now <= item.end_time
        and now <= item.start_time + timedelta(minutes=checkin_grace_minutes)
    )
    return {
        "id": item.id,
        "seat_id": item.seat_id,
        "start_time": item.start_time,
        "end_time": item.end_time,
        "status": item.status,
        "status_text": _status_text(item.status),
        "can_checkin": can_checkin,
        "checked_in_at": item.checked_in_at,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _notification_to_item(item: StudentNotification) -> dict[str, Any]:
    return {
        "id": item.id,
        "title": item.title,
        "content": item.content,
        "notification_type": item.notification_type,
        "notification_type_text": NOTIFICATION_TYPE_TEXT.get(item.notification_type, "系统通知"),
        "is_read": item.is_read,
        "read_at": item.read_at,
        "email_status": item.email_status,
        "email_status_text": EMAIL_STATUS_TEXT.get(item.email_status, "未发送"),
        "email_error": item.email_error,
        "created_at": item.created_at,
    }


def _notice_to_item(db: Session, item) -> dict[str, Any]:
    store = get_store(db, item.store_id) if item.store_id is not None else None
    return {
        "id": item.id,
        "store_id": item.store_id,
        "store_name": store.name if store is not None else None,
        "title": item.title,
        "content": item.content,
        "status": item.status,
        "published_at": item.published_at,
        "created_at": item.created_at,
    }


def _format_local_time(value: datetime) -> str:
    return value.astimezone(ZoneInfo(settings.timezone)).strftime("%Y-%m-%d %H:%M")


@router.get("/stores")
def student_list_stores(db: Session = Depends(get_db)) -> dict[str, Any]:
    stmt = select(Store).where(Store.status == 1).order_by(Store.id)
    stores = list(db.scalars(stmt).all())
    return success_response(
        data=[
            {
                "id": store.id,
                "name": store.name,
                "address": store.address,
                "contact_phone": store.contact_phone,
                "description": store.description,
                "open_time": store.open_time.isoformat(),
                "close_time": store.close_time.isoformat(),
            }
            for store in stores
        ]
    )


@router.get("/seats")
def student_list_seats(
    store_id: int | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(Seat).where(Seat.is_available.is_(True), Seat.seat_status == "available")
    if store_id is not None:
        stmt = stmt.where(Seat.store_id == store_id)
    stmt = stmt.order_by(Seat.id)
    seats = list(db.scalars(stmt).all())
    return success_response(
        data=[
            {
                "id": seat.id,
                "store_id": seat.store_id,
                "area_id": seat.area_id,
                "seat_no": seat.seat_no,
                "seat_type": seat.seat_type,
                "seat_status": seat.seat_status,
                "is_available": seat.is_available,
            }
            for seat in seats
        ]
    )


@router.get("/seats/{seat_id}/available-slots")
def student_get_seat_available_slots(
    seat_id: int,
    slot_date: date_type | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        data = get_seat_available_slots_for_date(
            db,
            seat_id=seat_id,
            target_date=slot_date,
        )
    except SeatNotFoundError as exc:
        raise error_response(status.HTTP_404_NOT_FOUND, "座位不存在") from exc
    except SeatUnavailableError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, "该座位当前不可用，请选择其他座位") from exc
    except StoreBusinessHourError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, "所选时间不在门店营业时间内") from exc

    return success_response(data=data)

@router.post("/bookings")
def student_create_booking(
    payload: StudentBookingCreateIn,
    db: Session = Depends(get_db),
    lock_client: Redis = Depends(get_redis_client),
    current_user: CurrentAuthUser = Depends(require_student_token_user),
) -> dict[str, Any]:
    try:
        logger.info(
            "student_create_booking start user_id=%s seat_id=%s start=%s end=%s redis=%s",
            current_user.id,
            payload.seat_id,
            payload.start_time,
            payload.end_time,
            getattr(getattr(lock_client, "connection_pool", None), "connection_kwargs", None),
        )
        booking = create_booking_with_lock(
            db,
            lock_client,
            BookingCreate(
                seat_id=payload.seat_id,
                start_time=payload.start_time,
                end_time=payload.end_time,
                user_id=current_user.id,
            ),
        )
    except BookingValidationError as exc:
        logger.warning("student_create_booking validation_error user_id=%s error=%s", current_user.id, exc)
        raise error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except SeatNotFoundError as exc:
        raise error_response(status.HTTP_404_NOT_FOUND, "座位不存在") from exc
    except SeatUnavailableError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, "该座位当前不可用，请选择其他座位") from exc
    except StoreBusinessHourError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, "所选时间不在门店营业时间内") from exc
    except UserNotFoundError as exc:
        raise error_response(status.HTTP_404_NOT_FOUND, "用户不存在") from exc
    except UserBlacklistedError as exc:
        raise error_response(status.HTTP_403_FORBIDDEN, "您已被列入黑名单，暂时无法预约") from exc
    except UserBookingConflictError as exc:
        raise error_response(status.HTTP_409_CONFLICT, "您在该时间段已有预约，不能重复预约") from exc
    except SeatLockBusyError as exc:
        raise error_response(status.HTTP_409_CONFLICT, "座位正在被其他用户预约，请稍后重试") from exc
    except LockServiceUnavailableError as exc:
        raise error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "预约锁服务不可用，请稍后重试") from exc
    except BookingConflictError as exc:
        raise error_response(status.HTTP_409_CONFLICT, "该座位在所选时间段已被预约") from exc
    except BookingStateError as exc:
        logger.warning("student_create_booking state_error user_id=%s error=%s", current_user.id, exc)
        raise error_response(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    if settings.order_module_enabled and get_order_by_booking_id(db, booking.id) is None:
        try:
            create_order(db, booking_id=booking.id, user_id=current_user.id, amount=0, status="pending")
        except IntegrityError:
            db.rollback()

    queue_student_notification(
        db,
        user_id=current_user.id,
        title="预约成功",
        content=(
            f"您已成功预约座位 #{booking.seat_id}，"
            f"开始时间：{_format_local_time(booking.start_time)}，"
            f"结束时间：{_format_local_time(booking.end_time)}。"
        ),
        notification_type="booking",
        related_type="booking",
        related_id=booking.id,
    )

    return success_response(
        data={
            "booking_id": booking.id,
            "status": booking.status,
            "status_text": _status_text(booking.status),
        },
        message="预约成功",
    )


@router.post("/bookings/{booking_id}/cancel")
def student_cancel_booking(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_student_token_user),
) -> dict[str, Any]:
    booking = get_booking(db, booking_id)
    if booking is None:
        raise error_response(status.HTTP_404_NOT_FOUND, "预约不存在")
    if booking.user_id != current_user.id:
        raise error_response(status.HTTP_403_FORBIDDEN, "无权操作此预约")

    try:
        booking = cancel_booking(db, booking)
    except BookingStateError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    _write_student_operation_log(
        db,
        request=request,
        user=current_user,
        module="student_booking_cancel",
        request_method="POST",
        request_path=f"/api/student/bookings/{booking_id}/cancel",
        content=f"取消预约 booking_id={booking.id}",
    )
    queue_student_notification(
        db,
        user_id=current_user.id,
        title="预约已取消",
        content=f"您已成功取消预约，预约编号：{booking.id}。",
        notification_type="booking",
        related_type="booking",
        related_id=booking.id,
    )
    return success_response(
        data={
            "booking_id": booking.id,
            "status": booking.status,
            "status_text": _status_text(booking.status),
        },
        message="取消预约成功",
    )


@router.put("/bookings/{booking_id}/reschedule")
def student_reschedule_booking(
    booking_id: int,
    payload: StudentBookingRescheduleIn,
    request: Request,
    db: Session = Depends(get_db),
    lock_client: Redis = Depends(get_redis_client),
    current_user: CurrentAuthUser = Depends(require_student_token_user),
) -> dict[str, Any]:
    try:
        booking = reschedule_booking_with_lock(
            db,
            lock_client,
            booking_id=booking_id,
            user_id=current_user.id,
            seat_id=payload.seat_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )
    except BookingValidationError as exc:
        raise error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except BookingNotFoundError as exc:
        raise error_response(status.HTTP_404_NOT_FOUND, "预约不存在") from exc
    except BookingPermissionError as exc:
        raise error_response(status.HTTP_403_FORBIDDEN, "无权操作此预约") from exc
    except SeatNotFoundError as exc:
        raise error_response(status.HTTP_404_NOT_FOUND, "座位不存在") from exc
    except SeatUnavailableError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, "该座位当前不可用，请选择其他座位") from exc
    except StoreBusinessHourError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, "所选时间不在门店营业时间内") from exc
    except UserBlacklistedError as exc:
        raise error_response(status.HTTP_403_FORBIDDEN, "您已被列入黑名单，暂时无法预约") from exc
    except UserBookingConflictError as exc:
        raise error_response(status.HTTP_409_CONFLICT, "您在该时间段已有预约，不能重复预约") from exc
    except BookingConflictError as exc:
        raise error_response(status.HTTP_409_CONFLICT, "该座位在所选时间段已被预约") from exc
    except BookingStateError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except SeatLockBusyError as exc:
        raise error_response(status.HTTP_409_CONFLICT, "座位正在被其他用户预约，请稍后重试") from exc
    except LockServiceUnavailableError as exc:
        raise error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "预约锁服务不可用，请稍后重试") from exc

    _write_student_operation_log(
        db,
        request=request,
        user=current_user,
        module="student_booking_reschedule",
        request_method="PUT",
        request_path=f"/api/student/bookings/{booking_id}/reschedule",
        content=(
            f"改期成功 booking_id={booking.id}, seat_id={booking.seat_id}, "
            f"start={booking.start_time.isoformat()}, end={booking.end_time.isoformat()}"
        ),
    )
    queue_student_notification(
        db,
        user_id=current_user.id,
        title="预约已改期",
        content=(
            f"您的预约已改期成功，新的座位编号：{booking.seat_id}，"
            f"开始时间：{_format_local_time(booking.start_time)}，"
            f"结束时间：{_format_local_time(booking.end_time)}。"
        ),
        notification_type="booking",
        related_type="booking",
        related_id=booking.id,
    )
    return success_response(
        data={
            "booking_id": booking.id,
            "seat_id": booking.seat_id,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "status": booking.status,
            "status_text": _status_text(booking.status),
        },
        message="改期成功",
    )


@router.get("/bookings/me")
def student_list_my_bookings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_student_token_user),
) -> dict[str, Any]:
    bookings = list_bookings(db, skip=skip, limit=limit, user_id=current_user.id)
    checkin_grace_minutes = get_setting_int(db, "checkin_grace_minutes", settings.checkin_grace_minutes)
    return success_response(
        data=[_booking_to_me_item(item, checkin_grace_minutes=checkin_grace_minutes) for item in bookings]
    )


@router.get("/my-reservations")
def student_list_my_reservations(
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_student_token_user),
) -> dict[str, Any]:
    rows = db.execute(
        select(
            Booking.id,
            Store.name.label("store_name"),
            Seat.seat_no,
            Booking.start_time,
            Booking.end_time,
            Booking.status,
        )
        .join(Seat, Seat.id == Booking.seat_id)
        .join(Store, Store.id == Seat.store_id)
        .where(Booking.user_id == current_user.id)
        .order_by(Booking.id.desc())
    ).all()

    now = datetime.now(timezone.utc)
    checkin_grace_minutes = get_setting_int(db, "checkin_grace_minutes", settings.checkin_grace_minutes)
    data = []
    for row in rows:
        can_sign_in = (
            row.status == "booked"
            and row.start_time <= now <= row.end_time
            and now <= row.start_time + timedelta(minutes=checkin_grace_minutes)
        )
        data.append(
            {
                "reservation_id": row.id,
                "store_name": row.store_name,
                "seat_no": row.seat_no,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "status": _status_text(row.status),
                "can_sign_in": can_sign_in,
            }
        )
    return success_response(data=data)


@router.post("/signin/{reservation_id}")
def student_signin_now(
    reservation_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_student_token_user),
) -> dict[str, Any]:
    try:
        booking = signin_booking_now(db, booking_id=reservation_id, user_id=current_user.id)
    except BookingNotFoundError as exc:
        raise error_response(status.HTTP_404_NOT_FOUND, "预约不存在") from exc
    except BookingPermissionError as exc:
        raise error_response(status.HTTP_403_FORBIDDEN, "无权操作此预约") from exc
    except BookingStateError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except UserBlacklistedError as exc:
        raise error_response(status.HTTP_403_FORBIDDEN, "您已被列入黑名单，暂时无法签到") from exc

    _write_student_operation_log(
        db,
        request=request,
        user=current_user,
        module="student_signin",
        request_method="POST",
        request_path=f"/api/student/signin/{reservation_id}",
        content=f"学生签到成功 reservation_id={reservation_id}",
    )
    queue_student_notification(
        db,
        user_id=current_user.id,
        title="签到成功",
        content=f"您已完成签到，预约编号：{booking.id}，当前状态为使用中。",
        notification_type="booking",
        related_type="booking",
        related_id=booking.id,
    )
    return success_response(
        data={
            "reservation_id": booking.id,
            "status": "checked_in",
            "status_text": "使用中",
            "sign_in_time": booking.checked_in_at,
        },
        message="签到成功",
    )


@router.post("/bookings/{booking_id}/checkin/qr-code")
def student_generate_qr_code(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_student_token_user),
) -> dict[str, Any]:
    try:
        booking, qr_token = generate_qr_checkin_token(db, booking_id=booking_id, user_id=current_user.id)
    except BookingNotFoundError as exc:
        raise error_response(status.HTTP_404_NOT_FOUND, "预约不存在") from exc
    except BookingPermissionError as exc:
        raise error_response(status.HTTP_403_FORBIDDEN, "无权操作此预约") from exc
    except UserBlacklistedError as exc:
        raise error_response(status.HTTP_403_FORBIDDEN, "您已被列入黑名单，暂时无法签到") from exc
    except BookingStateError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    qr_content = f"studyroom://checkin?booking_id={booking.id}&token={qr_token}"
    return success_response(
        data={
            "booking_id": booking.id,
            "status": booking.status,
            "qr_token": qr_token,
            "qr_content": qr_content,
            "qr_expires_at": booking.qr_token_expires_at,
        },
        message="二维码生成成功",
    )


@router.post("/bookings/{booking_id}/checkin/qr-signin")
def student_qr_signin(
    booking_id: int,
    payload: StudentQrCheckinConfirmIn,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_student_token_user),
) -> dict[str, Any]:
    try:
        booking = checkin_with_qr_token(
            db,
            booking_id=booking_id,
            user_id=current_user.id,
            qr_token=payload.qr_token,
        )
    except BookingNotFoundError as exc:
        raise error_response(status.HTTP_404_NOT_FOUND, "预约不存在") from exc
    except BookingPermissionError as exc:
        raise error_response(status.HTTP_403_FORBIDDEN, "无权操作此预约") from exc
    except UserBlacklistedError as exc:
        raise error_response(status.HTTP_403_FORBIDDEN, "您已被列入黑名单，暂时无法签到") from exc
    except QRCodeExpiredError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except QRCodeInvalidError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except BookingStateError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    queue_student_notification(
        db,
        user_id=current_user.id,
        title="签到成功",
        content=f"您已通过二维码完成签到，预约编号：{booking.id}，当前状态为使用中。",
        notification_type="booking",
        related_type="booking",
        related_id=booking.id,
    )
    return success_response(
        data={
            "booking_id": booking.id,
            "status": booking.status,
            "checked_in_at": booking.checked_in_at,
        },
        message="签到成功",
    )


@router.get("/notifications")
def student_list_notifications_endpoint(
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_student_token_user),
) -> dict[str, Any]:
    total, unread_count, items = list_student_notifications(
        db,
        user_id=current_user.id,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )
    return success_response(
        data={
            "total": total,
            "unread_count": unread_count,
            "items": [_notification_to_item(item) for item in items],
        }
    )


@router.post("/notifications/{notification_id}/read")
def student_mark_notification_read_endpoint(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_student_token_user),
) -> dict[str, Any]:
    notification = get_student_notification(db, notification_id, current_user.id)
    if notification is None:
        raise error_response(status.HTTP_404_NOT_FOUND, "通知不存在")
    notification = mark_student_notification_read(db, notification=notification)
    return success_response(data=_notification_to_item(notification), message="已标记为已读")


@router.post("/notifications/read-all")
def student_mark_all_notifications_read_endpoint(
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_student_token_user),
) -> dict[str, Any]:
    updated_count = mark_all_student_notifications_read(db, user_id=current_user.id)
    return success_response(data={"updated_count": updated_count}, message="全部通知已标记为已读")


@router.get("/notices")
def student_list_notices(
    store_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _current_user: CurrentAuthUser = Depends(require_student_token_user),
) -> dict[str, Any]:
    notices = list_notices(db, store_id=store_id, status="published", skip=skip, limit=limit)
    return success_response(data=[_notice_to_item(db, item) for item in notices])


@router.get("/notices/{notice_id}")
def student_get_notice_detail(
    notice_id: int,
    db: Session = Depends(get_db),
    _current_user: CurrentAuthUser = Depends(require_student_token_user),
) -> dict[str, Any]:
    notice = get_published_notice(db, notice_id)
    if notice is None:
        raise error_response(status.HTTP_404_NOT_FOUND, "公告不存在或已下线")
    return success_response(data=_notice_to_item(db, notice))
