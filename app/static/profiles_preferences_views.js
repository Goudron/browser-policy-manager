(() => {
    function create({
        documentRef = document,
        wizardPreferenceSections = [],
        wizardKnownPreferences = [],
        wizardPreferenceViews = {},
        wizardPreferenceRowTemplateEl = null,
        wizardPreferencesKnownListEl = null,
        dependencies = {},
        rowHelpers = {},
        stateApi = {},
    }) {
        const { t, escapeHtml, serializePreferenceValue, setStatus } = dependencies;
        const {
            getPreferenceFieldInput,
            setPreferenceRowValue,
            updatePreferenceRowAssist,
            updatePreferenceRowPresentation,
        } = rowHelpers;

        function renderPreferencePresetButtons() {
            wizardPreferenceSections.forEach((section) => {
                const view = wizardPreferenceViews[section.id];
                if (!view?.presets) return;

                view.presets.innerHTML = "";
                (section.presets || []).forEach((preset) => {
                    const button = documentRef.createElement("button");
                    button.type = "button";
                    button.className = "button-base ghost-button wizard-search-engine-preset";
                    button.dataset.preferenceSection = section.id;
                    button.dataset.preferencePreset = preset.id;
                    button.dataset.settingsTarget = `preference-preset:${preset.id}`;
                    button.innerHTML = `
                        <span>${t(preset.label_key, preset.pref)}</span>
                        <span class="wizard-search-engine-preset-copy">${t(preset.description_key, preset.pref)}</span>
                    `;
                    button.addEventListener("click", () => {
                        stateApi.appendPreferenceDraft(section.id, preset.pref, {
                            Value: preset.value,
                            Status: preset.status,
                            Type: preset.type,
                        });
                        setStatus(t("profiles.wizard_preferences_preset_applied"), "info");
                    });
                    view.presets.appendChild(button);
                });
            });
        }

        function renderPreferenceBundleButtons() {
            wizardPreferenceSections.forEach((section) => {
                const view = wizardPreferenceViews[section.id];
                if (!view?.bundles) return;

                view.bundles.innerHTML = "";
                (section.bundles || []).forEach((bundle) => {
                    const button = documentRef.createElement("button");
                    const bundleState = stateApi.getPreferenceBundleState(bundle);
                    button.type = "button";
                    button.className = "button-base ghost-button wizard-search-engine-preset";
                    if (bundleState.state === "applied") button.classList.add("wizard-search-engine-preset--applied");
                    if (bundleState.state === "partial") button.classList.add("wizard-search-engine-preset--partial");
                    if (bundleState.state === "conflict") button.classList.add("wizard-search-engine-preset--conflict");
                    button.dataset.preferenceSection = section.id;
                    button.dataset.preferenceBundle = bundle.id;
                    button.dataset.settingsTarget = `preference-bundle:${bundle.id}`;
                    button.innerHTML = `
                        <span>${t(bundle.label_key, bundle.id)}</span>
                        <span class="wizard-search-engine-preset-copy">${t(bundle.description_key, bundle.id)}</span>
                        <span class="wizard-search-engine-preset-copy wizard-search-engine-preset-status">${stateApi.formatPreferenceBundleStatus(bundleState)}</span>
                    `;
                    button.addEventListener("click", () => {
                        stateApi.appendPreferenceBundle(section.id, bundle);
                        setStatus(t("profiles.wizard_preferences_bundle_applied"), "info");
                    });
                    view.bundles.appendChild(button);
                });
            });
        }

        function renderKnownPreferenceButtons() {
            wizardPreferenceSections.forEach((section) => {
                const view = wizardPreferenceViews[section.id];
                if (!view?.known) return;

                view.known.innerHTML = "";
                (section.known_preferences || []).forEach((knownPreference) => {
                    const button = documentRef.createElement("button");
                    const knownState = stateApi.getKnownPreferenceState(knownPreference);
                    const label = t(knownPreference.label_key, knownPreference.fallback || knownPreference.pref);
                    const description = t(
                        knownPreference.description_key,
                        knownPreference.description_fallback || knownPreference.pref,
                    );

                    button.type = "button";
                    button.className = "button-base ghost-button wizard-search-engine-preset";
                    if (knownState.state === "suggested") button.classList.add("wizard-search-engine-preset--applied");
                    if (knownState.state === "present") button.classList.add("wizard-search-engine-preset--partial");
                    if (knownState.state === "overridden") button.classList.add("wizard-search-engine-preset--conflict");
                    button.dataset.preferenceSection = section.id;
                    button.dataset.knownPreference = knownPreference.pref;
                    button.dataset.settingsTarget = `known-preference:${knownPreference.pref}`;
                    button.innerHTML = `
                        <span>${escapeHtml(label)}</span>
                        <span class="wizard-search-engine-preset-copy">${escapeHtml(description)}</span>
                        <span class="wizard-search-engine-preset-copy wizard-search-engine-preset-status">${escapeHtml(stateApi.formatKnownPreferenceStatus(knownState))}</span>
                    `;
                    button.addEventListener("click", () => {
                        stateApi.appendPreferenceDraft(section.id, knownPreference.pref, stateApi.createKnownPreferenceSeed(knownPreference));
                        setStatus(t("profiles.wizard_preferences_known_applied"), "info");
                    });
                    view.known.appendChild(button);
                });
            });
        }

        function renderKnownPreferenceOptions() {
            if (!wizardPreferencesKnownListEl) return;

            wizardPreferencesKnownListEl.innerHTML = wizardKnownPreferences
                .map((entry) => {
                    const label = t(entry.label_key, entry.fallback || entry.pref);
                    const description = t(entry.description_key, entry.description_fallback || "");
                    const details = [label, description].filter(Boolean).join(" • ");
                    return `<option value="${escapeHtml(entry.pref)}" label="${escapeHtml(details)}"></option>`;
                })
                .join("");
        }

        function renderPreferenceDrafts(disabled = false) {
            wizardPreferenceSections.forEach((section) => {
                const view = wizardPreferenceViews[section.id];
                if (!view?.list || !view.empty || !view.add || !wizardPreferenceRowTemplateEl) return;

                view.list.innerHTML = "";
                view.add.disabled = disabled;
                const sectionDrafts = stateApi.getDrafts().filter((draft) => draft.section === section.id);
                view.empty.hidden = sectionDrafts.length > 0;

                sectionDrafts.forEach((draft, index) => {
                    const fragment = wizardPreferenceRowTemplateEl.content.cloneNode(true);
                    const row = fragment.querySelector("[data-preference-row]");
                    const seed = draft.seed || {};

                    row.dataset.preferenceRow = draft.id;
                    row.dataset.preferenceUiDisabled = disabled ? "true" : "false";
                    setPreferenceRowValue(row, "name", draft.sourceName);
                    setPreferenceRowValue(row, "status", typeof seed.Status === "string" ? seed.Status : "default");
                    setPreferenceRowValue(row, "type", typeof seed.Type === "string" ? seed.Type : "");
                    setPreferenceRowValue(row, "value", seed.Value === undefined ? "" : serializePreferenceValue(seed.Value));

                    row.querySelectorAll("input, select, button").forEach((element) => {
                        element.disabled = disabled;
                    });
                    updatePreferenceRowAssist(row, {
                        getKnownPreference: stateApi.getKnownPreference,
                        forceAutofill: false,
                    });
                    updatePreferenceRowPresentation(row, index, {
                        getKnownPreference: stateApi.getKnownPreference,
                    });

                    row.querySelectorAll("[data-preference-field]").forEach((input) => {
                        input.addEventListener("input", () => {
                            updatePreferenceRowAssist(row, {
                                getKnownPreference: stateApi.getKnownPreference,
                                forceAutofill: input.dataset.preferenceField === "name",
                            });
                            updatePreferenceRowPresentation(row, index, {
                                getKnownPreference: stateApi.getKnownPreference,
                            });
                            renderPreferenceBundleButtons();
                            renderKnownPreferenceButtons();
                            stateApi.applyPreferencesFromWizard();
                        });
                        input.addEventListener("change", () => {
                            updatePreferenceRowAssist(row, {
                                getKnownPreference: stateApi.getKnownPreference,
                                forceAutofill: input.dataset.preferenceField === "name",
                            });
                            updatePreferenceRowPresentation(row, index, {
                                getKnownPreference: stateApi.getKnownPreference,
                            });
                            renderPreferenceBundleButtons();
                            renderKnownPreferenceButtons();
                            stateApi.applyPreferencesFromWizard();
                        });
                    });

                    row.querySelector("[data-preference-remove]")?.addEventListener("click", () => {
                        stateApi.removeDraft(draft.id);
                        stateApi.updatePreferenceSectionOverrides();
                        renderPreferenceDrafts(false);
                        stateApi.applyPreferencesFromWizard();
                    });

                    view.list.appendChild(fragment);
                });
            });

            renderPreferenceBundleButtons();
            renderKnownPreferenceButtons();
        }

        function bindAddButtonListeners() {
            wizardPreferenceSections.forEach((section) => {
                wizardPreferenceViews[section.id]?.add?.addEventListener("click", () => {
                    stateApi.appendPreferenceDraft(section.id);
                });
            });
        }

        return {
            renderPreferencePresetButtons,
            renderPreferenceBundleButtons,
            renderKnownPreferenceButtons,
            renderKnownPreferenceOptions,
            renderPreferenceDrafts,
            bindAddButtonListeners,
        };
    }

    window.BPMProfilesPreferenceViews = { create };
})();
