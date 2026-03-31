(() => {
    function create({
        dependencies = {},
    }) {
        const {
            t,
            escapeHtml,
            serializePreferenceValue,
            parsePreferenceValue,
            serializePreferenceSelectValue,
        } = dependencies;

        function getPreferenceFieldInputs(row, field) {
            return Array.from(row.querySelectorAll(`[data-preference-field="${field}"]`));
        }

        function getPreferenceFieldInput(row, field) {
            const inputs = getPreferenceFieldInputs(row, field);
            return inputs.find((input) => !input.hidden) || inputs[0] || null;
        }

        function readPreferenceFieldsFromRow(row) {
            const read = (field) => {
                const input = getPreferenceFieldInput(row, field);
                return input ? input.value : "";
            };

            return {
                name: read("name").trim(),
                status: read("status") || "default",
                type: read("type"),
                value: read("value"),
            };
        }

        function setPreferenceRowValue(row, field, value) {
            const nextValue = value == null ? "" : String(value);
            getPreferenceFieldInputs(row, field).forEach((input) => {
                input.value = nextValue;
            });
        }

        function getPreferenceValueEditorConfig(knownPreference, effectiveType) {
            if (knownPreference?.value_options?.length) {
                return {
                    kind: "select",
                    options: knownPreference.value_options,
                };
            }

            if (effectiveType === "boolean") {
                return {
                    kind: "select",
                    options: [
                        { value: true, fallback: t("profiles.wizard_preferences_boolean_true") },
                        { value: false, fallback: t("profiles.wizard_preferences_boolean_false") },
                    ],
                };
            }

            return {
                kind: "text",
                options: [],
            };
        }

        function updatePreferenceValueEditor(row, knownPreference, effectiveType, currentValue, disabled) {
            const valueInput = row.querySelector("[data-preference-value-input]");
            const valueSelect = row.querySelector("[data-preference-value-select]");
            if (!valueInput || !valueSelect) return;

            const editorConfig = getPreferenceValueEditorConfig(knownPreference, effectiveType);
            const selectValue = String(currentValue || "").trim();

            if (editorConfig.kind === "select") {
                const options = [{ value: "", fallback: "" }].concat(editorConfig.options || []);
                const allowedValues = new Set(options.map((option) => serializePreferenceSelectValue(option.value)));

                if (selectValue && !allowedValues.has(selectValue)) {
                    options.push({
                        value: selectValue,
                        fallback: t("profiles.wizard_preferences_value_custom").replace("{value}", selectValue),
                    });
                }

                valueSelect.innerHTML = options
                    .map((option) => {
                        const rawValue = serializePreferenceSelectValue(option.value);
                        const label = option.label_key
                            ? t(option.label_key, option.fallback || rawValue)
                            : (option.fallback || rawValue);
                        return `<option value="${escapeHtml(rawValue)}">${escapeHtml(label)}</option>`;
                    })
                    .join("");
                valueSelect.value = selectValue;
                valueSelect.hidden = false;
                valueSelect.disabled = disabled;
                valueInput.hidden = true;
                valueInput.disabled = true;
            } else {
                valueInput.hidden = false;
                valueInput.disabled = disabled;
                valueSelect.hidden = true;
                valueSelect.disabled = true;
            }
        }

        function formatPreferenceStatusLabel(status) {
            const normalizedStatus = String(status || "default").trim() || "default";
            if (normalizedStatus === "locked") return t("profiles.wizard_preferences_status_locked");
            if (normalizedStatus === "user") return t("profiles.wizard_preferences_status_user");
            if (normalizedStatus === "clear") return t("profiles.wizard_preferences_status_clear");
            return t("profiles.wizard_preferences_status_default");
        }

        function formatPreferenceTypeLabel(type) {
            const normalizedType = String(type || "").trim();
            if (normalizedType === "boolean") return t("profiles.wizard_preferences_type_boolean");
            if (normalizedType === "number") return t("profiles.wizard_preferences_type_number");
            if (normalizedType === "string") return t("profiles.wizard_preferences_type_string");
            return t("profiles.wizard_preferences_type_auto");
        }

        function localizePreferenceRow(row) {
            const labels = {
                name: t("profiles.wizard_preferences_field_name"),
                status: t("profiles.wizard_preferences_field_status"),
                type: t("profiles.wizard_preferences_field_type"),
                value: t("profiles.wizard_preferences_field_value"),
            };

            row.querySelectorAll("[data-preference-label]").forEach((labelEl) => {
                const key = labelEl.dataset.preferenceLabel;
                if (key && labels[key]) {
                    labelEl.textContent = labels[key];
                }
            });

            const removeButton = row.querySelector("[data-preference-remove]");
            if (removeButton) {
                removeButton.textContent = t("profiles.wizard_preferences_remove_button");
            }

            const statusInput = row.querySelector('[data-preference-field="status"]');
            if (statusInput?.options?.length >= 4) {
                statusInput.options[0].textContent = t("profiles.wizard_preferences_status_default");
                statusInput.options[1].textContent = t("profiles.wizard_preferences_status_locked");
                statusInput.options[2].textContent = t("profiles.wizard_preferences_status_user");
                statusInput.options[3].textContent = t("profiles.wizard_preferences_status_clear");
            }

            const typeInput = row.querySelector('[data-preference-field="type"]');
            if (typeInput?.options?.length >= 4) {
                typeInput.options[0].textContent = t("profiles.wizard_preferences_type_auto_option");
                typeInput.options[1].textContent = t("profiles.wizard_preferences_type_boolean");
                typeInput.options[2].textContent = t("profiles.wizard_preferences_type_number");
                typeInput.options[3].textContent = t("profiles.wizard_preferences_type_string");
            }
        }

        function updatePreferenceRowAssist(row, { getKnownPreference, forceAutofill = false }) {
            const values = readPreferenceFieldsFromRow(row);
            const knownPreference = getKnownPreference(values.name);
            const statusInput = row.querySelector('[data-preference-field="status"]');
            const typeInput = row.querySelector('[data-preference-field="type"]');
            const valueInput = row.querySelector("[data-preference-value-input]");
            const hintEl = row.querySelector("[data-preference-hint]");
            const nameInput = row.querySelector('[data-preference-field="name"]');
            const rowDisabled = row.dataset.preferenceUiDisabled === "true";
            const knownDescription = knownPreference
                ? t(knownPreference.description_key, knownPreference.description_fallback || "")
                : "";

            if (nameInput) {
                nameInput.setAttribute("list", "wizard-preferences-known-list");
            }

            const canAutofillExisting = statusInput
                && typeInput
                && valueInput
                && statusInput.value === "default"
                && !typeInput.value
                && !String(valueInput.value || "").trim();

            if (knownPreference && (forceAutofill || canAutofillExisting)) {
                if (statusInput && knownPreference.status) statusInput.value = knownPreference.status;
                if (typeInput && knownPreference.type) typeInput.value = knownPreference.type;
                if (valueInput && knownPreference.can_autofill && knownPreference.value !== null) {
                    valueInput.value = serializePreferenceValue(knownPreference.value);
                }
            }

            const effectiveStatus = statusInput?.value || "default";
            const effectiveType = typeInput?.value || knownPreference?.type || "";
            const activeValue = readPreferenceFieldsFromRow(row).value;
            const shouldDisable = rowDisabled || effectiveStatus === "clear";

            updatePreferenceValueEditor(row, knownPreference, effectiveType, activeValue, shouldDisable);

            if (valueInput) {
                valueInput.placeholder = effectiveType === "boolean"
                    ? t("profiles.wizard_preferences_value_placeholder_boolean")
                    : effectiveType === "number"
                        ? t("profiles.wizard_preferences_value_placeholder_number")
                        : t("profiles.wizard_preferences_value_placeholder_default");
                valueInput.inputMode = effectiveType === "number" ? "decimal" : "text";
            }

            if (hintEl) {
                if (effectiveStatus === "clear") {
                    hintEl.textContent = t("profiles.wizard_preferences_hint_clear");
                } else if (knownDescription) {
                    const suffix = knownPreference?.can_autofill
                        ? ` ${t("profiles.wizard_preferences_hint_known")}`
                        : ` ${t("profiles.wizard_preferences_hint_known_multiple")}`;
                    hintEl.textContent = `${knownDescription}${suffix}`;
                } else if (knownPreference?.can_autofill) {
                    hintEl.textContent = t("profiles.wizard_preferences_hint_known");
                } else if (knownPreference) {
                    hintEl.textContent = t("profiles.wizard_preferences_hint_known_multiple");
                } else {
                    hintEl.textContent = t(
                        "profiles.wizard_preferences_hint_default",
                        "Use true/false, numbers, or text. JSON objects and arrays are also accepted when value type is inferred.",
                    );
                }
            }
        }

        function updatePreferenceRowPresentation(row, index, { getKnownPreference }) {
            const values = readPreferenceFieldsFromRow(row);
            const knownPreference = getKnownPreference(values.name);
            const titleEl = row.querySelector("[data-preference-title]");
            const metaEl = row.querySelector("[data-preference-meta]");
            const summaryEl = row.querySelector("[data-preference-summary]");
            const warningEl = row.querySelector("[data-preference-warning]");
            const nameRequired = !values.name;
            const valueRequired = values.status !== "clear" && !values.value.trim();
            const invalid = nameRequired || valueRequired;

            localizePreferenceRow(row);

            if (titleEl) {
                titleEl.textContent = values.name || `${t("profiles.wizard_preferences_card_title")} ${index + 1}`;
            }
            if (metaEl) {
                metaEl.textContent = values.name
                    ? knownPreference
                        ? `${t(knownPreference.label_key, knownPreference.fallback || values.name)} • ${values.name}`
                        : `${values.name} -> ${t("profiles.wizard_preferences_meta_target")}`
                    : t("profiles.wizard_preferences_card_meta");
            }
            if (summaryEl) {
                const summaryParts = [
                    formatPreferenceStatusLabel(values.status),
                    formatPreferenceTypeLabel(values.type),
                ];
                if (values.status !== "clear" && values.value.trim()) {
                    summaryParts.push(values.value.trim());
                }
                summaryEl.textContent = values.name
                    ? summaryParts.join(" • ")
                    : t(
                        "profiles.wizard_preferences_summary_default",
                        "Set the preference key, value, status, and optional explicit type.",
                    );
            }
            if (warningEl) {
                warningEl.textContent = `${t("profiles.wizard_preferences_error_name")} ${t("profiles.wizard_preferences_error_value")}`;
                warningEl.hidden = !invalid;
            }

            row.classList.toggle("wizard-search-engine-card--invalid", invalid);
            row.querySelectorAll("[data-preference-field]").forEach((input) => {
                const field = input.dataset.preferenceField;
                const fieldInvalid = (field === "name" && nameRequired) || (field === "value" && valueRequired);
                input.classList.toggle("input-invalid", fieldInvalid);
                input.setAttribute("aria-invalid", fieldInvalid ? "true" : "false");
            });
        }

        return {
            getPreferenceFieldInputs,
            getPreferenceFieldInput,
            readPreferenceFieldsFromRow,
            setPreferenceRowValue,
            updatePreferenceRowAssist,
            updatePreferenceRowPresentation,
        };
    }

    window.BPMProfilesPreferenceRows = { create };
})();
