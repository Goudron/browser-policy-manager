(() => {
    function create({
        managedExtensionProfiles = [],
        managedExtensionFields = [],
        managedExtensionStatusEls = [],
        elements = {},
        dependencies = {},
        state = {},
    }) {
        const {
            t,
            linesToArray,
            fromEditorValue,
            toEditorValue,
            setStatus,
            renderExtensionReviewSummary,
            updateWizardSummary,
        } = dependencies;
        const getEditor = state.getEditor || (() => null);
        const setCurrentRaw = state.setCurrentRaw || (() => {});
        const wizardExtensionManagedKeys = state.wizardExtensionManagedKeys || [];

        const {
            wizardExtensionDefaultModeEl,
            wizardExtensionInstallEl,
            wizardExtensionLockedEl,
            wizardExtensionUninstallEl,
            wizardExtensionSectionStatusEl,
            wizardExtensionFineTuningToggleEl,
            wizardExtensionFineTuningPanelEl,
            wizardExtensionMoreRulesToggleEl,
            wizardExtensionMoreRulesPanelEl,
            wizardExtensionCuratedStatusEl,
            wizardExtensionCuratedToggleEl,
            wizardExtensionCuratedPanelEl,
            wizardSyncSectionStatusEl,
            wizardSyncFineTuningToggleEl,
            wizardSyncFineTuningPanelEl,
            wizardLanguageSectionStatusEl,
            wizardAiSectionStatusEl,
            wizardAiSurfacesSectionStatusEl,
            wizardAiFineTuningToggleEl,
            wizardAiFineTuningPanelEl,
            wizardWebsiteSectionStatusEl,
            wizardWebsiteFineTuningToggleEl,
            wizardWebsiteFineTuningPanelEl,
        } = elements;
        let extensionFineTuningPanelPreference = null;
        let extensionMoreRulesPanelPreference = null;
        let curatedPanelPreference = null;
        const extensionProfileDetailsPreferences = new Map();
        let syncPanelPreference = null;
        let aiPanelPreference = null;
        let websitePanelPreference = null;

        function setText(el, value) {
            if (el) {
                el.textContent = String(value);
            }
        }

        function countTextareaLines(value) {
            return linesToArray(value).length;
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

        function countHandlerRuleBucket(bucket) {
            return bucket && typeof bucket === "object" && !Array.isArray(bucket)
                ? Object.keys(bucket).filter(Boolean).length
                : 0;
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

        function getManagedExtensionField(profileId, field) {
            return managedExtensionFields.find((element) =>
                element.dataset.extensionProfile === profileId && element.dataset.extensionField === field
            ) || null;
        }

        function getManagedExtensionStatusEl(profileId) {
            return managedExtensionStatusEls.find((element) =>
                element.dataset.extensionProfileStatus === profileId
            ) || null;
        }

        function getManagedExtensionCardEl(profileId) {
            return getManagedExtensionField(profileId, "mode")?.closest("[data-extension-profile-card]") || null;
        }

        function getManagedExtensionDetailsToggleEl(profileId) {
            return getManagedExtensionCardEl(profileId)?.querySelector("[data-extension-profile-toggle]") || null;
        }

        function getManagedExtensionDetailsPanelEl(profileId) {
            return getManagedExtensionCardEl(profileId)?.querySelector("[data-extension-profile-details-panel]") || null;
        }

        function formatManagedExtensionModeLabel(mode) {
            if (mode === "allowed") {
                return t("profiles.wizard_extension_profile_mode_allowed");
            }
            if (mode === "blocked") {
                return t("profiles.wizard_extension_profile_mode_blocked");
            }
            if (mode === "force_installed") {
                return t("profiles.wizard_extension_profile_mode_force");
            }
            if (mode === "normal_installed") {
                return t("profiles.wizard_extension_profile_mode_normal");
            }
            return "";
        }

        function getManagedExtensionProfileValues(profile) {
            const modeEl = getManagedExtensionField(profile.id, "mode");
            const urlEl = getManagedExtensionField(profile.id, "url");
            const updatesEl = getManagedExtensionField(profile.id, "updates_disabled");
            const privateEl = getManagedExtensionField(profile.id, "private_browsing");
            const mode = modeEl ? modeEl.value.trim() : "";
            const typedUrl = urlEl ? urlEl.value.trim() : "";
            const effectiveUrl = (mode === "force_installed" || mode === "normal_installed")
                ? (typedUrl || profile.defaultUrl)
                : typedUrl;

            return {
                mode,
                typedUrl,
                effectiveUrl,
                updatesDisabled: updatesEl?.checked === true,
                privateBrowsing: privateEl?.checked === true,
            };
        }

        function getManagedExtensionProfileState(profile) {
            const values = getManagedExtensionProfileValues(profile);
            const hasExplicitRule = Boolean(
                values.mode
                || values.typedUrl
                || values.updatesDisabled
                || values.privateBrowsing
            );

            if (!hasExplicitRule) {
                return { state: "missing", values };
            }

            const usesCatalogUrl = Boolean(
                (values.mode === "force_installed" || values.mode === "normal_installed")
                && values.effectiveUrl === profile.defaultUrl
            );

            if (usesCatalogUrl) {
                return { state: "catalog_url", values };
            }

            if (values.effectiveUrl && values.effectiveUrl !== profile.defaultUrl) {
                return { state: "custom_url", values };
            }

            return { state: "configured", values };
        }

        function formatManagedExtensionProfileState(profileState) {
            if (profileState.state === "missing") {
                return t("profiles.wizard_extension_profile_state_missing");
            }

            const parts = [];
            const modeLabel = formatManagedExtensionModeLabel(profileState.values?.mode || "");
            if (modeLabel) {
                parts.push(modeLabel);
            }
            if (profileState.state === "catalog_url") {
                parts.push(t("profiles.wizard_extension_profile_state_catalog_url"));
            } else if (profileState.state === "custom_url") {
                parts.push(t("profiles.wizard_extension_profile_state_custom_url"));
            } else if (!parts.length) {
                parts.push(t("profiles.wizard_extension_profile_state_configured"));
            }
            if (profileState.values?.updatesDisabled) {
                parts.push(t("profiles.wizard_extension_profile_state_updates_disabled"));
            }
            if (profileState.values?.privateBrowsing) {
                parts.push(t("profiles.wizard_extension_profile_state_private_browsing"));
            }
            return parts.join(" • ");
        }

        function setManagedExtensionDetailsExpanded(profileId, expanded) {
            const cardEl = getManagedExtensionCardEl(profileId);
            const panelEl = getManagedExtensionDetailsPanelEl(profileId);
            const toggleEl = getManagedExtensionDetailsToggleEl(profileId);

            if (cardEl) {
                cardEl.dataset.extensionProfileDetailsExpanded = expanded ? "true" : "false";
            }
            if (panelEl) {
                panelEl.hidden = !expanded;
            }
            if (toggleEl) {
                toggleEl.setAttribute("aria-expanded", expanded ? "true" : "false");
                toggleEl.textContent = expanded
                    ? t("profiles.wizard_extension_profile_details_hide")
                    : t("profiles.wizard_extension_profile_details_show");
            }
        }

        function syncManagedExtensionDetailsVisibility(profile, profileState) {
            const preferredState = extensionProfileDetailsPreferences.get(profile.id);
            const hasSecondaryDetails = profileState.state === "custom_url"
                || profileState.values?.updatesDisabled
                || profileState.values?.privateBrowsing;
            const expanded = preferredState === undefined ? hasSecondaryDetails : preferredState;

            setManagedExtensionDetailsExpanded(profile.id, expanded);
        }

        function formatDefaultModeLabel(defaultMode) {
            if (defaultMode === "allowed") {
                return t("profiles.wizard_extensions_mode_allowed");
            }
            if (defaultMode === "blocked") {
                return t("profiles.wizard_extensions_mode_blocked");
            }
            return t("profiles.wizard_extensions_mode_inherit");
        }

        function renderExtensionSectionStatus({ configuredCount = 0, customUrlCount = 0 } = {}) {
            const defaultMode = wizardExtensionDefaultModeEl?.value.trim() || "";
            const installCount = countTextareaLines(wizardExtensionInstallEl?.value || "");
            const lockedCount = countTextareaLines(wizardExtensionLockedEl?.value || "");
            const uninstallCount = countTextareaLines(wizardExtensionUninstallEl?.value || "");
            const fragments = [];

            if (defaultMode) {
                fragments.push(
                    t("profiles.wizard_extensions_section_state_mode")
                        .replace("{value}", formatDefaultModeLabel(defaultMode)),
                );
            }
            if (installCount > 0) {
                fragments.push(
                    t("profiles.wizard_extensions_section_state_install")
                        .replace("{count}", String(installCount)),
                );
            }
            if (lockedCount > 0) {
                fragments.push(
                    t("profiles.wizard_extensions_section_state_locked")
                        .replace("{count}", String(lockedCount)),
                );
            }
            if (uninstallCount > 0) {
                fragments.push(
                    t("profiles.wizard_extensions_section_state_uninstall")
                        .replace("{count}", String(uninstallCount)),
                );
            }
            if (configuredCount > 0) {
                fragments.push(
                    t("profiles.wizard_extensions_section_state_curated")
                        .replace("{count}", String(configuredCount)),
                );
            }

            setText(
                wizardExtensionSectionStatusEl,
                fragments.length
                    ? fragments.join(" • ")
                    : t("profiles.wizard_extensions_section_state_empty"),
            );

            let curatedStatus = t("profiles.wizard_extensions_profiles_empty");
            if (configuredCount > 0) {
                curatedStatus = t("profiles.wizard_extensions_profiles_configured")
                    .replace("{count}", String(configuredCount));
                if (customUrlCount > 0) {
                    curatedStatus += ` • ${t("profiles.wizard_extensions_profiles_custom_urls")
                        .replace("{count}", String(customUrlCount))}`;
                }
            }
            setText(wizardExtensionCuratedStatusEl, curatedStatus);

            setPanelExpanded(
                wizardExtensionFineTuningPanelEl,
                wizardExtensionFineTuningToggleEl,
                extensionFineTuningPanelPreference === null
                    ? (installCount + lockedCount + uninstallCount + configuredCount > 0)
                    : extensionFineTuningPanelPreference,
                t("profiles.wizard_fine_tuning_show"),
                t("profiles.wizard_fine_tuning_hide"),
            );
            setPanelExpanded(
                wizardExtensionMoreRulesPanelEl,
                wizardExtensionMoreRulesToggleEl,
                extensionMoreRulesPanelPreference === null
                    ? (uninstallCount + configuredCount > 0)
                    : extensionMoreRulesPanelPreference,
                t("profiles.wizard_more_rules_show"),
                t("profiles.wizard_more_rules_hide"),
            );
        }

        function setCuratedPanelExpanded(expanded) {
            if (wizardExtensionCuratedPanelEl) {
                wizardExtensionCuratedPanelEl.hidden = !expanded;
            }
            if (wizardExtensionCuratedToggleEl) {
                wizardExtensionCuratedToggleEl.setAttribute("aria-expanded", expanded ? "true" : "false");
                wizardExtensionCuratedToggleEl.textContent = expanded
                    ? t("profiles.wizard_extensions_profiles_hide")
                    : t("profiles.wizard_extensions_profiles_show");
            }
        }

        function syncCuratedPanelVisibility({ configuredCount = 0 } = {}) {
            const expanded = curatedPanelPreference === null ? configuredCount > 0 : curatedPanelPreference;
            setCuratedPanelExpanded(expanded);
        }

        function toggleCuratedPanel() {
            const currentlyExpanded = wizardExtensionCuratedPanelEl?.hidden === false;
            curatedPanelPreference = !currentlyExpanded;
            setCuratedPanelExpanded(curatedPanelPreference);
        }

        function toggleExtensionFineTuningPanel() {
            extensionFineTuningPanelPreference = !(wizardExtensionFineTuningPanelEl?.hidden === false);
            renderManagedExtensionProfileStatuses();
        }

        function toggleExtensionMoreRulesPanel() {
            extensionMoreRulesPanelPreference = !(wizardExtensionMoreRulesPanelEl?.hidden === false);
            renderManagedExtensionProfileStatuses();
        }

        function getStepSixSummaryData(parsed) {
            const userMessagingControls = countConfiguredObjectEntries(parsed?.UserMessaging);
            const requestedLocales = Array.isArray(parsed?.RequestedLocales)
                ? parsed.RequestedLocales.filter((entry) => typeof entry === "string" && entry.trim()).length
                : 0;
            const generativeAiControls = countConfiguredObjectEntries(parsed?.GenerativeAI);
            const websiteFilter = parsed?.WebsiteFilter && typeof parsed.WebsiteFilter === "object" && !Array.isArray(parsed.WebsiteFilter)
                ? parsed.WebsiteFilter
                : {};
            const handlers = parsed?.Handlers && typeof parsed.Handlers === "object" && !Array.isArray(parsed.Handlers)
                ? parsed.Handlers
                : {};

            return {
                accountsManaged: typeof parsed?.DisableFirefoxAccounts === "boolean",
                accountsDisabled: parsed?.DisableFirefoxAccounts === true,
                userMessagingControls,
                requestedLocales,
                translateManaged: typeof parsed?.TranslateEnabled === "boolean",
                translateEnabled: parsed?.TranslateEnabled === true,
                visualSearchManaged: typeof parsed?.VisualSearchEnabled === "boolean",
                generativeAiControls,
                blockedSites: Array.isArray(websiteFilter.Block) ? websiteFilter.Block.length : 0,
                exceptionSites: Array.isArray(websiteFilter.Exceptions) ? websiteFilter.Exceptions.length : 0,
                handlerRules: countHandlerRuleBucket(handlers.mimeTypes)
                    + countHandlerRuleBucket(handlers.schemes)
                    + countHandlerRuleBucket(handlers.extensions),
            };
        }

        function renderStepSixExperience(parsed) {
            const summary = getStepSixSummaryData(parsed && typeof parsed === "object" ? parsed : {});

            const syncFragments = [];
            if (summary.accountsManaged) {
                syncFragments.push(
                    summary.accountsDisabled
                        ? t("profiles.wizard_sync_section_state_accounts_disabled")
                        : t("profiles.wizard_sync_section_state_accounts_enabled"),
                );
            }
            if (summary.userMessagingControls > 0) {
                syncFragments.push(
                    t("profiles.wizard_sync_section_state_user_messaging")
                        .replace("{count}", String(summary.userMessagingControls)),
                );
            }
            setText(
                wizardSyncSectionStatusEl,
                syncFragments.length
                    ? syncFragments.join(" • ")
                    : t("profiles.wizard_sync_section_state_empty"),
            );

            const languageFragments = [];
            if (summary.requestedLocales > 0) {
                languageFragments.push(
                    t("profiles.wizard_language_section_state_locales")
                        .replace("{count}", String(summary.requestedLocales)),
                );
            }
            if (summary.translateManaged) {
                languageFragments.push(
                    summary.translateEnabled
                        ? t("profiles.wizard_language_section_state_translate_enabled")
                        : t("profiles.wizard_language_section_state_translate_disabled"),
                );
            }
            setText(
                wizardLanguageSectionStatusEl,
                languageFragments.length
                    ? languageFragments.join(" • ")
                    : t("profiles.wizard_language_section_state_empty"),
            );

            const websiteFragments = [];
            if (summary.blockedSites > 0) {
                websiteFragments.push(
                    t("profiles.wizard_website_section_state_blocked")
                        .replace("{count}", String(summary.blockedSites)),
                );
            }
            if (summary.exceptionSites > 0) {
                websiteFragments.push(
                    t("profiles.wizard_website_section_state_exceptions")
                        .replace("{count}", String(summary.exceptionSites)),
                );
            }
            if (summary.handlerRules > 0) {
                websiteFragments.push(
                    t("profiles.wizard_website_section_state_handlers")
                        .replace("{count}", String(summary.handlerRules)),
                );
            }
            setText(
                wizardWebsiteSectionStatusEl,
                websiteFragments.length
                    ? websiteFragments.join(" • ")
                    : t("profiles.wizard_website_section_state_empty"),
            );

            const showFineTuning = t("profiles.wizard_fine_tuning_show");
            const hideFineTuning = t("profiles.wizard_fine_tuning_hide");
            setPanelExpanded(
                wizardSyncFineTuningPanelEl,
                wizardSyncFineTuningToggleEl,
                syncPanelPreference === null ? summary.userMessagingControls > 0 : syncPanelPreference,
                showFineTuning,
                hideFineTuning,
            );
            setPanelExpanded(
                wizardWebsiteFineTuningPanelEl,
                wizardWebsiteFineTuningToggleEl,
                websitePanelPreference === null ? (summary.blockedSites + summary.exceptionSites + summary.handlerRules > 0) : websitePanelPreference,
                showFineTuning,
                hideFineTuning,
            );
        }

        function renderStepSevenAiExperience(parsed) {
            const summary = getStepSixSummaryData(parsed && typeof parsed === "object" ? parsed : {});
            const aiFragments = [];

            if (summary.generativeAiControls > 0) {
                aiFragments.push(
                    t("profiles.wizard_ai_section_state_controls")
                        .replace("{count}", String(summary.generativeAiControls)),
                );
            }
            if (summary.visualSearchManaged) {
                aiFragments.push(
                    summary.visualSearchEnabled
                        ? t("profiles.wizard_ai_section_state_visual_search_enabled")
                        : t("profiles.wizard_ai_section_state_visual_search_disabled"),
                );
            }

            setText(
                wizardAiSectionStatusEl,
                aiFragments.length
                    ? aiFragments.join(" • ")
                    : t("profiles.wizard_ai_section_state_empty"),
            );
            setText(
                wizardAiSurfacesSectionStatusEl,
                summary.visualSearchManaged
                    ? (
                        summary.visualSearchEnabled
                            ? t("profiles.wizard_ai_surfaces_state_visual_search_on")
                            : t("profiles.wizard_ai_surfaces_state_visual_search_off")
                    )
                    : t("profiles.wizard_ai_surfaces_state_empty"),
            );

            const showFineTuning = t("profiles.wizard_fine_tuning_show");
            const hideFineTuning = t("profiles.wizard_fine_tuning_hide");
            setPanelExpanded(
                wizardAiFineTuningPanelEl,
                wizardAiFineTuningToggleEl,
                aiPanelPreference === null ? summary.visualSearchManaged : aiPanelPreference,
                showFineTuning,
                hideFineTuning,
            );
        }

        function toggleSectionPanel(panelKey) {
            if (panelKey === "sync") {
                syncPanelPreference = !(wizardSyncFineTuningPanelEl?.hidden === false);
            }
            if (panelKey === "ai") {
                aiPanelPreference = !(wizardAiFineTuningPanelEl?.hidden === false);
            }
            if (panelKey === "website") {
                websitePanelPreference = !(wizardWebsiteFineTuningPanelEl?.hidden === false);
            }
            const editor = getEditor();
            if (!editor) return;
            try {
                const parsed = fromEditorValue(editor.getValue(), document.getElementById("mode").value);
                const normalized = parsed && typeof parsed === "object" ? parsed : {};
                renderStepSixExperience(normalized);
                renderStepSevenAiExperience(normalized);
            } catch {
                renderStepSixExperience({});
                renderStepSevenAiExperience({});
            }
        }

        function renderManagedExtensionProfileStatuses() {
            let configuredCount = 0;
            let customUrlCount = 0;

            managedExtensionProfiles.forEach((profile) => {
                const statusEl = getManagedExtensionStatusEl(profile.id);
                const modeEl = getManagedExtensionField(profile.id, "mode");
                const cardEl = modeEl?.closest(".wizard-section-group");
                const profileState = getManagedExtensionProfileState(profile);

                if (profileState.state !== "missing") configuredCount += 1;
                if (profileState.state === "custom_url") customUrlCount += 1;

                if (statusEl) {
                    statusEl.textContent = formatManagedExtensionProfileState(profileState);
                }
                if (cardEl) {
                    cardEl.dataset.extensionProfileState = profileState.state;
                    cardEl.classList.remove(
                        "wizard-search-engine-preset--applied",
                        "wizard-search-engine-preset--partial",
                        "wizard-search-engine-preset--conflict",
                    );
                    if (profileState.state === "catalog_url") cardEl.classList.add("wizard-search-engine-preset--applied");
                    if (profileState.state === "configured") cardEl.classList.add("wizard-search-engine-preset--partial");
                    if (profileState.state === "custom_url") cardEl.classList.add("wizard-search-engine-preset--conflict");
                }
                syncManagedExtensionDetailsVisibility(profile, profileState);
            });

            renderExtensionSectionStatus({ configuredCount, customUrlCount });
            syncCuratedPanelVisibility({ configuredCount, customUrlCount });
        }

        function syncFromEditor() {
            const editor = getEditor();
            if (!editor) return;
            extensionFineTuningPanelPreference = null;
            extensionMoreRulesPanelPreference = null;
            curatedPanelPreference = null;
            syncPanelPreference = null;
            aiPanelPreference = null;
            websitePanelPreference = null;

            try {
                const parsed = fromEditorValue(editor.getValue(), document.getElementById("mode").value);
                const normalized = parsed && typeof parsed === "object" ? parsed : {};
                const extensions = normalized.Extensions && typeof normalized.Extensions === "object" ? normalized.Extensions : {};
                const extensionSettings = normalized.ExtensionSettings && typeof normalized.ExtensionSettings === "object"
                    ? normalized.ExtensionSettings
                    : {};
                const defaultSettings = extensionSettings["*"] && typeof extensionSettings["*"] === "object"
                    ? extensionSettings["*"]
                    : {};

                wizardExtensionDefaultModeEl.disabled = false;
                wizardExtensionInstallEl.disabled = false;
                wizardExtensionLockedEl.disabled = false;
                wizardExtensionUninstallEl.disabled = false;
                managedExtensionFields.forEach((element) => {
                    element.disabled = false;
                });

                wizardExtensionDefaultModeEl.value = typeof defaultSettings.installation_mode === "string"
                    ? defaultSettings.installation_mode
                    : "";
                wizardExtensionInstallEl.value = Array.isArray(extensions.Install) ? extensions.Install.join("\n") : "";
                wizardExtensionLockedEl.value = Array.isArray(extensions.Locked) ? extensions.Locked.join("\n") : "";
                wizardExtensionUninstallEl.value = Array.isArray(extensions.Uninstall) ? extensions.Uninstall.join("\n") : "";

                managedExtensionProfiles.forEach((profile) => {
                    const settings = extensionSettings[profile.id] && typeof extensionSettings[profile.id] === "object"
                        ? extensionSettings[profile.id]
                        : {};
                    const modeEl = getManagedExtensionField(profile.id, "mode");
                    const urlEl = getManagedExtensionField(profile.id, "url");
                    const updatesEl = getManagedExtensionField(profile.id, "updates_disabled");
                    const privateEl = getManagedExtensionField(profile.id, "private_browsing");
                    if (modeEl) modeEl.value = typeof settings.installation_mode === "string" ? settings.installation_mode : "";
                    if (urlEl) urlEl.value = typeof settings.install_url === "string" ? settings.install_url : "";
                    if (updatesEl) updatesEl.checked = settings.updates_disabled === true;
                    if (privateEl) privateEl.checked = settings.private_browsing === true;
                });
                renderStepSixExperience(normalized);
                renderStepSevenAiExperience(normalized);
            } catch {
                wizardExtensionDefaultModeEl.value = "";
                wizardExtensionInstallEl.value = "";
                wizardExtensionLockedEl.value = "";
                wizardExtensionUninstallEl.value = "";
                wizardExtensionDefaultModeEl.disabled = true;
                wizardExtensionInstallEl.disabled = true;
                wizardExtensionLockedEl.disabled = true;
                wizardExtensionUninstallEl.disabled = true;
                managedExtensionFields.forEach((element) => {
                    if (element.type === "checkbox") {
                        element.checked = false;
                    } else {
                        element.value = "";
                    }
                    element.disabled = true;
                });
                renderStepSixExperience({});
                renderStepSevenAiExperience({});
            }

            renderManagedExtensionProfileStatuses();
            renderExtensionReviewSummary();
            updateWizardSummary();
        }

        function applyFromWizard() {
            const editor = getEditor();
            if (!editor) return;

            try {
                const mode = document.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const install = linesToArray(wizardExtensionInstallEl.value);
                const locked = linesToArray(wizardExtensionLockedEl.value);
                const uninstall = linesToArray(wizardExtensionUninstallEl.value);
                const defaultMode = wizardExtensionDefaultModeEl.value.trim();

                const nextExtensions = { ...(normalized.Extensions && typeof normalized.Extensions === "object" ? normalized.Extensions : {}) };
                const nextExtensionSettings = {
                    ...(normalized.ExtensionSettings && typeof normalized.ExtensionSettings === "object" ? normalized.ExtensionSettings : {}),
                };
                const nextDefaultSettings = {
                    ...(nextExtensionSettings["*"] && typeof nextExtensionSettings["*"] === "object" ? nextExtensionSettings["*"] : {}),
                };

                if (install.length) {
                    nextExtensions.Install = install;
                } else {
                    delete nextExtensions.Install;
                }

                if (locked.length) {
                    nextExtensions.Locked = locked;
                } else {
                    delete nextExtensions.Locked;
                }

                if (uninstall.length) {
                    nextExtensions.Uninstall = uninstall;
                } else {
                    delete nextExtensions.Uninstall;
                }

                if (defaultMode) {
                    nextDefaultSettings.installation_mode = defaultMode;
                } else {
                    delete nextDefaultSettings.installation_mode;
                }

                if (Object.keys(nextDefaultSettings).length) {
                    nextExtensionSettings["*"] = nextDefaultSettings;
                } else {
                    delete nextExtensionSettings["*"];
                }

                managedExtensionProfiles.forEach((profile) => {
                    const nextProfileSettings = {
                        ...(nextExtensionSettings[profile.id] && typeof nextExtensionSettings[profile.id] === "object"
                            ? nextExtensionSettings[profile.id]
                            : {}),
                    };
                    const modeEl = getManagedExtensionField(profile.id, "mode");
                    const urlEl = getManagedExtensionField(profile.id, "url");
                    const updatesEl = getManagedExtensionField(profile.id, "updates_disabled");
                    const privateEl = getManagedExtensionField(profile.id, "private_browsing");
                    const selectedMode = modeEl ? modeEl.value : "";
                    const typedUrl = urlEl ? urlEl.value.trim() : "";
                    const installUrl = (selectedMode === "force_installed" || selectedMode === "normal_installed")
                        ? (typedUrl || profile.defaultUrl)
                        : "";

                    wizardExtensionManagedKeys.forEach((key) => {
                        delete nextProfileSettings[key];
                    });

                    if (selectedMode) {
                        nextProfileSettings.installation_mode = selectedMode;
                    }
                    if (installUrl) {
                        nextProfileSettings.install_url = installUrl;
                    }
                    if (updatesEl?.checked) {
                        nextProfileSettings.updates_disabled = true;
                    }
                    if (privateEl?.checked) {
                        nextProfileSettings.private_browsing = true;
                    }

                    if (Object.keys(nextProfileSettings).length) {
                        nextExtensionSettings[profile.id] = nextProfileSettings;
                    } else {
                        delete nextExtensionSettings[profile.id];
                    }
                });

                if (Object.keys(nextExtensions).length) {
                    normalized.Extensions = nextExtensions;
                } else {
                    delete normalized.Extensions;
                }

                if (Object.keys(nextExtensionSettings).length) {
                    normalized.ExtensionSettings = nextExtensionSettings;
                } else {
                    delete normalized.ExtensionSettings;
                }

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                renderStepSixExperience(normalized);
                renderStepSevenAiExperience(normalized);
                renderManagedExtensionProfileStatuses();
                renderExtensionReviewSummary(normalized);
                setStatus(t("profiles.wizard_extensions_applied"), "info");
            } catch (e) {
                setStatus(t("profiles.error_wizard_extensions").replace("{detail}", e.message || e), "error");
            }
        }

        function bindInputListeners(applyExtensionsFromWizard) {
            managedExtensionFields.forEach((input) => {
                input.addEventListener("input", applyExtensionsFromWizard);
                input.addEventListener("change", applyExtensionsFromWizard);
            });
            [
                wizardExtensionDefaultModeEl,
                wizardExtensionInstallEl,
                wizardExtensionLockedEl,
                wizardExtensionUninstallEl,
            ].forEach((input) => {
                input.addEventListener("input", applyExtensionsFromWizard);
                input.addEventListener("change", applyExtensionsFromWizard);
            });
            if (wizardExtensionCuratedToggleEl) {
                wizardExtensionCuratedToggleEl.addEventListener("click", () => {
                    toggleCuratedPanel();
                });
            }
            managedExtensionProfiles.forEach((profile) => {
                const toggleEl = getManagedExtensionDetailsToggleEl(profile.id);
                if (!toggleEl) return;
                toggleEl.addEventListener("click", () => {
                    const nextExpanded = getManagedExtensionDetailsPanelEl(profile.id)?.hidden !== false;
                    extensionProfileDetailsPreferences.set(profile.id, nextExpanded);
                    setManagedExtensionDetailsExpanded(profile.id, nextExpanded);
                });
            });
            if (wizardExtensionFineTuningToggleEl) {
                wizardExtensionFineTuningToggleEl.addEventListener("click", () => {
                    toggleExtensionFineTuningPanel();
                });
            }
            if (wizardExtensionMoreRulesToggleEl) {
                wizardExtensionMoreRulesToggleEl.addEventListener("click", () => {
                    toggleExtensionMoreRulesPanel();
                });
            }
            if (wizardSyncFineTuningToggleEl) {
                wizardSyncFineTuningToggleEl.addEventListener("click", () => {
                    toggleSectionPanel("sync");
                });
            }
            if (wizardAiFineTuningToggleEl) {
                wizardAiFineTuningToggleEl.addEventListener("click", () => {
                    toggleSectionPanel("ai");
                });
            }
            if (wizardWebsiteFineTuningToggleEl) {
                wizardWebsiteFineTuningToggleEl.addEventListener("click", () => {
                    toggleSectionPanel("website");
                });
            }
        }

        return {
            getManagedExtensionField,
            renderManagedExtensionProfileStatuses,
            syncFromEditor,
            applyFromWizard,
            bindInputListeners,
        };
    }

    window.BPMProfilesExtensions = { create };
})();
