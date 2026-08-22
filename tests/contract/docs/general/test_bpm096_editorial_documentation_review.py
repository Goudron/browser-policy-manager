"""Focused source-review contract for BPM096-M10-05."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from tests.docs_index import doc_path_from_index

ROOT = Path(__file__).resolve().parents[4]
DITA = ROOT / "documentation" / "src" / "dita"
WIZARD_CATALOGS = ROOT / "app" / "i18n_src"
REVIEW = ROOT / "docs" / "architecture" / "profile-documentation-editorial-review-0.9.6.md"
BACKLOG = ROOT / "docs" / "bpm_0_9_6_profile_creation_guided_editor_backlog_2026-08-20.md"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
GUIDES = (
    "user-guide",
    "firefox-policy-guide",
    "cis-settings-guide",
    "administrator-guide",
)
STEP_MARKERS = {
    "en": ("Step 1", "Step 2", "Step 4", "Step 6", "Step 7"),
    "ru": ("шаг 1", "шаг 2", "шаг 4", "шаг 6", "шаг 7"),
    "de": ("Schritt 1", "Schritt 2", "Schritt 4", "Schritt 6", "Schritt 7"),
    "zh-CN": ("步骤 1", "步骤 2", "步骤 4", "步骤 6", "步骤 7"),
    "fr": ("étape 1", "étape 2", "étape 4", "étape 6", "étape 7"),
    "es-ES": ("paso 1", "paso 2", "paso 4", "paso 6", "paso 7"),
}
DRAFT_MARKERS = ("draft", "черновик", "entwurf", "草稿", "brouillon", "borrador")
GUIDED_STEP_KEYS = (
    "profiles.wizard_step_one",
    "profiles.wizard_step_two",
    "profiles.wizard_step_three",
    "profiles.wizard_step_four",
    "profiles.wizard_step_five",
    "profiles.wizard_step_six",
    "profiles.wizard_step_seven",
    "profiles.wizard_step_eight",
)


def _topic(locale: str, guide: str, topic: str) -> tuple[ET.Element, str]:
    path = DITA / locale / guide / f"{topic}.dita"
    root = ET.parse(path).getroot()
    return root, " ".join("".join(root.itertext()).split())


def _map_keyrefs(locale: str, guide: str) -> list[str]:
    root = ET.parse(DITA / locale / "maps" / f"{guide}.ditamap").getroot()
    return [element.attrib["keyref"] for element in root.findall(".//topicref")]


def _catalog(locale: str) -> dict[str, str]:
    return json.loads((WIZARD_CATALOGS / locale / "wizard.json").read_text(encoding="utf-8"))


def _uicontrol_text(elements: list[ET.Element]) -> list[str]:
    return ["".join(element.itertext()) for element in elements]


def test_review_is_indexed_backlog_linked_and_records_full_editorial_scope() -> None:
    assert (
        doc_path_from_index(
            "architecture/profile-documentation-editorial-review-0.9.6.md", status="active"
        )
        == REVIEW
    )
    source = REVIEW.read_text(encoding="utf-8")
    for required in (
        "BPM096-M10-05",
        "Every published guide is affected. No guide is untouched",
        "Microsoft Writing Style Guide",
        "Pontoon",
        "SUMO",
        "app/i18n_src/{locale}/wizard.json",
        "30 newly captured localized source PNGs",
        "not-reviewed` rendered visual acceptance",
        "Search and documentation assistant remain separate",
        "Chinese heading guard no longer rejects `配置文件`",
        "site and PDF candidate work remain M10-07 and M10-08",
    ):
        assert required in source
    assert "### BPM096-M10-05" in BACKLOG.read_text(encoding="utf-8")


def test_all_localized_guide_maps_preserve_the_same_reachable_current_topics() -> None:
    expected = {
        "user-guide": {
            "topic.ug-task-create-first-profile",
            "topic.ug-task-duplicate-profile",
            "topic.ug-task-use-guided-editor",
            "topic.ug-concept-documentation-search-boundary",
            "topic.ug-task-use-local-documentation-assistant",
        },
        "firefox-policy-guide": {"topic.fx-concept-complex-policy-families"},
        "cis-settings-guide": {
            "topic.cis-task-select-cis-baseline",
            "topic.cis-task-run-level-2-hardened-workflow",
        },
        "administrator-guide": {"topic.admin-task-sync-profile-lifecycle"},
    }
    for guide in GUIDES:
        english = _map_keyrefs("en", guide)
        assert expected[guide] <= set(english)
        for locale in LOCALES[1:]:
            assert _map_keyrefs(locale, guide) == english


def test_reviewed_sources_have_one_current_guided_owner_and_no_draft_lifecycle() -> None:
    required_literals = {"ExtensionSettings", "SecurityDevices", "AIControls.SmartWindow"}
    for locale in LOCALES:
        _, home = _topic(locale, "user", "ug-task-configure-home-search-navigation")
        complex_root, complex_policy = _topic(
            locale, "firefox", "fx-concept-complex-policy-families"
        )
        _, cis_selection = _topic(locale, "cis", "cis-task-select-cis-baseline")
        _, cis_level_2 = _topic(locale, "cis", "cis-task-run-level-2-hardened-workflow")
        combined = "\n".join((home, complex_policy, cis_selection, cis_level_2)).casefold()

        assert "SearchEngines" in complex_policy
        assert all(literal in complex_policy for literal in required_literals)
        assert all(
            section.attrib["id"] != "bpm096-delivered-workflow"
            for section in complex_root.findall(".//section")
        )
        assert all(
            marker.casefold() in complex_policy.casefold() for marker in STEP_MARKERS[locale]
        )
        assert not any(marker in combined for marker in DRAFT_MARKERS)


def test_guided_step_ui_labels_follow_the_same_locale_runtime_catalog_keys() -> None:
    for locale in LOCALES:
        catalog = _catalog(locale)
        guided_root, _ = _topic(locale, "user", "ug-task-use-guided-editor")
        complex_root, _ = _topic(locale, "firefox", "fx-concept-complex-policy-families")

        expected = [catalog[key] for key in GUIDED_STEP_KEYS]
        assert _uicontrol_text(guided_root.findall(".//steps/step/cmd/uicontrol")) == expected
        assert _uicontrol_text(complex_root.findall(".//section/p/uicontrol")) == [
            expected[5],
            expected[3],
            expected[6],
        ]

        figure_title = guided_root.find(".//fig[@id='screenshot-guided-step-6-extensions']/title")
        assert figure_title is not None
        assert "".join(figure_title.itertext()) == expected[5]


def test_review_records_locale_specific_pontoon_and_sumo_evidence() -> None:
    source = REVIEW.read_text(encoding="utf-8")
    for locale in ("ru", "de", "zh-CN", "fr", "es-ES"):
        assert f"https://pontoon.mozilla.org/{locale}/firefox/" in source
    for required in (
        "support.mozilla.org/ru/",
        "support.mozilla.org/de/",
        "support.mozilla.org/zh-CN/",
        "support.mozilla.org/fr/",
        "support.mozilla.org/es/",
        "https://pontoon.mozilla.org/projects/firefox/",
    ):
        assert required in source
