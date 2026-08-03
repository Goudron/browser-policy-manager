"""Bounded, explicit release-UI lifecycle controller for the selected local model.

It owns no chat, worker or retrieval capability.  The controller only bridges a deliberate model
installation UI to the existing M6 checksum-verified installer, retaining minimal in-memory progress
for one owner session at a time.
"""

from __future__ import annotations

import secrets
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from app.ai.model_installation import (
    InstallationCancelled,
    InstallationResult,
    ModelInstallationError,
    ModelInstaller,
    VerificationResult,
)
from app.core.config import get_settings

OperationKind = Literal["install", "verify", "remove"]
OperationState = Literal["idle", "running", "installed", "removed", "cancelled", "failed"]


@dataclass
class _Operation:
    operation_id: str
    owner_session_id: str
    kind: OperationKind
    state: OperationState = "running"
    cancel_requested: threading.Event = field(default_factory=threading.Event)
    downloaded_bytes: int = 0
    total_bytes: int = 0
    reason_code: str = ""
    phase: str = ""
    after_install: Callable[[], bool] | None = None


class ModelManagementController:
    """Run at most one explicit selected-artifact operation without starting chat infrastructure."""

    def __init__(self, installer: ModelInstaller) -> None:
        self._installer = installer
        self._lock = threading.RLock()
        self._operation: _Operation | None = None
        self._last_verification: VerificationResult | None = None

    @classmethod
    def from_settings(cls) -> ModelManagementController:
        settings = get_settings()
        return cls(
            ModelInstaller(
                Path(settings.DATA_DIR) / "ai" / "models",
                timeout_seconds=settings.AI_MODEL_DOWNLOAD_TIMEOUT_SECONDS,
            )
        )

    def status(self, *, locale: str, session_id: str) -> dict[str, Any]:
        """Return disclosure plus bounded, non-sensitive operation state without verification I/O."""

        disclosure = self._installer.disclosure(locale)
        with self._lock:
            operation = self._operation_snapshot_locked(session_id)
            verification = self._verification_snapshot_locked()
        return {
            "api_version": 1,
            "disclosure": disclosure,
            "verification": verification,
            "operation": operation,
            "lexical_search_ready": True,
        }

    def start_install(
        self,
        *,
        locale: str,
        session_id: str,
        after_install: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        self._installer.disclosure(locale)
        return self._start(
            session_id=session_id,
            kind="install",
            after_install=after_install,
        )

    def start_verify(self, *, locale: str, session_id: str) -> dict[str, Any]:
        self._installer.disclosure(locale)
        return self._start(session_id=session_id, kind="verify")

    def start_remove(self, *, locale: str, session_id: str) -> dict[str, Any]:
        self._installer.disclosure(locale)
        return self._start(session_id=session_id, kind="remove")

    def cancel(self, *, session_id: str, operation_id: str) -> dict[str, Any]:
        with self._lock:
            operation = self._operation
            if (
                operation is None
                or operation.operation_id != operation_id
                or operation.owner_session_id != session_id
                or operation.state != "running"
            ):
                return {"accepted": False, "reason_code": "model_operation_not_cancellable"}
            if operation.kind != "install":
                return {"accepted": False, "reason_code": "model_operation_not_cancellable"}
            operation.cancel_requested.set()
            return {"accepted": True, "reason_code": "model_cancellation_requested"}

    def _start(
        self,
        *,
        session_id: str,
        kind: OperationKind,
        after_install: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            if self._operation is not None and self._operation.state == "running":
                return {"accepted": False, "reason_code": "model_operation_busy"}
            operation = _Operation(
                operation_id=secrets.token_urlsafe(18),
                owner_session_id=session_id,
                kind=kind,
                phase="downloading" if kind == "install" else "verifying" if kind == "verify" else "",
                after_install=after_install,
            )
            self._operation = operation
        thread = threading.Thread(
            target=self._run_operation,
            args=(operation,),
            name=f"bpm-model-{kind}",
            daemon=True,
        )
        thread.start()
        return {"accepted": True, "operation": self._operation_payload(operation)}

    def _run_operation(self, operation: _Operation) -> None:
        try:
            if operation.kind == "install":
                result = self._installer.install(
                    confirmed=True,
                    progress=lambda progress: self._record_progress(operation, progress),
                    cancelled=operation.cancel_requested.is_set,
                )
                self._record_install_verification(result)
                self._set_phase(operation, "preparing_documentation")
                if operation.after_install is not None and not operation.after_install():
                    self._finish(
                        operation,
                        state="failed",
                        reason_code="assistant_preparation_failed",
                    )
                    return
                self._record_result(operation, result)
            elif operation.kind == "verify":
                self._record_verification(operation, self._installer.verify())
            else:
                self._record_result(operation, self._installer.remove(confirmed=True))
        except InstallationCancelled:
            self._finish(operation, state="cancelled", reason_code="model_operation_cancelled")
        except ModelInstallationError as error:
            self._finish(operation, state="failed", reason_code=str(error))
        except Exception:
            self._finish(operation, state="failed", reason_code="model_operation_failed")

    def _record_progress(self, operation: _Operation, progress: Any) -> None:
        with self._lock:
            if self._operation is not operation or operation.state != "running":
                return
            operation.downloaded_bytes = min(max(int(progress.downloaded_bytes), 0), int(progress.total_bytes))
            operation.total_bytes = max(int(progress.total_bytes), 0)

    def _set_phase(self, operation: _Operation, phase: str) -> None:
        with self._lock:
            if self._operation is operation and operation.state == "running":
                operation.phase = phase

    def _record_result(self, operation: _Operation, result: InstallationResult) -> None:
        state: OperationState = "installed" if result.state in {"installed", "already-installed"} else "removed"
        if state == "installed":
            self._record_install_verification(result)
        else:
            with self._lock:
                self._last_verification = VerificationResult(
                    state="not-installed",
                    verified=False,
                    reason_code="artifact_missing",
                    model_id=result.model_id,
                )
        self._finish(operation, state=state, reason_code=result.state)

    def _record_install_verification(self, result: InstallationResult) -> None:
        with self._lock:
            self._last_verification = VerificationResult(
                state="installed",
                verified=True,
                reason_code="verified",
                model_id=result.model_id,
                byte_count=result.byte_count,
                sha256=result.sha256,
            )

    def _record_verification(self, operation: _Operation, verification: VerificationResult) -> None:
        with self._lock:
            self._last_verification = verification
        self._finish(
            operation,
            state="installed" if verification.verified else "failed",
            reason_code=verification.reason_code,
        )

    def _finish(self, operation: _Operation, *, state: OperationState, reason_code: str) -> None:
        with self._lock:
            if self._operation is operation:
                operation.state = state
                operation.reason_code = reason_code
                operation.phase = "completed" if state == "installed" else "failed" if state == "failed" else ""
                operation.after_install = None

    def _verification_snapshot_locked(self) -> dict[str, Any]:
        if self._last_verification is not None:
            return {
                "state": self._last_verification.state,
                "verified": self._last_verification.verified,
                "reason_code": self._last_verification.reason_code,
            }
        if self._installer.model_dir.exists() or self._installer.model_dir.is_symlink():
            return {
                "state": "present-unverified",
                "verified": False,
                "reason_code": "explicit_verification_required",
            }
        return {"state": "not-installed", "verified": False, "reason_code": "artifact_missing"}

    def _operation_snapshot_locked(self, session_id: str) -> dict[str, Any]:
        operation = self._operation
        if operation is None:
            return {"state": "idle"}
        payload = self._operation_payload(operation)
        if operation.owner_session_id != session_id:
            return {"state": "running" if operation.state == "running" else "idle", "busy": operation.state == "running"}
        return payload

    @staticmethod
    def _operation_payload(operation: _Operation) -> dict[str, Any]:
        total = operation.total_bytes
        return {
            "operation_id": operation.operation_id,
            "kind": operation.kind,
            "state": operation.state,
            "reason_code": operation.reason_code,
            "downloaded_bytes": operation.downloaded_bytes,
            "total_bytes": total,
            "progress_percent": (operation.downloaded_bytes * 100 // total) if total else 0,
            "cancellable": operation.kind == "install" and operation.state == "running",
            "phase": operation.phase,
        }
