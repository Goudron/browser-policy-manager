    function create({
        documentRef = document,
        elements = {},
        dependencies = {},
        state = {},
    }) {
        const {
            t,
            cloneJsonValue,
            fromEditorValue,
            toEditorValue,
            renderWizardSchemaShell,
            renderAllSettingsList,
            buildWizardSettingsSearchIndex,
            renderWizardSettingsSearchResults,
            currentSnapshotState,
            renderFinalExportStepSummary,
            saveCurrent,
            getBaselineSnapshot,
            setStatus,
        } = dependencies;

        const getEditor = state.getEditor || (() => null);
        const getCurrentId = state.getCurrentId || (() => null);
        const setCurrentRaw = state.setCurrentRaw || (() => { });

        const {
            quickPolicyKeys = [],
            wizardPreferenceSections = [],
        } = state;

        const {
            wizardStepButtons = [],
            wizardPanels = [],
            wizardStepMemoryCopyEl,
            wizardStepMemoryListEl,
            wizardPrevEl,
            wizardNextEl,
            wizardFinishEl,
            wizardProgressTextEl,
            wizardSummaryModeEl,
            wizardSummaryPoliciesEl,
            wizardSummaryExtensionsEl,
            wizardPolicyInputs = [],
            wizardPolicySelectInputs = [],
        } = elements;

        const wizardSteps = wizardStepButtons
            .map((button, index) => {
                const step = Number(button.dataset.step);
                const id = String(button.dataset.stepId || "").trim();
                return Number.isInteger(step) && step > 0 && id
                    ? { step, id, index, button }
                    : null;
            })
            .filter(Boolean);
        const wizardStepByNumber = new Map(wizardSteps.map((step) => [step.step, step]));
        const wizardStepById = new Map(wizardSteps.map((step) => [step.id, step]));
        const wizardTotalSteps = wizardSteps.length;
        let wizardStep = wizardSteps[0]?.step || 1;
        let siteDataFineTuningPreference = null;
        let wizardBaselineSnapshot = null;
        const stepEntrySnapshots = {};
        const recentStepChanges = new Map();
        let recentChangeSequence = 0;
        const stepScopedPolicyKeys = {
            1: [
                "DisableAppUpdate",
                "DisableSystemAddonUpdate",
                "AppAutoUpdate",
                "DontCheckDefaultBrowser",
                "PromptForDownloadLocation",
                "Proxy",
                "WindowsSSO",
                "Authentication",
                "Certificates",
                "DNSOverHTTPS",
                "SearchBar",
                "SearchSuggestEnabled",
                "SearchEngines",
                "FirefoxSuggest",
            ],
            2: [
                "Homepage",
                "NewTabPage",
                "OverrideFirstRunPage",
                "OverridePostUpdatePage",
                "FirefoxHome",
                "WebsiteFilter",
                "AllowedDomainsForApps",
                "HttpAllowlist",
                "LocalFileLinks",
                "Handlers",
                "AutoLaunchProtocolsFromOrigins",
                "GoToIntranetSiteForSingleWordEntryInAddressBar",
                "Bookmarks",
                "ManagedBookmarks",
                "NoDefaultBookmarks",
            ],
            3: [
                "DisableTelemetry",
                "DisableFirefoxStudies",
                "DisablePrivateBrowsing",
                "OfferToSaveLogins",
                "PasswordManagerEnabled",
                "BlockAboutConfig",
                "BlockAboutProfiles",
                "DisableDeveloperTools",
                "DisableBuiltinPDFViewer",
                "HttpsOnlyMode",
                "SanitizeOnShutdown",
                "Permissions",
                "Cookies",
                "IPProtectionAvailable",
                "LocalNetworkAccess",
                "XSLTEnabled",
            ],
            5: [
                "DisableFirefoxAccounts",
                "UserMessaging",
                "RequestedLocales",
                "TranslateEnabled",
            ],
            6: [
                "Extensions",
                "ExtensionSettings",
                "ExtensionUpdate",
                "InstallAddonsPermission",
            ],
            7: [
                "AIControls",
                "GenerativeAI",
                "VisualSearchEnabled",
            ],
        };
        const stepPreferenceSections = {
            1: ["general", "search"],
            2: ["home"],
            3: ["privacy"],
            5: ["sync"],
        };

        const privacyManagedPolicyKeys = [
            "DisableTelemetry",
            "DisableFirefoxStudies",
            "DisablePrivateBrowsing",
            "OfferToSaveLogins",
            "PasswordManagerEnabled",
        ];
        const lockdownManagedPolicyKeys = [
            "BlockAboutConfig",
            "BlockAboutProfiles",
            "DisableDeveloperTools",
            "DisableBuiltinPDFViewer",
            "HttpsOnlyMode",
        ];
        const hardeningManagedPolicyKeys = [
            ...privacyManagedPolicyKeys,
            ...lockdownManagedPolicyKeys,
            "SanitizeOnShutdown",
        ];
        const hardeningPresets = {
            defaults: {},
            balanced: {
                DisableTelemetry: true,
                DisableFirefoxStudies: true,
                BlockAboutConfig: true,
                DisableDeveloperTools: true,
                HttpsOnlyMode: "enabled",
            },
            strict: {
                DisableTelemetry: true,
                DisableFirefoxStudies: true,
                DisablePrivateBrowsing: true,
                OfferToSaveLogins: false,
                PasswordManagerEnabled: false,
                BlockAboutConfig: true,
                BlockAboutProfiles: true,
                DisableDeveloperTools: true,
                DisableBuiltinPDFViewer: true,
                HttpsOnlyMode: "force_enabled",
                SanitizeOnShutdown: {
                    Cache: true,
                    Cookies: true,
                    History: true,
                    Sessions: true,
                    SiteSettings: true,
                },
            },
        };
        const cleanupManagedPolicyKeys = ["SanitizeOnShutdown"];
        const cleanupPresets = {
            defaults: {},
            shared: {
                SanitizeOnShutdown: {
                    Cache: true,
                    Cookies: true,
                    History: true,
                    Sessions: true,
                    SiteSettings: true,
                },
            },
            strict: {
                SanitizeOnShutdown: {
                    Cache: true,
                    Cookies: true,
                    FormData: true,
                    History: true,
                    Sessions: true,
                    SiteSettings: true,
                    Locked: true,
                },
            },
        };
        const siteDataManagedKeys = ["Permissions", "Cookies", "LocalNetworkAccess"];
        const siteDataPresets = {
            defaults: {},
            balanced: {
                Permissions: {
                    Camera: { BlockNewRequests: true },
                    Microphone: { BlockNewRequests: true },
                    Location: { BlockNewRequests: true },
                    Notifications: { BlockNewRequests: true },
                    ScreenShare: { BlockNewRequests: true },
                    VirtualReality: { BlockNewRequests: true },
                },
                Cookies: {
                    Behavior: "reject-foreign",
                },
            },
            strict: {
                Permissions: {
                    Camera: { BlockNewRequests: true, Locked: true },
                    Microphone: { BlockNewRequests: true, Locked: true },
                    Location: { BlockNewRequests: true, Locked: true },
                    Notifications: { BlockNewRequests: true, Locked: true },
                    ScreenShare: { BlockNewRequests: true, Locked: true },
                    VirtualReality: { BlockNewRequests: true, Locked: true },
                    Autoplay: { Default: "block-audio-video", Locked: true },
                },
                Cookies: {
                    Behavior: "reject-tracker-and-partition-foreign",
                    BehaviorPrivateBrowsing: "reject-tracker-and-partition-foreign",
                    Locked: true,
                },
            },
        };
        const aiPosturePresets = {
            defaults: {},
            disable: {
                AIControls: {
                    Default: {
                        Value: "blocked",
                        Locked: true,
                    },
                },
                VisualSearchEnabled: false,
            },
            availability: {
                AIControls: {
                    Default: {
                        Value: "available",
                        Locked: true,
                    },
                },
            },
            mixed: {
                AIControls: {
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
                },
                VisualSearchEnabled: false,
            },
        };

        function getStepActionCopyEl() {
            return documentRef.getElementById("wizard-step-actions-copy");
        }

        function getStepUndoButtonEl() {
            return documentRef.getElementById("wizard-step-undo");
        }

        function getStepResetButtonEl() {
            return documentRef.getElementById("wizard-step-reset");
        }

        function getCurrentMode() {
            return documentRef.getElementById("mode")?.value || "json";
        }

        function getWizardStepMeta(reference) {
            if (typeof reference === "string") {
                const normalizedReference = reference.trim();
                if (!normalizedReference) return null;
                if (wizardStepById.has(normalizedReference)) {
                    return wizardStepById.get(normalizedReference);
                }
                const number = Number(normalizedReference);
                return Number.isInteger(number) ? wizardStepByNumber.get(number) || null : null;
            }
            const number = Number(reference);
            return Number.isInteger(number) ? wizardStepByNumber.get(number) || null : null;
        }

        function getWizardPanel(stepMeta) {
            if (!stepMeta) return null;
            return wizardPanels.find((panel) => panel.dataset.wizardStepId === stepMeta.id)
                || documentRef.getElementById(`wizard-step-${stepMeta.step}`)
                || null;
        }

        function getAdjacentWizardStep(offset) {
            const currentMeta = getWizardStepMeta(wizardStep);
            if (!currentMeta) return null;
            return wizardSteps[currentMeta.index + Number(offset)]?.step || null;
        }

        function getWizardStepFromLocation() {
            const windowRef = documentRef.defaultView;
            if (!windowRef?.location || wizardSteps.length === 0) return null;
            let locationUrl;
            try {
                locationUrl = new URL(windowRef.location.href);
            } catch {
                return null;
            }

            const currentStep = getWizardStepMeta(locationUrl.searchParams.get("step") || "");
            if (currentStep) return currentStep.step;

            const legacyStep = Number(locationUrl.searchParams.get("legacy_step") || "");
            const legacyStepMap = new Map([
                [1, "browser_network_search"],
                [2, "browser_network_search"],
                [3, "security_privacy"],
                [4, "users_language_sync"],
                [5, "ai"],
                [6, "review_export"],
            ]);
            const mappedLegacyStep = getWizardStepMeta(legacyStepMap.get(legacyStep) || "");
            if (mappedLegacyStep) return mappedLegacyStep.step;

            const hash = String(locationUrl.hash || "").replace(/^#/, "");
            const hashStep = getWizardStepMeta(hash.replace(/^wizard-step-/, ""));
            return hashStep?.step || null;
        }

        function syncWizardStepLocation(stepMeta, historyMode = "push") {
            if (!stepMeta || historyMode === "none") return;
            const windowRef = documentRef.defaultView;
            if (
                !windowRef?.history
                || !windowRef?.location
                || documentRef.body?.dataset.profilesRouteMode !== "edit"
            ) return;
            let locationUrl;
            try {
                locationUrl = new URL(windowRef.location.href);
            } catch {
                return;
            }
            if (locationUrl.searchParams.get("step") === stepMeta.id && !locationUrl.searchParams.has("legacy_step")) {
                return;
            }
            locationUrl.searchParams.set("step", stepMeta.id);
            locationUrl.searchParams.delete("legacy_step");
            const nextPath = `${locationUrl.pathname}${locationUrl.search}${locationUrl.hash}`;
            const historyMethod = historyMode === "replace" ? "replaceState" : "pushState";
            windowRef.history[historyMethod]?.({ bpmWizardStep: stepMeta.id }, "", nextPath);
        }

        function getWizardStepLabel(stepNumber) {
            const stepMeta = getWizardStepMeta(stepNumber);
            return stepMeta?.button
                ?.querySelector(".wizard-step-label")
                ?.textContent
                ?.trim() || `Step ${stepMeta?.step || ""}`;
        }

        function getRecentChangeSummary(stepNumber) {
            const summaryMap = {
                1: t("profiles.wizard_step_memory_step_browser"),
                3: t("profiles.wizard_step_memory_step_privacy"),
                5: t("profiles.wizard_step_memory_step_features"),
                7: t("profiles.wizard_step_memory_step_ai"),
            };
            return summaryMap[Number(stepNumber)] || t("profiles.wizard_step_memory_step_generic");
        }

        function captureWizardUiSnapshot() {
            const editor = getEditor();
            if (!editor) return null;
            try {
                return {
                    flags: cloneJsonValue(fromEditorValue(editor.getValue(), getCurrentMode()), {}),
                };
            } catch {
                return null;
            }
        }

        function parseBaselineProfileSnapshot() {
            const stored = getBaselineSnapshot?.();
            if (!stored) return null;
            try {
                const parsed = JSON.parse(stored);
                return {
                    flags: cloneJsonValue(parsed.flags, {}),
                };
            } catch {
                return null;
            }
        }

        function getStepScope(stepNumber) {
            const stepMeta = getWizardStepMeta(stepNumber);
            if (!stepMeta || stepMeta.index === wizardSteps.length - 1) return { readOnly: true };
            return {
                policyKeys: stepScopedPolicyKeys[stepMeta.step] || [],
                preferenceSections: stepPreferenceSections[stepMeta.step] || [],
            };
        }

        function collectPreferencePrefixes(sectionIds = []) {
            return wizardPreferenceSections
                .filter((section) => sectionIds.includes(section.id))
                .flatMap((section) => Array.isArray(section.prefixes) ? section.prefixes : [])
                .filter((prefix) => typeof prefix === "string" && prefix.trim());
        }

        function preferenceBelongsToSections(prefName, sectionIds = []) {
            const normalizedName = String(prefName || "").trim();
            if (!normalizedName) return false;
            return collectPreferencePrefixes(sectionIds).some((prefix) =>
                normalizedName === prefix || normalizedName.startsWith(prefix)
            );
        }

        function extractStepSnapshotSubset(snapshot, stepNumber) {
            if (!snapshot) return null;
            const scope = getStepScope(stepNumber);
            if (scope.full) {
                return {
                    form: snapshot.form || {},
                    flags: snapshot.flags || {},
                };
            }
            if (scope.readOnly) return { readOnly: true };

            const subset = {
                form: {},
                flags: {},
            };
            const flags = snapshot.flags && typeof snapshot.flags === "object" ? snapshot.flags : {};
            scope.policyKeys.forEach((key) => {
                if (Object.prototype.hasOwnProperty.call(flags, key)) {
                    subset.flags[key] = cloneJsonValue(flags[key], flags[key]);
                }
            });

            const preferences = flags.Preferences && typeof flags.Preferences === "object" && !Array.isArray(flags.Preferences)
                ? flags.Preferences
                : {};
            const scopedPreferences = Object.fromEntries(
                Object.entries(preferences).filter(([prefName]) => preferenceBelongsToSections(prefName, scope.preferenceSections)),
            );
            if (Object.keys(scopedPreferences).length) {
                subset.flags.Preferences = cloneJsonValue(scopedPreferences, scopedPreferences);
            }
            return subset;
        }

        function snapshotsDifferForStep(left, right, stepNumber) {
            return JSON.stringify(normalizeForCompare(extractStepSnapshotSubset(left, stepNumber)))
                !== JSON.stringify(normalizeForCompare(extractStepSnapshotSubset(right, stepNumber)));
        }

        function applyScopedPreferences(targetFlags, sourceFlags, sectionIds = []) {
            const targetPreferences = targetFlags.Preferences && typeof targetFlags.Preferences === "object" && !Array.isArray(targetFlags.Preferences)
                ? { ...targetFlags.Preferences }
                : {};
            const sourcePreferences = sourceFlags.Preferences && typeof sourceFlags.Preferences === "object" && !Array.isArray(sourceFlags.Preferences)
                ? sourceFlags.Preferences
                : {};

            Object.keys(targetPreferences).forEach((prefName) => {
                if (preferenceBelongsToSections(prefName, sectionIds)) {
                    delete targetPreferences[prefName];
                }
            });
            Object.entries(sourcePreferences).forEach(([prefName, value]) => {
                if (preferenceBelongsToSections(prefName, sectionIds)) {
                    targetPreferences[prefName] = cloneJsonValue(value, value);
                }
            });

            if (Object.keys(targetPreferences).length) {
                targetFlags.Preferences = targetPreferences;
            } else {
                delete targetFlags.Preferences;
            }
        }

        function buildRestoredSnapshotForStep(sourceSnapshot, stepNumber) {
            const currentSnapshot = captureWizardUiSnapshot();
            if (!sourceSnapshot || !currentSnapshot) return null;

            const scope = getStepScope(stepNumber);
            if (scope.readOnly) return null;
            if (scope.full) {
                return {
                    form: {
                        ...currentSnapshot.form,
                        ...(sourceSnapshot.form || {}),
                    },
                    flags: cloneJsonValue(sourceSnapshot.flags, {}),
                };
            }

            const nextFlags = cloneJsonValue(currentSnapshot.flags, {});
            const sourceFlags = sourceSnapshot.flags && typeof sourceSnapshot.flags === "object" ? sourceSnapshot.flags : {};

            scope.policyKeys.forEach((key) => {
                if (Object.prototype.hasOwnProperty.call(sourceFlags, key)) {
                    nextFlags[key] = cloneJsonValue(sourceFlags[key], sourceFlags[key]);
                } else {
                    delete nextFlags[key];
                }
            });
            applyScopedPreferences(nextFlags, sourceFlags, scope.preferenceSections);

            return {
                form: { ...currentSnapshot.form },
                flags: nextFlags,
            };
        }

        function captureStepEntrySnapshot(stepNumber = wizardStep) {
            const snapshot = captureWizardUiSnapshot();
            if (!snapshot) return;
            stepEntrySnapshots[Number(stepNumber)] = snapshot;
        }

        function applyWizardUiSnapshot(snapshot, stepNumber) {
            const editor = getEditor();
            if (!editor || !snapshot) return false;

            setCurrentRaw(cloneJsonValue(snapshot.flags, {}));
            editor.setValue(toEditorValue(snapshot.flags, getCurrentMode()));
            syncWizardFieldsFromForm();
            captureStepEntrySnapshot(stepNumber);
            return true;
        }

        function markWizardBaselineSnapshot() {
            wizardBaselineSnapshot = captureWizardUiSnapshot();
            captureStepEntrySnapshot(wizardStep);
            renderCurrentStepActions();
        }

        function renderRecentStepMemory() {
            if (!wizardStepMemoryCopyEl || !wizardStepMemoryListEl) return;

            const baselineSnapshot = wizardBaselineSnapshot || parseBaselineProfileSnapshot();
            const currentSnapshot = captureWizardUiSnapshot();
            if (baselineSnapshot && currentSnapshot) {
                wizardSteps.slice(0, -1).forEach(({ step: stepNumber }) => {
                        const changed = snapshotsDifferForStep(currentSnapshot, baselineSnapshot, stepNumber);
                        if (changed) {
                            const existing = recentStepChanges.get(stepNumber);
                            recentStepChanges.set(stepNumber, {
                                step: stepNumber,
                                title: getWizardStepLabel(stepNumber),
                                summary: getRecentChangeSummary(stepNumber),
                                sequence: existing?.sequence || (++recentChangeSequence),
                            });
                        } else {
                            recentStepChanges.delete(stepNumber);
                        }
                    });
            } else {
                recentStepChanges.clear();
            }

            const items = Array.from(recentStepChanges.values())
                .sort((left, right) => right.sequence - left.sequence)
                .slice(0, 4);

            wizardStepMemoryCopyEl.textContent = items.length
                ? t("profiles.wizard_step_memory_active")
                : t("profiles.wizard_step_memory_empty");
            wizardStepMemoryListEl.innerHTML = items
                .map((item) => {
                    const isCurrentStep = Number(item.step) === Number(wizardStep);
                    const actionLabel = isCurrentStep
                        ? t("profiles.wizard_step_memory_current")
                        : t("profiles.wizard_step_memory_open");
                    const stepTarget = getWizardStepId(item.step) || String(item.step);
                    return `<div class="wizard-step-memory-item" data-step-memory-state="${isCurrentStep ? "current" : "recent"}"><div class="wizard-step-memory-item-main"><div class="wizard-step-memory-item-title">${item.title}</div><div class="wizard-step-memory-item-copy">${item.summary}</div></div><button type="button" class="button-base ghost-button wizard-step-memory-action" data-step-memory-jump="${stepTarget}"${isCurrentStep ? " disabled" : ""}>${actionLabel}</button></div>`;
                })
                .join("");
        }

        function renderCurrentStepActions() {
            const copyEl = getStepActionCopyEl();
            const undoButtonEl = getStepUndoButtonEl();
            const resetButtonEl = getStepResetButtonEl();
            if (!copyEl || !undoButtonEl || !resetButtonEl) return;

            const scope = getStepScope(wizardStep);
            const currentSnapshot = captureWizardUiSnapshot();
            const entrySnapshot = stepEntrySnapshots[wizardStep] || null;
            const baselineSnapshot = wizardBaselineSnapshot || parseBaselineProfileSnapshot();

            let copyKey = "profiles.wizard_step_actions_clean";
            let copyValue = t(copyKey);
            let tone = "default";
            let canUndo = false;
            let canReset = false;

            if (scope.readOnly) {
                copyKey = "profiles.wizard_step_actions_read_only";
                copyValue = t(copyKey);
            } else if (!currentSnapshot) {
                copyKey = "profiles.wizard_step_actions_invalid";
                copyValue = t(copyKey);
                tone = "attention";
            } else {
                canUndo = Boolean(entrySnapshot) && snapshotsDifferForStep(currentSnapshot, entrySnapshot, wizardStep);
                canReset = Boolean(baselineSnapshot) && snapshotsDifferForStep(currentSnapshot, baselineSnapshot, wizardStep);

                if (canUndo && canReset) {
                    copyKey = "profiles.wizard_step_actions_both";
                    copyValue = t(copyKey);
                    tone = "active";
                } else if (canUndo) {
                    copyKey = "profiles.wizard_step_actions_undo_only";
                    copyValue = t(copyKey);
                    tone = "active";
                } else if (canReset) {
                    copyKey = "profiles.wizard_step_actions_reset_only";
                    copyValue = t(copyKey);
                    tone = "active";
                }
            }

            copyEl.textContent = copyValue;
            copyEl.setAttribute("data-i18n", copyKey);
            copyEl.dataset.stepActionTone = tone;
            undoButtonEl.disabled = !canUndo;
            resetButtonEl.disabled = !canReset;
            renderRecentStepMemory();
        }

        function undoCurrentStepChanges() {
            const restoredSnapshot = buildRestoredSnapshotForStep(stepEntrySnapshots[wizardStep] || null, wizardStep);
            if (!restoredSnapshot) {
                renderCurrentStepActions();
                return;
            }
            applyWizardUiSnapshot(restoredSnapshot, wizardStep);
            setStatus(t("profiles.wizard_step_undo_done"), "success");
        }

        function resetCurrentStepToBaseline() {
            const sourceSnapshot = wizardBaselineSnapshot || parseBaselineProfileSnapshot();
            const restoredSnapshot = buildRestoredSnapshotForStep(sourceSnapshot, wizardStep);
            if (!restoredSnapshot) {
                renderCurrentStepActions();
                return;
            }
            applyWizardUiSnapshot(restoredSnapshot, wizardStep);
            setStatus(t("profiles.wizard_step_reset_done"), "success");
        }

        function setPanelExpanded(panelEl, toggleEl, expanded) {
            if (panelEl) {
                panelEl.hidden = !expanded;
            }
            if (toggleEl) {
                toggleEl.setAttribute("aria-expanded", expanded ? "true" : "false");
                toggleEl.textContent = expanded ? t("profiles.wizard_fine_tuning_hide") : t("profiles.wizard_fine_tuning_show");
            }
        }

        function hasMeaningfulValue(value) {
            if (typeof value === "boolean" || typeof value === "number") return true;
            if (typeof value === "string") return value.trim().length > 0;
            if (Array.isArray(value)) return value.some((entry) => hasMeaningfulValue(entry));
            if (value && typeof value === "object") return Object.values(value).some((entry) => hasMeaningfulValue(entry));
            return false;
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

        function countConfiguredObjectEntries(value) {
            if (!value || typeof value !== "object" || Array.isArray(value)) return 0;
            return Object.values(value).filter((entry) => hasMeaningfulValue(entry)).length;
        }

        function matchesPolicyPreset(current, managedKeys, presetValues) {
            return managedKeys.every((key) => {
                if (Object.prototype.hasOwnProperty.call(presetValues, key)) {
                    return valuesEqual(current[key], presetValues[key]);
                }
                return current[key] === undefined;
            });
        }

        function renderPresetButtonState(buttons, activeKey) {
            buttons.forEach((button) => {
                const isActive = button.dataset.privacyPreset === activeKey
                    || button.dataset.lockdownPreset === activeKey
                    || button.dataset.siteDataPreset === activeKey
                    || button.dataset.hardeningPreset === activeKey
                    || button.dataset.cleanupPreset === activeKey
                    || button.dataset.aiPosturePreset === activeKey;
                button.classList.toggle("wizard-search-engine-preset--applied", isActive);
                button.classList.toggle("wizard-search-engine-preset--partial", false);
                button.classList.toggle("wizard-search-engine-preset--conflict", false);
                button.setAttribute("aria-pressed", isActive ? "true" : "false");
            });
        }

        function buildAiControlsValue(presetKey) {
            return cloneJsonValue(aiPosturePresets[presetKey]?.AIControls, null);
        }

        function buildGenerativeAiValue(presetKey) {
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

        function isAiPolicyUnsupported(policyCardId) {
            const policyCardEl = documentRef.getElementById(policyCardId);
            const cardEl = policyCardEl?.matches?.("[data-schema-policy-card]")
                ? policyCardEl
                : policyCardEl?.querySelector?.("[data-schema-policy-card]");
            return cardEl?.dataset?.schemaPolicyKind === "unsupported";
        }

        function hasUsableAiControlsCard() {
            return !isAiPolicyUnsupported("wizard-ai-controls-card");
        }

        function hasUsableGenerativeAiCard() {
            return !isAiPolicyUnsupported("wizard-generative-ai-card");
        }

        function summarizeAiPosture(parsed = {}) {
            const aiControls = parsed?.AIControls && typeof parsed.AIControls === "object" && !Array.isArray(parsed.AIControls)
                ? parsed.AIControls
                : {};
            const generativeAi = parsed?.GenerativeAI && typeof parsed.GenerativeAI === "object" && !Array.isArray(parsed.GenerativeAI)
                ? parsed.GenerativeAI
                : {};
            const defaultControl = aiControls.Default && typeof aiControls.Default === "object" && !Array.isArray(aiControls.Default)
                ? aiControls.Default
                : {};
            return {
                aiControlsManaged: countConfiguredObjectEntries(aiControls),
                generativeAiControls: countConfiguredObjectEntries(generativeAi),
                aiDefaultBlocked: defaultControl.Value === "blocked",
                visualSearchManaged: typeof parsed?.VisualSearchEnabled === "boolean",
                visualSearchEnabled: parsed?.VisualSearchEnabled === true,
            };
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

        function syncAiPresetUi(parsed = {}) {
            const aiButtons = Array.from(documentRef.querySelectorAll("[data-ai-posture-preset]"));
            const aiStatusEl = documentRef.getElementById("wizard-ai-section-status");
            const aiGovernanceCopyEl = documentRef.getElementById("wizard-ai-governance-copy");
            const summary = summarizeAiPosture(parsed);
            const activePreset = resolveAiPosturePreset(summary);
            const aiFragments = [];

            renderPresetButtonState(aiButtons, activePreset);

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

            if (aiStatusEl) {
                aiStatusEl.textContent = aiFragments.length
                    ? aiFragments.join(" • ")
                    : t("profiles.wizard_ai_section_state_empty");
            }
            if (aiGovernanceCopyEl) {
                const hasManagedAiPosture = summary.aiControlsManaged > 0 || summary.generativeAiControls > 0 || summary.visualSearchManaged;
                aiGovernanceCopyEl.textContent = hasManagedAiPosture
                    ? t("profiles.wizard_ai_controls_active")
                    : t("profiles.wizard_ai_controls_body");
            }
        }

        function applyAiPosturePreset(presetKey) {
            const editor = getEditor();
            if (!editor) return;

            if (presetKey !== "defaults" && !hasUsableAiControlsCard() && !hasUsableGenerativeAiCard()) {
                setStatus(t("profiles.wizard_ai_policy_unavailable"), "info");
                return;
            }

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};

                delete normalized.AIControls;
                delete normalized.GenerativeAI;
                delete normalized.VisualSearchEnabled;

                if (presetKey !== "defaults") {
                    if (hasUsableAiControlsCard()) {
                        normalized.AIControls = buildAiControlsValue(presetKey);
                    } else if (hasUsableGenerativeAiCard()) {
                        normalized.GenerativeAI = buildGenerativeAiValue(presetKey);
                    }

                    if (presetKey === "disable" || presetKey === "mixed") {
                        normalized.VisualSearchEnabled = false;
                    }
                }

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                syncAiPresetUi(normalized);
                updateWizardSummary();
                setStatus(t("profiles.wizard_ai_applied"), "info");
            } catch (e) {
                setStatus(t("profiles.error_wizard_policy").replace("{detail}", e.message || e), "error");
            }
        }

        function syncHardeningPresetUi(parsed = {}) {
            const hardeningButtons = Array.from(documentRef.querySelectorAll("[data-hardening-preset]"));
            const statusEl = documentRef.getElementById("wizard-hardening-section-status");
            const activePreset = Object.entries(hardeningPresets).find(([, presetValues]) =>
                matchesPolicyPreset(parsed, hardeningManagedPolicyKeys, presetValues)
            )?.[0] || "";
            const customConfig = hardeningManagedPolicyKeys.some((key) => hasMeaningfulValue(parsed[key])) && !activePreset;

            renderPresetButtonState(hardeningButtons, activePreset);
            if (!statusEl) return;
            if (activePreset === "balanced") {
                statusEl.textContent = t("profiles.wizard_hardening_section_state_balanced");
                return;
            }
            if (activePreset === "strict") {
                statusEl.textContent = t("profiles.wizard_hardening_section_state_strict");
                return;
            }
            if (customConfig) {
                statusEl.textContent = t("profiles.wizard_hardening_section_state_custom");
                return;
            }
            statusEl.textContent = t("profiles.wizard_hardening_section_state_empty");
        }

        function syncCleanupPresetUi(parsed = {}) {
            const cleanupButtons = Array.from(documentRef.querySelectorAll("[data-cleanup-preset]"));
            const statusEl = documentRef.getElementById("wizard-cleanup-section-status");
            const activePreset = Object.entries(cleanupPresets).find(([, presetValues]) =>
                matchesPolicyPreset(parsed, cleanupManagedPolicyKeys, presetValues)
            )?.[0] || "";
            const hasCustomConfig = cleanupManagedPolicyKeys.some((key) => hasMeaningfulValue(parsed[key])) && !activePreset;

            renderPresetButtonState(cleanupButtons, activePreset);
            if (!statusEl) return;
            if (activePreset === "shared") {
                statusEl.textContent = t("profiles.wizard_cleanup_section_state_shared");
                return;
            }
            if (activePreset === "strict") {
                statusEl.textContent = t("profiles.wizard_cleanup_section_state_strict");
                return;
            }
            if (hasCustomConfig) {
                statusEl.textContent = t("profiles.wizard_cleanup_section_state_custom");
                return;
            }
            statusEl.textContent = t("profiles.wizard_cleanup_section_state_empty");
        }

        function syncSiteDataPresetUi(parsed = {}) {
            const siteDataButtons = Array.from(documentRef.querySelectorAll("[data-site-data-preset]"));
            const panelEl = documentRef.getElementById("wizard-site-data-fine-tuning-panel");
            const toggleEl = documentRef.getElementById("wizard-site-data-fine-tuning-toggle");

            const activePreset = Object.entries(siteDataPresets).find(([, presetValues]) =>
                matchesPolicyPreset(parsed, siteDataManagedKeys, presetValues)
            )?.[0] || "";

            renderPresetButtonState(siteDataButtons, activePreset);

            const hasCustomConfig = siteDataManagedKeys.some((key) => hasMeaningfulValue(parsed[key])) && !activePreset;
            setPanelExpanded(
                panelEl,
                toggleEl,
                siteDataFineTuningPreference === null ? hasCustomConfig : siteDataFineTuningPreference,
            );
        }


        function syncWizardFieldsFromForm() {
            renderWizardSchemaShell();
            renderAllSettingsList();
            buildWizardSettingsSearchIndex();
            renderWizardSettingsSearchResults();
        }

        function resolveQuickPolicyEnabledValue() {
            return true;
        }

        function updateWizardSummary() {
            const mode = documentRef.getElementById("mode").value || "json";
            let enabledQuickPolicies = 0;
            let managedExtensions = 0;
            const editor = getEditor();

            if (editor) {
                try {
                    const parsed = fromEditorValue(editor.getValue(), mode);
                    if (parsed && typeof parsed === "object") {
                        enabledQuickPolicies = quickPolicyKeys.filter((key) => parsed[key] !== undefined).length;
                        const extensionSettings = parsed.ExtensionSettings && typeof parsed.ExtensionSettings === "object"
                            ? parsed.ExtensionSettings
                            : {};
                        const explicitProfiles = Object.entries(extensionSettings)
                            .filter(([profileId, settings]) =>
                                profileId !== "*"
                                && settings
                                && typeof settings === "object"
                                && !Array.isArray(settings)
                                && Object.keys(settings).length > 0
                            )
                            .length;
                        managedExtensions = (Array.isArray(parsed.Extensions?.Install) ? parsed.Extensions.Install.length : 0) + explicitProfiles;
                    }
                } catch {
                    enabledQuickPolicies = 0;
                    managedExtensions = 0;
                }
            }

            wizardSummaryModeEl && (wizardSummaryModeEl.textContent = mode.toUpperCase());
            wizardSummaryPoliciesEl && (wizardSummaryPoliciesEl.textContent = `${enabledQuickPolicies}`);
            wizardSummaryExtensionsEl && (wizardSummaryExtensionsEl.textContent = `${managedExtensions}`);
        }

        function syncWizardPoliciesFromEditor() {
            const editor = getEditor();
            if (!editor) return;

            try {
                const parsed = fromEditorValue(editor.getValue(), documentRef.getElementById("mode").value);
                const normalized = parsed && typeof parsed === "object" ? parsed : {};
                wizardPolicyInputs.forEach((input) => {
                    input.disabled = input.closest("[data-schema-policy-control]")?.hidden === true;
                    input.checked = normalized[input.dataset.policyKey] === true;
                });
                wizardPolicySelectInputs.forEach((input) => {
                    input.disabled = input.closest("[data-schema-policy-control]")?.hidden === true;
                    const policyKey = input.dataset.policySelectKey;
                    const currentValue = policyKey ? normalized[policyKey] : "";
                    input.value = currentValue == null ? "" : String(currentValue);
                });
                syncHardeningPresetUi(normalized);
                syncCleanupPresetUi(normalized);
                syncSiteDataPresetUi(normalized);
                syncAiPresetUi(normalized);
            } catch {
                wizardPolicyInputs.forEach((input) => {
                    input.checked = false;
                    input.disabled = true;
                });
                wizardPolicySelectInputs.forEach((input) => {
                    input.value = "";
                    input.disabled = true;
                });
                syncHardeningPresetUi({});
                syncCleanupPresetUi({});
                syncSiteDataPresetUi({});
                syncAiPresetUi({});
            }

            updateWizardSummary();
        }

        function applyPolicyPreset(managedKeys, presetValues) {
            const editor = getEditor();
            if (!editor) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};

                managedKeys.forEach((key) => {
                    delete normalized[key];
                });
                Object.entries(presetValues).forEach(([key, value]) => {
                    normalized[key] = cloneJsonValue(value, value);
                });

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                setStatus(t("profiles.wizard_policy_applied"), "info");
            } catch (e) {
                setStatus(t("profiles.error_wizard_policy").replace("{detail}", e.message || e), "error");
            }
        }

        function applyQuickPolicyFromWizard(policyKey, enabled) {
            const editor = getEditor();
            if (!editor) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};

                if (enabled) {
                    normalized[policyKey] = resolveQuickPolicyEnabledValue(policyKey);
                } else {
                    delete normalized[policyKey];
                }

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                setStatus(t("profiles.wizard_policy_applied"), "info");
            } catch (e) {
                setStatus(t("profiles.error_wizard_policy").replace("{detail}", e.message || e), "error");
            }
        }

        function applyQuickPolicySelectFromWizard(policyKey, rawValue) {
            const editor = getEditor();
            if (!editor || !policyKey) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const nextValue = String(rawValue || "").trim();

                if (nextValue) {
                    normalized[policyKey] = nextValue;
                } else {
                    delete normalized[policyKey];
                }

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                setStatus(t("profiles.wizard_policy_applied"), "info");
            } catch (e) {
                setStatus(t("profiles.error_wizard_policy").replace("{detail}", e.message || e), "error");
            }
        }

        function setWizardStep(nextStep, options = {}) {
            const { history: historyMode = "push" } = options;
            const hasWizardUi = wizardPanels.length > 0
                && wizardPrevEl
                && wizardNextEl
                && wizardProgressTextEl;
            if (!hasWizardUi) {
                wizardStep = getWizardStepMeta(nextStep)?.step || wizardStep;
                updateWizardSummary();
                return;
            }

            const nextStepMeta = getWizardStepMeta(nextStep) || getWizardStepMeta(wizardStep) || wizardSteps[0];
            if (!nextStepMeta) return;
            const previousStep = wizardStep;
            wizardStep = nextStepMeta.step;
            const activeStepButton = nextStepMeta.button;

            wizardStepButtons.forEach((button) => {
                const isActive = Number(button.dataset.step) === wizardStep;
                button.classList.toggle("wizard-step--active", isActive);
                button.tabIndex = isActive ? 0 : -1;
                if (isActive) {
                    button.setAttribute("aria-current", "step");
                } else {
                    button.removeAttribute("aria-current");
                }
            });
            const stepperScrollBehavior = documentRef.defaultView?.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches
                ? "auto"
                : "smooth";
            const stepperEl = activeStepButton?.closest?.(".wizard-stepper");
            if (stepperEl && activeStepButton && stepperEl.scrollWidth > stepperEl.clientWidth) {
                const stepperBounds = stepperEl.getBoundingClientRect();
                const activeStepBounds = activeStepButton.getBoundingClientRect();
                const activeStepVisible = activeStepBounds.left >= stepperBounds.left
                    && activeStepBounds.right <= stepperBounds.right;
                if (!activeStepVisible) {
                    const centeredOffset = (stepperEl.clientWidth - activeStepBounds.width) / 2;
                    const targetLeft = stepperEl.scrollLeft
                        + activeStepBounds.left
                        - stepperBounds.left
                        - centeredOffset;
                    const maxScrollLeft = stepperEl.scrollWidth - stepperEl.clientWidth;
                    stepperEl.scrollTo({
                        behavior: stepperScrollBehavior,
                        left: Math.max(0, Math.min(targetLeft, maxScrollLeft)),
                    });
                }
            }
            wizardPanels.forEach((panel) => {
                const isActive = panel === getWizardPanel(nextStepMeta);
                panel.classList.toggle("is-active", isActive);
                panel.setAttribute("aria-hidden", isActive ? "false" : "true");
            });

            wizardPrevEl.disabled = nextStepMeta.index === 0;
            wizardPrevEl.classList.toggle("is-visibility-hidden", nextStepMeta.index === 0);
            wizardNextEl.disabled = nextStepMeta.index === wizardSteps.length - 1;
            wizardNextEl.classList.toggle("is-visibility-hidden", nextStepMeta.index === wizardSteps.length - 1);
            wizardNextEl.textContent = t("profiles.wizard_next");

            const progressKey = activeStepButton?.dataset?.stepProgressKey || "profiles.wizard_progress_one";
            const progressFallback = activeStepButton?.dataset?.stepProgressFallback || "Step 1 of 8: Browser, network & search";
            wizardProgressTextEl.textContent = t(progressKey, progressFallback);
            updateWizardSummary();
            if (nextStepMeta.index === wizardSteps.length - 1 && typeof renderFinalExportStepSummary === "function") {
                const { dirty = true, invalid = true } = currentSnapshotState?.() || {};
                renderFinalExportStepSummary(dirty, invalid);
            }
            if (wizardStep !== previousStep || !stepEntrySnapshots[wizardStep]) {
                captureStepEntrySnapshot(wizardStep);
            }
            renderCurrentStepActions();
            if (wizardStep !== previousStep || historyMode === "replace") {
                syncWizardStepLocation(nextStepMeta, historyMode);
            }
        }

        function getWizardStep() {
            return wizardStep;
        }

        function getWizardStepId(stepReference = wizardStep) {
            return getWizardStepMeta(stepReference)?.id || "";
        }

        async function finishWizard() {
            const { invalid, dirty } = currentSnapshotState();

            if (invalid) {
                setStatus(t("profiles.wizard_finish_invalid"), "warn");
                return;
            }

            if (!getCurrentId()) {
                documentRef.defaultView?.location.assign("/profiles/new");
                return;
            }

            if (dirty) {
                const saved = await saveCurrent();
                if (!saved) return;
            }

            setWizardStep(wizardSteps[wizardSteps.length - 1]?.step || wizardStep);
        }

        Array.from(documentRef.querySelectorAll("[data-hardening-preset]")).forEach((button) => {
            button.addEventListener("click", () => {
                const presetKey = button.dataset.hardeningPreset || "defaults";
                applyPolicyPreset(hardeningManagedPolicyKeys, hardeningPresets[presetKey] || {});
            });
        });
        Array.from(documentRef.querySelectorAll("[data-cleanup-preset]")).forEach((button) => {
            button.addEventListener("click", () => {
                const presetKey = button.dataset.cleanupPreset || "defaults";
                applyPolicyPreset(cleanupManagedPolicyKeys, cleanupPresets[presetKey] || {});
            });
        });
        Array.from(documentRef.querySelectorAll("[data-site-data-preset]")).forEach((button) => {
            button.addEventListener("click", () => {
                const presetKey = button.dataset.siteDataPreset || "defaults";
                applyPolicyPreset(siteDataManagedKeys, siteDataPresets[presetKey] || {});
            });
        });
        Array.from(documentRef.querySelectorAll("[data-ai-posture-preset]")).forEach((button) => {
            button.addEventListener("click", () => {
                const presetKey = button.dataset.aiPosturePreset || "defaults";
                applyAiPosturePreset(presetKey);
            });
        });
        documentRef.getElementById("wizard-site-data-fine-tuning-toggle")?.addEventListener("click", () => {
            const panelEl = documentRef.getElementById("wizard-site-data-fine-tuning-panel");
            const nextExpanded = panelEl?.hidden !== false;
            siteDataFineTuningPreference = nextExpanded;
            setPanelExpanded(panelEl, documentRef.getElementById("wizard-site-data-fine-tuning-toggle"), nextExpanded);
        });
        return {
            syncWizardFieldsFromForm,
            updateWizardSummary,
            syncWizardPoliciesFromEditor,
            applyQuickPolicyFromWizard,
            applyQuickPolicySelectFromWizard,
            setWizardStep,
            getWizardStep,
            getWizardStepId,
            getWizardStepFromLocation,
            getPreviousWizardStep: () => getAdjacentWizardStep(-1),
            getNextWizardStep: () => getAdjacentWizardStep(1),
            renderCurrentStepActions,
            markWizardBaselineSnapshot,
            undoCurrentStepChanges,
            resetCurrentStepToBaseline,
            finishWizard,
        };
    }

    export { create };
