from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

SUPPORTED = {"en", "ru"}


class LocaleMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        lang = request.query_params.get("lang") or request.cookies.get("lang") or "en"
        if lang not in SUPPORTED:
            lang = "en"
        request.state.lang = lang
        response: Response = await call_next(request)
        if "lang" in request.query_params:
            response.set_cookie(
                "lang",
                lang,
                max_age=60 * 60 * 24 * 365,
                httponly=False,
                samesite="lax",
            )
        return response
