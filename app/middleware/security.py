# app/middleware/security.py
from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    """Middleware that adds basic HTTP security headers.

    Notes:
        - CSP is permissive enough for CDN-hosted scripts/styles (e.g., Monaco/Tailwind).
          When moving to self-hosted static assets, CSP can be tightened.
        - HSTS is commented out intentionally; enable only in HTTPS environments.
    """

    def __init__(self, app: ASGIApp, *, csp: str | None = None) -> None:
        self.app = app
        # Default CSP allows local and CDN content; adjust as needed.
        self.csp = csp or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "worker-src 'self' blob:; "
            "child-src 'self' blob:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                self._append_if_missing(headers, b"x-frame-options", b"DENY")
                self._append_if_missing(headers, b"x-xss-protection", b"0")
                self._append_if_missing(headers, b"x-content-type-options", b"nosniff")
                self._append_if_missing(headers, b"referrer-policy", b"no-referrer")
                self._append_if_missing(
                    headers,
                    b"permissions-policy",
                    b"geolocation=(), microphone=(), camera=()",
                )
                self._append_if_missing(
                    headers,
                    b"content-security-policy",
                    self.csp.encode("utf-8"),
                )
            await send(message)

        await self.app(scope, receive, send_with_security_headers)

    @staticmethod
    def _append_if_missing(
        headers: list[tuple[bytes, bytes]],
        name: bytes,
        value: bytes,
    ) -> None:
        normalized = name.lower()
        if any(header_name.lower() == normalized for header_name, _ in headers):
            return
        headers.append((name, value))
