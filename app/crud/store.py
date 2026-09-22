from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.store import Store
from app.schemas.store import StoreCreate, StoreUpdate


def create_store(db: Session, payload: StoreCreate) -> Store:
    obj = Store(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_stores(db: Session, skip: int = 0, limit: int = 100) -> list[Store]:
    stmt = select(Store).offset(skip).limit(limit).order_by(Store.id)
    return list(db.scalars(stmt).all())


def get_store(db: Session, store_id: int) -> Store | None:
    return db.get(Store, store_id)


def update_store(db: Session, obj: Store, payload: StoreUpdate) -> Store:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_store(db: Session, obj: Store) -> None:
    db.delete(obj)
    db.commit()
