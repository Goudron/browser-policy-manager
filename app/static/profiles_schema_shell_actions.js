(() => {
    function create({
        documentRef = document,
        dependencies = {},
        state = {},
        helpers = {},
    }) {
        const {
            t,
            escapeHtml,
            fromEditorValue,
            toEditorValue,
            setStatus,
        } = dependencies;
        const { getEditor = () => null, setCurrentRaw = () => {} } = state;
        const {
            parseSchemaPolicyFieldValue,
            readSchemaNestedFieldSpecs,
            renderWizardSchemaNestedArrayRow,
            renderWizardSchemaNestedDictionaryRow,
        } = helpers;

        function refreshSchemaNestedArrayRows(container) {
            const field = {
                name: container.dataset.schemaNestedField || "",
                label: container.dataset.schemaNestedLabel || "",
                fields: readSchemaNestedFieldSpecs(container),
            };
            const listEl = container.querySelector("[data-schema-nested-array-list]");
            if (!listEl) return;

            const rows = Array.from(listEl.querySelectorAll("[data-schema-nested-array-row]"));
            if (rows.length === 0) {
                listEl.innerHTML = `<div class="wizard-shell-empty" data-schema-nested-empty>${escapeHtml(t("profiles.wizard_shell_array_empty", "No items yet."))}</div>`;
                return;
            }

            listEl.querySelector("[data-schema-nested-empty]")?.remove();
            rows.forEach((row, index) => {
                row.dataset.schemaNestedArrayIndex = String(index);
                row.querySelector(".wizard-search-engine-title").textContent = row.querySelector(".wizard-search-engine-title").textContent || `${field.label || field.name || "Item"} ${index + 1}`;
                row.querySelector(".wizard-search-engine-meta").textContent = `${t("profiles.wizard_shell_array_item_meta", "Array item")} ${index + 1}`;
            });
        }

        function refreshSchemaNestedDictionaryRows(container) {
            const field = {
                name: container.dataset.schemaNestedField || "",
                label: container.dataset.schemaNestedLabel || "",
                fields: readSchemaNestedFieldSpecs(container),
            };
            const listEl = container.querySelector("[data-schema-nested-dict-list]");
            if (!listEl) return;

            const rows = Array.from(listEl.querySelectorAll("[data-schema-nested-dict-row]"));
            if (rows.length === 0) {
                listEl.innerHTML = `<div class="wizard-shell-empty" data-schema-nested-empty>${escapeHtml(t("profiles.wizard_shell_dictionary_empty", "No entries yet."))}</div>`;
                return;
            }

            listEl.querySelector("[data-schema-nested-empty]")?.remove();
            rows.forEach((row, index) => {
                row.dataset.schemaNestedDictIndex = String(index);
                const entryKey = String(row.querySelector("[data-schema-nested-dict-key]")?.value || "").trim();
                row.querySelector(".wizard-search-engine-title").textContent = entryKey || `${field.label || field.name || "Entry"} ${index + 1}`;
                row.querySelector(".wizard-search-engine-meta").textContent = `${t("profiles.wizard_shell_dictionary_item_meta", "Dictionary entry")} ${index + 1}`;
            });
        }

        function appendSchemaNestedArrayItem(container) {
            const listEl = container?.querySelector("[data-schema-nested-array-list]");
            if (!container || !listEl) return;

            const field = {
                name: container.dataset.schemaNestedField || "",
                label: container.dataset.schemaNestedLabel || "",
                fields: readSchemaNestedFieldSpecs(container),
            };
            const nextIndex = listEl.querySelectorAll("[data-schema-nested-array-row]").length;
            listEl.querySelector("[data-schema-nested-empty]")?.remove();
            listEl.insertAdjacentHTML("beforeend", renderWizardSchemaNestedArrayRow(field, {}, nextIndex, false));
            refreshSchemaNestedArrayRows(container);
        }

        function removeSchemaNestedArrayItem(container, row) {
            if (!container || !row) return;
            row.remove();
            refreshSchemaNestedArrayRows(container);
        }

        function appendSchemaNestedDictionaryEntry(container) {
            const listEl = container?.querySelector("[data-schema-nested-dict-list]");
            if (!container || !listEl) return;

            const field = {
                name: container.dataset.schemaNestedField || "",
                label: container.dataset.schemaNestedLabel || "",
                fields: readSchemaNestedFieldSpecs(container),
            };
            const nextIndex = listEl.querySelectorAll("[data-schema-nested-dict-row]").length;
            listEl.querySelector("[data-schema-nested-empty]")?.remove();
            listEl.insertAdjacentHTML("beforeend", renderWizardSchemaNestedDictionaryRow(field, "", {}, nextIndex, false));
            refreshSchemaNestedDictionaryRows(container);
        }

        function removeSchemaNestedDictionaryEntry(container, row) {
            if (!container || !row) return;
            row.remove();
            refreshSchemaNestedDictionaryRows(container);
        }

        function applySchemaPolicyFromCard(card) {
            const editor = getEditor();
            if (!editor || !card) return;

            const policyId = card.dataset.schemaPolicyId;
            const policyKind = card.dataset.schemaPolicyKind;
            if (!policyId || !policyKind) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};

                if (policyKind === "boolean-select") {
                    const select = card.querySelector('[data-schema-policy-field="__value__"]');
                    const nextValue = dependencies.parseBooleanSelectValue(select?.value || "");
                    if (nextValue === null) {
                        delete normalized[policyId];
                    } else {
                        normalized[policyId] = nextValue;
                    }
                } else if (policyKind === "dictionary-object") {
                    const rows = Array.from(card.querySelectorAll("[data-schema-dict-row]"));
                    const nextEntries = {};

                    for (const row of rows) {
                        const entryKey = String(row.querySelector("[data-schema-dict-key]")?.value || "").trim();
                        if (!entryKey) continue;

                        const nextEntry = {};
                        let hasValue = false;
                        const controls = Array.from(row.querySelectorAll("[data-schema-policy-field]"));
                        for (const control of controls) {
                            const fieldName = control.dataset.schemaPolicyField;
                            const fieldKind = control.dataset.schemaFieldKind || "text";
                            if (!fieldName) continue;

                            const parsedValue = parseSchemaPolicyFieldValue(control, fieldKind);
                            if (!parsedValue.ok) {
                                setStatus(parsedValue.message, "warn");
                                return;
                            }
                            if (parsedValue.hasValue) {
                                nextEntry[fieldName] = parsedValue.value;
                                hasValue = true;
                            }
                        }

                        if (hasValue) {
                            nextEntries[entryKey] = nextEntry;
                        }
                    }

                    if (Object.keys(nextEntries).length > 0) {
                        normalized[policyId] = nextEntries;
                    } else {
                        delete normalized[policyId];
                    }
                } else if (policyKind === "array-of-objects") {
                    const rows = Array.from(card.querySelectorAll("[data-schema-array-row]"));
                    const nextItems = [];

                    for (const row of rows) {
                        const nextItem = {};
                        let hasValue = false;
                        const controls = Array.from(row.querySelectorAll("[data-schema-policy-field]"));
                        for (const control of controls) {
                            const fieldName = control.dataset.schemaPolicyField;
                            const fieldKind = control.dataset.schemaFieldKind || "text";
                            if (!fieldName) continue;

                            const parsedValue = parseSchemaPolicyFieldValue(control, fieldKind);
                            if (!parsedValue.ok) {
                                setStatus(parsedValue.message, "warn");
                                return;
                            }
                            if (parsedValue.hasValue) {
                                nextItem[fieldName] = parsedValue.value;
                                hasValue = true;
                            }
                        }

                        if (hasValue) {
                            nextItems.push(nextItem);
                        }
                    }

                    if (nextItems.length > 0) {
                        normalized[policyId] = nextItems;
                    } else {
                        delete normalized[policyId];
                    }
                } else if (policyKind === "branch") {
                    const branchMode = card.querySelector("[data-schema-branch-mode]")?.value || "";
                    if (!branchMode) {
                        delete normalized[policyId];
                    } else if (branchMode === "boolean") {
                        const select = card.querySelector('[data-schema-policy-field="__branch_boolean__"]');
                        const nextValue = dependencies.parseBooleanSelectValue(select?.value || "");
                        normalized[policyId] = nextValue === null ? true : nextValue;
                    } else if (branchMode === "object") {
                        const existing = normalized[policyId] && typeof normalized[policyId] === "object" && !Array.isArray(normalized[policyId])
                            ? { ...normalized[policyId] }
                            : {};
                        const managedFields = String(card.dataset.schemaBranchObjectManagedFields || "")
                            .split(",")
                            .map((field) => field.trim())
                            .filter(Boolean);
                        managedFields.forEach((field) => delete existing[field]);

                        const controls = Array.from(card.querySelectorAll('[data-schema-branch-section="object"] [data-schema-policy-field]'));
                        for (const control of controls) {
                            const fieldName = control.dataset.schemaPolicyField;
                            const fieldKind = control.dataset.schemaFieldKind || "text";
                            if (!fieldName) continue;

                            const parsedValue = parseSchemaPolicyFieldValue(control, fieldKind);
                            if (!parsedValue.ok) {
                                setStatus(parsedValue.message, "warn");
                                return;
                            }
                            if (parsedValue.hasValue) {
                                existing[fieldName] = parsedValue.value;
                            }
                        }

                        normalized[policyId] = existing;
                    }
                } else if (policyKind === "object-card") {
                    const existing = normalized[policyId] && typeof normalized[policyId] === "object" && !Array.isArray(normalized[policyId])
                        ? { ...normalized[policyId] }
                        : {};
                    const managedFields = String(card.dataset.schemaManagedFields || "")
                        .split(",")
                        .map((field) => field.trim())
                        .filter(Boolean);
                    managedFields.forEach((field) => delete existing[field]);

                    const controls = Array.from(card.querySelectorAll("[data-schema-policy-field]"));
                    for (const control of controls) {
                        const fieldName = control.dataset.schemaPolicyField;
                        const fieldKind = control.dataset.schemaFieldKind || "text";
                        if (!fieldName) continue;

                        const parsedValue = parseSchemaPolicyFieldValue(control, fieldKind);
                        if (!parsedValue.ok) {
                            setStatus(parsedValue.message, "warn");
                            return;
                        }
                        if (parsedValue.hasValue) {
                            existing[fieldName] = parsedValue.value;
                        }
                    }

                    if (Object.keys(existing).length > 0) {
                        normalized[policyId] = existing;
                    } else {
                        delete normalized[policyId];
                    }
                }

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                setStatus(t("profiles.wizard_schema_policy_applied", "Schema-driven policy updated."), "info");
            } catch (e) {
                setStatus(`Schema policy error: ${e.message || e}`, "error");
            }
        }

        function appendSchemaArrayItem(card) {
            const editor = getEditor();
            if (!editor || !card) return;

            const policyId = card.dataset.schemaPolicyId;
            if (!policyId) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const nextItems = Array.isArray(normalized[policyId]) ? [...normalized[policyId]] : [];
                nextItems.push({});
                normalized[policyId] = nextItems;
                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                setStatus(t("profiles.wizard_shell_array_item_added", "Array item added."), "info");
            } catch (e) {
                setStatus(`Schema array error: ${e.message || e}`, "error");
            }
        }

        function removeSchemaArrayItem(card, indexValue) {
            const editor = getEditor();
            if (!editor || !card) return;

            const policyId = card.dataset.schemaPolicyId;
            const index = Number(indexValue);
            if (!policyId || Number.isNaN(index)) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const nextItems = Array.isArray(normalized[policyId]) ? [...normalized[policyId]] : [];
                nextItems.splice(index, 1);
                if (nextItems.length > 0) {
                    normalized[policyId] = nextItems;
                } else {
                    delete normalized[policyId];
                }
                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                setStatus(t("profiles.wizard_shell_array_item_removed", "Array item removed."), "info");
            } catch (e) {
                setStatus(`Schema array error: ${e.message || e}`, "error");
            }
        }

        function appendSchemaDictionaryEntry(card) {
            const editor = getEditor();
            if (!editor || !card) return;

            const policyId = card.dataset.schemaPolicyId;
            if (!policyId) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const nextEntries = normalized[policyId] && typeof normalized[policyId] === "object" && !Array.isArray(normalized[policyId])
                    ? { ...normalized[policyId] }
                    : {};
                const seedBase = "new_entry";
                let candidate = seedBase;
                let counter = 1;
                while (candidate in nextEntries) {
                    counter += 1;
                    candidate = `${seedBase}_${counter}`;
                }
                nextEntries[candidate] = {};
                normalized[policyId] = nextEntries;
                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                setStatus(t("profiles.wizard_shell_dictionary_entry_added", "Dictionary entry added."), "info");
            } catch (e) {
                setStatus(`Schema dictionary error: ${e.message || e}`, "error");
            }
        }

        function removeSchemaDictionaryEntry(card, indexValue) {
            const editor = getEditor();
            if (!editor || !card) return;

            const policyId = card.dataset.schemaPolicyId;
            const index = Number(indexValue);
            if (!policyId || Number.isNaN(index)) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const nextEntries = normalized[policyId] && typeof normalized[policyId] === "object" && !Array.isArray(normalized[policyId])
                    ? { ...normalized[policyId] }
                    : {};
                const keys = Object.keys(nextEntries);
                const keyToRemove = keys[index];
                if (keyToRemove) {
                    delete nextEntries[keyToRemove];
                }
                if (Object.keys(nextEntries).length > 0) {
                    normalized[policyId] = nextEntries;
                } else {
                    delete normalized[policyId];
                }
                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                setStatus(t("profiles.wizard_shell_dictionary_entry_removed", "Dictionary entry removed."), "info");
            } catch (e) {
                setStatus(`Schema dictionary error: ${e.message || e}`, "error");
            }
        }

        return {
            refreshSchemaNestedArrayRows,
            refreshSchemaNestedDictionaryRows,
            appendSchemaNestedArrayItem,
            removeSchemaNestedArrayItem,
            appendSchemaNestedDictionaryEntry,
            removeSchemaNestedDictionaryEntry,
            applySchemaPolicyFromCard,
            appendSchemaArrayItem,
            removeSchemaArrayItem,
            appendSchemaDictionaryEntry,
            removeSchemaDictionaryEntry,
        };
    }

    window.BPMProfilesSchemaShellActions = { create };
})();
