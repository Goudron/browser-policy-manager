from __future__ import annotations

import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

import app.ai.model_management as management
from app.ai.model_installation import (
    InstallationCancelled,
    InstallationResult,
    ModelInstallationError,
    VerificationResult,
)
from app.ai.model_management import ModelManagementController


class _Installer:
    model_dir = Path("/nonexistent/bpm-model-management-test")

    def disclosure(self, locale: str) -> dict[str, str]:
        assert locale == "en"
        return {"model_id": "qwen3-0.6b-q8_0-official-gguf"}

    def install(self, **_kwargs: object) -> InstallationResult:
        return InstallationResult(
            state="installed",
            model_id="qwen3-0.6b-q8_0-official-gguf",
            byte_count=1,
            sha256="a" * 64,
        )


def _wait_for_completion(
    controller: ModelManagementController, session_id: str, completed: threading.Event
) -> dict[str, object]:
    assert completed.wait(timeout=1)
    deadline = time.monotonic() + 1
    while time.monotonic() < deadline:
        snapshot = controller.status(locale="en", session_id=session_id)
        assert isinstance(snapshot["operation"], dict)
        if snapshot["operation"].get("state") != "running":
            return snapshot["operation"]
        time.sleep(0.001)
    raise AssertionError("model operation did not complete")


def test_install_runs_the_explicit_post_verification_activation_before_ready() -> None:
    controller = ModelManagementController(_Installer())
    completed = threading.Event()
    session_id = "session"
    result = controller.start_install(
        locale="en",
        session_id=session_id,
        after_install=lambda: completed.set() or True,
    )

    assert result["accepted"] is True
    operation = _wait_for_completion(controller, session_id, completed)
    assert operation["state"] == "installed"
    assert operation["phase"] == "completed"
    assert controller.status(locale="en", session_id=session_id)["verification"] == {
        "state": "installed",
        "verified": True,
        "reason_code": "verified",
    }


def test_failed_post_verification_activation_keeps_the_verified_model() -> None:
    controller = ModelManagementController(_Installer())
    completed = threading.Event()
    session_id = "session"
    result = controller.start_install(
        locale="en",
        session_id=session_id,
        after_install=lambda: completed.set() or False,
    )

    assert result["accepted"] is True
    operation = _wait_for_completion(controller, session_id, completed)
    assert operation["state"] == "failed"
    assert operation["reason_code"] == "assistant_preparation_failed"
    assert controller.status(locale="en", session_id=session_id)["verification"]["verified"] is True


def test_controller_status_starts_cancellation_and_visibility_are_session_bounded(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    class Installer(_Installer):
        model_dir = Path("/nonexistent/model")

        def verify(self) -> VerificationResult:
            return VerificationResult("installed", True, "verified", "model", 1, "hash")

        def remove(self, **_: object) -> InstallationResult:
            return InstallationResult("removed", "model", 0, "hash")

    installer = Installer()
    controller = ModelManagementController(installer)  # type: ignore[arg-type]
    assert controller.status(locale="en", session_id="one")["operation"] == {"state": "idle"}

    class Thread:
        def __init__(self, *, target, args, **_: object) -> None:  # type: ignore[no-untyped-def]
            self.target = target
            self.args = args

        def start(self) -> None:
            return None

    monkeypatch.setattr(management.threading, "Thread", Thread)
    installed = controller.start_install(locale="en", session_id="one")
    operation_id = installed["operation"]["operation_id"]
    assert controller.status(locale="en", session_id="two")["operation"] == {"state": "running", "busy": True}
    assert controller.start_verify(locale="en", session_id="two") == {
        "accepted": False,
        "reason_code": "model_operation_busy",
    }
    assert controller.cancel(session_id="two", operation_id=operation_id) == {
        "accepted": False,
        "reason_code": "model_operation_not_cancellable",
    }
    assert controller.cancel(session_id="one", operation_id=operation_id)["accepted"] is True
    operation = controller._operation
    assert operation is not None and operation.cancel_requested.is_set()
    controller._run_operation(operation)
    assert controller.status(locale="en", session_id="one")["operation"]["state"] == "installed"

    verified = controller.start_verify(locale="en", session_id="one")
    verify_operation = controller._operation
    assert verified["accepted"] is True and verify_operation is not None
    assert controller.cancel(session_id="one", operation_id=verify_operation.operation_id)["accepted"] is False
    controller._run_operation(verify_operation)
    assert controller.status(locale="en", session_id="one")["operation"]["state"] == "installed"
    removed = controller.start_remove(locale="en", session_id="one")
    remove_operation = controller._operation
    assert removed["accepted"] is True and remove_operation is not None
    controller._run_operation(remove_operation)
    assert controller.status(locale="en", session_id="one")["verification"]["state"] == "not-installed"


def test_controller_failure_progress_and_snapshot_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    class Installer(_Installer):
        model_dir = Path("/nonexistent/model")

        def install(self, **_: object) -> InstallationResult:
            raise InstallationCancelled("cancelled")

        def verify(self) -> VerificationResult:
            raise ModelInstallationError("verify_failed")

        def remove(self, **_: object) -> InstallationResult:
            raise RuntimeError("unexpected")

    controller = ModelManagementController(Installer())  # type: ignore[arg-type]
    for kind, expected in (
        ("install", "cancelled"),
        ("verify", "failed"),
        ("remove", "failed"),
    ):
        operation = management._Operation("id", "session", kind)  # type: ignore[arg-type]
        controller._operation = operation
        controller._run_operation(operation)
        assert operation.state == expected
    operation = management._Operation("progress", "session", "install")
    controller._operation = operation
    controller._record_progress(
        operation, SimpleNamespace(downloaded_bytes=-1, total_bytes=5)
    )
    assert operation.downloaded_bytes == 0 and operation.total_bytes == 5
    controller._record_progress(
        operation, SimpleNamespace(downloaded_bytes=10, total_bytes=5)
    )
    assert operation.downloaded_bytes == 5
    controller._set_phase(operation, "preparing")
    assert operation.phase == "preparing"
    controller._finish(operation, state="failed", reason_code="failed")
    assert operation.phase == "failed" and operation.after_install is None
    detached = management._Operation("detached", "session", "install")
    controller._record_progress(detached, SimpleNamespace(downloaded_bytes=1, total_bytes=1))
    controller._set_phase(detached, "ignored")
    controller._finish(detached, state="installed", reason_code="ignored")
    assert detached.phase == "" and detached.state == "running"
    assert controller._operation_payload(management._Operation("id", "s", "verify"))["cancellable"] is False

    class Present:
        exists = lambda self: True  # noqa: E731
        is_symlink = lambda self: False  # noqa: E731

    controller._last_verification = None
    controller._installer = SimpleNamespace(model_dir=Present())
    assert controller._verification_snapshot_locked()["state"] == "present-unverified"


def test_controller_from_settings_constructs_the_pinned_installer(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class Installer:
        def __init__(self, root: Path, **kwargs: object) -> None:
            captured["root"] = root
            captured.update(kwargs)

    monkeypatch.setattr(management, "get_settings", lambda: SimpleNamespace(DATA_DIR=Path("/data"), AI_MODEL_DOWNLOAD_TIMEOUT_SECONDS=9))
    monkeypatch.setattr(management, "ModelInstaller", Installer)
    assert isinstance(ModelManagementController.from_settings(), ModelManagementController)
    assert captured == {"root": Path("/data/ai/models"), "timeout_seconds": 9}
