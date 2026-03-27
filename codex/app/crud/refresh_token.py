from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


def create_refresh_token_record(
    db: Session,
    user_id: int,
    jti: str,
    token_hash: str,
    expires_at: datetime,
) -> RefreshToken:
    obj = RefreshToken(user_id=user_id, jti=jti, token_hash=token_hash, expires_at=expires_at)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_refresh_token_by_jti(db: Session, jti: str) -> RefreshToken | None:
    stmt = select(RefreshToken).where(RefreshToken.jti == jti).limit(1)
    return db.scalars(stmt).first()


def revoke_refresh_token(db: Session, obj: RefreshToken) -> RefreshToken:
    if obj.revoked_at is None:
        obj.revoked_at = datetime.now(timezone.utc)
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj


def revoke_refresh_token_by_jti(db: Session, jti: str) -> bool:
    token = get_refresh_token_by_jti(db, jti)
    if token is None:
        return False
    revoke_refresh_token(db, token)
    return True

