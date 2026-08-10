from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPO_ROOT / "documentation"
BUILD_DOCS = DOCUMENTATION_ROOT / "tools/build_docs.py"
SEARCH_FACETS = DOCUMENTATION_ROOT / "config/search-facets-filters-0.9.0.json"
SEARCH_UI_CONTRACT = DOCUMENTATION_ROOT / "config/search-ui-filter-contract-0.9.1.json"
SEARCH_SCRIPT = DOCUMENTATION_ROOT / "assets/theme/bpm-docs-search.js"

SPEC = importlib.util.spec_from_file_location("build_docs", BUILD_DOCS)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_search_filter_locale_labels_cover_all_facets_and_values() -> None:
    facets = build_docs._search_facets_filters()
    facet_fields = facets["facet_fields"]

    assert set(build_docs.SEARCH_FILTER_FIELD_LABELS) == set(build_docs.LOCALES)
    assert set(build_docs.SEARCH_FILTER_VALUE_LABELS) == set(build_docs.LOCALES)
    for locale in build_docs.LOCALES:
        localized = build_docs._localized_search_facet_fields(locale, facets)
        assert set(localized) == set(facet_fields)
        assert set(build_docs.SEARCH_FILTER_FIELD_LABELS[locale]) == set(facet_fields)

        for field, definition in facet_fields.items():
            assert localized[field]["values"] == definition["values"]
            assert localized[field]["label"]
            assert set(localized[field]["value_labels"]) == {
                str(value) for value in definition["values"] if value is not None
            }


def test_non_english_visible_filter_labels_do_not_fall_back_to_raw_english() -> None:
    facets = build_docs._search_facets_filters()
    contract = _json(SEARCH_UI_CONTRACT)
    visible_fields = set(contract["localized_labels"]["visible_facets"])
    for locale in set(build_docs.LOCALES) - {"en"}:
        localized = build_docs._localized_search_facet_fields(locale, facets)
        for field in visible_fields:
            assert localized[field]["label"] != field
            assert localized[field]["label"] != facets["facet_fields"][field]["label"]

            for value, label in localized[field]["value_labels"].items():
                assert label
                assert label != value or value.startswith(("esr-", "release-"))


def test_localized_filter_payload_preserves_url_params_and_raw_values() -> None:
    facets = build_docs._search_facets_filters()

    for locale in build_docs.LOCALES:
        localized = build_docs._localized_search_facet_fields(locale, facets)
        for field, definition in facets["facet_fields"].items():
            assert localized[field]["values"] == definition["values"]
        assert facets["url_state"]["parameters"]["guide_id"] == "guide"
        assert facets["url_state"]["parameters"]["firefox_channel"] == "channel"
        assert (
            build_docs._filter_url_query(
                {"guide_id": ["administrator-guide"], "api_area": ["validation"]},
                facets,
            )
            == "api_area=validation&guide=administrator-guide"
        )


def test_search_runtime_renders_localized_value_labels_without_mutating_checkbox_values() -> None:
    script = SEARCH_SCRIPT.read_text(encoding="utf-8")

    for required in (
        "const valueLabels = definition.value_labels || {};",
        "checkbox.value = value;",
        "checkbox.dataset.searchFilter = field;",
        "appendText(label, ` ${valueLabels[value] || value} (${count})`);",
    ):
        assert required in script
