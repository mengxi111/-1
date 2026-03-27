from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.order import Order
from app.models.seat import Seat
from app.models.store import Store
from app.models.user import User


def create_order(
    db: Session,
    booking_id: int,
    user_id: int,
    amount: float,
    status: str = "pending",
) -> Order:
    obj = Order(booking_id=booking_id, user_id=user_id, amount=amount, status=status)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_order(db: Session, order_id: int) -> Order | None:
    return db.get(Order, order_id)


def get_order_by_booking_id(db: Session, booking_id: int) -> Order | None:
    stmt = select(Order).where(Order.booking_id == booking_id).limit(1)
    return db.scalars(stmt).first()


def _base_order_stmt():
    return (
        select(
            Order.id,
            Order.booking_id,
            Order.user_id,
            Order.amount,
            Order.status,
            Order.created_at,
            Order.updated_at,
            Booking.store_id,
            Booking.status.label("booking_status"),
            Booking.start_time,
            Booking.end_time,
            Store.name.label("store_name"),
            User.name.label("user_name"),
            User.phone.label("user_phone"),
            Seat.seat_no.label("seat_no"),
        )
        .join(Booking, Booking.id == Order.booking_id)
        .outerjoin(Store, Store.id == Booking.store_id)
        .outerjoin(User, User.id == Order.user_id)
        .outerjoin(Seat, Seat.id == Booking.seat_id)
    )


def _apply_order_filters(
    stmt,
    *,
    store_id: int | None = None,
    status: str | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    if store_id is not None:
        stmt = stmt.where(Booking.store_id == store_id)
    if status:
        stmt = stmt.where(Order.status == status)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                cast(Order.user_id, String).ilike(pattern),
                User.phone.ilike(pattern),
                User.name.ilike(pattern),
                Store.name.ilike(pattern),
            )
        )
    if date_from is not None:
        stmt = stmt.where(Order.created_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(Order.created_at <= date_to)
    return stmt


def _normalize_order_row(row: Any) -> dict[str, Any]:
    amount = row.amount
    if isinstance(amount, Decimal):
        amount = float(amount)
    return {
        "id": row.id,
        "booking_id": row.booking_id,
        "user_id": row.user_id,
        "amount": amount,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "store_id": row.store_id,
        "store_name": row.store_name,
        "user_name": row.user_name,
        "user_phone": row.user_phone,
        "booking_status": row.booking_status,
        "seat_no": row.seat_no,
        "start_time": row.start_time,
        "end_time": row.end_time,
    }


def list_orders(
    db: Session,
    store_id: int | None = None,
    status: str | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[int, list[dict[str, Any]]]:
    stmt = _apply_order_filters(
        _base_order_stmt(),
        store_id=store_id,
        status=status,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )
    count_stmt = _apply_order_filters(
        select(func.count(Order.id))
        .select_from(Order)
        .join(Booking, Booking.id == Order.booking_id)
        .outerjoin(Store, Store.id == Booking.store_id)
        .outerjoin(User, User.id == Order.user_id),
        store_id=store_id,
        status=status,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )
    total = int(db.execute(count_stmt).scalar() or 0)
    rows = db.execute(stmt.order_by(Order.id.desc()).offset(skip).limit(limit)).mappings().all()
    return total, [_normalize_order_row(row) for row in rows]


def get_order_detail(db: Session, order_id: int) -> dict[str, Any] | None:
    stmt = _base_order_stmt().where(Order.id == order_id).limit(1)
    row = db.execute(stmt).mappings().first()
    if row is None:
        return None
    return _normalize_order_row(row)


def update_order_status(db: Session, obj: Order, new_status: str) -> Order:
    obj.status = new_status
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
