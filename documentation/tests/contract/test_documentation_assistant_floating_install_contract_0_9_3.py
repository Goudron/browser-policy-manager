from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"

pytestmark = pytest.mark.docs_contract


def test_m12b_05_uses_only_the_existing_guarded_model_lifecycle_after_explicit_action() -> None:
    transport = (
        DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-transport.js"
    ).read_text(encoding="utf-8")
    builder = (DOCUMENTATION_ROOT / "tools/build_docs.py").read_text(encoding="utf-8")
    model_api = (ROOT / "app/api/local_model.py").read_text(encoding="utf-8")
    controller = (ROOT / "app/ai/model_management.py").read_text(encoding="utf-8")

    for required in (
        'const MODEL_API_ROOT = "/api/local-model"',
        "startInstallation",
        "modelStatus",
        "loadModelStatus",
        "MODEL_POLL_INTERVAL_MS",
        "confirm_install: true",
        "csrf_token: context.modelCsrfToken",
        "validModelStatus",
        "validModelAction",
        "installationStatus",
        "data-assistant-install",
        "assistant_installing",
        "assistant_preparing_documentation",
        "assistant_install_failed",
        "after_install",
        "documentation_assistant_activation",
    ):
        assert required in transport or required in builder or required in model_api or required in controller

    for forbidden in (
            "brave.com",
        "localStorage",
        "IndexedDB",
        "document.cookie",
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "window.confirm(",
    ):
        assert forbidden not in transport


def test_m12b_05_keeps_polling_scoped_to_an_explicit_server_owned_installation() -> None:
    transport = (
        DOCUMENTATION_ROOT / "assets/theme/bpm-docs-assistant-transport.js"
    ).read_text(encoding="utf-8")

    assert 'event.detail && event.detail.expanded' in transport
    assert 'if (operation.state === "running")' in transport
    assert "scheduleModelStatus(context)" in transport
    assert "stopModelPolling(context)" in transport
    assert 'window.setTimeout(() =>' in transport
    assert "window.clearTimeout(context.modelTimer)" in transport
    assert "No status" not in transport
