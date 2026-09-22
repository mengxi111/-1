from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.booking_blacklist import BookingBlacklist
from app.models.user import User


def get_blacklist_by_user_id(db: Session, user_id: int) -> BookingBlacklist | None:
    now = datetime.now(timezone.utc)
    stmt = (
        select(BookingBlacklist)
        .where(
            BookingBlacklist.user_id == user_id,
            BookingBlacklist.is_active.is_(True),
            (BookingBlacklist.end_at.is_(None) | (BookingBlacklist.end_at > now)),
        )
        .limit(1)
    )
    return db.scalars(stmt).first()


def is_user_blacklisted(db: Session, user_id: int) -> bool:
    return get_blacklist_by_user_id(db, user_id) is not None


def list_blacklists(db: Session, skip: int = 0, limit: int = 100) -> list[BookingBlacklist]:
    stmt = (
        select(BookingBlacklist)
        .offset(skip)
        .limit(limit)
        .order_by(BookingBlacklist.is_active.desc(), BookingBlacklist.id.desc())
    )
    return list(db.scalars(stmt).all())


def add_user_to_blacklist(
    db: Session,
    *,
    user_id: int,
    reason: str,
    source: str,
    duration_days: int | None = None,
    no_show_count_snapshot: int | None = None,
    created_by: int | None = None,
    commit: bool = True,
) -> tuple[BookingBlacklist, bool]:
    now = datetime.now(timezone.utc)
    end_at = now + timedelta(days=duration_days) if duration_days and duration_days > 0 else None
    obj = db.scalars(
        select(BookingBlacklist).where(BookingBlacklist.user_id == user_id).with_for_update()
    ).first()

    created = False
    if obj is None:
        obj = BookingBlacklist(
            user_id=user_id,
            reason=reason,
            source=source,
            no_show_count_snapshot=no_show_count_snapshot,
            created_by=created_by,
            start_at=now,
            end_at=end_at,
            is_active=True,
        )
        db.add(obj)
        db.flush()
        created = True
    else:
        if not obj.is_active:
            created = True
        obj.reason = reason
        obj.source = source
        obj.no_show_count_snapshot = no_show_count_snapshot
        obj.created_by = created_by
        obj.start_at = now
        obj.end_at = end_at
        obj.is_active = True
        db.add(obj)

    if commit:
        db.commit()
        db.refresh(obj)
    return obj, created


def remove_user_from_blacklist(
    db: Session,
    *,
    user_id: int,
    reset_no_show_count: bool = False,
    commit: bool = True,
) -> bool:
    now = datetime.now(timezone.utc)
    updated = db.execute(
        update(BookingBlacklist)
        .where(BookingBlacklist.user_id == user_id, BookingBlacklist.is_active.is_(True))
        .values(is_active=False, end_at=now)
    )
    if reset_no_show_count:
        db.execute(update(User).where(User.id == user_id).values(no_show_count=0))
    removed = (updated.rowcount or 0) > 0
    if commit:
        db.commit()
    return removed
