from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "app/documentation/manifest.py"
REVIEW = ROOT / "docs/architecture/context-help-gap-review-0.9.2.md"
MAP = ROOT / "docs/architecture/ui-copy-documentation-disposition-map-0.9.2.md"
DITA_ROOT = ROOT / "documentation/src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
SURFACE_TARGETS = {
    "library": "topic:ug-task-use-profile-library",
    "compare": "topic:ug-task-compare-profiles",
    "guided": "topic:ug-task-use-guided-editor",
    "settings": "topic:ug-task-use-all-settings",
    "json": "topic:ug-task-use-json-editor",
}
DEEP_TARGETS = {
    "preparation-create": "topic:ug-task-create-first-profile",
    "preparation-duplicate": "topic:ug-task-duplicate-profile",
    "guided-urls-sites-navigation": "policy:Homepage",
    "guided-certificates-trust": "policy:Certificates",
    "guided-extensions": "policy:ExtensionSettings",
    "policy-ai-controls": "policy:AIControls",
    "policy-visual-search-enabled": "policy:VisualSearchEnabled",
    "cis-baseline-selection": "cis:1.1.1.1",
    "validation": "topic:ug-task-validate-profile",
    "import-firefox-policies": "topic:ug-task-import-policies-json",
    "export-firefox-policies": "topic:ug-task-export-policies-json",
}

pytestmark = pytest.mark.docs_contract


def _manifest_constant(name: str) -> dict[str, str]:
    module = ast.parse(MANIFEST.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                return ast.literal_eval(node.value)
    raise AssertionError(f"Missing manifest constant: {name}")


def test_gap_review_authorizes_no_new_context_help_until_a_proven_ambiguity() -> None:
    review = REVIEW.read_text(encoding="utf-8")
    disposition_map = MAP.read_text(encoding="utf-8")

    assert "No new contextual-help topic or circled-info link is approved" in review
    assert "only when it records the exact source control" in review
    assert "no new topic or circled-info control is authorized" in disposition_map


def test_existing_context_help_targets_cover_the_approved_m2_boundaries() -> None:
    assert _manifest_constant("DOCUMENTATION_CONTEXTUAL_HELP_TARGET_IDS") == SURFACE_TARGETS
    assert _manifest_constant("DOCUMENTATION_DEEP_HELP_TARGET_IDS") == DEEP_TARGETS


def test_existing_topic_targets_have_every_locale_peer() -> None:
    topic_ids = {
        target.removeprefix("topic:")
        for target in (*SURFACE_TARGETS.values(), *DEEP_TARGETS.values())
        if target.startswith("topic:")
    }

    for locale in LOCALES:
        for topic_id in topic_ids:
            matches = list((DITA_ROOT / locale).rglob(f"{topic_id}.dita"))
            assert len(matches) == 1, (locale, topic_id, matches)
