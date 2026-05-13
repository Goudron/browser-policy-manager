(() => {
    function create({
        documentRef = document,
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
            getActiveWizardSchemaVersion,
        } = dependencies;
        const getEditor = state.getEditor || (() => null);
        const setCurrentRaw = state.setCurrentRaw || (() => {});
        const wizardExtensionManagedKeys = state.wizardExtensionManagedKeys || [];

        const {
            wizardExtensionDefaultModeEl,
            wizardExtensionInstallEl,
            wizardExtensionInstallSummaryEl,
            wizardExtensionInstallToggleEl,
            wizardExtensionInstallPanelEl,
            wizardExtensionLockedEl,
            wizardExtensionLockedSummaryEl,
            wizardExtensionLockedToggleEl,
            wizardExtensionLockedPanelEl,
            wizardExtensionUninstallEl,
            wizardExtensionUninstallSummaryEl,
            wizardExtensionUninstallToggleEl,
            wizardExtensionUninstallPanelEl,
            wizardExtensionSectionStatusEl,
            wizardExtensionFineTuningToggleEl,
            wizardExtensionFineTuningPanelEl,
            wizardExtensionCuratedStatusEl,
            wizardExtensionCuratedToggleEl,
            wizardExtensionCuratedPanelEl,
            wizardSyncSectionStatusEl,
            wizardSyncFineTuningToggleEl,
            wizardSyncFineTuningPanelEl,
            wizardBookmarksSectionStatusEl,
            wizardBookmarksOpenAdvancedEl,
            wizardBookmarksConfiguredActionsEl,
            wizardBookmarksLinksJumpEl,
            wizardBookmarksFoldersJumpEl,
            wizardBookmarksNestedJumpEl,
            wizardLanguageSectionStatusEl,
            wizardLanguageAiHandoffEl,
            wizardAiEsrcEmptyStateEl,
            wizardAiPostureBarEl,
            wizardAiPostureBodyEl,
            wizardAiPosturePresetsEl,
            wizardAiPolicyControlsEl,
            wizardAiProvidersHandoffEl,
            wizardAiSectionStatusEl,
            wizardAiControlsCardEl,
            wizardGenerativeAiCardEl,
            wizardVisualSearchEnabledCardEl,
            wizardAiGovernanceCopyEl,
            wizardAiProvidersOpenAdvancedEl,
            wizardWebsiteSectionStatusEl,
            wizardWebsiteFineTuningToggleEl,
            wizardWebsiteFineTuningPanelEl,
        } = elements;
        let extensionFineTuningPanelPreference = null;
        let extensionInstallPanelPreference = null;
        let extensionLockedPanelPreference = null;
        let extensionUninstallPanelPreference = null;
        let curatedPanelPreference = null;
        const extensionProfileDetailsPreferences = new Map();
        let syncPanelPreference = null;
        let websitePanelPreference = null;
        const extensionGovernancePresetButtons = Array.from(document.querySelectorAll("[data-extension-governance-preset]"));
        const aiPosturePresetButtons = Array.from(document.querySelectorAll("[data-ai-posture-preset]"));
        const syncFocusPresetButtons = Array.from(documentRef.querySelectorAll("[data-sync-focus-preset]"));
        const languagePresetButtons = Array.from(documentRef.querySelectorAll("[data-language-preset]"));
        const websiteAccessPostureButtons = Array.from(documentRef.querySelectorAll("[data-website-access-posture]"));
        const websiteAccessHandlerButtons = Array.from(documentRef.querySelectorAll("[data-website-access-handlers]"));
        const aiProvidersSectionStatusEl = document.getElementById("wizard-ai-providers-section-status");

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

        function isReleaseAiWizardAvailable() {
            return getActiveWizardSchemaVersion() === "release-150";
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

        function focusTargetForA11y(targetEl) {
            if (!targetEl) return;
            const focusTarget = targetEl.matches("input, select, textarea, button, [tabindex]")
                ? targetEl
                : targetEl.querySelector("input, select, textarea, button, [tabindex]");
            const resolvedTarget = focusTarget || targetEl;
            if (!resolvedTarget.matches("input, select, textarea, button, [tabindex]")) {
                resolvedTarget.setAttribute("tabindex", "-1");
            }
            resolvedTarget.focus?.({ preventScroll: true });
        }

        function renderPresetButtonState(buttons, activeKey, datasetKey) {
            buttons.forEach((button) => {
                const isActive = button.dataset[datasetKey] === activeKey;
                button.classList.toggle("wizard-search-engine-preset--applied", isActive);
                button.classList.toggle("wizard-search-engine-preset--partial", false);
                button.classList.toggle("wizard-search-engine-preset--conflict", false);
                button.setAttribute("aria-pressed", isActive ? "true" : "false");
            });
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

        function resolveExtensionGovernancePreset({
            defaultMode = "",
            installCount = 0,
            lockedCount = 0,
            uninstallCount = 0,
            configuredCount = 0,
        } = {}) {
            const rulesCount = installCount + lockedCount + uninstallCount;
            if (configuredCount > 0 && rulesCount > 0) return "mixed";
            if (configuredCount > 0) return "curated";
            if (rulesCount > 0) return "managed";
            if (defaultMode === "allowed") return "open";
            if (defaultMode === "blocked") return "blocked";
            return "";
        }

        function applyExtensionGovernancePreset(presetKey) {
            if (!wizardExtensionDefaultModeEl) return;
            if (presetKey === "open") {
                wizardExtensionDefaultModeEl.value = "allowed";
            } else {
                wizardExtensionDefaultModeEl.value = "blocked";
            }

            if (presetKey === "managed") {
                extensionFineTuningPanelPreference = true;
                extensionInstallPanelPreference = true;
            } else if (presetKey === "curated") {
                extensionFineTuningPanelPreference = true;
                curatedPanelPreference = true;
            } else if (presetKey === "mixed") {
                extensionFineTuningPanelPreference = true;
                extensionInstallPanelPreference = true;
                curatedPanelPreference = true;
            }
            applyFromWizard();
        }

        function revealExtensionArea(kind) {
            extensionFineTuningPanelPreference = true;
            setPanelExpanded(
                wizardExtensionFineTuningPanelEl,
                wizardExtensionFineTuningToggleEl,
                true,
                t("profiles.wizard_fine_tuning_show"),
                t("profiles.wizard_fine_tuning_hide"),
            );

            let targetEl = null;
            if (kind === "known") {
                curatedPanelPreference = true;
                setCuratedPanelExpanded(true);
                targetEl = document.getElementById("wizard-extension-curated-section");
            } else if (kind === "rules") {
                extensionInstallPanelPreference = true;
                setPanelExpanded(
                    wizardExtensionInstallPanelEl,
                    wizardExtensionInstallToggleEl,
                    true,
                    t("profiles.wizard_extension_rule_show"),
                    t("profiles.wizard_extension_rule_hide"),
                );
                targetEl = wizardExtensionInstallEl?.closest(".wizard-subsection-card") || wizardExtensionInstallEl;
            } else if (kind === "mixed") {
                curatedPanelPreference = true;
                setCuratedPanelExpanded(true);
                targetEl = document.getElementById("wizard-extension-curated-section")
                    || wizardExtensionInstallEl?.closest(".wizard-subsection-card");
            }

            if (!targetEl) return;
            targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
            targetEl.classList.add("settings-target-highlight");
            window.setTimeout(() => {
                targetEl.classList.remove("settings-target-highlight");
            }, 1800);
            focusTargetForA11y(targetEl);
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

            renderPresetButtonState(
                extensionGovernancePresetButtons,
                resolveExtensionGovernancePreset({
                    defaultMode,
                    installCount,
                    lockedCount,
                    uninstallCount,
                    configuredCount,
                }),
                "extensionGovernancePreset",
            );

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

            setText(
                wizardExtensionInstallSummaryEl,
                installCount > 0
                    ? t("profiles.wizard_extensions_rule_count").replace("{count}", String(installCount))
                    : t("profiles.wizard_extensions_rule_empty"),
            );
            setText(
                wizardExtensionLockedSummaryEl,
                lockedCount > 0
                    ? t("profiles.wizard_extensions_rule_count").replace("{count}", String(lockedCount))
                    : t("profiles.wizard_extensions_rule_empty"),
            );
            setText(
                wizardExtensionUninstallSummaryEl,
                uninstallCount > 0
                    ? t("profiles.wizard_extensions_rule_count").replace("{count}", String(uninstallCount))
                    : t("profiles.wizard_extensions_rule_empty"),
            );

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
                wizardExtensionInstallPanelEl,
                wizardExtensionInstallToggleEl,
                extensionInstallPanelPreference === null ? installCount > 0 : extensionInstallPanelPreference,
                t("profiles.wizard_extension_rule_show"),
                t("profiles.wizard_extension_rule_hide"),
            );
            setPanelExpanded(
                wizardExtensionLockedPanelEl,
                wizardExtensionLockedToggleEl,
                extensionLockedPanelPreference === null ? lockedCount > 0 : extensionLockedPanelPreference,
                t("profiles.wizard_extension_rule_show"),
                t("profiles.wizard_extension_rule_hide"),
            );
            setPanelExpanded(
                wizardExtensionUninstallPanelEl,
                wizardExtensionUninstallToggleEl,
                extensionUninstallPanelPreference === null ? uninstallCount > 0 : extensionUninstallPanelPreference,
                t("profiles.wizard_extension_rule_show"),
                t("profiles.wizard_extension_rule_hide"),
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

        function getStepSixSummaryData(parsed) {
            const bookmarkEntries = Array.isArray(parsed?.Bookmarks)
                ? parsed.Bookmarks.filter((item) => item && typeof item === "object" && !Array.isArray(item) && Object.keys(item).length > 0)
                : [];
            const managedFolders = Array.isArray(parsed?.ManagedBookmarks)
                ? parsed.ManagedBookmarks.filter((item) => item && typeof item === "object" && !Array.isArray(item) && Object.keys(item).length > 0)
                : [];
            const nestedRows = managedFolders.filter((item) => Array.isArray(item.children) && item.children.length > 0);
            const userMessagingControls = countConfiguredObjectEntries(parsed?.UserMessaging);
            const requestedLocales = Array.isArray(parsed?.RequestedLocales)
                ? parsed.RequestedLocales.filter((entry) => typeof entry === "string" && entry.trim()).length
                : 0;
            const generativeAiControls = countConfiguredObjectEntries(parsed?.GenerativeAI);
            const aiControls = parsed?.AIControls && typeof parsed.AIControls === "object" && !Array.isArray(parsed.AIControls)
                ? parsed.AIControls
                : {};
            const aiControlsManaged = countConfiguredObjectEntries(aiControls);
            const aiDefaultControl = aiControls.Default && typeof aiControls.Default === "object" && !Array.isArray(aiControls.Default)
                ? aiControls.Default
                : {};
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
                visualSearchEnabled: parsed?.VisualSearchEnabled === true,
                aiControlsManaged,
                aiDefaultBlocked: aiDefaultControl.Value === "blocked",
                aiDefaultAvailable: aiDefaultControl.Value === "available",
                aiDefaultLocked: aiDefaultControl.Locked === true,
                generativeAiControls,
                bookmarkEntries: bookmarkEntries.length,
                managedBookmarkFolders: managedFolders.length,
                nestedBookmarkFolders: nestedRows.length,
                blockedSites: Array.isArray(websiteFilter.Block) ? websiteFilter.Block.length : 0,
                exceptionSites: Array.isArray(websiteFilter.Exceptions) ? websiteFilter.Exceptions.length : 0,
                handlerMimeRules: countHandlerRuleBucket(handlers.mimeTypes),
                handlerSchemeRules: countHandlerRuleBucket(handlers.schemes),
                handlerExtensionRules: countHandlerRuleBucket(handlers.extensions),
                intranetSingleWordManaged: parsed?.GoToIntranetSiteForSingleWordEntryInAddressBar === true,
            };
        }

        function hasUsableAiControlsCard() {
            return !isAiPolicyUnsupported(wizardAiControlsCardEl);
        }

        function hasUsableGenerativeAiCard() {
            return !isAiPolicyUnsupported(wizardGenerativeAiCardEl);
        }

        function buildAiControlsValue(presetKey) {
            if (presetKey === "disable") {
                return {
                    Default: {
                        Value: "blocked",
                        Locked: true,
                    },
                };
            }
            if (presetKey === "availability") {
                return {
                    Default: {
                        Value: "available",
                        Locked: true,
                    },
                };
            }
            if (presetKey === "mixed") {
                return {
                    Default: {
                        Value: "available",
                        Locked: true,
                    },
                    SidebarChatbot: {
                        Value: "blocked",
                        Locked: true,
                    },
                    SmartWindow: {
                        Value: "blocked",
                        Locked: true,
                    },
                };
            }
            return null;
        }

        function buildLegacyGenerativeAiValue(presetKey) {
            if (presetKey === "disable") {
                return {
                    Enabled: false,
                    Chatbot: false,
                    LinkPreviews: false,
                    TabGroups: false,
                    Locked: true,
                };
            }
            if (presetKey === "availability") {
                return {
                    Enabled: true,
                    Locked: true,
                };
            }
            if (presetKey === "mixed") {
                return {
                    Enabled: true,
                    Chatbot: true,
                    LinkPreviews: true,
                    TabGroups: true,
                    Locked: true,
                };
            }
            return null;
        }

        function resolveAiPosturePreset(summary) {
            const managedAiControls = summary.aiControlsManaged > 0 || summary.generativeAiControls > 0;
            if ((summary.aiDefaultBlocked || summary.generativeAiControls > 0) && summary.visualSearchManaged && !summary.visualSearchEnabled) {
                return "disable";
            }
            if (managedAiControls && summary.visualSearchManaged) {
                return "mixed";
            }
            if (managedAiControls) {
                return "availability";
            }
            return "defaults";
        }

        function resolveWebsiteHandlersPreset(summary) {
            const fileRules = summary.handlerMimeRules + summary.handlerExtensionRules;
            const protocolRules = summary.handlerSchemeRules;

            if (fileRules > 0 && protocolRules > 0) return "both";
            if (fileRules > 0) return "files";
            if (protocolRules > 0) return "protocols";
            return "defaults";
        }

        function resolveWebsiteAccessPosture(summary) {
            if (summary.blockedSites > 0 && summary.exceptionSites > 0) return "mixed";
            if (summary.blockedSites > 0) return "block_some";
            if (summary.exceptionSites > 0) return "allow_only";
            return "defaults";
        }

        function resolveSyncFocusPreset(summary) {
            if (summary.accountsManaged && summary.userMessagingControls > 0) return "managed";
            if (summary.userMessagingControls > 0) return "guidance";
            if (summary.accountsManaged) return "accounts";
            return "defaults";
        }

        function resolveLanguagePreset(summary) {
            if (summary.requestedLocales > 0 && summary.translateManaged && summary.translateEnabled) {
                return "managed";
            }
            if (summary.requestedLocales > 0) {
                return "locales";
            }
            if (summary.translateManaged && !summary.translateEnabled) {
                return "translation_off";
            }
            return "defaults";
        }

        function applyLanguagePreset(presetKey) {
            const editor = getEditor();
            if (!editor) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const existingLocales = Array.isArray(parsed?.RequestedLocales)
                    ? parsed.RequestedLocales.filter((entry) => typeof entry === "string" && entry.trim())
                    : [];

                delete normalized.RequestedLocales;
                delete normalized.TranslateEnabled;

                if (presetKey === "locales") {
                    normalized.RequestedLocales = existingLocales.length ? existingLocales : ["en-US", "ru"];
                } else if (presetKey === "translation_off") {
                    normalized.TranslateEnabled = false;
                } else if (presetKey === "managed") {
                    normalized.RequestedLocales = existingLocales.length ? existingLocales : ["en-US", "ru"];
                    normalized.TranslateEnabled = true;
                }

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                renderStepSixWorkspace(normalized);
                updateWizardSummary();
                setStatus(t("profiles.wizard_policy_applied"), "info");
            } catch (e) {
                setStatus(t("profiles.error_wizard_policy").replace("{detail}", e.message || e), "error");
            }
        }

        function applyWebsiteAccessPosturePreset(presetKey) {
            const editor = getEditor();
            if (!editor) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const nextWebsiteFilter = {};

                if (presetKey === "block_some") {
                    nextWebsiteFilter.Block = ["https://blocked.example.test"];
                } else if (presetKey === "allow_only") {
                    nextWebsiteFilter.Exceptions = ["https://allowed.example.test"];
                } else if (presetKey === "mixed") {
                    nextWebsiteFilter.Block = ["https://blocked.example.test"];
                    nextWebsiteFilter.Exceptions = ["https://allowed.example.test"];
                }

                if (Object.keys(nextWebsiteFilter).length) {
                    normalized.WebsiteFilter = nextWebsiteFilter;
                } else {
                    delete normalized.WebsiteFilter;
                }

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                renderStepSixWorkspace(normalized);
                updateWizardSummary();
                setStatus(t("profiles.wizard_policy_applied"), "info");
            } catch (e) {
                setStatus(t("profiles.error_wizard_policy").replace("{detail}", e.message || e), "error");
            }
        }

        function applyWebsiteHandlersPreset(presetKey) {
            const editor = getEditor();
            if (!editor) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const nextHandlers = {};

                if (presetKey === "mime_types") {
                    nextHandlers.mimeTypes = {
                        "application/pdf": { action: "saveToDisk" },
                    };
                } else if (presetKey === "protocols") {
                    nextHandlers.schemes = {
                        mailto: { action: "useSystemDefault" },
                    };
                } else if (presetKey === "mixed") {
                    nextHandlers.mimeTypes = {
                        "application/pdf": { action: "saveToDisk" },
                    };
                    nextHandlers.schemes = {
                        mailto: { action: "useSystemDefault" },
                    };
                }

                if (Object.keys(nextHandlers).length) {
                    normalized.Handlers = nextHandlers;
                } else {
                    delete normalized.Handlers;
                }

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                renderStepSixWorkspace(normalized);
                updateWizardSummary();
                setStatus(t("profiles.wizard_policy_applied"), "info");
            } catch (e) {
                setStatus(t("profiles.error_wizard_policy").replace("{detail}", e.message || e), "error");
            }
        }

        function revealLanguageTarget(kind) {
            const targetEl = kind === "translate"
                ? documentRef.getElementById("wizard-translate-enabled-card")
                : documentRef.getElementById("wizard-requested-locales-card");
            if (!targetEl) return;
            targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
            targetEl.classList.add("settings-target-highlight");
            window.setTimeout(() => {
                targetEl.classList.remove("settings-target-highlight");
            }, 1800);
            targetEl.querySelector("input, select, textarea, button")?.focus?.({ preventScroll: true });
        }

        function revealHandlersCard() {
            if (wizardWebsiteFineTuningPanelEl?.hidden !== false) {
                websitePanelPreference = true;
                setPanelExpanded(
                    wizardWebsiteFineTuningPanelEl,
                    wizardWebsiteFineTuningToggleEl,
                    true,
                    t("profiles.wizard_fine_tuning_show"),
                    t("profiles.wizard_fine_tuning_hide"),
                );
            }
            const handlersCardEl = documentRef.getElementById("wizard-handlers-card");
            if (!handlersCardEl) return;
            handlersCardEl.scrollIntoView({ behavior: "smooth", block: "center" });
            handlersCardEl.classList.add("settings-target-highlight");
            window.setTimeout(() => {
                handlersCardEl.classList.remove("settings-target-highlight");
            }, 1800);
            focusTargetForA11y(handlersCardEl);
        }

        function revealWebsiteFilterCard() {
            const filterCardEl = documentRef.getElementById("wizard-website-filter-card");
            if (!filterCardEl) return;
            filterCardEl.scrollIntoView({ behavior: "smooth", block: "center" });
            filterCardEl.classList.add("settings-target-highlight");
            window.setTimeout(() => {
                filterCardEl.classList.remove("settings-target-highlight");
            }, 1800);
            focusTargetForA11y(filterCardEl);
        }

        function revealSyncFocus(kind) {
            if (kind === "guidance" || kind === "managed") {
                if (wizardSyncFineTuningPanelEl?.hidden !== false) {
                    syncPanelPreference = true;
                    setPanelExpanded(
                        wizardSyncFineTuningPanelEl,
                        wizardSyncFineTuningToggleEl,
                        true,
                        t("profiles.wizard_fine_tuning_show"),
                        t("profiles.wizard_fine_tuning_hide"),
                    );
                }
                const messagingTarget = documentRef.getElementById("wizard-user-messaging-card");
                if (!messagingTarget) return;
                messagingTarget.scrollIntoView({ behavior: "smooth", block: "center" });
                messagingTarget.classList.add("settings-target-highlight");
                window.setTimeout(() => {
                    messagingTarget.classList.remove("settings-target-highlight");
                }, 1800);
                focusTargetForA11y(messagingTarget);
                return;
            }

            const accountTarget = documentRef.querySelector('[data-policy-key="DisableFirefoxAccounts"]')
                || documentRef.querySelector("#wizard-step-6 [data-policy-key]")
                || wizardSyncSectionStatusEl;
            if (!accountTarget) return;
            accountTarget.scrollIntoView({ behavior: "smooth", block: "center" });
            accountTarget.classList.add("settings-target-highlight");
            window.setTimeout(() => {
                accountTarget.classList.remove("settings-target-highlight");
            }, 1800);
            focusTargetForA11y(accountTarget);
        }

        function revealBookmarksFocus(kind) {
            const jumpId = kind === "links"
                ? "wizard-bookmark-summary-links-jump"
                : (kind === "folders" || kind === "mixed"
                    ? "wizard-bookmark-summary-folders-jump"
                    : "wizard-bookmark-summary-links-jump");
            const jumpButton = documentRef.getElementById(jumpId);
            if (jumpButton && !jumpButton.disabled) {
                jumpButton.click();
                return;
            }
            openBookmarksAdvanced(kind);
        }

        function openBookmarksAdvanced(kind = "links") {
            const advancedLink = documentRef.getElementById("editor-mode-settings");
            const advancedHref = advancedLink?.getAttribute("href") || "";
            if (
                !advancedLink
                || advancedLink.getAttribute("aria-disabled") === "true"
                || advancedLink.matches("button[disabled]")
                || !advancedHref
                || advancedHref === "#"
            ) {
                return;
            }

            const wantsManaged = kind === "folders" || kind === "mixed" || kind === "nested";
            const focusTarget = wantsManaged
                ? "shell-policy:6:ManagedBookmarks"
                : "shell-policy:6:Bookmarks";

            try {
                const nextUrl = new URL(advancedHref, window.location.origin);
                nextUrl.searchParams.set("focus", focusTarget);
                const advancedWindow = window.open(
                    `${nextUrl.pathname}${nextUrl.search}`,
                    "_blank",
                    "noopener",
                );
                if (advancedWindow) {
                    advancedWindow.opener = null;
                }
                return;
            } catch {
                advancedLink.click();
            }
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
            renderPresetButtonState(
                syncFocusPresetButtons,
                resolveSyncFocusPreset(summary),
                "syncFocusPreset",
            );

            const bookmarkFragments = [];
            if (summary.bookmarkEntries > 0) {
                bookmarkFragments.push(
                    t("profiles.wizard_bookmarks_section_state_links")
                        .replace("{count}", String(summary.bookmarkEntries)),
                );
            }
            if (summary.managedBookmarkFolders > 0) {
                bookmarkFragments.push(
                    t("profiles.wizard_bookmarks_section_state_folders")
                        .replace("{count}", String(summary.managedBookmarkFolders)),
                );
            }
            if (summary.nestedBookmarkFolders > 0) {
                bookmarkFragments.push(
                    t("profiles.wizard_bookmarks_section_state_nested")
                        .replace("{count}", String(summary.nestedBookmarkFolders)),
                );
            }
            setText(
                wizardBookmarksSectionStatusEl,
                bookmarkFragments.length
                    ? bookmarkFragments.join(" • ")
                    : t("profiles.wizard_bookmarks_section_state_empty"),
            );
            const hasConfiguredBookmarks = summary.bookmarkEntries + summary.managedBookmarkFolders + summary.nestedBookmarkFolders > 0;
            if (wizardBookmarksConfiguredActionsEl) {
                wizardBookmarksConfiguredActionsEl.hidden = !hasConfiguredBookmarks;
            }
            [
                { el: wizardBookmarksLinksJumpEl, count: summary.bookmarkEntries },
                { el: wizardBookmarksFoldersJumpEl, count: summary.managedBookmarkFolders },
                { el: wizardBookmarksNestedJumpEl, count: summary.nestedBookmarkFolders },
            ].forEach(({ el, count }) => {
                if (!el) return;
                el.hidden = count <= 0;
                el.disabled = count <= 0;
            });

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
            setText(
                wizardLanguageAiHandoffEl,
                summary.generativeAiControls > 0 || summary.visualSearchManaged
                    ? t("profiles.wizard_language_ai_handoff_go_ai")
                    : (
                        summary.requestedLocales > 0 || summary.translateManaged
                            ? t("profiles.wizard_language_ai_handoff_skip")
                            : t("profiles.wizard_language_ai_handoff_optional")
                    ),
            );
            renderPresetButtonState(
                languagePresetButtons,
                resolveLanguagePreset(summary),
                "languagePreset",
            );
            const websiteFragments = [];
            const handlerRules = summary.handlerMimeRules + summary.handlerSchemeRules + summary.handlerExtensionRules;
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
            if (handlerRules > 0) {
                websiteFragments.push(
                    t("profiles.wizard_website_section_state_handlers")
                        .replace("{count}", String(handlerRules)),
                );
            }
            renderPresetButtonState(
                websiteAccessPostureButtons,
                resolveWebsiteAccessPosture(summary),
                "websiteAccessPosture",
            );
            renderPresetButtonState(
                websiteAccessHandlerButtons,
                resolveWebsiteHandlersPreset(summary),
                "websiteAccessHandlers",
            );
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
                websitePanelPreference === null ? (summary.blockedSites + summary.exceptionSites + handlerRules > 0) : websitePanelPreference,
                showFineTuning,
                hideFineTuning,
            );
        }

        function renderStepSevenAiExperience(parsed) {
            const summary = getStepSixSummaryData(parsed && typeof parsed === "object" ? parsed : {});
            const releaseAiAvailable = isReleaseAiWizardAvailable();
            const aiFragments = [];

            if (wizardAiEsrcEmptyStateEl) {
                wizardAiEsrcEmptyStateEl.hidden = releaseAiAvailable;
            }
            if (wizardAiPostureBarEl) {
                wizardAiPostureBarEl.hidden = !releaseAiAvailable;
            }
            if (wizardAiPostureBodyEl) {
                wizardAiPostureBodyEl.hidden = !releaseAiAvailable;
            }
            if (wizardAiPosturePresetsEl) {
                wizardAiPosturePresetsEl.hidden = !releaseAiAvailable;
            }
            if (wizardAiPolicyControlsEl) {
                wizardAiPolicyControlsEl.hidden = !releaseAiAvailable;
            }
            if (wizardAiProvidersHandoffEl) {
                wizardAiProvidersHandoffEl.hidden = !releaseAiAvailable;
            }

            if (!releaseAiAvailable) {
                setText(wizardAiSectionStatusEl, t("profiles.wizard_ai_esr_state"));
                setText(aiProvidersSectionStatusEl, t("profiles.wizard_ai_esr_state"));
                if (wizardAiGovernanceCopyEl) {
                    wizardAiGovernanceCopyEl.textContent = t("profiles.wizard_ai_esr_body");
                }
                renderPresetButtonState(aiPosturePresetButtons, null, "aiPosturePreset");
                return;
            }

            if (summary.aiControlsManaged > 0) {
                aiFragments.push(
                    t("profiles.wizard_ai_section_state_feature_controls")
                        .replace("{count}", String(summary.aiControlsManaged)),
                );
            } else if (summary.generativeAiControls > 0) {
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
            renderPresetButtonState(
                aiPosturePresetButtons,
                resolveAiPosturePreset(summary),
                "aiPosturePreset",
            );
            setText(
                aiProvidersSectionStatusEl,
                t("profiles.wizard_ai_providers_state_empty"),
            );
            if (wizardAiGovernanceCopyEl) {
                const hasManagedAiPosture = summary.aiControlsManaged > 0 || summary.generativeAiControls > 0 || summary.visualSearchManaged;
                wizardAiGovernanceCopyEl.textContent = hasManagedAiPosture
                    ? t("profiles.wizard_ai_controls_active")
                    : t("profiles.wizard_ai_controls_body");
            }
        }

        function isAiPolicyUnsupported(policyCardEl) {
            const cardEl = policyCardEl?.matches?.("[data-schema-policy-card]")
                ? policyCardEl
                : policyCardEl?.querySelector("[data-schema-policy-card]");
            return cardEl?.dataset?.schemaPolicyKind === "unsupported";
        }

        function applyAiPosturePreset(presetKey) {
            if (presetKey === "providers") {
                revealAiProvidersTarget("providers");
                return;
            }

            const editor = getEditor();
            if (!editor) return;

            if (presetKey !== "defaults" && !hasUsableAiControlsCard() && !hasUsableGenerativeAiCard()) {
                revealAiTarget(presetKey === "mixed" ? "mixed" : "availability");
                setStatus(t("profiles.wizard_ai_policy_unavailable"), "info");
                return;
            }

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};

                // Reflect the chosen posture immediately so the guided step reacts
                // even before the editor round-trip finishes.
                renderPresetButtonState(aiPosturePresetButtons, presetKey, "aiPosturePreset");

                if (presetKey === "defaults") {
                    delete normalized.AIControls;
                    delete normalized.GenerativeAI;
                    delete normalized.VisualSearchEnabled;
                } else {
                    if (hasUsableAiControlsCard()) {
                        normalized.AIControls = buildAiControlsValue(presetKey);
                        delete normalized.GenerativeAI;
                    } else if (hasUsableGenerativeAiCard()) {
                        normalized.GenerativeAI = buildLegacyGenerativeAiValue(presetKey);
                    }

                    if (presetKey === "disable" || presetKey === "mixed") {
                        normalized.VisualSearchEnabled = false;
                    } else if (presetKey === "availability") {
                        delete normalized.VisualSearchEnabled;
                    }
                }

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                renderStepSixExperience(normalized);
                renderStepSevenAiExperience(normalized);
                updateWizardSummary();
                setStatus(t("profiles.wizard_ai_applied"), "info");
                if (presetKey !== "defaults") {
                    revealAiTarget(presetKey === "mixed" ? "mixed" : "availability");
                }
            } catch (e) {
                setStatus(t("profiles.error_wizard_policy").replace("{detail}", e.message || e), "error");
            }
        }

        function revealAiTarget(kind) {
            let targetEl = null;
            if (kind === "availability" || kind === "disable") {
                targetEl = wizardAiControlsCardEl
                    || wizardGenerativeAiCardEl;
            } else if (kind === "providers") {
                revealAiProvidersTarget("providers");
                return;
            } else if (kind === "surfaces") {
                targetEl = wizardVisualSearchEnabledCardEl;
            } else if (kind === "mixed") {
                targetEl = wizardAiControlsCardEl
                    || wizardGenerativeAiCardEl
                    || wizardVisualSearchEnabledCardEl;
            }
            if (!targetEl) return;
            targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
            targetEl.classList.add("settings-target-highlight");
            window.setTimeout(() => {
                targetEl.classList.remove("settings-target-highlight");
            }, 1800);
            focusTargetForA11y(targetEl);
        }

        function revealAiProvidersTarget(kind) {
            const targetEl = document.getElementById("wizard-ai-providers-section-status");
            if (kind === "providers" || kind === "mixed") {
                wizardAiProvidersOpenAdvancedEl?.click();
                return;
            }
            if (!targetEl) return;
            targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
            targetEl.classList.add("settings-target-highlight");
            window.setTimeout(() => {
                targetEl.classList.remove("settings-target-highlight");
            }, 1800);
            focusTargetForA11y(targetEl);
        }

        function toggleSectionPanel(panelKey) {
            if (panelKey === "sync") {
                syncPanelPreference = !(wizardSyncFineTuningPanelEl?.hidden === false);
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
            if (
                !wizardExtensionDefaultModeEl
                || !wizardExtensionInstallEl
                || !wizardExtensionLockedEl
                || !wizardExtensionUninstallEl
            ) {
                return;
            }
            extensionFineTuningPanelPreference = null;
            extensionInstallPanelPreference = null;
            extensionLockedPanelPreference = null;
            extensionUninstallPanelPreference = null;
            curatedPanelPreference = null;
            syncPanelPreference = null;
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
            managedExtensionFields.filter(Boolean).forEach((input) => {
                input.addEventListener("input", applyExtensionsFromWizard);
                input.addEventListener("change", applyExtensionsFromWizard);
            });
            [
                wizardExtensionDefaultModeEl,
                wizardExtensionInstallEl,
                wizardExtensionLockedEl,
                wizardExtensionUninstallEl,
            ].filter(Boolean).forEach((input) => {
                input.addEventListener("input", applyExtensionsFromWizard);
                input.addEventListener("change", applyExtensionsFromWizard);
            });
            if (wizardExtensionCuratedToggleEl) {
                wizardExtensionCuratedToggleEl.addEventListener("click", () => {
                    toggleCuratedPanel();
                });
            }
            if (wizardExtensionInstallToggleEl) {
                wizardExtensionInstallToggleEl.addEventListener("click", () => {
                    extensionInstallPanelPreference = !(wizardExtensionInstallPanelEl?.hidden === false);
                    renderManagedExtensionProfileStatuses();
                });
            }
            if (wizardExtensionLockedToggleEl) {
                wizardExtensionLockedToggleEl.addEventListener("click", () => {
                    extensionLockedPanelPreference = !(wizardExtensionLockedPanelEl?.hidden === false);
                    renderManagedExtensionProfileStatuses();
                });
            }
            if (wizardExtensionUninstallToggleEl) {
                wizardExtensionUninstallToggleEl.addEventListener("click", () => {
                    extensionUninstallPanelPreference = !(wizardExtensionUninstallPanelEl?.hidden === false);
                    renderManagedExtensionProfileStatuses();
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
            if (wizardSyncFineTuningToggleEl) {
                wizardSyncFineTuningToggleEl.addEventListener("click", () => {
                    toggleSectionPanel("sync");
                });
            }
            if (wizardWebsiteFineTuningToggleEl) {
                wizardWebsiteFineTuningToggleEl.addEventListener("click", () => {
                    toggleSectionPanel("website");
                });
            }
            websiteAccessHandlerButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    applyWebsiteHandlersPreset(button.dataset.websiteAccessHandlers || "defaults");
                    if ((button.dataset.websiteAccessHandlers || "defaults") !== "defaults") {
                        revealHandlersCard();
                    }
                });
            });
            websiteAccessPostureButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    applyWebsiteAccessPosturePreset(button.dataset.websiteAccessPosture || "defaults");
                    if ((button.dataset.websiteAccessPosture || "defaults") !== "defaults") {
                        revealWebsiteFilterCard();
                    }
                });
            });
            syncFocusPresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    revealSyncFocus(button.dataset.syncFocusPreset || "defaults");
                });
            });
            wizardBookmarksOpenAdvancedEl?.addEventListener("click", () => {
                const editor = getEditor();
                if (!editor) {
                    openBookmarksAdvanced("links");
                    return;
                }
                try {
                    const parsed = fromEditorValue(editor.getValue(), document.getElementById("mode").value);
                    const summary = getStepSixSummaryData(parsed && typeof parsed === "object" ? parsed : {});
                    if (summary.bookmarkEntries > 0) {
                        revealBookmarksFocus("links");
                    } else if (summary.managedBookmarkFolders > 0 || summary.nestedBookmarkFolders > 0) {
                        revealBookmarksFocus("folders");
                    } else {
                        openBookmarksAdvanced("links");
                    }
                } catch {
                    openBookmarksAdvanced("links");
                }
            });
            extensionGovernancePresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    const presetKey = button.dataset.extensionGovernancePreset || "open";
                    applyExtensionGovernancePreset(presetKey);
                    if (presetKey === "managed") {
                        revealExtensionArea("rules");
                    } else if (presetKey === "curated") {
                        revealExtensionArea("known");
                    } else if (presetKey === "mixed") {
                        revealExtensionArea("mixed");
                    }
                });
            });
            aiPosturePresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    const presetKey = button.dataset.aiPosturePreset || "defaults";
                    applyAiPosturePreset(presetKey);
                });
            });
            languagePresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    const presetKey = button.dataset.languagePreset || "defaults";
                    applyLanguagePreset(presetKey);
                    if (presetKey === "translation_off") {
                        revealLanguageTarget("translate");
                        return;
                    }
                    revealLanguageTarget("locales");
                });
            });
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
