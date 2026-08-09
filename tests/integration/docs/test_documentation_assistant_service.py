from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.documentation.assistant_service import (
    AssistantSource,
    ControllerDocumentationAssistantService,
    TrainingDocumentationAssistantService,
)
from app.documentation.conversation import ConversationRequest
from app.documentation.conversation_context import (
    ConversationContextStore,
    ConversationContextUnavailable,
)
from app.documentation.conversation_diagnostics import AssistantDiagnostics
from app.documentation.conversation_stream import ConversationAdmission, ConversationStreamEvent
from app.documentation.retrieval import LocalCitation
from app.documentation.web_evidence_consent import (
    WebEvidenceConfiguration,
    WebEvidenceModeStore,
)

TAB_A = "tab_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
TAB_B = "tab_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


@dataclass
class _Diagnostics:
    value: AssistantDiagnostics

    def status(self) -> AssistantDiagnostics:
        return self.value


class _Controller:
    def __init__(self) -> None:
        self.submitted: list[ConversationRequest] = []
        self.cancelled: list[str] = []
        self._events = [
            ConversationStreamEvent(
                "accepted",
                "request-1",
                "accepted",
                1,
                "assistant_accepted",
                "assistant_chat_accepted",
                "assistant_chat_cancel",
            ),
            ConversationStreamEvent(
                "final",
                "request-1",
                "answer",
                2,
                "assistant_citations_validated",
                "assistant_chat_answer",
                "",
                "answer",
                "Grounded answer",
                ("source-1",),
            ),
        ]

    def submit(self, request: ConversationRequest) -> ConversationAdmission:
        self.submitted.append(request)
        return ConversationAdmission("request-1", "accepted", "assistant_accepted", 1)

    def poll(self, request_id: str) -> tuple[ConversationStreamEvent, ...]:
        assert request_id == "request-1"
        events = tuple(self._events)
        self._events.clear()
        return events

    def cancel(self, request_id: str) -> bool:
        self.cancelled.append(request_id)
        return request_id == "request-1"

    def disconnect(self, request_id: str) -> bool:
        return self.cancel(request_id)

    def source(self, request_id: str, source_id: str) -> LocalCitation | None:
        if request_id != "request-1" or source_id not in {"source-1", "src_opaque"}:
            return None
        return LocalCitation("source-1", "/help/en/user/overview.html", "overview", "root")


def _service(
    controller: _Controller,
    store: ConversationContextStore,
    web_mode_store: WebEvidenceModeStore | None = None,
) -> ControllerDocumentationAssistantService:
    return ControllerDocumentationAssistantService(
        controller=controller,  # type: ignore[arg-type]
        context_store=store,
        diagnostics=_Diagnostics(
            AssistantDiagnostics(
                "ready", True, True, True, True, True, "ready", "idle", "none", "local_only"
            )
        ),  # type: ignore[arg-type]
        bpm_version="0.9.3",
        source_resolver=lambda citation: AssistantSource(
            citation.citation_id,
            "BPM overview",
            citation.published_url,
            "en",
            "Approved documentation excerpt.",
        ),
        web_mode_store=web_mode_store,
    )


def test_controller_service_binds_opaque_browser_session_to_context_and_sources() -> None:
    controller = _Controller()
    store = ConversationContextStore()
    service = _service(controller, store)

    status = service.status(locale="en", session_id="browser-session")
    assert status.assistant_ready is True
    assert status.reason_code == "assistant_ready"

    admitted = service.ask(
        request=ConversationRequest("en", "How do I configure BPM?"),
        session_id="browser-session",
    )
    assert admitted.request_id == "request-1"
    context_id = controller.submitted[0].session_id
    assert context_id is not None and context_id != "browser-session"

    events = tuple(service.events(request_id="request-1", session_id="browser-session") or ())
    assert [event.state for event in events] == ["accepted", "answer"]
    assert service.events(request_id="request-1", session_id="other-browser") is None

    source = service.source(
        request_id="request-1", source_id="source-1", session_id="browser-session"
    )
    assert source is not None
    assert source.published_url == "/help/en/user/overview.html"

    opaque_source = service.source(
        request_id="request-1", source_id="src_opaque", session_id="browser-session"
    )
    assert opaque_source is not None
    assert opaque_source.source_id == "src_opaque"

    assert service.clear(session_id="browser-session") is True
    assert controller.cancelled == ["request-1"]
    assert (
        service.source(request_id="request-1", source_id="source-1", session_id="browser-session")
        is None
    )
    try:
        store.snapshot(session_id=context_id, locale="en", bpm_version="0.9.3")
    except ConversationContextUnavailable as error:
        assert error.code == "assistant_session_unavailable"
    else:
        raise AssertionError("clear must remove the local dialogue context")


def test_service_derives_web_mode_from_server_state_and_clear_does_not_reset_it() -> None:
    controller = _Controller()
    context = ConversationContextStore()
    mode = WebEvidenceModeStore(configuration=WebEvidenceConfiguration(True, "server-only-token"))
    service = _service(controller, context, mode)

    service.ask(
        request=ConversationRequest(
            "en", "Crafted request", web_mode="request_web", web_tab_id=TAB_A
        ),
        session_id="browser-session",
    )
    assert controller.submitted[-1].web_mode == "local_only"

    enabled = service.set_web_mode(
        locale="en", session_id="browser-session", enabled=True, tab_id=TAB_A
    )
    assert enabled.enabled is True
    service.ask(
        request=ConversationRequest("en", "Next question", web_mode="local_only", web_tab_id=TAB_A),
        session_id="browser-session",
    )
    submitted = controller.submitted[-1]
    assert submitted.web_mode == "request_web"
    assert submitted.web_session_id == f"browser-session.{TAB_A}"

    service.ask(
        request=ConversationRequest("en", "Other tab", web_mode="request_web", web_tab_id=TAB_B),
        session_id="browser-session",
    )
    assert controller.submitted[-1].web_mode == "local_only"

    service.clear(session_id="browser-session")
    assert (
        service.web_mode_status(locale="en", session_id="browser-session", tab_id=TAB_A).enabled
        is True
    )
    assert (
        service.web_mode_status(locale="en", session_id="browser-session", tab_id=TAB_B).enabled
        is False
    )

    disabled = service.set_web_mode(
        locale="en", session_id="browser-session", enabled=False, tab_id=TAB_A
    )
    assert disabled.enabled is False


def test_service_keeps_context_and_clear_private_to_one_tab_and_locale() -> None:
    controller = _Controller()
    store = ConversationContextStore()
    service = _service(controller, store)

    for tab_id, question in ((TAB_A, "First tab"), (TAB_B, "Second tab"), (TAB_A, "Follow up")):
        service.ask(
            request=ConversationRequest("en", question, web_tab_id=tab_id),
            session_id="browser-session",
        )

    first_context, second_context, first_follow_up = (
        request.session_id for request in controller.submitted
    )
    assert first_context is not None
    assert second_context is not None
    assert first_context != second_context
    assert first_follow_up == first_context

    assert service.clear(session_id="browser-session", locale="en", tab_id=TAB_A) is True
    try:
        store.snapshot(session_id=first_context, locale="en", bpm_version="0.9.3")
    except ConversationContextUnavailable as error:
        assert error.code == "assistant_session_unavailable"
    else:
        raise AssertionError("tab-specific Clear must remove only its tab context")
    assert store.snapshot(session_id=second_context, locale="en", bpm_version="0.9.3").turns == ()


def test_training_service_is_session_private_and_only_returns_the_release_notice() -> None:
    service = TrainingDocumentationAssistantService()

    status = service.status(locale="ru", session_id="browser-a")
    assert status.assistant_ready is True
    assert status.reason_code == "assistant_training_notice"
    admission = service.ask(
        request=ConversationRequest("ru", "Что умеет помощник?"), session_id="browser-a"
    )
    assert admission.request_id is not None
    assert service.events(request_id=admission.request_id, session_id="browser-b") is None
    events = tuple(service.events(request_id=admission.request_id, session_id="browser-a") or ())
    assert [event.state for event in events] == ["accepted", "answer"]
    assert "обучение" in events[-1].text
    assert service.cancel(request_id=admission.request_id, session_id="browser-b") is False
    assert service.cancel(request_id=admission.request_id, session_id="browser-a") is True
    assert (
        service.web_mode_status(locale="ru", session_id="browser-a").reason_code
        == "assistant_web_disabled"
    )
    assert (
        service.set_web_mode(locale="ru", session_id="browser-a", enabled=True).available is False
    )
    assert (
        service.source(
            request_id=admission.request_id, source_id="anything", session_id="browser-a"
        )
        is None
    )
    assert service.clear(session_id="browser-a") is True
    assert service.events(request_id=admission.request_id, session_id="browser-a") is None


def test_training_service_bounds_expired_and_shutdown_request_ownership() -> None:
    now = 0.0
    service = TrainingDocumentationAssistantService(
        request_retention_seconds=5.0,
        max_requests=2,
        clock=lambda: now,
    )
    first = service.ask(request=ConversationRequest("en", "first"), session_id="browser-a")
    second = service.ask(request=ConversationRequest("en", "second"), session_id="browser-b")
    third = service.ask(request=ConversationRequest("en", "third"), session_id="browser-c")

    assert first.request_id is not None
    assert second.request_id is not None
    assert third.request_id is not None
    assert service.events(request_id=first.request_id, session_id="browser-a") is None
    assert service.events(request_id=second.request_id, session_id="browser-b") is not None
    assert len(service._requests) == 2

    now = 5.0
    assert service.events(request_id=second.request_id, session_id="browser-b") is None
    assert service.shutdown() == 0

    fourth = service.ask(request=ConversationRequest("en", "fourth"), session_id="browser-d")
    assert fourth.request_id is not None
    assert service.shutdown() == 1
    assert service.shutdown() == 0


def test_controller_service_prunes_ownership_when_a_context_or_request_expires() -> None:
    controller = _Controller()
    now = 0.0
    store = ConversationContextStore(
        idle_ttl_seconds=5.0, absolute_ttl_seconds=100.0, clock=lambda: now
    )
    service = _service(controller, store)
    admission = service.ask(request=ConversationRequest("en", "question"), session_id="browser")
    assert admission.request_id == "request-1"
    assert service._request_owners and service._context_sessions

    now = 5.0
    assert service.events(request_id="request-1", session_id="browser") is not None
    assert not service._context_sessions


def test_controller_service_drops_request_ownership_when_controller_retention_ends() -> None:
    class _ExpiredController(_Controller):
        def retains(self, request_id: str) -> bool:
            return False

    service = _service(_ExpiredController(), ConversationContextStore())
    admission = service.ask(request=ConversationRequest("en", "question"), session_id="browser")
    assert admission.request_id == "request-1"
    assert service._request_owners

    assert service.cancel(request_id="request-1", session_id="browser") is None
    assert not service._request_owners


class _RejectedController(_Controller):
    def submit(self, request: ConversationRequest) -> ConversationAdmission:
        self.submitted.append(request)
        return ConversationAdmission(None, "rejected", "assistant_busy", 4)


def test_controller_service_fails_closed_for_admission_web_state_and_source_resolution() -> None:
    controller = _RejectedController()
    store = ConversationContextStore()
    service = _service(controller, store)

    rejected = service.ask(request=ConversationRequest("en", "question"), session_id="browser")
    assert rejected.request_id is None
    assert store.clear_all() == 0
    assert (
        service.web_mode_status(locale="en", session_id="browser").reason_code
        == "assistant_web_disabled"
    )
    assert (
        service.set_web_mode(locale="en", session_id="browser", enabled=True).reason_code
        == "assistant_web_disabled"
    )

    available = WebEvidenceModeStore(configuration=WebEvidenceConfiguration(True, "token"))
    checked = _service(_Controller(), ConversationContextStore(), available)
    assert (
        checked.web_mode_status(locale="en", session_id="browser", tab_id="bad").reason_code
        == "assistant_web_mode_invalid"
    )
    assert (
        checked.set_web_mode(
            locale="en", session_id="browser", enabled=True, tab_id="bad"
        ).reason_code
        == "assistant_web_mode_invalid"
    )

    class InvalidMode:
        def status(self, **_: object) -> object:
            return object()

        def set_enabled(self, **_: object) -> object:
            return type(
                "Bad", (), {"enabled": 1, "available": True, "reason_code": "", "state_epoch": -1}
            )()

        def is_enabled(self, **_: object) -> bool:
            return False

    invalid = _service(_Controller(), ConversationContextStore(), InvalidMode())  # type: ignore[arg-type]
    assert (
        invalid.web_mode_status(locale="en", session_id="browser").reason_code
        == "assistant_web_mode_unavailable"
    )
    assert (
        invalid.set_web_mode(locale="en", session_id="browser", enabled=True).reason_code
        == "assistant_web_mode_unavailable"
    )

    controller = _Controller()
    unresolved = ControllerDocumentationAssistantService(
        controller=controller,  # type: ignore[arg-type]
        context_store=ConversationContextStore(),
        diagnostics=_Diagnostics(
            AssistantDiagnostics(
                "offline", False, True, True, True, True, "ready", "idle", "none", "local_only"
            )
        ),  # type: ignore[arg-type]
        bpm_version="0.9.3",
        source_resolver=lambda _: None,
    )
    assert (
        unresolved.status(locale="en", session_id="browser").action_key == "assistant_manage_model"
    )
    admitted = unresolved.ask(request=ConversationRequest("en", "question"), session_id="browser")
    assert admitted.request_id == "request-1"
    assert (
        unresolved.source(request_id="request-1", source_id="source-1", session_id="browser")
        is None
    )
    assert (
        unresolved.source(request_id="unknown", source_id="source-1", session_id="browser") is None
    )


def test_service_stream_disconnects_only_when_no_terminal_event(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    controller = _Controller()
    controller._events = []
    service = _service(controller, ConversationContextStore())
    admitted = service.ask(request=ConversationRequest("en", "question"), session_id="browser")
    assert admitted.request_id == "request-1"
    values = iter((0.0, 0.0, 99_999.0))
    monkeypatch.setattr("app.documentation.assistant_service.time.monotonic", lambda: next(values))
    monkeypatch.setattr("app.documentation.assistant_service.time.sleep", lambda _: None)
    assert tuple(service.events(request_id="request-1", session_id="browser") or ()) == ()
    assert controller.cancelled == ["request-1"]


def test_controller_service_handles_context_races_and_all_ownership_fallbacks() -> None:
    with pytest.raises(ValueError, match="bpm_version"):
        ControllerDocumentationAssistantService(
            controller=_Controller(),  # type: ignore[arg-type]
            context_store=ConversationContextStore(),
            diagnostics=_Diagnostics(
                AssistantDiagnostics(
                    "ready", True, True, True, True, True, "ready", "idle", "none", "local_only"
                )
            ),  # type: ignore[arg-type]
            bpm_version="",
            source_resolver=lambda _: None,
        )

    class RaceStore(ConversationContextStore):
        def snapshot(self, **kwargs: object):  # type: ignore[no-untyped-def,override]
            raise ConversationContextUnavailable("assistant_session_unavailable")

    accepted = _service(_Controller(), RaceStore())
    admission = accepted.ask(request=ConversationRequest("en", "question"), session_id="browser")
    assert admission.request_id == "request-1"
    assert accepted.cancel(request_id="request-1", session_id="other") is None
    assert accepted.cancel(request_id="request-1", session_id="browser") is True
    assert (
        accepted.source(request_id="request-1", source_id="missing", session_id="browser") is None
    )

    # A second rejected admission reuses an existing context.  It must not clear that context.
    controller = _Controller()
    service = _service(controller, ConversationContextStore())
    service.ask(request=ConversationRequest("en", "first"), session_id="browser")
    controller.submit = lambda request: ConversationAdmission(None, "rejected", "assistant_busy", 2)  # type: ignore[method-assign]
    rejected = service.ask(request=ConversationRequest("en", "second"), session_id="browser")
    assert rejected.request_id is None
    assert service.clear(session_id="other") is True

    # A concurrent clear may remove a just-created context before rejected admission cleanup.
    racing_controller = _Controller()
    racing = _service(racing_controller, ConversationContextStore())

    def reject_after_concurrent_clear(_: ConversationRequest) -> ConversationAdmission:
        racing._context_sessions.clear()
        return ConversationAdmission(None, "rejected", "assistant_busy", 2)

    racing_controller.submit = reject_after_concurrent_clear  # type: ignore[method-assign]
    assert (
        racing.ask(request=ConversationRequest("en", "raced"), session_id="browser").request_id
        is None
    )

    training = TrainingDocumentationAssistantService()
    training.ask(request=ConversationRequest("en", "first"), session_id="a")
    training.ask(request=ConversationRequest("en", "second"), session_id="b")
    assert training.clear(session_id="a") is True


def test_safe_web_mode_status_keeps_available_disabled_state() -> None:
    status = ControllerDocumentationAssistantService._safe_web_mode_status(
        type(
            "State",
            (),
            {"enabled": False, "available": True, "reason_code": "web_ready", "state_epoch": 4},
        )(),
        "en",
    )
    assert status.enabled is False and status.available is True and status.state_epoch == 4
