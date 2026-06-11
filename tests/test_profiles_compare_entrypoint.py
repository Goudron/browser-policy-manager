from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_compare_script(script_body: str) -> dict:
    compare_state_source = (
        REPO_ROOT / "app" / "static" / "profiles_compare_state.js"
    ).read_text(encoding="utf-8")
    source = (REPO_ROOT / "app" / "static" / "profiles_compare.js").read_text(
        encoding="utf-8"
    )
    script = textwrap.dedent(
        f"""
        const assert = require("node:assert/strict");
        const vm = require("node:vm");
        const context = {{ window: {{}} }};
        vm.createContext(context);
        vm.runInContext({compare_state_source!r}, context);
        vm.runInContext({source!r}, context);
        const compare = context.window.BPMProfilesCompare;
        const compareState = context.window.BPMProfilesCompareState;
        {script_body}
        """
    )
    result = subprocess.run(
        ["node", "-e", script],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_compare_entrypoint_builds_active_profile_search_filters() -> None:
    result = _run_compare_script(
        """
        const filters = compare.buildProfileSearchFilters("  Finance  ");
        console.log(JSON.stringify(filters));
        """
    )

    assert result == {
        "q": "Finance",
        "lifecycle": "active",
        "includeDeleted": False,
        "sort": "updated_at",
        "order": "desc",
    }


def test_compare_entrypoint_initializes_two_independent_selection_sides() -> None:
    result = _run_compare_script(
        """
        const state = compare.createInitialState();
        state.left.selected = { id: 1, name: "Left" };
        console.log(JSON.stringify({
            leftSelected: state.left.selected.name,
            rightSelected: state.right.selected,
            sameObject: state.left === state.right,
        }));
        """
    )

    assert result == {
        "leftSelected": "Left",
        "rightSelected": None,
        "sameObject": False,
    }


def test_compare_entrypoint_resolves_optional_preselected_profile_ids() -> None:
    result = _run_compare_script(
        """
        const selected = compare.resolvePreselectedProfileIds({
            href: "http://bpm.test/profiles/compare?left=7&right=abc&extra=9",
        });
        const invalid = compare.resolvePreselectedProfileIds({
            href: "http://bpm.test/profiles/compare?left=-1&right=0",
        });
        console.log(JSON.stringify({ selected, invalid }));
        """
    )

    assert result == {
        "selected": {"left": 7, "right": None},
        "invalid": {"left": None, "right": None},
    }


def test_compare_entrypoint_formats_profile_summary_and_escapes_html() -> None:
    result = _run_compare_script(
        """
        const summary = compare.formatProfileSummary(
            { schema_version: "release-151", updated_at: "2026-06-05T12:00:00Z" },
            (value) => `Firefox ${value}`,
        );
        const escaped = compare.escapeHtml("<b>Managed & safe</b>");
        console.log(JSON.stringify({ summary, escaped }));
        """
    )

    assert result == {
        "summary": "Firefox release-151 • 2026-06-05T12:00:00Z",
        "escaped": "&lt;b&gt;Managed &amp; safe&lt;/b&gt;",
    }


def test_compare_entrypoint_builds_two_column_setting_rows() -> None:
    fixture = json.loads(
        (REPO_ROOT / "tests" / "fixtures" / "profile_compare_contract.json").read_text(
            encoding="utf-8"
        )
    )
    result = _run_compare_script(
        f"""
        const contract = {json.dumps(fixture)};
        const rows = compare.buildCompareRows(
            contract.profiles.left,
            contract.profiles.right,
            compareState,
        );
        console.log(JSON.stringify(rows.map((row) => ({{
            id: row.id,
            kind: row.kind,
            settingKey: row.settingKey,
            leftState: row.left.state,
            leftStateLabel: row.left.stateLabel,
            leftDisplay: row.left.displayValue,
            rightState: row.right.state,
            rightStateLabel: row.right.stateLabel,
            rightDisplay: row.right.displayValue,
            changed: row.changed,
        }}))));
        """
    )

    assert [row["id"] for row in result] == [
        "policy:DisableTelemetry",
        "policy:Homepage",
        "policy:SearchBar",
        "preference:browser.startup.homepage",
        "preference:browser.tabs.warnOnClose",
    ]
    assert result[0] == {
        "id": "policy:DisableTelemetry",
        "kind": "policy",
        "settingKey": "DisableTelemetry",
        "leftState": "equal",
        "leftStateLabel": "Same value",
        "leftDisplay": "true",
        "rightState": "equal",
        "rightStateLabel": "Same value",
        "rightDisplay": "true",
        "changed": False,
    }
    assert result[1]["leftState"] == "different"
    assert result[1]["leftStateLabel"] == "Different value"
    assert result[1]["rightState"] == "missing"
    assert result[1]["rightStateLabel"] == "Missing"
    assert result[1]["rightDisplay"] == "Missing"
    assert result[2]["leftState"] == "missing"
    assert result[2]["rightState"] == "different"
    assert result[3]["leftState"] == "different"
    assert result[3]["rightState"] == "different"
    assert result[4]["leftState"] == "equal"
    assert result[4]["rightState"] == "equal"


def test_compare_entrypoint_labels_managed_preferences_as_first_class_settings() -> None:
    result = _run_compare_script(
        """
        const preferenceLabels = compare.buildPreferenceLabelLookup(
            {
                known_preferences: [
                    {
                        pref: "browser.startup.homepage",
                        label_key: "",
                        fallback: "Homepage URL",
                    },
                    {
                        pref: "browser.tabs.warnOnClose",
                        label_key: "profiles.warn_tabs",
                        fallback: "browser.tabs.warnOnClose",
                    },
                ],
            },
            { "profiles.warn_tabs": "Warn before closing tabs" },
        );
        const rows = compare.buildCompareRows(
            {
                flags: {
                    Preferences: {
                        "browser.startup.homepage": { Status: "locked", Value: "https://left.test" },
                        "unknown.preference": { Status: "default", Value: true },
                    },
                },
            },
            {
                flags: {
                    Preferences: {
                        "browser.tabs.warnOnClose": { Status: "default", Value: true },
                    },
                },
            },
            compareState,
            {
                preferenceLabels,
                preferenceKindLabel: "Managed preference",
                policyKindLabel: "Policy",
            },
        );
        console.log(JSON.stringify(rows.map((row) => ({
            id: row.id,
            kind: row.kind,
            kindLabel: row.kindLabel,
            label: row.label,
            settingKey: row.settingKey,
        }))));
        """
    )

    assert result == [
        {
            "id": "preference:browser.startup.homepage",
            "kind": "preference",
            "kindLabel": "Managed preference",
            "label": "Homepage URL",
            "settingKey": "Preferences.browser.startup.homepage",
        },
        {
            "id": "preference:browser.tabs.warnOnClose",
            "kind": "preference",
            "kindLabel": "Managed preference",
            "label": "Warn before closing tabs",
            "settingKey": "Preferences.browser.tabs.warnOnClose",
        },
        {
            "id": "preference:unknown.preference",
            "kind": "preference",
            "kindLabel": "Managed preference",
            "label": "unknown.preference",
            "settingKey": "Preferences.unknown.preference",
        },
    ]


def test_compare_entrypoint_supports_accessible_value_state_labels() -> None:
    result = _run_compare_script(
        """
        const rows = compare.buildCompareRows(
            { flags: { DisableTelemetry: true, Homepage: { URL: "https://left.test" } } },
            { flags: { DisableTelemetry: true, SearchBar: "separate" } },
            compareState,
            {
                stateLabels: {
                    missing: "Missing",
                    equal: "Same",
                    different: "Changed",
                },
            },
        );
        console.log(JSON.stringify(rows.map((row) => ({
            id: row.id,
            leftState: row.left.state,
            leftLabel: row.left.stateLabel,
            rightState: row.right.state,
            rightLabel: row.right.stateLabel,
        }))));
        """
    )

    assert result == [
        {
            "id": "policy:DisableTelemetry",
            "leftState": "equal",
            "leftLabel": "Same",
            "rightState": "equal",
            "rightLabel": "Same",
        },
        {
            "id": "policy:Homepage",
            "leftState": "different",
            "leftLabel": "Changed",
            "rightState": "missing",
            "rightLabel": "Missing",
        },
        {
            "id": "policy:SearchBar",
            "leftState": "missing",
            "leftLabel": "Missing",
            "rightState": "different",
            "rightLabel": "Changed",
        },
    ]
