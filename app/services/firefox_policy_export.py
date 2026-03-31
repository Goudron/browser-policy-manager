from __future__ import annotations

from typing import Any


def render_firefox_policies_document(flags: dict[str, Any] | None) -> dict[str, Any]:
    """Build the canonical Firefox enterprise policies document."""
    return {"policies": dict(flags or {})}
