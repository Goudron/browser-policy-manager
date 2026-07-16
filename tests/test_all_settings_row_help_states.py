import json
import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = REPO_ROOT / "app/static"


def test_all_settings_row_help_states_never_emit_broken_links():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / 'profiles_all_settings_state.js'}", "utf8"));
        eval(fs.readFileSync("{STATIC_ROOT / 'profiles_all_settings_list.js'}", "utf8"));

        const entries = {json.dumps([
            {
                "id": "KnownPolicy", "label": "KnownPolicy", "kind": "policy",
                "categoryId": "general", "configured": True, "value": "true",
                "unknown": False, "rawFallback": False, "sources": [],
            },
            {
                "id": "MissingPolicy", "label": "MissingPolicy", "kind": "policy",
                "categoryId": "general", "configured": True, "value": "true",
                "unknown": False, "rawFallback": False, "sources": [],
            },
            {
                "id": "UnknownPolicy", "label": "UnknownPolicy", "kind": "policy",
                "categoryId": "raw-unmapped", "configured": True, "value": "true",
                "unknown": True, "rawFallback": False, "sources": ["unknown"],
            },
            {
                "id": "raw.preference", "label": "raw.preference", "kind": "preference",
                "categoryId": "raw-unmapped", "configured": True, "value": "true",
                "unknown": False, "rawFallback": True, "knownPreference": None, "sources": ["raw-fallback"],
            },
        ])};
        const labels = {{
            "profiles.all_settings.row_help.open": "Open {{setting}}",
            "profiles.all_settings.row_help.missing": "Missing {{setting}}",
            "profiles.all_settings.row_help.unavailable": "Unavailable {{setting}}",
            "profiles.all_settings.row_help.raw_not_applicable": "Raw {{setting}}",
            "profiles.all_settings.row_help.unknown_not_supported": "Unknown {{setting}}",
            "profiles.settings_list_column_setting": "Setting",
            "profiles.settings_list_column_value": "Value",
            "profiles.settings_list_kind_policy": "Policy",
            "profiles.settings_list_kind_preference": "Preference",
            "profiles.settings_list_state_configured": "Configured",
            "profiles.settings_list_state_available": "Available",
            "profiles.settings_list_summary": "{{total}}",
            "profiles.settings_list_summary_filtered": "{{visible}}",
            "profiles.settings_list_empty": "Empty",
            "profiles.settings_list_filtered_empty": "Filtered empty",
        }};
        const t = (key) => labels[key] || key;

        function element() {{
            return {{
                hidden: false, innerHTML: "", textContent: "",
                addEventListener: () => {{}}, querySelectorAll: () => [], querySelector: () => null,
            }};
        }}
        function render(status, links) {{
            const listEl = element();
            const routeState = window.BPMProfilesAllSettingsState.create({{ activeMode: "catalog" }});
            const list = window.BPMProfilesAllSettingsList.create({{
                documentRef: {{ documentElement: {{ lang: "en" }} }},
                elements: {{
                    allSettingsListEl: listEl,
                    allSettingsListSummaryEl: element(),
                    allSettingsListEmptyEl: element(),
                    allSettingsFilterButtons: [],
                    allSettingsSourceFilterButtons: [],
                }},
                dependencies: {{
                    t,
                    escapeHtml: (value) => String(value ?? ""),
                    getCurrentLang: () => "en",
                    readWizardSchemaSource: () => ({{ ok: true, data: {{}} }}),
                    allSettingsRouteState: routeState,
                    settingsInventory: {{ collect: () => entries }},
                    documentationRowHelpLinks: links,
                    documentationRowHelpStatus: status,
                    onSelectionChange: () => {{}},
                }},
                allSettingsCategoryCatalog: {{}},
            }});
            list.render();
            return listEl.innerHTML;
        }}

        const available = render("available", {{
            "policy:KnownPolicy": {{ en: "/help/en/known-policy" }},
        }});
        if ((available.match(/\\shref=/g) || []).length !== 1) throw new Error("broken href emitted");
        if (!available.includes('data-settings-entry-help-disposition="linked"')) throw new Error("linked missing");
        if (!available.includes('data-settings-entry-help-disposition="missing_documentation"')) throw new Error("missing state missing");
        if (!available.includes('data-settings-entry-help-disposition="unsupported_unknown"')) throw new Error("unknown state missing");
        if (!available.includes('data-settings-entry-help-disposition="not_applicable_raw"')) throw new Error("raw state missing");
        if ((available.match(/role="img"/g) || []).length !== 3) throw new Error("no-link indicators are not static");

        for (const status of [
            "artifact_unavailable",
            "artifact_stale",
            "artifact_incomplete",
            "artifact_incompatible",
        ]) {{
            const unavailable = render(status, {{}});
            if ((unavailable.match(/\\shref=/g) || []).length !== 0) {{
                throw new Error(`${{status}} emitted href`);
            }}
            if (!unavailable.includes(`data-settings-entry-help-disposition="${{status}}"`)) {{
                throw new Error(`${{status}} state missing`);
            }}
            if (!unavailable.includes("Unavailable MissingPolicy")) {{
                throw new Error(`${{status}} label is not localized`);
            }}
            if (!unavailable.includes('data-settings-entry-help-disposition="unsupported_unknown"')) {{
                throw new Error(`${{status}} replaced unknown disposition`);
            }}
            if (!unavailable.includes('data-settings-entry-help-disposition="not_applicable_raw"')) {{
                throw new Error(`${{status}} replaced raw disposition`);
            }}
        }}
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)


def test_search_no_link_indicators_are_noninteractive_and_localized():
    source = (STATIC_ROOT / "profiles_settings_search.js").read_text(encoding="utf-8")

    assert 'const indicator = documentRef.createElement("span")' in source
    assert 'indicator.setAttribute("role", "img")' in source
    assert 'indicator.setAttribute("aria-disabled", "true")' in source
    assert "indicator.dataset.settingsEntryHelpDisposition = disposition" in source
