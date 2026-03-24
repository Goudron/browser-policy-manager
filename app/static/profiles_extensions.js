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
        } = elements;

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
                return { state: "missing" };
            }

            const usesCatalogUrl = Boolean(
                (values.mode === "force_installed" || values.mode === "normal_installed")
                && values.effectiveUrl === profile.defaultUrl
            );

            if (usesCatalogUrl) {
                return { state: "catalog_url" };
            }

            if (values.effectiveUrl && values.effectiveUrl !== profile.defaultUrl) {
                return { state: "custom_url" };
            }

            return { state: "configured" };
        }

        function formatManagedExtensionProfileState(profileState) {
            if (profileState.state === "catalog_url") {
                return t("profiles.wizard_extension_profile_state_catalog_url", "Uses catalog install URL");
            }
            if (profileState.state === "custom_url") {
                return t("profiles.wizard_extension_profile_state_custom_url", "Custom install URL");
            }
            if (profileState.state === "configured") {
                return t("profiles.wizard_extension_profile_state_configured", "Configured");
            }
            return t("profiles.wizard_extension_profile_state_missing", "No explicit rule");
        }

        function renderManagedExtensionProfileStatuses() {
            managedExtensionProfiles.forEach((profile) => {
                const statusEl = getManagedExtensionStatusEl(profile.id);
                const modeEl = getManagedExtensionField(profile.id, "mode");
                const cardEl = modeEl?.closest(".wizard-section-group");
                const profileState = getManagedExtensionProfileState(profile);

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
            });
        }

        function syncFromEditor() {
            const editor = getEditor();
            if (!editor) return;

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
                renderManagedExtensionProfileStatuses();
                renderExtensionReviewSummary(normalized);
                setStatus(t("profiles.wizard_extensions_applied", "Extension settings updated."), "info");
            } catch (e) {
                setStatus(`Wizard extensions error: ${e.message || e}`, "error");
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
