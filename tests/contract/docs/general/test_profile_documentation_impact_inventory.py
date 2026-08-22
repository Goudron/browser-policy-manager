"""Executable ownership guard for BPM096-M10-01's documentation impact inventory."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[4]
INVENTORY_PATH = REPO_ROOT / "docs/architecture/profile-documentation-impact-inventory-0.9.6.md"
BACKLOG_PATH = REPO_ROOT / "docs/bpm_0_9_6_profile_creation_guided_editor_backlog_2026-08-20.md"
KEYS_PATH = REPO_ROOT / "documentation/src/dita/en/maps/keys.ditamap"
FIXTURE_MARKER = "<!-- bpm096-profile-documentation-impact-inventory-v1 -->"


def _inventory() -> dict[str, Any]:
    source = INVENTORY_PATH.read_text(encoding="utf-8")
    match = re.search(
        rf"{re.escape(FIXTURE_MARKER)}\s*```json\s*(\{{.*?\}})\s*```",
        source,
        flags=re.DOTALL,
    )
    assert match, "profile documentation impact fixture is missing"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def _keyrefs() -> set[str]:
    return set(re.findall(r'<keydef keys="topic\.([^"]+)"', KEYS_PATH.read_text(encoding="utf-8")))


def test_inventory_is_indexed_backlog_linked_and_scoped_to_m10_01() -> None:
    assert (
        doc_path_from_index(
            "architecture/profile-documentation-impact-inventory-0.9.6.md", status="active"
        )
        == INVENTORY_PATH
    )
    inventory = _inventory()
    assert inventory["inventory_id"] == "bpm096-profile-documentation-impact"
    assert inventory["inventory_version"] == 1
    assert inventory["backlog_item"] == "BPM096-M10-01"
    assert inventory["target_bpm_version"] == "0.9.6"
    assert inventory["source_locale"] == "en"
    assert inventory["localized_peer_locales"] == ["ru", "de", "zh-CN", "fr", "es-ES"]
    assert "BPM096-M10-01" in BACKLOG_PATH.read_text(encoding="utf-8")


def test_all_four_guides_are_reviewed_and_any_future_untouched_guide_requires_reason() -> None:
    inventory = _inventory()
    guides = inventory["guide_maps"]
    assert set(guides) == {
        "user-guide",
        "firefox-policy-guide",
        "cis-settings-guide",
        "administrator-guide",
    }
    assert {guide["review"] for guide in guides.values()} == {"affected"}
    assert inventory["untouched_guide_rule"] == (
        "Every guide with review=unaffected must record a non-empty reason. "
        "No published guide is unaffected for BPM096-M10-01."
    )
    for guide in guides.values():
        assert guide["primary_reader"]
        assert guide["owners"]
        assert guide["source_topics"]
        assert guide["reason"]


def test_every_reader_and_failure_recovery_boundary_has_one_primary_guide_owner() -> None:
    inventory = _inventory()
    guide_names = set(inventory["guide_maps"])
    expected_owners = {
        "atomic-create-duplicate",
        "eight-step-editor",
        "extension-policy-and-amo-boundary",
        "url-site-policy-shapes",
        "certificate-trust-policy-shapes",
        "preset-cis-selection",
        "baseline-and-value-attribution",
        "cis-conflict-and-manual-review",
        "public-preparation-and-profile-api",
        "firefox-interchange",
        "deployment-and-support-boundary",
    }
    owners = inventory["reader_ownership"]
    assert set(owners) == expected_owners
    for owner in owners.values():
        assert owner["guide"] in guide_names
        assert owner["topics"]
        assert owner["boundary"]

    assert (
        "no target and does not mutate the source" in owners["atomic-create-duplicate"]["boundary"]
    )
    assert "no XPI/result URL is fetched" in owners["extension-policy-and-amo-boundary"]["boundary"]
    assert (
        "does not upload, open, hash, read, or validate"
        in owners["certificate-trust-policy-shapes"]["boundary"]
    )
    assert (
        "never assert browser, deployment, or organization compliance"
        in owners["cis-conflict-and-manual-review"]["boundary"]
    )


def test_inventory_topic_ids_are_current_english_keymap_sources() -> None:
    inventory = _inventory()
    keys = _keyrefs()
    topic_ids = {
        topic_id
        for guide in inventory["guide_maps"].values()
        for topic_id in guide["source_topics"]
    }
    topic_ids.update(
        topic_id for owner in inventory["reader_ownership"].values() for topic_id in owner["topics"]
    )
    topic_ids.update(inventory["search_and_contextual_help"]["required_action_topics"].values())
    assert topic_ids <= keys


def test_search_help_screenshot_and_stale_claim_follow_up_owners_are_explicit() -> None:
    inventory = _inventory()
    help_scope = inventory["search_and_contextual_help"]
    assert help_scope["owner"] == "BPM096-M10-04"
    assert set(help_scope["required_action_topics"]) == {
        "preparation-create",
        "preparation-duplicate",
        "guided-editor",
        "extensions",
        "urls-sites-navigation",
        "certificates-trust",
        "cis-review",
        "profile-api",
    }
    assert "separate from the documentation assistant" in help_scope["rule"]

    screenshots = inventory["screenshot_disposition"]
    assert screenshots["owner"] == "BPM096-M10-04"
    assert screenshots["affected_scenarios"] == [
        "library-overview",
        "guided-editor-overview",
        "guided-settings-search",
        "all-settings-review",
        "json-editor",
    ]
    assert screenshots["new_required_subjects"] == [
        "preparation-create",
        "preparation-duplicate",
        "guided-step-2-urls-sites-navigation",
        "guided-step-4-certificates-trust",
        "guided-step-6-extensions",
    ]

    stale = inventory["stale_claim_dispositions"]
    assert set(stale) == {
        "six-guided-steps",
        "profile-baseline-guided-step",
        "new-profile-draft",
        "draft-save-recovery",
        "inline-clone-name-panel",
        "schema-selector-in-editor-chrome",
        "old-domain-ownership",
    }
    assert (
        stale["six-guided-steps"]["replacement"]
        == "eight delivered steps and their one-domain owners"
    )
    assert stale["new-profile-draft"]["status"] == "remove"
    assert stale["inline-clone-name-panel"]["status"] == "replace"
    assert stale["old-domain-ownership"]["replacement"].startswith("URLs/sites step 2")
