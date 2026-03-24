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
            wizardSearchDefaultsSectionStatusEl,
            wizardFirefoxSuggestSectionStatusEl,
            wizardNewTabPageEl,
            wizardOverrideFirstRunEl,
            wizardOverridePostUpdateEl,
            wizardFirefoxHomeInputs = [],
            wizardFirefoxSuggestInputs = [],
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
        } = elements;

        const {
            wizardHomepageManagedKeys = [],
            wizardLandingScalarKeys = [],
            wizardSearchEnginesManagedKeys = [],
            wizardFirefoxHomeManagedKeys = [],
            wizardFirefoxSuggestManagedKeys = [],
            wizardProxyManagedKeys = [],
        } = state;

        function setManualSectionStatus(element, text) {
            if (element) {
                element.textContent = text;
            }
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
                return t("profiles.wizard_homepage_section_state_empty", "No homepage overrides yet.");
            }
            if (requiresUrl && !url) {
                return t("profiles.wizard_homepage_section_state_invalid", "Startup expects a homepage URL.");
            }

            const parts = [];
            if (url) {
                parts.push(t("profiles.wizard_homepage_section_state_url", "Homepage URL set"));
            }
            if (additionalCount > 0) {
                parts.push(
                    t("profiles.wizard_homepage_section_state_additional", "Additional tabs: {count}")
                        .replace("{count}", String(additionalCount)),
                );
            }
            if (startPage) {
                parts.push(
                    t("profiles.wizard_homepage_section_state_start", "Start: {value}")
                        .replace("{value}", startPage),
                );
            }
            if (locked) {
                parts.push(t("profiles.wizard_homepage_section_state_locked", "Locked"));
            }
            return parts.join(" • ");
        }

        function getHomeOverridesManualSectionStatus(parsed) {
            const overrideCount = (typeof parsed?.NewTabPage === "boolean" ? 1 : 0)
                + (typeof parsed?.OverrideFirstRunPage === "string" && parsed.OverrideFirstRunPage.trim() ? 1 : 0)
                + (typeof parsed?.OverridePostUpdatePage === "string" && parsed.OverridePostUpdatePage.trim() ? 1 : 0);

            if (!overrideCount) {
                return t("profiles.wizard_home_overrides_section_state_empty", "No startup overrides yet.");
            }
            return t("profiles.wizard_home_overrides_section_state_configured", "Startup overrides active: {count}")
                .replace("{count}", String(overrideCount));
        }

        function getFirefoxHomeManualSectionStatus(parsed) {
            const firefoxHome = parsed?.FirefoxHome && typeof parsed.FirefoxHome === "object" && !Array.isArray(parsed.FirefoxHome)
                ? parsed.FirefoxHome
                : {};
            let shownCount = 0;
            let hiddenCount = 0;

            Object.entries(firefoxHome).forEach(([key, value]) => {
                if (key === "Locked" || typeof value !== "boolean") return;
                if (value) shownCount += 1;
                else hiddenCount += 1;
            });

            const locked = firefoxHome.Locked === true;
            if (!shownCount && !hiddenCount && !locked) {
                return t("profiles.wizard_firefox_home_section_state_empty", "No Firefox Home card overrides yet.");
            }

            let text = t("profiles.wizard_firefox_home_section_state_configured", "Show: {show} • Hide: {hide}")
                .replace("{show}", String(shownCount))
                .replace("{hide}", String(hiddenCount));
            if (locked) {
                text += ` • ${t("profiles.wizard_firefox_home_section_state_locked", "Locked")}`;
            }
            return text;
        }

        function getSearchDefaultsManualSectionStatus(parsed) {
            const searchEngines = parsed?.SearchEngines && typeof parsed.SearchEngines === "object" && !Array.isArray(parsed.SearchEngines)
                ? parsed.SearchEngines
                : {};
            const firefoxSuggest = parsed?.FirefoxSuggest && typeof parsed.FirefoxSuggest === "object" && !Array.isArray(parsed.FirefoxSuggest)
                ? parsed.FirefoxSuggest
                : {};
            const defaultCount = (typeof parsed?.SearchBar === "string" && parsed.SearchBar.trim() ? 1 : 0)
                + (typeof parsed?.SearchSuggestEnabled === "boolean" ? 1 : 0)
                + (typeof searchEngines.Default === "string" && searchEngines.Default.trim() ? 1 : 0)
                + (typeof searchEngines.PreventInstalls === "boolean" ? 1 : 0);
            const hiddenCount = Array.isArray(searchEngines.Remove) ? searchEngines.Remove.length : 0;
            const customCount = Array.isArray(searchEngines.Add) ? searchEngines.Add.length : 0;
            const suggestConflict = parsed?.SearchSuggestEnabled === false
                && (
                    firefoxSuggest.WebSuggestions === true
                    || firefoxSuggest.SponsoredSuggestions === true
                    || firefoxSuggest.ImproveSuggest === true
                );

            if (!defaultCount && !hiddenCount && !customCount) {
                return t("profiles.wizard_search_defaults_section_state_empty", "No search defaults overridden yet.");
            }

            let text = t("profiles.wizard_search_defaults_section_state_configured", "Defaults: {defaults} • Hidden: {hidden} • Custom: {custom}")
                .replace("{defaults}", String(defaultCount))
                .replace("{hidden}", String(hiddenCount))
                .replace("{custom}", String(customCount));
            if (suggestConflict) {
                text += ` • ${t("profiles.wizard_search_defaults_section_state_conflict", "Search suggestions are off while Firefox Suggest surfaces stay enabled")}`;
            }
            return text;
        }

        function getFirefoxSuggestManualSectionStatus(parsed) {
            const firefoxSuggest = parsed?.FirefoxSuggest && typeof parsed.FirefoxSuggest === "object" && !Array.isArray(parsed.FirefoxSuggest)
                ? parsed.FirefoxSuggest
                : {};
            let enabledCount = 0;
            let disabledCount = 0;

            Object.entries(firefoxSuggest).forEach(([key, value]) => {
                if (key === "Locked" || typeof value !== "boolean") return;
                if (value) enabledCount += 1;
                else disabledCount += 1;
            });

            const locked = firefoxSuggest.Locked === true;
            const webConflict = firefoxSuggest.WebSuggestions === false
                && (firefoxSuggest.SponsoredSuggestions === true || firefoxSuggest.ImproveSuggest === true);

            if (!enabledCount && !disabledCount && !locked) {
                return t("profiles.wizard_firefox_suggest_section_state_empty", "No Firefox Suggest overrides yet.");
            }

            let text = t("profiles.wizard_firefox_suggest_section_state_configured", "Enabled: {enabled} • Disabled: {disabled}")
                .replace("{enabled}", String(enabledCount))
                .replace("{disabled}", String(disabledCount));
            if (locked) {
                text += ` • ${t("profiles.wizard_firefox_suggest_section_state_locked", "Locked")}`;
            }
            if (webConflict) {
                text += ` • ${t("profiles.wizard_firefox_suggest_section_state_conflict", "Dependent surfaces need web suggestions")}`;
            }
            return text;
        }

        function renderManualHomeAndSearchSectionStatuses(parsed) {
            setManualSectionStatus(wizardHomepageSectionStatusEl, getHomepageManualSectionStatus(parsed));
            setManualSectionStatus(wizardHomeOverridesSectionStatusEl, getHomeOverridesManualSectionStatus(parsed));
            setManualSectionStatus(wizardFirefoxHomeSectionStatusEl, getFirefoxHomeManualSectionStatus(parsed));
            setManualSectionStatus(wizardSearchDefaultsSectionStatusEl, getSearchDefaultsManualSectionStatus(parsed));
            setManualSectionStatus(wizardFirefoxSuggestSectionStatusEl, getFirefoxSuggestManualSectionStatus(parsed));
        }

        function syncFromEditor() {
            const editor = getEditor();
            if (!editor) return;

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
                if (proxyHttp) nextProxy.HTTPProxy = proxyHttp;
                if (proxySsl) nextProxy.SSLProxy = proxySsl;
                if (proxyFtp) nextProxy.FTPProxy = proxyFtp;
                if (proxySocks) nextProxy.SOCKSProxy = proxySocks;
                if (proxyPassthrough.length) nextProxy.Passthrough = proxyPassthrough.join(", ");
                if (proxyAutoConfig) nextProxy.AutoConfigURL = proxyAutoConfig;
                if (proxySocksVersion) nextProxy.SOCKSVersion = Number(proxySocksVersion);
                if (wizardProxyUseHttpForAllEl.checked) nextProxy.UseHTTPProxyForAllProtocols = true;
                if (wizardProxyAutoLoginEl.checked) nextProxy.AutoLogin = true;
                if (wizardProxyUseDnsEl.checked) nextProxy.UseProxyForDNS = true;

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
                setStatus(t("profiles.wizard_network_applied", "Landing, search, and proxy settings updated."), "info");
            } catch (e) {
                clearSearchEngineSyncOnce();
                setStatus(`Wizard network error: ${e.message || e}`, "error");
            }
        }

        return {
            renderManualHomeAndSearchSectionStatuses,
            syncFromEditor,
            applyFromWizard,
        };
    }

    window.BPMProfilesNetwork = { create };
})();
