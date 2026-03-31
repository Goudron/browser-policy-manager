from __future__ import annotations

from typing import Any

from .general import get_general_section
from .home import get_home_section
from .privacy import get_privacy_section
from .search import get_search_section
from .sync import get_sync_section


def get_wizard_settings_catalog() -> dict[str, Any]:
    """Return the shared Firefox Settings map used by the guided wizard."""

    sections = [
        get_general_section(),
        get_home_section(),
        get_search_section(),
        get_privacy_section(),
        get_sync_section(),
    ]

    return {
        "sections": sections,
        "sections_by_id": {section["id"]: section for section in sections},
    }
