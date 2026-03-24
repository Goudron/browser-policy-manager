(() => {
    function create({
        documentRef = document,
        elements = {},
        dependencies = {},
        state = {},
        wizardSchemaShellCatalog = {},
        wizardSchemaShellViews = {},
    }) {
        const {
            t,
            escapeHtml,
            humanizeIdentifier,
            formatBooleanSelectValue,
            parseBooleanSelectValue,
            formatSchemaLabel,
            fromEditorValue,
            toEditorValue,
            setStatus,
            readWizardSchemaSource,
            getActiveWizardSchemaVersion,
            renderManualHomeAndSearchSectionStatuses,
            renderNetworkReviewSummary,
            renderHomeReviewSummary,
            renderSearchReviewSummary,
            renderBookmarkReviewSummary,
            renderWebsiteAccessReviewSummary,
            renderPrivacyReviewSummary,
            getManagedExtensionProfileById,
            textToList,
        } = dependencies;

        const getEditor = state.getEditor || (() => null);
        const setCurrentRaw = state.setCurrentRaw || (() => {});

        const {
            wizardInstallAddonsPermissionCardEl,
            wizardExtensionSettingsCardEl,
        } = elements;

        const valueIO = window.BPMProfilesSchemaShellValueIO.create({
            dependencies: {
                t,
                textToList,
                parseBooleanSelectValue,
            },
        });

        const review = window.BPMProfilesSchemaShellReview.create({
            documentRef,
            dependencies: {
                t,
                getManagedExtensionProfileById,
            },
            helpers: valueIO,
        });

        function renderWizardSchemaShell() {
            const schemaVersion = getActiveWizardSchemaVersion();
            const channelData = wizardSchemaShellCatalog.channels?.[schemaVersion];
            const shellSteps = Array.isArray(wizardSchemaShellCatalog.steps) ? wizardSchemaShellCatalog.steps : [];
            const sourceState = readWizardSchemaSource();

            shellSteps.forEach((stepMeta) => {
                const view = wizardSchemaShellViews[String(stepMeta.step)];
                if (!view) return;

                const stepData = channelData?.steps?.[String(stepMeta.step)] || {
                    recommended: [],
                    additional: [],
                    raw_fallback: [],
                    preferences: [],
                    compatibility: { total: 0, mapped: 0, raw_fallback: 0, deprecated: 0 },
                };

                renderWizardSchemaShellBadges(view.badges, schemaVersion, stepData.compatibility || {});
                renderWizardSchemaShellPolicyBucket(
                    view.recommended,
                    stepData.recommended || [],
                    t("profiles.wizard_shell_empty_recommended", "No recommended policies are mapped into this step yet."),
                    sourceState.data,
                    !sourceState.ok,
                );
                renderWizardSchemaShellPolicyBucket(
                    view.additional,
                    stepData.additional || [],
                    t("profiles.wizard_shell_empty_additional", "No additional mapped policies are listed for this step yet."),
                    sourceState.data,
                    !sourceState.ok,
                );
                renderWizardSchemaShellPreferenceBucket(
                    view.preferences,
                    stepData.preferences || [],
                    t("profiles.wizard_shell_empty_preferences", "No preference sections are attached to this step."),
                );
                renderWizardSchemaShellPolicyBucket(
                    view.raw,
                    stepData.raw_fallback || [],
                    t("profiles.wizard_shell_empty_raw", "This step currently does not need a raw JSON fallback bucket."),
                    sourceState.data,
                    !sourceState.ok,
                );
            });

            renderManualHomeAndSearchSectionStatuses(sourceState.data);
            renderNetworkReviewSummary(sourceState.data);
            renderHomeReviewSummary(sourceState.data);
            renderSearchReviewSummary(sourceState.data);
            renderWizardExtensionAdvancedPolicies(sourceState.data, !sourceState.ok, channelData);
        }

        function getWizardSchemaPolicyItem(policyId, channelData, preferredStep = null) {
            if (!policyId || !channelData?.steps) return null;

            const stepKeys = preferredStep != null
                ? [String(preferredStep)]
                : Object.keys(channelData.steps);

            for (const stepKey of stepKeys) {
                const stepData = channelData.steps?.[stepKey];
                const buckets = [
                    ...(Array.isArray(stepData?.recommended) ? stepData.recommended : []),
                    ...(Array.isArray(stepData?.additional) ? stepData.additional : []),
                    ...(Array.isArray(stepData?.raw_fallback) ? stepData.raw_fallback : []),
                ];
                const match = buckets.find((item) => item.id === policyId);
                if (match) return match;
            }

            return null;
        }

        function renderMountedSchemaPolicy(container, item, sourceData = {}, disabled = false) {
            if (!container) return;

            if (!item?.inline_editor) {
                container.innerHTML = "";
                container.hidden = true;
                return;
            }

            container.hidden = false;
            container.innerHTML = renderWizardSchemaInlineEditor(item, sourceData?.[item.id], disabled);
            review.renderSchemaPolicyReviewState(container.querySelector("[data-schema-policy-card]"));
        }

        function renderWizardExtensionAdvancedPolicies(sourceData = {}, disabled = false, channelData = null) {
            const resolvedChannelData = channelData || wizardSchemaShellCatalog.channels?.[getActiveWizardSchemaVersion()];
            const installPermissionItem = getWizardSchemaPolicyItem("InstallAddonsPermission", resolvedChannelData, 6);
            const extensionSettingsItem = getWizardSchemaPolicyItem("ExtensionSettings", resolvedChannelData, 6);

            renderMountedSchemaPolicy(
                wizardInstallAddonsPermissionCardEl,
                installPermissionItem,
                sourceData,
                disabled,
            );
            renderMountedSchemaPolicy(
                wizardExtensionSettingsCardEl,
                extensionSettingsItem,
                sourceData,
                disabled,
            );
            renderBookmarkReviewSummary(sourceData);
            renderWebsiteAccessReviewSummary(sourceData);
            renderPrivacyReviewSummary(sourceData);
        }

        function renderWizardSchemaShellBadges(container, schemaVersion, compatibility) {
            if (!container) return;

            const badges = [
                {
                    tone: "accent",
                    label: `${t("profiles.wizard_shell_badge_schema", "Schema")} • ${formatSchemaLabel(schemaVersion)}`,
                },
                {
                    tone: "accent",
                    label: `${t("profiles.wizard_shell_badge_mapped", "Mapped")} • ${compatibility.mapped || 0}`,
                },
                {
                    tone: "warm",
                    label: `${t("profiles.wizard_shell_badge_raw", "Raw fallback")} • ${compatibility.raw_fallback || 0}`,
                },
            ];
            if ((compatibility.deprecated || 0) > 0) {
                badges.push({
                    tone: "warm",
                    label: `${t("profiles.wizard_shell_badge_deprecated", "Deprecated")} • ${compatibility.deprecated}`,
                });
            }

            container.innerHTML = badges
                .map((badge) => `<span class="wizard-shell-badge wizard-shell-badge--${badge.tone}">${escapeHtml(badge.label)}</span>`)
                .join("");
        }

        function renderWizardSchemaShellPolicyBucket(container, items, emptyMessage, sourceData = {}, disabled = false) {
            if (!container) return;

            if (!Array.isArray(items) || items.length === 0) {
                container.innerHTML = `<div class="wizard-shell-empty">${escapeHtml(emptyMessage)}</div>`;
                return;
            }

            container.innerHTML = items
                .map((item) => {
                    if (item.inline_editor) {
                        return renderWizardSchemaInlineEditor(item, sourceData?.[item.id], disabled);
                    }

                    const tags = Array.isArray(item.tags) && item.tags.length > 0
                        ? `<div class="wizard-shell-item-tags">${item.tags.slice(0, 3).map((tag) => `<span class="wizard-shell-item-tag">${escapeHtml(humanizeIdentifier(tag))}</span>`).join("")}</div>`
                        : "";
                    const metaParts = [
                        item.subsection_label || humanizeIdentifier(item.subsection || ""),
                        humanizeIdentifier(item.widget || ""),
                        item.complexity === "basic"
                            ? t("profiles.wizard_shell_meta_basic", "Basic")
                            : t("profiles.wizard_shell_meta_advanced", "Advanced"),
                    ].filter(Boolean);

                    return `
                        <button
                            type="button"
                            class="button-base ghost-button wizard-shell-item"
                            data-wizard-shell-target="policy"
                            data-wizard-shell-policy-id="${escapeHtml(item.id || "")}"
                            data-settings-target="${escapeHtml(item.target || "")}">
                            <span class="wizard-shell-item-title">${escapeHtml(item.label || item.id || "")}</span>
                            <span class="wizard-shell-item-meta">${escapeHtml(metaParts.join(" • "))}</span>
                            ${tags}
                        </button>
                    `;
                })
                .join("");

            container.querySelectorAll("[data-schema-policy-card]").forEach((card) => {
                review.renderSchemaPolicyReviewState(card);
            });
        }

        function renderWizardSchemaInlineEditor(item, currentValue, disabled) {
            const inlineEditor = item.inline_editor || {};
            const metaParts = [
                item.subsection_label || humanizeIdentifier(item.subsection || ""),
                humanizeIdentifier(item.widget || ""),
                item.complexity === "basic"
                    ? t("profiles.wizard_shell_meta_basic", "Basic")
                    : t("profiles.wizard_shell_meta_advanced", "Advanced"),
            ].filter(Boolean);
            const disabledAttr = disabled ? "disabled" : "";
            const currentObject = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue) ? currentValue : {};
            const unsupportedNotice = inlineEditor.unsupported_field_count > 0
                ? `<div class="wizard-input-hint">${escapeHtml(
                    t(
                        "profiles.wizard_shell_inline_partial_notice",
                        "Some nested fields are still preserved through raw JSON.",
                    ),
                )}</div>`
                : "";

            if (inlineEditor.kind === "boolean-select") {
                return `
                    <div
                        class="wizard-shell-card"
                        data-schema-policy-card
                        data-schema-policy-id="${escapeHtml(item.id || "")}"
                        data-schema-policy-kind="boolean-select"
                        data-settings-target="${escapeHtml(item.target || "")}">
                        <div>
                            <div class="wizard-shell-card-title">${escapeHtml(item.label || item.id || "")}</div>
                            <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                        </div>
                        <label>
                            <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_shell_field_value", "Value"))}</div>
                            <select class="soft-input" data-schema-policy-field="__value__" ${disabledAttr}>
                                ${renderBooleanSelectOptions(currentValue)}
                            </select>
                        </label>
                    </div>
                `;
            }

            if (inlineEditor.kind === "branch") {
                const branchMode = typeof currentValue === "boolean"
                    ? "boolean"
                    : (currentValue && typeof currentValue === "object" && !Array.isArray(currentValue) ? "object" : "");
                const objectBranch = (inlineEditor.branches || []).find((branch) => branch.id === "object");
                const objectValue = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue) ? currentValue : {};
                const objectFieldsMarkup = (objectBranch?.fields || [])
                    .map((field) => renderWizardSchemaInlineField(item.id, field, objectValue[field.name], disabled))
                    .join("");

                return `
                    <div
                        class="wizard-shell-card"
                        data-schema-policy-card
                        data-schema-policy-id="${escapeHtml(item.id || "")}"
                        data-schema-policy-kind="branch"
                        data-schema-branch-object-managed-fields="${escapeHtml(((objectBranch?.managed_fields) || []).join(","))}"
                        data-settings-target="${escapeHtml(item.target || "")}">
                        <div>
                            <div class="wizard-shell-card-title">${escapeHtml(item.label || item.id || "")}</div>
                            <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                        </div>
                        <label>
                            <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_shell_branch_mode_label", "Mode"))}</div>
                            <select class="soft-input" data-schema-branch-mode ${disabledAttr}>
                                <option value=""></option>
                                <option value="boolean"${branchMode === "boolean" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_shell_branch_mode_simple", "Simple on/off"))}</option>
                                <option value="object"${branchMode === "object" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_shell_branch_mode_custom", "Custom cleanup rules"))}</option>
                            </select>
                        </label>
                        <div data-schema-branch-section="boolean"${branchMode === "boolean" ? "" : " hidden"}>
                            <label>
                                <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_shell_field_value", "Value"))}</div>
                                <select class="soft-input" data-schema-policy-field="__branch_boolean__" ${disabledAttr}>
                                    ${renderBooleanSelectOptions(typeof currentValue === "boolean" ? currentValue : null)}
                                </select>
                            </label>
                        </div>
                        <div data-schema-branch-section="object"${branchMode === "object" ? "" : " hidden"}>
                            <div class="wizard-grid">
                                ${objectFieldsMarkup}
                            </div>
                        </div>
                    </div>
                `;
            }

            if (inlineEditor.kind === "array-of-objects") {
                const rows = Array.isArray(currentValue) ? currentValue : [];
                const rowMarkup = rows.length > 0
                    ? rows.map((rowValue, index) => renderWizardSchemaArrayRow(item, inlineEditor, rowValue, index, disabled)).join("")
                    : `<div class="wizard-shell-empty">${escapeHtml(t("profiles.wizard_shell_array_empty", "No items yet."))}</div>`;

                return `
                    <div
                        class="wizard-shell-card"
                        data-schema-policy-card
                        data-schema-policy-id="${escapeHtml(item.id || "")}"
                        data-schema-policy-kind="array-of-objects"
                        data-settings-target="${escapeHtml(item.target || "")}">
                        <div class="wizard-search-engine-head">
                            <div>
                                <div class="wizard-shell-card-title">${escapeHtml(item.label || item.id || "")}</div>
                                <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                            </div>
                            <button type="button" class="button-base ghost-button" data-schema-array-add ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_array_add", "Add item"))}</button>
                        </div>
                        <div class="wizard-search-engine-list" data-schema-array-list>
                            ${rowMarkup}
                        </div>
                    </div>
                `;
            }

            if (inlineEditor.kind === "dictionary-object") {
                const entries = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue)
                    ? Object.entries(currentValue)
                    : [];
                const rowMarkup = entries.length > 0
                    ? entries.map(([entryKey, entryValue], index) => renderWizardSchemaDictionaryRow(item, inlineEditor, entryKey, entryValue, index, disabled)).join("")
                    : `<div class="wizard-shell-empty">${escapeHtml(t("profiles.wizard_shell_dictionary_empty", "No entries yet."))}</div>`;

                return `
                    <div
                        class="wizard-shell-card"
                        data-schema-policy-card
                        data-schema-policy-id="${escapeHtml(item.id || "")}"
                        data-schema-policy-kind="dictionary-object"
                        data-settings-target="${escapeHtml(item.target || "")}">
                        <div class="wizard-search-engine-head">
                            <div>
                                <div class="wizard-shell-card-title">${escapeHtml(item.label || item.id || "")}</div>
                                <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                            </div>
                            <button type="button" class="button-base ghost-button" data-schema-dict-add ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_dictionary_add", "Add entry"))}</button>
                        </div>
                        <div class="wizard-search-engine-list" data-schema-dict-list>
                            ${rowMarkup}
                        </div>
                    </div>
                `;
            }

            const fieldsMarkup = (inlineEditor.fields || [])
                .map((field) => renderWizardSchemaInlineField(item.id, field, currentObject[field.name], disabled))
                .join("");

            return `
                <div
                    class="wizard-shell-card"
                    data-schema-policy-card
                    data-schema-policy-id="${escapeHtml(item.id || "")}"
                    data-schema-policy-kind="object-card"
                    data-schema-managed-fields="${escapeHtml((inlineEditor.managed_fields || []).join(","))}"
                    data-settings-target="${escapeHtml(item.target || "")}">
                    <div>
                        <div class="wizard-shell-card-title">${escapeHtml(item.label || item.id || "")}</div>
                        <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                        ${["Authentication", "Certificates", "Cookies", "DNSOverHTTPS", "Handlers", "Permissions", "UserMessaging", "WebsiteFilter"].includes(item.id) ? `<div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-object-status></div>` : ""}
                    </div>
                    <div class="wizard-grid">
                        ${fieldsMarkup}
                    </div>
                    ${unsupportedNotice}
                </div>
            `;
        }

        function renderWizardSchemaInlineField(policyId, field, currentValue, disabled) {
            const disabledAttr = disabled ? "disabled" : "";
            const label = field.label || humanizeIdentifier(field.name || "");
            const fieldName = escapeHtml(field.name || "");
            const fieldPath = field.name || "";

            if (field.kind === "nested-object") {
                const nestedValue = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue)
                    ? currentValue
                    : {};
                const nestedFieldsMarkup = (field.fields || [])
                    .map((nestedField) => renderWizardSchemaNestedField(policyId, field.name, nestedField, nestedValue[nestedField.name], disabled))
                    .join("");
                const unsupportedNotice = (field.unsupported_field_count || 0) > 0
                    ? `<div class="wizard-input-hint">${escapeHtml(t("profiles.wizard_shell_nested_unsupported", "Some nested fields still fall back to raw JSON."))}</div>`
                    : "";

                return `
                    <div class="wizard-field-full" data-schema-policy-field="${fieldName}" data-schema-field-kind="nested-object" data-schema-nested-path="${escapeHtml(fieldPath)}">
                        <div class="wizard-search-engine-head">
                            <div>
                                <div class="field-label mb-1">${escapeHtml(label)}</div>
                                <div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-nested-status></div>
                            </div>
                        </div>
                        <div class="wizard-section-group">
                            <div class="wizard-grid">
                                ${nestedFieldsMarkup}
                            </div>
                            ${unsupportedNotice}
                        </div>
                    </div>
                `;
            }

            if (field.kind === "boolean-select") {
                return `
                    <label>
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <select class="soft-input" data-schema-policy-field="${fieldName}" data-schema-field-kind="boolean-select" ${disabledAttr}>
                            ${renderBooleanSelectOptions(currentValue)}
                        </select>
                    </label>
                `;
            }

            if (field.kind === "enum-select") {
                const options = [`<option value=""></option>`]
                    .concat((field.enum || []).map((option) => `<option value="${escapeHtml(option)}"${currentValue === option ? " selected" : ""}>${escapeHtml(option)}</option>`))
                    .join("");
                return `
                    <label>
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <select class="soft-input" data-schema-policy-field="${fieldName}" data-schema-field-kind="enum-select" ${disabledAttr}>
                            ${options}
                        </select>
                    </label>
                `;
            }

            if (field.kind === "string-list") {
                const serialized = Array.isArray(currentValue) ? currentValue.join("\n") : "";
                return `
                    <label class="wizard-field-full">
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <textarea class="soft-input" rows="3" data-schema-policy-field="${fieldName}" data-schema-field-kind="string-list" ${disabledAttr}>${escapeHtml(serialized)}</textarea>
                    </label>
                `;
            }

            if (field.kind === "true-map") {
                const serialized = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue)
                    ? Object.entries(currentValue)
                        .filter(([, enabled]) => enabled === true)
                        .map(([key]) => key)
                        .join("\n")
                    : "";
                return `
                    <label class="wizard-field-full">
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <textarea class="soft-input" rows="3" data-schema-policy-field="${fieldName}" data-schema-field-kind="true-map" ${disabledAttr}>${escapeHtml(serialized)}</textarea>
                        <div class="wizard-input-hint">${escapeHtml(t("profiles.wizard_shell_true_map_hint", "One hostname or origin per line."))}</div>
                    </label>
                `;
            }

            if (field.kind === "json") {
                const serialized = currentValue == null
                    ? ""
                    : JSON.stringify(currentValue, null, 2);
                return `
                    <label class="wizard-field-full">
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <textarea class="soft-input" rows="4" data-schema-policy-field="${fieldName}" data-schema-field-kind="json" ${disabledAttr}>${escapeHtml(serialized)}</textarea>
                        <div class="wizard-input-hint">${escapeHtml(t("profiles.wizard_shell_json_hint", "Use valid JSON for nested lists or objects."))}</div>
                    </label>
                `;
            }

            if (field.kind === "number") {
                return `
                    <label>
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <input type="number" class="soft-input" data-schema-policy-field="${fieldName}" data-schema-field-kind="number" value="${currentValue ?? ""}" ${disabledAttr} />
                    </label>
                `;
            }

            return `
                <label>
                    <div class="field-label mb-1">${escapeHtml(label)}</div>
                    <input type="text" class="soft-input" data-schema-policy-field="${fieldName}" data-schema-field-kind="text" value="${escapeHtml(currentValue ?? "")}" ${disabledAttr} />
                </label>
            `;
        }

        function renderWizardSchemaNestedField(policyId, parentFieldName, field, currentValue, disabled) {
            const disabledAttr = disabled ? "disabled" : "";
            const label = field.label || humanizeIdentifier(field.name || "");
            const fieldName = escapeHtml(field.name || "");
            const fieldPath = parentFieldName ? `${parentFieldName}.${field.name || ""}` : (field.name || "");

            if (field.kind === "nested-dictionary-object") {
                const entries = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue)
                    ? Object.entries(currentValue)
                    : [];
                const rowMarkup = entries.length > 0
                    ? entries.map(([entryKey, entryValue], index) => renderWizardSchemaNestedDictionaryRow(field, entryKey, entryValue, index, disabled)).join("")
                    : `<div class="wizard-shell-empty" data-schema-nested-empty>${escapeHtml(t("profiles.wizard_shell_dictionary_empty", "No entries yet."))}</div>`;

                return `
                    <div
                        class="wizard-field-full"
                        data-schema-nested-field="${fieldName}"
                        data-schema-nested-kind="nested-dictionary-object"
                        data-schema-nested-path="${escapeHtml(fieldPath)}"
                        data-schema-nested-label="${escapeHtml(label)}"
                        data-schema-nested-fields='${escapeHtml(JSON.stringify(field.fields || []))}'>
                        <div class="wizard-search-engine-head">
                            <div>
                                <div class="field-label mb-1">${escapeHtml(label)}</div>
                                <div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-nested-status></div>
                            </div>
                            <button type="button" class="button-base ghost-button" data-schema-nested-dict-add ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_dictionary_add", "Add entry"))}</button>
                        </div>
                        <div class="wizard-search-engine-list" data-schema-nested-dict-list>
                            ${rowMarkup}
                        </div>
                    </div>
                `;
            }

            if (field.kind === "nested-array-of-objects") {
                const rows = Array.isArray(currentValue) ? currentValue : [];
                const rowMarkup = rows.length > 0
                    ? rows.map((rowValue, index) => renderWizardSchemaNestedArrayRow(field, rowValue, index, disabled)).join("")
                    : `<div class="wizard-shell-empty" data-schema-nested-empty>${escapeHtml(t("profiles.wizard_shell_array_empty", "No items yet."))}</div>`;

                return `
                    <div
                        class="wizard-field-full"
                        data-schema-nested-field="${fieldName}"
                        data-schema-nested-kind="nested-array-of-objects"
                        data-schema-nested-path="${escapeHtml(fieldPath)}"
                        data-schema-nested-label="${escapeHtml(label)}"
                        data-schema-nested-fields='${escapeHtml(JSON.stringify(field.fields || []))}'>
                        <div class="wizard-search-engine-head">
                            <div>
                                <div class="field-label mb-1">${escapeHtml(label)}</div>
                                <div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-nested-status></div>
                            </div>
                            <button type="button" class="button-base ghost-button" data-schema-nested-array-add ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_array_add", "Add item"))}</button>
                        </div>
                        <div class="wizard-search-engine-list" data-schema-nested-array-list>
                            ${rowMarkup}
                        </div>
                    </div>
                `;
            }

            if (field.kind === "nested-object") {
                const nestedValue = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue)
                    ? currentValue
                    : {};
                const nestedFieldsMarkup = (field.fields || [])
                    .map((nestedField) => renderWizardSchemaNestedField(policyId, fieldPath, nestedField, nestedValue[nestedField.name], disabled))
                    .join("");
                const unsupportedNotice = (field.unsupported_field_count || 0) > 0
                    ? `<div class="wizard-input-hint">${escapeHtml(t("profiles.wizard_shell_nested_unsupported", "Some nested fields still fall back to raw JSON."))}</div>`
                    : "";

                return `
                    <div class="wizard-field-full" data-schema-nested-field="${fieldName}" data-schema-nested-kind="nested-object" data-schema-nested-path="${escapeHtml(fieldPath)}">
                        <div class="wizard-search-engine-head">
                            <div>
                                <div class="field-label mb-1">${escapeHtml(label)}</div>
                                <div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-nested-status></div>
                            </div>
                        </div>
                        <div class="wizard-section-group">
                            <div class="wizard-grid">
                                ${nestedFieldsMarkup}
                            </div>
                            ${unsupportedNotice}
                        </div>
                    </div>
                `;
            }

            if (field.kind === "boolean-select") {
                return `
                    <label>
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <select class="soft-input" data-schema-nested-field="${fieldName}" data-schema-nested-kind="boolean-select" ${disabledAttr}>
                            ${renderBooleanSelectOptions(currentValue)}
                        </select>
                    </label>
                `;
            }

            if (field.kind === "enum-select") {
                const options = [`<option value=""></option>`]
                    .concat((field.enum || []).map((option) => `<option value="${escapeHtml(option)}"${currentValue === option ? " selected" : ""}>${escapeHtml(option)}</option>`))
                    .join("");
                return `
                    <label>
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <select class="soft-input" data-schema-nested-field="${fieldName}" data-schema-nested-kind="enum-select" ${disabledAttr}>
                            ${options}
                        </select>
                    </label>
                `;
            }

            if (field.kind === "string-list") {
                const serialized = Array.isArray(currentValue) ? currentValue.join("\n") : "";
                return `
                    <label class="wizard-field-full">
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <textarea class="soft-input" rows="3" data-schema-nested-field="${fieldName}" data-schema-nested-kind="string-list" ${disabledAttr}>${escapeHtml(serialized)}</textarea>
                    </label>
                `;
            }

            if (field.kind === "true-map") {
                const serialized = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue)
                    ? Object.entries(currentValue)
                        .filter(([, enabled]) => enabled === true)
                        .map(([key]) => key)
                        .join("\n")
                    : "";
                return `
                    <label class="wizard-field-full">
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <textarea class="soft-input" rows="3" data-schema-nested-field="${fieldName}" data-schema-nested-kind="true-map" ${disabledAttr}>${escapeHtml(serialized)}</textarea>
                        <div class="wizard-input-hint">${escapeHtml(t("profiles.wizard_shell_true_map_hint", "One hostname or origin per line."))}</div>
                    </label>
                `;
            }

            if (field.kind === "json") {
                const serialized = currentValue == null
                    ? ""
                    : JSON.stringify(currentValue, null, 2);
                return `
                    <label class="wizard-field-full">
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <textarea class="soft-input" rows="4" data-schema-nested-field="${fieldName}" data-schema-nested-kind="json" ${disabledAttr}>${escapeHtml(serialized)}</textarea>
                        <div class="wizard-input-hint">${escapeHtml(t("profiles.wizard_shell_json_hint", "Use valid JSON for nested lists or objects."))}</div>
                    </label>
                `;
            }

            if (field.kind === "number") {
                return `
                    <label>
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <input type="number" class="soft-input" data-schema-nested-field="${fieldName}" data-schema-nested-kind="number" value="${currentValue ?? ""}" ${disabledAttr} />
                    </label>
                `;
            }

            return `
                <label>
                    <div class="field-label mb-1">${escapeHtml(label)}</div>
                    <input type="text" class="soft-input" data-schema-nested-field="${fieldName}" data-schema-nested-kind="text" value="${escapeHtml(currentValue ?? "")}" ${disabledAttr} />
                </label>
            `;
        }

        function renderWizardSchemaNestedArrayRow(field, rowValue, index, disabled) {
            const disabledAttr = disabled ? "disabled" : "";
            const currentObject = rowValue && typeof rowValue === "object" && !Array.isArray(rowValue) ? rowValue : {};
            const rowTitle = currentObject.name
                || currentObject.Title
                || currentObject.URL
                || currentObject.path
                || `${field.label || field.name || "Item"} ${index + 1}`;
            const fieldsMarkup = (field.fields || [])
                .map((nestedField) => renderWizardSchemaNestedField("", field.name || "", nestedField, currentObject[nestedField.name], disabled))
                .join("");

            return `
                <div class="wizard-search-engine-card" data-schema-nested-array-row data-schema-nested-array-index="${index}">
                    <div class="wizard-search-engine-head">
                        <div>
                            <div class="wizard-search-engine-title">${escapeHtml(rowTitle)}</div>
                            <div class="wizard-search-engine-meta">${escapeHtml(t("profiles.wizard_shell_array_item_meta", "Array item"))} ${index + 1}</div>
                        </div>
                        <button type="button" class="button-base danger-button" data-schema-nested-array-remove ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_array_remove", "Remove"))}</button>
                    </div>
                    <div class="wizard-grid">
                        ${fieldsMarkup}
                    </div>
                </div>
            `;
        }

        function renderWizardSchemaNestedDictionaryRow(field, entryKey, entryValue, index, disabled) {
            const disabledAttr = disabled ? "disabled" : "";
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            const rowTitle = entryKey || `${field.label || field.name || "Entry"} ${index + 1}`;
            const fieldsMarkup = (field.fields || [])
                .map((nestedField) => renderWizardSchemaNestedField("", field.name || "", nestedField, currentObject[nestedField.name], disabled))
                .join("");

            return `
                <div class="wizard-search-engine-card" data-schema-nested-dict-row data-schema-nested-dict-index="${index}">
                    <div class="wizard-search-engine-head">
                        <div>
                            <div class="wizard-search-engine-title">${escapeHtml(rowTitle)}</div>
                            <div class="wizard-search-engine-meta">${escapeHtml(t("profiles.wizard_shell_dictionary_item_meta", "Dictionary entry"))} ${index + 1}</div>
                        </div>
                        <button type="button" class="button-base danger-button" data-schema-nested-dict-remove ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_dictionary_remove", "Remove"))}</button>
                    </div>
                    <label class="wizard-field-full">
                        <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_shell_dictionary_key_label", "Entry key"))}</div>
                        <input type="text" class="soft-input" data-schema-nested-dict-key value="${escapeHtml(entryKey || "")}" ${disabledAttr} />
                    </label>
                    <div class="wizard-grid">
                        ${fieldsMarkup}
                    </div>
                </div>
            `;
        }

        function renderBooleanSelectOptions(currentValue) {
            const selected = formatBooleanSelectValue(currentValue);
            return `
                <option value=""></option>
                <option value="true"${selected === "true" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_shell_boolean_true", "Enabled"))}</option>
                <option value="false"${selected === "false" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_shell_boolean_false", "Disabled"))}</option>
            `;
        }

        function renderWizardSchemaArrayRow(item, inlineEditor, rowValue, index, disabled) {
            const disabledAttr = disabled ? "disabled" : "";
            const currentObject = rowValue && typeof rowValue === "object" && !Array.isArray(rowValue) ? rowValue : {};
            const rowTitle = currentObject.Title
                || currentObject.name
                || currentObject.toplevel_name
                || currentObject.URL
                || currentObject.url
                || `${item.label || item.id} ${index + 1}`;
            const fieldsMarkup = (inlineEditor.fields || [])
                .map((field) => renderWizardSchemaInlineField(item.id, field, currentObject[field.name], disabled))
                .join("");
            const statusMarkup = ["Bookmarks", "ManagedBookmarks"].includes(item.id)
                ? `<div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-array-status></div>`
                : "";

            return `
                <div class="wizard-search-engine-card" data-schema-array-row data-schema-array-index="${index}">
                    <div class="wizard-search-engine-head">
                        <div>
                            <div class="wizard-search-engine-title">${escapeHtml(rowTitle)}</div>
                            <div class="wizard-search-engine-meta">${escapeHtml(t("profiles.wizard_shell_array_item_meta", "Array item"))} ${index + 1}</div>
                            ${statusMarkup}
                        </div>
                        <button type="button" class="button-base danger-button" data-schema-array-remove data-schema-array-index="${index}" ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_array_remove", "Remove"))}</button>
                    </div>
                    <div class="wizard-grid">
                        ${fieldsMarkup}
                    </div>
                </div>
            `;
        }

        function renderWizardSchemaDictionaryRow(item, inlineEditor, entryKey, entryValue, index, disabled) {
            const disabledAttr = disabled ? "disabled" : "";
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            const rowTitle = entryKey || `${item.label || item.id} ${index + 1}`;
            const fieldsMarkup = (inlineEditor.fields || [])
                .map((field) => renderWizardSchemaInlineField(item.id, field, currentObject[field.name], disabled))
                .join("");
            const statusMarkup = item.id === "ExtensionSettings"
                ? `<div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-dict-status></div>`
                : "";

            return `
                <div class="wizard-search-engine-card" data-schema-dict-row data-schema-dict-index="${index}">
                    <div class="wizard-search-engine-head">
                        <div>
                            <div class="wizard-search-engine-title">${escapeHtml(rowTitle)}</div>
                            <div class="wizard-search-engine-meta">${escapeHtml(t("profiles.wizard_shell_dictionary_item_meta", "Dictionary entry"))} ${index + 1}</div>
                            ${statusMarkup}
                        </div>
                        <button type="button" class="button-base danger-button" data-schema-dict-remove data-schema-dict-index="${index}" ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_dictionary_remove", "Remove"))}</button>
                    </div>
                    <label class="wizard-field-full">
                        <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_shell_dictionary_key_label", "Entry key"))}</div>
                        <input type="text" class="soft-input" data-schema-dict-key value="${escapeHtml(entryKey || "")}" ${disabledAttr} />
                    </label>
                    <div class="wizard-grid">
                        ${fieldsMarkup}
                    </div>
                </div>
            `;
        }

        const actions = window.BPMProfilesSchemaShellActions.create({
            documentRef,
            dependencies: {
                t,
                escapeHtml,
                fromEditorValue,
                toEditorValue,
                setStatus,
                parseBooleanSelectValue,
            },
            state: {
                getEditor,
                setCurrentRaw,
            },
            helpers: {
                ...valueIO,
                renderWizardSchemaNestedArrayRow,
                renderWizardSchemaNestedDictionaryRow,
            },
        });

        function renderWizardSchemaShellPreferenceBucket(container, items, emptyMessage) {
            if (!container) return;

            if (!Array.isArray(items) || items.length === 0) {
                container.innerHTML = `<div class="wizard-shell-empty">${escapeHtml(emptyMessage)}</div>`;
                return;
            }

            container.innerHTML = items
                .map((item) => {
                    const meta = t(
                        "profiles.wizard_shell_preferences_meta",
                        "{prefixes} prefixes • {presets} presets",
                    )
                        .replace("{prefixes}", String(item.prefix_count || 0))
                        .replace("{presets}", String(item.preset_count || 0));

                    return `
                        <button
                            type="button"
                            class="button-base ghost-button wizard-shell-item"
                            data-wizard-shell-jump="preferences"
                            data-settings-jump-target="${escapeHtml(item.target || "")}">
                            <span class="wizard-shell-item-title">${escapeHtml(t(item.title_key, item.fallback || item.id || ""))}</span>
                            <span class="wizard-shell-item-meta">${escapeHtml(meta)}</span>
                        </button>
                    `;
                })
                .join("");
        }

        return {
            renderWizardSchemaShell,
            renderSchemaPolicyReviewState: review.renderSchemaPolicyReviewState,
            applySchemaPolicyFromCard: actions.applySchemaPolicyFromCard,
            refreshSchemaNestedArrayRows: actions.refreshSchemaNestedArrayRows,
            refreshSchemaNestedDictionaryRows: actions.refreshSchemaNestedDictionaryRows,
            appendSchemaNestedArrayItem: actions.appendSchemaNestedArrayItem,
            removeSchemaNestedArrayItem: actions.removeSchemaNestedArrayItem,
            appendSchemaNestedDictionaryEntry: actions.appendSchemaNestedDictionaryEntry,
            removeSchemaNestedDictionaryEntry: actions.removeSchemaNestedDictionaryEntry,
            appendSchemaArrayItem: actions.appendSchemaArrayItem,
            removeSchemaArrayItem: actions.removeSchemaArrayItem,
            appendSchemaDictionaryEntry: actions.appendSchemaDictionaryEntry,
            removeSchemaDictionaryEntry: actions.removeSchemaDictionaryEntry,
            getAuthenticationObjectSummary: review.getAuthenticationObjectSummary,
            getCertificatesObjectSummary: review.getCertificatesObjectSummary,
            getDnsOverHttpsObjectSummary: review.getDnsOverHttpsObjectSummary,
            getUserMessagingObjectSummary: review.getUserMessagingObjectSummary,
        };
    }

    window.BPMProfilesSchemaShellSections = { create };
})();
