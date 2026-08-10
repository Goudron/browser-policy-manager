from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"
CONTRACT_PATH = (
    DOCUMENTATION_ROOT / "config/documentation-assistant-floating-ui-contract-0.9.3.json"
)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_m12b_01_freezes_geometry_content_order_and_short_locale_copy() -> None:
    contract = _contract()

    assert contract["collapsed"] == {
        "default": True,
        "placement": "fixed in the lower-right corner of the visible documentation viewport",
        "visible_content": (
            "Only the locale-owned assistant title is visible; icons, badges, status, explanatory prose, transcripts and controls are absent."
        ),
        "activation": (
            "The title is the localized accessible button name and toggles the expanded panel."
        ),
    }
    assert contract["expanded"]["desktop_viewport"]["minimum_inline_size"] == "33.333vw"
    assert contract["expanded"]["desktop_viewport"]["block_size"] == "50dvh"
    assert contract["expanded"]["narrow_viewport"] == {
        "breakpoint": "48rem",
        "inline_size": "calc(100vw - 2rem)",
        "block_size": "50dvh",
        "placement": "fixed lower-right overlay with a 1rem viewport inset",
    }
    assert contract["expanded"]["order"] == [
        "localized title",
        "scrollable chat transcript",
        "question composer",
        "bottom status row",
    ]
    assert contract["copy_authority"]["collapsed_titles"]["ru"] == "ИИ-помощник BPM"
    assert set(contract["copy_authority"]["collapsed_titles"]) == set(contract["locales"])
    assert contract["copy_authority"]["no_explanatory_copy"].startswith("The widget shows no")


def test_m12b_01_freezes_ready_installation_and_tab_scoped_persistence_boundaries() -> None:
    contract = _contract()

    assert contract["state_to_controls"]["ready"] == {
        "status": "ready",
        "composer": "enabled",
        "bottom_controls": ["external_sources_switch", "clear"],
        "installation_control": "absent",
    }
    assert contract["state_to_controls"]["not_ready"]["states"] == [
        "disabled",
        "not-installed",
        "downloading",
        "indexing",
        "loading",
        "cancelled",
        "degraded",
        "incompatible",
        "crashed",
    ]
    assert contract["state_to_controls"]["installation_progress"]["phases"] == [
        "downloading",
        "verifying",
        "preparing_documentation",
        "completed",
        "failed",
    ]
    persistent = contract["persistent_state"]
    assert (
        persistent["storage"]
        == "sessionStorage only, under a versioned locale-private key owned by the portal"
    )
    assert persistent["forbidden_storage"] == [
        "localStorage",
        "IndexedDB",
        "cookies",
        "server database",
        "telemetry",
        "cross-origin storage",
    ]
    assert persistent["dialogue_clear_conditions"] == [
        "explicit Clear",
        "browser-tab close",
        "locale change",
        "server-declared conversation expiry",
    ]
    assert persistent["external_sources_clear_conditions"] == [
        "explicit switch off",
        "browser-tab close",
        "locale change",
    ]
    assert contract["security_and_network"]["ordinary_search_changed"] is False
