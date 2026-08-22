"""BPM096 source-only help, search, and screenshot refresh contract."""

from __future__ import annotations

import json
from pathlib import Path

from app.documentation.manifest import DOCUMENTATION_DEEP_HELP_TARGET_IDS

ROOT = Path(__file__).resolve().parents[4]
CONFIG = ROOT / "documentation/config"


def _json(name: str) -> dict[str, object]:
    return json.loads((CONFIG / name).read_text(encoding="utf-8"))


def test_bpm096_actions_have_canonical_help_and_search_owners() -> None:
    target_contract = _json("all-settings-help-target-map-0.9.1.json")
    search = _json("search-normalization-aliases-0.9.0.json")
    expected = {
        "preparation-create": "topic:ug-task-create-first-profile",
        "preparation-duplicate": "topic:ug-task-duplicate-profile",
        "guided-urls-sites-navigation": "policy:Homepage",
        "guided-certificates-trust": "policy:Certificates",
        "guided-extensions": "policy:ExtensionSettings",
    }

    assert target_contract["contextual_action_targets"] == {
        **expected,
        "rule": target_contract["contextual_action_targets"]["rule"],
    }
    assert {action: DOCUMENTATION_DEEP_HELP_TARGET_IDS[action] for action in expected} == expected
    aliases = {group["alias_id"]: group for group in search["alias_groups"]}
    assert aliases["profile-preparation"]["target_ids"] == [
        expected["preparation-create"],
        expected["preparation-duplicate"],
    ]
    assert aliases["guided-urls-sites-navigation"]["target_ids"] == [
        expected["guided-urls-sites-navigation"]
    ]
    assert aliases["guided-certificates-trust"]["target_ids"] == [
        expected["guided-certificates-trust"]
    ]
    assert aliases["guided-extensions"]["target_ids"] == [expected["guided-extensions"]]
