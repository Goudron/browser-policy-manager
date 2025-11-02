# app/middleware/security.py
from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that adds basic HTTP security headers.

    Notes:
        - CSP is permissive enough for CDN-hosted scripts/styles (e.g., Monaco/Tailwind).
          When moving to self-hosted static assets, CSP can be tightened.
        - HSTS is commented out intentionally; enable only in HTTPS environments.
    """

    def __init__(self, app, *, csp: str | None = None) -> None:
        super().__init__(app)
        # Default CSP allows local and CDN content; adjust as needed.
        self.csp = csp or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Injects headers into the outgoing response."""
        response = await call_next(request)

        # Prevent clickjacking
        response.headers.setdefault("X-Frame-Options", "DENY")
        # Disable legacy XSS filter (modern browsers handle this automatically)
        response.headers.setdefault("X-XSS-Protection", "0")
        # Prevent MIME-type sniffing
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        # Hide referrer information
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        # Restrict browser features
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )
        # Apply Content Security Policy
        response.headers.setdefault("Content-Security-Policy", self.csp)
        # Enable this only under HTTPS deployments
        # response.headers.setdefault("Strict-Transport-Security", "max-age=15552000; includeSubDomains")

        return response
