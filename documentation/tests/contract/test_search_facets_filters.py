from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
FACETS_CONTRACT = DOCUMENTATION_ROOT / "config/search-facets-filters-0.9.0.json"
MODULE_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
SPEC = importlib.util.spec_from_file_location("build_docs", MODULE_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict[str, object]:
    return json.loads(FACETS_CONTRACT.read_text(encoding="utf-8"))


def test_search_facets_contract_is_static_localized_and_non_ai() -> None:
    contract = _contract()

    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "bpm-doc-search-facets-filters-0.9.0"
    assert contract["backlog_item"] == "BPM090-M10-05"
    assert contract["target_bpm_version"] == "0.9.0"
    assert contract["status"] == "accepted"
    assert contract["search_mode"] == "deterministic-local-static"
    assert contract["non_ai_boundary"]["mode"] == "no-ai-no-rag-no-embeddings-no-generative-answers"

    facets = contract["facet_fields"]
    assert facets["bpm_version"]["values"] == [build_docs.PRODUCT_VERSION_FACET_PLACEHOLDER]
    assert facets["locale"]["values"] == list(build_docs.LOCALES)
    assert set(facets) == {
        "locale",
        "guide_id",
        "topic_kind",
        "firefox_channel",
        "policy_category",
        "cis_level",
        "cis_control_state",
        "api_area",
        "bpm_version",
    }
    assert facets["guide_id"]["values"] == [
        "user-guide",
        "firefox-policy-guide",
        "cis-settings-guide",
        "administrator-guide",
    ]
    assert facets["firefox_channel"]["values"] == [
        "esr-115.39",
        "esr-140.13",
        "esr-153.0",
        "release-153",
    ]
    for locale in build_docs.LOCALES:
        labels = build_docs._localized_search_facet_fields(locale, contract)["firefox_channel"]
        assert labels["value_labels"]["esr-115.39"] == "Firefox ESR 115.39"
        assert set(labels["value_labels"]) == set(facets["firefox_channel"]["values"])
    assert "ai_smart" in facets["policy_category"]["values"]
    assert facets["cis_level"]["values"] == ["level-1", "level-2"]
    assert facets["api_area"]["values"] == [
        "service",
        "health",
        "profiles",
        "validation",
        "import-export",
        "ui",
    ]


def test_search_filter_contract_defines_composition_url_state_and_localized_empty_recovery() -> (
    None
):
    contract = _contract()

    assert contract["filter_contract"]["composition"] == (
        "AND across facet fields; OR within values of the same facet field."
    )
    assert contract["url_state"]["multi_value_encoding"] == "repeat-parameter"
    assert contract["url_state"]["parameters"]["guide_id"] == "guide"
    assert contract["url_state"]["parameters"]["api_area"] == "api_area"
    assert set(contract["empty_result"]["messages"]) == set(build_docs.LOCALES)
    assert all(contract["empty_result"]["messages"][locale] for locale in build_docs.LOCALES)


def test_search_filter_fixture_matrix_covers_all_locales_and_empty_recovery() -> None:
    contract = _contract()
    fixtures = contract["filter_fixtures"]

    fixture_locales = {fixture["locale"] for fixture in fixtures}
    empty_fixture_locales = {
        fixture["locale"] for fixture in fixtures if fixture.get("expected_empty")
    }
    assert fixture_locales == set(build_docs.LOCALES)
    assert empty_fixture_locales == set(build_docs.LOCALES)
    assert any(
        fixture["filters"] == {"guide_id": ["administrator-guide"], "api_area": ["validation"]}
        for fixture in fixtures
    )


def test_filter_helpers_apply_and_across_fields_or_within_a_field_and_preserve_url_state() -> None:
    docs = [
        {
            "topic_id": "api",
            "filter_facets": {
                "guide_id": ["administrator-guide"],
                "api_area": ["validation", "profiles"],
            },
        },
        {
            "topic_id": "cis",
            "filter_facets": {
                "guide_id": ["cis-settings-guide"],
                "cis_level": ["level-2"],
            },
        },
        {
            "topic_id": "user",
            "filter_facets": {
                "guide_id": ["user-guide"],
                "topic_kind": ["task"],
            },
        },
    ]
    contract = _contract()

    filtered = build_docs._filter_search_documents(
        docs,
        {"guide_id": ["administrator-guide"], "api_area": ["profiles", "validation"]},
    )
    assert [document["topic_id"] for document in filtered] == ["api"]

    assert (
        build_docs._filter_search_documents(
            docs, {"api_area": ["validation"], "cis_level": ["level-2"]}
        )
        == []
    )
    assert (
        build_docs._filter_url_query(
            {"api_area": ["validation"], "guide_id": ["administrator-guide"]},
            contract,
        )
        == "api_area=validation&guide=administrator-guide"
    )


@pytest.mark.parametrize(
    ("operation_id", "area"),
    [
        ("API-SVC-001", "service"),
        ("API-HEALTH-001", "health"),
        ("API-PROFILE-001", "profiles"),
        ("API-VAL-001", "validation"),
        ("API-FF-001", "import-export"),
        ("WEB-DOC-001", "ui"),
    ],
)
def test_api_operation_ids_map_to_declared_search_api_areas(operation_id: str, area: str) -> None:
    assert build_docs._api_operation_area(operation_id) == area
