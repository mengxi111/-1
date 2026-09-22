from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis import Redis
from sqlalchemy.orm import Session

from app.core.redis_client import create_redis_client
from app.core.security import decode_access_token
from app.crud.user import get_user
from app.db.session import get_db


VALID_ROLES = {"student", "staff", "admin", "super_admin"}
ADMIN_PORTAL_ROLES = {"staff", "admin", "super_admin"}
ADMIN_WRITE_ROLES = {"admin", "super_admin"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
oauth2_scheme_strict = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


@dataclass
class CurrentAuthUser:
    id: int
    role: str
    name: str
    phone: str | None
    email: str | None


def get_current_user_id(x_user_id: int | None = Header(default=None, alias="X-User-Id")) -> int | None:
    return x_user_id


def get_current_user_role(x_user_role: str = Header(default="student", alias="X-User-Role")) -> str:
    return x_user_role.lower()


def _from_token(db: Session, token: str) -> CurrentAuthUser:
    payload = decode_access_token(token)
    subject = payload.get("sub")
    role = (payload.get("role") or "").lower()
    if not subject or role not in VALID_ROLES:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态无效，请重新登录")
    try:
        user_id = int(subject)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态无效，请重新登录") from exc

    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已删除")
    if user.status != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")

    return CurrentAuthUser(id=user.id, role=user.role, name=user.name, phone=user.phone, email=user.email)


def _from_legacy_headers(
    db: Session,
    x_user_id: int | None,
    x_user_role: str,
) -> CurrentAuthUser:
    if x_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录后访问")
    user = get_user(db, x_user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    role = x_user_role.lower()
    if role not in VALID_ROLES:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户角色无效")
    return CurrentAuthUser(id=user.id, role=role, name=user.name, phone=user.phone, email=user.email)


def get_current_auth_user(
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
    x_user_role: str = Header(default="student", alias="X-User-Role"),
) -> CurrentAuthUser:
    # Prefer JWT bearer token. Keep header fallback for backward compatibility.
    if token:
        try:
            return _from_token(db, token)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return _from_legacy_headers(db, x_user_id, x_user_role)


def require_login_user(user: CurrentAuthUser = Depends(get_current_auth_user)) -> CurrentAuthUser:
    return user


def require_login_token_user(
    user: CurrentAuthUser = Depends(get_current_auth_user),
    token: str | None = Depends(oauth2_scheme),
) -> CurrentAuthUser:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要提供登录令牌")
    return user


def require_admin(user: CurrentAuthUser = Depends(get_current_auth_user)) -> CurrentAuthUser:
    if user.role not in ADMIN_WRITE_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可执行该操作")
    return user


def get_current_token_user(
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme_strict),
) -> CurrentAuthUser:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期")
    try:
        return _from_token(db, token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态无效，请重新登录") from exc


def require_student_token_user(user: CurrentAuthUser = Depends(get_current_token_user)) -> CurrentAuthUser:
    if user.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅学生可访问该接口")
    return user


def require_admin_token_user(user: CurrentAuthUser = Depends(get_current_token_user)) -> CurrentAuthUser:
    if user.role not in ADMIN_WRITE_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可执行该操作")
    return user


def require_admin_portal_token_user(user: CurrentAuthUser = Depends(get_current_token_user)) -> CurrentAuthUser:
    if user.role not in ADMIN_PORTAL_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅员工或管理员可访问该接口")
    return user


def require_super_admin_token_user(user: CurrentAuthUser = Depends(get_current_token_user)) -> CurrentAuthUser:
    if user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅超级管理员可执行该操作")
    return user


def get_redis_client() -> Redis:
    # Create a fresh client for request handling to avoid stale connection pools
    # under the Windows reload process model.
    return create_redis_client()
