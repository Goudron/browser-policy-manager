from __future__ import annotations

import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
NAVIGATION_CONTRACT = DOCUMENTATION_ROOT / "config/navigation-tree-contract-0.9.1.json"
LANGUAGE_BROWSER_QA = (
    DOCUMENTATION_ROOT / "config/documentation-navigation-language-browser-qa-0.9.1.json"
)
BROWSER_SMOKE = DOCUMENTATION_ROOT / "tests/browser/test_documentation_portal_browser_smoke.py"
MODULE_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
SPEC = importlib.util.spec_from_file_location("build_docs", MODULE_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict[str, object]:
    return json.loads(NAVIGATION_CONTRACT.read_text(encoding="utf-8"))


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _element_text(element: ET.Element | None) -> str:
    assert element is not None
    return " ".join("".join(element.itertext()).split())


def test_navigation_tree_contract_is_scoped_to_091_and_manifest_owned() -> None:
    contract = _contract()

    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "bpm-doc-navigation-tree-contract-0.9.1"
    assert contract["backlog_item"] == "BPM091-M2-05"
    assert contract["target_bpm_version"] == "0.9.1"
    assert contract["status"] == "accepted"
    assert "single hierarchical navigation model" in contract["purpose"]

    inherited = set(contract["inherits_from"])
    assert {
        "docs/architecture/documentation-identifiers-and-url-conventions-0.9.0.md",
        "docs/architecture/product-documentation-manifest-and-ui-target-schema-0.9.0.md",
        "docs/architecture/product-documentation-accessibility-security-contract-0.9.0.md",
        "documentation/config/search-ui-filter-contract-0.9.1.json",
    } <= inherited
    assert contract["source_authority"]["guide_order"].startswith("manifest.navigation")
    assert (
        contract["source_authority"]["guide_titles"] == "manifest.guides.{guide_id}.title.{locale}"
    )
    assert contract["source_authority"]["section_nodes"] == (
        "documentation/config/topic-section-taxonomy-0.9.1.json for affected guides"
    )
    assert contract["source_authority"]["section_labels"] == (
        "documentation/config/topic-section-labels-0.9.1.json for the exact locale matrix"
    )
    assert contract["source_authority"]["topic_nodes"].startswith("manifest.topics")


def test_navigation_tree_contract_matches_existing_guide_and_locale_matrix() -> None:
    contract = _contract()

    assert contract["locales"] == list(build_docs.LOCALES)
    assert contract["guide_node_order"] == [
        guide_id for guide_id, _filename, _anchor, _url_root in build_docs.GUIDE_MAPS
    ]
    assert contract["guide_node_order"] == [
        "user-guide",
        "firefox-policy-guide",
        "cis-settings-guide",
        "administrator-guide",
    ]


def test_navigation_tree_model_defines_root_guide_section_topic_nodes_and_display_rules() -> None:
    contract = _contract()
    tree = contract["tree_model"]

    assert tree["root_node"] == {
        "node_id": "documentation-root",
        "node_type": "root",
        "label_key": "navigation.root",
        "href": "/help/{locale}/",
        "children": "guide_node_order",
    }
    assert tree["guide_node"]["node_id"] == "{guide_id}"
    assert tree["guide_node"]["href_source"] == (
        "manifest topic output for manifest.guides.{guide_id}.home_topic_id"
    )
    assert tree["section_node"] == {
        "node_type": "section",
        "node_id": "section:{guide_id}:{section_id}",
        "label_source": "topic-section label catalog value for label_key and active locale",
        "label_key_source": "topic-section taxonomy label_key",
        "href_source": None,
        "children": "taxonomy-owned topic nodes in unchanged DITA map order",
    }
    assert tree["topic_node"]["node_id"] == "{topic_id}"
    assert tree["topic_node"]["href_source"] == "manifest.topics.{topic_id}.output.{locale}"
    assert "owning section node" in tree["topic_node"]["parent"]

    display = contract["display_rules"]
    assert "authoritative place for guide/document names" in display["primary_left_navigation"]
    assert "must not be repeated" in display["no_duplicate_guide_title"]
    assert "topic title or documentation home title" in display["topic_heading_rule"]
    assert "same tree path" in display["breadcrumbs"]


def test_navigation_contract_covers_current_state_return_paths_and_url_invariants() -> None:
    contract = _contract()

    active = contract["active_state"]
    assert active["root_page"]["current_node"] == "documentation-root"
    assert active["guide_page"]["expanded_nodes"] == ["documentation-root", "{guide_id}"]
    assert active["topic_page"]["current_node"] == "{topic_id}"
    assert "{section_node_id}" in active["topic_page"]["expanded_nodes"]
    assert "highlight more than one current page node" in active["must_not"]
    assert "derive current state from translated labels" in active["must_not"]
    assert "collapse the current topic's ancestors" in active["must_not"]

    returns = contract["return_behavior"]
    assert "locale documentation root" in returns["root_link"]
    assert "guide's landing topic" in returns["guide_link"]
    assert "without introducing a new canonical page or URL" in returns["section_node"]
    assert "nearest topic parent" in returns["parent_topic_link"]
    assert "ordinary links" in returns["browser_history"]
    assert "direct topic URL expands" in returns["direct_url"]

    urls = contract["url_behavior"]
    assert "manifest-resolved topic outputs" in urls["canonical_identity"]
    assert "must not change canonical topic URLs" in urls["state_parameters"]
    assert "translated filenames" in urls["forbidden"]
    assert "hash-only guide navigation as the only route to a guide" in urls["forbidden"]
    assert "JavaScript-only return to root" in urls["forbidden"]


def test_navigation_contract_defines_accessible_keyboard_tree_and_localization() -> None:
    contract = _contract()

    keyboard = contract["keyboard_tree"]
    assert keyboard["roles"] == ["tree", "treeitem", "group"]
    required_keys = " ".join(keyboard["required_keys"])
    for key in ("ArrowDown", "ArrowUp", "ArrowRight", "ArrowLeft", "Home", "End", "Enter", "Space"):
        assert key in required_keys
    assert "Only one tree item has tabindex=0 at a time." in keyboard["focus_rules"]
    assert "Collapsed descendants are not tabbable." in keyboard["focus_rules"]

    collapse = contract["collapse_state"]
    assert "Root is expanded" in collapse["default"]
    assert "direct URLs always expand current ancestors" in collapse["persistence"]
    assert "hide selected ancestors" in collapse["must_not"]

    localization = contract["localization"]
    assert "locale-owned" in localization["label_ownership"]
    assert "must not fall back to English navigation labels" in localization["no_fallback"]
    assert {
        "navigation.root",
        "navigation.tree_label",
        "navigation.expand",
        "navigation.collapse",
        "navigation.current",
        "navigation.parent",
        "navigation.back_to_root",
        "navigation.section.{guide_id}.{section_id}",
    } <= set(localization["required_locale_keys"])


def test_navigation_contract_defines_independent_sidebar_scrolling() -> None:
    contract = _contract()
    scrolling = contract["sidebar_scroll"]

    assert scrolling["implementation_task"] == "BPM091-M10-02"
    assert scrolling["container"] == ".bpm-docs-sidebar"
    assert "viewport-relative maximum block size" in scrolling["desktop"]
    assert "height-bounded" in scrolling["narrow"]
    assert "without scrolling the article viewport" in scrolling["active_item"]
    assert "Arrow, Home, and End" in scrolling["keyboard"]
    assert "Wheel, touch, scrollbar-thumb" in scrolling["pointer"]
    assert "horizontal scrolling" in " ".join(scrolling["layout"])


def test_navigation_contract_defines_one_manifest_backed_source_per_locale() -> None:
    contract = _contract()
    shared = contract["shared_source"]

    assert shared["implementation_task"] == "BPM091-M10-07"
    assert shared["path"] == "{locale}/navigation.json"
    assert shared["schema"].endswith("product-documentation-navigation-v1.schema.json")
    assert "SHA-256" in shared["manifest_owner"]
    assert "does not embed tree nodes" in shared["html_host"]
    assert "same-origin locale source" in shared["runtime"]
    assert "working root link" in shared["failure"]
    assert "textContent" in shared["security"]
    assert "without innerHTML" in shared["security"]
    assert "does not change the article column" in shared["layout"]


def test_navigation_contract_routes_implementation_and_verification_to_tree_tasks() -> None:
    contract = _contract()

    assert contract["implementation_tasks"] == [
        "BPM091-M4-04",
        "BPM091-M4-05",
        "BPM091-M4-06",
        "BPM091-M4-07",
        "BPM091-M8-03",
        "BPM091-M8-04",
        "BPM091-M8-05",
        "BPM091-M10-02",
        "BPM091-M10-07",
        "BPM091-M10-08",
        "BPM091-M10-09",
    ]
    assert "make test-docs-browser" in contract["verification"]["release_gates"]
    browser_required = contract["verification"]["browser_required_for"]
    assert "root-to-guide-to-section-to-topic navigation" in browser_required
    assert "current document and section ancestor expansion" in browser_required
    assert "flat navigation for documents excluded from the section taxonomy" in browser_required
    assert "independent desktop and narrow sidebar scrolling" in browser_required
    assert (
        "direct-topic and keyboard-focus auto-reveal without article scrolling" in browser_required
    )
    assert "successful and failed shared navigation-source loading" in browser_required
    assert "absence of embedded full-tree copies and incoherent loading shift" in browser_required
    assert "native wheel and keyboard scrolling in every locale" in browser_required
    assert "absence of the retired standalone API guide node" in browser_required
    assert "exact locale-owned interface names and representative visible prose" in browser_required
    assert "absence of frozen English prose in non-English locale samples" in browser_required
    assert "generated output remains non-authoritative" in contract["non_goals"][0]
    assert "This contract does not change topic IDs" in contract["non_goals"][1]


def test_navigation_browser_smoke_covers_section_level_behavior() -> None:
    smoke = BROWSER_SMOKE.read_text(encoding="utf-8")

    for fragment in (
        "first_user_section",
        "first_admin_section",
        "first_firefox_topic_id",
        "keys.Keys.ARROW_RIGHT",
        "keys.Keys.ARROW_LEFT",
        "keys.Keys.ENTER",
        "keys.Keys.SPACE",
        "driver.set_window_size(390, 900)",
        'topic_state["tabStops"] == [first_user_topic_id]',
        'current_section_state["expanded"] == "true"',
        "data-docs-tree-host",
        "navigation.json",
        "bpm-docs-tree-status--unavailable",
        "documentation-navigation-language-browser-qa-0.9.1.json",
        "ScrollOrigin.from_element",
        "forbidden_guide_node_ids",
        "forbidden_english_fragments",
    ):
        assert fragment in smoke


def test_navigation_language_browser_qa_matches_dita_and_runtime_catalogs() -> None:
    contract = _contract()
    qa = _json(LANGUAGE_BROWSER_QA)

    assert qa["schema_version"] == 1
    assert qa["qa_id"] == "bpm-0.9.1-documentation-navigation-language-browser-qa"
    assert qa["target_bpm_version"] == "0.9.1"
    assert qa["backlog_item"] == "BPM091-M10-09"
    assert qa["status"] == "accepted"
    assert qa["locales"] == list(build_docs.LOCALES)
    assert qa["expected_guide_node_ids"] == contract["guide_node_order"]
    assert qa["forbidden_guide_node_ids"] == ["api-integration-guide"]
    assert qa["viewports"] == {
        "desktop": {"width": 1366, "height": 1000},
        "narrow": {"width": 390, "height": 900},
    }
    assert contract["browser_qa"] == {
        "implementation_task": "BPM091-M10-09",
        "matrix": "documentation/config/documentation-navigation-language-browser-qa-0.9.1.json",
        "locale_scope": list(build_docs.LOCALES),
        "language_sample_topic": "ug-task-use-all-settings",
        "required_inputs": ["native wheel", "keyboard", "pointer"],
        "required_failure_scope": "missing navigation.json in every locale",
        "forbidden_guide_node": "api-integration-guide",
    }

    language_sample = qa["language_sample"]
    assert language_sample["topic_id"] == "ug-task-use-all-settings"
    assert set(language_sample["locales"]) == set(build_docs.LOCALES)
    english = language_sample["locales"]["en"]
    for locale, expected in language_sample["locales"].items():
        source = REPOSITORY_ROOT / language_sample["source"].format(locale=locale)
        root = ET.parse(source).getroot()
        assert expected["title"] == _element_text(root.find("title"))
        assert expected["shortdesc"] == _element_text(root.find("shortdesc"))
        assert expected["first_paragraph"] == _element_text(next(root.iter("p")))
        runtime_catalog = _json(REPOSITORY_ROOT / f"app/i18n/{locale}.json")
        assert expected["interface_name"] == runtime_catalog[language_sample["runtime_catalog_key"]]
        if locale == "en":
            assert expected["forbidden_english_fragments"] == []
        else:
            assert expected["forbidden_english_fragments"] == [
                english["title"],
                english["shortdesc"],
                english["first_paragraph"],
            ]

    assert qa["execution"] == {
        "test": "documentation/tests/browser/test_documentation_portal_browser_smoke.py",
        "target": "make test-docs-browser",
        "persistent_server": False,
        "chromium_parallelism": 1,
        "disk_backed_pytest_basetemp": ".cache/pytest-docs-browser",
    }
