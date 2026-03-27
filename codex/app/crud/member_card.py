from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.member_card import MemberCard
from app.schemas.member_card import MemberCardCreate, MemberCardUpdate


def create_member_card(db: Session, payload: MemberCardCreate) -> MemberCard:
    obj = MemberCard(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_member_cards(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
) -> list[MemberCard]:
    stmt = select(MemberCard)
    if user_id is not None:
        stmt = stmt.where(MemberCard.user_id == user_id)
    stmt = stmt.offset(skip).limit(limit).order_by(MemberCard.id)
    return list(db.scalars(stmt).all())


def get_member_card(db: Session, card_id: int) -> MemberCard | None:
    return db.get(MemberCard, card_id)


def update_member_card(db: Session, obj: MemberCard, payload: MemberCardUpdate) -> MemberCard:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_member_card(db: Session, obj: MemberCard) -> None:
    db.delete(obj)
    db.commit()


def renew_member_card(
    db: Session,
    obj: MemberCard,
    add_minutes: int = 0,
    add_times: int = 0,
    extend_days: int = 0,
) -> MemberCard:
    obj.balance_minutes += add_minutes
    obj.balance_times += add_times
    if extend_days > 0:
        if obj.expire_at is None:
            obj.expire_at = date.today() + timedelta(days=extend_days)
        else:
            obj.expire_at = obj.expire_at + timedelta(days=extend_days)
    obj.status = "active"
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def set_member_card_frozen(db: Session, obj: MemberCard, frozen: bool) -> MemberCard:
    obj.status = "disabled" if frozen else "active"
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
