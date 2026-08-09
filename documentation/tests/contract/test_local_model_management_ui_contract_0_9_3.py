from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"
CONTRACT_PATH = DOCUMENTATION_ROOT / "config/local-model-management-ui-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_m10_03a_keeps_model_lifecycle_separate_from_chat_enablement() -> None:
    contract = _contract()
    script = (DOCUMENTATION_ROOT / "assets/theme/bpm-docs-model-manager.js").read_text(
        encoding="utf-8"
    )
    builder = (DOCUMENTATION_ROOT / "buildlib/portal.py").read_text(encoding="utf-8")
    api = (ROOT / "app/api/local_model.py").read_text(encoding="utf-8")

    assert contract["backlog_item"] == "BPM093-M10-03A"
    assert (
        contract["status"]
        == "implemented-explicit-release-model-management-with-reviewed-post-install-activation"
    )
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert contract["ui_boundary"]["initial_page_load"].startswith("The only enabled control")
    assert "documentation-assistant/chat" not in api
    assert "documentation-assistant/status" not in api
    assert "EventSource" not in script
    assert "innerHTML" not in script
    assert "data-local-model-manager" not in builder
    assert "MODEL_MANAGER_SCRIPT" in builder
    assert 'manager.inspect.addEventListener("click", () => manager.inspectStatus(false))' in script
    assert "window.setTimeout(() => manager.inspectStatus(true), pollIntervalMs)" in script
    assert "window.confirm(messages.model.confirm_install)" in script
    assert "window.confirm(messages.model.remove_confirm)" in script
    assert (
        'operation.state === "failed" ? messages.actions.retry : messages.actions.install' in script
    )


def test_m10_03a_api_has_bounded_same_origin_and_explicit_action_gates() -> None:
    contract = _contract()
    api = (ROOT / "app/api/local_model.py").read_text(encoding="utf-8")
    controller = (ROOT / "app/ai/model_management.py").read_text(encoding="utf-8")
    installer = (ROOT / "app/ai/model_installation.py").read_text(encoding="utf-8")

    assert contract["api_boundary"]["base_path"] == "/api/local-model"
    for required in (
        "stream = request.stream()",
        "chunk = await anext(stream)",
        "MAX_REQUEST_BYTES = min(1024, ASSISTANT_MAX_REQUEST_BYTES)",
        'ConfigDict(extra="forbid", strict=True)',
        "_sessions.consume_and_rotate",
        "SESSION_COOKIE",
        'samesite="strict"',
        '@router.post("/install")',
        '@router.post("/verify")',
        '@router.post("/remove")',
        '@router.post("/cancel")',
    ):
        assert required in api
    assert "threading.Thread(" in controller
    assert "cancel_requested" in controller
    assert "InstallationCancelled" in controller
    assert "after_install" in controller
    assert "documentation_assistant_activation" in api
    assert "_raise_if_cancelled(cancelled)" in installer
    assert "document." not in controller
    assert "prompt" not in api
