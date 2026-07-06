from __future__ import annotations

import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
FIXTURE_CATALOG = DOCUMENTATION_ROOT / "fixtures/fixture-catalog-0.9.0.json"
SUITE_BOUNDARIES = DOCUMENTATION_ROOT / "tests/suite-boundaries-0.9.0.json"

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_fixture_catalog_covers_required_documentation_states() -> None:
    catalog = _json(FIXTURE_CATALOG)

    assert catalog["schema_version"] == 1
    assert catalog["backlog_item"] == "BPM090-M11-05"
    assert catalog["target_bpm_version"] == "0.9.0"
    assert catalog["status"] == "accepted"
    assert catalog["max_fixture_bytes"] == 16384

    categories = {
        category
        for fixture in catalog["fixtures"]
        for category in [fixture["category"], *fixture.get("also_covers", [])]
    }
    assert categories == set(catalog["required_categories"])
    assert categories == {
        "profile",
        "policy",
        "preference",
        "cis",
        "api",
        "locale",
        "search",
        "screenshot",
    }


def test_fixture_catalog_entries_are_compact_synthetic_json_inputs() -> None:
    catalog = _json(FIXTURE_CATALOG)
    max_bytes = catalog["max_fixture_bytes"]
    forbidden_fragments = (
        "/build/",
        "/dist/",
        "/reports/coverage/",
        ".sqlite",
        ".db",
        ".pdf",
        "firefox.tar",
        "browser.tar",
    )
    forbidden_text = (
        "password",
        "secret",
        "token",
        "customer",
        "tenant",
        "production",
        "corp.local",
    )

    for fixture in catalog["fixtures"]:
        path = REPOSITORY_ROOT / fixture["path"]
        assert path.is_file(), fixture["id"]
        assert path.suffix == ".json", fixture["id"]
        assert path.stat().st_size <= max_bytes, fixture["id"]
        assert not any(fragment in fixture["path"] for fragment in forbidden_fragments)
        payload = _json(path)
        assert payload["schema_version"] == 1
        assert payload["target_bpm_version"] == "0.9.0"
        assert payload["synthetic"] is True
        serialized = json.dumps(payload, ensure_ascii=False).lower()
        assert not any(fragment in serialized for fragment in forbidden_text), fixture["id"]


def test_fixture_catalog_maps_failure_domains_to_existing_suite_boundaries() -> None:
    catalog = _json(FIXTURE_CATALOG)
    boundaries = _json(SUITE_BOUNDARIES)
    known_domains = set(boundaries["domains"])
    mapped_domains = {
        domain
        for fixture in catalog["fixtures"]
        for domain in fixture["failure_domains"]
    }

    assert mapped_domains <= known_domains
    for required_domain in (
        "content",
        "localization",
        "screenshot",
        "search",
        "links",
        "api_examples",
        "portal_integration",
    ):
        assert required_domain in mapped_domains


def test_fixture_catalog_is_registered_in_suite_boundary_contract() -> None:
    boundaries = _json(SUITE_BOUNDARIES)
    fixtures_domain = boundaries["domains"]["fixtures"]

    assert fixtures_domain["primary_suite"] == "contract"
    assert "documentation/tests/contract/test_documentation_fixture_catalog.py" in fixtures_domain[
        "path_globs"
    ]
    assert "documentation/fixtures/fixture-catalog-0.9.0.json" in fixtures_domain["fixtures"]
    assert fixtures_domain["focused_rerun"] == (
        "./.venv/bin/pytest -q -m docs_contract "
        "documentation/tests/contract/test_documentation_fixture_catalog.py"
    )
