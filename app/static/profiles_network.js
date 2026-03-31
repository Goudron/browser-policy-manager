(() => {
    function create({
        documentRef = document,
        elements = {},
        dependencies = {},
        state = {},
    }) {
        const {
            t,
            linesToArray,
            textToList,
            formatBooleanSelectValue,
            parseBooleanSelectValue,
            formatSearchBarSelectValue,
            parseSearchBarSelectValue,
            fromEditorValue,
            toEditorValue,
            syncBooleanSelectGroup,
            applyBooleanSelectGroup,
            buildSearchEngineAddItemsFromWizard,
            syncSearchEngineDraftsFromPolicy,
            renderSearchEngineDrafts,
            consumeSearchEngineSyncOnce,
            clearSearchEngineSyncOnce,
            markSearchEngineSyncOnce,
            renderHomeReviewSummary,
            renderSearchReviewSummary,
            setStatus,
        } = dependencies;

        const getEditor = state.getEditor || (() => null);
        const setCurrentRaw = state.setCurrentRaw || (() => {});

        const {
            wizardHomepageUrlEl,
            wizardHomepageAdditionalEl,
            wizardHomepageStartPageEl,
            wizardHomepageLockedEl,
            wizardSearchBarEl,
            wizardSearchSuggestEl,
            wizardSearchDefaultEngineEl,
            wizardSearchPreventInstallsEl,
            wizardSearchRemoveEl,
            wizardSearchEngineAddButtonEl,
            wizardSearchEnginePresetButtons = [],
            wizardHomepageSectionStatusEl,
            wizardHomeOverridesSectionStatusEl,
            wizardFirefoxHomeSectionStatusEl,
            wizardFirefoxHomeFineTuningToggleEl,
            wizardFirefoxHomeFineTuningPanelEl,
            wizardSearchDefaultsSectionStatusEl,
            wizardSearchDefaultsFineTuningToggleEl,
            wizardSearchDefaultsFineTuningPanelEl,
            wizardFirefoxSuggestSectionStatusEl,
            wizardSearchSuggestFineTuningToggleEl,
            wizardSearchSuggestFineTuningPanelEl,
            wizardNewTabPageEl,
            wizardOverrideFirstRunEl,
            wizardOverridePostUpdateEl,
            wizardFirefoxHomeInputs = [],
            wizardFirefoxSuggestInputs = [],
            wizardProxyModeEl,
            wizardProxySectionStatusEl,
            wizardProxyLockedEl,
            wizardProxyHttpEl,
            wizardProxySslEl,
            wizardProxyFtpEl,
            wizardProxySocksEl,
            wizardProxySocksVersionEl,
            wizardProxyPassthroughEl,
            wizardProxyAutoConfigUrlEl,
            wizardProxyUseHttpForAllEl,
            wizardProxyAutoLoginEl,
            wizardProxyUseDnsEl,
            wizardProxyModeGroups = [],
            wizardNetworkEnterpriseSectionStatusEl,
            wizardNetworkEnterpriseFineTuningToggleEl,
            wizardNetworkEnterpriseFineTuningPanelEl,
        } = elements;

        const {
            wizardHomepageManagedKeys = [],
            wizardLandingScalarKeys = [],
            wizardSearchEnginesManagedKeys = [],
            wizardFirefoxHomeManagedKeys = [],
            wizardFirefoxSuggestManagedKeys = [],
            wizardProxyManagedKeys = [],
        } = state;
        let networkEnterprisePanelPreference = null;
        let firefoxHomePanelPreference = null;
        let searchDefaultsPanelPreference = null;
        let searchSuggestPanelPreference = null;

        function setManualSectionStatus(element, text) {
            if (element) {
                element.textContent = text;
            }
        }

        function hasMeaningfulValue(value) {
            if (typeof value === "boolean" || typeof value === "number") return true;
            if (typeof value === "string") return value.trim().length > 0;
            if (Array.isArray(value)) return value.some((entry) => hasMeaningfulValue(entry));
            if (value && typeof value === "object") return Object.values(value).some((entry) => hasMeaningfulValue(entry));
            return false;
        }

        function countConfiguredObjectEntries(value) {
            const currentObject = value && typeof value === "object" && !Array.isArray(value) ? value : {};
            return Object.values(currentObject).filter((entry) => hasMeaningfulValue(entry)).length;
        }

        function setPanelExpanded(panelEl, toggleEl, expanded, showLabel, hideLabel) {
            if (panelEl) {
                panelEl.hidden = !expanded;
            }
            if (toggleEl) {
                toggleEl.setAttribute("aria-expanded", expanded ? "true" : "false");
                toggleEl.textContent = expanded ? hideLabel : showLabel;
            }
        }

        function formatHomepageStartPageLabel(value) {
            if (value === "none") return t("profiles.wizard_homepage_start_none");
            if (value === "homepage") return t("profiles.wizard_homepage_start_homepage");
            if (value === "previous-session") return t("profiles.wizard_homepage_start_previous");
            if (value === "homepage-locked") return t("profiles.wizard_homepage_start_locked");
            return value;
        }

        function formatSearchBarLabel(value) {
            if (value === "unified") return t("profiles.wizard_search_bar_unified");
            if (value === "separate") return t("profiles.wizard_search_bar_separate");
            return value;
        }

        function buildFirefoxHomeDecisionSummary(firefoxHome) {
            const visible = [];
            const hidden = [];
            [
                ["Search", t("profiles.wizard_firefox_home_search_label")],
                ["TopSites", t("profiles.wizard_firefox_home_top_sites_label")],
                ["Pocket", t("profiles.wizard_firefox_home_pocket_label")],
            ].forEach(([key, label]) => {
                if (firefoxHome[key] === true) visible.push(label);
                if (firefoxHome[key] === false) hidden.push(label);
            });

            const secondaryCount = [
                "SponsoredTopSites",
                "Highlights",
                "Stories",
                "SponsoredPocket",
                "SponsoredStories",
                "Snippets",
            ].filter((key) => typeof firefoxHome[key] === "boolean").length;
            const locked = firefoxHome.Locked === true;
            const fragments = [];

            if (visible.length) {
                fragments.push(
                    t("profiles.wizard_firefox_home_section_state_visible")
                        .replace("{value}", visible.join(", ")),
                );
            }
            if (hidden.length) {
                fragments.push(
                    t("profiles.wizard_firefox_home_section_state_hidden")
                        .replace("{value}", hidden.join(", ")),
                );
            }
            if (secondaryCount > 0) {
                fragments.push(
                    t("profiles.wizard_firefox_home_section_state_more")
                        .replace("{count}", String(secondaryCount)),
                );
            }
            if (locked) {
                fragments.push(t("profiles.wizard_firefox_home_section_state_locked"));
            }

            return { fragments, secondaryCount, locked };
        }

        function getProxyGroupModes(groupEl) {
            return String(groupEl?.dataset.proxyModeGroup || "")
                .split(/\s+/)
                .map((value) => value.trim())
                .filter(Boolean);
        }

        function setProxyGroupVisibility(activeMode, disableAll = false) {
            wizardProxyModeGroups.forEach((groupEl) => {
                const groupModes = getProxyGroupModes(groupEl);
                const isActive = !disableAll && groupModes.includes(activeMode);
                groupEl.hidden = !isActive;
                groupEl.setAttribute("aria-hidden", isActive ? "false" : "true");
                groupEl.querySelectorAll("input, select, textarea, button").forEach((input) => {
                    input.disabled = disableAll || !isActive;
                });
            });
        }

        function getProxyManualSectionStatus(proxy) {
            const mode = typeof proxy?.Mode === "string" ? proxy.Mode : "";
            const endpointCount = [
                proxy?.HTTPProxy,
                proxy?.SSLProxy,
                proxy?.FTPProxy,
                proxy?.SOCKSProxy,
            ].filter((value) => typeof value === "string" && value.trim()).length;
            const passthroughCount = typeof proxy?.Passthrough === "string" && proxy.Passthrough.trim()
                ? textToList(proxy.Passthrough).length
                : 0;

            if (!mode) {
                return t("profiles.wizard_proxy_section_state_empty");
            }
            if (mode === "none") {
                return t("profiles.wizard_proxy_section_state_none");
            }
            if (mode === "system") {
                return t("profiles.wizard_proxy_section_state_system");
            }
            if (mode === "autoDetect") {
                return t("profiles.wizard_proxy_section_state_auto_detect");
            }
            if (mode === "autoConfig") {
                const autoConfigUrl = typeof proxy?.AutoConfigURL === "string" ? proxy.AutoConfigURL.trim() : "";
                if (!autoConfigUrl) {
                    return t("profiles.wizard_proxy_section_state_auto_config_missing");
                }
                return t("profiles.wizard_proxy_section_state_auto_config_ready");
            }
            if (mode === "manual") {
                if (!endpointCount) {
                    return t("profiles.wizard_proxy_section_state_manual_missing");
                }
                return t("profiles.wizard_proxy_section_state_manual_ready")
                    .replace("{count}", String(endpointCount))
                    .replace("{bypass}", String(passthroughCount));
            }
            return t("profiles.wizard_proxy_section_state_empty");
        }

        function renderProxySectionStatus(proxy = {}) {
            const resolvedProxy = proxy && typeof proxy === "object" && !Array.isArray(proxy) ? proxy : {};
            setManualSectionStatus(wizardProxySectionStatusEl, getProxyManualSectionStatus(resolvedProxy));
            setProxyGroupVisibility(typeof resolvedProxy.Mode === "string" ? resolvedProxy.Mode : "", false);
        }

        function renderNetworkEnterpriseSectionStatus(parsed = {}) {
            const resolved = parsed && typeof parsed === "object" ? parsed : {};
            const dnsConfigured = countConfiguredObjectEntries(resolved.DNSOverHTTPS);
            const authConfigured = countConfiguredObjectEntries(resolved.Authentication);
            const certificatesConfigured = countConfiguredObjectEntries(resolved.Certificates);
            const fragments = [];

            if (dnsConfigured > 0) {
                fragments.push(t("profiles.wizard_network_enterprise_section_state_doh"));
            }
            if (typeof resolved.WindowsSSO === "boolean") {
                fragments.push(t("profiles.wizard_network_enterprise_section_state_windows_sso"));
            }
            if (authConfigured > 0) {
                fragments.push(
                    t("profiles.wizard_network_enterprise_section_state_authentication")
                        .replace("{count}", String(authConfigured)),
                );
            }
            if (certificatesConfigured > 0) {
                fragments.push(
                    t("profiles.wizard_network_enterprise_section_state_certificates")
                        .replace("{count}", String(certificatesConfigured)),
                );
            }

            setManualSectionStatus(
                wizardNetworkEnterpriseSectionStatusEl,
                fragments.length
                    ? fragments.join(" • ")
                    : t("profiles.wizard_network_enterprise_section_state_empty"),
            );

            setPanelExpanded(
                wizardNetworkEnterpriseFineTuningPanelEl,
                wizardNetworkEnterpriseFineTuningToggleEl,
                networkEnterprisePanelPreference === null
                    ? (authConfigured > 0 || certificatesConfigured > 0)
                    : networkEnterprisePanelPreference,
                t("profiles.wizard_fine_tuning_show"),
                t("profiles.wizard_fine_tuning_hide"),
            );
        }

        function getHomepageManualSectionStatus(parsed) {
            const homepage = parsed?.Homepage && typeof parsed.Homepage === "object" && !Array.isArray(parsed.Homepage)
                ? parsed.Homepage
                : {};
            const url = typeof homepage.URL === "string" ? homepage.URL.trim() : "";
            const additionalCount = Array.isArray(homepage.Additional) ? homepage.Additional.length : 0;
            const startPage = typeof homepage.StartPage === "string" ? homepage.StartPage.trim() : "";
            const locked = homepage.Locked === true;
            const requiresUrl = startPage === "homepage" || startPage === "homepage-locked";

            if (!url && !additionalCount && !startPage && !locked) {
                return t("profiles.wizard_homepage_section_state_empty");
            }
            if (requiresUrl && !url) {
                return t("profiles.wizard_homepage_section_state_invalid");
            }

            const parts = [];
            if (url) {
                parts.push(t("profiles.wizard_homepage_section_state_url"));
            }
            if (additionalCount > 0) {
                parts.push(
                    t("profiles.wizard_homepage_section_state_additional")
                        .replace("{count}", String(additionalCount)),
                );
            }
            if (startPage) {
                parts.push(
                    t("profiles.wizard_homepage_section_state_start")
                        .replace("{value}", formatHomepageStartPageLabel(startPage)),
                );
            }
            if (locked) {
                parts.push(t("profiles.wizard_homepage_section_state_locked"));
            }
            return parts.join(" • ");
        }

        function getHomeOverridesManualSectionStatus(parsed) {
            const parts = [];
            if (parsed?.NewTabPage === true) {
                parts.push(t("profiles.wizard_home_overrides_section_state_new_tab_on"));
            } else if (parsed?.NewTabPage === false) {
                parts.push(t("profiles.wizard_home_overrides_section_state_new_tab_off"));
            }
            if (typeof parsed?.OverrideFirstRunPage === "string" && parsed.OverrideFirstRunPage.trim()) {
                parts.push(t("profiles.wizard_home_overrides_section_state_first_run"));
            }
            if (typeof parsed?.OverridePostUpdatePage === "string" && parsed.OverridePostUpdatePage.trim()) {
                parts.push(t("profiles.wizard_home_overrides_section_state_post_update"));
            }

            if (!parts.length) {
                return t("profiles.wizard_home_overrides_section_state_empty");
            }
            return parts.join(" • ");
        }

        function getFirefoxHomeManualSectionStatus(parsed) {
            const firefoxHome = parsed?.FirefoxHome && typeof parsed.FirefoxHome === "object" && !Array.isArray(parsed.FirefoxHome)
                ? parsed.FirefoxHome
                : {};
            const { fragments, secondaryCount, locked } = buildFirefoxHomeDecisionSummary(firefoxHome);

            if (!fragments.length && !secondaryCount && !locked) {
                return t("profiles.wizard_firefox_home_section_state_empty");
            }
            return fragments.join(" • ");
        }

        function getFirefoxHomeFineTuningCount(parsed) {
            const firefoxHome = parsed?.FirefoxHome && typeof parsed.FirefoxHome === "object" && !Array.isArray(parsed.FirefoxHome)
                ? parsed.FirefoxHome
                : {};
            return [
                "SponsoredTopSites",
                "Highlights",
                "Stories",
                "SponsoredPocket",
                "SponsoredStories",
                "Snippets",
                "Locked",
            ].filter((key) => typeof firefoxHome[key] === "boolean").length;
        }

        function getSearchDefaultsManualSectionStatus(parsed) {
            const searchEngines = parsed?.SearchEngines && typeof parsed.SearchEngines === "object" && !Array.isArray(parsed.SearchEngines)
                ? parsed.SearchEngines
                : {};
            const firefoxSuggest = parsed?.FirefoxSuggest && typeof parsed.FirefoxSuggest === "object" && !Array.isArray(parsed.FirefoxSuggest)
                ? parsed.FirefoxSuggest
                : {};
            const searchBarValue = typeof parsed?.SearchBar === "string" ? parsed.SearchBar.trim() : "";
            const defaultEngine = typeof searchEngines.Default === "string" ? searchEngines.Default.trim() : "";
            const searchSuggestEnabledValue = typeof parsed?.SearchSuggestEnabled === "boolean" ? parsed.SearchSuggestEnabled : null;
            const preventInstallsValue = typeof searchEngines.PreventInstalls === "boolean" ? searchEngines.PreventInstalls : null;
            const hiddenCount = Array.isArray(searchEngines.Remove) ? searchEngines.Remove.length : 0;
            const customCount = Array.isArray(searchEngines.Add) ? searchEngines.Add.length : 0;
            const suggestConflict = parsed?.SearchSuggestEnabled === false
                && (
                    firefoxSuggest.WebSuggestions === true
                    || firefoxSuggest.SponsoredSuggestions === true
                    || firefoxSuggest.ImproveSuggest === true
                );

            const parts = [];
            if (defaultEngine) {
                parts.push(
                    t("profiles.wizard_search_defaults_section_state_default_engine")
                        .replace("{value}", defaultEngine),
                );
            }
            if (searchSuggestEnabledValue === true) {
                parts.push(t("profiles.wizard_search_defaults_section_state_suggestions_on"));
            } else if (searchSuggestEnabledValue === false) {
                parts.push(t("profiles.wizard_search_defaults_section_state_suggestions_off"));
            }
            if (searchBarValue) {
                parts.push(
                    t("profiles.wizard_search_defaults_section_state_search_bar")
                        .replace("{value}", formatSearchBarLabel(searchBarValue)),
                );
            }
            if (preventInstallsValue === true) {
                parts.push(t("profiles.wizard_search_defaults_section_state_installs_blocked"));
            } else if (preventInstallsValue === false) {
                parts.push(t("profiles.wizard_search_defaults_section_state_installs_allowed"));
            }
            if (hiddenCount > 0) {
                parts.push(
                    t("profiles.wizard_search_defaults_section_state_hidden")
                        .replace("{count}", String(hiddenCount)),
                );
            }
            if (customCount > 0) {
                parts.push(
                    t("profiles.wizard_search_defaults_section_state_custom")
                        .replace("{count}", String(customCount)),
                );
            }

            if (!parts.length) {
                return t("profiles.wizard_search_defaults_section_state_empty");
            }
            let text = parts.join(" • ");
            if (suggestConflict) {
                text += ` • ${t("profiles.wizard_search_defaults_section_state_conflict")}`;
            }
            return text;
        }

        function getSearchDefaultsFineTuningCount(parsed) {
            const searchEngines = parsed?.SearchEngines && typeof parsed.SearchEngines === "object" && !Array.isArray(parsed.SearchEngines)
                ? parsed.SearchEngines
                : {};
            return (typeof parsed?.SearchBar === "string" && parsed.SearchBar.trim() ? 1 : 0)
                + (typeof searchEngines.PreventInstalls === "boolean" ? 1 : 0)
                + (Array.isArray(searchEngines.Remove) ? searchEngines.Remove.length : 0)
                + (Array.isArray(searchEngines.Add) ? searchEngines.Add.length : 0);
        }

        function getFirefoxSuggestManualSectionStatus(parsed) {
            const firefoxSuggest = parsed?.FirefoxSuggest && typeof parsed.FirefoxSuggest === "object" && !Array.isArray(parsed.FirefoxSuggest)
                ? parsed.FirefoxSuggest
                : {};
            const locked = firefoxSuggest.Locked === true;
            const webConflict = firefoxSuggest.WebSuggestions === false
                && (firefoxSuggest.SponsoredSuggestions === true || firefoxSuggest.ImproveSuggest === true);
            const parts = [];

            if (firefoxSuggest.WebSuggestions === true) {
                parts.push(t("profiles.wizard_firefox_suggest_section_state_web_on"));
            } else if (firefoxSuggest.WebSuggestions === false) {
                parts.push(t("profiles.wizard_firefox_suggest_section_state_web_off"));
            }
            if (firefoxSuggest.SponsoredSuggestions === true) {
                parts.push(t("profiles.wizard_firefox_suggest_section_state_sponsored_on"));
            } else if (firefoxSuggest.SponsoredSuggestions === false) {
                parts.push(t("profiles.wizard_firefox_suggest_section_state_sponsored_off"));
            }
            if (firefoxSuggest.ImproveSuggest === true) {
                parts.push(t("profiles.wizard_firefox_suggest_section_state_improve_on"));
            } else if (firefoxSuggest.ImproveSuggest === false) {
                parts.push(t("profiles.wizard_firefox_suggest_section_state_improve_off"));
            }

            if (!parts.length && !locked) {
                return t("profiles.wizard_firefox_suggest_section_state_empty");
            }
            let text = parts.join(" • ");
            if (locked) {
                text += `${text ? " • " : ""}${t("profiles.wizard_firefox_suggest_section_state_locked")}`;
            }
            if (webConflict) {
                text += ` • ${t("profiles.wizard_firefox_suggest_section_state_conflict")}`;
            }
            return text;
        }

        function getFirefoxSuggestFineTuningCount(parsed) {
            const firefoxSuggest = parsed?.FirefoxSuggest && typeof parsed.FirefoxSuggest === "object" && !Array.isArray(parsed.FirefoxSuggest)
                ? parsed.FirefoxSuggest
                : {};
            return ["SponsoredSuggestions", "ImproveSuggest", "Locked"]
                .filter((key) => typeof firefoxSuggest[key] === "boolean")
                .length;
        }

        function renderManualHomeAndSearchSectionStatuses(parsed) {
            setManualSectionStatus(wizardHomepageSectionStatusEl, getHomepageManualSectionStatus(parsed));
            setManualSectionStatus(wizardHomeOverridesSectionStatusEl, getHomeOverridesManualSectionStatus(parsed));
            setManualSectionStatus(wizardFirefoxHomeSectionStatusEl, getFirefoxHomeManualSectionStatus(parsed));
            setManualSectionStatus(wizardSearchDefaultsSectionStatusEl, getSearchDefaultsManualSectionStatus(parsed));
            setManualSectionStatus(wizardFirefoxSuggestSectionStatusEl, getFirefoxSuggestManualSectionStatus(parsed));
            setPanelExpanded(
                wizardFirefoxHomeFineTuningPanelEl,
                wizardFirefoxHomeFineTuningToggleEl,
                firefoxHomePanelPreference === null
                    ? getFirefoxHomeFineTuningCount(parsed) > 0
                    : firefoxHomePanelPreference,
                t("profiles.wizard_fine_tuning_show"),
                t("profiles.wizard_fine_tuning_hide"),
            );
            setPanelExpanded(
                wizardSearchDefaultsFineTuningPanelEl,
                wizardSearchDefaultsFineTuningToggleEl,
                searchDefaultsPanelPreference === null
                    ? getSearchDefaultsFineTuningCount(parsed) > 0
                    : searchDefaultsPanelPreference,
                t("profiles.wizard_fine_tuning_show"),
                t("profiles.wizard_fine_tuning_hide"),
            );
            setPanelExpanded(
                wizardSearchSuggestFineTuningPanelEl,
                wizardSearchSuggestFineTuningToggleEl,
                searchSuggestPanelPreference === null
                    ? getFirefoxSuggestFineTuningCount(parsed) > 0
                    : searchSuggestPanelPreference,
                t("profiles.wizard_fine_tuning_show"),
                t("profiles.wizard_fine_tuning_hide"),
            );
            renderProxySectionStatus(parsed?.Proxy);
            renderNetworkEnterpriseSectionStatus(parsed);
        }

        function toggleNetworkEnterprisePanel() {
            networkEnterprisePanelPreference = !(wizardNetworkEnterpriseFineTuningPanelEl?.hidden === false);
            const editor = getEditor();
            if (!editor) return;
            try {
                const parsed = fromEditorValue(editor.getValue(), documentRef.getElementById("mode").value);
                renderNetworkEnterpriseSectionStatus(parsed && typeof parsed === "object" ? parsed : {});
            } catch {
                renderNetworkEnterpriseSectionStatus({});
            }
        }

        function toggleHomeAndSearchPanel(panelKey) {
            if (panelKey === "firefox_home") {
                firefoxHomePanelPreference = !(wizardFirefoxHomeFineTuningPanelEl?.hidden === false);
            }
            if (panelKey === "search_defaults") {
                searchDefaultsPanelPreference = !(wizardSearchDefaultsFineTuningPanelEl?.hidden === false);
            }
            if (panelKey === "search_suggest") {
                searchSuggestPanelPreference = !(wizardSearchSuggestFineTuningPanelEl?.hidden === false);
            }
            const editor = getEditor();
            if (!editor) return;
            try {
                const parsed = fromEditorValue(editor.getValue(), document.getElementById("mode").value);
                renderManualHomeAndSearchSectionStatuses(parsed && typeof parsed === "object" ? parsed : {});
            } catch {
                renderManualHomeAndSearchSectionStatuses({});
            }
        }

        function syncFromEditor() {
            const editor = getEditor();
            if (!editor) return;
            networkEnterprisePanelPreference = null;
            firefoxHomePanelPreference = null;
            searchDefaultsPanelPreference = null;
            searchSuggestPanelPreference = null;

            try {
                const parsed = fromEditorValue(editor.getValue(), documentRef.getElementById("mode").value);
                const normalized = parsed && typeof parsed === "object" ? parsed : {};
                const homepage = normalized.Homepage && typeof normalized.Homepage === "object" ? normalized.Homepage : {};
                const searchEngines = normalized.SearchEngines && typeof normalized.SearchEngines === "object"
                    ? normalized.SearchEngines
                    : {};
                const firefoxHome = normalized.FirefoxHome && typeof normalized.FirefoxHome === "object"
                    ? normalized.FirefoxHome
                    : {};
                const firefoxSuggest = normalized.FirefoxSuggest && typeof normalized.FirefoxSuggest === "object"
                    ? normalized.FirefoxSuggest
                    : {};
                const proxy = normalized.Proxy && typeof normalized.Proxy === "object" ? normalized.Proxy : {};

                [
                    wizardHomepageUrlEl,
                    wizardHomepageAdditionalEl,
                    wizardHomepageStartPageEl,
                    wizardHomepageLockedEl,
                    wizardSearchBarEl,
                    wizardSearchSuggestEl,
                    wizardSearchDefaultEngineEl,
                    wizardSearchPreventInstallsEl,
                    wizardSearchRemoveEl,
                    wizardSearchEngineAddButtonEl,
                    ...wizardSearchEnginePresetButtons,
                    wizardNewTabPageEl,
                    wizardOverrideFirstRunEl,
                    wizardOverridePostUpdateEl,
                    wizardProxyModeEl,
                    wizardProxyLockedEl,
                    wizardProxyHttpEl,
                    wizardProxySslEl,
                    wizardProxyFtpEl,
                    wizardProxySocksEl,
                    wizardProxySocksVersionEl,
                    wizardProxyPassthroughEl,
                    wizardProxyAutoConfigUrlEl,
                    wizardProxyUseHttpForAllEl,
                    wizardProxyAutoLoginEl,
                    wizardProxyUseDnsEl,
                    ...wizardFirefoxHomeInputs,
                    ...wizardFirefoxSuggestInputs,
                ].forEach((input) => {
                    input.disabled = false;
                });

                wizardHomepageUrlEl.value = typeof homepage.URL === "string" ? homepage.URL : "";
                wizardHomepageAdditionalEl.value = Array.isArray(homepage.Additional)
                    ? homepage.Additional.join("\n")
                    : typeof homepage.Additional === "string"
                        ? homepage.Additional
                        : "";
                wizardHomepageStartPageEl.value = typeof homepage.StartPage === "string" ? homepage.StartPage : "";
                wizardHomepageLockedEl.checked = homepage.Locked === true;
                wizardSearchBarEl.value = formatSearchBarSelectValue(normalized.SearchBar);
                wizardSearchSuggestEl.value = formatBooleanSelectValue(normalized.SearchSuggestEnabled);
                wizardSearchDefaultEngineEl.value = typeof searchEngines.Default === "string" ? searchEngines.Default : "";
                wizardSearchPreventInstallsEl.value = formatBooleanSelectValue(searchEngines.PreventInstalls);
                wizardSearchRemoveEl.value = Array.isArray(searchEngines.Remove)
                    ? searchEngines.Remove.join("\n")
                    : typeof searchEngines.Remove === "string"
                        ? searchEngines.Remove
                        : "";
                if (consumeSearchEngineSyncOnce()) {
                    renderSearchEngineDrafts(false);
                } else {
                    syncSearchEngineDraftsFromPolicy(searchEngines.Add);
                }
                wizardNewTabPageEl.value = formatBooleanSelectValue(normalized.NewTabPage);
                wizardOverrideFirstRunEl.value = typeof normalized.OverrideFirstRunPage === "string" ? normalized.OverrideFirstRunPage : "";
                wizardOverridePostUpdateEl.value = typeof normalized.OverridePostUpdatePage === "string" ? normalized.OverridePostUpdatePage : "";
                syncBooleanSelectGroup(wizardFirefoxHomeInputs, firefoxHome, "firefoxHomeKey");
                syncBooleanSelectGroup(wizardFirefoxSuggestInputs, firefoxSuggest, "firefoxSuggestKey");

                wizardProxyModeEl.value = typeof proxy.Mode === "string" ? proxy.Mode : "";
                wizardProxyLockedEl.checked = proxy.Locked === true;
                wizardProxyHttpEl.value = typeof proxy.HTTPProxy === "string" ? proxy.HTTPProxy : "";
                wizardProxySslEl.value = typeof proxy.SSLProxy === "string" ? proxy.SSLProxy : "";
                wizardProxyFtpEl.value = typeof proxy.FTPProxy === "string" ? proxy.FTPProxy : "";
                wizardProxySocksEl.value = typeof proxy.SOCKSProxy === "string" ? proxy.SOCKSProxy : "";
                wizardProxySocksVersionEl.value = proxy.SOCKSVersion != null ? String(proxy.SOCKSVersion) : "";
                wizardProxyPassthroughEl.value = Array.isArray(proxy.Passthrough)
                    ? proxy.Passthrough.join("\n")
                    : typeof proxy.Passthrough === "string"
                        ? proxy.Passthrough.split(",").map((value) => value.trim()).filter(Boolean).join("\n")
                        : "";
                wizardProxyAutoConfigUrlEl.value = typeof proxy.AutoConfigURL === "string" ? proxy.AutoConfigURL : "";
                wizardProxyUseHttpForAllEl.checked = proxy.UseHTTPProxyForAllProtocols === true;
                wizardProxyAutoLoginEl.checked = proxy.AutoLogin === true;
                wizardProxyUseDnsEl.checked = proxy.UseProxyForDNS === true;
                renderManualHomeAndSearchSectionStatuses(normalized);
            } catch {
                [
                    wizardHomepageUrlEl,
                    wizardHomepageAdditionalEl,
                    wizardHomepageStartPageEl,
                    wizardHomepageLockedEl,
                    wizardSearchBarEl,
                    wizardSearchSuggestEl,
                    wizardSearchDefaultEngineEl,
                    wizardSearchPreventInstallsEl,
                    wizardSearchRemoveEl,
                    wizardSearchEngineAddButtonEl,
                    ...wizardSearchEnginePresetButtons,
                    wizardNewTabPageEl,
                    wizardOverrideFirstRunEl,
                    wizardOverridePostUpdateEl,
                    wizardProxyModeEl,
                    wizardProxyLockedEl,
                    wizardProxyHttpEl,
                    wizardProxySslEl,
                    wizardProxyFtpEl,
                    wizardProxySocksEl,
                    wizardProxySocksVersionEl,
                    wizardProxyPassthroughEl,
                    wizardProxyAutoConfigUrlEl,
                    wizardProxyUseHttpForAllEl,
                    wizardProxyAutoLoginEl,
                    wizardProxyUseDnsEl,
                    ...wizardFirefoxHomeInputs,
                    ...wizardFirefoxSuggestInputs,
                ].forEach((input) => {
                    input.disabled = true;
                });
                setProxyGroupVisibility("", true);
                clearSearchEngineSyncOnce();
                renderSearchEngineDrafts(true);
                renderManualHomeAndSearchSectionStatuses({});
            }
        }

        function applyFromWizard() {
            const editor = getEditor();
            if (!editor) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const nextHomepage = {
                    ...(normalized.Homepage && typeof normalized.Homepage === "object" ? normalized.Homepage : {}),
                };
                const nextSearchEngines = {
                    ...(normalized.SearchEngines && typeof normalized.SearchEngines === "object" ? normalized.SearchEngines : {}),
                };
                const nextFirefoxHome = {
                    ...(normalized.FirefoxHome && typeof normalized.FirefoxHome === "object" ? normalized.FirefoxHome : {}),
                };
                const nextFirefoxSuggest = {
                    ...(normalized.FirefoxSuggest && typeof normalized.FirefoxSuggest === "object" ? normalized.FirefoxSuggest : {}),
                };
                const nextProxy = {
                    ...(normalized.Proxy && typeof normalized.Proxy === "object" ? normalized.Proxy : {}),
                };

                wizardHomepageManagedKeys.forEach((key) => delete nextHomepage[key]);
                wizardLandingScalarKeys.forEach((key) => delete normalized[key]);
                wizardSearchEnginesManagedKeys.forEach((key) => delete nextSearchEngines[key]);
                wizardFirefoxHomeManagedKeys.forEach((key) => delete nextFirefoxHome[key]);
                wizardFirefoxSuggestManagedKeys.forEach((key) => delete nextFirefoxSuggest[key]);
                wizardProxyManagedKeys.forEach((key) => delete nextProxy[key]);

                const homepageUrl = wizardHomepageUrlEl.value.trim();
                const homepageAdditional = linesToArray(wizardHomepageAdditionalEl.value);
                const homepageStartPage = wizardHomepageStartPageEl.value;
                const searchBar = parseSearchBarSelectValue(wizardSearchBarEl.value);
                const searchSuggestEnabled = parseBooleanSelectValue(wizardSearchSuggestEl.value);
                const searchDefaultEngine = wizardSearchDefaultEngineEl.value.trim();
                const searchPreventInstalls = parseBooleanSelectValue(wizardSearchPreventInstallsEl.value);
                const searchRemove = linesToArray(wizardSearchRemoveEl.value);
                const searchAdd = buildSearchEngineAddItemsFromWizard();
                const newTabPage = parseBooleanSelectValue(wizardNewTabPageEl.value);
                const overrideFirstRunPage = wizardOverrideFirstRunEl.value.trim();
                const overridePostUpdatePage = wizardOverridePostUpdateEl.value.trim();

                if (homepageUrl) nextHomepage.URL = homepageUrl;
                if (homepageAdditional.length) nextHomepage.Additional = homepageAdditional;
                if (homepageStartPage) nextHomepage.StartPage = homepageStartPage;
                if (wizardHomepageLockedEl.checked) nextHomepage.Locked = true;
                if (searchBar !== null) normalized.SearchBar = searchBar;
                if (searchSuggestEnabled !== null) normalized.SearchSuggestEnabled = searchSuggestEnabled;
                if (newTabPage !== null) normalized.NewTabPage = newTabPage;
                if (overrideFirstRunPage) normalized.OverrideFirstRunPage = overrideFirstRunPage;
                if (overridePostUpdatePage) normalized.OverridePostUpdatePage = overridePostUpdatePage;
                if (searchAdd.length) nextSearchEngines.Add = searchAdd;
                if (searchDefaultEngine) nextSearchEngines.Default = searchDefaultEngine;
                if (searchPreventInstalls !== null) nextSearchEngines.PreventInstalls = searchPreventInstalls;
                if (searchRemove.length) nextSearchEngines.Remove = searchRemove;
                applyBooleanSelectGroup(wizardFirefoxHomeInputs, nextFirefoxHome, "firefoxHomeKey");
                applyBooleanSelectGroup(wizardFirefoxSuggestInputs, nextFirefoxSuggest, "firefoxSuggestKey");

                const proxyMode = wizardProxyModeEl.value;
                const proxyHttp = wizardProxyHttpEl.value.trim();
                const proxySsl = wizardProxySslEl.value.trim();
                const proxyFtp = wizardProxyFtpEl.value.trim();
                const proxySocks = wizardProxySocksEl.value.trim();
                const proxyPassthrough = textToList(wizardProxyPassthroughEl.value);
                const proxyAutoConfig = wizardProxyAutoConfigUrlEl.value.trim();
                const proxySocksVersion = wizardProxySocksVersionEl.value;

                if (proxyMode) nextProxy.Mode = proxyMode;
                if (wizardProxyLockedEl.checked) nextProxy.Locked = true;
                if (proxyMode === "manual") {
                    if (proxyHttp) nextProxy.HTTPProxy = proxyHttp;
                    if (proxySsl) nextProxy.SSLProxy = proxySsl;
                    if (proxyFtp) nextProxy.FTPProxy = proxyFtp;
                    if (proxySocks) nextProxy.SOCKSProxy = proxySocks;
                    if (proxyPassthrough.length) nextProxy.Passthrough = proxyPassthrough.join(", ");
                    if (proxySocksVersion) nextProxy.SOCKSVersion = Number(proxySocksVersion);
                    if (wizardProxyUseHttpForAllEl.checked) nextProxy.UseHTTPProxyForAllProtocols = true;
                    if (wizardProxyAutoLoginEl.checked) nextProxy.AutoLogin = true;
                    if (wizardProxyUseDnsEl.checked) nextProxy.UseProxyForDNS = true;
                } else if (proxyMode === "autoConfig") {
                    if (proxyPassthrough.length) nextProxy.Passthrough = proxyPassthrough.join(", ");
                    if (proxyAutoConfig) nextProxy.AutoConfigURL = proxyAutoConfig;
                    if (wizardProxyAutoLoginEl.checked) nextProxy.AutoLogin = true;
                }

                if (Object.keys(nextHomepage).length) {
                    normalized.Homepage = nextHomepage;
                } else {
                    delete normalized.Homepage;
                }

                if (Object.keys(nextSearchEngines).length) {
                    normalized.SearchEngines = nextSearchEngines;
                } else {
                    delete normalized.SearchEngines;
                }

                if (Object.keys(nextFirefoxHome).length) {
                    normalized.FirefoxHome = nextFirefoxHome;
                } else {
                    delete normalized.FirefoxHome;
                }

                if (Object.keys(nextFirefoxSuggest).length) {
                    normalized.FirefoxSuggest = nextFirefoxSuggest;
                } else {
                    delete normalized.FirefoxSuggest;
                }

                if (Object.keys(nextProxy).length) {
                    normalized.Proxy = nextProxy;
                } else {
                    delete normalized.Proxy;
                }

                setCurrentRaw(normalized);
                markSearchEngineSyncOnce();
                editor.setValue(toEditorValue(normalized, mode));
                renderManualHomeAndSearchSectionStatuses(normalized);
                renderHomeReviewSummary(normalized);
                renderSearchReviewSummary(normalized);
                setStatus(t("profiles.wizard_network_applied"), "info");
            } catch (e) {
                clearSearchEngineSyncOnce();
                setStatus(t("profiles.error_wizard_network").replace("{detail}", e.message || e), "error");
            }
        }

        if (wizardNetworkEnterpriseFineTuningToggleEl) {
            wizardNetworkEnterpriseFineTuningToggleEl.addEventListener("click", () => {
                toggleNetworkEnterprisePanel();
            });
        }
        if (wizardFirefoxHomeFineTuningToggleEl) {
            wizardFirefoxHomeFineTuningToggleEl.addEventListener("click", () => {
                toggleHomeAndSearchPanel("firefox_home");
            });
        }
        if (wizardSearchDefaultsFineTuningToggleEl) {
            wizardSearchDefaultsFineTuningToggleEl.addEventListener("click", () => {
                toggleHomeAndSearchPanel("search_defaults");
            });
        }
        if (wizardSearchSuggestFineTuningToggleEl) {
            wizardSearchSuggestFineTuningToggleEl.addEventListener("click", () => {
                toggleHomeAndSearchPanel("search_suggest");
            });
        }

        return {
            renderManualHomeAndSearchSectionStatuses,
            syncFromEditor,
            applyFromWizard,
        };
    }

    window.BPMProfilesNetwork = { create };
})();
