import csv
import io
import re
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from redis import Redis
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.booking_blacklist import add_user_to_blacklist, list_blacklists, remove_user_from_blacklist
from app.crud.booking import (
    BookingNotFoundError,
    BookingConflictError,
    BookingStateError,
    BookingValidationError,
    LockServiceUnavailableError,
    SeatLockBusyError,
    SeatNotFoundError,
    SeatUnavailableError,
    StoreBusinessHourError,
    UserBlacklistedError,
    UserBookingConflictError,
    UserNotFoundError,
    admin_cancel_booking,
    admin_complete_booking,
    admin_force_checkin_booking,
    create_booking_with_lock,
    list_admin_bookings,
)
from app.crud.admin_operation_log import list_admin_operation_logs
from app.crud.checkin_record import list_checkin_records
from app.crud.area import create_area, delete_area, get_area, list_areas, update_area
from app.crud.member_card import get_member_card, list_member_cards, renew_member_card, set_member_card_frozen
from app.crud.notice import create_notice, delete_notice, get_notice, list_notices, set_notice_status, update_notice
from app.crud.order import create_order, get_order, get_order_by_booking_id, get_order_detail, list_orders, update_order_status
from app.crud.pricing_plan import create_plan, delete_plan, get_plan, list_plans, update_plan
from app.crud.seat import create_seat, delete_seat, get_seat, list_seats, update_seat
from app.crud.stats import get_checkin_stats, get_overview_stats
from app.crud.store import create_store, delete_store, get_store, list_stores, update_store
from app.crud.student_notification import queue_notice_notifications_for_students, queue_student_notification
from app.crud.system_setting import get_system_config, reset_settings_to_defaults, upsert_settings
from app.crud.user import DELETED_USER_STATUS, create_user, delete_user, get_user, list_users, update_user
from app.core.api_response import success_response, error_response
from app.db.session import get_db
from app.deps import (
    CurrentAuthUser,
    get_current_token_user,
    get_redis_client,
    require_admin_portal_token_user,
    require_admin_token_user,
    require_super_admin_token_user,
)
from app.models.booking import Booking
from app.models.booking_blacklist import BookingBlacklist
from app.models.member_card import MemberCard
from app.models.order import Order
from app.models.seat import Seat
from app.models.booking_release_log import BookingReleaseLog
from app.models.user import User
from app.services.bootstrap import bootstrap_initial_data
from app.services.demo_seed import bootstrap_demo_data
from app.schemas.admin_api import (
    AdminUserRoleAssignIn,
    AdminUserRoleAssignOut,
    AdminSeatBatchCreateIn,
    AdminSeatBatchCreateOut,
    AdminSeatCreate,
    AdminSeatOut,
    AdminSeatUpdate,
    AdminUserDetailOut,
    AdminUserListOut,
    AreaCreate,
    AreaOut,
    AreaUpdate,
    BlacklistActionOut,
    BlacklistCreateIn,
    BlacklistOut,
    BootstrapDemoOut,
    BookingReleaseLogOut,
    BootstrapOut,
    CheckinRecordOut,
    CheckinRecordPageOut,
    MembershipFreezeIn,
    MembershipOpenIn,
    MembershipOut,
    MembershipRenewIn,
    OperationLogOut,
    OperationLogPageOut,
    OrderActionOut,
    OrderOut,
    OrderPageOut,
    PlanCreate,
    PlanOut,
    PlanUpdate,
    SystemConfigOut,
    SystemConfigUpdateIn,
)
from app.schemas.booking import BookingCreate
from app.schemas.member_card import MemberCardCreate
from app.schemas.notice import NoticeCreate, NoticeDetailOut, NoticeOut, NoticeUpdate
from app.schemas.stats import CheckinStatsOut, StatsOverviewOut
from app.schemas.store import StoreCreate, StoreOut, StoreUpdate
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter(dependencies=[Depends(require_admin_portal_token_user)])

LOG_DURATION_RE = re.compile(r"耗时=(\d+)ms")


def _serialize_operation_log(item) -> OperationLogOut:
    duration_ms = None
    if item.content:
        match = LOG_DURATION_RE.search(item.content)
        if match:
            duration_ms = int(match.group(1))
    summary = item.content.split(";")[0] if item.content else None
    return OperationLogOut(
        id=item.id,
        operator_id=item.operator_id,
        operator_name=item.operator_name,
        operator_role=item.operator_role,
        ip=item.ip,
        module=item.module,
        request_method=item.request_method,
        request_path=item.request_path,
        status_code=item.status_code,
        content=item.content,
        summary=summary,
        duration_ms=duration_ms,
        created_at=item.created_at,
    )


def _build_admin_user_list(db: Session, users: list[User]) -> list[AdminUserListOut]:
    if not users:
        return []

    user_ids = [user.id for user in users]
    active_blacklists = {
        row.user_id: row
        for row in db.scalars(
            select(BookingBlacklist)
            .where(BookingBlacklist.user_id.in_(user_ids), BookingBlacklist.is_active.is_(True))
            .order_by(BookingBlacklist.id.desc())
        ).all()
    }
    booking_rows = db.execute(
        select(Booking.user_id, func.count(Booking.id))
        .where(Booking.user_id.in_(user_ids))
        .group_by(Booking.user_id)
    ).all()
    booking_count_map = {user_id: int(count or 0) for user_id, count in booking_rows}

    return [
        AdminUserListOut(
            id=user.id,
            phone=user.phone,
            email=user.email,
            name=user.name,
            role=user.role,
            status=user.status,
            no_show_count=user.no_show_count,
            is_blacklisted=user.id in active_blacklists,
            blacklist_end_at=active_blacklists[user.id].end_at if user.id in active_blacklists else None,
            history_booking_count=booking_count_map.get(user.id, 0),
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        for user in users
    ]


def _role_text(role: str) -> str:
    mapping = {
        "student": "学生",
        "staff": "店员",
        "admin": "管理员",
        "super_admin": "超级管理员",
    }
    return mapping.get(role, role)


def _notice_detail_out(db: Session, notice) -> NoticeDetailOut:
    store_name = None
    created_by_name = None
    if notice.store_id is not None:
        store = get_store(db, notice.store_id)
        store_name = store.name if store else None
    if notice.created_by is not None:
        creator = get_user(db, notice.created_by)
        created_by_name = creator.name if creator else None
    return NoticeDetailOut(
        id=notice.id,
        store_id=notice.store_id,
        store_name=store_name,
        title=notice.title,
        content=notice.content,
        status=notice.status,
        published_at=notice.published_at,
        created_by=notice.created_by,
        created_by_name=created_by_name,
        created_at=notice.created_at,
        updated_at=notice.updated_at,
    )


@router.post("/bootstrap", response_model=BootstrapOut)
def admin_bootstrap(
    db: Session = Depends(get_db),
    _super_admin: CurrentAuthUser = Depends(require_super_admin_token_user),
) -> BootstrapOut:
    try:
        result = bootstrap_initial_data(db=db, only_if_empty=False)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="初始化失败，请稍后重试") from exc

    return BootstrapOut(
        stores_created=result.stores_created,
        areas_created=result.areas_created,
        seats_created=result.seats_created,
        plans_created=result.plans_created,
        message="初始化完成",
    )


@router.post("/bootstrap-demo", response_model=BootstrapDemoOut)
def admin_bootstrap_demo(
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> BootstrapDemoOut:
    try:
        result = bootstrap_demo_data(db=db, only_if_empty=False)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="演示数据初始化失败，请稍后重试") from exc

    return BootstrapDemoOut(
        stores_created=result.stores_created,
        areas_created=result.areas_created,
        seats_created=result.seats_created,
        plans_created=result.plans_created,
        users_created=result.users_created,
        bookings_created=result.bookings_created,
        orders_created=result.orders_created,
        notices_created=result.notices_created,
        notifications_created=result.notifications_created,
        message="演示数据初始化完成",
    )


def _apply_seat_state(payload: dict) -> dict:
    seat_status = payload.get("seat_status")
    if seat_status in {"maintenance", "disabled"}:
        payload["is_available"] = False
    elif seat_status == "available" and "is_available" not in payload:
        payload["is_available"] = True
    return payload


@router.get("/bookings/release-logs", response_model=list[BookingReleaseLogOut])
def admin_list_release_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[BookingReleaseLogOut]:
    stmt = select(BookingReleaseLog)
    if user_id is not None:
        stmt = stmt.where(BookingReleaseLog.user_id == user_id)
    stmt = stmt.order_by(BookingReleaseLog.id.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


@router.get("/bookings")
def admin_list_bookings(
    booking_status: str | None = Query(default=None, alias="status"),
    store_id: int | None = None,
    user_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> dict:
    if start_from and start_to and start_from > start_to:
        raise error_response(status.HTTP_400_BAD_REQUEST, "开始时间不能晚于结束时间")

    bookings = list_admin_bookings(
        db,
        booking_status=booking_status,
        store_id=store_id,
        user_id=user_id,
        start_from=start_from,
        start_to=start_to,
        skip=skip,
        limit=limit,
    )

    seat_map = {
        seat.id: seat
        for seat in db.scalars(
            select(Seat).where(Seat.id.in_([item.seat_id for item in bookings]))
        ).all()
    } if bookings else {}

    data = []
    for item in bookings:
        seat = seat_map.get(item.seat_id)
        data.append(
            {
                "id": item.id,
                "user_id": item.user_id,
                "seat_id": item.seat_id,
                "seat_no": seat.seat_no if seat else None,
                "store_id": item.store_id,
                "start_time": item.start_time,
                "end_time": item.end_time,
                "status": item.status,
                "checked_in_at": item.checked_in_at,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
        )
    return success_response(data=data)


@router.post("/bookings")
def admin_create_booking_api(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    lock_client: Redis = Depends(get_redis_client),
    current_user: CurrentAuthUser = Depends(require_admin_token_user),
) -> dict:
    try:
        booking = create_booking_with_lock(db, lock_client, payload)
    except BookingValidationError as exc:
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
        raise error_response(status.HTTP_403_FORBIDDEN, "该用户已被列入黑名单，暂时无法预约") from exc
    except UserBookingConflictError as exc:
        raise error_response(status.HTTP_409_CONFLICT, "该用户在所选时间段已有其他预约，不能重复预约") from exc
    except SeatLockBusyError as exc:
        raise error_response(status.HTTP_409_CONFLICT, "该座位正在处理其他预约，请稍后重试") from exc
    except LockServiceUnavailableError as exc:
        raise error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "预约锁服务不可用，请稍后重试") from exc
    except BookingConflictError as exc:
        raise error_response(status.HTTP_409_CONFLICT, "该座位在所选时间段已被预约，请更换时间或座位") from exc
    except BookingStateError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    if get_order_by_booking_id(db, booking.id) is None:
        try:
            create_order(db, booking_id=booking.id, user_id=booking.user_id, amount=0, status="pending")
        except IntegrityError:
            db.rollback()

    try:
        queue_student_notification(
            db,
            user_id=booking.user_id,
            title="管理员已为您创建预约",
            content=(
                f"管理员已为您预约座位 #{booking.seat_id}，"
                f"开始时间：{booking.start_time.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')}，"
                f"结束时间：{booking.end_time.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')}。"
            ),
            notification_type="booking",
            related_type="booking",
            related_id=booking.id,
        )
    except Exception:
        db.rollback()

    return success_response(
        message="已代学生创建预约",
        data={
            "booking_id": booking.id,
            "status": booking.status,
            "user_id": booking.user_id,
            "seat_id": booking.seat_id,
            "operator_id": current_user.id,
        },
    )


@router.post("/bookings/{booking_id}/cancel")
def admin_cancel_booking_api(
    booking_id: int,
    reason: str = "管理员手动取消预约",
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_admin_token_user),
) -> dict:
    try:
        booking = admin_cancel_booking(db, booking_id=booking_id, reason=reason)
    except BookingNotFoundError as exc:
        raise error_response(status.HTTP_404_NOT_FOUND, "预约不存在") from exc
    except BookingStateError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return success_response(
        message="取消预约成功",
        data={
            "booking_id": booking.id,
            "status": booking.status,
            "operator_id": current_user.id,
        },
    )


@router.post("/bookings/{booking_id}/force-checkin")
def admin_force_checkin_booking_api(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_admin_portal_token_user),
) -> dict:
    try:
        booking = admin_force_checkin_booking(db, booking_id=booking_id)
    except BookingNotFoundError as exc:
        raise error_response(status.HTTP_404_NOT_FOUND, "预约不存在") from exc
    except BookingStateError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return success_response(
        message="强制签到成功",
        data={
            "booking_id": booking.id,
            "status": booking.status,
            "checked_in_at": booking.checked_in_at,
            "operator_id": current_user.id,
        },
    )


@router.post("/bookings/{booking_id}/complete")
def admin_complete_booking_api(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_admin_token_user),
) -> dict:
    try:
        booking = admin_complete_booking(db, booking_id=booking_id)
    except BookingNotFoundError as exc:
        raise error_response(status.HTTP_404_NOT_FOUND, "预约不存在") from exc
    except BookingStateError as exc:
        raise error_response(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return success_response(
        message="标记完成成功",
        data={
            "booking_id": booking.id,
            "status": booking.status,
            "operator_id": current_user.id,
        },
    )


@router.get("/operation-logs", response_model=OperationLogPageOut)
def admin_list_operation_logs_api(
    skip: int = 0,
    limit: int = 20,
    module: str | None = None,
    operator_id: int | None = None,
    operator_keyword: str | None = None,
    request_method: str | None = Query(default=None, alias="method"),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> OperationLogPageOut:
    if start_time and end_time and start_time > end_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="开始时间不能晚于结束时间")
    total, items = list_admin_operation_logs(
        db,
        skip=skip,
        limit=limit,
        module=module,
        operator_id=operator_id,
        operator_keyword=operator_keyword,
        request_method=request_method,
        start_time=start_time,
        end_time=end_time,
    )
    return OperationLogPageOut(total=total, skip=skip, limit=limit, items=[_serialize_operation_log(i) for i in items])


@router.get("/checkins/records", response_model=CheckinRecordPageOut)
def admin_list_checkin_records(
    store_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> CheckinRecordPageOut:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="开始时间不能晚于结束时间")

    total, items = list_checkin_records(
        db,
        store_id=store_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    return CheckinRecordPageOut(
        total=total,
        skip=skip,
        limit=limit,
        items=[CheckinRecordOut.model_validate(item) for item in items],
    )


# Blacklists
@router.get("/blacklists", response_model=list[BlacklistOut])
def admin_list_blacklists(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[BlacklistOut]:
    return list_blacklists(db, skip=skip, limit=limit)


@router.post("/blacklists", response_model=BlacklistActionOut, status_code=status.HTTP_201_CREATED)
def admin_add_blacklist(
    payload: BlacklistCreateIn,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_admin_token_user),
) -> BlacklistActionOut:
    user = get_user(db, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    reason = payload.reason or "管理员手动拉黑"
    config = get_system_config(db)
    _, created = add_user_to_blacklist(
        db,
        user_id=payload.user_id,
        reason=reason,
        source="manual",
        duration_days=int(config.get("blacklist_effective_days", 7)),
        no_show_count_snapshot=user.no_show_count,
        created_by=current_user.id,
    )
    if created:
        queue_student_notification(
            db,
            user_id=payload.user_id,
            title="黑名单提醒",
            content=f"您已被管理员加入黑名单，原因：{reason}",
            notification_type="violation",
            related_type="blacklist",
            related_id=payload.user_id,
        )
    return BlacklistActionOut(
        user_id=payload.user_id,
        blacklisted=True,
        message="已加入黑名单" if created else "用户已在黑名单中",
    )


@router.delete("/blacklists/{user_id}", response_model=BlacklistActionOut)
def admin_remove_blacklist(
    user_id: int,
    reset_no_show_count: bool = False,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> BlacklistActionOut:
    removed = remove_user_from_blacklist(db, user_id=user_id, reset_no_show_count=reset_no_show_count)
    if removed:
        queue_student_notification(
            db,
            user_id=user_id,
            title="黑名单解除通知",
            content="管理员已将您移出黑名单，您现在可以继续正常预约。",
            notification_type="system",
            related_type="blacklist",
            related_id=user_id,
        )
    return BlacklistActionOut(
        user_id=user_id,
        blacklisted=False,
        message="已移出黑名单" if removed else "用户不在黑名单中",
    )


# Users
@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_admin_token_user),
) -> UserOut:
    if payload.role in {"staff", "admin", "super_admin"} and current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅超级管理员可创建员工账号")
    try:
        return create_user(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="手机号或邮箱已存在") from exc


@router.get("/users", response_model=list[AdminUserListOut])
def admin_list_users(
    skip: int = 0,
    limit: int = 100,
    keyword: str | None = None,
    name: str | None = None,
    phone: str | None = None,
    role: str | None = None,
    user_status: int | None = Query(default=None, alias="status"),
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_portal_token_user),
) -> list[AdminUserListOut]:
    if created_from and created_to and created_from > created_to:
        raise error_response(status.HTTP_400_BAD_REQUEST, "开始时间不能晚于结束时间")
    users = list_users(
        db,
        skip=skip,
        limit=limit,
        keyword=keyword,
        name=name,
        phone=phone,
        role=role,
        status=user_status,
        created_from=created_from,
        created_to=created_to,
    )
    return _build_admin_user_list(db, users)


@router.get("/users/{user_id}", response_model=UserOut)
def admin_get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_portal_token_user),
) -> UserOut:
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user


@router.get("/users/{user_id}/detail", response_model=AdminUserDetailOut)
def admin_get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_portal_token_user),
) -> AdminUserDetailOut:
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    blacklist = db.scalars(
        select(BookingBlacklist)
        .where(BookingBlacklist.user_id == user.id, BookingBlacklist.is_active.is_(True))
        .order_by(BookingBlacklist.id.desc())
        .limit(1)
    ).first()
    history_booking_count = int(
        db.execute(select(func.count(Booking.id)).where(Booking.user_id == user.id)).scalar() or 0
    )
    last_booking_at = db.execute(
        select(func.max(Booking.created_at)).where(Booking.user_id == user.id)
    ).scalar()

    return AdminUserDetailOut(
        id=user.id,
        phone=user.phone,
        email=user.email,
        name=user.name,
        role=user.role,
        status=user.status,
        no_show_count=user.no_show_count,
        is_blacklisted=blacklist is not None,
        blacklist_end_at=blacklist.end_at if blacklist else None,
        history_booking_count=history_booking_count,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_booking_at=last_booking_at,
    )


@router.put("/users/{user_id}", response_model=UserOut)
def admin_update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_admin_token_user),
) -> UserOut:
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if current_user.id == user.id and payload.status == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能冻结当前登录账号")
    if current_user.id == user.id and payload.status == DELETED_USER_STATUS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除当前登录账号")
    target_role = payload.role if payload.role is not None else user.role
    if target_role in {"staff", "admin", "super_admin"} and current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅超级管理员可修改员工账号")
    try:
        return update_user(db, user, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="手机号或邮箱已存在") from exc


@router.post("/users/{user_id}/assign-role")
def admin_assign_user_role(
    user_id: int,
    payload: AdminUserRoleAssignIn,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_super_admin_token_user),
) -> dict:
    user = get_user(db, user_id)
    if user is None:
        raise error_response(status.HTTP_404_NOT_FOUND, "用户不存在")
    if user.status == DELETED_USER_STATUS:
        raise error_response(status.HTTP_400_BAD_REQUEST, "已删除用户不能分配权限")
    if current_user.id == user.id:
        raise error_response(status.HTTP_400_BAD_REQUEST, "不能修改当前登录账号的权限")

    updated = update_user(db, user, UserUpdate(role=payload.role))
    return success_response(
        message="权限分配成功",
        data=AdminUserRoleAssignOut(
            user_id=updated.id,
            role=updated.role,
            role_text=_role_text(updated.role),
        ).model_dump(),
    )


@router.post("/users/{user_id}/freeze", response_model=UserOut)
def admin_freeze_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_admin_token_user),
) -> UserOut:
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if current_user.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能冻结当前登录账号")
    if user.role in {"staff", "admin", "super_admin"} and current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅超级管理员可冻结员工账号")
    return update_user(db, user, UserUpdate(status=0))


@router.post("/users/{user_id}/unfreeze", response_model=UserOut)
def admin_unfreeze_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_admin_token_user),
) -> UserOut:
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if user.role in {"staff", "admin", "super_admin"} and current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅超级管理员可解冻员工账号")
    return update_user(db, user, UserUpdate(status=1))


@router.delete("/users/{user_id}")
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_admin_token_user),
) -> dict:
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if current_user.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除当前登录账号")
    if user.role in {"staff", "admin", "super_admin"} and current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅超级管理员可删除员工账号")
    delete_user(db, user)
    return success_response(message="用户已删除", data={"user_id": user_id, "status": DELETED_USER_STATUS})


# Stores
@router.post("/stores", response_model=StoreOut, status_code=status.HTTP_201_CREATED)
def admin_create_store(
    payload: StoreCreate,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> StoreOut:
    try:
        return create_store(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="门店数据校验失败，请检查后重试") from exc


@router.get("/stores", response_model=list[StoreOut])
def admin_list_stores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[StoreOut]:
    return list_stores(db, skip=skip, limit=limit)


@router.get("/stores/{store_id}", response_model=StoreOut)
def admin_get_store(store_id: int, db: Session = Depends(get_db)) -> StoreOut:
    store = get_store(db, store_id)
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="门店不存在")
    return store


@router.put("/stores/{store_id}", response_model=StoreOut)
def admin_update_store(
    store_id: int,
    payload: StoreUpdate,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> StoreOut:
    store = get_store(db, store_id)
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="门店不存在")
    try:
        return update_store(db, store, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="门店数据校验失败，请检查后重试") from exc


@router.delete("/stores/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_store(
    store_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> Response:
    store = get_store(db, store_id)
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="门店不存在")
    delete_store(db, store)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Areas
@router.post("/areas", response_model=AreaOut, status_code=status.HTTP_201_CREATED)
def admin_create_area(
    payload: AreaCreate,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> AreaOut:
    if get_store(db, payload.store_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="门店不存在")
    try:
        return create_area(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="区域数据校验失败，请检查后重试") from exc


@router.get("/areas", response_model=list[AreaOut])
def admin_list_areas(
    store_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[AreaOut]:
    return list_areas(db, store_id=store_id, skip=skip, limit=limit)


@router.get("/areas/{area_id}", response_model=AreaOut)
def admin_get_area(area_id: int, db: Session = Depends(get_db)) -> AreaOut:
    area = get_area(db, area_id)
    if area is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="区域不存在")
    return area


@router.put("/areas/{area_id}", response_model=AreaOut)
def admin_update_area(
    area_id: int,
    payload: AreaUpdate,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> AreaOut:
    area = get_area(db, area_id)
    if area is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="区域不存在")
    try:
        return update_area(db, area, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="区域数据校验失败，请检查后重试") from exc


@router.delete("/areas/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_area(
    area_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> Response:
    area = get_area(db, area_id)
    if area is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="区域不存在")
    delete_area(db, area)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Seats
@router.post("/seats", response_model=AdminSeatOut, status_code=status.HTTP_201_CREATED)
def admin_create_seat(
    payload: AdminSeatCreate,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> AdminSeatOut:
    data = _apply_seat_state(payload.model_dump())
    if get_store(db, data["store_id"]) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="门店不存在")
    try:
        return create_seat(db, AdminSeatCreate.model_validate(data))
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="座位数据校验失败，请检查后重试") from exc


@router.post("/seats/batch", response_model=AdminSeatBatchCreateOut, status_code=status.HTTP_201_CREATED)
def admin_batch_create_seats(
    payload: AdminSeatBatchCreateIn,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> AdminSeatBatchCreateOut:
    if payload.end_no < payload.start_no:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="结束编号不能小于开始编号")
    if get_store(db, payload.store_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="门店不存在")
    if payload.area_id is not None and get_area(db, payload.area_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="区域不存在")

    created_count = 0
    skipped_count = 0
    created_seat_nos: list[str] = []
    width = max(1, payload.padding)

    for no in range(payload.start_no, payload.end_no + 1):
        seat_no = f"{payload.prefix}{no:0{width}d}"
        exists = db.scalar(
            select(Seat.id).where(
                Seat.store_id == payload.store_id,
                Seat.seat_no == seat_no,
            )
        )
        if exists is not None:
            skipped_count += 1
            continue
        seat = Seat(
            store_id=payload.store_id,
            area_id=payload.area_id,
            seat_no=seat_no,
            seat_type=payload.seat_type,
            seat_status=payload.seat_status,
            is_available=payload.is_available if payload.seat_status == "available" else False,
        )
        db.add(seat)
        created_count += 1
        created_seat_nos.append(seat_no)

    db.commit()
    return AdminSeatBatchCreateOut(
        created_count=created_count,
        skipped_count=skipped_count,
        seat_nos=created_seat_nos,
    )


@router.get("/seats", response_model=list[AdminSeatOut])
def admin_list_seats(
    store_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[AdminSeatOut]:
    return list_seats(db, skip=skip, limit=limit, store_id=store_id)


@router.get("/seats/{seat_id}", response_model=AdminSeatOut)
def admin_get_seat(seat_id: int, db: Session = Depends(get_db)) -> AdminSeatOut:
    seat = get_seat(db, seat_id)
    if seat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="座位不存在")
    return seat


@router.put("/seats/{seat_id}", response_model=AdminSeatOut)
def admin_update_seat(
    seat_id: int,
    payload: AdminSeatUpdate,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> AdminSeatOut:
    seat = get_seat(db, seat_id)
    if seat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="座位不存在")
    data = _apply_seat_state(payload.model_dump(exclude_unset=True))
    try:
        return update_seat(db, seat, AdminSeatUpdate.model_validate(data))
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="座位数据校验失败，请检查后重试") from exc


@router.delete("/seats/{seat_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_seat(
    seat_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> Response:
    seat = get_seat(db, seat_id)
    if seat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="座位不存在")
    delete_seat(db, seat)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Pricing plans
@router.post("/plans", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
def admin_create_plan(
    payload: PlanCreate,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> PlanOut:
    if get_store(db, payload.store_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="门店不存在")
    try:
        return create_plan(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="价格方案数据校验失败，请检查后重试") from exc


@router.get("/plans", response_model=list[PlanOut])
def admin_list_plans(
    store_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[PlanOut]:
    return list_plans(db, store_id=store_id, skip=skip, limit=limit)


@router.get("/plans/{plan_id}", response_model=PlanOut)
def admin_get_plan(plan_id: int, db: Session = Depends(get_db)) -> PlanOut:
    plan = get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="价格方案不存在")
    return plan


@router.put("/plans/{plan_id}", response_model=PlanOut)
def admin_update_plan(
    plan_id: int,
    payload: PlanUpdate,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> PlanOut:
    plan = get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="价格方案不存在")
    try:
        return update_plan(db, plan, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="价格方案数据校验失败，请检查后重试") from exc


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> Response:
    plan = get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="价格方案不存在")
    delete_plan(db, plan)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Orders
@router.get("/orders", response_model=OrderPageOut)
def admin_list_orders(
    store_id: int | None = None,
    order_status: str | None = Query(default=None, alias="status"),
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> OrderPageOut:
    if date_from and date_to and date_from > date_to:
        raise error_response(status.HTTP_400_BAD_REQUEST, "开始时间不能晚于结束时间")
    total, items = list_orders(
        db,
        store_id=store_id,
        status=order_status,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    return OrderPageOut(total=total, skip=skip, limit=limit, items=[OrderOut(**item) for item in items])


@router.get("/orders/{order_id}", response_model=OrderOut)
def admin_get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_portal_token_user),
) -> OrderOut:
    item = get_order_detail(db, order_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    return OrderOut(**item)


@router.get("/orders/export")
def admin_export_orders_csv(
    store_id: int | None = None,
    order_status: str | None = Query(default=None, alias="status"),
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> Response:
    if date_from and date_to and date_from > date_to:
        raise error_response(status.HTTP_400_BAD_REQUEST, "开始时间不能晚于结束时间")

    _, rows = list_orders(
        db,
        store_id=store_id,
        status=order_status,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
        skip=0,
        limit=5000,
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["订单编号", "预约编号", "用户编号", "昵称", "手机号", "门店", "座位", "金额", "状态", "创建时间"])
    for row in rows:
        writer.writerow(
            [
                row["id"],
                row["booking_id"],
                row["user_id"],
                row.get("user_name") or "",
                row.get("user_phone") or "",
                row.get("store_name") or "",
                row.get("seat_no") or "",
                row["amount"],
                row["status"],
                row["created_at"].isoformat() if row.get("created_at") else "",
            ]
        )

    csv_content = "\ufeff" + output.getvalue()
    output.close()

    filename = f"orders_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/orders/{order_id}/cancel", response_model=OrderActionOut)
def admin_cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> OrderActionOut:
    order = get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.status in {"cancelled", "refunded"}:
        return OrderActionOut(order_id=order.id, status=order.status)
    if order.status == "paid":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已支付订单不能直接取消，请走退款流程")
    order = update_order_status(db, order, "cancelled")
    return OrderActionOut(order_id=order.id, status=order.status)


@router.post("/orders/{order_id}/paid", response_model=OrderActionOut)
def admin_mark_order_paid(
    order_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> OrderActionOut:
    order = get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.status == "paid":
        return OrderActionOut(order_id=order.id, status=order.status)
    if order.status in {"cancelled", "refunded"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前订单状态不可标记为已支付")
    order = update_order_status(db, order, "paid")
    return OrderActionOut(order_id=order.id, status=order.status)


@router.post("/orders/{order_id}/refund", response_model=OrderActionOut)
def admin_refund_order(
    order_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> OrderActionOut:
    order = get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.status == "refunded":
        return OrderActionOut(order_id=order.id, status=order.status)
    if order.status != "paid":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有已支付订单才能退款")
    order = update_order_status(db, order, "refunded")
    return OrderActionOut(order_id=order.id, status=order.status)


# Memberships
@router.get("/memberships", response_model=list[MembershipOut])
def admin_list_memberships(
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[MembershipOut]:
    return list_member_cards(db, skip=skip, limit=limit, user_id=user_id)


@router.post("/memberships/open", response_model=MembershipOut, status_code=status.HTTP_201_CREATED)
def admin_open_membership(
    payload: MembershipOpenIn,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> MembershipOut:
    if payload.expire_at is None:
        payload_expire_at = (datetime.now(timezone.utc).date() + timedelta(days=30))
    else:
        payload_expire_at = payload.expire_at
    data = MemberCardCreate(
        user_id=payload.user_id,
        card_name=payload.card_name,
        card_type=payload.card_type,
        balance_minutes=payload.balance_minutes,
        balance_times=payload.balance_times,
        expire_at=payload_expire_at,
        status="active",
    )
    card = MemberCard(**data.model_dump())
    db.add(card)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="会员卡数据校验失败，请检查后重试") from exc
    db.refresh(card)
    return card


@router.post("/memberships/{membership_id}/renew", response_model=MembershipOut)
def admin_renew_membership(
    membership_id: int,
    payload: MembershipRenewIn,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> MembershipOut:
    card = get_member_card(db, membership_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会员卡不存在")
    return renew_member_card(
        db,
        card,
        add_minutes=payload.add_minutes,
        add_times=payload.add_times,
        extend_days=payload.extend_days,
    )


@router.post("/memberships/{membership_id}/freeze", response_model=MembershipOut)
def admin_freeze_membership(
    membership_id: int,
    payload: MembershipFreezeIn,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> MembershipOut:
    card = get_member_card(db, membership_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会员卡不存在")
    return set_member_card_frozen(db, card, frozen=payload.frozen)


# Notices
@router.post("/notices", response_model=NoticeOut, status_code=status.HTTP_201_CREATED)
def admin_create_notice(
    payload: NoticeCreate,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
    current_user: CurrentAuthUser = Depends(get_current_token_user),
) -> NoticeOut:
    if payload.store_id is not None and get_store(db, payload.store_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="门店不存在")
    notice = create_notice(db, payload, created_by=current_user.id)
    if notice.status == "published":
        queue_notice_notifications_for_students(db, notice=notice)
    return notice


@router.get("/notices", response_model=list[NoticeOut])
def admin_list_notices(
    store_id: int | None = None,
    notice_status: str | None = Query(default=None, alias="status"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[NoticeOut]:
    return list_notices(db, store_id=store_id, status=notice_status, skip=skip, limit=limit)


@router.get("/notices/{notice_id}", response_model=NoticeDetailOut)
def admin_get_notice_detail(
    notice_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_portal_token_user),
) -> NoticeDetailOut:
    notice = get_notice(db, notice_id)
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")
    return _notice_detail_out(db, notice)


@router.put("/notices/{notice_id}", response_model=NoticeOut)
def admin_update_notice(
    notice_id: int,
    payload: NoticeUpdate,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> NoticeOut:
    notice = get_notice(db, notice_id)
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")
    previous_status = notice.status
    updated_notice = update_notice(db, notice, payload)
    if previous_status != "published" and updated_notice.status == "published":
        queue_notice_notifications_for_students(db, notice=updated_notice)
    return updated_notice


@router.delete("/notices/{notice_id}")
def admin_delete_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> dict:
    notice = get_notice(db, notice_id)
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")
    delete_notice(db, notice)
    return success_response(message="公告删除成功")


@router.post("/notices/{notice_id}/publish", response_model=NoticeOut)
def admin_publish_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> NoticeOut:
    notice = get_notice(db, notice_id)
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")
    was_published = notice.status == "published"
    updated_notice = set_notice_status(db, notice, "published")
    if not was_published:
        queue_notice_notifications_for_students(db, notice=updated_notice)
    return updated_notice


@router.post("/notices/{notice_id}/offline", response_model=NoticeOut)
def admin_offline_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_token_user),
) -> NoticeOut:
    notice = get_notice(db, notice_id)
    if notice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")
    return set_notice_status(db, notice, "offline")


@router.get("/system-config", response_model=SystemConfigOut)
def admin_get_system_config(
    db: Session = Depends(get_db),
    _admin: CurrentAuthUser = Depends(require_admin_portal_token_user),
) -> SystemConfigOut:
    return SystemConfigOut(**get_system_config(db))


@router.put("/system-config", response_model=SystemConfigOut)
def admin_update_system_config(
    payload: SystemConfigUpdateIn,
    db: Session = Depends(get_db),
    _super_admin: CurrentAuthUser = Depends(require_super_admin_token_user),
) -> SystemConfigOut:
    updates = payload.model_dump(exclude_none=True)
    current = get_system_config(db)
    merged = {**current, **updates}
    if merged["min_booking_minutes"] > merged["max_booking_hours"] * 60:
        raise error_response(status.HTTP_400_BAD_REQUEST, "最短预约时长不能大于最长预约时长")
    if merged["cancel_before_minutes"] > merged["reschedule_before_minutes"]:
        raise error_response(status.HTTP_400_BAD_REQUEST, "可取消时间不能晚于可改期时间")
    if merged["default_open_time"] >= merged["default_close_time"]:
        raise error_response(status.HTTP_400_BAD_REQUEST, "默认营业开始时间必须早于结束时间")

    upsert_settings(db, values=updates)
    return SystemConfigOut(**get_system_config(db))


@router.post("/system-config/reset", response_model=SystemConfigOut)
def admin_reset_system_config(
    db: Session = Depends(get_db),
    _super_admin: CurrentAuthUser = Depends(require_super_admin_token_user),
) -> SystemConfigOut:
    return SystemConfigOut(**reset_settings_to_defaults(db))


# Stats
@router.get("/stats/overview", response_model=StatsOverviewOut)
def admin_stats_overview(
    store_id: int | None = None,
    query_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
) -> StatsOverviewOut:
    target_date = query_date or datetime.now(timezone.utc).date()
    stats, _ = get_overview_stats(db, target_date=target_date, store_id=store_id)
    return stats


@router.get("/stats/checkin", response_model=CheckinStatsOut)
def admin_stats_checkin(
    store_id: int | None = None,
    query_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
) -> CheckinStatsOut:
    target_date = query_date or datetime.now(timezone.utc).date()
    stats, _ = get_checkin_stats(db, target_date=target_date, store_id=store_id)
    return stats


@router.get("/checkins/stats", response_model=CheckinStatsOut)
def admin_checkins_stats(
    store_id: int | None = None,
    query_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
) -> CheckinStatsOut:
    target_date = query_date or datetime.now(timezone.utc).date()
    stats, _ = get_checkin_stats(db, target_date=target_date, store_id=store_id)
    return stats
