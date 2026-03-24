(() => {
    function create({
        documentRef = document,
        elements = {},
        searchEnginePresets = {},
        wizardSearchEngineItemManagedKeys = [],
        dependencies = {},
    }) {
        const {
            t,
            cloneJsonValue,
            escapeHtml,
            setStatus,
            applyNetworkFromWizard,
        } = dependencies;
        const {
            addButtonEl,
            emptyEl,
            listEl,
            templateEl,
            presetButtons = [],
        } = elements;

        let drafts = [];
        let draftCounter = 0;
        let uiDisabled = false;
        let skipSyncOnce = false;

        function createDraft(source = {}) {
            draftCounter += 1;
            return {
                id: `search-engine-${draftCounter}`,
                seed: cloneJsonValue(source, {}) || {},
                values: {},
            };
        }

        function readManagedFieldsFromRow(row) {
            const read = (field) => {
                const input = row.querySelector(`[data-search-engine-field="${field}"]`);
                return input ? input.value.trim() : "";
            };

            return {
                Name: read("Name"),
                URLTemplate: read("URLTemplate"),
                Method: read("Method"),
                IconURL: read("IconURL"),
                Alias: read("Alias"),
                Description: read("Description"),
                PostData: read("PostData"),
                SuggestURLTemplate: read("SuggestURLTemplate"),
                Encoding: read("Encoding"),
            };
        }

        function syncDraftSnapshotsFromDom() {
            if (!listEl) return;

            drafts.forEach((draft) => {
                const row = listEl.querySelector(`[data-search-engine-row="${draft.id}"]`);
                if (!row) return;
                draft.values = readManagedFieldsFromRow(row);
            });
        }

        function collectCurrentEntries() {
            if (!listEl) return [];

            return Array.from(listEl.querySelectorAll("[data-search-engine-row]"))
                .map((row) => readManagedFieldsFromRow(row))
                .filter((entry) => Object.values(entry).some(Boolean));
        }

        function getPresetState(preset) {
            const entries = collectCurrentEntries();
            const presetKeys = wizardSearchEngineItemManagedKeys.filter((key) => Boolean(preset?.[key]));
            const normalizedName = String(preset?.Name || "").trim();
            const normalizedUrl = String(preset?.URLTemplate || "").trim();
            let partialMatches = 0;
            let conflictCandidate = false;

            for (const entry of entries) {
                const sameIdentity = (
                    (normalizedName && entry.Name === normalizedName)
                    || (normalizedUrl && entry.URLTemplate === normalizedUrl)
                );
                if (!sameIdentity) continue;

                let matchedKeys = 0;
                let comparedKeys = 0;
                presetKeys.forEach((key) => {
                    comparedKeys += 1;
                    if ((entry[key] || "") === (preset[key] || "")) {
                        matchedKeys += 1;
                    }
                });

                if (comparedKeys > 0 && matchedKeys === comparedKeys) {
                    return { state: "applied" };
                }
                if (matchedKeys > 0) {
                    partialMatches = Math.max(partialMatches, matchedKeys);
                } else {
                    conflictCandidate = true;
                }
            }

            if (partialMatches > 0) return { state: "partial" };
            if (conflictCandidate) return { state: "conflict" };
            return { state: "missing" };
        }

        function formatPresetStatus(presetState) {
            if (presetState.state === "applied") {
                return t("profiles.wizard_search_preset_state_applied", "Preset matches current engine");
            }
            if (presetState.state === "partial") {
                return t("profiles.wizard_search_preset_state_partial", "Preset partially applied");
            }
            if (presetState.state === "conflict") {
                return t("profiles.wizard_search_preset_state_conflict", "Preset differs from current engine");
            }
            return t("profiles.wizard_search_preset_state_missing", "Preset not added yet");
        }

        function renderPresetButtonStates() {
            presetButtons.forEach((button) => {
                const presetKey = button.dataset.searchEnginePreset;
                const preset = presetKey ? searchEnginePresets[presetKey] : null;
                const presetState = getPresetState(preset);
                let statusEl = button.querySelector("[data-search-engine-preset-status]");

                button.classList.remove(
                    "wizard-search-engine-preset--applied",
                    "wizard-search-engine-preset--partial",
                    "wizard-search-engine-preset--conflict",
                );
                if (presetState.state === "applied") button.classList.add("wizard-search-engine-preset--applied");
                if (presetState.state === "partial") button.classList.add("wizard-search-engine-preset--partial");
                if (presetState.state === "conflict") button.classList.add("wizard-search-engine-preset--conflict");

                if (!statusEl) {
                    statusEl = documentRef.createElement("span");
                    statusEl.className = "wizard-search-engine-preset-copy wizard-search-engine-preset-status";
                    statusEl.dataset.searchEnginePresetStatus = "true";
                    button.appendChild(statusEl);
                }
                statusEl.textContent = formatPresetStatus(presetState);
            });
        }

        function setRowValue(row, field, value) {
            const input = row.querySelector(`[data-search-engine-field="${field}"]`);
            if (input) input.value = typeof value === "string" ? value : "";
        }

        function updateRowPresentation(row, index) {
            const values = readManagedFieldsFromRow(row);
            const nameValue = values.Name;
            const urlValue = values.URLTemplate;
            const titleEl = row.querySelector("[data-search-engine-title]");
            const metaEl = row.querySelector("[data-search-engine-meta]");
            const summaryEl = row.querySelector("[data-search-engine-summary]");
            const warningEl = row.querySelector("[data-search-engine-warning]");
            const hasSeedPayload = row.dataset.searchEngineHasSeed === "true";
            const hasManagedContent = wizardSearchEngineItemManagedKeys.some((key) => Boolean(values[key]));
            const hasContent = hasManagedContent || hasSeedPayload;
            const missingRequired = [
                !nameValue ? t("profiles.wizard_search_engine_name_label", "Engine name") : null,
                !urlValue ? t("profiles.wizard_search_engine_url_label", "Search URL template") : null,
            ].filter(Boolean);

            if (titleEl) {
                titleEl.textContent = nameValue || `${t("profiles.wizard_search_engine_card_title", "Search engine")} ${index + 1}`;
            }
            if (metaEl) {
                metaEl.textContent = urlValue
                    || t("profiles.wizard_search_engine_card_meta", "Writes one item into SearchEngines.Add.");
            }
            if (summaryEl) {
                if (!hasContent) {
                    summaryEl.textContent = t(
                        "profiles.wizard_search_engine_summary_default",
                        "GET by default. Add the required fields to complete this engine.",
                    );
                } else {
                    const summaryParts = [values.Method || "GET"];
                    if (values.Alias) {
                        summaryParts.push(`${t("profiles.wizard_search_engine_summary_keyword", "keyword")} ${values.Alias}`);
                    }
                    if (values.Encoding) summaryParts.push(values.Encoding);
                    if (values.SuggestURLTemplate) {
                        summaryParts.push(t("profiles.wizard_search_engine_summary_suggest", "suggestions"));
                    }
                    if (values.PostData) {
                        summaryParts.push(t("profiles.wizard_search_engine_summary_post", "POST data"));
                    }
                    summaryEl.textContent = summaryParts.join(" • ");
                }
            }
            if (warningEl) {
                warningEl.hidden = !hasContent || missingRequired.length === 0;
                warningEl.textContent = t(
                    "profiles.wizard_search_engine_warning_required",
                    "Required for a valid engine: Name and Search URL template.",
                );
            }

            row.classList.toggle("wizard-search-engine-card--invalid", hasContent && missingRequired.length > 0);
            ["Name", "URLTemplate"].forEach((field) => {
                const input = row.querySelector(`[data-search-engine-field="${field}"]`);
                const invalid = hasContent && !values[field];
                if (!input) return;
                input.classList.toggle("input-invalid", invalid);
                input.setAttribute("aria-invalid", invalid ? "true" : "false");
            });
        }

        function applyRowTranslations(row) {
            const labels = {
                Name: t("profiles.wizard_search_engine_name_label", "Engine name"),
                URLTemplate: t("profiles.wizard_search_engine_url_label", "Search URL template"),
                Method: t("profiles.wizard_search_engine_method_label", "Request method"),
                IconURL: t("profiles.wizard_search_engine_icon_label", "Icon URL"),
                Alias: t("profiles.wizard_search_engine_alias_label", "Alias keyword"),
                Description: t("profiles.wizard_search_engine_description_label", "Description"),
                PostData: t("profiles.wizard_search_engine_post_data_label", "POST payload"),
                SuggestURLTemplate: t("profiles.wizard_search_engine_suggest_label", "Suggestions URL template"),
                Encoding: t("profiles.wizard_search_engine_encoding_label", "Query encoding"),
            };
            const placeholders = {
                Name: t("profiles.wizard_search_engine_name_placeholder", "Example Search"),
                URLTemplate: t("profiles.wizard_search_engine_url_placeholder", "https://www.example.org/search?q={searchTerms}"),
                IconURL: t("profiles.wizard_search_engine_icon_placeholder", "https://www.example.org/favicon.ico"),
                Alias: t("profiles.wizard_search_engine_alias_placeholder", "example"),
                Description: t("profiles.wizard_search_engine_description_placeholder", "Internal knowledge base search"),
                PostData: t("profiles.wizard_search_engine_post_data_placeholder", "q={searchTerms}&source=firefox"),
                SuggestURLTemplate: t("profiles.wizard_search_engine_suggest_placeholder", "https://www.example.org/suggest?q={searchTerms}"),
                Encoding: t("profiles.wizard_search_engine_encoding_placeholder", "UTF-8"),
            };

            row.querySelectorAll("[data-search-engine-label]").forEach((labelEl) => {
                const key = labelEl.dataset.searchEngineLabel;
                if (key && labels[key]) labelEl.textContent = labels[key];
            });
            row.querySelectorAll("[data-search-engine-field]").forEach((input) => {
                const field = input.dataset.searchEngineField;
                if (field && placeholders[field]) input.placeholder = placeholders[field];
            });

            const methodEl = row.querySelector('[data-search-engine-field="Method"]');
            if (methodEl?.options?.length >= 3) {
                methodEl.options[0].textContent = t("profiles.wizard_search_engine_method_default", "GET (default)");
                methodEl.options[1].textContent = t("profiles.wizard_search_engine_method_get", "GET");
                methodEl.options[2].textContent = t("profiles.wizard_search_engine_method_post", "POST");
            }

            const removeButton = row.querySelector("[data-search-engine-remove]");
            if (removeButton) {
                removeButton.textContent = t("profiles.wizard_search_engine_remove", "Remove");
            }
        }

        function renderDrafts(disabled = false) {
            if (!listEl || !templateEl) return;

            uiDisabled = disabled;
            listEl.innerHTML = "";
            if (emptyEl) emptyEl.hidden = drafts.length > 0;
            if (addButtonEl) addButtonEl.disabled = disabled;

            drafts.forEach((draft, index) => {
                const fragment = templateEl.content.cloneNode(true);
                const row = fragment.querySelector("[data-search-engine-row]");
                const source = draft.values && Object.keys(draft.values).length ? draft.values : draft.seed || {};

                row.dataset.searchEngineRow = draft.id;
                row.dataset.searchEngineHasSeed = Object.keys(draft.seed || {}).length ? "true" : "false";
                setRowValue(row, "Name", source.Name);
                setRowValue(row, "URLTemplate", source.URLTemplate);
                setRowValue(row, "Method", source.Method);
                setRowValue(row, "IconURL", source.IconURL);
                setRowValue(row, "Alias", source.Alias);
                setRowValue(row, "Description", source.Description);
                setRowValue(row, "PostData", source.PostData);
                setRowValue(row, "SuggestURLTemplate", source.SuggestURLTemplate);
                setRowValue(row, "Encoding", source.Encoding);
                applyRowTranslations(row);
                updateRowPresentation(row, index);

                row.querySelectorAll("input, select, textarea, button").forEach((element) => {
                    element.disabled = disabled;
                });

                row.querySelectorAll("[data-search-engine-field]").forEach((input) => {
                    input.addEventListener("input", () => {
                        updateRowPresentation(row, index);
                        renderPresetButtonStates();
                        applyNetworkFromWizard();
                    });
                    input.addEventListener("change", () => {
                        updateRowPresentation(row, index);
                        renderPresetButtonStates();
                        applyNetworkFromWizard();
                    });
                });

                row.querySelector("[data-search-engine-remove]")?.addEventListener("click", () => {
                    syncDraftSnapshotsFromDom();
                    drafts = drafts.filter((item) => item.id !== draft.id);
                    renderDrafts(false);
                    renderPresetButtonStates();
                    applyNetworkFromWizard();
                });

                listEl.appendChild(fragment);
            });

            renderPresetButtonStates();
        }

        function syncDraftsFromPolicy(addEntries) {
            const entries = Array.isArray(addEntries)
                ? addEntries.filter((item) => item && typeof item === "object" && !Array.isArray(item))
                : [];
            drafts = entries.map((entry) => createDraft(entry));
            renderDrafts(false);
        }

        function buildAddItemsFromWizard() {
            if (!listEl) return [];

            return drafts
                .map((draft) => {
                    const row = listEl.querySelector(`[data-search-engine-row="${draft.id}"]`);
                    const nextItem = cloneJsonValue(draft.seed, {}) || {};

                    if (!row) return null;

                    wizardSearchEngineItemManagedKeys.forEach((key) => delete nextItem[key]);
                    const values = readManagedFieldsFromRow(row);

                    if (values.Name) nextItem.Name = values.Name;
                    if (values.URLTemplate) nextItem.URLTemplate = values.URLTemplate;
                    if (values.Method) nextItem.Method = values.Method;
                    if (values.IconURL) nextItem.IconURL = values.IconURL;
                    if (values.Alias) nextItem.Alias = values.Alias;
                    if (values.Description) nextItem.Description = values.Description;
                    if (values.PostData) nextItem.PostData = values.PostData;
                    if (values.SuggestURLTemplate) nextItem.SuggestURLTemplate = values.SuggestURLTemplate;
                    if (values.Encoding) nextItem.Encoding = values.Encoding;

                    return Object.keys(nextItem).length ? nextItem : null;
                })
                .filter(Boolean);
        }

        function appendDraft(source = {}) {
            syncDraftSnapshotsFromDom();
            drafts.push(createDraft(source));
            renderDrafts(false);
            applyNetworkFromWizard();
            const latestRow = listEl?.querySelector("[data-search-engine-row]:last-child");
            latestRow?.querySelector('[data-search-engine-field="Name"]')?.focus();
        }

        function applyPreset(presetKey) {
            const preset = searchEnginePresets[presetKey];
            if (!preset) return;

            appendDraft(preset);
            setStatus(t("profiles.wizard_search_preset_applied", "Search engine preset added."), "info");
        }

        function rerenderForLocale() {
            syncDraftSnapshotsFromDom();
            renderDrafts(uiDisabled);
        }

        function markPendingSyncOnce() {
            skipSyncOnce = true;
        }

        function consumePendingSyncOnce() {
            if (!skipSyncOnce) return false;
            skipSyncOnce = false;
            return true;
        }

        function clearPendingSyncOnce() {
            skipSyncOnce = false;
        }

        return {
            syncDraftSnapshotsFromDom,
            renderDrafts,
            syncDraftsFromPolicy,
            buildAddItemsFromWizard,
            appendDraft,
            applyPreset,
            rerenderForLocale,
            markPendingSyncOnce,
            consumePendingSyncOnce,
            clearPendingSyncOnce,
        };
    }

    window.BPMProfilesSearchEngines = { create };
})();
