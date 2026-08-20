import json

from tests.docs_index import REPO_ROOT, doc_path_from_index

INVENTORY_PATH = "architecture/firefox-schema-lifecycle-documentation-impact-inventory-0.9.5.json"
SUMMARY_PATH = "architecture/firefox-schema-lifecycle-documentation-impact-inventory-0.9.5.md"
EXPECTED_GUIDES = {
    "user-guide",
    "firefox-policy-guide",
    "cis-settings-guide",
    "administrator-guide",
}
EXPECTED_CONSUMERS = {"schema-inventory", "search", "contextual-help", "screenshots"}


def _inventory() -> dict[str, object]:
    path = doc_path_from_index(INVENTORY_PATH, status="active")
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _assert_existing_source(path: str) -> None:
    assert "documentation/build" not in path
    assert "documentation/dist" not in path
    assert "documentation/reports" not in path
    assert "app/documentation/site" not in path
    assert (REPO_ROOT / path).exists(), path


def test_m8_impact_inventory_has_one_audience_owner_for_every_behavior_and_boundary() -> None:
    inventory = _inventory()

    assert inventory["schema_version"] == 1
    assert inventory["inventory_id"] == "bpm095-firefox-schema-lifecycle-documentation-impact"
    assert inventory["backlog_item"] == "BPM095-M8-01"
    assert inventory["target_bpm_version"] == "0.9.5.1"
    assert inventory["status"] == "accepted-authoring-inventory"

    owners = inventory["audience_owners"]
    assert isinstance(owners, list)
    owner_ids = {row["owner_id"] for row in owners}
    assert owner_ids == {
        "user",
        "firefox-policy",
        "cis",
        "administrator-devops",
        "api",
        "support-troubleshooting",
    }

    behaviors = inventory["delivered_behaviors"]
    assert isinstance(behaviors, list)
    assert {row["behavior_id"] for row in behaviors} == {
        "four-channel-selection-and-esr115-caveat",
        "four-channel-policy-availability",
        "cis-four-channel-layers-and-presets",
        "manual-pairwise-conversion",
        "latest-esr-recommendation",
        "conversion-api",
        "retired-esr-successor-migration",
        "conversion-and-retirement-recovery",
    }
    for row in behaviors:
        assert row["audience_owner"] in owner_ids
        assert row["authoring_task"] == "BPM095-M8-02"
        assert row["required_reader_boundary"]
        for path in row["source_paths"]:
            _assert_existing_source(path)

    consumers = inventory["consumer_impacts"]
    assert isinstance(consumers, list)
    assert {row["impact_id"] for row in consumers} == EXPECTED_CONSUMERS
    for row in consumers:
        assert row["audience_owner"] in owner_ids
        assert row["status"] in {"refresh-in-M8-04", "review-in-M8-04"}
        assert row["reason"]
        for path in row["owner_sources"]:
            _assert_existing_source(path.replace("{locale}/", "en/"))


def test_m8_impact_inventory_records_all_guides_and_three_channel_dispositions() -> None:
    inventory = _inventory()
    guides = inventory["guide_dispositions"]
    assert isinstance(guides, list)
    assert {row["guide_id"] for row in guides} == EXPECTED_GUIDES
    for row in guides:
        assert row["status"] in {"affected", "unaffected"}
        assert row["reason"]

    stale = inventory["stale_three_channel_dispositions"]
    assert isinstance(stale, list)
    paths = {row["path"] for row in stale}
    assert {
        "README.md",
        "documentation/src/dita/en/user/ug-task-choose-profile-identity-schema.dita",
        "documentation/src/dita/en/firefox/fx-concept-release-esr-differences.dita",
        "documentation/src/dita/en/cis/cis-concept-levels-channels-layers.dita",
        "docs/architecture/firefox-policy-documentation-inventory-0.9.0.md",
        "docs/architecture/firefox-153-dual-esr-schema-contract-0.9.2.md",
    } <= paths
    for row in stale:
        _assert_existing_source(row["path"])
        assert row["disposition"]
        assert row["reason"]


def test_m8_impact_inventory_keeps_source_locale_and_generated_boundaries_explicit() -> None:
    inventory = _inventory()
    scope = inventory["scope"]
    assert scope["source_locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert "M8-04 is the only task" in scope["generation_policy"]

    summary = " ".join(
        doc_path_from_index(SUMMARY_PATH, status="active").read_text(encoding="utf-8").split()
    )
    for phrase in (
        "M8-02 authors English DITA",
        "M8-03 supplies reviewed equivalent content",
        "M8-04 refreshes those only after source review",
        "no task hand-edits generated HTML, search, manifest, PDF,",
        "All four published guide families are affected.",
    ):
        assert phrase in summary
