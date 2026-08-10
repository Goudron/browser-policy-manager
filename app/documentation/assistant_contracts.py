"""Runtime-free transport contracts for the release documentation assistant.

The default BPM assembly exposes the training-notice assistant without loading the optional local
model/RAG implementation. These data-only types are shared by that release surface and the
incubating implementation, so importing an API router cannot pull native runtime dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Literal

API_VERSION = 1
SUPPORTED_LOCALES: Final[tuple[str, ...]] = ("en", "ru", "de", "zh-CN", "fr", "es-ES")

WebMode = Literal["local_only", "request_web"]
EventType = Literal["accepted", "progress", "final", "cancelled", "error"]
RequestState = Literal[
    "accepted",
    "scope_check",
    "evidence_check",
    "generating",
    "validating",
    "answer",
    "clarify",
    "abstain",
    "refuse",
    "cancelled",
    "error",
]


@dataclass(frozen=True)
class DialogueTurn:
    """One controller-owned prior turn; it never contains client-provided evidence."""

    role: Literal["user", "assistant"]
    text: str


@dataclass(frozen=True)
class ConversationRequest:
    """Bounded same-origin request data shared by release and incubation assemblies."""

    locale: str
    question: str
    web_mode: WebMode = "local_only"
    dialogue: tuple[DialogueTurn, ...] = ()
    session_id: str | None = None
    web_session_id: str | None = None
    web_tab_id: str | None = None
    timing_context_characters: int = 0
    timing_evidence_tokens: int = 2_048


@dataclass(frozen=True)
class ConversationTimePreview:
    """A display-safe, locale-neutral inclusive range in whole seconds."""

    minimum_seconds: int
    maximum_seconds: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.minimum_seconds, int)
            or not isinstance(self.maximum_seconds, int)
            or self.minimum_seconds < 1
            or self.maximum_seconds < self.minimum_seconds
        ):
            raise ValueError("invalid local response-time range")


@dataclass(frozen=True)
class ConversationStreamExternalClaim:
    """One external claim with request-opaque citation handles."""

    text: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class ConversationStreamEvent:
    """A display-safe, transport-ready event; source IDs are opaque server handles."""

    event_type: EventType
    request_id: str
    state: RequestState
    state_epoch: int
    reason_code: str
    message_key: str
    action_key: str
    disposition: str | None = None
    text: str = ""
    source_ids: tuple[str, ...] = ()
    incomplete: bool = False
    api_version: int = API_VERSION
    external_claims: tuple[ConversationStreamExternalClaim, ...] = ()


@dataclass(frozen=True)
class ConversationAdmission:
    """The safe result of accepting, queueing, or refusing a chat request."""

    request_id: str | None
    state: RequestState
    reason_code: str
    state_epoch: int
    api_version: int = API_VERSION
    time_preview: ConversationTimePreview = field(
        default_factory=lambda: ConversationTimePreview(60, 900)
    )
