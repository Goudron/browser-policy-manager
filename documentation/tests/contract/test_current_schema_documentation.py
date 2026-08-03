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
