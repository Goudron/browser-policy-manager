(() => {
    function create({
        documentRef = document,
        elements = {},
        dependencies = {},
        state = {},
    }) {
        const {
            t,
            cloneJsonValue,
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
            wizardSearchDefaultsPresetButtons = [],
            wizardHomepageSectionStatusEl,
            wizardHomeOverridesSectionStatusEl,
            wizardFirefoxHomeSectionStatusEl,
            wizardHomeSurfacesWorkflowCopyEl,
            wizardHomeSurfacesWorkflowListEl,
            wizardFirefoxHomeFineTuningToggleEl,
            wizardFirefoxHomeFineTuningPanelEl,
            wizardSearchDefaultsSectionStatusEl,
            wizardSearchSurfacesWorkflowCopyEl,
            wizardSearchSurfacesWorkflowListEl,
            wizardSearchDefaultsFineTuningToggleEl,
            wizardSearchDefaultsFineTuningPanelEl,
            wizardFirefoxSuggestSectionStatusEl,
            wizardFirefoxSuggestPresetButtons = [],
            wizardSearchSuggestFineTuningToggleEl,
            wizardSearchSuggestFineTuningPanelEl,
            wizardNewTabPageEl,
            wizardOverrideFirstRunEl,
            wizardOverridePostUpdateEl,
            wizardFirefoxHomeInputs = [],
            wizardFirefoxSuggestInputs = [],
            wizardGeneralPolicySectionStatusEl,
            wizardUpkeepGovernanceCopyEl,
            wizardUpkeepGovernanceListEl,
            wizardGeneralPolicyPresetButtons = [],
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
            wizardTrustAuthWorkflowCopyEl,
            wizardTrustAuthWorkflowListEl,
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
        const proxyPresetButtons = Array.from(documentRef.querySelectorAll("[data-proxy-preset]"));
        const homepagePresetButtons = Array.from(documentRef.querySelectorAll("[data-homepage-preset]"));
        const homepageSharedPresetButtons = Array.from(documentRef.querySelectorAll("[data-homepage-shared-preset]"));
        const homeOverridesPresetButtons = Array.from(documentRef.querySelectorAll("[data-home-overrides-preset]"));
        const firefoxHomePresetButtons = Array.from(documentRef.querySelectorAll("[data-firefox-home-preset]"));
        const searchDefaultsPresetButtons = Array.from(wizardSearchDefaultsPresetButtons);
        const firefoxSuggestPresetButtons = Array.from(wizardFirefoxSuggestPresetButtons);
        const generalPolicyPresetButtons = Array.from(wizardGeneralPolicyPresetButtons);
        const networkEnterpriseManagedKeys = ["WindowsSSO", "Certificates"];
        const networkEnterprisePresets = {
            defaults: {},
            sso: {
                WindowsSSO: true,
            },
            roots: {
                Certificates: {
                    ImportEnterpriseRoots: true,
                },
            },
            managed: {
                WindowsSSO: true,
                Certificates: {
                    ImportEnterpriseRoots: true,
                },
            },
        };
        const proxyPresets = {
            defaults: {},
            none: {
                Mode: "none",
            },
            system: {
                Mode: "system",
            },
            autoConfig: {
                Mode: "autoConfig",
            },
            manual: {
                Mode: "manual",
            },
        };

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

        function normalizeForCompare(value) {
            if (Array.isArray(value)) {
                return value.map((entry) => normalizeForCompare(entry));
            }
            if (value && typeof value === "object") {
                return Object.keys(value).sort().reduce((acc, key) => {
                    acc[key] = normalizeForCompare(value[key]);
                    return acc;
                }, {});
            }
            return value;
        }

        function valuesEqual(left, right) {
            return JSON.stringify(normalizeForCompare(left)) === JSON.stringify(normalizeForCompare(right));
        }

        function matchesPolicyPreset(current, managedKeys, presetValues) {
            return managedKeys.every((key) => {
                if (Object.prototype.hasOwnProperty.call(presetValues, key)) {
                    return valuesEqual(current[key], presetValues[key]);
                }
                return current[key] === undefined;
            });
        }

        function renderPresetButtonState(buttons, activeKey, datasetKey = "networkEnterprisePreset") {
            buttons.forEach((button) => {
                const isActive = button.dataset[datasetKey] === activeKey;
                button.classList.toggle("wizard-search-engine-preset--applied", isActive);
                button.classList.toggle("wizard-search-engine-preset--partial", false);
                button.classList.toggle("wizard-search-engine-preset--conflict", false);
                button.setAttribute("aria-pressed", isActive ? "true" : "false");
            });
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

        function getGeneralPolicySectionStatus(parsed) {
            const parts = [];
            let updateCount = 0;

            if (parsed?.DisableAppUpdate === true) updateCount += 1;
            if (parsed?.DisableSystemAddonUpdate === true) updateCount += 1;
            if (typeof parsed?.AppAutoUpdate === "boolean") updateCount += 1;
            if (updateCount > 0) {
                parts.push(
                    t("profiles.wizard_general_policy_section_state_updates")
                        .replace("{count}", String(updateCount)),
                );
            }
            if (parsed?.DontCheckDefaultBrowser === true) {
                parts.push(t("profiles.wizard_general_policy_section_state_browser_prompt_off"));
            }
            if (parsed?.PromptForDownloadLocation === true) {
                parts.push(t("profiles.wizard_general_policy_section_state_download_prompt_on"));
            }

            if (!parts.length) {
                return t("profiles.wizard_general_policy_section_state_empty");
            }
            return parts.join(" • ");
        }

        function resolveGeneralPolicyPreset(parsed) {
            const updateCount = (parsed?.DisableAppUpdate === true ? 1 : 0)
                + (parsed?.DisableSystemAddonUpdate === true ? 1 : 0)
                + (typeof parsed?.AppAutoUpdate === "boolean" ? 1 : 0);
            const hasBrowserPrompt = parsed?.DontCheckDefaultBrowser === true;
            const hasDownloads = parsed?.PromptForDownloadLocation === true;

            if (updateCount > 0 && (hasBrowserPrompt || hasDownloads)) return "managed";
            if (updateCount > 0) return "updates";
            if (hasBrowserPrompt) return "browser_prompt";
            if (hasDownloads) return "downloads";
            return "defaults";
        }

        function renderUpkeepGovernanceWorkflow(parsed = {}) {
            if (!wizardUpkeepGovernanceCopyEl || !wizardUpkeepGovernanceListEl) return;

            const resolved = parsed && typeof parsed === "object" ? parsed : {};
            const updateCount = (resolved.DisableAppUpdate === true ? 1 : 0)
                + (resolved.DisableSystemAddonUpdate === true ? 1 : 0)
                + (typeof resolved.AppAutoUpdate === "boolean" ? 1 : 0);
            const hasBrowserPrompt = resolved.DontCheckDefaultBrowser === true;
            const hasDownloads = resolved.PromptForDownloadLocation === true;
            const activePreset = resolveGeneralPolicyPreset(resolved);
            const hasManagedUpkeep = updateCount > 0 || hasBrowserPrompt || hasDownloads;
            const hasDeeperOperationalMix = activePreset === "managed"
                || resolved.DisableSystemAddonUpdate === true
                || typeof resolved.AppAutoUpdate === "boolean";

            wizardUpkeepGovernanceCopyEl.textContent = hasManagedUpkeep
                ? t("profiles.wizard_upkeep_governance_active")
                : t("profiles.wizard_upkeep_governance_body");

            const items = [
                {
                    title: t("profiles.wizard_upkeep_governance_item_updates"),
                    copy: updateCount > 0
                        ? t("profiles.wizard_upkeep_governance_item_updates_ready").replace("{count}", String(updateCount))
                        : (hasManagedUpkeep
                            ? t("profiles.wizard_upkeep_governance_item_updates_needed")
                            : t("profiles.wizard_upkeep_governance_item_updates_optional")),
                    tone: updateCount > 0 ? "ready" : (hasManagedUpkeep ? "strict" : "default"),
                    target: "policy:DisableAppUpdate",
                },
                {
                    title: t("profiles.wizard_upkeep_governance_item_prompts"),
                    copy: hasBrowserPrompt
                        ? t("profiles.wizard_upkeep_governance_item_prompts_ready")
                        : (hasManagedUpkeep
                            ? t("profiles.wizard_upkeep_governance_item_prompts_needed")
                            : t("profiles.wizard_upkeep_governance_item_prompts_optional")),
                    tone: hasBrowserPrompt ? "ready" : (hasManagedUpkeep ? "strict" : "default"),
                    target: "policy:DontCheckDefaultBrowser",
                },
                {
                    title: t("profiles.wizard_upkeep_governance_item_downloads"),
                    copy: hasDownloads
                        ? t("profiles.wizard_upkeep_governance_item_downloads_ready")
                        : (hasManagedUpkeep
                            ? t("profiles.wizard_upkeep_governance_item_downloads_needed")
                            : t("profiles.wizard_upkeep_governance_item_downloads_optional")),
                    tone: hasDownloads ? "ready" : (hasManagedUpkeep ? "strict" : "default"),
                    target: "policy:PromptForDownloadLocation",
                },
                {
                    title: t("profiles.wizard_upkeep_governance_item_mix"),
                    copy: hasDeeperOperationalMix
                        ? t("profiles.wizard_upkeep_governance_item_mix_ready")
                        : (hasManagedUpkeep
                            ? t("profiles.wizard_upkeep_governance_item_mix_optional")
                            : t("profiles.wizard_upkeep_governance_item_mix_later")),
                    tone: hasDeeperOperationalMix ? "ready" : (hasManagedUpkeep ? "default" : "default"),
                    target: "policy:DisableSystemAddonUpdate",
                },
            ];

            wizardUpkeepGovernanceListEl.replaceChildren(
                ...items.map((item) => {
                    const rowEl = documentRef.createElement("div");
                    rowEl.className = "wizard-export-plan-item";
                    rowEl.dataset.planTone = item.tone;

                    const copyEl = documentRef.createElement("div");
                    copyEl.className = "wizard-export-plan-copy";
                    const titleEl = documentRef.createElement("div");
                    titleEl.textContent = item.title;
                    const bodyEl = documentRef.createElement("div");
                    bodyEl.className = "wizard-input-hint";
                    bodyEl.textContent = item.copy;
                    copyEl.append(titleEl, bodyEl);

                    const actionEl = documentRef.createElement("button");
                    actionEl.type = "button";
                    actionEl.className = "button-base ghost-button wizard-export-plan-action";
                    actionEl.dataset.settingsJumpTarget = item.target;
                    actionEl.textContent = t("profiles.wizard_export_open");

                    rowEl.append(copyEl, actionEl);
                    return rowEl;
                }),
            );
        }

        function renderHomeSurfacesWorkflow(parsed = {}) {
            if (!wizardHomeSurfacesWorkflowCopyEl || !wizardHomeSurfacesWorkflowListEl) return;

            const resolved = parsed && typeof parsed === "object" ? parsed : {};
            const homepage = resolved.Homepage && typeof resolved.Homepage === "object" && !Array.isArray(resolved.Homepage)
                ? resolved.Homepage
                : {};
            const firefoxHome = resolved.FirefoxHome && typeof resolved.FirefoxHome === "object" && !Array.isArray(resolved.FirefoxHome)
                ? resolved.FirefoxHome
                : {};
            const homepageConfigured = Boolean(
                (typeof homepage.URL === "string" && homepage.URL.trim())
                || (Array.isArray(homepage.Additional) && homepage.Additional.length)
                || (typeof homepage.StartPage === "string" && homepage.StartPage.trim())
                || homepage.Locked === true
            );
            const landingOverridesConfigured = Boolean(
                typeof resolved.NewTabPage === "boolean"
                || (typeof resolved.OverrideFirstRunPage === "string" && resolved.OverrideFirstRunPage.trim())
                || (typeof resolved.OverridePostUpdatePage === "string" && resolved.OverridePostUpdatePage.trim())
            );
            const firefoxHomeConfigured = Object.values(firefoxHome).some((value) => typeof value === "boolean");
            const activeHomePreset = resolveHomepagePreset(resolved);
            const activeOverridesPreset = resolveHomeOverridesPreset(resolved);
            const activeFirefoxHomePreset = resolveFirefoxHomePreset(resolved);
            const hasManagedHomeExperience = homepageConfigured || landingOverridesConfigured || firefoxHomeConfigured;
            const hasCoordinatedLandingMix = [
                activeHomePreset,
                activeOverridesPreset,
                activeFirefoxHomePreset,
            ].filter((value) => value && value !== "defaults").length >= 2;

            wizardHomeSurfacesWorkflowCopyEl.textContent = hasManagedHomeExperience
                ? t("profiles.wizard_home_surfaces_workflow_active")
                : t("profiles.wizard_home_surfaces_workflow_body");

            const items = [
                {
                    title: t("profiles.wizard_home_surfaces_workflow_item_homepage"),
                    copy: homepageConfigured
                        ? t("profiles.wizard_home_surfaces_workflow_item_homepage_ready")
                        : (hasManagedHomeExperience
                            ? t("profiles.wizard_home_surfaces_workflow_item_homepage_needed")
                            : t("profiles.wizard_home_surfaces_workflow_item_homepage_optional")),
                    tone: homepageConfigured ? "ready" : (hasManagedHomeExperience ? "strict" : "default"),
                    target: "field:wizard-homepage-url",
                },
                {
                    title: t("profiles.wizard_home_surfaces_workflow_item_landing"),
                    copy: landingOverridesConfigured
                        ? t("profiles.wizard_home_surfaces_workflow_item_landing_ready")
                        : (hasManagedHomeExperience
                            ? t("profiles.wizard_home_surfaces_workflow_item_landing_needed")
                            : t("profiles.wizard_home_surfaces_workflow_item_landing_optional")),
                    tone: landingOverridesConfigured ? "ready" : (hasManagedHomeExperience ? "strict" : "default"),
                    target: "field:wizard-new-tab-page",
                },
                {
                    title: t("profiles.wizard_home_surfaces_workflow_item_cards"),
                    copy: firefoxHomeConfigured
                        ? t("profiles.wizard_home_surfaces_workflow_item_cards_ready")
                        : (hasManagedHomeExperience
                            ? t("profiles.wizard_home_surfaces_workflow_item_cards_needed")
                            : t("profiles.wizard_home_surfaces_workflow_item_cards_optional")),
                    tone: firefoxHomeConfigured ? "ready" : (hasManagedHomeExperience ? "strict" : "default"),
                    target: "field:firefox-home-search",
                },
                {
                    title: t("profiles.wizard_home_surfaces_workflow_item_mix"),
                    copy: hasCoordinatedLandingMix
                        ? t("profiles.wizard_home_surfaces_workflow_item_mix_ready")
                        : (hasManagedHomeExperience
                            ? t("profiles.wizard_home_surfaces_workflow_item_mix_optional")
                            : t("profiles.wizard_home_surfaces_workflow_item_mix_later")),
                    tone: hasCoordinatedLandingMix ? "ready" : "default",
                    target: "field:wizard-override-first-run",
                },
            ];

            wizardHomeSurfacesWorkflowListEl.replaceChildren(
                ...items.map((item) => {
                    const rowEl = documentRef.createElement("div");
                    rowEl.className = "wizard-export-plan-item";
                    rowEl.dataset.planTone = item.tone;

                    const copyEl = documentRef.createElement("div");
                    copyEl.className = "wizard-export-plan-copy";
                    const titleEl = documentRef.createElement("div");
                    titleEl.textContent = item.title;
                    const bodyEl = documentRef.createElement("div");
                    bodyEl.className = "wizard-input-hint";
                    bodyEl.textContent = item.copy;
                    copyEl.append(titleEl, bodyEl);

                    const actionEl = documentRef.createElement("button");
                    actionEl.type = "button";
                    actionEl.className = "button-base ghost-button wizard-export-plan-action";
                    actionEl.dataset.settingsJumpTarget = item.target;
                    actionEl.textContent = t("profiles.wizard_export_open");

                    rowEl.append(copyEl, actionEl);
                    return rowEl;
                }),
            );
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

        function resolveFirefoxHomePreset(parsed) {
            const firefoxHome = parsed?.FirefoxHome && typeof parsed.FirefoxHome === "object" && !Array.isArray(parsed.FirefoxHome)
                ? parsed.FirefoxHome
                : {};
            const configuredCount = [
                "Search",
                "TopSites",
                "Pocket",
                "SponsoredTopSites",
                "Highlights",
                "Stories",
                "SponsoredPocket",
                "SponsoredStories",
                "Snippets",
                "Locked",
            ].filter((key) => typeof firefoxHome[key] === "boolean").length;

            if (!configuredCount) return "defaults";

            const focusedPattern = firefoxHome.Search === true
                && firefoxHome.TopSites === false
                && firefoxHome.Pocket === false
                && firefoxHome.Stories === false
                && firefoxHome.Snippets === false;
            if (focusedPattern) return "focused";

            const shortcutsPattern = firefoxHome.Search === true
                && firefoxHome.TopSites === true
                && firefoxHome.Pocket === false
                && firefoxHome.Stories !== true;
            if (shortcutsPattern && configuredCount <= 4) return "shortcuts";

            return "managed";
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
            const activeProxyPreset = (() => {
                if (!Object.keys(resolvedProxy).length) return "defaults";
                const mode = typeof resolvedProxy.Mode === "string" ? resolvedProxy.Mode : "";
                return Object.prototype.hasOwnProperty.call(proxyPresets, mode) ? mode : "";
            })();
            renderPresetButtonState(proxyPresetButtons, activeProxyPreset);
            setManualSectionStatus(wizardProxySectionStatusEl, getProxyManualSectionStatus(resolvedProxy));
            setProxyGroupVisibility(typeof resolvedProxy.Mode === "string" ? resolvedProxy.Mode : "", false);
        }

        function buildProxyFromWizardFields() {
            const proxy = {};
            const mode = typeof wizardProxyModeEl?.value === "string" ? wizardProxyModeEl.value.trim() : "";
            const httpProxy = typeof wizardProxyHttpEl?.value === "string" ? wizardProxyHttpEl.value.trim() : "";
            const sslProxy = typeof wizardProxySslEl?.value === "string" ? wizardProxySslEl.value.trim() : "";
            const ftpProxy = typeof wizardProxyFtpEl?.value === "string" ? wizardProxyFtpEl.value.trim() : "";
            const socksProxy = typeof wizardProxySocksEl?.value === "string" ? wizardProxySocksEl.value.trim() : "";
            const autoConfigUrl = typeof wizardProxyAutoConfigUrlEl?.value === "string"
                ? wizardProxyAutoConfigUrlEl.value.trim()
                : "";
            const passthrough = textToList(wizardProxyPassthroughEl?.value || "");
            const socksVersion = typeof wizardProxySocksVersionEl?.value === "string"
                ? wizardProxySocksVersionEl.value.trim()
                : "";

            if (mode) proxy.Mode = mode;
            if (wizardProxyLockedEl?.checked) proxy.Locked = true;
            if (httpProxy) proxy.HTTPProxy = httpProxy;
            if (sslProxy) proxy.SSLProxy = sslProxy;
            if (ftpProxy) proxy.FTPProxy = ftpProxy;
            if (socksProxy) proxy.SOCKSProxy = socksProxy;
            if (autoConfigUrl) proxy.AutoConfigURL = autoConfigUrl;
            if (passthrough.length) proxy.Passthrough = passthrough.join(", ");
            if (socksVersion) proxy.SOCKSVersion = Number(socksVersion);
            if (wizardProxyUseHttpForAllEl?.checked) proxy.UseHTTPProxyForAllProtocols = true;
            if (wizardProxyAutoLoginEl?.checked) proxy.AutoLogin = true;
            if (wizardProxyUseDnsEl?.checked) proxy.UseProxyForDNS = true;

            return proxy;
        }

        function applyProxyPreset(presetKey) {
            const resolvedPreset = Object.prototype.hasOwnProperty.call(proxyPresets, presetKey)
                ? presetKey
                : "defaults";

            if (wizardProxyModeEl) {
                wizardProxyModeEl.value = proxyPresets[resolvedPreset]?.Mode || "";
            }
            if (resolvedPreset !== "manual") {
                if (wizardProxyHttpEl) wizardProxyHttpEl.value = "";
                if (wizardProxySslEl) wizardProxySslEl.value = "";
                if (wizardProxyFtpEl) wizardProxyFtpEl.value = "";
                if (wizardProxySocksEl) wizardProxySocksEl.value = "";
                if (wizardProxySocksVersionEl) wizardProxySocksVersionEl.value = "";
                if (wizardProxyUseHttpForAllEl) wizardProxyUseHttpForAllEl.checked = false;
                if (wizardProxyUseDnsEl) wizardProxyUseDnsEl.checked = false;
            }
            if (resolvedPreset !== "autoConfig") {
                if (wizardProxyAutoConfigUrlEl) wizardProxyAutoConfigUrlEl.value = "";
            }
            if (!["manual", "autoConfig"].includes(resolvedPreset)) {
                if (wizardProxyPassthroughEl) wizardProxyPassthroughEl.value = "";
                if (wizardProxyAutoLoginEl) wizardProxyAutoLoginEl.checked = false;
            }
            if (resolvedPreset === "defaults" && wizardProxyLockedEl) {
                wizardProxyLockedEl.checked = false;
            }

            applyFromWizard();
        }

        function renderNetworkEnterpriseSectionStatus(parsed = {}) {
            const resolved = parsed && typeof parsed === "object" ? parsed : {};
            const dnsConfigured = countConfiguredObjectEntries(resolved.DNSOverHTTPS);
            const authConfigured = countConfiguredObjectEntries(resolved.Authentication);
            const certificatesConfigured = countConfiguredObjectEntries(resolved.Certificates);
            const certificateInstallCount = Array.isArray(resolved?.Certificates?.Install)
                ? resolved.Certificates.Install.length
                : 0;
            const activePreset = Object.entries(networkEnterprisePresets).find(([, presetValues]) =>
                matchesPolicyPreset(resolved, networkEnterpriseManagedKeys, presetValues)
            )?.[0] || "";
            renderPresetButtonState(
                Array.from(documentRef.querySelectorAll("[data-network-enterprise-preset]")),
                activePreset,
            );
            const fragments = [];

            if (activePreset === "sso") {
                fragments.push(t("profiles.wizard_network_enterprise_section_state_sso_preset"));
            } else if (activePreset === "roots") {
                fragments.push(t("profiles.wizard_network_enterprise_section_state_roots_preset"));
            } else if (activePreset === "managed") {
                fragments.push(t("profiles.wizard_network_enterprise_section_state_managed_preset"));
            }
            if (dnsConfigured > 0) {
                fragments.push(t("profiles.wizard_network_enterprise_section_state_doh"));
            }
            if (typeof resolved.WindowsSSO === "boolean" && !["sso", "managed"].includes(activePreset)) {
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

            const hasCustomEnterpriseConfig = authConfigured > 0
                || certificateInstallCount > 0
                || (hasMeaningfulValue(resolved.Certificates) && !activePreset);
            setPanelExpanded(
                wizardNetworkEnterpriseFineTuningPanelEl,
                wizardNetworkEnterpriseFineTuningToggleEl,
                networkEnterprisePanelPreference === null
                    ? hasCustomEnterpriseConfig
                    : networkEnterprisePanelPreference,
                t("profiles.wizard_fine_tuning_show"),
                t("profiles.wizard_fine_tuning_hide"),
            );
        }

        function renderTrustAuthWorkflow(parsed = {}) {
            if (!wizardTrustAuthWorkflowCopyEl || !wizardTrustAuthWorkflowListEl) return;

            const resolved = parsed && typeof parsed === "object" ? parsed : {};
            const authentication = resolved.Authentication && typeof resolved.Authentication === "object" && !Array.isArray(resolved.Authentication)
                ? resolved.Authentication
                : {};
            const certificates = resolved.Certificates && typeof resolved.Certificates === "object" && !Array.isArray(resolved.Certificates)
                ? resolved.Certificates
                : {};
            const trustedHostRuleCount = [
                Array.isArray(authentication.SPNEGO) ? authentication.SPNEGO.length : 0,
                Array.isArray(authentication.Delegated) ? authentication.Delegated.length : 0,
                Array.isArray(authentication.NTLM) ? authentication.NTLM.length : 0,
                authentication.AllowNonFQDN === true ? 1 : 0,
                authentication.AllowProxies === true ? 1 : 0,
            ].reduce((sum, count) => sum + count, 0);
            const signInPostureManaged = resolved.WindowsSSO === true
                || authentication.Locked === true
                || authentication.PrivateBrowsing === true;
            const enterpriseRootsEnabled = certificates.ImportEnterpriseRoots === true;
            const certificateFileCount = Array.isArray(certificates.Install) ? certificates.Install.length : 0;
            const hasEnterpriseFootprint = signInPostureManaged
                || trustedHostRuleCount > 0
                || enterpriseRootsEnabled
                || certificateFileCount > 0;

            wizardTrustAuthWorkflowCopyEl.textContent = hasEnterpriseFootprint
                ? t("profiles.wizard_trust_auth_workflow_active")
                : t("profiles.wizard_trust_auth_workflow_body");

            const items = [
                {
                    title: t("profiles.wizard_trust_auth_workflow_signin"),
                    copy: signInPostureManaged
                        ? t("profiles.wizard_trust_auth_workflow_signin_ready")
                        : (hasEnterpriseFootprint
                            ? t("profiles.wizard_trust_auth_workflow_signin_needed")
                            : t("profiles.wizard_trust_auth_workflow_signin_optional")),
                    tone: signInPostureManaged ? "ready" : (hasEnterpriseFootprint ? "strict" : "default"),
                    target: "policy:WindowsSSO",
                },
                {
                    title: t("profiles.wizard_trust_auth_workflow_hosts"),
                    copy: trustedHostRuleCount > 0
                        ? t("profiles.wizard_trust_auth_workflow_hosts_ready").replace("{count}", String(trustedHostRuleCount))
                        : (hasEnterpriseFootprint
                            ? t("profiles.wizard_trust_auth_workflow_hosts_needed")
                            : t("profiles.wizard_trust_auth_workflow_hosts_optional")),
                    tone: trustedHostRuleCount > 0 ? "ready" : (hasEnterpriseFootprint ? "strict" : "default"),
                    target: "policy:Authentication",
                },
                {
                    title: t("profiles.wizard_trust_auth_workflow_roots"),
                    copy: enterpriseRootsEnabled
                        ? t("profiles.wizard_trust_auth_workflow_roots_ready")
                        : (hasEnterpriseFootprint
                            ? t("profiles.wizard_trust_auth_workflow_roots_needed")
                            : t("profiles.wizard_trust_auth_workflow_roots_optional")),
                    tone: enterpriseRootsEnabled ? "ready" : (hasEnterpriseFootprint ? "strict" : "default"),
                    target: "policy:Certificates",
                },
                {
                    title: t("profiles.wizard_trust_auth_workflow_files"),
                    copy: certificateFileCount > 0
                        ? t("profiles.wizard_trust_auth_workflow_files_ready").replace("{count}", String(certificateFileCount))
                        : (hasEnterpriseFootprint
                            ? t("profiles.wizard_trust_auth_workflow_files_needed")
                            : t("profiles.wizard_trust_auth_workflow_files_optional")),
                    tone: certificateFileCount > 0 ? "ready" : (hasEnterpriseFootprint ? "strict" : "default"),
                    target: "policy:Certificates",
                },
            ];

            wizardTrustAuthWorkflowListEl.replaceChildren(
                ...items.map((item) => {
                    const rowEl = documentRef.createElement("div");
                    rowEl.className = "wizard-export-plan-item";
                    rowEl.dataset.planTone = item.tone;

                    const copyEl = documentRef.createElement("div");
                    copyEl.className = "wizard-export-plan-copy";
                    const titleEl = documentRef.createElement("div");
                    titleEl.textContent = item.title;
                    const bodyEl = documentRef.createElement("div");
                    bodyEl.className = "wizard-input-hint";
                    bodyEl.textContent = item.copy;
                    copyEl.append(titleEl, bodyEl);

                    const actionEl = documentRef.createElement("button");
                    actionEl.type = "button";
                    actionEl.className = "button-base ghost-button wizard-export-plan-action";
                    actionEl.dataset.settingsJumpTarget = item.target;
                    actionEl.textContent = t("profiles.wizard_export_open");

                    rowEl.append(copyEl, actionEl);
                    return rowEl;
                }),
            );
        }

        function applyNetworkEnterprisePreset(presetKey) {
            const editor = getEditor();
            if (!editor) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const presetValues = networkEnterprisePresets[presetKey] || {};

                networkEnterpriseManagedKeys.forEach((key) => {
                    delete normalized[key];
                });
                Object.entries(presetValues).forEach(([key, value]) => {
                    normalized[key] = cloneJsonValue(value, value);
                });

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                renderNetworkEnterpriseSectionStatus(normalized);
                renderTrustAuthWorkflow(normalized);
                setStatus(t("profiles.wizard_policy_applied"), "info");
            } catch (e) {
                setStatus(t("profiles.error_wizard_network").replace("{detail}", e.message || e), "error");
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

        function resolveHomepagePreset(parsed) {
            const homepage = parsed?.Homepage && typeof parsed.Homepage === "object" && !Array.isArray(parsed.Homepage)
                ? parsed.Homepage
                : {};
            const url = typeof homepage.URL === "string" ? homepage.URL.trim() : "";
            const startPage = typeof homepage.StartPage === "string" ? homepage.StartPage.trim() : "";
            const locked = homepage.Locked === true || startPage === "homepage-locked";

            if (!url && !startPage && !locked) return "defaults";
            if (startPage === "previous-session") return "session";
            if (locked) return "locked";
            if (url || startPage === "homepage") return "portal";
            return "defaults";
        }

        function resolveHomeOverridesPreset(parsed) {
            const hasNewTab = typeof parsed?.NewTabPage === "boolean";
            const hasFirstRun = typeof parsed?.OverrideFirstRunPage === "string" && parsed.OverrideFirstRunPage.trim();
            const hasPostUpdate = typeof parsed?.OverridePostUpdatePage === "string" && parsed.OverridePostUpdatePage.trim();

            if (hasNewTab && (hasFirstRun || hasPostUpdate)) return "managed";
            if (hasFirstRun || hasPostUpdate) return "first_run";
            if (hasNewTab) return "new_tab";
            return "defaults";
        }

        function resolveSearchDefaultsPreset(parsed) {
            const searchEngines = parsed?.SearchEngines && typeof parsed.SearchEngines === "object" && !Array.isArray(parsed.SearchEngines)
                ? parsed.SearchEngines
                : {};
            const defaultEngine = typeof searchEngines.Default === "string" ? searchEngines.Default.trim() : "";
            const customCount = Array.isArray(searchEngines.Add) ? searchEngines.Add.length : 0;
            const hiddenCount = Array.isArray(searchEngines.Remove) ? searchEngines.Remove.length : 0;
            const installsBlocked = searchEngines.PreventInstalls === true;

            if (!defaultEngine && customCount === 0 && hiddenCount === 0 && !installsBlocked) return "defaults";
            if (customCount > 0) return "custom_engines";
            if (hiddenCount > 0 || installsBlocked) return "restricted";
            return "managed_default";
        }

        function resolveFirefoxSuggestPreset(parsed) {
            const firefoxSuggest = parsed?.FirefoxSuggest && typeof parsed.FirefoxSuggest === "object" && !Array.isArray(parsed.FirefoxSuggest)
                ? parsed.FirefoxSuggest
                : {};
            const web = firefoxSuggest.WebSuggestions;
            const sponsored = firefoxSuggest.SponsoredSuggestions;
            const improve = firefoxSuggest.ImproveSuggest;
            const locked = firefoxSuggest.Locked === true;

            if (typeof web !== "boolean" && typeof sponsored !== "boolean" && typeof improve !== "boolean" && !locked) {
                return "defaults";
            }
            if (locked || (web === false && sponsored === false && improve === false)) return "locked_down";
            if (web === false && sponsored !== true && improve !== true) return "private";
            return "managed";
        }

        function revealHomeField(targetSelector) {
            const targetEl = documentRef.querySelector(targetSelector);
            if (!targetEl) return;
            targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
            targetEl.classList.add("settings-target-highlight");
            window.setTimeout(() => {
                targetEl.classList.remove("settings-target-highlight");
            }, 1800);
            const focusTarget = targetEl.matches("input, select, textarea, button")
                ? targetEl
                : targetEl.querySelector("input, select, textarea, button");
            focusTarget?.focus?.({ preventScroll: true });
        }

        function revealSearchField(targetSelector, { expandPanel = false, toggleEl = null, panelEl = null } = {}) {
            if (expandPanel && panelEl && toggleEl && panelEl.hidden) {
                toggleEl.click();
            }
            window.setTimeout(() => {
                const targetEl = documentRef.querySelector(targetSelector);
                if (!targetEl) return;
                targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
                targetEl.classList.add("settings-target-highlight");
                window.setTimeout(() => {
                    targetEl.classList.remove("settings-target-highlight");
                }, 1800);
                const focusTarget = targetEl.matches("input, select, textarea, button")
                    ? targetEl
                    : targetEl.querySelector("input, select, textarea, button");
                focusTarget?.focus?.({ preventScroll: true });
            }, expandPanel ? 80 : 0);
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

        function renderSearchSurfacesWorkflow(parsed = {}) {
            if (!wizardSearchSurfacesWorkflowCopyEl || !wizardSearchSurfacesWorkflowListEl) return;

            const resolved = parsed && typeof parsed === "object" ? parsed : {};
            const searchEngines = resolved.SearchEngines && typeof resolved.SearchEngines === "object" && !Array.isArray(resolved.SearchEngines)
                ? resolved.SearchEngines
                : {};
            const firefoxSuggest = resolved.FirefoxSuggest && typeof resolved.FirefoxSuggest === "object" && !Array.isArray(resolved.FirefoxSuggest)
                ? resolved.FirefoxSuggest
                : {};
            const searchDefaultsConfigured = Boolean(
                (typeof searchEngines.Default === "string" && searchEngines.Default.trim())
                || typeof resolved.SearchSuggestEnabled === "boolean"
                || (typeof resolved.SearchBar === "string" && resolved.SearchBar.trim())
            );
            const managedEnginesConfigured = Boolean(
                (Array.isArray(searchEngines.Add) && searchEngines.Add.length)
                || (Array.isArray(searchEngines.Remove) && searchEngines.Remove.length)
                || typeof searchEngines.PreventInstalls === "boolean"
            );
            const firefoxSuggestConfigured = Object.values(firefoxSuggest).some((value) => typeof value === "boolean");
            const activeSearchDefaultsPreset = resolveSearchDefaultsPreset(resolved);
            const activeFirefoxSuggestPreset = resolveFirefoxSuggestPreset(resolved);
            const hasManagedSearchExperience = searchDefaultsConfigured || managedEnginesConfigured || firefoxSuggestConfigured;
            const hasCoordinatedSearchMix = [activeSearchDefaultsPreset, activeFirefoxSuggestPreset]
                .filter((value) => value && value !== "defaults").length >= 2;

            wizardSearchSurfacesWorkflowCopyEl.textContent = hasManagedSearchExperience
                ? t("profiles.wizard_search_surfaces_workflow_active")
                : t("profiles.wizard_search_surfaces_workflow_body");

            const items = [
                {
                    title: t("profiles.wizard_search_surfaces_workflow_item_defaults"),
                    copy: searchDefaultsConfigured
                        ? t("profiles.wizard_search_surfaces_workflow_item_defaults_ready")
                        : (hasManagedSearchExperience
                            ? t("profiles.wizard_search_surfaces_workflow_item_defaults_needed")
                            : t("profiles.wizard_search_surfaces_workflow_item_defaults_optional")),
                    tone: searchDefaultsConfigured ? "ready" : (hasManagedSearchExperience ? "strict" : "default"),
                    target: "field:wizard-search-default-engine",
                },
                {
                    title: t("profiles.wizard_search_surfaces_workflow_item_engines"),
                    copy: managedEnginesConfigured
                        ? t("profiles.wizard_search_surfaces_workflow_item_engines_ready")
                        : (hasManagedSearchExperience
                            ? t("profiles.wizard_search_surfaces_workflow_item_engines_needed")
                            : t("profiles.wizard_search_surfaces_workflow_item_engines_optional")),
                    tone: managedEnginesConfigured ? "ready" : (hasManagedSearchExperience ? "strict" : "default"),
                    target: "field:wizard-search-default-engine",
                },
                {
                    title: t("profiles.wizard_search_surfaces_workflow_item_suggest"),
                    copy: firefoxSuggestConfigured
                        ? t("profiles.wizard_search_surfaces_workflow_item_suggest_ready")
                        : (hasManagedSearchExperience
                            ? t("profiles.wizard_search_surfaces_workflow_item_suggest_needed")
                            : t("profiles.wizard_search_surfaces_workflow_item_suggest_optional")),
                    tone: firefoxSuggestConfigured ? "ready" : (hasManagedSearchExperience ? "strict" : "default"),
                    target: "field:firefox-suggest-web",
                },
                {
                    title: t("profiles.wizard_search_surfaces_workflow_item_mix"),
                    copy: hasCoordinatedSearchMix
                        ? t("profiles.wizard_search_surfaces_workflow_item_mix_ready")
                        : (hasManagedSearchExperience
                            ? t("profiles.wizard_search_surfaces_workflow_item_mix_optional")
                            : t("profiles.wizard_search_surfaces_workflow_item_mix_later")),
                    tone: hasCoordinatedSearchMix ? "ready" : "default",
                    target: "field:wizard-search-suggest",
                },
            ];

            wizardSearchSurfacesWorkflowListEl.replaceChildren(
                ...items.map((item) => {
                    const rowEl = documentRef.createElement("div");
                    rowEl.className = "wizard-export-plan-item";
                    rowEl.dataset.planTone = item.tone;

                    const copyEl = documentRef.createElement("div");
                    copyEl.className = "wizard-export-plan-copy";
                    const titleEl = documentRef.createElement("div");
                    titleEl.textContent = item.title;
                    const bodyEl = documentRef.createElement("div");
                    bodyEl.className = "wizard-input-hint";
                    bodyEl.textContent = item.copy;
                    copyEl.append(titleEl, bodyEl);

                    const actionEl = documentRef.createElement("button");
                    actionEl.type = "button";
                    actionEl.className = "button-base ghost-button wizard-export-plan-action";
                    actionEl.dataset.settingsJumpTarget = item.target;
                    actionEl.textContent = t("profiles.wizard_export_open");

                    rowEl.append(copyEl, actionEl);
                    return rowEl;
                }),
            );
        }

        function renderManualHomeAndSearchSectionStatuses(parsed) {
            renderPresetButtonState(generalPolicyPresetButtons, resolveGeneralPolicyPreset(parsed), "generalPolicyPreset");
            setManualSectionStatus(wizardGeneralPolicySectionStatusEl, getGeneralPolicySectionStatus(parsed));
            renderUpkeepGovernanceWorkflow(parsed);
            renderPresetButtonState(homepagePresetButtons, resolveHomepagePreset(parsed), "homepagePreset");
            renderPresetButtonState(homeOverridesPresetButtons, resolveHomeOverridesPreset(parsed), "homeOverridesPreset");
            renderPresetButtonState(firefoxHomePresetButtons, resolveFirefoxHomePreset(parsed), "firefoxHomePreset");
            renderPresetButtonState(searchDefaultsPresetButtons, resolveSearchDefaultsPreset(parsed), "searchDefaultsPreset");
            renderPresetButtonState(firefoxSuggestPresetButtons, resolveFirefoxSuggestPreset(parsed), "firefoxSuggestPreset");
            setManualSectionStatus(wizardHomepageSectionStatusEl, getHomepageManualSectionStatus(parsed));
            setManualSectionStatus(wizardHomeOverridesSectionStatusEl, getHomeOverridesManualSectionStatus(parsed));
            setManualSectionStatus(wizardFirefoxHomeSectionStatusEl, getFirefoxHomeManualSectionStatus(parsed));
            setManualSectionStatus(wizardSearchDefaultsSectionStatusEl, getSearchDefaultsManualSectionStatus(parsed));
            setManualSectionStatus(wizardFirefoxSuggestSectionStatusEl, getFirefoxSuggestManualSectionStatus(parsed));
            renderHomeSurfacesWorkflow(parsed);
            renderSearchSurfacesWorkflow(parsed);
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
            renderTrustAuthWorkflow(parsed);
        }

        function toggleNetworkEnterprisePanel() {
            networkEnterprisePanelPreference = !(wizardNetworkEnterpriseFineTuningPanelEl?.hidden === false);
            const editor = getEditor();
            if (!editor) return;
            try {
                const parsed = fromEditorValue(editor.getValue(), documentRef.getElementById("mode").value);
                renderNetworkEnterpriseSectionStatus(parsed && typeof parsed === "object" ? parsed : {});
                renderTrustAuthWorkflow(parsed && typeof parsed === "object" ? parsed : {});
            } catch {
                renderNetworkEnterpriseSectionStatus({});
                renderTrustAuthWorkflow({});
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

            renderProxySectionStatus(buildProxyFromWizardFields());

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
                renderProxySectionStatus(buildProxyFromWizardFields());
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
        homepagePresetButtons.forEach((button) => {
            button.addEventListener("click", () => {
                const presetKey = button.dataset.homepagePreset || "defaults";
                if (presetKey === "session") {
                    revealHomeField('[data-settings-target="field:wizard-homepage-start-page"]');
                    return;
                }
                revealHomeField('[data-settings-target="field:wizard-homepage-url"]');
            });
        });
        homepageSharedPresetButtons.forEach((button) => {
            button.addEventListener("click", () => {
                const presetKey = button.dataset.homepageSharedPreset || "portal_locked";
                if (presetKey === "return_session") {
                    revealHomeField('[data-settings-target="field:wizard-homepage-start-page"]');
                    return;
                }
                revealHomeField('[data-settings-target="field:wizard-homepage-url"]');
            });
        });
        homeOverridesPresetButtons.forEach((button) => {
            button.addEventListener("click", () => {
                const presetKey = button.dataset.homeOverridesPreset || "defaults";
                if (presetKey === "new_tab") {
                    revealHomeField('[data-settings-target="field:wizard-new-tab-page"]');
                    return;
                }
                if (presetKey === "first_run" || presetKey === "managed") {
                    revealHomeField('[data-settings-target="field:wizard-override-first-run"]');
                    return;
                }
            });
        });
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
        searchDefaultsPresetButtons.forEach((button) => {
            button.addEventListener("click", () => {
                const presetKey = button.dataset.searchDefaultsPreset || "defaults";
                if (presetKey === "managed_default") {
                    revealSearchField('[data-settings-target="field:wizard-search-default-engine"]');
                    return;
                }
                if (presetKey === "custom_engines") {
                    revealSearchField("#wizard-search-engine-list", {
                        expandPanel: true,
                        toggleEl: wizardSearchDefaultsFineTuningToggleEl,
                        panelEl: wizardSearchDefaultsFineTuningPanelEl,
                    });
                    return;
                }
                if (presetKey === "restricted") {
                    revealSearchField('[data-settings-target="field:wizard-search-prevent-installs"]', {
                        expandPanel: true,
                        toggleEl: wizardSearchDefaultsFineTuningToggleEl,
                        panelEl: wizardSearchDefaultsFineTuningPanelEl,
                    });
                    return;
                }
                revealSearchField('[data-settings-target="field:wizard-search-suggest"]');
            });
        });
        firefoxSuggestPresetButtons.forEach((button) => {
            button.addEventListener("click", () => {
                const presetKey = button.dataset.firefoxSuggestPreset || "defaults";
                if (presetKey === "locked_down") {
                    revealSearchField('[data-settings-target="field:firefox-suggest-locked"]', {
                        expandPanel: true,
                        toggleEl: wizardSearchSuggestFineTuningToggleEl,
                        panelEl: wizardSearchSuggestFineTuningPanelEl,
                    });
                    return;
                }
                revealSearchField('[data-settings-target="field:firefox-suggest-web"]');
            });
        });
        generalPolicyPresetButtons.forEach((button) => {
            button.addEventListener("click", () => {
                const presetKey = button.dataset.generalPolicyPreset || "defaults";
                if (presetKey === "updates") {
                    revealSearchField('[data-settings-target="policy:DisableAppUpdate"]');
                    return;
                }
                if (presetKey === "browser_prompt") {
                    revealSearchField('[data-settings-target="policy:DontCheckDefaultBrowser"]');
                    return;
                }
                if (presetKey === "downloads") {
                    revealSearchField('[data-settings-target="policy:PromptForDownloadLocation"]');
                    return;
                }
                if (presetKey === "managed") {
                    revealSearchField('[data-settings-target="policy:DisableAppUpdate"]');
                    return;
                }
                revealSearchField('[data-settings-target="policy:DontCheckDefaultBrowser"]');
            });
        });
        firefoxHomePresetButtons.forEach((button) => {
            button.addEventListener("click", () => {
                const presetKey = button.dataset.firefoxHomePreset || "defaults";
                if (presetKey === "managed") {
                    if (wizardFirefoxHomeFineTuningPanelEl?.hidden) {
                        wizardFirefoxHomeFineTuningToggleEl?.click();
                    }
                    window.setTimeout(() => {
                        revealHomeField('[data-settings-target="field:firefox-home-stories"]');
                    }, 90);
                    return;
                }
                if (presetKey === "shortcuts") {
                    revealHomeField('[data-settings-target="field:firefox-home-top-sites"]');
                    return;
                }
                revealHomeField('[data-settings-target="field:firefox-home-search"]');
            });
        });
        Array.from(documentRef.querySelectorAll("[data-network-enterprise-preset]")).forEach((button) => {
            button.addEventListener("click", () => {
                const presetKey = button.dataset.networkEnterprisePreset || "defaults";
                applyNetworkEnterprisePreset(presetKey);
            });
        });
        proxyPresetButtons.forEach((button) => {
            button.addEventListener("click", () => {
                const presetKey = button.dataset.proxyPreset || "defaults";
                applyProxyPreset(presetKey);
            });
        });

        return {
            renderManualHomeAndSearchSectionStatuses,
            syncFromEditor,
            applyFromWizard,
        };
    }

    window.BPMProfilesNetwork = { create };
})();
