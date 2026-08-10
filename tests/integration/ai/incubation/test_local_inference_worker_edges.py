from __future__ import annotations

import queue
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import app.ai.local_inference_worker as module
from app.ai.local_inference_worker import (
    InferenceRequest,
    LocalInferenceWorker,
    WorkerBusy,
    WorkerCancelled,
    WorkerResourceExceeded,
    WorkerTimedOut,
    WorkerUnavailable,
)
from app.ai.model_installation import VerificationResult
from app.ai.runtime_installation import RuntimeVerification


def _verified_model() -> VerificationResult:
    return VerificationResult("installed", True, "verified", "model")


def _verified_runtime() -> RuntimeVerification:
    return RuntimeVerification("installed", True, "verified", "runtime")


def _worker(tmp_path: Path, *, enabled: bool = True) -> LocalInferenceWorker:
    root = tmp_path / "ai"
    root.mkdir(parents=True)
    model = root / "model.gguf"
    archive = root / "runtime.tar.gz"
    model.write_bytes(b"model")
    archive.write_bytes(b"runtime")
    return LocalInferenceWorker(
        enabled=enabled,
        model_verifier=_verified_model,
        runtime_verifier=_verified_runtime,
        runtime_archive=archive,
        work_root=root / "work",
        model_path=model,
        trusted_root=root,
    )


class _Process:
    def __init__(self, *, poll: int | None = None, stdout: object | None = None) -> None:
        self.pid = 12345
        self._poll = poll
        self.stdout = stdout
        self.stdin = SimpleNamespace(write=lambda _: None, flush=lambda: None, close=lambda: None)
        self.wait_calls: list[int] = []

    def poll(self) -> int | None:
        return self._poll

    def wait(self, timeout: int) -> int:
        self.wait_calls.append(timeout)
        return 0


def test_default_installation_health_timing_and_state_guards(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class Installer:
        def __init__(self, root: Path) -> None:
            self.artifact_path = root / "artifact"
            self.archive_path = root / "archive"

        def verify(self) -> object:
            return _verified_model()

    monkeypatch.setattr(
        module,
        "get_settings",
        lambda: SimpleNamespace(DATA_DIR=tmp_path, AI_LOCAL_CHAT_ENABLED=False),
    )
    monkeypatch.setattr(module, "ModelInstaller", Installer)
    monkeypatch.setattr(module, "RuntimeInstaller", Installer)
    default = LocalInferenceWorker.for_default_installation()
    assert default.health().state == "disabled"
    assert (
        LocalInferenceWorker.for_default_installation(enabled=True).health().state
        == "not-installed"
    )

    worker = _worker(tmp_path / "states")
    for state, reason in (
        ("ready", "assistant_ready"),
        ("busy", "assistant_busy"),
        ("cancelled", "assistant_cancelled"),
        ("crashed", "assistant_crashed"),
        ("incompatible", "assistant_incompatible"),
    ):
        worker._state = state
        worker._fault_reason = None
        assert worker.health().reason_code == reason
    worker._state = "idle"
    worker._generation_rates.extend((2.0, 4.0))
    worker._last_cold_start_seconds = 3.0
    worker._process = _Process()  # type: ignore[assignment]
    timing = worker.timing_profile()
    assert timing.cold_start_required is False
    assert timing.rolling_tokens_per_second == 3.0
    assert timing.last_cold_start_seconds == 3.0
    assert worker.cancel() is False
    worker.unload()
    assert not worker._generation_rates

    worker._state = "busy"
    with pytest.raises(WorkerBusy):
        worker.generate(InferenceRequest("en", "question", "{}"))
    worker._state = "crashed"
    worker._fault_reason = "fault"
    with pytest.raises(WorkerUnavailable, match="fault"):
        worker.generate(InferenceRequest("en", "question", "{}"))


def test_startup_and_serialization_edge_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _worker(tmp_path)
    for request, code in (
        (InferenceRequest("xx", "question", "{}"), "assistant_unsupported_locale"),
        (InferenceRequest("en", "", "{}"), "assistant_invalid_question"),
        (
            InferenceRequest("en", "question", "{}", (("bad", "text"),)),
            "assistant_invalid_dialogue",
        ),
        (InferenceRequest("en", "question", "{}", (("user", 3),)), "assistant_invalid_dialogue"),  # type: ignore[arg-type]
    ):
        with pytest.raises(WorkerUnavailable, match=code):
            worker._serialize_request(request)

    worker._cancel_requested.set()
    with pytest.raises(WorkerCancelled):
        worker._ensure_started_locked()
    worker._cancel_requested.clear()
    worker._process = _Process()  # type: ignore[assignment]
    worker._ensure_started_locked()
    worker._process = None
    worker._runtime_verifier = lambda: RuntimeVerification("bad", False, "bad", "runtime")
    monkeypatch.setattr(worker, "_assert_execution_paths", lambda: None)
    with pytest.raises(WorkerUnavailable, match="assistant_runtime_unverified"):
        worker._ensure_started_locked()

    worker = _worker(tmp_path / "errors")
    monkeypatch.setattr(worker, "_assert_execution_paths", lambda: None)
    monkeypatch.setattr(
        module, "extract_verified_worker_bundle", lambda *_: (_ for _ in ()).throw(OSError("no"))
    )
    with pytest.raises(WorkerUnavailable, match="assistant_start_failed"):
        worker._ensure_started_locked()
    worker = _worker(tmp_path / "runtime-error")
    monkeypatch.setattr(worker, "_assert_execution_paths", lambda: None)
    monkeypatch.setattr(
        module,
        "extract_verified_worker_bundle",
        lambda *_: (_ for _ in ()).throw(RuntimeError("bad")),
    )
    with pytest.raises(WorkerUnavailable, match="assistant_start_failed"):
        worker._ensure_started_locked()


def test_startup_cancellation_before_bundle_extraction_cleans_up_runtime_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _worker(tmp_path)
    monkeypatch.setattr(worker, "_assert_execution_paths", lambda: None)
    original_temporary_directory = module.tempfile.TemporaryDirectory

    def cancel_after_runtime_directory(*args: object, **kwargs: object) -> object:
        runtime_directory = original_temporary_directory(*args, **kwargs)
        worker._cancel_requested.set()
        return runtime_directory

    monkeypatch.setattr(module.tempfile, "TemporaryDirectory", cancel_after_runtime_directory)
    monkeypatch.setattr(
        module,
        "extract_verified_worker_bundle",
        lambda *_: pytest.fail("cancelled startup must not extract the runtime bundle"),
    )

    with pytest.raises(WorkerCancelled, match="assistant_cancelled"):
        worker._ensure_started_locked()

    assert worker._temporary_runtime is None


def test_worker_io_timeout_resource_and_process_cleanup_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _worker(tmp_path)
    worker._read_output()
    assert worker._output.get_nowait() is None
    worker._output = queue.Queue()
    worker._output.put(None)
    with pytest.raises(WorkerUnavailable, match="assistant_worker_exited"):
        worker._wait_for_prompt(1, "startup")
    worker._cancel_requested.set()
    with pytest.raises(WorkerCancelled):
        worker._wait_for_prompt(1, "startup")
    worker._cancel_requested.clear()
    worker._process = _Process(poll=1)  # type: ignore[assignment]
    with pytest.raises(WorkerUnavailable, match="assistant_worker_exited"):
        worker._wait_for_prompt(0.01, "startup")
    worker._process = _Process()  # type: ignore[assignment]
    monkeypatch.setattr(worker, "_rss_exceeds_limit", lambda: True)
    with pytest.raises(WorkerResourceExceeded):
        worker._wait_for_prompt(1, "startup")
    monkeypatch.setattr(worker, "_rss_exceeds_limit", lambda: False)
    with pytest.raises(WorkerTimedOut):
        worker._wait_for_prompt(0, "response")
    with pytest.raises(WorkerUnavailable, match="assistant_start_timeout"):
        worker._wait_for_prompt(0, "startup")

    worker._cancel_requested.set()
    with pytest.raises(WorkerCancelled):
        worker._request_response("prompt")
    worker._cancel_requested.clear()
    worker._process = None
    with pytest.raises(WorkerUnavailable, match="assistant_worker_unavailable"):
        worker._request_response("prompt")
    worker._record_generation_timing(cold_start_seconds=1, response_seconds=0, visible_text="text")
    worker._record_generation_timing(cold_start_seconds=2, response_seconds=1, visible_text="текст")
    assert worker._last_cold_start_seconds == 2
    worker._process = None
    assert worker._rss_exceeds_limit() is False
    assert worker._rss_bytes(-1) is None

    class StatusPath:
        def __init__(self, text: str) -> None:
            self.text = text

        def read_text(self, **_: object) -> str:
            return self.text

    monkeypatch.setattr(module, "Path", lambda _: StatusPath("VmRSS: bad value"))
    assert worker._rss_bytes(1) is None
    monkeypatch.setattr(module, "Path", lambda _: StatusPath("Name: x\nVmRSS:\t12 kB\n"))
    assert worker._rss_bytes(1) == 12 * 1024
    monkeypatch.setattr(module, "Path", Path)

    worker = _worker(tmp_path / "process")
    finished = _Process(poll=0)
    worker._process = finished  # type: ignore[assignment]
    worker._terminate_process_locked()
    assert finished.wait_calls == [0]
    running = _Process()
    worker._process = running  # type: ignore[assignment]
    monkeypatch.setattr(module.os, "killpg", lambda *_: None)
    worker._terminate_process_locked()
    assert running.wait_calls == [5]

    class FailingCloseStream:
        def close(self) -> None:
            raise OSError("already closed")

    reader_join_calls: list[int] = []
    reader = SimpleNamespace(
        join=lambda timeout: reader_join_calls.append(timeout),
        is_alive=lambda: True,
    )
    close_errors = _Process(poll=0, stdout=FailingCloseStream())
    close_errors.stdin = FailingCloseStream()  # type: ignore[assignment]
    worker._process = close_errors  # type: ignore[assignment]
    worker._reader = reader  # type: ignore[assignment]
    worker._terminate_process_locked()
    assert reader_join_calls == [1, 1]

    no_stdin = _Process(poll=0)
    no_stdin.stdin = None  # type: ignore[assignment]
    worker._process = no_stdin  # type: ignore[assignment]
    worker._terminate_process_locked()


def test_worker_path_safety_and_hidden_reasoning_are_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _worker(tmp_path)
    worker._work_root.write_text("not a directory", encoding="utf-8")
    with pytest.raises(WorkerUnavailable, match="assistant_unsafe_work_root"):
        worker._prepare_work_root_locked()
    worker._work_root.unlink()
    worker._prepare_work_root_locked()
    assert worker._work_root.stat().st_mode & 0o777 == 0o700
    monkeypatch.setattr(
        module,
        "require_managed_path",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(module.LeastPrivilegeViolation("unsafe")),
    )
    with pytest.raises(WorkerUnavailable, match="unsafe"):
        worker._assert_execution_paths()
    assert worker.health().state == "incompatible"
    assert (
        LocalInferenceWorker._strip_hidden_reasoning("<think>x</think> answer <think>y")
        == "answer y"
    )


def test_worker_terminal_process_and_remaining_os_fallbacks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _worker(tmp_path)
    exited = _Process(poll=1)
    monkeypatch.setattr(
        worker, "_ensure_started_locked", lambda: setattr(worker, "_process", exited)
    )
    monkeypatch.setattr(worker, "_request_response", lambda _: "answer")
    with pytest.raises(WorkerUnavailable, match="assistant_worker_exited"):
        worker.generate(InferenceRequest("en", "question", "{}"))
    assert worker.health().state == "crashed"

    worker._record_generation_timing(cold_start_seconds=0, response_seconds=1, visible_text="text")

    class StatusPath:
        def read_text(self, **_: object) -> str:
            return "Name: no-rss\n"

    monkeypatch.setattr(module, "Path", lambda _: StatusPath())
    assert worker._rss_bytes(1) is None
    monkeypatch.setattr(module, "Path", Path)

    class TimeoutProcess(_Process):
        def wait(self, timeout: int) -> int:
            raise subprocess.TimeoutExpired("worker", timeout)

    finished = TimeoutProcess(poll=0)
    worker._process = finished  # type: ignore[assignment]
    worker._terminate_process_locked()

    running = TimeoutProcess()
    worker._process = running  # type: ignore[assignment]
    monkeypatch.setattr(module.os, "killpg", lambda *_: None)
    worker._terminate_process_locked()

    kill_error = TimeoutProcess()
    worker._process = kill_error  # type: ignore[assignment]
    signals: list[int] = []

    def kill_then_error(_: int, signal_number: int) -> None:
        signals.append(signal_number)
        if len(signals) == 2:
            raise OSError("already gone")

    monkeypatch.setattr(module.os, "killpg", kill_then_error)
    worker._terminate_process_locked()
    assert len(signals) == 2
