from __future__ import annotations

from pathlib import Path

import pytest

from app.ai.least_privilege import (
    ASSISTANT_MAX_REQUEST_BYTES,
    AssistantRequestGuard,
    AssistantRequestMetadata,
    LeastPrivilegeViolation,
    require_managed_path,
    restricted_worker_environment,
)
from app.ai.local_inference_worker import InferenceRequest, LocalInferenceWorker, WorkerUnavailable
from app.ai.model_installation import VerificationResult
from app.ai.runtime_installation import RUNTIME_ID, RuntimeVerification


def test_managed_execution_paths_reject_traversal_symlinks_and_shell_shaped_components(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ai"
    model = root / "models" / "model.gguf"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"model")
    outside = tmp_path / "outside.gguf"
    outside.write_bytes(b"outside")
    alias = root / "models" / "alias.gguf"
    alias.symlink_to(outside)
    real_parent = tmp_path / "real-parent"
    inherited_root = real_parent / "ai"
    inherited_model = inherited_root / "models" / "model.gguf"
    inherited_model.parent.mkdir(parents=True)
    inherited_model.write_bytes(b"model")
    alias_parent = tmp_path / "alias-parent"
    alias_parent.symlink_to(real_parent, target_is_directory=True)

    assert require_managed_path(model, root, require_regular=True) == model
    for path in (
        root / ".." / "outside.gguf",
        root / "models" / "model;curl.gguf",
        root / "models" / "%2e%2e%2fsecret.gguf",
        root / "models" / "..\\secret.gguf",
        alias_parent / "ai" / "models" / "model.gguf",
        alias,
    ):
        with pytest.raises(LeastPrivilegeViolation, match="assistant_unsafe_execution_path"):
            require_managed_path(path, root, require_regular=True)


def test_worker_rejects_paths_outside_its_owned_root_before_artifact_verification(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ai"
    model = root / "models" / "model.gguf"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"model")
    outside_runtime = tmp_path / "outside-runtime.tar.gz"
    outside_runtime.write_bytes(b"runtime")
    model_checks = 0
    runtime_checks = 0

    def verify_model() -> VerificationResult:
        nonlocal model_checks
        model_checks += 1
        return VerificationResult("installed", True, "verified", "qwen3-0.6b-q8_0-official-gguf")

    def verify_runtime() -> RuntimeVerification:
        nonlocal runtime_checks
        runtime_checks += 1
        return RuntimeVerification("installed", True, "verified", RUNTIME_ID)

    worker = LocalInferenceWorker(
        enabled=True,
        model_verifier=verify_model,
        runtime_verifier=verify_runtime,
        runtime_archive=outside_runtime,
        work_root=root / "worker-tmp",
        model_path=model,
        trusted_root=root,
    )

    with pytest.raises(WorkerUnavailable, match="assistant_unsafe_execution_path"):
        worker.generate(InferenceRequest("en", "BPM question", "{}"))

    assert model_checks == runtime_checks == 0
    assert worker.health().reason_code == "assistant_unsafe_execution_path"


def test_future_assistant_transport_accepts_only_same_origin_bounded_json_post() -> None:
    guard = AssistantRequestGuard("https://bpm.example:8443")
    valid = AssistantRequestMetadata(
        method="POST",
        origin="https://bpm.example:8443",
        host="bpm.example:8443",
        content_type="application/json; charset=utf-8",
        sec_fetch_site="same-origin",
        content_length=ASSISTANT_MAX_REQUEST_BYTES,
    )

    guard.require_same_origin_json(valid)
    invalid = (
        AssistantRequestMetadata("OPTIONS", valid.origin, valid.host, "application/json"),
        AssistantRequestMetadata("POST", "https://evil.example", valid.host, "application/json"),
        AssistantRequestMetadata("POST", valid.origin, "evil.example", "application/json"),
        AssistantRequestMetadata("POST", valid.origin, valid.host, "text/plain"),
        AssistantRequestMetadata(
            "POST", valid.origin, valid.host, "application/json", "cross-site"
        ),
        AssistantRequestMetadata(
            "POST",
            valid.origin,
            valid.host,
            "application/json",
            content_length=ASSISTANT_MAX_REQUEST_BYTES + 1,
        ),
    )

    for request in invalid:
        with pytest.raises(LeastPrivilegeViolation):
            guard.require_same_origin_json(request)


def test_origin_policy_and_child_environment_reject_wildcards_and_proxy_inheritance() -> None:
    with pytest.raises(LeastPrivilegeViolation, match="assistant_invalid_origin_policy"):
        AssistantRequestGuard("*")
    with pytest.raises(LeastPrivilegeViolation, match="assistant_invalid_origin_policy"):
        AssistantRequestGuard("https://bpm.example/assistant")

    environment = restricted_worker_environment()

    assert environment == {
        "LC_ALL": "C",
        "PATH": "",
        "NO_PROXY": "*",
        "no_proxy": "*",
        "HTTP_PROXY": "",
        "HTTPS_PROXY": "",
        "ALL_PROXY": "",
    }


def test_path_and_request_guard_cover_remaining_fail_closed_forms(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    child = root / "child"
    child.write_text("x", encoding="utf-8")
    assert require_managed_path(child, root) == child
    for candidate, managed in (
        (Path("relative"), root),
        (child, Path("relative")),
        (tmp_path / "elsewhere", root),
    ):
        with pytest.raises(LeastPrivilegeViolation):
            require_managed_path(candidate, managed)
    with pytest.raises(LeastPrivilegeViolation):
        require_managed_path(root / "missing", root, require_regular=True)
    directory = root / "directory"
    directory.mkdir()
    with pytest.raises(LeastPrivilegeViolation):
        require_managed_path(directory, root, require_regular=True)
    unsafe_root = tmp_path / "unsafe-root"
    unsafe_root.write_text("x", encoding="utf-8")
    with pytest.raises(LeastPrivilegeViolation):
        require_managed_path(unsafe_root / "child", unsafe_root)
    linked_root = tmp_path / "linked-root"
    linked_root.symlink_to(root, target_is_directory=True)
    with pytest.raises(LeastPrivilegeViolation):
        require_managed_path(linked_root / "child", linked_root)
    inherited_parent = tmp_path / "inherited-parent"
    inherited_parent.symlink_to(tmp_path, target_is_directory=True)
    inherited_root = inherited_parent / "root"
    with pytest.raises(LeastPrivilegeViolation):
        require_managed_path(inherited_root / "child", inherited_root)
    linked_child = root / "linked-child"
    linked_child.symlink_to(child)
    with pytest.raises(LeastPrivilegeViolation):
        require_managed_path(linked_child, root)
    for origin in ("ftp://bpm.example", "https://user@bpm.example", "https://bpm.example?x=1"):
        with pytest.raises(LeastPrivilegeViolation):
            AssistantRequestGuard(origin)
    guard = AssistantRequestGuard("https://bpm.example", maximum_bytes=1)
    with pytest.raises(LeastPrivilegeViolation, match="too_large"):
        guard.require_same_origin_json(
            AssistantRequestMetadata(
                "POST", "https://bpm.example", "bpm.example", "application/json", content_length=-1
            )
        )
