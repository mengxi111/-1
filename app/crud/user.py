from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


DELETED_USER_STATUS = -1


def create_user(db: Session, payload: UserCreate) -> User:
    data = payload.model_dump()
    raw_password = data.pop("password", None)
    if raw_password:
        data["password_hash"] = hash_password(raw_password)
    obj = User(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    keyword: str | None = None,
    name: str | None = None,
    phone: str | None = None,
    role: str | None = None,
    status: int | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    include_deleted: bool = False,
) -> list[User]:
    stmt = select(User)
    if status is None and not include_deleted:
        stmt = stmt.where(User.status != DELETED_USER_STATUS)
    elif status is not None:
        stmt = stmt.where(User.status == status)

    if keyword:
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                User.phone.ilike(pattern),
                User.name.ilike(pattern),
                User.email.ilike(pattern),
            )
        )
    if name:
        stmt = stmt.where(User.name.ilike(f"%{name.strip()}%"))
    if phone:
        stmt = stmt.where(User.phone.ilike(f"%{phone.strip()}%"))
    if role:
        stmt = stmt.where(User.role == role)
    if created_from is not None:
        stmt = stmt.where(User.created_at >= created_from)
    if created_to is not None:
        stmt = stmt.where(User.created_at <= created_to)

    stmt = stmt.offset(skip).limit(limit).order_by(User.id)
    return list(db.scalars(stmt).all())


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_phone(db: Session, phone: str) -> User | None:
    stmt = select(User).where(User.phone == phone).limit(1)
    return db.scalars(stmt).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email).limit(1)
    return db.scalars(stmt).first()


def get_user_by_account(db: Session, account: str) -> User | None:
    stmt = select(User).where((User.phone == account) | (User.email == account) | (User.name == account)).limit(1)
    return db.scalars(stmt).first()


def update_user(db: Session, obj: User, payload: UserUpdate) -> User:
    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        password = data.pop("password")
        obj.password_hash = hash_password(password) if password else None
    for field, value in data.items():
        setattr(obj, field, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_user(db: Session, obj: User) -> None:
    now_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    obj.status = DELETED_USER_STATUS
    if obj.phone:
        obj.phone = f"deleted_{obj.id}_{now_suffix}_{obj.phone}"[:20]
    if obj.email:
        obj.email = f"deleted_{obj.id}_{now_suffix}@deleted.local"[:255]
    if "[已删除]" not in obj.name:
        obj.name = f"{obj.name}[已删除]"[:50]
    db.add(obj)
    db.commit()
