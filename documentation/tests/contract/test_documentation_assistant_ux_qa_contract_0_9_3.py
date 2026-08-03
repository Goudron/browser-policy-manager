from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "documentation"
pytestmark = pytest.mark.docs_contract


def test_m10_07_closes_static_six_locale_ux_matrix_without_claiming_chat_enablement() -> None:
    contract = json.loads((DOCS / "config/documentation-assistant-ux-qa-0.9.3.json").read_text(encoding="utf-8"))
    builder = (DOCS / "tools/build_docs.py").read_text(encoding="utf-8")
    assert contract["backlog_item"] == "BPM093-M10-07"
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert "chat route" in contract["current_truth_boundary"]
    for required in ("data-documentation-assistant-widget", "data-assistant-toggle", "data-assistant-panel", "data-assistant-question", "data-assistant-install", "disabled aria-disabled=\"true\""):
        assert required in builder
    for script in ("bpm-docs-assistant-renderer.js", "bpm-docs-assistant-state-machine.js"):
        source = (DOCS / "assets/theme" / script).read_text(encoding="utf-8")
        assert "fetch(" not in source
        assert "innerHTML" not in source
