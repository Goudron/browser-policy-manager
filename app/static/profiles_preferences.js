(() => {
    function create({
        documentRef = document,
        wizardPreferenceSections = [],
        wizardKnownPreferences = [],
        wizardKnownPreferenceIndex = {},
        wizardPreferenceEntryManagedKeys = [],
        dependencies = {},
        state = {},
    }) {
        const {
            t,
            escapeHtml,
            cloneJsonValue,
            stablePreferenceValueKey,
            serializePreferenceValue,
            parsePreferenceValue,
            serializePreferenceSelectValue,
            normalizePreferenceName,
            fromEditorValue,
            toEditorValue,
            setStatus,
        } = dependencies;

        const wizardPreferenceRowTemplateEl = documentRef.getElementById("wizard-preference-row-template");
        const wizardPreferencesKnownListEl = documentRef.getElementById("wizard-preferences-known-list");
        const generalPreferencesFocusButtons = Array.from(documentRef.querySelectorAll("[data-general-preferences-focus]"));
        const wizardPreferenceViews = Object.fromEntries(
            wizardPreferenceSections.map((section) => [
                section.id,
                {
                    list: documentRef.getElementById(`wizard-preferences-${section.id}-list`),
                    empty: documentRef.getElementById(`wizard-preferences-${section.id}-empty`),
                    presets: documentRef.getElementById(`wizard-preferences-${section.id}-presets`),
                    bundles: documentRef.getElementById(`wizard-preferences-${section.id}-bundles`),
                    known: documentRef.getElementById(`wizard-preferences-${section.id}-known`),
                    add: documentRef.getElementById(`wizard-preferences-${section.id}-add`),
                    count: documentRef.getElementById(`wizard-preferences-${section.id}-count`),
                },
            ]),
        );

        const rowHelpers = window.BPMProfilesPreferenceRows.create({
            dependencies: {
                t,
                escapeHtml,
                serializePreferenceValue,
                parsePreferenceValue,
                serializePreferenceSelectValue,
            },
        });

        const preferenceState = window.BPMProfilesPreferenceState.create({
            documentRef,
            wizardPreferenceSections,
            wizardKnownPreferenceIndex,
            wizardPreferenceEntryManagedKeys,
            wizardPreferenceViews,
            dependencies: {
                t,
                cloneJsonValue,
                stablePreferenceValueKey,
                parsePreferenceValue,
                normalizePreferenceName,
                fromEditorValue,
                toEditorValue,
                setStatus,
            },
            state,
            rowHelpers,
        });

        const preferenceViews = window.BPMProfilesPreferenceViews.create({
            documentRef,
            wizardPreferenceSections,
            wizardKnownPreferences,
            wizardPreferenceViews,
            wizardPreferenceRowTemplateEl,
            wizardPreferencesKnownListEl,
            dependencies: {
                t,
                escapeHtml,
                serializePreferenceValue,
                setStatus,
            },
            rowHelpers,
            stateApi: preferenceState,
        });

        preferenceState.connectViews({
            renderPreferenceDrafts: preferenceViews.renderPreferenceDrafts,
        });

        function revealPreferenceFocus(kind) {
            const generalView = wizardPreferenceViews.general || {};
            let targetEl = null;

            if (kind === "startup") {
                targetEl = generalView.presets?.querySelector('[data-preference-preset="restore_session"]')
                    || generalView.presets?.querySelector('[data-preference-preset="open_homepage"]');
            } else if (kind === "downloads") {
                targetEl = generalView.presets?.querySelector('[data-preference-preset="download_prompt"]')
                    || generalView.presets?.querySelector('[data-preference-preset="download_dir"]');
            } else if (kind === "behavior") {
                targetEl = generalView.presets?.querySelector('[data-preference-preset="smooth_scroll"]')
                    || generalView.presets?.querySelector('[data-preference-preset="spellcheck_multiline"]')
                    || generalView.known?.querySelector('[data-known-preference="general.autoScroll"]');
            } else if (kind === "manual") {
                targetEl = generalView.known || generalView.list || generalView.presets;
            }

            if (!targetEl) return;
            targetEl.scrollIntoView?.({ behavior: "smooth", block: "center" });
            targetEl.classList.add("settings-target-highlight");
            window.setTimeout(() => {
                targetEl.classList.remove("settings-target-highlight");
            }, 1800);
            const focusTarget = targetEl.matches("button, input, select, textarea, [tabindex]")
                ? targetEl
                : targetEl.querySelector("button, input, select, textarea, [tabindex]");
            if (focusTarget?.focus) {
                if (focusTarget === targetEl && !targetEl.hasAttribute("tabindex")) {
                    targetEl.setAttribute("tabindex", "-1");
                }
                focusTarget.focus({ preventScroll: true });
            }
        }

        generalPreferencesFocusButtons.forEach((button) => {
            button.addEventListener("click", () => {
                revealPreferenceFocus(button.dataset.generalPreferencesFocus || "manual");
            });
        });

        return {
            renderPreferencePresetButtons: preferenceViews.renderPreferencePresetButtons,
            renderPreferenceBundleButtons: preferenceViews.renderPreferenceBundleButtons,
            renderKnownPreferenceButtons: preferenceViews.renderKnownPreferenceButtons,
            renderKnownPreferenceOptions: preferenceViews.renderKnownPreferenceOptions,
            appendPreferenceDraft: preferenceState.appendPreferenceDraft,
            applyPreferencesFromWizard: preferenceState.applyPreferencesFromWizard,
            syncWizardPreferencesFromEditor: preferenceState.syncWizardPreferencesFromEditor,
            bindAddButtonListeners: preferenceViews.bindAddButtonListeners,
        };
    }

    window.BPMProfilesPreferences = { create };
})();
