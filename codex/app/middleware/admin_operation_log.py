from __future__ import annotations

import logging
from time import perf_counter

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_access_token
from app.crud.admin_operation_log import create_admin_operation_log
from app.db.session import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

ADMIN_API_PREFIX = "/api/admin"
CONTENT_MAX_LEN = 2000



def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"



def _module_from_path(path: str) -> str:
    parts = [part for part in path.split("/") if part]
    if len(parts) >= 3:
        return parts[2]
    return "admin"



def _parse_operator(db, request: Request) -> tuple[int | None, str | None, str | None]:
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return None, None, None

    token = authorization[7:].strip()
    if not token:
        return None, None, None

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        role = payload.get("role")
        if subject is None:
            return None, None, role
        user_id = int(subject)
    except Exception:
        return None, None, None

    user = db.get(User, user_id)
    if user is None:
        return user_id, None, role
    return user_id, user.name, user.role


class AdminOperationLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method.upper()
        if not path.startswith(ADMIN_API_PREFIX) or method == "OPTIONS":
            return await call_next(request)

        body_preview = ""
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            try:
                body_raw = await request.body()
                if body_raw:
                    body_preview = body_raw.decode("utf-8", errors="ignore")
            except Exception:
                body_preview = ""

        query_text = request.url.query
        start = perf_counter()
        status_code = 500
        response = None
        raised_error: Exception | None = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            raised_error = exc
            raise
        finally:
            elapsed_ms = int((perf_counter() - start) * 1000)
            db = SessionLocal()
            try:
                operator_id, operator_name, operator_role = _parse_operator(db, request)
                module = _module_from_path(path)
                content = (
                    f"方法={method}; 路径={path}; 查询参数={query_text or '-'}; "
                    f"请求体={body_preview or '-'}; 耗时={elapsed_ms}ms"
                )
                if len(content) > CONTENT_MAX_LEN:
                    content = content[: CONTENT_MAX_LEN - 3] + "..."

                if raised_error is not None:
                    content = f"{content}; 异常={type(raised_error).__name__}"

                create_admin_operation_log(
                    db,
                    operator_id=operator_id,
                    operator_name=operator_name,
                    operator_role=operator_role,
                    ip=_client_ip(request),
                    module=module,
                    request_method=method,
                    request_path=path,
                    status_code=status_code,
                    content=content,
                )
            except Exception:
                db.rollback()
                logger.exception("写入管理员操作日志失败")
            finally:
                db.close()
