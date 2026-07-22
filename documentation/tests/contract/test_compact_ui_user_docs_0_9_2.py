from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DITA_ROOT = ROOT / "documentation/src/dita"
REVIEW = ROOT / "docs/architecture/compact-ui-user-documentation-review-0.9.2.md"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")

pytestmark = pytest.mark.docs_contract


def _topic(locale: str, topic_id: str) -> str:
    path = DITA_ROOT / locale / "user" / f"{topic_id}.dita"
    return " ".join(ET.parse(path).getroot().itertext())


def test_compact_ui_guidance_exists_in_all_active_locales() -> None:
    for locale in LOCALES:
        version = _topic(locale, "ug-reference-product-version")
        library = _topic(locale, "ug-task-use-profile-library")
        switcher = _topic(locale, "ug-task-switch-editor-mode")
        surfaces = _topic(locale, "ug-concept-choose-editor-surface")

        assert version.strip(), locale
        assert library.strip(), locale
        assert switcher.strip(), locale
        assert surfaces.strip(), locale
        assert len(ET.parse(DITA_ROOT / locale / "user" / "ug-task-use-profile-library.dita").findall(".//step")) == 3


def test_english_guidance_uses_single_bpm_version_and_compact_library_order() -> None:
    version = _topic("en", "ug-reference-product-version")
    library = _topic("en", "ug-task-use-profile-library")
    switcher = _topic("en", "ug-task-switch-editor-mode")
    surfaces = _topic("en", "ug-concept-choose-editor-surface")

    assert "no separate visible version" in version
    assert "Firefox ESR 140.13 and Firefox Release 153" in version
    assert "action grid comes first" in library
    assert "immediately above the profile table" in library
    assert "compact shared context" in switcher
    assert "Guided, All settings, and JSON" in switcher
    assert "Library, Guided editor, All settings, JSON editor, and Compare" in surfaces


def test_compact_ui_screenshot_evidence_is_recaptured_for_refresh() -> None:
    review = REVIEW.read_text(encoding="utf-8")

    assert "`BPM092-M11-03`" in review
    assert review.count("recaptured M11-03") == 5
    for key in (
        "screenshot.library-overview",
        "screenshot.guided-editor-overview",
        "screenshot.all-settings-review",
        "screenshot.json-editor",
        "screenshot.compare-profiles",
    ):
        assert f"`{key}`" in review
