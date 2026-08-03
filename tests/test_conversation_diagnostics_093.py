from __future__ import annotations

from dataclasses import dataclass

from app.ai.local_inference_worker import WorkerHealth
from app.documentation.conversation_diagnostics import (
    AssistantDiagnosticsService,
    CompatibilitySnapshot,
)


@dataclass
class FakeQueue:
    value: str = "idle"

    def queue_depth_class(self) -> str:
        return self.value


def _service(
    *,
    compatibility: CompatibilitySnapshot | None = None,
    worker: WorkerHealth | None = None,
    queue: FakeQueue | None = None,
    web: str = "not_configured",
) -> AssistantDiagnosticsService:
    actual_compatibility = compatibility or CompatibilitySnapshot(True, True, True)
    actual_worker = worker or WorkerHealth("ready", True, True, "assistant_ready")
    actual_queue = queue or FakeQueue()
    return AssistantDiagnosticsService(
        compatibility_provider=lambda: actual_compatibility,
        worker_health_provider=lambda: actual_worker,
        queue_depth_provider=actual_queue,  # type: ignore[arg-type]  # Invalid probes are tested.
        web_availability_provider=lambda: web,  # type: ignore[return-value]  # Invalid probes are tested.
    )


def test_diagnostics_reports_safe_compatible_ready_state_without_content_or_network() -> None:
    diagnostics = _service(queue=FakeQueue("active"), web="local_only").status()

    assert diagnostics.state == "ready"
    assert diagnostics.assistant_ready is True
    assert diagnostics.lexical_search_ready is True
    assert diagnostics.configuration_compatible is True
    assert diagnostics.model_compatible is True
    assert diagnostics.index_compatible is True
    assert diagnostics.load_state == "ready"
    assert diagnostics.queue_depth_class == "active"
    assert diagnostics.last_local_error_class == "none"
    assert diagnostics.web_availability == "local_only"
    assert "question" not in diagnostics.__dataclass_fields__
    assert "prompt" not in diagnostics.__dataclass_fields__
    assert "excerpt" not in diagnostics.__dataclass_fields__


def test_diagnostics_discard_a_content_bearing_worker_reason() -> None:
    secret = "private question and retrieved excerpt"
    diagnostics = _service(
        worker=WorkerHealth("crashed", False, True, f"assistant_timeout: {secret}")
    ).status()

    assert diagnostics.last_local_error_class == "runtime"
    assert secret not in repr(diagnostics)


def test_diagnostics_distinguishes_setup_model_index_and_runtime_failures() -> None:
    setup = _service(compatibility=CompatibilitySnapshot(False, True, True)).status()
    model = _service(compatibility=CompatibilitySnapshot(True, False, True)).status()
    index = _service(compatibility=CompatibilitySnapshot(True, True, False)).status()
    runtime = _service(worker=WorkerHealth("crashed", False, True, "assistant_timeout")).status()

    assert (setup.state, setup.last_local_error_class) == ("degraded", "setup")
    assert (model.state, model.last_local_error_class) == ("incompatible", "model")
    assert (index.state, index.last_local_error_class) == ("degraded", "index")
    assert (runtime.state, runtime.last_local_error_class) == ("crashed", "runtime")
    assert all(not value.assistant_ready for value in (setup, model, index, runtime))
    assert all(value.lexical_search_ready for value in (setup, model, index, runtime))


def test_diagnostics_reports_a_lazy_verified_worker_as_ready_without_loading_it() -> None:
    diagnostics = _service(
        worker=WorkerHealth("not-installed", False, True, "assistant_not_started")
    ).status()

    assert diagnostics.state == "ready"
    assert diagnostics.assistant_ready is True
    assert diagnostics.load_state == "not_started"
    assert diagnostics.last_local_error_class == "none"


def test_diagnostics_retains_only_last_safe_error_class_and_labels_web_offline() -> None:
    worker = WorkerHealth("crashed", False, True, "assistant_timeout")
    web = "not_configured"
    service = AssistantDiagnosticsService(
        compatibility_provider=lambda: CompatibilitySnapshot(True, True, True),
        worker_health_provider=lambda: worker,
        queue_depth_provider=FakeQueue(),
        web_availability_provider=lambda: web,  # type: ignore[return-value]
    )

    failed = service.status()
    worker = WorkerHealth("ready", True, True, "assistant_ready")
    web = "offline"
    recovered = service.status()

    assert failed.last_local_error_class == "runtime"
    assert recovered.state == "web-offline"
    assert recovered.assistant_ready is True
    assert recovered.last_local_error_class == "runtime"
    assert recovered.web_availability == "offline"


def test_invalid_or_failed_probe_fails_closed_to_safe_setup_diagnostics() -> None:
    invalid = _service(queue=FakeQueue("two-active")).status()
    invalid_web = _service(web="unexpected").status()
    failing = AssistantDiagnosticsService(
        compatibility_provider=lambda: (_ for _ in ()).throw(RuntimeError("hidden")),
        worker_health_provider=lambda: WorkerHealth("ready", True, True, "assistant_ready"),
        queue_depth_provider=FakeQueue(),
    ).status()

    assert invalid.state == invalid_web.state == failing.state == "degraded"
    assert invalid.last_local_error_class == invalid_web.last_local_error_class == failing.last_local_error_class == "setup"
    assert invalid.assistant_ready is invalid_web.assistant_ready is failing.assistant_ready is False
