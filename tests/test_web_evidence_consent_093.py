from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.core.config import Settings
from app.documentation.web_evidence_consent import (
    BRAVE_PROVIDER_NAME,
    BRAVE_QUERY_LOG_RETENTION_WARNING,
    BRAVE_RECIPIENT,
    CONSENT_TTL_SECONDS,
    MAX_PENDING_CONSENTS,
    WEB_QUERY_CHARACTERS_MAX,
    WEB_QUERY_WORDS_MAX,
    WebEvidenceAuthorization,
    WebEvidenceConfiguration,
    WebEvidenceConsentStore,
    WebEvidenceModeStore,
)


@dataclass
class _Clock:
    now: float = 100.0

    def __call__(self) -> float:
        return self.now


def _store(clock: _Clock | None = None) -> WebEvidenceConsentStore:
    return WebEvidenceConsentStore(
        configuration=WebEvidenceConfiguration(True, "test-subscription-token"),
        clock=clock or _Clock(),
    )


def test_default_and_missing_byok_are_normal_local_only_states() -> None:
    disabled = WebEvidenceConsentStore(configuration=WebEvidenceConfiguration())
    missing_credential = WebEvidenceConsentStore(configuration=WebEvidenceConfiguration(True))

    assert disabled.disclose(session_id="session", locale="en", question="BPM question").reason_code == (
        "assistant_web_disabled"
    )
    assert (
        missing_credential.disclose(session_id="session", locale="en", question="BPM question").reason_code
        == "assistant_web_credential_unavailable"
    )
    assert WebEvidenceConfiguration.from_settings(Settings()).availability_code == "assistant_web_disabled"


def test_disclosure_shows_exact_query_and_required_brave_privacy_facts_without_the_key() -> None:
    question = "How do I configure Firefox policies in BPM?"
    store = _store()
    result = store.disclose(session_id="session", locale="en", question=question)

    assert result.state == "disclosure_required"
    assert result.reason_code == "assistant_web_consent_required"
    assert result.disclosure is not None
    assert result.disclosure.outgoing_query == question
    assert result.disclosure.provider == BRAVE_PROVIDER_NAME
    assert result.disclosure.recipient == BRAVE_RECIPIENT
    assert result.disclosure.query_log_retention_warning == BRAVE_QUERY_LOG_RETENTION_WARNING
    assert "test-subscription-token" not in repr(result)
    assert "test-subscription-token" not in repr(WebEvidenceConfiguration(True, "test-subscription-token"))
    assert all(not hasattr(pending, "question") for pending in store._pending.values())
    assert question not in repr(next(iter(store._pending.values())))


@pytest.mark.parametrize(
    ("locale", "language"),
    (("en", "en"), ("ru", "ru"), ("de", "de"), ("zh-CN", "zh-hans"), ("fr", "fr"), ("es-ES", "es")),
)
def test_disclosure_preserves_each_supported_locale_and_uses_its_provider_language(
    locale: str, language: str
) -> None:
    result = _store().disclose(session_id="session", locale=locale, question="BPM Firefox policy")

    assert result.disclosure is not None
    assert result.disclosure.locale == locale
    assert result.disclosure.search_language == language


def test_exact_question_session_locale_and_one_time_approval_are_required() -> None:
    store = _store()
    disclosed = store.disclose(session_id="session-a", locale="en", question="BPM Firefox policy")
    assert disclosed.disclosure is not None

    rejected = store.approve(session_id="session-b", consent_id=disclosed.disclosure.consent_id)
    assert rejected.reason_code == "assistant_web_consent_unavailable"

    approved = store.approve(session_id="session-a", consent_id=disclosed.disclosure.consent_id)
    assert approved.authorization is not None
    assert not store.consume(
        authorization=approved.authorization,
        session_id="session-a",
        locale="en",
        question="Different question",
    )
    assert not store.consume(
        authorization=approved.authorization,
        session_id="session-a",
        locale="en",
        question="BPM Firefox policy",
    )

    next_disclosure = store.disclose(session_id="session-a", locale="en", question="BPM Firefox policy")
    assert next_disclosure.disclosure is not None
    next_approval = store.approve(session_id="session-a", consent_id=next_disclosure.disclosure.consent_id)
    assert next_approval.authorization is not None
    assert store.consume(
        authorization=next_approval.authorization,
        session_id="session-a",
        locale="en",
        question="BPM Firefox policy",
    )


def test_expiry_clear_and_question_bounds_remove_any_pending_capability() -> None:
    clock = _Clock()
    store = _store(clock)
    disclosed = store.disclose(session_id="session", locale="en", question="BPM Firefox policy")
    assert disclosed.disclosure is not None
    clock.now += CONSENT_TTL_SECONDS
    assert store.approve(session_id="session", consent_id=disclosed.disclosure.consent_id).reason_code == (
        "assistant_web_consent_unavailable"
    )

    second = store.disclose(session_id="session", locale="en", question="BPM Firefox policy")
    assert second.disclosure is not None
    assert store.clear_session("session") == 1
    assert store.approve(session_id="session", consent_id=second.disclosure.consent_id).reason_code == (
        "assistant_web_consent_unavailable"
    )
    assert store.disclose(
        session_id="session", locale="en", question="x" * (WEB_QUERY_CHARACTERS_MAX + 1)
    ).reason_code == "assistant_web_consent_invalid"
    assert store.disclose(
        session_id="session", locale="en", question=" ".join("word" for _ in range(WEB_QUERY_WORDS_MAX + 1))
    ).reason_code == "assistant_web_consent_invalid"


def test_pending_consent_records_are_bounded_and_never_store_raw_questions() -> None:
    store = _store()
    for number in range(MAX_PENDING_CONSENTS):
        assert store.disclose(
            session_id=f"session-{number}", locale="en", question=f"BPM question {number}"
        ).state == "disclosure_required"

    assert store.disclose(
        session_id="one-more-session", locale="en", question="BPM one more question"
    ).reason_code == "assistant_web_consent_unavailable"
    assert all(not hasattr(pending, "question") for pending in store._pending.values())
    assert all("BPM question" not in repr(pending) for pending in store._pending.values())


def test_web_mode_validation_capacity_and_process_clear_remain_bounded() -> None:
    with pytest.raises(ValueError, match="mode bound"):
        WebEvidenceModeStore(
            configuration=WebEvidenceConfiguration(True, "server-only-token"), max_records=0
        )

    store = WebEvidenceModeStore(
        configuration=WebEvidenceConfiguration(True, "server-only-token"), max_records=1
    )
    assert store.status(session_id="", locale="en").reason_code == "assistant_web_mode_invalid"
    assert store.set_enabled(session_id="session", locale="en", enabled=1).reason_code == (  # type: ignore[arg-type]
        "assistant_web_mode_invalid"
    )
    assert store.set_enabled(session_id="first", locale="en", enabled=True).enabled is True
    assert store.set_enabled(session_id="second", locale="en", enabled=True).reason_code == (
        "assistant_web_mode_unavailable"
    )
    assert store.clear_all() == 1
    assert store.clear_all() == 0


def test_consent_store_rejects_unavailable_invalid_and_expired_capabilities() -> None:
    with pytest.raises(ValueError, match="consent TTL"):
        WebEvidenceConsentStore(
            configuration=WebEvidenceConfiguration(True, "token"), consent_ttl_seconds=0
        )

    disabled = WebEvidenceConsentStore(configuration=WebEvidenceConfiguration())
    assert disabled.approve(session_id="session", consent_id="consent").reason_code == (
        "assistant_web_disabled"
    )

    clock = _Clock()
    store = _store(clock)
    disclosure = store.disclose(session_id="session", locale="en", question="BPM Firefox policy")
    assert disclosure.disclosure is not None
    authorization = WebEvidenceAuthorization(disclosure.disclosure.consent_id, "en")
    assert store.consume(
        authorization=authorization,
        session_id="session",
        locale="en",
        question="",
    ) is False
    assert store.is_consumable(
        authorization=authorization,
        session_id="session",
        locale="en",
        question="",
    ) is False
    assert store.is_consumable(
        authorization=WebEvidenceAuthorization("missing", "en"),
        session_id="session",
        locale="en",
        question="BPM Firefox policy",
    ) is False
    assert store._require_pending_locked("") is None

    clock.now += CONSENT_TTL_SECONDS
    assert store.clear_expired() == 1
    second = store.disclose(session_id="session", locale="en", question="BPM Firefox policy")
    assert second.disclosure is not None
    assert store.clear_all() == 1
    assert store.clear_all() == 0
