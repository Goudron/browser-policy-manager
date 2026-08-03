"""Small, transport-neutral least-privilege controls for the local assistant."""

from __future__ import annotations

import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from urllib.parse import urlsplit

FORBIDDEN_PATH_CHARACTERS: Final[frozenset[str]] = frozenset(";&|`$><\\%:\x00")
ASSISTANT_MAX_REQUEST_BYTES: Final[int] = 48 * 1024


class LeastPrivilegeViolation(ValueError):
    """A stable reason that must stop an assistant operation before it allocates work."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def require_managed_path(
    path: Path, root: Path, *, require_regular: bool = False
) -> Path:
    """Accept only a non-symlink child path with no traversal or shell-shaped component."""

    candidate = Path(path)
    managed_root = Path(root)
    if not candidate.is_absolute() or not managed_root.is_absolute():
        raise LeastPrivilegeViolation("assistant_unsafe_execution_path")
    if managed_root.is_symlink() or (managed_root.exists() and not managed_root.is_dir()):
        raise LeastPrivilegeViolation("assistant_unsafe_execution_path")
    if _has_symlink_component(managed_root):
        raise LeastPrivilegeViolation("assistant_unsafe_execution_path")
    try:
        relative = candidate.relative_to(managed_root)
    except ValueError as error:
        raise LeastPrivilegeViolation("assistant_unsafe_execution_path") from error
    if not relative.parts or any(
        part in {"", ".", ".."}
        or any(char in part for char in FORBIDDEN_PATH_CHARACTERS)
        or any(ord(char) < 32 or ord(char) == 127 for char in part)
        for part in relative.parts
    ):
        raise LeastPrivilegeViolation("assistant_unsafe_execution_path")
    current = managed_root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise LeastPrivilegeViolation("assistant_unsafe_execution_path")
    if require_regular:
        try:
            mode = candidate.lstat().st_mode
        except FileNotFoundError as error:
            raise LeastPrivilegeViolation("assistant_unsafe_execution_path") from error
        if not stat.S_ISREG(mode) or candidate.is_symlink():
            raise LeastPrivilegeViolation("assistant_unsafe_execution_path")
    return candidate


def _has_symlink_component(path: Path) -> bool:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            return True
    return False


@dataclass(frozen=True)
class AssistantRequestMetadata:
    """The only headers a future assistant route may use for same-origin admission."""

    method: str
    origin: str | None
    host: str | None
    content_type: str | None
    sec_fetch_site: str | None = None
    content_length: int | None = None


class AssistantRequestGuard:
    """Fail closed for the future same-origin JSON assistant surface; no route is added here."""

    def __init__(self, expected_origin: str, *, maximum_bytes: int = ASSISTANT_MAX_REQUEST_BYTES) -> None:
        parsed = urlsplit(expected_origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
            or expected_origin == "*"
            or maximum_bytes < 1
        ):
            raise LeastPrivilegeViolation("assistant_invalid_origin_policy")
        self._expected_origin = expected_origin
        self._expected_host = parsed.netloc.casefold()
        self._maximum_bytes = maximum_bytes

    def require_same_origin_json(self, request: AssistantRequestMetadata) -> None:
        """Reject cross-origin, preflight, non-JSON or oversized future assistant requests."""

        if request.method != "POST":
            raise LeastPrivilegeViolation("assistant_method_not_allowed")
        if request.origin != self._expected_origin:
            raise LeastPrivilegeViolation("assistant_cross_origin")
        if request.host is None or request.host.casefold() != self._expected_host:
            raise LeastPrivilegeViolation("assistant_host_mismatch")
        if request.sec_fetch_site is not None and request.sec_fetch_site != "same-origin":
            raise LeastPrivilegeViolation("assistant_cross_origin")
        media_type = request.content_type.split(";", 1)[0].strip().casefold() if request.content_type else ""
        if media_type != "application/json":
            raise LeastPrivilegeViolation("assistant_invalid_content_type")
        if request.content_length is not None and (
            request.content_length < 0 or request.content_length > self._maximum_bytes
        ):
            raise LeastPrivilegeViolation("assistant_request_too_large")


def restricted_worker_environment() -> dict[str, str]:
    """Return the complete child environment rather than inheriting proxies or credentials."""

    return {
        "LC_ALL": "C",
        "PATH": "",
        "NO_PROXY": "*",
        "no_proxy": "*",
        "HTTP_PROXY": "",
        "HTTPS_PROXY": "",
        "ALL_PROXY": "",
    }
