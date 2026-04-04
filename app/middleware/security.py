# app/middleware/security.py
from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    """Middleware that adds basic HTTP security headers.

    Notes:
        - CSP is limited to strict self-hosted assets across the whole app.
        - Script execution is limited to self-hosted assets; `/profiles`
          no longer relies on inline executable bootstrapping or Monaco's AMD loader.
        - HSTS is commented out intentionally; enable only in HTTPS environments.
    """

    def __init__(self, app: ASGIApp, *, csp: str | None = None) -> None:
        self.app = app
        self.csp = csp or (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "worker-src 'self'; "
            "child-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        self.profiles_csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "worker-src 'self'; "
            "child-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        csp_value = self.profiles_csp if path == "/profiles" else self.csp

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
                    csp_value.encode("utf-8"),
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
