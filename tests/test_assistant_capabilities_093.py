from __future__ import annotations

import pytest

from app.documentation import assistant_capabilities
from app.documentation.conversation import ConversationRequest


def test_capability_answer_fails_closed_for_unsupported_and_incomplete_copy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert assistant_capabilities.capability_answer(
        ConversationRequest("unsupported", "What can you answer?")
    ) is None

    monkeypatch.delitem(assistant_capabilities._ANSWERS, "en")  # type: ignore[attr-defined]

    assert assistant_capabilities.capability_answer(
        ConversationRequest("en", "What can you answer?")
    ) is None


def test_capability_answer_requires_a_nonempty_reviewed_alias() -> None:
    assert assistant_capabilities.capability_answer(ConversationRequest("ru", "  \t ")) is None
    outcome = assistant_capabilities.capability_answer(
        ConversationRequest("ru", "На какие вопросы ты можешь отвечать?")
    )

    assert outcome is not None
    assert outcome.reason_code == "assistant_capability_answer"
    assert outcome.citations[0].citation_id.endswith("#assistant")
