from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.services.schema_service import available_list, validate_doc


def select_version(channel: Optional[str] = None, version: Optional[str] = None) -> str:
    """
    Pick a concrete schema version string based on optional channel/version hints.

    Rules:
      - If 'version' provided -> use it verbatim.
      - Else if 'channel' provided -> pick the first available item with matching channel.
      - Else -> fallback to the first available version.
    """
    items = available_list()  # List[{"channel","version"}]

    if version:
        return version

    if channel:
        for it in items:
            if it.get("channel") == channel and "version" in it:
                return it["version"]

    # Default fallback
    if items and "version" in items[0]:
        return items[0]["version"]
    return "firefox-ESR"


def validate_payload(
    doc: Dict[str, Any],
    *,
    channel: Optional[str] = None,
    version: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate a policy document against a selected schema version.

    Ensures we pass a concrete 'str' version into validate_doc(), which expects str.
    """
    selected: str = select_version(channel=channel, version=version)
    ok, errors = validate_doc(doc, version=selected)
    return ok, errors
