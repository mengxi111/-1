from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.area import Area
from app.schemas.admin_api import AreaCreate, AreaUpdate


def create_area(db: Session, payload: AreaCreate) -> Area:
    obj = Area(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_areas(db: Session, store_id: int | None = None, skip: int = 0, limit: int = 100) -> list[Area]:
    stmt = select(Area)
    if store_id is not None:
        stmt = stmt.where(Area.store_id == store_id)
    stmt = stmt.offset(skip).limit(limit).order_by(Area.sort_order.asc(), Area.id.asc())
    return list(db.scalars(stmt).all())


def get_area(db: Session, area_id: int) -> Area | None:
    return db.get(Area, area_id)


def update_area(db: Session, obj: Area, payload: AreaUpdate) -> Area:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_area(db: Session, obj: Area) -> None:
    db.delete(obj)
    db.commit()
