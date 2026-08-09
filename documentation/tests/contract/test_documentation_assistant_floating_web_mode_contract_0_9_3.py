from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"
CONTRACT_PATH = (
    DOCUMENTATION_ROOT / "config/documentation-assistant-floating-web-mode-contract-0.9.3.json"
)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_m12b_06_keeps_its_server_side_boundary_without_a_release_ui_path() -> None:
    contract = _contract()
    conversation = (
        DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-conversation.js"
    ).read_text(encoding="utf-8")
    transport = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-transport.js").read_text(
        encoding="utf-8"
    )

    assert contract["tab_and_locale_state"]["new_tab_default"] == "off"
    assert contract["tab_and_locale_state"]["page_load_requests"] == 0
    assert contract["transport"]["crafted_web_mode_authority"] is False
    assert contract["boundaries"]["direct_brave_browser_call"] is False
    for required in (
        "window.crypto.getRandomValues",
        "web_enabled: false",
        "setWebEnabled",
        "webState",
    ):
        assert required in conversation
    for required in (
        "tab_id: context.tabId",
        'web_mode: "local_only"',
        "appendExternalClaims",
        "approvedExternalUrl",
        'link.rel = "noopener noreferrer"',
        'link.target = "_blank"',
    ):
        assert required in transport
    for forbidden in ("requestWebMode", "loadWebMode", "changeWebMode", "request_web"):
        assert forbidden not in transport
    for forbidden in ("localStorage", "IndexedDB", "innerHTML", "insertAdjacentHTML"):
        assert forbidden not in conversation
        assert forbidden not in transport
