from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_compare_state_script(script_body: str) -> dict:
    source = (REPO_ROOT / "app" / "static" / "profiles_compare_state.js").read_text(
        encoding="utf-8"
    )
    script = textwrap.dedent(
        f"""
        const assert = require("node:assert/strict");
        const vm = require("node:vm");
        const context = {{ window: {{}} }};
        vm.createContext(context);
        vm.runInContext({source!r}, context);
        const compareState = context.window.BPMProfilesCompareState;
        {script_body}
        """
    )
    result = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return json.loads(result.stdout)


def test_compare_state_normalizes_nested_objects_and_arrays() -> None:
    result = _run_compare_state_script(
        """
        const normalized = compareState.normalizeValue({
            beta: [{ z: 1, a: 2 }],
            alpha: { z: true, a: false },
        });
        assert.deepEqual(Object.keys(normalized), ["alpha", "beta"]);
        assert.deepEqual(Object.keys(normalized.alpha), ["a", "z"]);
        assert.deepEqual(Object.keys(normalized.beta[0]), ["a", "z"]);
        console.log(JSON.stringify(normalized));
        """
    )

    assert result == {
        "alpha": {"a": False, "z": True},
        "beta": [{"a": 2, "z": 1}],
    }


def test_compare_state_collects_missing_branches_and_array_changes() -> None:
    result = _run_compare_state_script(
        """
        const paths = compareState.collectDiffPaths(
            {
                Homepage: { URL: "https://example.test" },
                SearchEngines: { Add: [{ Name: "Internal", URLTemplate: "https://a.test" }] },
            },
            {
                SearchEngines: { Add: [{ Name: "Internal", URLTemplate: "https://b.test" }] },
            },
        );
        console.log(JSON.stringify(paths));
        """
    )

    assert result == [["Homepage", "URL"], ["SearchEngines", "Add"]]


def test_compare_state_collects_policy_and_preference_rows_in_stable_order() -> None:
    result = _run_compare_state_script(
        """
        const rows = compareState.collectProfileSettingKeys(
            {
                SearchBar: "unified",
                DisableTelemetry: true,
                Preferences: {
                    "browser.tabs.warnOnClose": false,
                    "browser.startup.homepage": "https://left.test",
                },
            },
            {
                Homepage: { URL: "https://right.test" },
                Preferences: {
                    "browser.startup.homepage": "https://right.test",
                },
            },
        );
        console.log(JSON.stringify(rows));
        """
    )

    assert [row["id"] for row in result] == [
        "policy:DisableTelemetry",
        "policy:Homepage",
        "policy:SearchBar",
        "preference:browser.startup.homepage",
        "preference:browser.tabs.warnOnClose",
    ]
    assert result[0]["settingKey"] == "DisableTelemetry"
    assert result[3]["settingKey"] == "Preferences.browser.startup.homepage"


def test_compare_state_reads_and_formats_policy_and_preference_values() -> None:
    result = _run_compare_state_script(
        """
        const flags = {
            DisableTelemetry: true,
            Homepage: { Locked: true, URL: "https://example.test" },
            Preferences: { "browser.tabs.warnOnClose": false },
        };
        const policy = compareState.collectProfileSettingKeys(flags, {})[0];
        const preference = {
            kind: "preference",
            preferenceName: "browser.tabs.warnOnClose",
        };
        const missing = {
            kind: "preference",
            preferenceName: "browser.startup.homepage",
        };
        const payload = {
            policy: compareState.formatCompareValue(compareState.readSettingValue(flags, policy)),
            objectValue: compareState.formatCompareValue(
                compareState.readSettingValue(flags, { kind: "policy", policyId: "Homepage" }),
            ),
            preference: compareState.formatCompareValue(compareState.readSettingValue(flags, preference)),
            missing: compareState.formatCompareValue(compareState.readSettingValue(flags, missing)),
        };
        console.log(JSON.stringify(payload));
        """
    )

    assert result == {
        "policy": "true",
        "objectValue": '{"Locked":true,"URL":"https://example.test"}',
        "preference": "false",
        "missing": "Not set",
    }
