from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).parent / "fixtures" / "profile_compare_contract.json"


def _load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _walk_values(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_values(child)
    else:
        yield value


def _policy_ids(flags: dict[str, Any]) -> set[str]:
    return {key for key in flags if key != "Preferences"}


def _preference_names(flags: dict[str, Any]) -> set[str]:
    preferences = flags.get("Preferences")
    if not isinstance(preferences, dict):
        return set()
    return set(preferences)


def test_profile_compare_contract_declares_two_saved_profile_model() -> None:
    contract = _load_contract()

    assert contract["schema_version"] == 1
    assert contract["backlog_item"] == "BPM087-M2-02"
    assert contract["comparison_model"] == {
        "scope": "two saved profiles",
        "row_identity": (
            "Each row represents one setting present in either profile: "
            "a top-level policy or one Preferences entry."
        ),
        "ordering": (
            "Policy rows sort by policy id before preference rows, "
            "which sort by preference name."
        ),
        "value_states": ["missing", "equal", "different"],
        "owner_metadata": "excluded",
    }

    for side in ("left", "right"):
        profile = contract["profiles"][side]
        assert isinstance(profile["id"], int)
        assert profile["name"]
        assert profile["schema_version"] == "release-152"
        assert isinstance(profile["flags"], dict)


def test_profile_compare_rows_are_union_of_policies_and_preferences() -> None:
    contract = _load_contract()
    left_flags = contract["profiles"]["left"]["flags"]
    right_flags = contract["profiles"]["right"]["flags"]
    rows = contract["expected_rows"]

    expected_policy_ids = sorted(_policy_ids(left_flags) | _policy_ids(right_flags))
    expected_preference_names = sorted(_preference_names(left_flags) | _preference_names(right_flags))
    expected_row_ids = [
        *(f"policy:{policy_id}" for policy_id in expected_policy_ids),
        *(f"preference:{name}" for name in expected_preference_names),
    ]

    assert [row["id"] for row in rows] == expected_row_ids
    assert len(expected_row_ids) == len(set(expected_row_ids))
    assert [row["kind"] for row in rows] == [
        "policy",
        "policy",
        "policy",
        "preference",
        "preference",
    ]


def test_profile_compare_value_states_and_missing_values_are_explicit() -> None:
    rows = {row["id"]: row for row in _load_contract()["expected_rows"]}

    assert rows["policy:DisableTelemetry"]["changed"] is False
    assert rows["policy:DisableTelemetry"]["left"]["state"] == "equal"
    assert rows["policy:DisableTelemetry"]["right"]["state"] == "equal"

    assert rows["policy:Homepage"]["changed"] is True
    assert rows["policy:Homepage"]["left"]["state"] == "different"
    assert rows["policy:Homepage"]["right"] == {
        "state": "missing",
        "value": None,
        "display_value": "Missing",
    }

    assert rows["policy:SearchBar"]["changed"] is True
    assert rows["policy:SearchBar"]["left"] == {
        "state": "missing",
        "value": None,
        "display_value": "Missing",
    }
    assert rows["policy:SearchBar"]["right"]["state"] == "different"

    assert rows["preference:browser.tabs.warnOnClose"]["changed"] is False
    assert rows["preference:browser.tabs.warnOnClose"]["left"]["state"] == "equal"
    assert rows["preference:browser.tabs.warnOnClose"]["right"]["state"] == "equal"


def test_profile_compare_value_display_is_stable_and_ownerless() -> None:
    contract = _load_contract()

    for value in _walk_values(contract):
        if isinstance(value, dict):
            assert "owner" not in value
        elif isinstance(value, str):
            assert "owner" not in value.casefold()

    for row in contract["expected_rows"]:
        for side in ("left", "right"):
            cell = row[side]
            value = cell["value"]
            if value is None:
                assert cell["display_value"] == "Missing"
            elif isinstance(value, bool):
                assert cell["display_value"] == str(value).lower()
            elif isinstance(value, dict):
                assert cell["display_value"] == json.dumps(value, sort_keys=True)
            else:
                assert cell["display_value"] == str(value)
