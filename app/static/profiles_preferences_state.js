(() => {
    function create({
        documentRef = document,
        wizardPreferenceSections = [],
        wizardKnownPreferenceIndex = {},
        wizardPreferenceEntryManagedKeys = [],
        wizardPreferenceViews = {},
        dependencies = {},
        state = {},
        rowHelpers = {},
    }) {
        const {
            t,
            cloneJsonValue,
            stablePreferenceValueKey,
            parsePreferenceValue,
            normalizePreferenceName,
            fromEditorValue,
            toEditorValue,
            setStatus,
        } = dependencies;
        const { getEditor = () => null, setCurrentRaw = () => {} } = state;
        const {
            readPreferenceFieldsFromRow,
            getPreferenceFieldInput,
        } = rowHelpers;

        let wizardPreferenceDrafts = [];
        let wizardPreferenceDraftCounter = 0;
        let wizardPreferenceSectionOverrides = {};
        let skipPreferenceDraftSyncOnce = false;
        let renderPreferenceDrafts = () => {};

        function connectViews(callbacks = {}) {
            renderPreferenceDrafts = callbacks.renderPreferenceDrafts || renderPreferenceDrafts;
        }

        function getDrafts() {
            return wizardPreferenceDrafts;
        }

        function resolvePreferenceSection(prefName) {
            if (typeof prefName !== "string" || !prefName.trim()) {
                return wizardPreferenceSections[0]?.id || "general";
            }

            const trimmed = prefName.trim();
            if (wizardPreferenceSectionOverrides[trimmed]) {
                return wizardPreferenceSectionOverrides[trimmed];
            }

            const matchedSection = wizardPreferenceSections.find((section) =>
                Array.isArray(section.prefixes)
                && section.prefixes.some((prefix) => trimmed === prefix || trimmed.startsWith(prefix))
            );

            return matchedSection?.id || wizardPreferenceSections[0]?.id || "general";
        }

        function getKnownPreference(prefName) {
            const trimmed = typeof prefName === "string" ? prefName.trim() : "";
            return trimmed ? wizardKnownPreferenceIndex[trimmed] || null : null;
        }

        function createKnownPreferenceSeed(knownPreference) {
            const seed = {};
            if (!knownPreference || typeof knownPreference !== "object") return seed;
            if (knownPreference.status) seed.Status = knownPreference.status;
            if (knownPreference.type) seed.Type = knownPreference.type;
            if (knownPreference.can_autofill && knownPreference.value !== null) {
                seed.Value = cloneJsonValue(knownPreference.value, knownPreference.value);
            }
            return seed;
        }

        function createPreferenceBundleSeed(item) {
            return {
                Status: item.status || "default",
                Type: item.type || "",
                Value: cloneJsonValue(item.value, item.value),
            };
        }

        function valuesMatchPreferenceBundleItem(currentEntry, bundleItem) {
            const expectedStatus = bundleItem.status || "default";
            const expectedType = bundleItem.type || "";

            if (!currentEntry) return false;
            if ((currentEntry.status || "default") !== expectedStatus) return false;
            if (expectedType && currentEntry.type && currentEntry.type !== expectedType) return false;
            if (expectedStatus === "clear") return true;
            if (!currentEntry.hasValue) return false;
            return stablePreferenceValueKey(currentEntry.value) === stablePreferenceValueKey(bundleItem.value);
        }

        function createPreferenceDraft(sectionId, sourceName = "", sourceEntry = {}) {
            wizardPreferenceDraftCounter += 1;
            return {
                id: `preference-${wizardPreferenceDraftCounter}`,
                section: sectionId || wizardPreferenceSections[0]?.id || "general",
                sourceName,
                seed: cloneJsonValue(sourceEntry, {}) || {},
            };
        }

        function collectCurrentPreferenceEntries() {
            const entries = {};

            wizardPreferenceSections.forEach((section) => {
                const view = wizardPreferenceViews[section.id];
                const rows = Array.from(view?.list?.querySelectorAll("[data-preference-row]") || []);

                rows.forEach((row) => {
                    const values = readPreferenceFieldsFromRow(row);
                    const prefName = normalizePreferenceName(values.name);
                    if (!prefName) return;

                    let parsedValue;
                    let hasValue = false;
                    if (values.status !== "clear" && values.value.trim()) {
                        const parsed = parsePreferenceValue(values.value, values.type, t);
                        parsedValue = parsed.ok ? parsed.value : values.value;
                        hasValue = true;
                    }

                    entries[prefName] = {
                        status: values.status || "default",
                        type: values.type || "",
                        hasValue,
                        value: parsedValue,
                    };
                });
            });

            return entries;
        }

        function getPreferenceBundleState(bundle) {
            const items = Array.isArray(bundle?.items) ? bundle.items : [];
            const currentEntries = collectCurrentPreferenceEntries();
            let matched = 0;
            let missing = 0;
            let conflicts = 0;

            items.forEach((item) => {
                const prefName = normalizePreferenceName(item?.pref);
                const currentEntry = prefName ? currentEntries[prefName] : null;
                if (!currentEntry) {
                    missing += 1;
                    return;
                }
                if (valuesMatchPreferenceBundleItem(currentEntry, item)) {
                    matched += 1;
                } else {
                    conflicts += 1;
                }
            });

            const total = items.length;
            const stateValue = conflicts > 0
                ? "conflict"
                : matched === total && total > 0
                    ? "applied"
                    : matched > 0
                        ? "partial"
                        : "missing";

            return {
                state: stateValue,
                total,
                matched,
                missing,
                conflicts,
            };
        }

        function formatPreferenceBundleStatus(bundleState) {
            if (bundleState.state === "applied") {
                return t("profiles.wizard_preferences_bundle_state_applied");
            }
            if (bundleState.state === "partial") {
                return t("profiles.wizard_preferences_bundle_state_partial")
                    .replace("{matched}", String(bundleState.matched))
                    .replace("{total}", String(bundleState.total));
            }
            if (bundleState.state === "conflict") {
                return t("profiles.wizard_preferences_bundle_state_conflict")
                    .replace("{conflicts}", String(bundleState.conflicts));
            }
            return t("profiles.wizard_preferences_bundle_state_missing");
        }

        function getKnownPreferenceState(knownPreference) {
            const prefName = normalizePreferenceName(knownPreference?.pref);
            const currentEntry = prefName ? collectCurrentPreferenceEntries()[prefName] : null;
            const expectedStatus = knownPreference?.status || "default";
            const expectedType = knownPreference?.type || "";
            const hasSuggestedValue = Boolean(knownPreference?.can_autofill && knownPreference?.value !== null);

            if (!currentEntry) {
                return { state: "missing" };
            }

            const statusMatches = (currentEntry.status || "default") === expectedStatus;
            const typeMatches = !expectedType || !currentEntry.type || currentEntry.type === expectedType;

            if (hasSuggestedValue) {
                const valueMatches = currentEntry.hasValue
                    && stablePreferenceValueKey(currentEntry.value) === stablePreferenceValueKey(knownPreference.value);
                return { state: statusMatches && typeMatches && valueMatches ? "suggested" : "overridden" };
            }

            return { state: statusMatches && typeMatches ? "present" : "overridden" };
        }

        function formatKnownPreferenceStatus(knownState) {
            if (knownState.state === "suggested") {
                return t("profiles.wizard_preferences_known_state_suggested");
            }
            if (knownState.state === "present") {
                return t("profiles.wizard_preferences_known_state_present");
            }
            if (knownState.state === "overridden") {
                return t("profiles.wizard_preferences_known_state_overridden");
            }
            return t("profiles.wizard_preferences_known_state_missing");
        }

        function syncPreferenceDraftSnapshotsFromDom() {
            wizardPreferenceDrafts = wizardPreferenceDrafts.map((draft) => {
                const view = wizardPreferenceViews[draft.section];
                const row = view?.list?.querySelector(`[data-preference-row="${draft.id}"]`);
                if (!row) return draft;

                const values = readPreferenceFieldsFromRow(row);
                const nextSeed = cloneJsonValue(draft.seed, {}) || {};
                nextSeed.Status = values.status || "default";
                if (values.type) {
                    nextSeed.Type = values.type;
                } else {
                    delete nextSeed.Type;
                }
                if (values.status !== "clear" && values.value.trim()) {
                    const parsed = parsePreferenceValue(values.value, values.type, t);
                    nextSeed.Value = parsed.ok ? parsed.value : values.value;
                } else {
                    delete nextSeed.Value;
                }

                return {
                    ...draft,
                    sourceName: values.name,
                    seed: nextSeed,
                };
            });
        }

        function findPreferenceDraftIndex(prefName) {
            const normalizedName = normalizePreferenceName(prefName);
            if (!normalizedName) return -1;

            return wizardPreferenceDrafts.findIndex((draft) =>
                normalizePreferenceName(draft.sourceName) === normalizedName
            );
        }

        function upsertPreferenceDraft(sectionId, sourceName = "", sourceEntry = {}) {
            const normalizedName = normalizePreferenceName(sourceName);
            const nextSection = sectionId || resolvePreferenceSection(normalizedName);
            const nextSeed = cloneJsonValue(sourceEntry, {}) || {};

            if (!normalizedName) {
                wizardPreferenceDrafts.push(createPreferenceDraft(nextSection, sourceName, nextSeed));
                return wizardPreferenceDrafts[wizardPreferenceDrafts.length - 1] || null;
            }

            const existingIndex = findPreferenceDraftIndex(normalizedName);
            if (existingIndex >= 0) {
                wizardPreferenceDrafts[existingIndex] = {
                    ...wizardPreferenceDrafts[existingIndex],
                    section: nextSection,
                    sourceName: normalizedName,
                    seed: nextSeed,
                };
                return wizardPreferenceDrafts[existingIndex];
            }

            wizardPreferenceDrafts.push(createPreferenceDraft(nextSection, normalizedName, nextSeed));
            return wizardPreferenceDrafts[wizardPreferenceDrafts.length - 1] || null;
        }

        function updatePreferenceSectionOverrides() {
            wizardPreferenceSectionOverrides = wizardPreferenceDrafts.reduce((acc, draft) => {
                const view = wizardPreferenceViews[draft.section];
                const row = view?.list?.querySelector(`[data-preference-row="${draft.id}"]`);
                const nameValue = row ? readPreferenceFieldsFromRow(row).name : draft.sourceName;
                if (nameValue) acc[nameValue] = draft.section;
                return acc;
            }, {});
        }

        function removeDraft(draftId) {
            wizardPreferenceDrafts = wizardPreferenceDrafts.filter((item) => item.id !== draftId);
        }

        function syncPreferenceDraftsFromPolicy(preferences) {
            const nextDrafts = Object.entries(preferences || {})
                .filter(([, entry]) => entry && typeof entry === "object" && !Array.isArray(entry))
                .map(([prefName, entry]) => createPreferenceDraft(resolvePreferenceSection(prefName), prefName, entry));

            wizardPreferenceDrafts = nextDrafts;
            updatePreferenceSectionOverrides();
            renderPreferenceDrafts(false);
        }

        function appendPreferenceBundle(sectionId, bundle) {
            if (!bundle || !Array.isArray(bundle.items) || !bundle.items.length) return;

            syncPreferenceDraftSnapshotsFromDom();
            bundle.items.forEach((item) => {
                if (!item?.pref) return;
                upsertPreferenceDraft(sectionId, item.pref, createPreferenceBundleSeed(item));
            });

            updatePreferenceSectionOverrides();
            renderPreferenceDrafts(false);
            applyPreferencesFromWizard();

            const view = wizardPreferenceViews[sectionId];
            const latestRow = view?.list?.querySelector("[data-preference-row]:last-child");
            getPreferenceFieldInput(latestRow, "value")?.focus();
        }

        function appendPreferenceDraft(sectionId, sourceName = "", sourceEntry = {}) {
            syncPreferenceDraftSnapshotsFromDom();
            const draft = upsertPreferenceDraft(sectionId, sourceName, sourceEntry);
            updatePreferenceSectionOverrides();
            renderPreferenceDrafts(false);

            const view = draft ? wizardPreferenceViews[draft.section] : wizardPreferenceViews[sectionId];
            const latestRow = view?.list?.querySelector(`[data-preference-row="${draft?.id || ""}"]`)
                || view?.list?.querySelector("[data-preference-row]:last-child");
            const focusTarget = sourceName
                ? (latestRow ? getPreferenceFieldInput(latestRow, "value") : null)
                : latestRow?.querySelector('[data-preference-field="name"]');
            focusTarget?.focus();
            applyPreferencesFromWizard();
        }

        function buildPreferencesFromWizard() {
            const nextPreferences = {};
            const errors = [];

            wizardPreferenceDrafts.forEach((draft) => {
                const view = wizardPreferenceViews[draft.section];
                const row = view?.list?.querySelector(`[data-preference-row="${draft.id}"]`);
                if (!row) return;

                const values = readPreferenceFieldsFromRow(row);
                const hasContent = values.name || values.value.trim() || values.type || values.status !== "default";
                if (!hasContent) return;

                if (!values.name) {
                    errors.push(t("profiles.wizard_preferences_error_name"));
                    return;
                }

                const nextEntry = cloneJsonValue(draft.seed, {}) || {};
                wizardPreferenceEntryManagedKeys.forEach((key) => delete nextEntry[key]);
                nextEntry.Status = values.status || "default";

                if (values.status !== "clear") {
                    if (!values.value.trim()) {
                        errors.push(t("profiles.wizard_preferences_error_value"));
                        return;
                    }

                    const parsed = parsePreferenceValue(values.value, values.type, t);
                    if (!parsed.ok) {
                        errors.push(parsed.message);
                        return;
                    }
                    nextEntry.Value = parsed.value;
                }

                if (values.type) {
                    nextEntry.Type = values.type;
                }

                nextPreferences[values.name] = nextEntry;
            });

            return { nextPreferences, errors };
        }

        function applyPreferencesFromWizard() {
            const editor = getEditor();
            if (!editor) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const { nextPreferences, errors } = buildPreferencesFromWizard();

                if (errors.length) {
                    setStatus(errors[0], "warn");
                    return;
                }

                if (Object.keys(nextPreferences).length) {
                    normalized.Preferences = nextPreferences;
                } else {
                    delete normalized.Preferences;
                }

                updatePreferenceSectionOverrides();
                setCurrentRaw(normalized);
                skipPreferenceDraftSyncOnce = true;
                editor.setValue(toEditorValue(normalized, mode));
                setStatus(t("profiles.wizard_preferences_applied"), "info");
            } catch (e) {
                skipPreferenceDraftSyncOnce = false;
                setStatus(t("profiles.error_wizard_preferences").replace("{detail}", e.message || e), "error");
            }
        }

        function syncWizardPreferencesFromEditor() {
            const editor = getEditor();
            if (!editor) return;

            try {
                const parsed = fromEditorValue(editor.getValue(), documentRef.getElementById("mode").value);
                const normalized = parsed && typeof parsed === "object" ? parsed : {};
                const preferences = normalized.Preferences && typeof normalized.Preferences === "object"
                    ? normalized.Preferences
                    : {};

                Object.values(wizardPreferenceViews).forEach((view) => {
                    if (view?.add) view.add.disabled = false;
                });
                if (skipPreferenceDraftSyncOnce) {
                    skipPreferenceDraftSyncOnce = false;
                    return;
                }
                syncPreferenceDraftsFromPolicy(preferences);
            } catch {
                skipPreferenceDraftSyncOnce = false;
                wizardPreferenceDrafts = [];
                Object.values(wizardPreferenceViews).forEach((view) => {
                    if (view?.add) view.add.disabled = true;
                    if (view?.list) view.list.innerHTML = "";
                    if (view?.empty) view.empty.hidden = false;
                });
            }
        }

        return {
            connectViews,
            getDrafts,
            getKnownPreference,
            createKnownPreferenceSeed,
            getPreferenceBundleState,
            formatPreferenceBundleStatus,
            getKnownPreferenceState,
            formatKnownPreferenceStatus,
            syncPreferenceDraftSnapshotsFromDom,
            updatePreferenceSectionOverrides,
            removeDraft,
            appendPreferenceBundle,
            appendPreferenceDraft,
            applyPreferencesFromWizard,
            syncWizardPreferencesFromEditor,
        };
    }

    window.BPMProfilesPreferenceState = { create };
})();
