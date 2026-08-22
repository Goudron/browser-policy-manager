"""Locale-equivalence contract for the delivered BPM096 profile workflow."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
DITA_ROOT = REPO_ROOT / "documentation" / "src" / "dita"
LOCALES = ("ru", "de", "zh-CN", "fr", "es-ES")
_AFFECTED_TOPICS = {
    "user": (
        "ug-task-configure-browser-access-defaults",
        "ug-task-configure-security-privacy",
        "ug-task-configure-users-addons-sites",
        "ug-task-create-first-profile",
        "ug-task-duplicate-profile",
        "ug-task-use-all-settings",
        "ug-task-use-guided-editor",
        "ug-task-use-json-editor",
        "ug-troubleshoot-policy-validation",
        "ug-troubleshoot-profile-name",
        "ug-troubleshoot-schema-mismatch",
    ),
    "firefox": (
        "fx-concept-complex-policy-families",
        "fx-concept-policy-selection",
        "fx-concept-release-esr-differences",
        "fx-concept-starter-presets",
        "fx-task-review-complex-policy-configuration",
    ),
    "cis": (
        "cis-concept-manual-review-exceptions",
        "cis-concept-presets-layers-merge",
        "cis-task-run-level-1-workflow",
        "cis-task-run-level-2-hardened-workflow",
        "cis-task-select-cis-baseline",
        "cis-task-trace-cis-source",
        "cis-task-verify-cis-deviation",
    ),
    "admin": (
        "admin-concept-api-conventions",
        "admin-concept-api-limitations",
        "admin-task-sync-profile-lifecycle",
        "admin-task-use-reusable-api-examples",
    ),
}
_FULLY_REWRITTEN_OR_DIRECTLY_ALIGNED = {
    ("user", "ug-task-configure-browser-access-defaults"),
    ("user", "ug-task-configure-security-privacy"),
    ("user", "ug-task-configure-users-addons-sites"),
    ("user", "ug-task-create-first-profile"),
    ("user", "ug-task-duplicate-profile"),
    ("user", "ug-task-use-all-settings"),
    ("user", "ug-task-use-guided-editor"),
    ("user", "ug-task-use-json-editor"),
    ("firefox", "fx-concept-complex-policy-families"),
    ("cis", "cis-concept-presets-layers-merge"),
    ("admin", "admin-concept-api-conventions"),
}

_GUIDED_STEP_WORD = {
    "ru": "восемь",
    "de": "acht",
    "zh-CN": "八",
    "fr": "huit",
    "es-ES": "ocho",
}
_FORBIDDEN_DRAFT_WORDS = {
    "ru": ("черновик",),
    "de": ("entwurf",),
    "zh-CN": ("草稿",),
    "fr": ("brouillon",),
    "es-ES": ("borrador",),
}


def _topic(locale: str, guide: str, topic: str) -> str:
    path = DITA_ROOT / locale / guide / f"{topic}.dita"
    ET.parse(path)
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("locale", LOCALES)
def test_every_affected_localized_peer_has_the_bpm096_delivery_record(locale: str) -> None:
    for guide, topics in _AFFECTED_TOPICS.items():
        for topic in topics:
            text = _topic(locale, guide, topic)
            if (guide, topic) not in _FULLY_REWRITTEN_OR_DIRECTLY_ALIGNED:
                assert 'id="bpm096-localized-current"' in text


@pytest.mark.parametrize("locale", LOCALES)
def test_localized_primary_workflow_has_no_fallback_or_preparation_draft(locale: str) -> None:
    create = _topic(locale, "user", "ug-task-create-first-profile")
    duplicate = _topic(locale, "user", "ug-task-duplicate-profile")
    guided = _topic(locale, "user", "ug-task-use-guided-editor")
    combined = (create + duplicate + guided).casefold()

    assert "CIS" in create
    assert "CIS" in duplicate
    assert "Guided editor" not in create
    assert "Guided editor" not in duplicate
    assert _GUIDED_STEP_WORD[locale] in guided.casefold()
    assert "AMO" in guided and "GUID" in guided and "URL" in guided
    for forbidden in _FORBIDDEN_DRAFT_WORDS[locale]:
        assert forbidden not in combined


@pytest.mark.parametrize("locale", LOCALES)
def test_localized_cross_guide_owners_cover_amo_cis_and_public_recovery(locale: str) -> None:
    firefox = _topic(locale, "firefox", "fx-concept-complex-policy-families")
    cis = _topic(locale, "cis", "cis-concept-presets-layers-merge")
    api = _topic(locale, "admin", "admin-concept-api-conventions")

    for identifier in ("AMO", "GUID", "XPI", "URL"):
        assert identifier in firefox
    for identifier in ("CIS", "baseline", "manual", "imported", "converted", "raw"):
        assert identifier in cis
    for endpoint in (
        "POST /api/profiles/prepare/new",
        "POST /api/profiles/prepare/duplicate",
        "POST /api/profiles/prepare/duplicate/preview",
        "ProfilePreparationErrorEnvelope",
        'mutation="none"',
    ):
        assert endpoint in api
