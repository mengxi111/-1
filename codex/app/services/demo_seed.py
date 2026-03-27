from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.crud.student_notification import queue_student_notification
from app.models.booking import Booking
from app.models.booking_blacklist import BookingBlacklist
from app.models.booking_checkin_record import BookingCheckinRecord
from app.models.booking_release_log import BookingReleaseLog
from app.models.notice import Notice
from app.models.order import Order
from app.models.seat import Seat
from app.models.store import Store
from app.models.student_notification import StudentNotification
from app.models.user import User
from app.services.bootstrap import bootstrap_initial_data

ACTIVE_BOOKING_STATUSES = {"booked", "checked_in"}
PAID_BOOKING_STATUSES = {"checked_in", "completed"}


@dataclass
class DemoSeedResult:
    stores_created: int = 0
    areas_created: int = 0
    seats_created: int = 0
    plans_created: int = 0
    users_created: int = 0
    bookings_created: int = 0
    notices_created: int = 0
    notifications_created: int = 0
    orders_created: int = 0

    @property
    def total_created(self) -> int:
        return (
            self.stores_created
            + self.areas_created
            + self.seats_created
            + self.plans_created
            + self.users_created
            + self.bookings_created
            + self.notices_created
            + self.notifications_created
            + self.orders_created
        )


def _count(db: Session, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _need_seed(db: Session) -> bool:
    return _count(db, User) == 0 and _count(db, Booking) == 0 and _count(db, Notice) == 0


def _needs_name_repair(name: str | None) -> bool:
    return not name or "?" in name


def _get_or_create_demo_user(db: Session, *, account: str, role: str, display_name: str) -> tuple[User, bool]:
    user = db.execute(select(User).where(User.phone == account)).scalar_one_or_none()
    if user is not None:
        if not user.password_hash:
            user.password_hash = hash_password("123456")
        if _needs_name_repair(user.name):
            user.name = display_name
        db.add(user)
        return user, False

    user = User(
        phone=account,
        name=display_name,
        role=role,
        status=1,
        password_hash=hash_password("123456"),
    )
    db.add(user)
    db.flush()
    return user, True


def _list_active_stores(db: Session) -> list[Store]:
    return list(
        db.scalars(
            select(Store)
            .where(Store.status == 1)
            .order_by(Store.id.asc())
        ).all()
    )


def _list_demo_students(db: Session) -> list[User]:
    blacklisted_user_ids = set(
        db.scalars(
            select(BookingBlacklist.user_id).where(BookingBlacklist.is_active.is_(True))
        ).all()
    )
    students = list(
        db.scalars(
            select(User)
            .where(
                User.role == "student",
                User.status == 1,
            )
            .order_by(User.id.asc())
        ).all()
    )
    return [student for student in students if student.id not in blacklisted_user_ids]


def _load_available_seats_by_store(db: Session, stores: list[Store]) -> dict[int, list[Seat]]:
    store_ids = [store.id for store in stores]
    if not store_ids:
        return {}

    seats = list(
        db.scalars(
            select(Seat)
            .where(
                Seat.store_id.in_(store_ids),
                Seat.is_available.is_(True),
                Seat.seat_status == "available",
            )
            .order_by(Seat.store_id.asc(), Seat.seat_no.asc())
        ).all()
    )

    grouped: dict[int, list[Seat]] = {store_id: [] for store_id in store_ids}
    for seat in seats:
        grouped.setdefault(seat.store_id, []).append(seat)
    return grouped


def _get_exact_booking(
    db: Session,
    *,
    user_id: int,
    seat_id: int,
    start_time: datetime,
    end_time: datetime,
) -> Booking | None:
    return db.execute(
        select(Booking).where(
            Booking.user_id == user_id,
            Booking.seat_id == seat_id,
            Booking.start_time == start_time,
            Booking.end_time == end_time,
        )
    ).scalar_one_or_none()


def _get_seed_booking(db: Session, *, marker: str) -> Booking | None:
    return db.execute(
        select(Booking).where(Booking.qr_token == marker)
    ).scalar_one_or_none()


def _has_active_booking_conflict(
    db: Session,
    *,
    seat_id: int | None = None,
    user_id: int | None = None,
    start_time: datetime,
    end_time: datetime,
) -> bool:
    stmt = select(Booking.id).where(
        Booking.status.in_(tuple(ACTIVE_BOOKING_STATUSES)),
        Booking.start_time < end_time,
        Booking.end_time > start_time,
    )
    if seat_id is not None:
        stmt = stmt.where(Booking.seat_id == seat_id)
    if user_id is not None:
        stmt = stmt.where(Booking.user_id == user_id)
    return db.execute(stmt.limit(1)).scalar_one_or_none() is not None


def _pick_seed_seat(
    db: Session,
    *,
    seats: list[Seat],
    seat_slot: int,
    start_time: datetime,
    end_time: datetime,
    status: str,
) -> Seat | None:
    if not seats:
        return None

    if status not in ACTIVE_BOOKING_STATUSES:
        return seats[seat_slot % len(seats)]

    for offset in range(len(seats)):
        candidate = seats[(seat_slot + offset) % len(seats)]
        if not _has_active_booking_conflict(
            db,
            seat_id=candidate.id,
            start_time=start_time,
            end_time=end_time,
        ):
            return candidate
    return None


def _pick_seed_student(
    db: Session,
    *,
    students: list[User],
    user_slot: int,
    start_time: datetime,
    end_time: datetime,
    status: str,
) -> User | None:
    if not students:
        return None

    if status not in ACTIVE_BOOKING_STATUSES:
        return students[user_slot % len(students)]

    for offset in range(len(students)):
        candidate = students[(user_slot + offset) % len(students)]
        if not _has_active_booking_conflict(
            db,
            user_id=candidate.id,
            start_time=start_time,
            end_time=end_time,
        ):
            return candidate
    return None


def _upsert_booking(
    db: Session,
    *,
    user: User,
    store: Store,
    seat: Seat,
    start_time: datetime,
    end_time: datetime,
    status: str,
    checked_in_at: datetime | None = None,
    cancel_reason: str | None = None,
    expire_reason: str | None = None,
    created_at: datetime | None = None,
    marker: str,
) -> tuple[Booking, bool]:
    booking = _get_seed_booking(db, marker=marker)
    if booking is None:
        booking = _get_exact_booking(
            db,
            user_id=user.id,
            seat_id=seat.id,
            start_time=start_time,
            end_time=end_time,
        )
    created = False
    if booking is None:
        booking = Booking(
            user_id=user.id,
            store_id=store.id,
            seat_id=seat.id,
            start_time=start_time,
            end_time=end_time,
        )
        created = True

    booking.status = status
    booking.checked_in_at = checked_in_at
    booking.sign_in_time = checked_in_at
    booking.cancel_reason = cancel_reason
    booking.expire_reason = expire_reason
    booking.qr_token = marker
    if created_at is not None:
        booking.created_at = created_at
        booking.updated_at = created_at

    db.add(booking)
    db.flush()
    return booking, created


def _upsert_order(
    db: Session,
    *,
    booking: Booking,
    amount: Decimal,
    status: str,
    created_at: datetime,
) -> bool:
    order = db.execute(select(Order).where(Order.booking_id == booking.id)).scalar_one_or_none()
    created = order is None
    if order is None:
        order = Order(
            booking_id=booking.id,
            user_id=booking.user_id,
            amount=amount,
            status=status,
        )
    order.amount = amount
    order.status = status
    order.created_at = created_at
    order.updated_at = created_at
    db.add(order)
    db.flush()
    return created


def _upsert_checkin_record(db: Session, *, booking: Booking) -> bool:
    if booking.checked_in_at is None or booking.status not in PAID_BOOKING_STATUSES:
        return False

    record = db.execute(
        select(BookingCheckinRecord).where(BookingCheckinRecord.booking_id == booking.id)
    ).scalar_one_or_none()
    created = record is None
    if record is None:
        record = BookingCheckinRecord(
            booking_id=booking.id,
            user_id=booking.user_id,
            seat_id=booking.seat_id,
            store_id=booking.store_id,
            checkin_time=booking.checked_in_at,
            checkin_method="code",
        )
    record.checkin_time = booking.checked_in_at
    record.checkin_method = "code"
    record.store_id = booking.store_id
    db.add(record)
    db.flush()
    return created


def _upsert_release_log(db: Session, *, booking: Booking) -> bool:
    if booking.status != "expired":
        return False

    log = db.execute(
        select(BookingReleaseLog).where(BookingReleaseLog.booking_id == booking.id)
    ).scalar_one_or_none()
    created = log is None
    if log is None:
        log = BookingReleaseLog(
            booking_id=booking.id,
            user_id=booking.user_id,
            seat_id=booking.seat_id,
            release_type="auto_timeout",
            reason="超时未签到自动过期",
            remark="看板演示数据",
            released_at=booking.end_time,
        )
    log.reason = "超时未签到自动过期"
    log.remark = "看板演示数据"
    log.released_at = booking.end_time
    db.add(log)
    db.flush()
    return created


def _booking_order_status(status: str) -> str:
    if status in PAID_BOOKING_STATUSES:
        return "paid"
    if status == "booked":
        return "pending"
    return "cancelled"


def _booking_amount(status: str, amount: Decimal) -> Decimal:
    if status in {"cancelled", "expired"}:
        return Decimal("0.00")
    return amount


def _seed_dashboard_bookings(
    db: Session,
    *,
    stores: list[Store],
    students: list[User],
) -> tuple[int, int]:
    if not stores or not students:
        return 0, 0

    seats_by_store = _load_available_seats_by_store(db, stores)
    if not all(seats_by_store.get(store.id) for store in stores):
        return 0, 0

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    day_start = now.replace(hour=0, minute=0)
    scenarios: list[dict] = []

    for day_index, day_offset in enumerate(range(-6, 0)):
        day_anchor = day_start + timedelta(days=day_offset)
        primary_store_slot = day_index % len(stores)
        secondary_store_slot = (day_index + 1) % len(stores)
        tertiary_store_slot = (day_index + 2) % len(stores)

        scenarios.append(
            {
                "marker": f"demo-dashboard-{day_offset}-morning",
                "store_slot": primary_store_slot,
                "seat_slot": day_index,
                "user_slot": day_index,
                "start_time": day_anchor + timedelta(hours=1, minutes=30),
                "end_time": day_anchor + timedelta(hours=3, minutes=30),
                "status": "completed",
                "checked_in_at": day_anchor + timedelta(hours=1, minutes=38),
                "amount": Decimal("10.00") + Decimal(day_index % 3),
            }
        )
        scenarios.append(
            {
                "marker": f"demo-dashboard-{day_offset}-afternoon",
                "store_slot": secondary_store_slot,
                "seat_slot": day_index + 1,
                "user_slot": day_index + 1,
                "start_time": day_anchor + timedelta(hours=4, minutes=30),
                "end_time": day_anchor + timedelta(hours=6),
                "status": "expired" if day_index in {1, 4} else "completed",
                "checked_in_at": None if day_index in {1, 4} else day_anchor + timedelta(hours=4, minutes=36),
                "expire_reason": "超时未签到自动过期" if day_index in {1, 4} else None,
                "amount": Decimal("12.00"),
            }
        )
        scenarios.append(
            {
                "marker": f"demo-dashboard-{day_offset}-evening",
                "store_slot": tertiary_store_slot,
                "seat_slot": day_index + 2,
                "user_slot": day_index + 2,
                "start_time": day_anchor + timedelta(hours=9),
                "end_time": day_anchor + timedelta(hours=11),
                "status": "cancelled" if day_index in {0, 3} else "completed",
                "checked_in_at": None if day_index in {0, 3} else day_anchor + timedelta(hours=9, minutes=8),
                "cancel_reason": "学生主动取消" if day_index in {0, 3} else None,
                "amount": Decimal("15.00"),
            }
        )

    scenarios.extend(
        [
            {
                "marker": "demo-dashboard-today-completed-1",
                "store_slot": 0,
                "seat_slot": 0,
                "user_slot": 0,
                "start_time": now - timedelta(hours=4, minutes=30),
                "end_time": now - timedelta(hours=2, minutes=30),
                "status": "completed",
                "checked_in_at": now - timedelta(hours=4, minutes=20),
                "amount": Decimal("10.00"),
            },
            {
                "marker": "demo-dashboard-today-completed-2",
                "store_slot": 0,
                "seat_slot": 0,
                "user_slot": 1,
                "start_time": now - timedelta(hours=2),
                "end_time": now - timedelta(minutes=30),
                "status": "completed",
                "checked_in_at": now - timedelta(hours=1, minutes=55),
                "amount": Decimal("10.00"),
            },
            {
                "marker": "demo-dashboard-today-checkin-live",
                "store_slot": 0,
                "seat_slot": 18,
                "user_slot": 2,
                "start_time": now - timedelta(minutes=45),
                "end_time": now + timedelta(minutes=75),
                "status": "checked_in",
                "checked_in_at": now - timedelta(minutes=40),
                "amount": Decimal("15.00"),
            },
            {
                "marker": "demo-dashboard-today-booked-live",
                "store_slot": 1 % len(stores),
                "seat_slot": 18,
                "user_slot": 3,
                "start_time": now - timedelta(minutes=20),
                "end_time": now + timedelta(minutes=100),
                "status": "booked",
                "checked_in_at": None,
                "amount": Decimal("12.00"),
            },
            {
                "marker": "demo-dashboard-today-expired",
                "store_slot": 2 % len(stores),
                "seat_slot": 2,
                "user_slot": 4,
                "start_time": now - timedelta(hours=3, minutes=30),
                "end_time": now - timedelta(hours=2),
                "status": "expired",
                "checked_in_at": None,
                "expire_reason": "超时未签到自动过期",
                "amount": Decimal("10.00"),
            },
            {
                "marker": "demo-dashboard-today-booked-future",
                "store_slot": 3 % len(stores),
                "seat_slot": 19,
                "user_slot": 5,
                "start_time": now + timedelta(hours=2),
                "end_time": now + timedelta(hours=4),
                "status": "booked",
                "checked_in_at": None,
                "amount": Decimal("10.00"),
            },
            {
                "marker": "demo-dashboard-today-cancelled",
                "store_slot": 1 % len(stores),
                "seat_slot": 4,
                "user_slot": 6,
                "start_time": now + timedelta(hours=5),
                "end_time": now + timedelta(hours=6),
                "status": "cancelled",
                "checked_in_at": None,
                "cancel_reason": "学生主动取消",
                "amount": Decimal("8.00"),
            },
            {
                "marker": "demo-dashboard-tomorrow-booked",
                "store_slot": 0,
                "seat_slot": 20,
                "user_slot": 7,
                "start_time": now + timedelta(days=1, hours=2),
                "end_time": now + timedelta(days=1, hours=4),
                "status": "booked",
                "checked_in_at": None,
                "amount": Decimal("12.00"),
            },
        ]
    )

    booking_created_count = 0
    order_created_count = 0

    for scenario in scenarios:
        existing_booking = _get_seed_booking(db, marker=scenario["marker"])

        store = stores[scenario["store_slot"] % len(stores)]
        seats = seats_by_store.get(store.id) or []
        if not seats:
            continue

        if existing_booking is not None:
            seat = next((item for item in seats if item.id == existing_booking.seat_id), None)
            student = next((item for item in students if item.id == existing_booking.user_id), None)
        else:
            seat = _pick_seed_seat(
                db,
                seats=seats,
                seat_slot=scenario["seat_slot"],
                start_time=scenario["start_time"],
                end_time=scenario["end_time"],
                status=scenario["status"],
            )
            student = _pick_seed_student(
                db,
                students=students,
                user_slot=scenario["user_slot"],
                start_time=scenario["start_time"],
                end_time=scenario["end_time"],
                status=scenario["status"],
            )
        if seat is None or student is None:
            continue

        booking, booking_created = _upsert_booking(
            db,
            user=student,
            store=store,
            seat=seat,
            start_time=scenario["start_time"],
            end_time=scenario["end_time"],
            status=scenario["status"],
            checked_in_at=scenario.get("checked_in_at"),
            cancel_reason=scenario.get("cancel_reason"),
            expire_reason=scenario.get("expire_reason"),
            created_at=scenario["start_time"] - timedelta(hours=12),
            marker=scenario["marker"],
        )
        booking_created_count += 1 if booking_created else 0

        order_created = _upsert_order(
            db,
            booking=booking,
            amount=_booking_amount(scenario["status"], scenario["amount"]),
            status=_booking_order_status(scenario["status"]),
            created_at=scenario["start_time"] - timedelta(minutes=25),
        )
        order_created_count += 1 if order_created else 0

        _upsert_checkin_record(db, booking=booking)
        _upsert_release_log(db, booking=booking)

    return booking_created_count, order_created_count


def _seed_notices(db: Session, *, store_id: int, admin_id: int) -> int:
    existing = _count(db, Notice)
    if existing > 0:
        return 0

    now = datetime.now(timezone.utc)
    notices = [
        Notice(
            store_id=store_id,
            title="欢迎使用自习室管理系统",
            content="请提前 10 分钟到店签到，保持安静，共同维护良好学习环境。",
            status="published",
            published_at=now,
            created_by=admin_id,
        ),
        Notice(
            store_id=store_id,
            title="座位使用提醒",
            content="请勿长时间离座占位，离开超过 30 分钟可能触发系统释放座位。",
            status="published",
            published_at=now,
            created_by=admin_id,
        ),
        Notice(
            store_id=store_id,
            title="夜间维护通知",
            content="每周日 23:00 后系统进行维护，期间可能短时无法预约。",
            status="offline",
            published_at=None,
            created_by=admin_id,
        ),
    ]
    db.add_all(notices)
    return len(notices)


def _seed_notifications(db: Session, *, student_id: int, booked_booking_id: int | None) -> int:
    exists = _count(db, StudentNotification)
    if exists > 0:
        return 0

    queue_student_notification(
        db,
        user_id=student_id,
        title="预约成功通知",
        content="您已成功创建预约，请按时到店签到。",
        notification_type="booking",
        related_type="booking",
        related_id=booked_booking_id,
        commit=False,
    )
    queue_student_notification(
        db,
        user_id=student_id,
        title="预约取消通知",
        content="您的一条预约已取消，如需使用请重新预约。",
        notification_type="booking",
        related_type="booking",
        related_id=booked_booking_id,
        commit=False,
    )
    queue_student_notification(
        db,
        user_id=student_id,
        title="即将开始提醒",
        content="您的预约即将开始，请准备前往自习室。",
        notification_type="booking",
        related_type="booking_reminder",
        related_id=booked_booking_id,
        commit=False,
    )
    queue_student_notification(
        db,
        user_id=student_id,
        title="黑名单规则提醒",
        content="累计爽约达到 3 次将自动加入黑名单，请按时签到。",
        notification_type="violation",
        related_type="blacklist_rule",
        related_id=student_id,
        commit=False,
    )
    return 4


def bootstrap_demo_data(db: Session, *, only_if_empty: bool = True) -> DemoSeedResult:
    result = DemoSeedResult()

    if only_if_empty and not _need_seed(db):
        return result

    base = bootstrap_initial_data(db, only_if_empty=False)
    result.stores_created += base.stores_created
    result.areas_created += base.areas_created
    result.seats_created += base.seats_created
    result.plans_created += base.plans_created

    stores = _list_active_stores(db)
    if not stores:
        return result

    try:
        super_admin, created = _get_or_create_demo_user(
            db,
            account="super_admin",
            role="super_admin",
            display_name="演示超级管理员",
        )
        result.users_created += 1 if created else 0

        admin, created = _get_or_create_demo_user(
            db,
            account="admin",
            role="admin",
            display_name="演示管理员",
        )
        result.users_created += 1 if created else 0

        student, created = _get_or_create_demo_user(
            db,
            account="student",
            role="student",
            display_name="演示学生",
        )
        result.users_created += 1 if created else 0

        demo_students = _list_demo_students(db)
        bookings_created, orders_created = _seed_dashboard_bookings(db, stores=stores, students=demo_students)
        result.bookings_created += bookings_created
        result.orders_created += orders_created

        primary_store = stores[0]
        result.notices_created += _seed_notices(db, store_id=primary_store.id, admin_id=admin.id or super_admin.id)

        booked_booking_id = db.execute(
            select(Booking.id)
            .where(Booking.user_id == student.id, Booking.status == "booked")
            .order_by(Booking.start_time.desc())
        ).scalar_one_or_none()
        result.notifications_created += _seed_notifications(
            db,
            student_id=student.id,
            booked_booking_id=booked_booking_id,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return result
