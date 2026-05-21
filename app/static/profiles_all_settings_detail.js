(() => {
    function create({
        documentRef = document,
        elements = {},
        dependencies = {},
        state = {},
        wizardPreferencesCatalog = {},
    }) {
        const {
            t,
            escapeHtml,
            normalizePreferenceName,
            serializePreferenceValue,
            serializePreferenceSelectValue,
            parsePreferenceValue,
            fromEditorValue,
            toEditorValue,
            readWizardSchemaSource,
            renderSchemaPolicyEditorCard,
            renderSchemaPolicyReviewState,
            onDocumentChange = () => {},
            setStatus,
        } = dependencies;
        const {
            allSettingsDetailPanelEl,
            allSettingsAddPreferenceEl,
        } = elements;
        const getEditor = state.getEditor || (() => null);
        const setCurrentRaw = state.setCurrentRaw || (() => {});
        let selectedEntry = null;

        function hasOwn(source, key) {
            return Boolean(source && Object.prototype.hasOwnProperty.call(source, key));
        }

        function formatDetailValue(value, configured) {
            if (!configured) return t("profiles.settings_list_value_not_configured");
            if (typeof value === "string") return value;
            try {
                return JSON.stringify(value, null, 2);
            } catch {
                return String(value);
            }
        }

        function formatJsonEditorValue(value, configured) {
            if (!configured) return "";
            try {
                return JSON.stringify(value, null, 2);
            } catch {
                return "";
            }
        }

        function getKnownPreference(prefName) {
            const knownPreferences = Array.isArray(wizardPreferencesCatalog.known_preferences)
                ? wizardPreferencesCatalog.known_preferences
                : [];
            return knownPreferences.find((item) => item?.pref === prefName) || null;
        }

        function getPreferenceNameFromEditor() {
            const nameInput = allSettingsDetailPanelEl?.querySelector("[data-settings-detail-pref-name]");
            if (!nameInput) return selectedEntry?.id || "";
            const normalizer = normalizePreferenceName || ((value) => String(value || "").trim());
            return normalizer(nameInput.value || "");
        }

        function issuePathLabel(issue) {
            return Array.isArray(issue?.path) && issue.path.length
                ? issue.path.join(".")
                : "";
        }

        function renderIssueList(entry) {
            const issues = Array.isArray(entry?.issues) ? entry.issues : [];
            if (!issues.length) {
                return `
                    <div class="all-settings-detail-validation all-settings-detail-validation--ok">
                        ${escapeHtml(t("profiles.settings_detail_validation_clear"))}
                    </div>
                `;
            }

            return `
                <div class="all-settings-detail-validation all-settings-detail-validation--error">
                    <div class="field-label">${escapeHtml(t("profiles.settings_detail_validation_title"))}</div>
                    <ul class="all-settings-detail-issues">
                        ${issues.map((issue) => `
                            <li>
                                ${issuePathLabel(issue) ? `<span>${escapeHtml(issuePathLabel(issue))}</span>` : ""}
                                ${escapeHtml(issue?.message || t("profiles.settings_detail_validation_unknown"))}
                            </li>
                        `).join("")}
                    </ul>
                </div>
            `;
        }

        function detailBadge(label, tone = "neutral") {
            return `<span class="all-settings-detail-badge" data-tone="${escapeHtml(tone)}">${escapeHtml(label)}</span>`;
        }

        function renderBadges(entry) {
            const badges = [
                detailBadge(entry.kindLabel),
                detailBadge(entry.categoryLabel),
                detailBadge(
                    entry.configured
                        ? t("profiles.settings_list_state_configured")
                        : t("profiles.settings_list_state_available"),
                    entry.configured ? "configured" : "neutral",
                ),
            ];

            if (entry.guided) {
                badges.push(detailBadge(t("profiles.settings_filter_guided_covered"), "accent"));
            } else {
                badges.push(detailBadge(t("profiles.settings_filter_all_settings_only")));
            }
            if (entry.invalid) badges.push(detailBadge(t("profiles.settings_filter_invalid"), "error"));
            if (entry.deprecated) badges.push(detailBadge(t("profiles.settings_filter_deprecated"), "warn"));
            if (entry.rawFallback) badges.push(detailBadge(t("profiles.settings_filter_raw"), "warn"));
            if (entry.unknown) badges.push(detailBadge(t("profiles.settings_filter_unknown"), "warn"));
            return badges.join("");
        }

        function renderActionBar(entry, { supportsOpen = true, supportsReset = true, supportsRemove = true } = {}) {
            return `
                <div class="all-settings-detail-actions">
                    ${supportsOpen && entry.target ? `
                        <button
                            type="button"
                            class="button-base ghost-button"
                            data-settings-search-target="${escapeHtml(entry.target)}">
                            ${escapeHtml(t("profiles.settings_detail_open_location"))}
                        </button>
                    ` : ""}
                    ${supportsReset ? `
                        <button type="button" class="button-base ghost-button" data-settings-detail-reset>
                            ${escapeHtml(t("profiles.settings_detail_reset_editor"))}
                        </button>
                    ` : ""}
                    ${supportsRemove ? `
                        <button
                            type="button"
                            class="button-base danger-button"
                            data-settings-detail-remove
                            ${entry.configured ? "" : "disabled"}>
                            ${escapeHtml(t("profiles.settings_detail_remove"))}
                        </button>
                    ` : ""}
                </div>
            `;
        }

        function renderPolicyMetadata(entry) {
            const item = entry.schemaItem || {};
            const rows = [
                [
                    t("profiles.settings_detail_meta_widget"),
                    item.widget ? t(`profiles.wizard_shell_widget_${item.widget}`) : "",
                ],
                [
                    t("profiles.settings_detail_meta_complexity"),
                    item.complexity === "basic"
                        ? t("profiles.wizard_shell_meta_basic")
                        : item.complexity
                            ? t("profiles.wizard_shell_meta_advanced")
                            : "",
                ],
                [
                    t("profiles.settings_detail_meta_support"),
                    item.support_level
                        ? t(`profiles.settings_detail_support_${item.support_level}`)
                        : "",
                ],
            ].filter(([, value]) => value);

            if (!rows.length) return "";
            return `
                <dl class="all-settings-detail-meta">
                    ${rows.map(([label, value]) => `
                        <div>
                            <dt>${escapeHtml(label)}</dt>
                            <dd>${escapeHtml(value)}</dd>
                        </div>
                    `).join("")}
                </dl>
            `;
        }

        function renderPolicyEditor(entry, sourceData) {
            if (entry.schemaItem?.inline_editor) {
                return renderSchemaPolicyEditorCard(entry.schemaItem, sourceData?.[entry.id], false);
            }

            return `
                <div class="all-settings-detail-raw-editor">
                    <label class="wizard-field-full">
                        <div class="field-label mb-1">${escapeHtml(t("profiles.settings_detail_raw_value"))}</div>
                        <textarea class="soft-input" rows="8" data-settings-detail-raw-value>${escapeHtml(
                            formatJsonEditorValue(sourceData?.[entry.id], entry.configured),
                        )}</textarea>
                    </label>
                    <button type="button" class="button-base primary-button" data-settings-detail-apply-raw>
                        ${escapeHtml(t("profiles.settings_detail_apply"))}
                    </button>
                </div>
            `;
        }

        function renderPolicyDetail(entry, sourceData) {
            return `
                <div class="all-settings-detail-head">
                    <div>
                        <div class="all-settings-detail-key">${escapeHtml(entry.label)}</div>
                        <div class="all-settings-detail-badges">${renderBadges(entry)}</div>
                    </div>
                    ${renderActionBar(entry)}
                </div>
                ${renderPolicyMetadata(entry)}
                <div class="all-settings-detail-current">
                    <div class="field-label">${escapeHtml(t("profiles.settings_detail_current_value"))}</div>
                    <pre>${escapeHtml(formatDetailValue(sourceData?.[entry.id], entry.configured))}</pre>
                </div>
                ${renderIssueList(entry)}
                <div class="all-settings-detail-editor">
                    ${renderPolicyEditor(entry, sourceData)}
                </div>
            `;
        }

        function getPreferenceSeed(entry, sourceData) {
            const preferences = sourceData?.Preferences && typeof sourceData.Preferences === "object"
                && !Array.isArray(sourceData.Preferences)
                ? sourceData.Preferences
                : {};
            const currentEntry = preferences[entry.id] && typeof preferences[entry.id] === "object"
                && !Array.isArray(preferences[entry.id])
                ? preferences[entry.id]
                : null;
            if (currentEntry) return currentEntry;

            const knownPreference = getKnownPreference(entry.id);
            const seed = {};
            if (knownPreference?.status) seed.Status = knownPreference.status;
            if (knownPreference?.type) seed.Type = knownPreference.type;
            if (knownPreference?.can_autofill && knownPreference.value !== null) {
                seed.Value = knownPreference.value;
            }
            return seed;
        }

        function getPreferenceValueOptions(knownPreference, effectiveType, currentValue) {
            if (Array.isArray(knownPreference?.value_options) && knownPreference.value_options.length) {
                const options = knownPreference.value_options.map((item) => ({
                    value: serializePreferenceSelectValue(item.value),
                    label: item.label_key ? t(item.label_key) : String(item.fallback || item.value),
                }));
                const currentSerialized = serializePreferenceSelectValue(currentValue);
                if (currentSerialized && !options.some((item) => item.value === currentSerialized)) {
                    options.push({
                        value: currentSerialized,
                        label: currentSerialized,
                    });
                }
                return options;
            }
            if (effectiveType === "boolean") {
                return [
                    { value: "true", label: t("profiles.wizard_preferences_boolean_true") },
                    { value: "false", label: t("profiles.wizard_preferences_boolean_false") },
                ];
            }
            return [];
        }

        function renderPreferenceEditor(entry, sourceData) {
            const seed = getPreferenceSeed(entry, sourceData);
            const knownPreference = getKnownPreference(entry.id);
            const currentStatus = seed.Status || "default";
            const currentType = seed.Type || knownPreference?.type || "";
            const currentValue = hasOwn(seed, "Value") ? seed.Value : "";
            const serializedValue = serializePreferenceValue(currentValue);
            const valueOptions = getPreferenceValueOptions(knownPreference, currentType, currentValue);
            const useSelect = valueOptions.length > 0;
            const valueDisabled = currentStatus === "clear";

            return `
                <div class="all-settings-detail-preference"
                    data-settings-detail-preference-editor
                    data-settings-detail-pref="${escapeHtml(entry.id)}"
                    data-settings-detail-new="${entry.isNewPreference ? "true" : "false"}"
                    data-settings-detail-known="${knownPreference ? "true" : "false"}">
                    <div class="wizard-grid">
                        ${entry.isNewPreference ? `
                            <label class="wizard-field-full">
                                <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_preferences_field_name"))}</div>
                                <input
                                    type="text"
                                    class="soft-input"
                                    list="wizard-preferences-known-list"
                                    data-settings-detail-pref-name
                                    data-i18n-placeholder="profiles.wizard_preferences_name_placeholder"
                                    placeholder="${escapeHtml(t("profiles.wizard_preferences_name_placeholder"))}" />
                            </label>
                        ` : ""}
                        <label>
                            <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_preferences_field_status"))}</div>
                            <select class="soft-input" data-settings-detail-pref-status>
                                <option value="default"${currentStatus === "default" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_preferences_status_default"))}</option>
                                <option value="locked"${currentStatus === "locked" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_preferences_status_locked"))}</option>
                                <option value="user"${currentStatus === "user" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_preferences_status_user"))}</option>
                                <option value="clear"${currentStatus === "clear" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_preferences_status_clear"))}</option>
                            </select>
                        </label>
                        <label>
                            <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_preferences_field_type"))}</div>
                            <select class="soft-input" data-settings-detail-pref-type>
                                <option value=""${!currentType ? " selected" : ""}>${escapeHtml(t("profiles.wizard_preferences_type_auto_option"))}</option>
                                <option value="boolean"${currentType === "boolean" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_preferences_type_boolean"))}</option>
                                <option value="number"${currentType === "number" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_preferences_type_number"))}</option>
                                <option value="string"${currentType === "string" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_preferences_type_string"))}</option>
                            </select>
                        </label>
                        <label class="wizard-field-full">
                            <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_preferences_field_value"))}</div>
                            <input
                                type="text"
                                class="soft-input"
                                value="${escapeHtml(serializedValue)}"
                                data-settings-detail-pref-value-input
                                ${useSelect ? "hidden disabled" : ""}
                                ${valueDisabled ? "disabled" : ""} />
                            <select
                                class="soft-input"
                                data-settings-detail-pref-value-select
                                ${useSelect ? "" : "hidden disabled"}
                                ${valueDisabled ? "disabled" : ""}>
                                <option value=""></option>
                                ${valueOptions.map((item) => `
                                    <option value="${escapeHtml(item.value)}"${serializePreferenceSelectValue(currentValue) === item.value ? " selected" : ""}>
                                        ${escapeHtml(item.label)}
                                    </option>
                                `).join("")}
                            </select>
                        </label>
                    </div>
                    <button type="button" class="button-base primary-button" data-settings-detail-apply-preference>
                        ${escapeHtml(t("profiles.settings_detail_apply"))}
                    </button>
                </div>
            `;
        }

        function renderPreferenceDetail(entry, sourceData) {
            const preferences = sourceData?.Preferences && typeof sourceData.Preferences === "object"
                && !Array.isArray(sourceData.Preferences)
                ? sourceData.Preferences
                : {};
            return `
                <div class="all-settings-detail-head">
                    <div>
                        <div class="all-settings-detail-key">${escapeHtml(entry.label)}</div>
                        <div class="all-settings-detail-badges">${renderBadges(entry)}</div>
                    </div>
                    ${renderActionBar(entry, {
                        supportsOpen: !entry.isNewPreference,
                        supportsReset: true,
                        supportsRemove: !entry.isNewPreference,
                    })}
                </div>
                <div class="all-settings-detail-current">
                    <div class="field-label">${escapeHtml(t("profiles.settings_detail_current_value"))}</div>
                    <pre>${escapeHtml(formatDetailValue(preferences[entry.id], entry.configured))}</pre>
                </div>
                ${renderIssueList(entry)}
                <div class="all-settings-detail-editor">
                    ${renderPreferenceEditor(entry, sourceData)}
                </div>
            `;
        }

        function renderNewPreference() {
            selectedEntry = {
                id: "__new_preference__",
                label: t("profiles.settings_preferences_add"),
                kind: "preference",
                kindLabel: t("profiles.settings_list_kind_preference"),
                categoryId: "raw-unmapped",
                categoryLabel: t("profiles.settings_preferences_title"),
                configured: false,
                guided: false,
                deprecated: false,
                rawFallback: false,
                unknown: false,
                invalid: false,
                isNewPreference: true,
                target: "",
                value: t("profiles.settings_list_value_not_configured"),
                issues: [],
            };
            render(selectedEntry);
            allSettingsDetailPanelEl?.querySelector("[data-settings-detail-pref-name]")?.focus();
        }

        function renderEmptyState() {
            if (!allSettingsDetailPanelEl) return;
            allSettingsDetailPanelEl.innerHTML = `
                <div class="wizard-shell-empty">
                    ${escapeHtml(t("profiles.settings_detail_empty"))}
                </div>
            `;
        }

        function render(entry = selectedEntry) {
            selectedEntry = entry || null;
            if (!allSettingsDetailPanelEl) return;
            if (!selectedEntry) {
                renderEmptyState();
                return;
            }

            const sourceState = readWizardSchemaSource();
            const sourceData = sourceState.ok && sourceState.data && typeof sourceState.data === "object"
                ? sourceState.data
                : {};
            allSettingsDetailPanelEl.dataset.settingsDetailKind = selectedEntry.kind;
            allSettingsDetailPanelEl.dataset.settingsDetailId = selectedEntry.id;
            allSettingsDetailPanelEl.innerHTML = selectedEntry.kind === "preference"
                ? renderPreferenceDetail(selectedEntry, sourceData)
                : renderPolicyDetail(selectedEntry, sourceData);
            allSettingsDetailPanelEl
                .querySelectorAll("[data-schema-policy-card]")
                .forEach((card) => renderSchemaPolicyReviewState(card));
        }

        function updateDocument(mutator) {
            try {
                const sourceState = readWizardSchemaSource();
                if (!sourceState.ok) {
                    setStatus(
                        t("profiles.settings_detail_apply_failed")
                            .replace("{detail}", t("profiles.validation_result_invalid")),
                        "error",
                    );
                    return false;
                }
                const normalized = sourceState.data && typeof sourceState.data === "object"
                    ? { ...sourceState.data }
                    : {};
                mutator(normalized);
                setCurrentRaw(normalized);

                const editor = getEditor();
                if (editor) {
                    const mode = documentRef.getElementById("mode")?.value || "json";
                    editor.setValue(toEditorValue(normalized, mode));
                } else {
                    onDocumentChange(normalized);
                }
                return true;
            } catch (error) {
                setStatus(t("profiles.settings_detail_apply_failed").replace("{detail}", error.message || error), "error");
                return false;
            }
        }

        function removeSelectedEntry() {
            if (!selectedEntry?.configured) return;
            const removed = updateDocument((document) => {
                if (selectedEntry.kind === "preference") {
                    const preferences = document.Preferences && typeof document.Preferences === "object"
                        && !Array.isArray(document.Preferences)
                        ? { ...document.Preferences }
                        : {};
                    delete preferences[selectedEntry.id];
                    if (Object.keys(preferences).length) {
                        document.Preferences = preferences;
                    } else {
                        delete document.Preferences;
                    }
                    return;
                }
                delete document[selectedEntry.id];
            });
            if (removed) setStatus(t("profiles.settings_detail_removed"), "info");
        }

        function applyRawPolicyValue() {
            if (!selectedEntry || selectedEntry.kind !== "policy") return;
            const textarea = allSettingsDetailPanelEl?.querySelector("[data-settings-detail-raw-value]");
            const rawValue = textarea?.value ?? "";
            let parsedValue;
            try {
                parsedValue = JSON.parse(rawValue);
            } catch {
                setStatus(t("profiles.settings_detail_raw_json_error"), "warn");
                return;
            }
            const applied = updateDocument((document) => {
                document[selectedEntry.id] = parsedValue;
            });
            if (applied) setStatus(t("profiles.settings_detail_applied"), "info");
        }

        function readPreferenceEditorValue() {
            const editorEl = allSettingsDetailPanelEl?.querySelector("[data-settings-detail-preference-editor]");
            if (!editorEl) return null;
            const name = getPreferenceNameFromEditor();
            const status = editorEl.querySelector("[data-settings-detail-pref-status]")?.value || "default";
            const type = editorEl.querySelector("[data-settings-detail-pref-type]")?.value || "";
            const textInput = editorEl.querySelector("[data-settings-detail-pref-value-input]");
            const selectInput = editorEl.querySelector("[data-settings-detail-pref-value-select]");
            const valueControl = selectInput && !selectInput.hidden ? selectInput : textInput;
            return {
                name,
                status,
                type,
                value: valueControl?.value || "",
            };
        }

        function applyPreferenceValue() {
            if (!selectedEntry || selectedEntry.kind !== "preference") return;
            const formValue = readPreferenceEditorValue();
            if (!formValue) return;
            const preferenceName = selectedEntry.isNewPreference ? formValue.name : selectedEntry.id;
            if (!preferenceName) {
                setStatus(t("profiles.wizard_preferences_error_name"), "warn");
                return;
            }
            if (formValue.status !== "clear" && !String(formValue.value || "").trim()) {
                setStatus(t("profiles.wizard_preferences_error_value"), "warn");
                return;
            }

            let nextValue;
            if (formValue.status !== "clear") {
                const parsed = parsePreferenceValue(formValue.value, formValue.type, t);
                if (!parsed.ok) {
                    setStatus(parsed.message, "warn");
                    return;
                }
                nextValue = parsed.value;
            }

            const applied = updateDocument((document) => {
                const preferences = document.Preferences && typeof document.Preferences === "object"
                    && !Array.isArray(document.Preferences)
                    ? { ...document.Preferences }
                    : {};
                const nextEntry = { Status: formValue.status || "default" };
                if (formValue.status !== "clear") nextEntry.Value = nextValue;
                if (formValue.type) nextEntry.Type = formValue.type;
                preferences[preferenceName] = nextEntry;
                document.Preferences = preferences;
            });
            if (applied) {
                selectedEntry = {
                    ...selectedEntry,
                    id: preferenceName,
                    label: preferenceName,
                    configured: true,
                    isNewPreference: false,
                    target: `known-preference:${preferenceName}`,
                };
                setStatus(t("profiles.settings_detail_applied"), "info");
                render(selectedEntry);
            }
        }

        function syncPreferenceValueEditor() {
            const editorEl = allSettingsDetailPanelEl?.querySelector("[data-settings-detail-preference-editor]");
            if (!editorEl) return;
            const status = editorEl.querySelector("[data-settings-detail-pref-status]")?.value || "default";
            const type = editorEl.querySelector("[data-settings-detail-pref-type]")?.value || "";
            const textInput = editorEl.querySelector("[data-settings-detail-pref-value-input]");
            const selectInput = editorEl.querySelector("[data-settings-detail-pref-value-select]");
            const nameInput = editorEl.querySelector("[data-settings-detail-pref-name]");
            const knownPreference = getKnownPreference(nameInput ? getPreferenceNameFromEditor() : selectedEntry?.id);
            const currentValue = selectInput && !selectInput.hidden
                ? selectInput.value
                : textInput?.value || "";
            const valueOptions = getPreferenceValueOptions(knownPreference, type, currentValue);
            const useSelect = valueOptions.length > 0;
            const valueDisabled = status === "clear";

            if (textInput) {
                textInput.value = serializePreferenceValue(currentValue);
                textInput.hidden = useSelect;
                textInput.disabled = useSelect || valueDisabled;
            }
            if (selectInput) {
                selectInput.innerHTML = `
                    <option value=""></option>
                    ${valueOptions.map((item) => `
                        <option value="${escapeHtml(item.value)}">${escapeHtml(item.label)}</option>
                    `).join("")}
                `;
                selectInput.value = serializePreferenceSelectValue(currentValue);
                selectInput.hidden = !useSelect;
                selectInput.disabled = !useSelect || valueDisabled;
            }
        }

        allSettingsAddPreferenceEl?.addEventListener("click", () => {
            renderNewPreference();
        });

        allSettingsDetailPanelEl?.addEventListener("click", (event) => {
            if (event.target.closest("[data-settings-detail-reset]")) {
                render(selectedEntry);
                return;
            }
            if (event.target.closest("[data-settings-detail-remove]")) {
                removeSelectedEntry();
                return;
            }
            if (event.target.closest("[data-settings-detail-apply-raw]")) {
                applyRawPolicyValue();
                return;
            }
            if (event.target.closest("[data-settings-detail-apply-preference]")) {
                applyPreferenceValue();
            }
        });

        allSettingsDetailPanelEl?.addEventListener("change", (event) => {
            if (event.target.closest("[data-settings-detail-pref-status], [data-settings-detail-pref-type]")) {
                syncPreferenceValueEditor();
            }
        });

        allSettingsDetailPanelEl?.addEventListener("input", (event) => {
            if (event.target.closest("[data-settings-detail-pref-name]")) {
                syncPreferenceValueEditor();
            }
        });

        return {
            render,
            renderNewPreference,
        };
    }

    window.BPMProfilesAllSettingsDetail = { create };
})();
