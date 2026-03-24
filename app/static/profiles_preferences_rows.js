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
                        { value: true, fallback: t("profiles.wizard_preferences_boolean_true", "true") },
                        { value: false, fallback: t("profiles.wizard_preferences_boolean_false", "false") },
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
                        fallback: t("profiles.wizard_preferences_value_custom", "Custom: {value}").replace("{value}", selectValue),
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
                    ? t("profiles.wizard_preferences_value_placeholder_boolean", "true")
                    : effectiveType === "number"
                        ? t("profiles.wizard_preferences_value_placeholder_number", "2")
                        : t("profiles.wizard_preferences_value_placeholder_default", "true");
                valueInput.inputMode = effectiveType === "number" ? "decimal" : "text";
            }

            if (hintEl) {
                if (effectiveStatus === "clear") {
                    hintEl.textContent = t("profiles.wizard_preferences_hint_clear", "Clear removes the managed value, so no explicit value is needed.");
                } else if (knownDescription) {
                    const suffix = knownPreference?.can_autofill
                        ? ` ${t("profiles.wizard_preferences_hint_known", "Known preference with a suggested managed default.")}`
                        : ` ${t("profiles.wizard_preferences_hint_known_multiple", "Known preference with multiple preset variants. Set status and value explicitly.")}`;
                    hintEl.textContent = `${knownDescription}${suffix}`;
                } else if (knownPreference?.can_autofill) {
                    hintEl.textContent = t("profiles.wizard_preferences_hint_known", "Known preference with a suggested managed default.");
                } else if (knownPreference) {
                    hintEl.textContent = t("profiles.wizard_preferences_hint_known_multiple", "Known preference with multiple preset variants. Set status and value explicitly.");
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

            if (titleEl) {
                titleEl.textContent = values.name || `${t("profiles.wizard_preferences_card_title", "Preference")} ${index + 1}`;
            }
            if (metaEl) {
                metaEl.textContent = values.name
                    ? knownPreference
                        ? `${t(knownPreference.label_key, knownPreference.fallback || values.name)} • ${values.name}`
                        : `${values.name} -> Preferences`
                    : t("profiles.wizard_preferences_card_meta", "Writes one item into Preferences.");
            }
            if (summaryEl) {
                const summaryParts = [values.status || "default", values.type || t("profiles.wizard_preferences_type_auto", "infer")];
                if (values.status !== "clear" && values.value.trim()) {
                    summaryParts.push(values.value.trim());
                }
                summaryEl.textContent = summaryParts.join(" • ");
            }
            if (warningEl) {
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
