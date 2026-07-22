from __future__ import annotations

import json

import pytest

from app.core.locales import ACTIVE_CATALOG_LOCALES
from tests.docs_index import REPO_ROOT, doc_path_from_index

FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "ui_compaction_baseline_guards_0.9.2.json"


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _guard(fixture: dict[str, object], guard_id: str) -> dict[str, object]:
    guards = fixture["guards"]
    assert isinstance(guards, list)
    return next(guard for guard in guards if guard["id"] == guard_id)


def _assert_no_markers(source: str, markers: list[str]) -> None:
    for marker in markers:
        assert marker not in source


def _assert_classified(key: str, fixture: dict[str, object]) -> None:
    exact = fixture["known_classification_keys"]
    prefixes = fixture["known_classification_prefixes"]
    assert isinstance(exact, list)
    assert isinstance(prefixes, list)
    assert key in exact or any(key.startswith(prefix) for prefix in prefixes)


def test_baseline_fixture_indexes_every_m2_contract_and_census() -> None:
    fixture = _fixture()

    assert fixture["schema_version"] == 1
    assert fixture["backlog_item"] == "BPM092-M2-08"
    assert fixture["target_bpm_version"] == "0.9.2"
    assert fixture["status"] == "active"
    assert fixture["source_census"] == {
        "candidate_keys": 449,
        "candidate_words": 5934,
        "guided_keys": 352,
        "guided_words": 4782,
    }

    contracts = fixture["contracts"]
    assert isinstance(contracts, list)
    for path in contracts:
        assert isinstance(path, str)
        doc_path_from_index(path, status="active")


def test_density_and_copy_contracts_require_zero_residual_removable_prose() -> None:
    density = doc_path_from_index(
        "architecture/ui-density-budget-contract-0.9.2.md", status="active"
    ).read_text(encoding="utf-8")
    classification = doc_path_from_index(
        "architecture/ui-copy-classification-contract-0.9.2.md", status="active"
    ).read_text(encoding="utf-8")

    assert "`remove-explanation` nodes and words | `0`" in density
    assert "Redundant presentation of a `deduplicate` fact | `0`" in density
    assert "`remove-explanation` | Remove routine workflow narration" in classification
    assert "`safety-accessibility` | Keep validation, error, consequence, recovery" in classification


def test_guard_detector_rejects_reintroduced_explanatory_block_fixture() -> None:
    fixture = _fixture()
    guard = _guard(fixture, "reintroduced-explanatory-block")
    markers = guard["forbidden_markers"]
    assert isinstance(markers, list)

    with pytest.raises(AssertionError):
        _assert_no_markers('<p data-i18n="profiles.sidebar_hint">Library tutorial</p>', markers)


def test_compact_shared_header_has_no_retired_explanatory_nodes() -> None:
    fixture = _fixture()
    guard = _guard(fixture, "reintroduced-explanatory-block")
    markers = guard["forbidden_markers"]
    assert isinstance(markers, list)
    header = (REPO_ROOT / "app" / "templates" / "profiles" / "_page_header.html").read_text(
        encoding="utf-8"
    )

    _assert_no_markers(header, markers[:3])
    assert 'data-bpm-header' in header
    assert 'data-bpm-header-brand' in header
    assert 'data-bpm-header-preferences' in header


def test_all_settings_and_json_workspaces_have_no_retired_overview_copy() -> None:
    fixture = _fixture()
    guard = _guard(fixture, "reintroduced-explanatory-block")
    markers = guard["forbidden_markers"]
    assert isinstance(markers, list)
    workspace_sources = (
        REPO_ROOT / "app" / "templates" / "profiles" / "_page_settings_workspace.html",
        REPO_ROOT / "app" / "templates" / "profiles" / "_page_json_workspace.html",
    )

    for source_path in workspace_sources:
        _assert_no_markers(source_path.read_text(encoding="utf-8"), markers)


def test_retired_shared_copy_has_no_active_catalog_or_layout_references() -> None:
    retired_keys = (
        "profiles.subtitle",
        "profiles.locale_hint",
        "profiles.theme_hint",
        "profiles.sidebar_hint",
        "profiles.empty_list",
        "profiles.clone_name_ready",
        "profiles.compare_route_eyebrow",
        "profiles.compare_selection_title",
        "profiles.compare_settings_title",
        "profiles.editor_chrome_modes_body",
        "profiles.editor_chrome_guided_body",
        "profiles.editor_chrome_settings_body",
        "profiles.editor_chrome_json_body",
    )

    for locale in ACTIVE_CATALOG_LOCALES:
        for catalog_path in (
            REPO_ROOT / "app" / "i18n_src" / locale / "common.json",
            REPO_ROOT / "app" / "i18n_src" / locale / "library.json",
            REPO_ROOT / "app" / "i18n" / f"{locale}.json",
        ):
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            assert all(key not in catalog for key in retired_keys), catalog_path

    active_sources = tuple((REPO_ROOT / "app" / "templates").rglob("*.html")) + tuple(
        (REPO_ROOT / "app" / "static" / "profiles_css").glob("*.css")
    )
    for source_path in active_sources:
        source = source_path.read_text(encoding="utf-8")
        assert all(key not in source for key in retired_keys), source_path
    assert all(
        marker not in source
        for source_path in active_sources
        for source in (source_path.read_text(encoding="utf-8"),)
        for marker in (
            "compact-toolbar-subtitle",
            "compact-toolbar-section",
            "compact-toolbar-brand",
            "library-panel-intro",
            "list-empty-illustration",
            "profile-clone-handoff",
            "compare-selection-title",
            "compare-settings-heading",
        )
    )


def test_guard_detector_rejects_unclassified_visible_prose_fixture() -> None:
    fixture = _fixture()
    _assert_classified("profiles.wizard_shell_json_hint", fixture)

    with pytest.raises(AssertionError):
        _assert_classified("profiles.unclassified_explanatory_copy", fixture)


def test_guard_detector_rejects_header_and_independent_documentation_version_fixtures() -> None:
    fixture = _fixture()

    for guard_id, regression in (
        ("header-drift", '<header data-bpm-header-missing-slot>'),
        ("independent-documentation-version", "<p>Documentation 0.9.2</p>"),
    ):
        guard = _guard(fixture, guard_id)
        markers = guard["forbidden_markers"]
        assert isinstance(markers, list)
        with pytest.raises(AssertionError):
            _assert_no_markers(regression, markers)


def test_guard_detector_rejects_search_auto_expand_and_editorial_regression_fixtures() -> None:
    fixture = _fixture()

    for guard_id, regression in (
        ("search-auto-expand", "setSearchExpanded(root, true); runSearch(root, index);"),
        ("maintainer-progress-narration", "This task is implemented for the maintainer."),
    ):
        guard = _guard(fixture, guard_id)
        markers = guard["forbidden_markers"]
        assert isinstance(markers, list)
        with pytest.raises(AssertionError):
            _assert_no_markers(regression, markers)
