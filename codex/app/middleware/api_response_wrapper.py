from __future__ import annotations

import json

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.api_response import success_response


class ApiResponseWrapperMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path

        if not path.startswith("/api/"):
            return response

        if response.status_code >= 400:
            return response

        if response.status_code == 204:
            return JSONResponse(status_code=200, content=success_response())

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        if not body:
            return JSONResponse(status_code=response.status_code, content=success_response())

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        if isinstance(payload, dict) and {"code", "message", "data"}.issubset(payload.keys()):
            wrapped = payload
        else:
            wrapped = success_response(data=payload, code=response.status_code)

        return JSONResponse(
            status_code=response.status_code,
            content=wrapped,
            headers={k: v for k, v in response.headers.items() if k.lower() != "content-length"},
        )
