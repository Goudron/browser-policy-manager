from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"
CONTRACT_PATH = DOCUMENTATION_ROOT / "config/documentation-assistant-web-mode-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_m10_06_renderer_is_retained_but_not_included_in_the_m13_release_ui() -> None:
    contract = _contract()
    renderer = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-web-mode.js").read_text(
        encoding="utf-8"
    )
    builder = (DOCUMENTATION_ROOT / "tools/build_docs.py").read_text(encoding="utf-8")

    assert contract["backlog_item"] == "BPM093-M10-06"
    assert contract["status"] == "historical-consent-renderer-superseded-by-m12b-06-reader-switch"
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert contract["release_amendment"]["owner"] == "BPM093-M12B-06"
    assert contract["input_boundary"]["exact_snapshot_fields"] == [
        "api_version",
        "available",
        "enabled",
        "locale",
        "reason_code",
        "state_epoch",
    ]
    assert contract["boundaries"] == {
        "page_load": (
            "The helper only registers validation/render functions and performs no fetch, status poll, provider request or DOM mutation on its own."
        ),
        "provider_request": False,
        "ordinary_search_changed": False,
        "local_or_session_storage_access": False,
    }
    for required in (
        "validSnapshot(snapshot, locale)",
        "!snapshot.enabled || snapshot.available",
        "toggle.checked = snapshot.enabled",
        "toggle.disabled = !snapshot.available",
        'toggle.setAttribute("aria-disabled"',
        "BPMDocumentationAssistantWebMode",
    ):
        assert required in renderer
    for forbidden in (
        "fetch(",
        "EventSource",
        "setTimeout(",
        "setInterval(",
        "innerHTML",
        "sessionStorage",
        "localStorage",
    ):
        assert forbidden not in renderer
    assert "ASSISTANT_WEB_MODE_SCRIPT" not in builder
    assert "data-assistant-web-toggle" not in builder


def test_m12b_06_has_locale_owned_short_switch_copy() -> None:
    from documentation.tools import build_docs

    labels = {
        "en": "External sources",
        "ru": "Внешние источники",
        "de": "Externe Quellen",
        "zh-CN": "外部来源",
        "fr": "Sources externes",
        "es-ES": "Fuentes externas",
    }
    assert {
        locale: build_docs.SHELL_LABELS[locale]["assistant_external_sources"]
        for locale in build_docs.LOCALES
    } == labels
