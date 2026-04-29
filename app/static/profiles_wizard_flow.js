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
            fromEditorValue,
            toEditorValue,
            formatSchemaLabel,
            getDefaultSchemaVersion,
            renderWizardSchemaShell,
            buildWizardSettingsSearchIndex,
            renderWizardSettingsSearchResults,
            currentSnapshotState,
            renderFinalExportStepSummary,
            saveCurrent,
            readFormState,
            getBaselineSnapshot,
            setStatus,
        } = dependencies;

        const getEditor = state.getEditor || (() => null);
        const setCurrentRaw = state.setCurrentRaw || (() => { });
        const getCurrentId = state.getCurrentId || (() => null);
        const getCloneSourceProfile = state.getCloneSourceProfile || (() => null);

        const {
            starterPresets = {},
            complianceLayers = {},
            complianceMergedPresets = {},
            complianceMetadata = {},
            starterManagedKeys = [],
            wizardHomepageManagedKeys = [],
            wizardProxyManagedKeys = [],
            quickPolicyKeys = [],
            quickPolicyEnabledValues = {},
            wizardPreferenceSections = [],
        } = state;

        const {
            nameInput,
            wizardContextCopyEl,
            wizardNameEl,
            wizardSchemaEl,
            wizardModeEl,
            wizardScenarioSummaryCopyEl,
            wizardScenarioSummaryListEl,
            wizardSharedDeviceWorkflowCopyEl,
            wizardSharedDeviceWorkflowListEl,
            wizardBaselineSummaryCopyEl,
            wizardBaselineSummaryListEl,
            wizardBaselinePreviewCopyEl,
            wizardBaselinePreviewListEl,
            wizardStepButtons = [],
            wizardPanels = [],
            wizardScenarioButtons = [],
            wizardStarterButtons = [],
            wizardCisLayerButtons = [],
            wizardStepMemoryCopyEl,
            wizardStepMemoryListEl,
            wizardPrevEl,
            wizardNextEl,
            wizardFinishEl,
            wizardProgressTextEl,
            wizardSummaryNameEl,
            wizardSummarySchemaEl,
            wizardSummaryStarterEl,
            wizardSummaryCisEl,
            wizardSummaryDerivedRowEl,
            wizardSummaryDerivedEl,
            wizardSummaryModeEl,
            wizardSummaryPoliciesEl,
            wizardSummaryExtensionsEl,
            wizardPolicyInputs = [],
            wizardPolicySelectInputs = [],
        } = elements;

        const wizardTotalSteps = wizardPanels.length;
        const defaultSchemaVersion = getDefaultSchemaVersion(documentRef);
        let wizardStep = 1;
        let wizardScenario = "corporate_default";
        let wizardStarter = "basic_corporate";
        let wizardComplianceLayer = "none";
        let wizardComplianceSnapshot = null;
        const wizardComplianceNotes = new Map();
        let wizardPreviewStarter = null;
        let siteDataFineTuningPreference = null;
        let wizardBaselineSnapshot = null;
        const stepEntrySnapshots = {};
        const recentStepChanges = new Map();
        let recentChangeSequence = 0;
        const stepScopedPolicyKeys = {
            2: [
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
            ],
            3: [
                "Homepage",
                "NewTabPage",
                "OverrideFirstRunPage",
                "OverridePostUpdatePage",
                "FirefoxHome",
            ],
            4: [
                "SearchBar",
                "SearchSuggestEnabled",
                "SearchEngines",
                "FirefoxSuggest",
            ],
            5: [
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
            ],
            6: [
                "DisableFirefoxAccounts",
                "UserMessaging",
                "RequestedLocales",
                "TranslateEnabled",
                "Extensions",
                "ExtensionSettings",
                "InstallAddonsPermission",
                "WebsiteFilter",
                "Handlers",
                "Bookmarks",
                "ManagedBookmarks",
            ],
            7: [
                "AIControls",
                "GenerativeAI",
                "VisualSearchEnabled",
            ],
        };
        const stepPreferenceSections = {
            2: ["general"],
            3: ["home"],
            4: ["search"],
            5: ["privacy"],
            6: ["sync"],
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
        const siteDataManagedKeys = ["Permissions", "Cookies"];
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

        function updateWizardContext() {
            if (!wizardContextCopyEl) return;
            const cloneSource = getCloneSourceProfile();
            if (cloneSource?.name) {
                wizardContextCopyEl.textContent = t("profiles.wizard_context_cloned")
                    .replace("{name}", cloneSource.name);
                return;
            }
            wizardContextCopyEl.textContent = getCurrentId()
                ? t("profiles.wizard_context_existing")
                : t("profiles.wizard_context_new");
        }

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

        function getWizardStepLabel(stepNumber) {
            return documentRef
                .querySelector(`.wizard-step[data-step="${Number(stepNumber)}"] .wizard-step-label`)
                ?.textContent
                ?.trim() || `Step ${Number(stepNumber)}`;
        }

        function getRecentChangeSummary(stepNumber) {
            const summaryMap = {
                1: t("profiles.wizard_step_memory_step_setup"),
                2: t("profiles.wizard_step_memory_step_network"),
                3: t("profiles.wizard_step_memory_step_home"),
                4: t("profiles.wizard_step_memory_step_search"),
                5: t("profiles.wizard_step_memory_step_privacy"),
                6: t("profiles.wizard_step_memory_step_features"),
                7: t("profiles.wizard_step_memory_step_ai"),
            };
            return summaryMap[Number(stepNumber)] || t("profiles.wizard_step_memory_step_generic");
        }

        function captureWizardUiSnapshot() {
            const editor = getEditor();
            if (!editor) return null;
            try {
                return {
                    form: {
                        ...readFormState(),
                    },
                    flags: cloneJsonValue(fromEditorValue(editor.getValue(), getCurrentMode()), {}),
                    wizardStarter,
                    wizardComplianceLayer,
                    wizardScenario,
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
                    form: {
                        name: typeof parsed.name === "string" ? parsed.name : "",
                        owner: typeof parsed.owner === "string" ? parsed.owner : "",
                        description: typeof parsed.description === "string" ? parsed.description : "",
                        schemaVersion: typeof parsed.schemaVersion === "string" ? parsed.schemaVersion : defaultSchemaVersion,
                    },
                    flags: cloneJsonValue(parsed.flags, {}),
                    wizardStarter: wizardBaselineSnapshot?.wizardStarter || (getCurrentId() ? "keep_current" : "blank"),
                    wizardComplianceLayer: wizardBaselineSnapshot?.wizardComplianceLayer || "none",
                    wizardScenario: wizardBaselineSnapshot?.wizardScenario || inferScenarioFromStarter(
                        wizardBaselineSnapshot?.wizardStarter || (getCurrentId() ? "keep_current" : "blank"),
                    ),
                };
            } catch {
                return null;
            }
        }

        function getStepScope(stepNumber) {
            if (Number(stepNumber) === 1) return { full: true };
            if (Number(stepNumber) === wizardTotalSteps) return { readOnly: true };
            return {
                policyKeys: stepScopedPolicyKeys[Number(stepNumber)] || [],
                preferenceSections: stepPreferenceSections[Number(stepNumber)] || [],
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
                    wizardStarter: snapshot.wizardStarter || "blank",
                    wizardComplianceLayer: snapshot.wizardComplianceLayer || "none",
                    wizardScenario: snapshot.wizardScenario || inferScenarioFromStarter(snapshot.wizardStarter || "blank"),
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
                    wizardStarter: sourceSnapshot.wizardStarter || "blank",
                    wizardComplianceLayer: sourceSnapshot.wizardComplianceLayer || "none",
                    wizardScenario: sourceSnapshot.wizardScenario || inferScenarioFromStarter(sourceSnapshot.wizardStarter || "blank"),
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
                wizardStarter: currentSnapshot.wizardStarter,
                wizardComplianceLayer: currentSnapshot.wizardComplianceLayer,
                wizardScenario: currentSnapshot.wizardScenario,
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

            const profileTypeEl = documentRef.getElementById("profile-type");
            const ownerInput = documentRef.getElementById("profile-owner");
            const descriptionInput = documentRef.getElementById("profile-description");
            const nextSchemaVersion = snapshot.form?.schemaVersion || defaultSchemaVersion;

            nameInput.value = snapshot.form?.name || "";
            if (ownerInput) ownerInput.value = snapshot.form?.owner || "";
            if (descriptionInput) descriptionInput.value = snapshot.form?.description || "";
            if (profileTypeEl) profileTypeEl.value = nextSchemaVersion;
            if (wizardSchemaEl) wizardSchemaEl.value = nextSchemaVersion;
            if (snapshot.wizardStarter) {
                setWizardStarter(snapshot.wizardStarter, { preserveScenario: true });
            }
            setWizardComplianceLayer(snapshot.wizardComplianceLayer || "none", { skipApply: true });
            if (snapshot.wizardScenario) {
                setWizardScenario(snapshot.wizardScenario);
            }

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
                [1, 2, 3, 4, 5, 6, 7].forEach((stepNumber) => {
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
                    return `<div class="wizard-step-memory-item" data-step-memory-state="${isCurrentStep ? "current" : "recent"}"><div class="wizard-step-memory-item-main"><div class="wizard-step-memory-item-title">${item.title}</div><div class="wizard-step-memory-item-copy">${item.summary}</div></div><button type="button" class="button-base ghost-button wizard-step-memory-action" data-step-memory-jump="${String(item.step)}"${isCurrentStep ? " disabled" : ""}>${actionLabel}</button></div>`;
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

        function formatWizardStarterLabel(key) {
            const starterLabels = {
                blank: t("profiles.wizard_starter_blank_label"),
                keep_current: t("profiles.wizard_starter_keep_label"),
                basic_corporate: t("profiles.wizard_starter_basic_label"),
                classroom_kiosk: t("profiles.wizard_starter_classroom_label"),
                soc_hard: t("profiles.wizard_starter_soc_label"),
            };
            return starterLabels[key] || starterLabels.blank;
        }

        function formatWizardComplianceLabel(key) {
            const layer = complianceLayers[key] || complianceLayers.none || {};
            if (layer.label_key) {
                return t(layer.label_key);
            }
            return t("profiles.wizard_cis_none_title");
        }

        function getMergedStarterPolicyValues(starterKey, schemaVersion, complianceLayerKey = wizardComplianceLayer) {
            const starterVariants = complianceMergedPresets?.[starterKey] || {};
            const layerVariants = starterVariants[complianceLayerKey] || starterVariants.none || {};
            const schemaVariant = layerVariants[schemaVersion] || layerVariants.default;
            if (schemaVariant?.policy_values && typeof schemaVariant.policy_values === "object") {
                return cloneJsonValue(schemaVariant.policy_values, {}) || {};
            }
            return null;
        }

        function getMergedStarterSummary(starterKey, schemaVersion, complianceLayerKey = wizardComplianceLayer) {
            const starterVariants = complianceMergedPresets?.[starterKey] || {};
            const layerVariants = starterVariants[complianceLayerKey] || {};
            return layerVariants[schemaVersion]?.summary || {};
        }

        function getMergedStarterDecisions(starterKey, schemaVersion, complianceLayerKey = wizardComplianceLayer) {
            const starterVariants = complianceMergedPresets?.[starterKey] || {};
            const layerVariants = starterVariants[complianceLayerKey] || {};
            const decisions = layerVariants[schemaVersion]?.decisions;
            return Array.isArray(decisions) ? cloneJsonValue(decisions, []) || [] : [];
        }

        function getCisDecisionNoteKey(decision) {
            const path = Array.isArray(decision?.path) ? decision.path : [];
            if (path.length) return String(path[0]);
            const recommendationIds = Array.isArray(decision?.recommendation_ids)
                ? decision.recommendation_ids.filter(Boolean)
                : [];
            if (recommendationIds.length) return `cis:${recommendationIds[0]}`;
            if (decision?.decision) return `cis:${decision.decision}`;
            return "";
        }

        function seedWizardComplianceNotes(decisions) {
            if (!Array.isArray(decisions)) return;
            decisions.forEach((decision) => {
                const key = getCisDecisionNoteKey(decision);
                if (!key) return;
                const note = decision?.exception_note || decision?.exceptionNote;
                if (note) {
                    wizardComplianceNotes.set(key, String(note));
                }
            });
        }

        function getWizardComplianceMergeInfo() {
            const schemaVersion = documentRef.getElementById("profile-type").value || wizardSchemaEl.value || defaultSchemaVersion;
            const resolvedSnapshot = wizardStarter === "keep_current"
                && wizardComplianceSnapshot
                && typeof wizardComplianceSnapshot === "object"
                && wizardComplianceSnapshot.layer === wizardComplianceLayer
                ? wizardComplianceSnapshot
                : null;
            const baseDecisions = wizardComplianceLayer === "none"
                ? []
                : (resolvedSnapshot?.decisions || getMergedStarterDecisions(wizardStarter, schemaVersion));
            const decisions = Array.isArray(baseDecisions)
                ? baseDecisions.map((decision) => {
                    const key = getCisDecisionNoteKey(decision);
                    if (!key) return decision;
                    const note = wizardComplianceNotes.get(key) || decision?.exception_note || decision?.exceptionNote;
                    return note ? { ...decision, exception_note: note } : decision;
                })
                : [];
            return {
                layer: wizardComplianceLayer,
                label: formatWizardComplianceLabel(wizardComplianceLayer),
                benchmark_id: resolvedSnapshot?.benchmark_id || complianceMetadata.benchmark_id,
                benchmark_version: resolvedSnapshot?.benchmark_version || complianceMetadata.upstream_version,
                benchmark_name: complianceMetadata.upstream_name,
                summary: resolvedSnapshot?.summary || getMergedStarterSummary(wizardStarter, schemaVersion),
                decisions,
            };
        }

        function resolveScenarioStarter(scenarioKey) {
            if (scenarioKey === "shared_devices") return "classroom_kiosk";
            if (scenarioKey === "hardened") return "soc_hard";
            if (scenarioKey === "extension_rollout") return "basic_corporate";
            if (scenarioKey === "targeted_edits") {
                return getCurrentId() ? "keep_current" : "blank";
            }
            return "basic_corporate";
        }

        function inferScenarioFromStarter(starterKey) {
            if (starterKey === "classroom_kiosk") return "shared_devices";
            if (starterKey === "soc_hard") return "hardened";
            if (starterKey === "blank" || starterKey === "keep_current") return "targeted_edits";
            return "corporate_default";
        }

        function formatScenarioSummary(scenarioKey) {
            const starterKey = resolveScenarioStarter(scenarioKey);
            const starterLabel = formatWizardStarterLabel(starterKey);

            if (scenarioKey === "shared_devices") {
                return {
                    copy: t("profiles.wizard_scenario_summary_shared").replace("{baseline}", starterLabel),
                    items: [
                        t("profiles.wizard_scenario_summary_shared_item_one"),
                        t("profiles.wizard_scenario_summary_shared_item_two"),
                        t("profiles.wizard_scenario_summary_shared_item_three"),
                    ],
                };
            }
            if (scenarioKey === "hardened") {
                return {
                    copy: t("profiles.wizard_scenario_summary_hardened").replace("{baseline}", starterLabel),
                    items: [
                        t("profiles.wizard_scenario_summary_hardened_item_one"),
                        t("profiles.wizard_scenario_summary_hardened_item_two"),
                        t("profiles.wizard_scenario_summary_hardened_item_three"),
                    ],
                };
            }
            if (scenarioKey === "extension_rollout") {
                return {
                    copy: t("profiles.wizard_scenario_summary_addons").replace("{baseline}", starterLabel),
                    items: [
                        t("profiles.wizard_scenario_summary_addons_item_one"),
                        t("profiles.wizard_scenario_summary_addons_item_two"),
                        t("profiles.wizard_scenario_summary_addons_item_three"),
                    ],
                };
            }
            if (scenarioKey === "targeted_edits") {
                return getCurrentId()
                    ? {
                        copy: t("profiles.wizard_scenario_summary_targeted_existing").replace("{baseline}", starterLabel),
                        items: [
                            t("profiles.wizard_scenario_summary_targeted_existing_item_one"),
                            t("profiles.wizard_scenario_summary_targeted_existing_item_two"),
                            t("profiles.wizard_scenario_summary_targeted_existing_item_three"),
                        ],
                    }
                    : {
                        copy: t("profiles.wizard_scenario_summary_targeted_new").replace("{baseline}", starterLabel),
                        items: [
                            t("profiles.wizard_scenario_summary_targeted_new_item_one"),
                            t("profiles.wizard_scenario_summary_targeted_new_item_two"),
                            t("profiles.wizard_scenario_summary_targeted_new_item_three"),
                        ],
                    };
            }

            return {
                copy: t("profiles.wizard_scenario_summary_corporate").replace("{baseline}", starterLabel),
                items: [
                    t("profiles.wizard_scenario_summary_corporate_item_one"),
                    t("profiles.wizard_scenario_summary_corporate_item_two"),
                    t("profiles.wizard_scenario_summary_corporate_item_three"),
                ],
            };
        }

        function renderScenarioSummary() {
            if (!wizardScenarioSummaryCopyEl || !wizardScenarioSummaryListEl) return;
            const summary = formatScenarioSummary(wizardScenario);
            wizardScenarioSummaryCopyEl.textContent = summary.copy;
            wizardScenarioSummaryListEl.innerHTML = summary.items
                .map((item) => `<div class="wizard-baseline-summary-item">${item}</div>`)
                .join("");
        }

        function renderSharedDeviceWorkflow(parsed = null) {
            if (!wizardSharedDeviceWorkflowCopyEl || !wizardSharedDeviceWorkflowListEl) return;

            const sourceParsed = parsed && typeof parsed === "object" ? parsed : {};
            const isSharedScenario = wizardScenario === "shared_devices" || wizardStarter === "classroom_kiosk";
            const homepage = sourceParsed.Homepage && typeof sourceParsed.Homepage === "object" && !Array.isArray(sourceParsed.Homepage)
                ? sourceParsed.Homepage
                : {};
            const hasHomepageDecision = hasMeaningfulData(homepage.URL)
                || hasMeaningfulData(homepage.StartPage)
                || homepage.Locked === true;
            const hasCleanupDecision = hasMeaningfulData(sourceParsed.SanitizeOnShutdown);
            const hasPrivateBrowsingDecision = sourceParsed.DisablePrivateBrowsing === true;
            const hasSiteAccessDecision = hasMeaningfulData(sourceParsed.WebsiteFilter)
                || hasMeaningfulData(sourceParsed.Permissions)
                || hasMeaningfulData(sourceParsed.Cookies);

            wizardSharedDeviceWorkflowCopyEl.textContent = isSharedScenario
                ? t("profiles.wizard_shared_device_workflow_active")
                : t("profiles.wizard_shared_device_workflow_body");

            const items = [
                {
                    title: t("profiles.wizard_shared_device_workflow_home"),
                    copy: hasHomepageDecision
                        ? t("profiles.wizard_shared_device_workflow_home_ready")
                        : (isSharedScenario
                            ? t("profiles.wizard_shared_device_workflow_home_needed")
                            : t("profiles.wizard_shared_device_workflow_home_optional")),
                    tone: hasHomepageDecision ? "ready" : (isSharedScenario ? "strict" : "default"),
                    target: "field:wizard-homepage-url",
                },
                {
                    title: t("profiles.wizard_shared_device_workflow_sites"),
                    copy: hasSiteAccessDecision
                        ? t("profiles.wizard_shared_device_workflow_sites_ready")
                        : (isSharedScenario
                            ? t("profiles.wizard_shared_device_workflow_sites_needed")
                            : t("profiles.wizard_shared_device_workflow_sites_optional")),
                    tone: hasSiteAccessDecision ? "ready" : (isSharedScenario ? "strict" : "default"),
                    target: "policy:WebsiteFilter",
                },
                {
                    title: t("profiles.wizard_shared_device_workflow_private"),
                    copy: hasPrivateBrowsingDecision
                        ? t("profiles.wizard_shared_device_workflow_private_ready")
                        : (isSharedScenario
                            ? t("profiles.wizard_shared_device_workflow_private_needed")
                            : t("profiles.wizard_shared_device_workflow_private_optional")),
                    tone: hasPrivateBrowsingDecision ? "ready" : (isSharedScenario ? "strict" : "default"),
                    target: "policy:DisablePrivateBrowsing",
                },
                {
                    title: t("profiles.wizard_shared_device_workflow_cleanup"),
                    copy: hasCleanupDecision
                        ? t("profiles.wizard_shared_device_workflow_cleanup_ready")
                        : (isSharedScenario
                            ? t("profiles.wizard_shared_device_workflow_cleanup_needed")
                            : t("profiles.wizard_shared_device_workflow_cleanup_optional")),
                    tone: hasCleanupDecision ? "ready" : (isSharedScenario ? "strict" : "default"),
                    target: "policy:SanitizeOnShutdown",
                },
            ];

            wizardSharedDeviceWorkflowListEl.replaceChildren(
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

        function buildStarterPreviewTarget(current, starterKey, schemaVersion, complianceLayerKey = wizardComplianceLayer) {
            const normalized = current && typeof current === "object" && !Array.isArray(current)
                ? cloneJsonValue(current, {}) || {}
                : {};

            if (starterKey === "keep_current") {
                return normalized;
            }

            const mergedPolicyValues = getMergedStarterPolicyValues(starterKey, schemaVersion, complianceLayerKey);
            if (mergedPolicyValues) {
                starterManagedKeys.forEach((key) => {
                    delete normalized[key];
                });
                for (const [key, value] of Object.entries(mergedPolicyValues)) {
                    normalized[key] = cloneJsonValue(value, value);
                }
                return normalized;
            }

            const nextHomepage = {
                ...(normalized.Homepage && typeof normalized.Homepage === "object" ? normalized.Homepage : {}),
            };
            const nextProxy = {
                ...(normalized.Proxy && typeof normalized.Proxy === "object" ? normalized.Proxy : {}),
            };
            const presetConfig = starterPresets[starterKey] || {};
            const starterPolicyValues = {
                ...(cloneJsonValue(presetConfig.policy_values?.default, {}) || {}),
                ...(cloneJsonValue(presetConfig.policy_values?.[schemaVersion], {}) || {}),
            };

            starterManagedKeys.forEach((key) => {
                delete normalized[key];
            });
            wizardHomepageManagedKeys.forEach((key) => delete nextHomepage[key]);
            wizardProxyManagedKeys.forEach((key) => delete nextProxy[key]);

            for (const [key, value] of Object.entries(starterPolicyValues)) {
                normalized[key] = cloneJsonValue(value, value);
            }

            Object.assign(nextHomepage, cloneJsonValue(presetConfig.homepage, {}) || {});
            Object.assign(nextProxy, cloneJsonValue(presetConfig.proxy, {}) || {});

            if (Object.keys(nextHomepage).length) {
                normalized.Homepage = nextHomepage;
            } else {
                delete normalized.Homepage;
            }

            if (Object.keys(nextProxy).length) {
                normalized.Proxy = nextProxy;
            } else {
                delete normalized.Proxy;
            }

            return normalized;
        }

        function hasMeaningfulData(value) {
            if (typeof value === "boolean" || typeof value === "number") return true;
            if (typeof value === "string") return value.trim().length > 0;
            if (Array.isArray(value)) return value.some((entry) => hasMeaningfulData(entry));
            if (value && typeof value === "object") return Object.values(value).some((entry) => hasMeaningfulData(entry));
            return false;
        }

        function readPolicySubset(source, keys) {
            return (Array.isArray(keys) ? keys : []).reduce((acc, key) => {
                if (source && Object.prototype.hasOwnProperty.call(source, key)) {
                    acc[key] = source[key];
                }
                return acc;
            }, {});
        }

        function hasSubsetDiff(currentSubset, targetSubset) {
            const currentHas = hasMeaningfulData(currentSubset);
            const targetHas = hasMeaningfulData(targetSubset);
            if (!currentHas && !targetHas) return false;
            return !valuesEqual(currentSubset, targetSubset);
        }

        function renderBaselinePreview() {
            if (!wizardBaselinePreviewCopyEl || !wizardBaselinePreviewListEl) return;

            const previewStarter = starterPresets[wizardPreviewStarter] !== undefined ? wizardPreviewStarter : wizardStarter;
            const previewLabel = formatWizardStarterLabel(previewStarter);
            const previewComplianceLabel = formatWizardComplianceLabel(wizardComplianceLayer);
            const editor = getEditor();
            if (!editor) {
                wizardBaselinePreviewCopyEl.textContent = t("profiles.wizard_baseline_preview_body");
                wizardBaselinePreviewListEl.innerHTML = "";
                return;
            }

            let current = {};
            try {
                current = fromEditorValue(editor.getValue(), documentRef.getElementById("mode").value) || {};
            } catch {
                current = {};
            }

            const schemaVersion = documentRef.getElementById("profile-type").value || wizardSchemaEl.value || defaultSchemaVersion;
            const target = buildStarterPreviewTarget(current, previewStarter, schemaVersion);
            const previewItems = [];
            const categoryChecks = [
                {
                    key: "profiles.wizard_baseline_preview_homepage",
                    changed: hasSubsetDiff(
                        readPolicySubset(current?.Homepage, wizardHomepageManagedKeys),
                        readPolicySubset(target?.Homepage, wizardHomepageManagedKeys),
                    ),
                },
                {
                    key: "profiles.wizard_baseline_preview_proxy",
                    changed: hasSubsetDiff(
                        readPolicySubset(current?.Proxy, wizardProxyManagedKeys),
                        readPolicySubset(target?.Proxy, wizardProxyManagedKeys),
                    ),
                },
                {
                    key: "profiles.wizard_baseline_preview_network_trust",
                    changed: hasSubsetDiff(
                        readPolicySubset(current, ["Certificates", "WindowsSSO", "Authentication", "DNSOverHTTPS"]),
                        readPolicySubset(target, ["Certificates", "WindowsSSO", "Authentication", "DNSOverHTTPS"]),
                    ),
                },
                {
                    key: "profiles.wizard_baseline_preview_privacy",
                    changed: hasSubsetDiff(
                        readPolicySubset(current, ["EnableTrackingProtection", "DisableTelemetry", "DisableFirefoxStudies"]),
                        readPolicySubset(target, ["EnableTrackingProtection", "DisableTelemetry", "DisableFirefoxStudies"]),
                    ),
                },
                {
                    key: "profiles.wizard_baseline_preview_features",
                    changed: hasSubsetDiff(
                        readPolicySubset(current, ["DisableFirefoxAccounts", "UserMessaging", "RequestedLocales", "TranslateEnabled"]),
                        readPolicySubset(target, ["DisableFirefoxAccounts", "UserMessaging", "RequestedLocales", "TranslateEnabled"]),
                    ),
                },
                {
                    key: "profiles.wizard_baseline_preview_addons",
                    changed: hasSubsetDiff(
                        readPolicySubset(current, ["ExtensionSettings", "InstallAddonsPermission"]),
                        readPolicySubset(target, ["ExtensionSettings", "InstallAddonsPermission"]),
                    ),
                },
                {
                    key: "profiles.wizard_baseline_preview_sites",
                    changed: hasSubsetDiff(
                        readPolicySubset(current, ["WebsiteFilter", "Permissions", "Cookies", "DisablePrivateBrowsing"]),
                        readPolicySubset(target, ["WebsiteFilter", "Permissions", "Cookies", "DisablePrivateBrowsing"]),
                    ),
                },
                {
                    key: "profiles.wizard_baseline_preview_hardening",
                    changed: hasSubsetDiff(
                        readPolicySubset(current, ["HttpsOnlyMode", "SanitizeOnShutdown", "DisableDeveloperTools", "BlockAboutConfig", "BlockAboutProfiles"]),
                        readPolicySubset(target, ["HttpsOnlyMode", "SanitizeOnShutdown", "DisableDeveloperTools", "BlockAboutConfig", "BlockAboutProfiles"]),
                    ),
                },
            ];

            categoryChecks.forEach(({ key, changed }) => {
                if (changed) {
                    previewItems.push(t(key));
                }
            });

            if (previewItems.length) {
                const previewCopyKey = wizardComplianceLayer === "none"
                    ? "profiles.wizard_baseline_preview_selected"
                    : "profiles.wizard_baseline_preview_selected_with_cis";
                wizardBaselinePreviewCopyEl.textContent = t(previewCopyKey)
                    .replace("{label}", previewLabel)
                    .replace("{cis}", previewComplianceLabel);
                wizardBaselinePreviewListEl.innerHTML = previewItems.slice(0, 5)
                    .map((item) => `<div class="wizard-baseline-summary-item">${item}</div>`)
                    .join("");
                return;
            }

            const noChangesKey = wizardComplianceLayer === "none"
                ? "profiles.wizard_baseline_preview_no_major_changes"
                : "profiles.wizard_baseline_preview_no_major_changes_with_cis";
            wizardBaselinePreviewCopyEl.textContent = t(noChangesKey)
                .replace("{label}", previewLabel)
                .replace("{cis}", previewComplianceLabel);
            wizardBaselinePreviewListEl.innerHTML = `<div class="wizard-baseline-summary-item">${t("profiles.wizard_baseline_preview_same")}</div>`;
        }

        function updateWizardScenarioUi() {
            wizardScenarioButtons.forEach((button) => {
                const isActive = button.dataset.scenarioKey === wizardScenario;
                const previewStarter = resolveScenarioStarter(button.dataset.scenarioKey || "");
                const isPreview = previewStarter === wizardPreviewStarter
                    && button.dataset.scenarioKey !== wizardScenario
                    && wizardPreviewStarter !== wizardStarter;
                button.classList.toggle("wizard-starter-card--active", isActive);
                button.classList.toggle("wizard-starter-card--preview", isPreview);
                button.setAttribute("aria-pressed", isActive ? "true" : "false");
            });
            renderScenarioSummary();
        }

        function formatBaselineSummary(starterKey) {
            const preset = starterPresets[starterKey] || {};
            const schemaVersion = documentRef.getElementById("profile-type").value || wizardSchemaEl.value || defaultSchemaVersion;
            const mergedPolicyValues = getMergedStarterPolicyValues(starterKey, schemaVersion) || {};
            const policyValues = Object.keys(mergedPolicyValues).length
                ? mergedPolicyValues
                : {
                    ...(cloneJsonValue(preset.policy_values?.default, {}) || {}),
                    ...(cloneJsonValue(preset.policy_values?.[schemaVersion], {}) || {}),
                };
            const homepage = Object.keys(mergedPolicyValues).length
                ? cloneJsonValue(mergedPolicyValues.Homepage, {}) || {}
                : cloneJsonValue(preset.homepage, {}) || {};
            const proxy = Object.keys(mergedPolicyValues).length
                ? cloneJsonValue(mergedPolicyValues.Proxy, {}) || {}
                : cloneJsonValue(preset.proxy, {}) || {};
            const items = [];

            if (starterKey === "blank" && wizardComplianceLayer === "none") {
                return {
                    copy: t("profiles.wizard_baseline_summary_blank"),
                    items: [
                        t("profiles.wizard_baseline_summary_blank_item_one"),
                        t("profiles.wizard_baseline_summary_blank_item_two"),
                    ],
                };
            }
            if (starterKey === "keep_current") {
                return {
                    copy: t("profiles.wizard_baseline_summary_keep"),
                    items: [
                        t("profiles.wizard_baseline_summary_keep_item_one"),
                        t("profiles.wizard_baseline_summary_keep_item_two"),
                    ],
                };
            }

            if (homepage.URL) {
                items.push(t("profiles.wizard_baseline_summary_homepage"));
            }
            if (proxy.Mode === "system") {
                items.push(t("profiles.wizard_baseline_summary_proxy_system"));
            } else if (proxy.Mode === "manual") {
                items.push(t("profiles.wizard_baseline_summary_proxy_manual"));
            }
            if (policyValues.EnableTrackingProtection || policyValues.DisableTelemetry || policyValues.DisableFirefoxStudies) {
                items.push(t("profiles.wizard_baseline_summary_privacy"));
            }
            if (policyValues.ExtensionSettings || policyValues.InstallAddonsPermission) {
                items.push(t("profiles.wizard_baseline_summary_addons"));
            }
            if (policyValues.WebsiteFilter || policyValues.Permissions || policyValues.DisablePrivateBrowsing) {
                items.push(t("profiles.wizard_baseline_summary_shared_device"));
            }
            if (policyValues.HttpsOnlyMode || policyValues.SanitizeOnShutdown || policyValues.DisableDeveloperTools) {
                items.push(t("profiles.wizard_baseline_summary_hardening"));
            }
            if (wizardComplianceLayer !== "none") {
                const mergeSummary = getMergedStarterSummary(starterKey, schemaVersion);
                const added = Number(mergeSummary.added_from_cis || 0);
                const replaced = Number(mergeSummary.cis_replaced_base || 0);
                const review = Number(mergeSummary.review_required || 0);
                items.push(t("profiles.wizard_baseline_summary_cis")
                    .replace("{level}", formatWizardComplianceLabel(wizardComplianceLayer))
                    .replace("{count}", `${added + replaced}`));
                if (review > 0) {
                    items.push(t("profiles.wizard_baseline_summary_cis_review").replace("{count}", `${review}`));
                }
            }

            return {
                copy: t(wizardComplianceLayer === "none"
                    ? "profiles.wizard_baseline_summary_selected"
                    : "profiles.wizard_baseline_summary_selected_with_cis")
                    .replace("{label}", formatWizardStarterLabel(starterKey))
                    .replace("{cis}", formatWizardComplianceLabel(wizardComplianceLayer)),
                items: items.slice(0, 6),
            };
        }

        function renderBaselineSummary() {
            if (!wizardBaselineSummaryCopyEl || !wizardBaselineSummaryListEl) return;
            const summary = formatBaselineSummary(wizardStarter);
            wizardBaselineSummaryCopyEl.textContent = summary.copy;
            wizardBaselineSummaryListEl.innerHTML = summary.items
                .map((item) => `<div class="wizard-baseline-summary-item">${item}</div>`)
                .join("");
            renderBaselinePreview();
        }

        function updateWizardStarterUi() {
            wizardStarterButtons.forEach((button) => {
                const isActive = button.dataset.starterKey === wizardStarter;
                const isPreview = button.dataset.starterKey === wizardPreviewStarter && wizardPreviewStarter !== wizardStarter;
                button.classList.toggle("wizard-starter-card--active", isActive);
                button.classList.toggle("wizard-starter-card--preview", isPreview);
                button.setAttribute("aria-pressed", isActive ? "true" : "false");
            });
            wizardCisLayerButtons.forEach((button) => {
                const isActive = button.dataset.cisLayerKey === wizardComplianceLayer;
                const isDisabled = wizardStarter === "keep_current" && button.dataset.cisLayerKey !== "none";
                button.classList.toggle("wizard-starter-card--active", isActive);
                button.disabled = isDisabled;
                button.setAttribute("aria-pressed", isActive ? "true" : "false");
            });
            updateWizardScenarioUi();
            renderBaselineSummary();
            renderSharedDeviceWorkflow();
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
                    || button.dataset.cleanupPreset === activeKey;
                button.classList.toggle("wizard-search-engine-preset--applied", isActive);
                button.classList.toggle("wizard-search-engine-preset--partial", false);
                button.classList.toggle("wizard-search-engine-preset--conflict", false);
                button.setAttribute("aria-pressed", isActive ? "true" : "false");
            });
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

        function setWizardStarter(nextStarter, options = {}) {
            wizardStarter = starterPresets[nextStarter] !== undefined ? nextStarter : "blank";
            wizardPreviewStarter = null;
            if (wizardStarter === "keep_current" && !options.preserveComplianceLayer) {
                wizardComplianceLayer = "none";
            }
            if (!options.preserveScenario) {
                wizardScenario = inferScenarioFromStarter(wizardStarter);
            }
            updateWizardStarterUi();
            updateWizardSummary();
        }

        function setWizardComplianceLayer(nextLayer, options = {}) {
            wizardComplianceLayer = complianceLayers[nextLayer] !== undefined ? nextLayer : "none";
            if (wizardStarter === "keep_current" && wizardComplianceLayer !== "none" && !options.allowKeepCurrent) {
                wizardComplianceLayer = "none";
            }
            updateWizardStarterUi();
            updateWizardSummary();
            if (!options.skipApply && wizardStarter !== "keep_current") {
                applyStarterPreset(wizardStarter, { preserveScenario: true, preserveComplianceLayer: true });
            }
        }

        function setWizardComplianceSnapshot(nextSnapshot) {
            if (nextSnapshot && typeof nextSnapshot === "object") {
                wizardComplianceSnapshot = cloneJsonValue(nextSnapshot, {}) || {};
                wizardComplianceNotes.clear();
                seedWizardComplianceNotes(wizardComplianceSnapshot.decisions);
            } else {
                wizardComplianceSnapshot = null;
                wizardComplianceNotes.clear();
            }
        }

        function setWizardComplianceDecisionNote(decisionKey, note) {
            if (!decisionKey) return;
            const normalized = (note || "").trim();
            if (!normalized) {
                wizardComplianceNotes.delete(decisionKey);
                return;
            }
            wizardComplianceNotes.set(decisionKey, normalized);
        }

        function setWizardScenario(nextScenario) {
            wizardScenario = [
                "corporate_default",
                "shared_devices",
                "hardened",
                "extension_rollout",
                "targeted_edits",
            ].includes(nextScenario) ? nextScenario : "corporate_default";
            updateWizardScenarioUi();
        }

        function setPreviewStarter(nextStarter) {
            wizardPreviewStarter = starterPresets[nextStarter] !== undefined ? nextStarter : null;
            updateWizardStarterUi();
        }

        function clearPreviewStarter() {
            wizardPreviewStarter = null;
            updateWizardStarterUi();
        }

        function applyScenarioPreset(scenarioKey) {
            setWizardScenario(scenarioKey);
            applyStarterPreset(resolveScenarioStarter(wizardScenario), { preserveScenario: true });
        }

        function applyStarterPreset(starterKey, options = {}) {
            const editor = getEditor();
            if (!editor) return;

            if (starterKey === "keep_current") {
                setWizardStarter(starterKey, options);
                setStatus(t("profiles.wizard_starter_applied_keep"), "info");
                return;
            }

            try {
                const mode = documentRef.getElementById("mode").value;
                const schemaVersion = documentRef.getElementById("profile-type").value || wizardSchemaEl.value || defaultSchemaVersion;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const presetConfig = starterPresets[starterKey] || {};
                const mergedPolicyValues = getMergedStarterPolicyValues(starterKey, schemaVersion);
                const starterPolicyValues = mergedPolicyValues || {
                    ...(cloneJsonValue(presetConfig.policy_values?.default, {}) || {}),
                    ...(cloneJsonValue(presetConfig.policy_values?.[schemaVersion], {}) || {}),
                };

                starterManagedKeys.forEach((key) => {
                    delete normalized[key];
                });

                for (const [key, value] of Object.entries(starterPolicyValues)) {
                    normalized[key] = cloneJsonValue(value, value);
                }

                if (!mergedPolicyValues) {
                    const nextHomepage = {};
                    const nextProxy = {};
                    Object.assign(nextHomepage, cloneJsonValue(presetConfig.homepage, {}) || {});
                    Object.assign(nextProxy, cloneJsonValue(presetConfig.proxy, {}) || {});
                    if (Object.keys(nextHomepage).length) {
                        normalized.Homepage = nextHomepage;
                    }
                    if (Object.keys(nextProxy).length) {
                        normalized.Proxy = nextProxy;
                    }
                }

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                setWizardStarter(starterKey, options);
                setStatus(t(wizardComplianceLayer === "none"
                    ? "profiles.wizard_starter_applied"
                    : "profiles.wizard_starter_applied_with_cis"), "info");
            } catch (e) {
                setStatus(t("profiles.error_wizard_starter").replace("{detail}", e.message || e), "error");
            }
        }

        function syncWizardFieldsFromForm() {
            wizardNameEl.value = nameInput.value;
            wizardSchemaEl.value = documentRef.getElementById("profile-type").value || defaultSchemaVersion;
            wizardModeEl.value = documentRef.getElementById("mode").value || "json";
            wizardNameEl.disabled = nameInput.disabled;
            renderWizardSchemaShell();
            buildWizardSettingsSearchIndex();
            renderWizardSettingsSearchResults();
            updateWizardContext();
            updateWizardScenarioUi();
        }

        function resolveQuickPolicyEnabledValue(policyKey) {
            const schemaVersion = documentRef.getElementById("profile-type").value || wizardSchemaEl.value || defaultSchemaVersion;
            const configuredValue = quickPolicyEnabledValues[policyKey];
            if (!configuredValue) return true;

            return cloneJsonValue(
                configuredValue[schemaVersion] ?? configuredValue.default,
                true,
            );
        }

        function updateWizardSummary() {
            const form = readFormState();
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

            wizardSummaryNameEl.textContent = form.name || "—";
            wizardSummarySchemaEl.textContent = formatSchemaLabel(form.schemaVersion || defaultSchemaVersion);
            wizardSummaryStarterEl.textContent = formatWizardStarterLabel(wizardStarter);
            if (wizardSummaryCisEl) {
                wizardSummaryCisEl.textContent = formatWizardComplianceLabel(wizardComplianceLayer);
            }
            if (wizardSummaryDerivedRowEl && wizardSummaryDerivedEl) {
                const cloneSource = getCloneSourceProfile();
                if (cloneSource?.name) {
                    wizardSummaryDerivedRowEl.hidden = false;
                    wizardSummaryDerivedEl.textContent = t("profiles.wizard_summary_derived_value")
                        .replace("{name}", cloneSource.name);
                } else {
                    wizardSummaryDerivedRowEl.hidden = true;
                    wizardSummaryDerivedEl.textContent = "";
                }
            }
            wizardSummaryModeEl.textContent = mode.toUpperCase();
            wizardSummaryPoliciesEl.textContent = `${enabledQuickPolicies}`;
            wizardSummaryExtensionsEl.textContent = `${managedExtensions}`;
            renderBaselinePreview();
        }

        function syncWizardPoliciesFromEditor() {
            const editor = getEditor();
            if (!editor) return;

            try {
                const parsed = fromEditorValue(editor.getValue(), documentRef.getElementById("mode").value);
                const normalized = parsed && typeof parsed === "object" ? parsed : {};
                wizardPolicyInputs.forEach((input) => {
                    input.disabled = false;
                    input.checked = normalized[input.dataset.policyKey] === true;
                });
                wizardPolicySelectInputs.forEach((input) => {
                    input.disabled = false;
                    const policyKey = input.dataset.policySelectKey;
                    const currentValue = policyKey ? normalized[policyKey] : "";
                    input.value = currentValue == null ? "" : String(currentValue);
                });
                syncHardeningPresetUi(normalized);
                syncCleanupPresetUi(normalized);
                syncSiteDataPresetUi(normalized);
                renderSharedDeviceWorkflow(normalized);
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
                renderSharedDeviceWorkflow({});
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

        function setWizardStep(nextStep) {
            const previousStep = wizardStep;
            wizardStep = Math.min(wizardTotalSteps, Math.max(1, Number(nextStep) || 1));
            let activeStepButton = null;

            wizardStepButtons.forEach((button) => {
                const isActive = Number(button.dataset.step) === wizardStep;
                button.classList.toggle("wizard-step--active", isActive);
                if (isActive) {
                    button.setAttribute("aria-current", "step");
                } else {
                    button.removeAttribute("aria-current");
                }
                if (isActive) {
                    activeStepButton = button;
                }
            });
            wizardPanels.forEach((panel) => {
                const isActive = panel.id === `wizard-step-${wizardStep}`;
                panel.classList.toggle("is-active", isActive);
                panel.setAttribute("aria-hidden", isActive ? "false" : "true");
            });

            wizardPrevEl.disabled = wizardStep === 1;
            wizardPrevEl.classList.toggle("is-visibility-hidden", wizardStep === 1);
            wizardNextEl.disabled = wizardStep === wizardTotalSteps;
            wizardNextEl.classList.toggle("is-visibility-hidden", wizardStep === wizardTotalSteps);
            wizardNextEl.textContent = t("profiles.wizard_next");

            const progressKey = activeStepButton?.dataset?.stepProgressKey || "profiles.wizard_progress_one";
            const progressFallback = activeStepButton?.dataset?.stepProgressFallback || "Step 1 of 8: start";
            wizardProgressTextEl.textContent = t(progressKey, progressFallback);
            updateWizardSummary();
            if (wizardStep === wizardTotalSteps && typeof renderFinalExportStepSummary === "function") {
                const { dirty = true, invalid = true } = currentSnapshotState?.() || {};
                renderFinalExportStepSummary(dirty, invalid);
            }
            if (wizardStep !== previousStep || !stepEntrySnapshots[wizardStep]) {
                captureStepEntrySnapshot(wizardStep);
            }
            renderCurrentStepActions();
        }

        function getWizardStep() {
            return wizardStep;
        }

        async function finishWizard() {
            const { invalid, dirty } = currentSnapshotState();

            if (invalid) {
                setStatus(t("profiles.wizard_finish_invalid"), "warn");
                return;
            }

            if (!getCurrentId() && !nameInput.value.trim()) {
                setStatus(t("profiles.wizard_finish_name_required"), "warn");
                setWizardStep(1);
                nameInput.focus();
                return;
            }

            if (!getCurrentId() || dirty) {
                const saved = await saveCurrent();
                if (!saved) return;
            }

            setWizardStep(7);
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
        documentRef.getElementById("wizard-site-data-fine-tuning-toggle")?.addEventListener("click", () => {
            const panelEl = documentRef.getElementById("wizard-site-data-fine-tuning-panel");
            const nextExpanded = panelEl?.hidden !== false;
            siteDataFineTuningPreference = nextExpanded;
            setPanelExpanded(panelEl, documentRef.getElementById("wizard-site-data-fine-tuning-toggle"), nextExpanded);
        });
        return {
            updateWizardContext,
            setWizardStarter,
            setWizardComplianceLayer,
            setWizardComplianceSnapshot,
            setWizardComplianceDecisionNote,
            setWizardScenario,
            setPreviewStarter,
            clearPreviewStarter,
            applyScenarioPreset,
            applyStarterPreset,
            getWizardScenario: () => wizardScenario,
            getWizardStarter: () => wizardStarter,
            getWizardComplianceLayer: () => wizardComplianceLayer,
            getWizardComplianceMergeInfo,
            getBaselineSummary: () => formatBaselineSummary(wizardStarter),
            syncWizardFieldsFromForm,
            updateWizardSummary,
            syncWizardPoliciesFromEditor,
            applyQuickPolicyFromWizard,
            applyQuickPolicySelectFromWizard,
            setWizardStep,
            getWizardStep,
            renderCurrentStepActions,
            markWizardBaselineSnapshot,
            undoCurrentStepChanges,
            resetCurrentStepToBaseline,
            finishWizard,
        };
    }

    window.BPMProfilesWizardFlow = { create };
})();
