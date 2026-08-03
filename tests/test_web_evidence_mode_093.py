from __future__ import annotations

from app.documentation.web_evidence_consent import (
    WebEvidenceConfiguration,
    WebEvidenceModeStore,
)


def test_release_web_mode_is_off_by_default_and_retained_until_explicitly_disabled() -> None:
    store = WebEvidenceModeStore(
        configuration=WebEvidenceConfiguration(True, "server-only-token")
    )

    initial = store.status(session_id="browser-session", locale="ru")
    assert (initial.enabled, initial.available, initial.state_epoch) == (False, True, 0)

    enabled = store.set_enabled(
        session_id="browser-session", locale="ru", enabled=True
    )
    assert (enabled.enabled, enabled.reason_code, enabled.state_epoch) == (
        True,
        "assistant_web_enabled",
        1,
    )
    assert store.is_enabled(session_id="browser-session", locale="ru")
    assert not store.is_enabled(session_id="browser-session", locale="de")
    assert store.status(session_id="browser-session", locale="ru").enabled

    unchanged = store.set_enabled(
        session_id="browser-session", locale="ru", enabled=True
    )
    assert unchanged.state_epoch == 1

    disabled = store.set_enabled(
        session_id="browser-session", locale="ru", enabled=False
    )
    assert (disabled.enabled, disabled.reason_code, disabled.state_epoch) == (
        False,
        "assistant_web_disabled_by_reader",
        2,
    )
    assert not store.is_enabled(session_id="browser-session", locale="ru")


def test_release_web_mode_cannot_enable_without_administrator_configuration() -> None:
    disabled = WebEvidenceModeStore(configuration=WebEvidenceConfiguration())
    missing_token = WebEvidenceModeStore(
        configuration=WebEvidenceConfiguration(True)
    )

    assert disabled.set_enabled(
        session_id="browser-session", locale="en", enabled=True
    ).reason_code == "assistant_web_disabled"
    unavailable = missing_token.set_enabled(
        session_id="browser-session", locale="en", enabled=True
    )
    assert (unavailable.enabled, unavailable.available) == (False, False)
    assert unavailable.reason_code == "assistant_web_credential_unavailable"
