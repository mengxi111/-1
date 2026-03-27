from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.booking_checkin_record import BookingCheckinRecord


def list_checkin_records(
    db: Session,
    *,
    store_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[int, list[BookingCheckinRecord]]:
    stmt = select(BookingCheckinRecord)
    count_stmt = select(func.count(BookingCheckinRecord.id))

    if store_id is not None:
        stmt = stmt.where(BookingCheckinRecord.store_id == store_id)
        count_stmt = count_stmt.where(BookingCheckinRecord.store_id == store_id)
    if date_from is not None:
        stmt = stmt.where(BookingCheckinRecord.checkin_time >= date_from)
        count_stmt = count_stmt.where(BookingCheckinRecord.checkin_time >= date_from)
    if date_to is not None:
        stmt = stmt.where(BookingCheckinRecord.checkin_time <= date_to)
        count_stmt = count_stmt.where(BookingCheckinRecord.checkin_time <= date_to)

    total = int(db.execute(count_stmt).scalar_one() or 0)
    items = list(
        db.scalars(
            stmt.order_by(BookingCheckinRecord.id.desc()).offset(skip).limit(limit)
        ).all()
    )
    return total, items
