from __future__ import annotations

import hashlib
import io
import json
import tarfile
import threading
import time
from pathlib import Path

import pytest

import app.ai.local_inference_worker as worker_module
import app.ai.runtime_installation as runtime
from app.ai.local_inference_worker import (
    MAX_WORKER_AND_RETRIEVAL_RSS_BYTES,
    InferenceRequest,
    LocalInferenceWorker,
    WorkerCancelled,
    WorkerResourceExceeded,
    WorkerTimedOut,
    WorkerUnavailable,
)
from app.ai.model_installation import VerificationResult
from app.core.locales import ACTIVE_CATALOG_LOCALES


def _install_fake_runtime(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> runtime.RuntimeInstaller:
    script = b"""#!/usr/bin/python3
import sys
import time

sys.stdout.write("ready\\n> ")
sys.stdout.flush()
for line in sys.stdin:
    if line.strip() == "/exit":
        break
    if "hang" in line:
        time.sleep(30)
        continue
    if "crash" in line:
        raise SystemExit(4)
    sys.stdout.write("<think>private reasoning</think>grounded text\\n> ")
    sys.stdout.flush()
"""
    source_archive = tmp_path / "source.tar.gz"
    with tarfile.open(source_archive, mode="w:gz") as archive:
        folder = tarfile.TarInfo("llama-b9637")
        folder.type = tarfile.DIRTYPE
        archive.addfile(folder)
        executable = tarfile.TarInfo("llama-b9637/llama-cli")
        executable.mode = 0o755
        executable.size = len(script)
        archive.addfile(executable, io.BytesIO(script))
    payload = source_archive.read_bytes()
    monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_BYTES", len(payload))
    monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_SHA256", hashlib.sha256(payload).hexdigest())
    installer = runtime.RuntimeInstaller(tmp_path / "ai" / "runtime")
    installer.install_local(source_archive, confirmed=True)
    return installer


def _verified_model() -> VerificationResult:
    return VerificationResult("installed", True, "verified", "qwen3-0.6b-q8_0-official-gguf")


def _worker(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> LocalInferenceWorker:
    installer = _install_fake_runtime(monkeypatch, tmp_path)
    model_path = tmp_path / "ai" / "models" / "model.gguf"
    model_path.parent.mkdir(parents=True)
    model_path.write_bytes(b"test-model")
    return LocalInferenceWorker(
        enabled=True,
        model_verifier=_verified_model,
        runtime_verifier=installer.verify,
        runtime_archive=installer.archive_path,
        work_root=tmp_path / "ai" / "worker-tmp",
        model_path=model_path,
        start_timeout_seconds=2,
        response_timeout_seconds=0.4,
    )


def test_worker_is_lazy_has_no_listener_and_strips_hidden_reasoning(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _worker(monkeypatch, tmp_path)

    assert worker.health().state == "not-installed"
    command = worker._command(Path("/runtime/llama-cli"), Path("/model.gguf"))
    assert "--offline" in command
    assert "--device" in command and "none" in command
    assert "--no-show-timings" in command
    assert "--conversation" in command
    assert "--no-conversation" not in command
    assert "independent explanation" in command[command.index("--system-prompt") + 1]
    assert "llama-server" not in " ".join(command)
    assert "--port" not in command
    assert command[command.index("--n-predict") + 1] == "512"
    assert command[command.index("--grammar") + 1] == worker_module._STRUCTURED_RESPONSE_GBNF

    answer = worker.generate(InferenceRequest("en", "How do I set a policy?", "{}"))

    assert answer.text == "grounded text"
    assert worker.health().state == "ready"
    assert worker._process is None
    timing = worker.timing_profile()
    assert timing.cold_start_required is True
    assert timing.rolling_tokens_per_second is not None
    assert timing.model_quantization == "Q8_0"
    worker.unload()
    assert worker.health().state == "not-installed"


def test_worker_disabled_or_unverified_artifacts_never_start(tmp_path: Path) -> None:
    model_path = tmp_path / "model.gguf"
    runtime_path = tmp_path / "missing.tar.gz"
    model_path.write_bytes(b"model")
    runtime_path.write_bytes(b"runtime")
    unavailable = LocalInferenceWorker(
        enabled=False,
        model_verifier=_verified_model,
        runtime_verifier=lambda: runtime.RuntimeVerification(
            "installed", True, "verified", runtime.RUNTIME_ID
        ),
        runtime_archive=runtime_path,
        work_root=tmp_path / "work",
        model_path=model_path,
    )
    with pytest.raises(WorkerUnavailable, match="assistant_disabled"):
        unavailable.generate(InferenceRequest("en", "question", "{}"))

    incompatible = LocalInferenceWorker(
        enabled=True,
        model_verifier=lambda: VerificationResult("incompatible", False, "bad", "model"),
        runtime_verifier=lambda: runtime.RuntimeVerification(
            "installed", True, "verified", runtime.RUNTIME_ID
        ),
        runtime_archive=runtime_path,
        work_root=tmp_path / "work-two",
        model_path=model_path,
    )
    with pytest.raises(WorkerUnavailable, match="assistant_model_unverified"):
        incompatible.generate(InferenceRequest("en", "question", "{}"))
    assert incompatible.health().lexical_search_ready is True


def test_worker_cancellation_and_timeout_terminate_the_child(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _worker(monkeypatch, tmp_path)
    observed: list[BaseException] = []

    def run() -> None:
        try:
            worker.generate(InferenceRequest("en", "hang", "{}"))
        except BaseException as error:  # Assert the cross-thread result below.
            observed.append(error)

    thread = threading.Thread(target=run)
    thread.start()
    for _ in range(20):
        if worker.health().state == "busy":
            break
        time.sleep(0.02)
    assert worker.cancel() is True
    thread.join(timeout=3)
    assert len(observed) == 1 and isinstance(observed[0], WorkerCancelled)
    assert worker.health().state == "cancelled"
    assert worker._process is None
    assert worker._temporary_runtime is None

    worker.unload()
    with pytest.raises(WorkerTimedOut):
        worker.generate(InferenceRequest("en", "hang", "{}"))
    assert worker.health().state == "crashed"
    assert worker.health().lexical_search_ready is True
    assert worker._process is None
    assert worker._temporary_runtime is None


def test_worker_cancellation_is_admitted_while_runtime_startup_is_in_progress(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _worker(monkeypatch, tmp_path)
    original_extract = worker_module.extract_verified_worker_bundle
    extraction_started = threading.Event()
    release_extraction = threading.Event()
    observed: list[BaseException] = []

    def delayed_extract(*args: object, **kwargs: object) -> Path:
        extraction_started.set()
        assert release_extraction.wait(timeout=2)
        return original_extract(*args, **kwargs)

    monkeypatch.setattr(worker_module, "extract_verified_worker_bundle", delayed_extract)

    def run() -> None:
        try:
            worker.generate(InferenceRequest("en", "question", "{}"))
        except BaseException as error:
            observed.append(error)

    thread = threading.Thread(target=run)
    thread.start()
    assert extraction_started.wait(timeout=2)
    assert worker.cancel() is True
    release_extraction.set()
    thread.join(timeout=3)

    assert len(observed) == 1 and isinstance(observed[0], WorkerCancelled)
    assert worker.health().state == "cancelled"


def test_worker_crash_and_rss_ceiling_fail_closed_without_allocating_memory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    worker = _worker(monkeypatch, tmp_path)

    with pytest.raises(WorkerUnavailable, match="assistant_worker_exited"):
        worker.generate(InferenceRequest("en", "crash", "{}"))
    assert worker.health().state == "crashed"
    assert worker.health().lexical_search_ready is True
    assert worker._process is None
    assert worker._temporary_runtime is None

    worker.unload()
    worker.generate(InferenceRequest("en", "normal", "{}"))
    monkeypatch.setattr(
        worker,
        "_rss_bytes",
        lambda process_id: MAX_WORKER_AND_RETRIEVAL_RSS_BYTES + 1,
    )
    with pytest.raises(WorkerResourceExceeded, match="assistant_resource_limit"):
        worker.generate(InferenceRequest("en", "normal", "{}"))
    assert worker.health().state == "crashed"
    assert worker.health().reason_code == "assistant_resource_limit"
    assert worker._process is None
    assert worker._temporary_runtime is None


@pytest.mark.parametrize(
    ("locale", "question"),
    [
        ("en", "How do I set a policy?"),
        ("ru", "Как настроить политику?"),
        ("de", "Wie konfiguriere ich eine Richtlinie?"),
        ("zh-CN", "如何配置策略？"),
        ("fr", "Comment configurer une stratégie ?"),
        ("es-ES", "¿Cómo configuro una política?"),
    ],
)
def test_worker_serializes_each_supported_locale_as_utf8_without_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, locale: str, question: str
) -> None:
    local_worker = _worker(monkeypatch, tmp_path)
    request = InferenceRequest(locale, question, '{"citation_id":"topic:validation"}')

    serialized = local_worker._serialize_request(request)
    payload = json.loads(serialized)

    assert locale in ACTIVE_CATALOG_LOCALES
    assert payload["locale"] == locale
    assert payload["question"] == question
    assert serialized.encode("utf-8").decode("utf-8") == serialized
    assert local_worker.generate(request).locale == locale


def test_worker_keeps_fixed_sampling_and_rejects_unbounded_packets(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    local_worker = _worker(monkeypatch, tmp_path)
    command = local_worker._command(Path("/runtime/llama-cli"), Path("/model.gguf"))

    assert command[command.index("--temperature") + 1] == "0"
    assert command[command.index("--top-p") + 1] == "1"
    assert command[command.index("--top-k") + 1] == "1"
    assert command[command.index("--seed") + 1] == "0"
    assert "--no-show-timings" in command
    assert command[command.index("--ctx-size") + 1] == "4096"
    grammar = command[command.index("--grammar") + 1]
    assert "root ::= answer | terminal" in grammar
    assert '"\\"sections\\""' in grammar
    assert "citation-array" in grammar
    with pytest.raises(WorkerUnavailable, match="assistant_invalid_evidence"):
        local_worker.generate(InferenceRequest("en", "question", "x" * 32_001))
    with pytest.raises(WorkerUnavailable, match="assistant_input_limit"):
        local_worker.generate(
            InferenceRequest(
                "en",
                "q" * 4_000,
                "e" * 32_000,
                (
                    ("user", "d" * 4_000),
                    ("assistant", "d" * 4_000),
                    ("user", "d" * 4_000),
                    ("assistant", "d" * 4_000),
                ),
            )
        )
    complete_dialogue = tuple(
        pair
        for number in range(8)
        for pair in (("user", f"question-{number}"), ("assistant", f"answer-{number}"))
    )
    assert len(complete_dialogue) == worker_module.MAX_DIALOGUE_TURNS == 16
    assert json.loads(
        local_worker._serialize_request(InferenceRequest("en", "question", "{}", complete_dialogue))
    )["dialogue"][-1] == {"role": "assistant", "text": "answer-7"}
    with pytest.raises(WorkerUnavailable, match="assistant_dialogue_limit"):
        local_worker._serialize_request(
            InferenceRequest("en", "question", "{}", complete_dialogue + (("user", "ninth"),))
        )
