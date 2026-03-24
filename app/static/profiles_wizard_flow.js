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
            renderWizardSchemaShell,
            buildWizardSettingsSearchIndex,
            renderWizardSettingsSearchResults,
            currentSnapshotState,
            saveCurrent,
            readFormState,
            setStatus,
        } = dependencies;

        const getEditor = state.getEditor || (() => null);
        const setCurrentRaw = state.setCurrentRaw || (() => {});
        const getCurrentId = state.getCurrentId || (() => null);

        const {
            starterPresets = {},
            starterManagedKeys = [],
            wizardHomepageManagedKeys = [],
            wizardProxyManagedKeys = [],
            quickPolicyKeys = [],
            quickPolicyEnabledValues = {},
        } = state;

        const {
            nameInput,
            wizardContextCopyEl,
            wizardNameEl,
            wizardSchemaEl,
            wizardModeEl,
            wizardStepButtons = [],
            wizardPanels = [],
            wizardStarterButtons = [],
            wizardPrevEl,
            wizardNextEl,
            wizardFinishEl,
            wizardProgressTextEl,
            wizardSummaryNameEl,
            wizardSummarySchemaEl,
            wizardSummaryStarterEl,
            wizardSummaryModeEl,
            wizardSummaryPoliciesEl,
            wizardSummaryExtensionsEl,
            wizardPolicyInputs = [],
            wizardPolicySelectInputs = [],
        } = elements;

        const wizardTotalSteps = wizardPanels.length;
        let wizardStep = 1;
        let wizardStarter = "blank";

        function updateWizardContext() {
            if (!wizardContextCopyEl) return;
            wizardContextCopyEl.textContent = getCurrentId()
                ? t("profiles.wizard_context_existing", "You are editing an existing profile. Open any step you need, save when ready, and export from the last step.")
                : t("profiles.wizard_context_new", "You are creating a new profile. Set the essentials first, then jump to any step you need.");
        }

        function formatWizardStarterLabel(key) {
            const starterLabels = {
                blank: t("profiles.wizard_starter_blank_label", "Blank draft"),
                keep_current: t("profiles.wizard_starter_keep_label", "Keep current"),
                basic_corporate: t("profiles.wizard_starter_basic_label", "Basic corporate"),
                classroom_kiosk: t("profiles.wizard_starter_classroom_label", "Classroom kiosk"),
                soc_hard: t("profiles.wizard_starter_soc_label", "Security hardened"),
            };
            return starterLabels[key] || starterLabels.blank;
        }

        function updateWizardStarterUi() {
            wizardStarterButtons.forEach((button) => {
                button.classList.toggle("wizard-starter-card--active", button.dataset.starterKey === wizardStarter);
            });
        }

        function setWizardStarter(nextStarter) {
            wizardStarter = starterPresets[nextStarter] !== undefined ? nextStarter : "blank";
            updateWizardStarterUi();
            updateWizardSummary();
        }

        function applyStarterPreset(starterKey) {
            const editor = getEditor();
            if (!editor) return;

            if (starterKey === "keep_current") {
                setWizardStarter(starterKey);
                setStatus(t("profiles.wizard_starter_applied_keep", "Current profile baseline kept."), "info");
                return;
            }

            try {
                const mode = documentRef.getElementById("mode").value;
                const schemaVersion = documentRef.getElementById("profile-type").value || wizardSchemaEl.value || "esr-140";
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
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

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                setWizardStarter(starterKey);
                setStatus(t("profiles.wizard_starter_applied", "Starter baseline applied."), "info");
            } catch (e) {
                setStatus(`Wizard starter error: ${e.message || e}`, "error");
            }
        }

        function syncWizardFieldsFromForm() {
            wizardNameEl.value = nameInput.value;
            wizardSchemaEl.value = documentRef.getElementById("profile-type").value || "esr-140";
            wizardModeEl.value = documentRef.getElementById("mode").value || "json";
            wizardNameEl.disabled = nameInput.disabled;
            renderWizardSchemaShell();
            buildWizardSettingsSearchIndex();
            renderWizardSettingsSearchResults();
            updateWizardContext();
        }

        function resolveQuickPolicyEnabledValue(policyKey) {
            const schemaVersion = documentRef.getElementById("profile-type").value || wizardSchemaEl.value || "esr-140";
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
            wizardSummarySchemaEl.textContent = formatSchemaLabel(form.schemaVersion || "esr-140");
            wizardSummaryStarterEl.textContent = formatWizardStarterLabel(wizardStarter);
            wizardSummaryModeEl.textContent = mode.toUpperCase();
            wizardSummaryPoliciesEl.textContent = `${enabledQuickPolicies}`;
            wizardSummaryExtensionsEl.textContent = `${managedExtensions}`;
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
            } catch {
                wizardPolicyInputs.forEach((input) => {
                    input.checked = false;
                    input.disabled = true;
                });
                wizardPolicySelectInputs.forEach((input) => {
                    input.value = "";
                    input.disabled = true;
                });
            }

            updateWizardSummary();
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
                setStatus(t("profiles.wizard_policy_applied", "Quick policy updated."), "info");
            } catch (e) {
                setStatus(`Wizard policy error: ${e.message || e}`, "error");
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
                setStatus(t("profiles.wizard_policy_applied", "Quick policy updated."), "info");
            } catch (e) {
                setStatus(`Wizard policy error: ${e.message || e}`, "error");
            }
        }

        function setWizardStep(nextStep) {
            wizardStep = Math.min(wizardTotalSteps, Math.max(1, Number(nextStep) || 1));

            wizardStepButtons.forEach((button) => {
                button.classList.toggle("wizard-step--active", Number(button.dataset.step) === wizardStep);
            });
            wizardPanels.forEach((panel) => {
                panel.classList.toggle("is-active", panel.id === `wizard-step-${wizardStep}`);
            });

            wizardPrevEl.disabled = wizardStep === 1;
            wizardPrevEl.style.visibility = wizardStep === 1 ? "hidden" : "visible";
            wizardNextEl.disabled = wizardStep === wizardTotalSteps;
            wizardNextEl.style.visibility = wizardStep === wizardTotalSteps ? "hidden" : "visible";
            wizardNextEl.textContent = t("profiles.wizard_next", "Next step");

            const progressKeys = [
                "profiles.wizard_progress_one",
                "profiles.wizard_progress_two",
                "profiles.wizard_progress_three",
                "profiles.wizard_progress_four",
                "profiles.wizard_progress_five",
                "profiles.wizard_progress_six",
                "profiles.wizard_progress_seven",
            ];
            const progressFallbacks = [
                "Step 1 of 7: profile setup",
                "Step 2 of 7: General",
                "Step 3 of 7: Home",
                "Step 4 of 7: Search",
                "Step 5 of 7: Privacy & security",
                "Step 6 of 7: Sync and add-ons",
                "Step 7 of 7: export",
            ];
            const progressKey = progressKeys[wizardStep - 1] || progressKeys[0];
            const progressFallback = progressFallbacks[wizardStep - 1] || progressFallbacks[0];
            wizardProgressTextEl.textContent = t(progressKey, progressFallback);
            updateWizardSummary();
        }

        function getWizardStep() {
            return wizardStep;
        }

        async function finishWizard() {
            const { invalid, dirty } = currentSnapshotState();

            if (invalid) {
                setStatus(t("profiles.wizard_finish_invalid", "Fix invalid JSON or YAML before finishing."), "warn");
                return;
            }

            if (!getCurrentId() && !nameInput.value.trim()) {
                setStatus(t("profiles.wizard_finish_name_required", "Profile name is required before finishing."), "warn");
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

        return {
            updateWizardContext,
            setWizardStarter,
            applyStarterPreset,
            syncWizardFieldsFromForm,
            updateWizardSummary,
            syncWizardPoliciesFromEditor,
            applyQuickPolicyFromWizard,
            applyQuickPolicySelectFromWizard,
            setWizardStep,
            getWizardStep,
            finishWizard,
        };
    }

    window.BPMProfilesWizardFlow = { create };
})();
