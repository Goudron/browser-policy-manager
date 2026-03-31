(() => {
    function create({ dependencies = {} }) {
        const { t, textToList, parseBooleanSelectValue } = dependencies;

        function readSchemaDictionaryRowEntry(row) {
            const entryKey = String(row.querySelector("[data-schema-dict-key]")?.value || "").trim();
            const nextEntry = {};

            Array.from(row.querySelectorAll("[data-schema-policy-field]")).forEach((control) => {
                const fieldName = control.dataset.schemaPolicyField;
                const fieldKind = control.dataset.schemaFieldKind || "text";
                if (!fieldName) return;

                const parsedValue = parseSchemaPolicyFieldValue(control, fieldKind);
                if (parsedValue.ok && parsedValue.hasValue) {
                    nextEntry[fieldName] = parsedValue.value;
                }
            });

            return {
                entryKey,
                entryValue: nextEntry,
            };
        }

        function readSchemaArrayRowEntry(row) {
            const nextItem = {};
            const parseErrors = [];

            Array.from(row.querySelectorAll("[data-schema-policy-field]")).forEach((control) => {
                const fieldName = control.dataset.schemaPolicyField;
                const fieldKind = control.dataset.schemaFieldKind || "text";
                if (!fieldName) return;

                const parsedValue = parseSchemaPolicyFieldValue(control, fieldKind);
                if (parsedValue.ok && parsedValue.hasValue) {
                    nextItem[fieldName] = parsedValue.value;
                } else if (!parsedValue.ok) {
                    parseErrors.push(fieldName);
                }
            });

            return {
                entryValue: nextItem,
                parseErrors,
            };
        }

        function readSchemaObjectCardValue(card) {
            const nextValue = {};
            const parseErrors = [];

            Array.from(card.querySelectorAll("[data-schema-policy-field]")).forEach((control) => {
                const fieldName = control.dataset.schemaPolicyField;
                const fieldKind = control.dataset.schemaFieldKind || "text";
                if (!fieldName) return;

                const parsedValue = parseSchemaPolicyFieldValue(control, fieldKind);
                if (parsedValue.ok && parsedValue.hasValue) {
                    nextValue[fieldName] = parsedValue.value;
                } else if (!parsedValue.ok) {
                    parseErrors.push(fieldName);
                }
            });

            return {
                entryValue: nextValue,
                parseErrors,
            };
        }

        function parseSchemaPolicyFieldValue(control, fieldKind) {
            if (fieldKind === "nested-object") {
                const nextValue = {};
                let hasValue = false;

                for (const node of getImmediateSchemaNestedFieldNodes(control)) {
                    const parsedValue = parseSchemaNestedFieldValue(node);
                    if (!parsedValue.ok) {
                        return parsedValue;
                    }
                    if (parsedValue.hasValue) {
                        nextValue[node.dataset.schemaNestedField] = parsedValue.value;
                        hasValue = true;
                    }
                }

                return { ok: true, hasValue, value: nextValue };
            }

            if (fieldKind === "boolean-select") {
                const value = parseBooleanSelectValue(control.value || "");
                return value === null ? { ok: true, hasValue: false, value: null } : { ok: true, hasValue: true, value };
            }

            if (fieldKind === "string-list") {
                const listInputs = Array.from(control.querySelectorAll("[data-schema-list-item]"));
                if (listInputs.length > 0) {
                    const values = listInputs
                        .map((input) => String(input.value || "").trim())
                        .filter(Boolean);
                    return values.length > 0 ? { ok: true, hasValue: true, value: values } : { ok: true, hasValue: false, value: [] };
                }
                const values = textToList(control.value || "");
                return values.length > 0 ? { ok: true, hasValue: true, value: values } : { ok: true, hasValue: false, value: [] };
            }

            if (fieldKind === "true-map") {
                const listInputs = Array.from(control.querySelectorAll("[data-schema-list-item]"));
                if (listInputs.length > 0) {
                    const values = listInputs
                        .map((input) => String(input.value || "").trim())
                        .filter(Boolean);
                    if (values.length === 0) return { ok: true, hasValue: false, value: {} };
                    return {
                        ok: true,
                        hasValue: true,
                        value: Object.fromEntries(values.map((entry) => [entry, true])),
                    };
                }
                const values = textToList(control.value || "");
                if (values.length === 0) return { ok: true, hasValue: false, value: {} };
                return {
                    ok: true,
                    hasValue: true,
                    value: Object.fromEntries(values.map((entry) => [entry, true])),
                };
            }

            if (fieldKind === "json") {
                const raw = String(control.value || "").trim();
                if (!raw) return { ok: true, hasValue: false, value: null };
                try {
                    return { ok: true, hasValue: true, value: JSON.parse(raw) };
                } catch {
                    return {
                        ok: false,
                        hasValue: false,
                        value: null,
                        message: t("profiles.wizard_shell_json_error"),
                    };
                }
            }

            if (fieldKind === "number") {
                const raw = String(control.value || "").trim();
                if (!raw) return { ok: true, hasValue: false, value: null };
                const numeric = Number(raw);
                if (Number.isNaN(numeric)) {
                    return {
                        ok: false,
                        hasValue: false,
                        value: null,
                        message: t("profiles.wizard_preferences_error_number"),
                    };
                }
                return { ok: true, hasValue: true, value: numeric };
            }

            const raw = String(control.value || "");
            const trimmed = raw.trim();
            if (!trimmed) return { ok: true, hasValue: false, value: null };
            return { ok: true, hasValue: true, value: trimmed };
        }

        function getImmediateSchemaNestedFieldNodes(container) {
            return Array.from(container.querySelectorAll("[data-schema-nested-field]"))
                .filter((node) => node.parentElement?.closest("[data-schema-nested-field]") === container);
        }

        function parseSchemaNestedFieldValue(node) {
            const fieldKind = node.dataset.schemaNestedKind || "text";
            if (fieldKind === "nested-dictionary-object") {
                const nextValue = {};
                let hasValue = false;

                for (const row of Array.from(node.querySelectorAll("[data-schema-nested-dict-row]"))) {
                    const entryKey = String(row.querySelector("[data-schema-nested-dict-key]")?.value || "").trim();
                    if (!entryKey) continue;

                    const nextEntry = {};
                    let rowHasValue = false;
                    for (const childNode of getImmediateSchemaNestedFieldNodes(row)) {
                        const parsedValue = parseSchemaNestedFieldValue(childNode);
                        if (!parsedValue.ok) {
                            return parsedValue;
                        }
                        if (parsedValue.hasValue) {
                            nextEntry[childNode.dataset.schemaNestedField] = parsedValue.value;
                            rowHasValue = true;
                        }
                    }

                    if (rowHasValue) {
                        nextValue[entryKey] = nextEntry;
                        hasValue = true;
                    }
                }

                return { ok: true, hasValue, value: nextValue };
            }

            if (fieldKind === "nested-array-of-objects") {
                const nextItems = [];

                for (const row of Array.from(node.querySelectorAll("[data-schema-nested-array-row]"))) {
                    const nextItem = {};
                    let rowHasValue = false;

                    for (const childNode of getImmediateSchemaNestedFieldNodes(row)) {
                        const parsedValue = parseSchemaNestedFieldValue(childNode);
                        if (!parsedValue.ok) {
                            return parsedValue;
                        }
                        if (parsedValue.hasValue) {
                            nextItem[childNode.dataset.schemaNestedField] = parsedValue.value;
                            rowHasValue = true;
                        }
                    }

                    if (rowHasValue) {
                        nextItems.push(nextItem);
                    }
                }

                return { ok: true, hasValue: nextItems.length > 0, value: nextItems };
            }

            if (fieldKind === "nested-object") {
                const nextValue = {};
                let hasValue = false;

                for (const childNode of getImmediateSchemaNestedFieldNodes(node)) {
                    const parsedValue = parseSchemaNestedFieldValue(childNode);
                    if (!parsedValue.ok) {
                        return parsedValue;
                    }
                    if (parsedValue.hasValue) {
                        nextValue[childNode.dataset.schemaNestedField] = parsedValue.value;
                        hasValue = true;
                    }
                }

                return { ok: true, hasValue, value: nextValue };
            }

            return parseSchemaPolicyFieldValue(node, fieldKind);
        }

        function getSchemaNestedValueAtPath(entryValue, path) {
            if (!path) return entryValue;

            return String(path)
                .split(".")
                .filter(Boolean)
                .reduce((current, segment) => {
                    if (!current || typeof current !== "object" || Array.isArray(current)) {
                        return undefined;
                    }
                    return current[segment];
                }, entryValue);
        }

        function pathHasSchemaParseError(path, parseErrors = []) {
            const topLevel = String(path || "").split(".")[0] || "";
            return parseErrors.includes(topLevel) || parseErrors.includes(path);
        }

        function readSchemaNestedFieldSpecs(container) {
            try {
                return JSON.parse(container.dataset.schemaNestedFields || "[]");
            } catch {
                return [];
            }
        }

        return {
            readSchemaDictionaryRowEntry,
            readSchemaArrayRowEntry,
            readSchemaObjectCardValue,
            parseSchemaPolicyFieldValue,
            getImmediateSchemaNestedFieldNodes,
            parseSchemaNestedFieldValue,
            getSchemaNestedValueAtPath,
            pathHasSchemaParseError,
            readSchemaNestedFieldSpecs,
        };
    }

    window.BPMProfilesSchemaShellValueIO = { create };
})();
