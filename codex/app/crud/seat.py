from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.seat import Seat
from app.schemas.seat import SeatCreate, SeatUpdate


def create_seat(db: Session, payload: SeatCreate) -> Seat:
    obj = Seat(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_seats(db: Session, skip: int = 0, limit: int = 100, store_id: int | None = None) -> list[Seat]:
    stmt = select(Seat)
    if store_id is not None:
        stmt = stmt.where(Seat.store_id == store_id)
    stmt = stmt.offset(skip).limit(limit).order_by(Seat.id)
    return list(db.scalars(stmt).all())


def get_seat(db: Session, seat_id: int) -> Seat | None:
    return db.get(Seat, seat_id)


def update_seat(db: Session, obj: Seat, payload: SeatUpdate) -> Seat:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_seat(db: Session, obj: Seat) -> None:
    db.delete(obj)
    db.commit()
