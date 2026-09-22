from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notice import Notice
from app.schemas.notice import NoticeCreate, NoticeUpdate


def create_notice(db: Session, payload: NoticeCreate, created_by: int | None) -> Notice:
    data = payload.model_dump()
    if data.get("status") == "published":
        data["published_at"] = datetime.now(timezone.utc)
    obj = Notice(**data, created_by=created_by)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_notices(
    db: Session,
    store_id: int | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Notice]:
    stmt = select(Notice)
    if store_id is not None:
        stmt = stmt.where(Notice.store_id == store_id)
    if status:
        stmt = stmt.where(Notice.status == status)
    stmt = stmt.offset(skip).limit(limit).order_by(Notice.id.desc())
    return list(db.scalars(stmt).all())


def get_notice(db: Session, notice_id: int) -> Notice | None:
    return db.get(Notice, notice_id)


def get_published_notice(db: Session, notice_id: int) -> Notice | None:
    stmt = select(Notice).where(Notice.id == notice_id, Notice.status == "published").limit(1)
    return db.scalars(stmt).first()


def update_notice(db: Session, obj: Notice, payload: NoticeUpdate) -> Notice:
    data = payload.model_dump(exclude_unset=True)
    status = data.get("status")
    if status == "published" and obj.status != "published":
        data["published_at"] = datetime.now(timezone.utc)
    if status in {"draft", "offline"}:
        data["published_at"] = None
    for field, value in data.items():
        setattr(obj, field, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def set_notice_status(db: Session, obj: Notice, status: str) -> Notice:
    obj.status = status
    obj.published_at = datetime.now(timezone.utc) if status == "published" else None
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_notice(db: Session, obj: Notice) -> None:
    db.delete(obj)
    db.commit()
