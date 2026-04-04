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
            wizardExtensionMoreRulesToggleEl,
            wizardExtensionMoreRulesPanelEl,
            wizardExtensionCuratedStatusEl,
            wizardExtensionCuratedToggleEl,
            wizardExtensionCuratedPanelEl,
            wizardSyncSectionStatusEl,
            wizardSyncFineTuningToggleEl,
            wizardSyncFineTuningPanelEl,
            wizardBookmarksSectionStatusEl,
            wizardBookmarksOpenAdvancedEl,
            wizardLanguageSectionStatusEl,
            wizardLanguageGovernanceCopyEl,
            wizardLanguageGovernanceListEl,
            wizardLanguageAiHandoffEl,
            wizardAiSectionStatusEl,
            wizardAiGovernanceCopyEl,
            wizardAiGovernanceListEl,
            wizardAiProvidersOpenAdvancedEl,
            wizardAiSurfacesSectionStatusEl,
            wizardAiFineTuningToggleEl,
            wizardAiFineTuningPanelEl,
            wizardWebsiteSectionStatusEl,
            wizardWebsiteFineTuningToggleEl,
            wizardWebsiteFineTuningPanelEl,
        } = elements;
        let extensionFineTuningPanelPreference = null;
        let extensionMoreRulesPanelPreference = null;
        let extensionInstallPanelPreference = null;
        let extensionLockedPanelPreference = null;
        let extensionUninstallPanelPreference = null;
        let curatedPanelPreference = null;
        const extensionProfileDetailsPreferences = new Map();
        let syncPanelPreference = null;
        let aiPanelPreference = null;
        let websitePanelPreference = null;
        const extensionRolloutPresetButtons = Array.from(document.querySelectorAll("[data-extension-rollout-preset]"));
        const extensionFocusPresetButtons = Array.from(document.querySelectorAll("[data-extension-focus-preset]"));
        const aiFocusPresetButtons = Array.from(document.querySelectorAll("[data-ai-focus-preset]"));
        const aiProvidersPresetButtons = Array.from(document.querySelectorAll("[data-ai-providers-preset]"));
        const syncFocusPresetButtons = Array.from(documentRef.querySelectorAll("[data-sync-focus-preset]"));
        const bookmarksPresetButtons = Array.from(documentRef.querySelectorAll("[data-bookmarks-preset]"));
        const languagePresetButtons = Array.from(documentRef.querySelectorAll("[data-language-preset]"));
        const websiteFilterPresetButtons = Array.from(documentRef.querySelectorAll("[data-website-filter-preset]"));
        const websiteFilterSharedPresetButtons = Array.from(documentRef.querySelectorAll("[data-website-filter-shared-preset]"));
        const websiteHandlersPresetButtons = Array.from(documentRef.querySelectorAll("[data-website-handlers-preset]"));
        const extensionGovernanceCopyEl = document.getElementById("wizard-extension-governance-copy");
        const extensionGovernanceListEl = document.getElementById("wizard-extension-governance-list");
        const extensionGovernanceOpenAdvancedEl = document.getElementById("wizard-extension-governance-open-advanced");
        const websiteGovernanceCopyEl = document.getElementById("wizard-website-governance-copy");
        const websiteGovernanceListEl = document.getElementById("wizard-website-governance-list");
        const websiteGovernanceOpenAdvancedEl = document.getElementById("wizard-website-governance-open-advanced");

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

        function resolveExtensionRolloutPreset({
            defaultMode = "",
            installCount = 0,
            lockedCount = 0,
            uninstallCount = 0,
            configuredCount = 0,
        } = {}) {
            const managedCount = installCount + lockedCount + uninstallCount + configuredCount;
            if (defaultMode === "allowed") return "open";
            if (defaultMode === "blocked" && managedCount > 0) return "managed";
            if (defaultMode === "blocked") return "blocked";
            if (!defaultMode && managedCount === 0) return "defaults";
            return "";
        }

        function applyExtensionRolloutPreset(presetKey) {
            if (!wizardExtensionDefaultModeEl) return;
            if (presetKey === "defaults") {
                wizardExtensionDefaultModeEl.value = "";
            } else if (presetKey === "open") {
                wizardExtensionDefaultModeEl.value = "allowed";
            } else {
                wizardExtensionDefaultModeEl.value = "blocked";
            }

            if (presetKey === "managed") {
                extensionFineTuningPanelPreference = true;
                extensionInstallPanelPreference = true;
                curatedPanelPreference = true;
            }
            applyFromWizard();
        }

        function resolveExtensionFocusPreset({
            installCount = 0,
            lockedCount = 0,
            uninstallCount = 0,
            configuredCount = 0,
        } = {}) {
            const rulesCount = installCount + lockedCount + uninstallCount;
            if (configuredCount > 0 && rulesCount > 0) return "mixed";
            if (configuredCount > 0) return "known";
            if (rulesCount > 0) return "rules";
            return "defaults";
        }

        function countInstallAddonsPermissionEntries(value) {
            const currentObject = value && typeof value === "object" && !Array.isArray(value) ? value : {};
            return Object.keys(currentObject).filter((key) => {
                const entry = currentObject[key];
                return Boolean(key) && hasMeaningfulValue(entry);
            }).length;
        }

        function getExtensionGovernanceSummary(parsed) {
            const normalized = parsed && typeof parsed === "object" ? parsed : {};
            const extensions = normalized.Extensions && typeof normalized.Extensions === "object" ? normalized.Extensions : {};
            const extensionSettings = normalized.ExtensionSettings && typeof normalized.ExtensionSettings === "object"
                ? normalized.ExtensionSettings
                : {};
            const installPermissionCount = countInstallAddonsPermissionEntries(normalized.InstallAddonsPermission);
            const curatedIds = new Set(managedExtensionProfiles.map((profile) => profile.id));
            const defaultSettings = extensionSettings["*"] && typeof extensionSettings["*"] === "object"
                ? extensionSettings["*"]
                : {};

            let arbitraryRules = 0;
            Object.entries(extensionSettings).forEach(([entryKey, entryValue]) => {
                if (!entryValue || typeof entryValue !== "object" || Array.isArray(entryValue) || !Object.keys(entryValue).length) {
                    return;
                }
                if (entryKey !== "*" && !curatedIds.has(entryKey)) {
                    arbitraryRules += 1;
                }
            });

            const curatedCount = managedExtensionProfiles.reduce((count, profile) => {
                const profileSettings = extensionSettings[profile.id];
                return profileSettings && typeof profileSettings === "object" && !Array.isArray(profileSettings) && Object.keys(profileSettings).length
                    ? count + 1
                    : count;
            }, 0);

            return {
                defaultMode: typeof defaultSettings.installation_mode === "string" ? defaultSettings.installation_mode : "",
                installCount: Array.isArray(extensions.Install) ? extensions.Install.length : 0,
                lockedCount: Array.isArray(extensions.Locked) ? extensions.Locked.length : 0,
                uninstallCount: Array.isArray(extensions.Uninstall) ? extensions.Uninstall.length : 0,
                curatedCount,
                installPermissionCount,
                arbitraryRules,
            };
        }

        function renderExtensionGovernanceWorkflow(parsed) {
            if (!extensionGovernanceListEl || !extensionGovernanceCopyEl) return;
            const summary = getExtensionGovernanceSummary(parsed);
            const rolloutCount = summary.installCount + summary.curatedCount;
            const deeperCount = summary.installPermissionCount + summary.arbitraryRules;
            const items = [
                summary.defaultMode
                    ? t("profiles.wizard_extensions_governance_item_posture_ready")
                        .replace("{value}", formatDefaultModeLabel(summary.defaultMode))
                    : t("profiles.wizard_extensions_governance_item_posture_needed"),
                rolloutCount > 0
                    ? t("profiles.wizard_extensions_governance_item_rollout_ready")
                        .replace("{count}", String(rolloutCount))
                    : t("profiles.wizard_extensions_governance_item_rollout_needed"),
                deeperCount > 0
                    ? t("profiles.wizard_extensions_governance_item_deeper_ready")
                        .replace("{count}", String(deeperCount))
                    : t("profiles.wizard_extensions_governance_item_deeper_optional"),
            ];

            extensionGovernanceCopyEl.textContent = summary.defaultMode || rolloutCount > 0 || deeperCount > 0
                ? t("profiles.wizard_extensions_governance_active")
                : t("profiles.wizard_extensions_governance_body");
            extensionGovernanceListEl.innerHTML = "";
            items.forEach((item) => {
                const li = document.createElement("li");
                li.className = "wizard-checklist-item";
                li.textContent = item;
                extensionGovernanceListEl.appendChild(li);
            });
        }

        function openExtensionGovernanceAdvanced() {
            const advancedButton = document.getElementById("workspace-scope-advanced");
            advancedButton?.click();
            window.setTimeout(() => {
                const targetEl = document.getElementById("wizard-install-addons-permission-card")
                    || document.getElementById("wizard-extension-settings-card");
                if (!targetEl) return;
                targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
                targetEl.classList.add("settings-target-highlight");
                window.setTimeout(() => {
                    targetEl.classList.remove("settings-target-highlight");
                }, 1800);
                focusTargetForA11y(targetEl);
            }, 140);
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
                extensionMoreRulesPanelPreference = true;
                setCuratedPanelExpanded(true);
                setPanelExpanded(
                    wizardExtensionMoreRulesPanelEl,
                    wizardExtensionMoreRulesToggleEl,
                    true,
                    t("profiles.wizard_more_rules_show"),
                    t("profiles.wizard_more_rules_hide"),
                );
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
                extensionRolloutPresetButtons,
                resolveExtensionRolloutPreset({
                    defaultMode,
                    installCount,
                    lockedCount,
                    uninstallCount,
                    configuredCount,
                }),
                "extensionRolloutPreset",
            );
            renderPresetButtonState(
                extensionFocusPresetButtons,
                resolveExtensionFocusPreset({
                    installCount,
                    lockedCount,
                    uninstallCount,
                    configuredCount,
                }),
                "extensionFocusPreset",
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
                wizardExtensionMoreRulesPanelEl,
                wizardExtensionMoreRulesToggleEl,
                extensionMoreRulesPanelPreference === null
                    ? (uninstallCount + configuredCount > 0)
                    : extensionMoreRulesPanelPreference,
                t("profiles.wizard_more_rules_show"),
                t("profiles.wizard_more_rules_hide"),
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

        function toggleExtensionMoreRulesPanel() {
            extensionMoreRulesPanelPreference = !(wizardExtensionMoreRulesPanelEl?.hidden === false);
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

        function renderWebsiteGovernanceWorkflow(summary) {
            if (!websiteGovernanceCopyEl || !websiteGovernanceListEl) return;

            const hasSiteRules = summary.blockedSites > 0 || summary.exceptionSites > 0;
            const handlerRules = summary.handlerMimeRules + summary.handlerSchemeRules + summary.handlerExtensionRules;
            const hasManagedWebsitePosture = hasSiteRules || handlerRules > 0 || summary.intranetSingleWordManaged;
            const items = [
                hasSiteRules
                    ? t("profiles.wizard_website_governance_item_sites_ready")
                        .replace("{count}", String(summary.blockedSites + summary.exceptionSites))
                    : (hasManagedWebsitePosture
                        ? t("profiles.wizard_website_governance_item_sites_needed")
                        : t("profiles.wizard_website_governance_item_sites_optional")),
                handlerRules > 0
                    ? t("profiles.wizard_website_governance_item_handlers_ready")
                        .replace("{count}", String(handlerRules))
                    : (hasManagedWebsitePosture
                        ? t("profiles.wizard_website_governance_item_handlers_needed")
                        : t("profiles.wizard_website_governance_item_handlers_optional")),
                summary.intranetSingleWordManaged
                    ? t("profiles.wizard_website_governance_item_intranet_ready")
                    : (hasManagedWebsitePosture
                        ? t("profiles.wizard_website_governance_item_intranet_optional")
                        : t("profiles.wizard_website_governance_item_intranet_later")),
            ];

            websiteGovernanceCopyEl.textContent = hasManagedWebsitePosture
                ? t("profiles.wizard_website_governance_active")
                : t("profiles.wizard_website_governance_body");
            websiteGovernanceListEl.innerHTML = "";
            items.forEach((item) => {
                const li = document.createElement("li");
                li.className = "wizard-checklist-item";
                li.textContent = item;
                websiteGovernanceListEl.appendChild(li);
            });
        }

        function openWebsiteGovernanceAdvanced() {
            const advancedButton = document.getElementById("workspace-scope-advanced");
            advancedButton?.click();
            window.setTimeout(() => {
                const targetEl = document.querySelector('[data-settings-target="policy:GoToIntranetSiteForSingleWordEntryInAddressBar"]')
                    || document.getElementById("wizard-website-filter-card")
                    || document.getElementById("wizard-handlers-card");
                if (!targetEl) return;
                targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
                targetEl.classList.add("settings-target-highlight");
                window.setTimeout(() => {
                    targetEl.classList.remove("settings-target-highlight");
                }, 1800);
                focusTargetForA11y(targetEl);
            }, 140);
        }

        function resolveWebsiteHandlersPreset(summary) {
            const fileRules = summary.handlerMimeRules + summary.handlerExtensionRules;
            const protocolRules = summary.handlerSchemeRules;

            if (fileRules > 0 && protocolRules > 0) return "both";
            if (fileRules > 0) return "files";
            if (protocolRules > 0) return "protocols";
            return "defaults";
        }

        function resolveWebsiteFilterPreset(summary) {
            if (summary.blockedSites > 0 && summary.exceptionSites > 0) return "mixed";
            if (summary.blockedSites > 0) return "blocked";
            if (summary.exceptionSites > 0) return "exceptions";
            return "defaults";
        }

        function resolveSyncFocusPreset(summary) {
            if (summary.accountsManaged && summary.userMessagingControls > 0) return "managed";
            if (summary.userMessagingControls > 0) return "guidance";
            if (summary.accountsManaged) return "accounts";
            return "defaults";
        }

        function resolveBookmarksPreset(summary) {
            if (summary.bookmarkEntries > 0 && summary.managedBookmarkFolders > 0) return "mixed";
            if (summary.bookmarkEntries > 0) return "links";
            if (summary.managedBookmarkFolders > 0 || summary.nestedBookmarkFolders > 0) return "folders";
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

        function renderLanguageGovernanceWorkflow(summary) {
            if (!wizardLanguageGovernanceCopyEl || !wizardLanguageGovernanceListEl) return;

            const hasManagedLanguagePosture = summary.requestedLocales > 0 || summary.translateManaged;
            const hasCoordinatedLanguageMix = summary.requestedLocales > 0 && summary.translateManaged;
            const items = [
                summary.requestedLocales > 0
                    ? t("profiles.wizard_language_governance_item_locales_ready")
                        .replace("{count}", String(summary.requestedLocales))
                    : (hasManagedLanguagePosture
                        ? t("profiles.wizard_language_governance_item_locales_needed")
                        : t("profiles.wizard_language_governance_item_locales_optional")),
                summary.translateManaged
                    ? (
                        summary.translateEnabled
                            ? t("profiles.wizard_language_governance_item_translation_enabled")
                            : t("profiles.wizard_language_governance_item_translation_disabled")
                    )
                    : (hasManagedLanguagePosture
                        ? t("profiles.wizard_language_governance_item_translation_needed")
                        : t("profiles.wizard_language_governance_item_translation_optional")),
                hasCoordinatedLanguageMix
                    ? t("profiles.wizard_language_governance_item_mix_ready")
                    : (hasManagedLanguagePosture
                        ? t("profiles.wizard_language_governance_item_mix_optional")
                        : t("profiles.wizard_language_governance_item_mix_later")),
            ];

            wizardLanguageGovernanceCopyEl.textContent = hasManagedLanguagePosture
                ? t("profiles.wizard_language_governance_active")
                : t("profiles.wizard_language_governance_body");
            wizardLanguageGovernanceListEl.innerHTML = "";
            items.forEach((item) => {
                const li = document.createElement("li");
                li.className = "wizard-checklist-item";
                li.textContent = item;
                wizardLanguageGovernanceListEl.appendChild(li);
            });
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
            if (!wizardBookmarksSectionStatusEl) return;
            wizardBookmarksSectionStatusEl.scrollIntoView({ behavior: "smooth", block: "center" });
            focusTargetForA11y(wizardBookmarksSectionStatusEl);
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
            renderPresetButtonState(
                bookmarksPresetButtons,
                resolveBookmarksPreset(summary),
                "bookmarksPreset",
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
            renderLanguageGovernanceWorkflow(summary);

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
                websiteFilterPresetButtons,
                resolveWebsiteFilterPreset(summary),
                "websiteFilterPreset",
            );
            renderPresetButtonState(
                websiteHandlersPresetButtons,
                resolveWebsiteHandlersPreset(summary),
                "websiteHandlersPreset",
            );
            setText(
                wizardWebsiteSectionStatusEl,
                websiteFragments.length
                    ? websiteFragments.join(" • ")
                    : t("profiles.wizard_website_section_state_empty"),
            );
            renderWebsiteGovernanceWorkflow(summary);

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
            const generativeAi = parsed?.GenerativeAI && typeof parsed.GenerativeAI === "object" && !Array.isArray(parsed.GenerativeAI)
                ? parsed.GenerativeAI
                : {};
            const providerLikeKeys = Object.keys(generativeAi).filter((key) => /provider|model|service|engine/i.test(String(key)));
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
            renderPresetButtonState(
                aiFocusPresetButtons,
                summary.generativeAiControls > 0 && summary.visualSearchManaged
                    ? "mixed"
                    : (summary.generativeAiControls > 0 ? "availability" : (summary.visualSearchManaged ? "surfaces" : "defaults")),
                "aiFocusPreset",
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
            renderPresetButtonState(
                aiProvidersPresetButtons,
                providerLikeKeys.length > 0
                    ? (summary.generativeAiControls > providerLikeKeys.length ? "mixed" : "providers")
                    : "defaults",
                "aiProvidersPreset",
            );
            if (wizardAiGovernanceCopyEl && wizardAiGovernanceListEl) {
                const hasManagedAiPosture = summary.generativeAiControls > 0 || summary.visualSearchManaged || providerLikeKeys.length > 0;
                const hasCoordinatedAiMix = (summary.generativeAiControls > 0 && summary.visualSearchManaged)
                    || (providerLikeKeys.length > 0 && (summary.generativeAiControls > providerLikeKeys.length || summary.visualSearchManaged));
                wizardAiGovernanceCopyEl.textContent = hasManagedAiPosture
                    ? t("profiles.wizard_ai_governance_active")
                    : t("profiles.wizard_ai_governance_body");
                wizardAiGovernanceListEl.innerHTML = "";
                [
                    summary.generativeAiControls > 0
                        ? t("profiles.wizard_ai_governance_item_availability_ready").replace("{count}", String(summary.generativeAiControls))
                        : (hasManagedAiPosture
                            ? t("profiles.wizard_ai_governance_item_availability_needed")
                            : t("profiles.wizard_ai_governance_item_availability_optional")),
                    summary.visualSearchManaged
                        ? (summary.visualSearchEnabled
                            ? t("profiles.wizard_ai_governance_item_surfaces_enabled")
                            : t("profiles.wizard_ai_governance_item_surfaces_disabled"))
                        : (hasManagedAiPosture
                            ? t("profiles.wizard_ai_governance_item_surfaces_needed")
                            : t("profiles.wizard_ai_governance_item_surfaces_optional")),
                    providerLikeKeys.length > 0
                        ? t("profiles.wizard_ai_governance_item_provider_handoff_ready").replace("{count}", String(providerLikeKeys.length))
                        : (hasCoordinatedAiMix
                            ? t("profiles.wizard_ai_governance_item_provider_handoff_optional")
                            : t("profiles.wizard_ai_governance_item_provider_handoff_later")),
                ].forEach((item) => {
                    const li = document.createElement("li");
                    li.className = "wizard-checklist-item";
                    li.textContent = item;
                    wizardAiGovernanceListEl.appendChild(li);
                });
            }

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

        function revealAiTarget(kind) {
            if (kind === "surfaces" || kind === "mixed") {
                aiPanelPreference = true;
                setPanelExpanded(
                    wizardAiFineTuningPanelEl,
                    wizardAiFineTuningToggleEl,
                    true,
                    t("profiles.wizard_fine_tuning_show"),
                    t("profiles.wizard_fine_tuning_hide"),
                );
            }

            let targetEl = null;
            if (kind === "availability") {
                targetEl = wizardGenerativeAiCardEl;
            } else if (kind === "surfaces") {
                targetEl = wizardVisualSearchEnabledCardEl
                    || document.getElementById("wizard-ai-surfaces-section-status");
            } else if (kind === "mixed") {
                targetEl = wizardGenerativeAiCardEl
                    || wizardVisualSearchEnabledCardEl
                    || document.getElementById("wizard-ai-surfaces-section-status");
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
                renderExtensionGovernanceWorkflow(normalized);
                renderStepSevenAiExperience(normalized);
            } catch {
                renderStepSixExperience({});
                renderExtensionGovernanceWorkflow({});
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
            extensionInstallPanelPreference = null;
            extensionLockedPanelPreference = null;
            extensionUninstallPanelPreference = null;
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
                renderExtensionGovernanceWorkflow(normalized);
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
            websiteHandlersPresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    revealHandlersCard();
                });
            });
            websiteFilterPresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    if ((button.dataset.websiteFilterPreset || "defaults") !== "defaults") {
                        revealWebsiteFilterCard();
                    }
                });
            });
            websiteFilterSharedPresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    revealWebsiteFilterCard();
                });
            });
            websiteGovernanceOpenAdvancedEl?.addEventListener("click", () => {
                openWebsiteGovernanceAdvanced();
            });
            syncFocusPresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    revealSyncFocus(button.dataset.syncFocusPreset || "defaults");
                });
            });
            bookmarksPresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    revealBookmarksFocus(button.dataset.bookmarksPreset || "defaults");
                });
            });
            wizardBookmarksOpenAdvancedEl?.addEventListener("click", () => {
                const editor = getEditor();
                if (!editor) {
                    revealBookmarksFocus("links");
                    return;
                }
                try {
                    const parsed = fromEditorValue(editor.getValue(), document.getElementById("mode").value);
                    const summary = getStepSixSummaryData(parsed && typeof parsed === "object" ? parsed : {});
                    revealBookmarksFocus(resolveBookmarksPreset(summary));
                } catch {
                    revealBookmarksFocus("links");
                }
            });
            extensionRolloutPresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    applyExtensionRolloutPreset(button.dataset.extensionRolloutPreset || "defaults");
                });
            });
            extensionFocusPresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    const presetKey = button.dataset.extensionFocusPreset || "defaults";
                    if (presetKey !== "defaults") {
                        revealExtensionArea(presetKey);
                    }
                });
            });
            aiFocusPresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    const presetKey = button.dataset.aiFocusPreset || "defaults";
                    if (presetKey !== "defaults") {
                        revealAiTarget(presetKey);
                    }
                });
            });
            aiProvidersPresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    const presetKey = button.dataset.aiProvidersPreset || "defaults";
                    revealAiProvidersTarget(presetKey);
                });
            });
            languagePresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    const presetKey = button.dataset.languagePreset || "defaults";
                    if (presetKey === "translation_off") {
                        revealLanguageTarget("translate");
                        return;
                    }
                    revealLanguageTarget("locales");
                });
            });
            extensionGovernanceOpenAdvancedEl?.addEventListener("click", openExtensionGovernanceAdvanced);
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
