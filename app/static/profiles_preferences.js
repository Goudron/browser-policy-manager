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
