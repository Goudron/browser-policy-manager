from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

from tests.web_profiles_page_helpers import static_source

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = REPO_ROOT / "app" / "static"


def test_all_settings_search_grouping_contract_is_wired():
    search_source = static_source("profiles_settings_search.js")
    css_source = static_source("profiles_css/20-editor-wizard.css")
    template_source = (REPO_ROOT / "app/templates/profiles/_page_settings_workspace.html").read_text(
        encoding="utf-8"
    )
    dom_source = static_source("profiles_dom.js")
    bootstrap_source = static_source("profiles_bootstrap_core.js")

    for snippet in (
        "searchGroup = \"actions\"",
        "searchScopes = []",
        "function matchesSearchScope(entry, scope)",
        "function syncScopeButtons()",
        "activeSearchScope = button.dataset.settingsSearchScope || \"all\"",
        "function resolveAllSettingsEntryTarget(targetKey)",
        "const entryTarget = resolveAllSettingsEntryTarget(normalizedTarget);",
        "findAllSettingsEntryTarget?.(entryTarget)",
        "[data-settings-detail-primary-focus], .all-settings-detail-editor [data-schema-policy-field]",
        "searchGroup: entry.kind === \"preference\"",
        "function dedupeTargets(matches)",
        "function allSettingsSearchGroups()",
        "function renderGroupedResults(matches)",
        "function firstResultButton()",
        "function activateSearchResult(button)",
        "profiles.settings_search_group_configured",
        "profiles.settings_search_group_available_policies",
        "profiles.settings_search_group_preferences",
        "profiles.settings_search_group_actions",
        "dataset.settingsSearchGroup = group.id",
        "scope: activeSearchScope",
        "dedupeTargets: isAllSettingsRoute",
    ):
        assert snippet in search_source

    for snippet in (
        ".wizard-settings-search-group",
        ".wizard-settings-search-group-title",
        ".wizard-settings-search-scope",
        ".wizard-settings-search-scope-button",
    ):
        assert snippet in css_source

    assert 'wizardSettingsSearchScopeEl: byId("wizard-settings-search-scope")' in dom_source
    assert 'wizardSettingsSearchScopeButtons: all("[data-settings-search-scope]")' in dom_source
    assert "wizardSettingsSearchScopeEl," in bootstrap_source
    assert "wizardSettingsSearchScopeButtons," in bootstrap_source
    assert "profiles.settings_search_scope_review" in template_source


def test_settings_search_builds_known_preference_sections_without_reference_errors():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_settings_search.js"}", "utf8"));

        const search = window.BPMProfilesSettingsSearch.create({{
            documentRef: {{ body: {{ dataset: {{ profilesTemplateKind: "settings" }} }} }},
            dependencies: {{
                t: (key, fallback = "") => fallback || key,
                escapeHtml: (value) => String(value || ""),
                humanizeIdentifier: (value) => String(value || ""),
                normalizeSearchText: (value) => String(value || "").toLowerCase(),
                setWizardStep: () => {{}},
                getAllSettingsSearchEntries: () => [],
                findAllSettingsEntryTarget: () => null,
            }},
            wizardSettingsCatalog: {{
                sections: [{{
                    id: "privacy",
                    preferences: {{
                        id: "privacy",
                        title_key: "privacy.title",
                        body_key: "privacy.body",
                        prefixes: ["browser.safebrowsing."],
                        gui_groups: [],
                        controls: [],
                        bundles: [],
                        known_preferences: [{{
                            pref: "browser.safebrowsing.malware.enabled",
                            status: "locked",
                            type: "boolean",
                        }}],
                    }},
                }}],
            }},
            wizardSearchSectionSteps: {{
                privacy: {{ step: 4, key: "privacy.step", fallback: "Privacy" }},
            }},
        }});

        search.buildIndex();
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)


def test_all_settings_search_runtime_groups_scopes_and_dedupes_targets():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{
            Event: class {{ constructor(type) {{ this.type = type; }} }},
            setTimeout: (callback) => callback(),
        }};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_settings_search.js"}", "utf8"));

        function fakeElement(tagName = "div") {{
            const state = {{ click: null, keydown: null, classes: {{}}, attrs: {{}}, focused: false, scrolled: false }};
            const element = {{
                tagName,
                type: "",
                value: "",
                hidden: false,
                className: "",
                textContent: "",
                _innerHTML: "",
                dataset: {{}},
                children: [],
                attrs: state.attrs,
                classList: {{
                    toggle: (name, active) => {{ state.classes[name] = Boolean(active); }},
                    add: (name) => {{ state.classes[name] = true; }},
                    remove: (name) => {{ state.classes[name] = false; }},
                }},
                addEventListener(eventName, handler) {{
                    if (eventName === "click") state.click = handler;
                    if (eventName === "keydown") state.keydown = handler;
                }},
                appendChild(child) {{
                    this.children.push(child);
                    return child;
                }},
                setAttribute(name, value) {{
                    this.attrs[name] = String(value);
                }},
                dispatchEvent: () => {{}},
                focus: () => {{ state.focused = true; }},
                scrollIntoView: () => {{ state.scrolled = true; }},
                click: () => state.click?.(),
                closest: () => null,
                matches: () => false,
                querySelector(selector) {{
                    const stack = [...this.children];
                    while (stack.length) {{
                        const item = stack.shift();
                        if (
                            selector === "[data-settings-search-target]"
                            && item.dataset.settingsSearchTarget
                        ) {{
                            return item;
                        }}
                        stack.push(...(item.children || []));
                    }}
                    return null;
                }},
                state,
            }};
            Object.defineProperty(element, "innerHTML", {{
                get() {{ return this._innerHTML; }},
                set(value) {{
                    this._innerHTML = String(value);
                    this.children = [];
                }},
            }});
            return element;
        }}

        function resultTargets(resultsEl) {{
            return resultsEl.children.flatMap((group) =>
                group.children.filter((child) => child.dataset.settingsSearchTarget)
            ).map((button) => button.dataset.settingsSearchTarget);
        }}

        let bundleClicks = 0;
        const listPanel = fakeElement("section");
        const bundleAction = {{
            click: () => {{ bundleClicks += 1; }},
        }};
        const documentRef = {{
            body: {{ dataset: {{ profilesTemplateKind: "settings" }} }},
            createElement: (tagName) => fakeElement(tagName),
            getElementById: (id) => id === "all-settings-list-panel" ? listPanel : null,
            querySelector: (selector) => selector === '[data-settings-target="preference-bundle:proxy_bundle"]'
                ? bundleAction
                : null,
        }};
        const input = fakeElement("input");
        input.value = "proxy";
        const results = fakeElement("div");
        const clear = fakeElement("button");
        const meta = fakeElement("div");
        const scopeEl = fakeElement("div");
        const scopeButtons = ["all", "review", "configured", "catalog"].map((scope) => {{
            const button = fakeElement("button");
            button.dataset.settingsSearchScope = scope;
            return button;
        }});
        const routeState = {{
            activeMode: "review",
            searchQuery: "",
            focusedTarget: "",
            setSearchQuery(query) {{ this.searchQuery = query; }},
            setFocusedTarget(target) {{ this.focusedTarget = target; }},
            getSnapshot() {{ return {{ activeMode: this.activeMode }}; }},
        }};
        const translations = {{
            "profiles.settings_search_hint": "Hint",
            "profiles.settings_search_empty": "Empty",
            "profiles.settings_search_match_one": "One {{count}}",
            "profiles.settings_search_match_many": "Many {{count}}",
            "profiles.settings_search_group_configured": "Configured settings",
            "profiles.settings_search_group_available_policies": "Available policies",
            "profiles.settings_search_group_preferences": "Preferences",
            "profiles.settings_search_group_actions": "Actions",
            "profiles.settings_search_scope_all": "All",
            "profiles.settings_search_scope_review": "Review",
            "profiles.settings_search_scope_configured": "Configured",
            "profiles.settings_search_scope_catalog": "Catalog",
            "profiles.settings_list_state_configured": "Configured",
            "profiles.settings_list_state_available": "Available",
            "profiles.settings_list_value_not_configured": "Not configured",
            "profiles.settings_filter_guided_covered": "Guided",
            "profiles.settings_filter_all_settings_only": "All settings",
            "profiles.settings_filter_invalid": "Invalid",
            "profiles.settings_filter_deprecated": "Deprecated",
            "profiles.settings_filter_raw": "Raw",
            "profiles.settings_filter_unknown": "Unknown",
            "profiles.wizard_settings_search_step": "Step",
            "profiles.wizard_settings_search_kind_control": "Control",
            "profiles.wizard_settings_search_kind_preferences_section": "Preferences section",
            "profiles.wizard_settings_search_kind_preference_preset": "Preference preset",
            "profiles.wizard_settings_search_kind_preference_bundle": "Preference bundle",
            "profiles.wizard_settings_search_kind_known_preference": "Known preference",
            "profiles.wizard_settings_search_kind_search_preset": "Search preset",
            "profiles.wizard_settings_search_kind_policy_blueprint": "Schema policy",
            "profiles.wizard_settings_search_kind_all_settings_policy": "Policy setting",
            "profiles.wizard_settings_search_kind_all_settings_preference": "Managed preference",
        }};
        const t = (key, fallback = "") => translations[key] || fallback || key;
        const openedTargets = [];
        const detailPanel = fakeElement("section");
        const search = window.BPMProfilesSettingsSearch.create({{
            documentRef,
            elements: {{
                wizardSettingsSearchInputEl: input,
                wizardSettingsSearchMetaEl: meta,
                wizardSettingsSearchResultsEl: results,
                wizardSettingsSearchClearEl: clear,
                wizardSettingsSearchScopeEl: scopeEl,
                wizardSettingsSearchScopeButtons: scopeButtons,
            }},
            dependencies: {{
                t,
                escapeHtml: (value) => String(value || ""),
                humanizeIdentifier: (value) => String(value || "").replace(/([A-Z])/g, " $1"),
                normalizeSearchText: (value) => String(value || "").toLowerCase(),
                setWizardStep: () => {{}},
                findAllSettingsEntryTarget: (target) => {{
                    openedTargets.push(target);
                    return detailPanel;
                }},
                getAllSettingsSearchEntries: () => [
                    {{
                        id: "Proxy",
                        label: "Proxy",
                        kind: "policy",
                        kindLabel: "Policy",
                        categoryId: "browser-access",
                        categoryLabel: "Browser access",
                        configured: true,
                        value: "system",
                        attentionFlags: {{ reviewRequired: true }},
                        target: "policy:Proxy",
                    }},
                    {{
                        id: "ProxyAvailable",
                        label: "Proxy available",
                        kind: "policy",
                        kindLabel: "Policy",
                        categoryId: "browser-access",
                        categoryLabel: "Browser access",
                        configured: false,
                        value: "Not configured",
                        target: "policy:ProxyAvailable",
                    }},
                    {{
                        id: "browser.proxy.type",
                        label: "browser.proxy.type",
                        kind: "preference",
                        kindLabel: "Managed preference",
                        categoryId: "privacy-security",
                        categoryLabel: "Security & privacy",
                        configured: true,
                        value: "locked",
                        target: "known-preference:browser.proxy.type",
                        editor: {{ preferenceSectionId: "network" }},
                    }},
                ],
            }},
            state: {{
                allSettingsRouteState: routeState,
            }},
            wizardSettingsCatalog: {{
                sections: [
                    {{
                        id: "network",
                        ui_maps: {{
                            main: [{{ id: "proxy", label_key: "area.proxy", fallback: "Proxy" }}],
                        }},
                        ui_controls: {{
                            main: [
                                {{
                                    label_key: "control.proxy",
                                    fallback: "Proxy",
                                    area_id: "proxy",
                                    target: "policy:Proxy",
                                }},
                                {{
                                    label_key: "control.proxy.mode",
                                    fallback: "Proxy mode action",
                                    area_id: "proxy",
                                    target: "policy:ProxyMode",
                                }},
                            ],
                        }},
                    }},
                ],
            }},
            wizardSearchSectionSteps: {{
                "network": {{ step: 2, key: "step.network", fallback: "Network" }},
                "browser-access": {{ step: 0, key: "category.browser", fallback: "Browser access" }},
                "privacy-security": {{ step: 0, key: "category.privacy", fallback: "Security & privacy" }},
            }},
            settingsTargetAliases: {{
                "policy:Proxy": "all-settings-entry:policy:Proxy",
            }},
        }});

        search.renderResults();

        const groupIds = results.children.map((child) => child.dataset.settingsSearchGroup);
        const expectedGroups = ["configured_settings", "available_policies", "preferences", "actions"];
        if (groupIds.join("|") !== expectedGroups.join("|")) {{
            throw new Error(`unexpected group order ${{groupIds.join("|")}}`);
        }}
        const targets = resultTargets(results);
        if (targets.filter((target) => target === "all-settings-entry:policy:Proxy").length !== 1) {{
            throw new Error("duplicate configured target");
        }}
        if (!targets.includes("all-settings-entry:policy:ProxyAvailable")) throw new Error("available policy missing");
        if (!targets.includes("all-settings-entry:preference:browser.proxy.type")) throw new Error("preference missing");
        if (!targets.includes("policy:ProxyMode")) throw new Error("action missing");
        if (results.hidden) throw new Error("grouped results hidden");
        if (!meta.textContent.includes(String(targets.length))) throw new Error("grouped result count missing");
        if (scopeEl.hidden) throw new Error("scope controls hidden");
        if (!scopeButtons[0].state.classes["is-active"]) throw new Error("all scope not active");

        const firstResult = results.querySelector("[data-settings-search-target]");
        const arrowDownEvent = {{
            key: "ArrowDown",
            prevented: false,
            preventDefault() {{ this.prevented = true; }},
        }};
        input.state.keydown(arrowDownEvent);
        if (!arrowDownEvent.prevented) throw new Error("ArrowDown did not prevent default");
        if (!firstResult.state.focused) throw new Error("ArrowDown did not focus first result");

        const enterEvent = {{
            key: "Enter",
            prevented: false,
            preventDefault() {{ this.prevented = true; }},
        }};
        input.state.keydown(enterEvent);
        if (!enterEvent.prevented) throw new Error("Enter did not prevent default");
        if (openedTargets.at(-1) !== "all-settings-entry:policy:Proxy") throw new Error("Enter did not open first result");
        if (routeState.focusedTarget !== "all-settings-entry:policy:Proxy") throw new Error("Enter did not preserve focused target");
        if (!detailPanel.state.scrolled) throw new Error("Enter did not reveal focused target");

        scopeButtons.find((button) => button.dataset.settingsSearchScope === "review").click();
        if (routeState.getSnapshot().activeMode !== "review") throw new Error("scope click changed active mode");
        if (!scopeButtons.find((button) => button.dataset.settingsSearchScope === "review").state.classes["is-active"]) {{
            throw new Error("review scope not active");
        }}
        const reviewTargets = resultTargets(results);
        if (reviewTargets.join("|") !== "all-settings-entry:policy:Proxy") {{
            throw new Error(`unexpected review scope targets ${{reviewTargets.join("|")}}`);
        }}

        scopeButtons.find((button) => button.dataset.settingsSearchScope === "configured").click();
        const configuredTargets = resultTargets(results);
        if (!configuredTargets.includes("all-settings-entry:policy:Proxy")) throw new Error("configured scope missing policy");
        if (!configuredTargets.includes("all-settings-entry:preference:browser.proxy.type")) throw new Error("configured scope missing preference");
        if (configuredTargets.includes("all-settings-entry:policy:ProxyAvailable")) throw new Error("configured scope leaked available policy");
        if (configuredTargets.includes("policy:ProxyMode")) throw new Error("configured scope leaked action");

        scopeButtons.find((button) => button.dataset.settingsSearchScope === "catalog").click();
        const catalogTargets = resultTargets(results);
        if (!catalogTargets.includes("all-settings-entry:policy:ProxyAvailable")) throw new Error("catalog scope missing available policy");
        if (catalogTargets.includes("policy:ProxyMode")) throw new Error("catalog scope leaked action");

        if (search.findTarget("policy:Proxy") !== detailPanel) throw new Error("policy focus did not open detail");
        if (openedTargets.at(-1) !== "all-settings-entry:policy:Proxy") throw new Error("policy focus target mismatch");
        if (search.findTarget("known-preference:browser.proxy.type") !== detailPanel) throw new Error("preference focus did not open detail");
        if (openedTargets.at(-1) !== "all-settings-entry:preference:browser.proxy.type") throw new Error("preference focus target mismatch");
        if (search.findTarget("pref-section:network") !== detailPanel) throw new Error("preference section focus did not open detail");
        if (openedTargets.at(-1) !== "all-settings-entry:preference:browser.proxy.type") {{
            throw new Error("preference section focus target mismatch");
        }}
        if (search.findTarget("preference-bundle:proxy_bundle") !== listPanel) {{
            throw new Error("preference bundle did not return list panel");
        }}
        if (bundleClicks !== 1) throw new Error("preference bundle action did not run");
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)
