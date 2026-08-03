"""Safe, content-free operational diagnostics for the local documentation assistant."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

from app.ai.local_inference_worker import WorkerHealth

AssistantState = Literal[
    "disabled",
    "not-installed",
    "ready",
    "busy",
    "cancelled",
    "degraded",
    "incompatible",
    "crashed",
    "web-offline",
]
LoadState = Literal["disabled", "not_started", "ready", "busy", "cancelled", "failed"]
QueueDepthClass = Literal["idle", "active", "queued"]
LocalErrorClass = Literal["none", "setup", "index", "model", "runtime"]
WebAvailability = Literal["not_configured", "local_only", "available", "offline"]


@dataclass(frozen=True)
class CompatibilitySnapshot:
    """Boolean compatibility results from approved lifecycle/index owners only."""

    configuration_compatible: bool
    model_compatible: bool
    index_compatible: bool


@dataclass(frozen=True)
class AssistantDiagnostics:
    """Safe status shape; it intentionally has no conversation or artifact-content fields."""

    state: AssistantState
    assistant_ready: bool
    lexical_search_ready: bool
    configuration_compatible: bool
    model_compatible: bool
    index_compatible: bool
    load_state: LoadState
    queue_depth_class: QueueDepthClass
    last_local_error_class: LocalErrorClass
    web_availability: WebAvailability


class QueueDepthProvider(Protocol):
    """The stream controller supplies only a coarse queue class."""

    def queue_depth_class(self) -> QueueDepthClass: ...


CompatibilityProvider = Callable[[], CompatibilitySnapshot]
WorkerHealthProvider = Callable[[], WorkerHealth]
WebAvailabilityProvider = Callable[[], WebAvailability]


class AssistantDiagnosticsService:
    """Combine injected safe probes without loading a model, retrieving evidence, or using network."""

    def __init__(
        self,
        *,
        compatibility_provider: CompatibilityProvider,
        worker_health_provider: WorkerHealthProvider,
        queue_depth_provider: QueueDepthProvider,
        web_availability_provider: WebAvailabilityProvider = lambda: "not_configured",
    ) -> None:
        self._compatibility_provider = compatibility_provider
        self._worker_health_provider = worker_health_provider
        self._queue_depth_provider = queue_depth_provider
        self._web_availability_provider = web_availability_provider
        self._last_local_error_class: LocalErrorClass = "none"

    def status(self) -> AssistantDiagnostics:
        """Return a content-free snapshot; all probe failures degrade safely to setup failure."""

        try:
            compatibility = self._compatibility_provider()
            worker = self._worker_health_provider()
            queue_depth_class = self._queue_depth_provider.queue_depth_class()
            web_availability = self._web_availability_provider()
        except Exception:
            return self._status_for_probe_failure()
        if queue_depth_class not in {"idle", "active", "queued"}:
            return self._status_for_probe_failure()
        if web_availability not in {"not_configured", "local_only", "available", "offline"}:
            return self._status_for_probe_failure()
        error_class = self._error_class(compatibility, worker)
        if error_class != "none":
            self._last_local_error_class = error_class
        state = self._state(compatibility, worker, web_availability)
        return AssistantDiagnostics(
            state=state,
            assistant_ready=state in {"ready", "web-offline"},
            lexical_search_ready=True,
            configuration_compatible=compatibility.configuration_compatible,
            model_compatible=compatibility.model_compatible,
            index_compatible=compatibility.index_compatible,
            load_state=self._load_state(worker.state),
            queue_depth_class=queue_depth_class,
            last_local_error_class=self._last_local_error_class,
            web_availability=web_availability,
        )

    def _status_for_probe_failure(self) -> AssistantDiagnostics:
        self._last_local_error_class = "setup"
        return AssistantDiagnostics(
            state="degraded",
            assistant_ready=False,
            lexical_search_ready=True,
            configuration_compatible=False,
            model_compatible=False,
            index_compatible=False,
            load_state="failed",
            queue_depth_class="idle",
            last_local_error_class="setup",
            web_availability="not_configured",
        )

    @staticmethod
    def _state(
        compatibility: CompatibilitySnapshot,
        worker: WorkerHealth,
        web_availability: WebAvailability,
    ) -> AssistantState:
        if not compatibility.configuration_compatible or not compatibility.index_compatible:
            return "degraded"
        if not compatibility.model_compatible:
            return "incompatible"
        # A verified, lazy worker has not allocated the model yet, but it is available for a
        # request.  Surface that as ready while ``load_state`` retains ``not_started``.
        if worker.state == "not-installed":
            return "ready"
        states: dict[str, AssistantState] = {
            "disabled": "disabled",
            "ready": "ready",
            "busy": "busy",
            "cancelled": "cancelled",
            "crashed": "crashed",
            "incompatible": "incompatible",
            "idle": "not-installed",
        }
        state = states.get(worker.state, "crashed")
        if state == "ready" and web_availability == "offline":
            return "web-offline"
        return state

    @staticmethod
    def _load_state(worker_state: str) -> LoadState:
        states: dict[str, LoadState] = {
            "disabled": "disabled",
            "idle": "not_started",
            "not-installed": "not_started",
            "ready": "ready",
            "busy": "busy",
            "cancelled": "cancelled",
            "crashed": "failed",
            "incompatible": "failed",
        }
        return states.get(worker_state, "failed")

    @staticmethod
    def _error_class(compatibility: CompatibilitySnapshot, worker: WorkerHealth) -> LocalErrorClass:
        if not compatibility.configuration_compatible:
            return "setup"
        if not compatibility.model_compatible or "model" in worker.reason_code:
            return "model"
        if not compatibility.index_compatible:
            return "index"
        if worker.state in {"crashed", "incompatible"}:
            return "runtime"
        return "none"
