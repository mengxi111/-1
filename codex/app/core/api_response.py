from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def success_response(data: Any = None, message: str = "操作成功", code: int = 200) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": data,
    }


def error_response(
    status_code: int,
    message: str,
    *,
    code: int | None = None,
    data: Any = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "code": status_code if code is None else code,
            "message": message,
            "data": data,
        },
    )


def _extract_message(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        message = detail.get("message")
        if isinstance(message, str) and message:
            return message
    return "请求失败"


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        payload = {
            "code": exc.detail.get("code", exc.status_code),
            "message": exc.detail.get("message", _extract_message(exc.detail)),
            "data": exc.detail.get("data"),
        }
    else:
        payload = {
            "code": exc.status_code,
            "message": _extract_message(exc.detail),
            "data": None,
        }
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    message = "参数校验失败"
    if errors:
        first_error = errors[0]
        loc_items = [str(item) for item in first_error.get("loc", []) if item not in {"body", "query", "path"}]
        field_name = ".".join(loc_items) if loc_items else "参数"
        if first_error.get("type") == "missing":
            message = f"{field_name}为必填项"
        else:
            message = f"{field_name}参数校验失败"
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": message,
            "data": {"errors": errors},
        },
    )
