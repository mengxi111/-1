from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.crud.refresh_token import create_refresh_token_record, get_refresh_token_by_jti, revoke_refresh_token
from app.crud.user import get_user, get_user_by_account, get_user_by_email, get_user_by_phone
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth_api import AuthUser, LoginIn, LogoutIn, LogoutOut, RefreshIn, RegisterIn, TokenPairOut

router = APIRouter()


def _to_auth_user(user: User) -> AuthUser:
    return AuthUser(
        id=user.id,
        role=user.role,
        nickname=user.name,
        phone=user.phone,
        email=user.email,
    )


def _issue_token_pair(db: Session, user: User) -> TokenPairOut:
    access_token = create_access_token(str(user.id), user.role)
    refresh_token, jti, refresh_expire_at = create_refresh_token(str(user.id), user.role)
    create_refresh_token_record(
        db=db,
        user_id=user.id,
        jti=jti,
        token_hash=hash_token(refresh_token),
        expires_at=refresh_expire_at,
    )
    return TokenPairOut(
        access_token=access_token,
        refresh_token=refresh_token,
        access_expires_in=settings.access_token_expire_minutes * 60,
        refresh_expires_at=refresh_expire_at,
        user=_to_auth_user(user),
    )


@router.post("/register", response_model=TokenPairOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> TokenPairOut:
    if payload.phone:
        if get_user_by_phone(db, payload.phone) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该手机号已注册")
    if payload.email:
        if get_user_by_email(db, payload.email) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该邮箱已注册")

    user = User(
        phone=payload.phone,
        email=payload.email,
        name=payload.nickname,
        role="student",
        status=1,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="账号已存在，请更换后重试") from exc
    db.refresh(user)
    return _issue_token_pair(db, user)


@router.post("/login", response_model=TokenPairOut)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> TokenPairOut:
    user = get_user_by_account(db, payload.account)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
    if user.status != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")
    return _issue_token_pair(db, user)


@router.post("/refresh", response_model=TokenPairOut)
def refresh(payload: RefreshIn, db: Session = Depends(get_db)) -> TokenPairOut:
    try:
        token_payload = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌无效，请重新登录") from exc

    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌类型错误")

    subject = token_payload.get("sub")
    jti = token_payload.get("jti")
    if not subject or not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌内容无效")
    try:
        user_id = int(subject)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌内容无效") from exc

    token_record = get_refresh_token_by_jti(db, jti)
    if token_record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌已失效，请重新登录")

    now = datetime.now(timezone.utc)
    if token_record.revoked_at is not None or token_record.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌已过期，请重新登录")
    if token_record.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌无效，请重新登录")
    if token_record.token_hash != hash_token(payload.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌无效，请重新登录")

    user = get_user(db, user_id)
    if user is None or user.status != 1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已被禁用")

    revoke_refresh_token(db, token_record)
    return _issue_token_pair(db, user)


@router.post("/logout", response_model=LogoutOut)
def logout(payload: LogoutIn, db: Session = Depends(get_db)) -> LogoutOut:
    try:
        token_payload = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌无效，请重新登录") from exc

    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌类型错误")

    jti = token_payload.get("jti")
    if not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌内容无效")
    token_record = get_refresh_token_by_jti(db, jti)
    if token_record is None:
        return LogoutOut(success=True)
    if token_record.token_hash != hash_token(payload.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌无效，请重新登录")

    revoke_refresh_token(db, token_record)
    return LogoutOut(success=True)
