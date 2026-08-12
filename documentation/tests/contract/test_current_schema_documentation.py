"""Keep published guides aligned with the current Firefox schema matrix."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DITA_ROOT = ROOT / "documentation" / "src" / "dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
CURRENT_CHANNELS = ("ESR 140.13", "ESR 153.0", "Release 153")
RETIRED_CHANNEL = re.compile(r"(?:Firefox[ -])?152\b", re.IGNORECASE)
M8_ENGLISH_SOURCE_TOPICS = (
    "user/ug-task-choose-profile-identity-schema.dita",
    "user/ug-concept-schema-aware-behavior.dita",
    "user/ug-task-choose-firefox-schema.dita",
    "user/ug-task-compare-profiles.dita",
    "user/ug-task-use-all-settings.dita",
    "user/ug-task-use-guided-editor.dita",
    "user/ug-task-use-json-editor.dita",
    "user/ug-task-use-profile-library.dita",
    "user/ug-troubleshoot-schema-mismatch.dita",
    "firefox/fx-concept-release-esr-differences.dita",
    "firefox/fx-concept-policy-selection.dita",
    "cis/cis-concept-levels-channels-layers.dita",
    "cis/cis-task-select-cis-baseline.dita",
    "admin/admin-concept-api-conventions.dita",
    "admin/admin-task-use-reusable-api-examples.dita",
    "admin/admin-task-run-source-update-migrations-docs.dita",
    "admin/admin-task-manage-profile-retirement.dita",
    "admin/admin-task-validate-firefox-policies-json.dita",
    "admin/admin-troubleshoot-database-storage.dita",
    "admin/admin-troubleshoot-import-export-failures.dita",
    "admin/admin-troubleshoot-schema-cache-validation.dita",
)

pytestmark = pytest.mark.docs_contract


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_published_dita_does_not_describe_the_retired_firefox_152_channel() -> None:
    for locale in LOCALES:
        for topic in sorted((DITA_ROOT / locale).rglob("*.dita")):
            assert not RETIRED_CHANNEL.search(_text(topic)), topic.relative_to(ROOT)


@pytest.mark.parametrize("locale", LOCALES)
def test_user_schema_topics_name_every_current_channel(locale: str) -> None:
    for topic_name in (
        "ug-reference-product-version.dita",
        "ug-concept-schema-aware-behavior.dita",
        "ug-task-choose-firefox-schema.dita",
        "ug-task-choose-profile-identity-schema.dita",
        "ug-troubleshoot-schema-mismatch.dita",
    ):
        topic = DITA_ROOT / locale / "user" / topic_name
        source = _text(topic)
        for channel in CURRENT_CHANNELS:
            assert channel in source, (locale, topic_name, channel)


@pytest.mark.parametrize("locale", LOCALES)
def test_cis_guidance_distinguishes_product_schema_support_from_generated_layers(
    locale: str,
) -> None:
    topic = DITA_ROOT / locale / "cis" / "cis-concept-levels-channels-layers.dita"
    source = _text(topic)

    for channel in CURRENT_CHANNELS:
        assert channel in source, (locale, channel)
    assert "cis-l1.esr-140.13" in source
    assert "cis-l1.release-153" in source


def test_english_m8_sources_cover_current_lifecycle_api_and_safe_recovery_boundaries() -> None:
    """Keep M8-02 current facts in English without pre-empting M8-03 localization."""
    text = "\n".join(_text(DITA_ROOT / "en" / topic) for topic in M8_ENGLISH_SOURCE_TOPICS)

    for channel in ("Release 153", "ESR 153.0", "ESR 140.13", "ESR 115.38"):
        assert channel in text

    for required in (
        "limited legacy-operating-system critical-security",
        "does not extend operating-system vendor support",
        "2027-03-01",
        "latest ESR, ESR 153.0",
        "any distinct pair of the four current artifacts",
        "Preview is read-only",
        "explicit confirmation",
        "leaves the profile unchanged",
        '{"policies":{...}}',
        "Profile ID, schema version, revision, compliance, and other BPM metadata are never members",
        "value-free detail envelope",
        "mutation=none",
        "retry_preview_required",
        "Only when a future candidate actually retires an ESR",
        "backup and read-only preflight gates",
        "new clean candidate",
        "do not repair or downgrade",
    ):
        assert required in text

    for forbidden in (
        "candidate materializer",
        "in-place repair",
        "manual conversion or downgrade procedure",
    ):
        assert forbidden not in text


@pytest.mark.parametrize("locale", LOCALES)
def test_m8_source_scope_has_exactly_21_localized_peers(locale: str) -> None:
    """Keep M8-03 strictly aligned with the complete M8-02 source scope."""
    source_topics = set(M8_ENGLISH_SOURCE_TOPICS)

    assert len(M8_ENGLISH_SOURCE_TOPICS) == len(source_topics) == 21
    assert all((DITA_ROOT / "en" / topic).is_file() for topic in source_topics)

    localized_topics = {topic for topic in source_topics if (DITA_ROOT / locale / topic).is_file()}
    assert localized_topics == source_topics


def test_m8_lifecycle_locales_keep_the_shipped_four_channel_and_conversion_contract() -> None:
    """Reject a localized M8 peer that falls back to the former three-channel scope."""
    topics = M8_ENGLISH_SOURCE_TOPICS
    for locale in LOCALES:
        text = "\n".join(_text(DITA_ROOT / locale / topic) for topic in topics)
        for required in (
            "Release 153",
            "ESR 153.0",
            "ESR 140.13",
            "ESR 115.38",
            "2027-03-01",
            "ESR 153.0",
            '{"policies":{...}}',
            "POST /api/profiles/{profile_id}/conversion-preview",
            "POST /api/profiles/{profile_id}/conversion-apply",
            "mutation=none",
            "retry_preview_required",
            "alembic upgrade head",
            "Schema channel is not available",
            "schema_channel_unknown",
        ):
            assert required in text, (locale, required)
