"""Release guard for M11-02 reader explanations and Firefox document examples."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app.services.firefox_policy_export import render_firefox_policies_document
from app.services.firefox_policy_import import validate_firefox_policies_document

ROOT = Path(__file__).resolve().parents[3]
DITA_ROOT = ROOT / "documentation/src/dita"
README_PATH = ROOT / "README.md"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
FIREFOX_DOCUMENT = {"policies": {"DisableTelemetry": True, "BlockAboutConfig": True}}
POLICY_TOPICS = (
    ("user", "ug-task-import-policies-json"),
    ("user", "ug-task-export-policies-json"),
    ("admin", "admin-task-import-firefox-policies-json"),
    ("admin", "admin-task-export-firefox-policies-json"),
)
ASSISTANT_TOPICS = (
    ("user", "ug-concept-browser-policy-manager-overview"),
    ("user", "ug-task-use-local-documentation-assistant"),
    ("admin", "admin-reference-minimum-system-requirements"),
    ("admin", "admin-task-maintain-local-documentation-assistant"),
    ("admin", "admin-task-operate-local-documentation-assistant"),
    ("admin", "admin-task-gate-control-product-startup"),
)

pytestmark = pytest.mark.docs_contract


def _topic(locale: str, guide: str, name: str) -> ET.Element:
    return ET.parse(DITA_ROOT / locale / guide / f"{name}.dita").getroot()


def _json_codeblocks(root: ET.Element) -> list[dict[str, object]]:
    parsed = []
    for block in root.iter("codeblock"):
        if block.attrib.get("outputclass") == "language-json":
            parsed.append(json.loads(block.text or ""))
    return parsed


def test_locale_topics_document_the_exact_system_selection_rules() -> None:
    for locale in LOCALES:
        root = _topic(locale, "user", "ug-concept-language-detection-fallback")
        text = " ".join("".join(root.itertext()).split())
        lead = root.find("shortdesc")
        assert "navigator.languages" in text
        assert "navigator.language" in text
        assert "bpm-lang-mode" in text
        assert lead is not None and lead.find(".//uicontrol") is not None
        assert root.find(".//section[@id='a-system-language']") is not None
        assert root.find(".//section[@id='a-fallback']") is not None
        assert any(
            link.attrib.get("keyref") == "topic.ug-task-change-interface-language"
            for link in root.findall(".//related-links/link")
        )


def test_all_reader_import_and_export_examples_are_full_valid_firefox_documents() -> None:
    for locale in LOCALES:
        for guide, name in POLICY_TOPICS:
            documents = _json_codeblocks(_topic(locale, guide, name))
            assert len(documents) == 1, (locale, guide, name)
            for document in documents:
                assert set(document) == {"policies"}, (locale, guide, name)
                flags = validate_firefox_policies_document(document, "release-153")
                assert render_firefox_policies_document(flags) == document
    assert (
        render_firefox_policies_document({"DisableTelemetry": True, "BlockAboutConfig": True})
        == FIREFOX_DOCUMENT
    )


def test_readme_has_a_standalone_full_firefox_document_example() -> None:
    blocks = re.findall(r"```json\n(.*?)\n```", README_PATH.read_text(encoding="utf-8"), re.DOTALL)
    assert FIREFOX_DOCUMENT in [json.loads(block) for block in blocks]


def test_assistant_topics_describe_the_delivered_boundary_without_stale_release_claims() -> None:
    for locale in LOCALES:
        for guide, name in ASSISTANT_TOPICS:
            text = " ".join("".join(_topic(locale, guide, name).itertext()).split())
            assert "0.9.3" not in text
            assert "BPM" in text


def test_overview_topics_state_the_current_assistant_boundary_without_release_or_future_copy() -> (
    None
):
    future_copy = (
        "later",
        "following version",
        "список следующих",
        "spätere",
        "后续",
        "ultérieure",
        "posterior",
    )

    for locale in LOCALES:
        root = _topic(locale, "user", "ug-concept-browser-policy-manager-overview")
        assistant = " ".join("".join(root.find(".//section[@id='assistant']").itertext()).split())
        boundary = " ".join(
            "".join(root.find(".//section[@id='assistant-installation']").itertext()).split()
        )
        text = f"{assistant} {boundary}".lower()
        assert "0.9." not in text
        assert all(term not in text for term in future_copy)
        assert "bpm" in text


def test_changed_chinese_examples_keep_protected_names_and_catalog_ui_copy() -> None:
    import_user = _topic("zh-CN", "user", "ug-task-import-policies-json")
    import_admin = _topic("zh-CN", "admin", "admin-task-import-firefox-policies-json")
    export_admin = _topic("zh-CN", "admin", "admin-task-export-firefox-policies-json")
    for root in (import_user, import_admin, export_admin):
        title = "".join(root.find(".//example/title").itertext())
        assert "Firefox" in title
        assert "policies.json" in title
        assert "火狐浏览器" not in title

    catalog = json.loads((ROOT / "app/i18n/zh-CN.json").read_text(encoding="utf-8"))
    editor = _topic("zh-CN", "user", "ug-task-use-json-editor")
    figure_title = "".join(editor.find(".//fig/title").itertext())
    assert catalog["profiles.editor_chrome_json_link"] in figure_title
    assert "数据交换文档编辑器" not in " ".join(editor.itertext())
