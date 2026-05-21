(() => {
    function create({
        documentRef = document,
        elements = {},
        dependencies = {},
        allSettingsCategoryCatalog = {},
        wizardPreferencesCatalog = {},
        wizardSchemaShellCatalog = {},
    }) {
        const {
            t,
            escapeHtml,
            getActiveWizardSchemaVersion,
            readWizardSchemaSource,
            getValidationIssues,
            onSelectionChange,
        } = dependencies;
        const {
            allSettingsListSummaryEl,
            allSettingsReviewSummaryEl,
            allSettingsReviewActionsEl,
            allSettingsListEl,
            allSettingsListEmptyEl,
            allSettingsFilterButtons = [],
        } = elements;
        let activeFilter = "all";
        let selectedEntryKey = "";
        let lastEntries = [];

        function entryKey(entry) {
            return `${entry.kind}:${entry.id}`;
        }

        function hasOwn(source, key) {
            return Boolean(source && Object.prototype.hasOwnProperty.call(source, key));
        }

        function categoryTitle(categoryId) {
            const category = allSettingsCategoryCatalog.categories_by_id?.[categoryId]
                || allSettingsCategoryCatalog.categories_by_id?.["raw-unmapped"];
            return category
                ? (t(category.title_key) || category.fallback || category.id)
                : "";
        }

        function formatStructuredValue(value) {
            if (Array.isArray(value)) {
                return t("profiles.settings_list_value_array")
                    .replace("{count}", String(value.length));
            }
            if (value && typeof value === "object") {
                return t("profiles.settings_list_value_object")
                    .replace("{count}", String(Object.keys(value).length));
            }
            if (typeof value === "string") {
                return value.length > 72 ? `${value.slice(0, 69)}...` : value;
            }
            if (value === undefined) {
                return t("profiles.settings_list_value_not_configured");
            }
            return JSON.stringify(value);
        }

        function formatPreferenceStatus(status) {
            const keyByStatus = {
                default: "profiles.wizard_preferences_status_default",
                locked: "profiles.wizard_preferences_status_locked",
                user: "profiles.wizard_preferences_status_user",
                clear: "profiles.wizard_preferences_status_clear",
            };
            return keyByStatus[status] ? t(keyByStatus[status], status) : status;
        }

        function formatPreferenceType(type) {
            const keyByType = {
                boolean: "profiles.wizard_preferences_type_boolean",
                number: "profiles.wizard_preferences_type_number",
                string: "profiles.wizard_preferences_type_string",
            };
            return keyByType[type] ? t(keyByType[type], type) : type;
        }

        function formatPreferenceEntry(entry) {
            if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
                return formatStructuredValue(entry);
            }

            const parts = [];
            if (hasOwn(entry, "Value")) {
                parts.push(formatStructuredValue(entry.Value));
            } else if (entry.Status === "clear") {
                parts.push(formatPreferenceStatus("clear"));
            }
            if (entry.Status && entry.Status !== "clear") {
                parts.push(formatPreferenceStatus(entry.Status));
            }
            if (entry.Type) {
                parts.push(formatPreferenceType(entry.Type));
            }

            return parts.join(" • ")
                || t("profiles.settings_list_value_not_configured");
        }

        function resolvePreferenceSection(prefName) {
            const sections = Array.isArray(wizardPreferencesCatalog.sections)
                ? wizardPreferencesCatalog.sections
                : [];
            const trimmed = String(prefName || "").trim();
            if (!trimmed) return "";

            return sections.find((section) =>
                Array.isArray(section.prefixes)
                && section.prefixes.some((prefix) => trimmed === prefix || trimmed.startsWith(prefix))
            )?.id || "";
        }

        function buildPolicyEntries(sourceData) {
            const schemaVersion = getActiveWizardSchemaVersion();
            const shellSteps = Array.isArray(wizardSchemaShellCatalog.steps)
                ? wizardSchemaShellCatalog.steps
                : [];
            const channelData = wizardSchemaShellCatalog.channels?.[schemaVersion];
            const entries = [];
            const seenIds = new Set();

            shellSteps.forEach((stepMeta) => {
                const stepData = channelData?.steps?.[String(stepMeta.step)] || {};
                [
                    ["recommended", stepData.recommended],
                    ["additional", stepData.additional],
                    ["raw_fallback", stepData.raw_fallback],
                ].forEach(([bucketKey, bucketItems]) => {
                    (Array.isArray(bucketItems) ? bucketItems : []).forEach((item) => {
                        if (!item?.id || seenIds.has(item.id)) return;
                        seenIds.add(item.id);

                        const configured = hasOwn(sourceData, item.id);
                        const categoryId = allSettingsCategoryCatalog.policy_section_to_category_id?.[item.section_id]
                            || "raw-unmapped";
                        entries.push({
                            id: item.id,
                            label: item.id,
                            kind: "policy",
                            kindLabel: t("profiles.settings_list_kind_policy"),
                            categoryId,
                            categoryLabel: categoryTitle(categoryId),
                            configured,
                            guided: bucketKey === "recommended",
                            deprecated: Boolean(item.deprecated),
                            rawFallback: bucketKey === "raw_fallback" || item.support_level === "fallback",
                            unknown: false,
                            schemaItem: item,
                            target: item.target || `policy:${item.id}`,
                            value: configured
                                ? formatStructuredValue(sourceData[item.id])
                                : t("profiles.settings_list_value_not_configured"),
                        });
                    });
                });
            });

            return entries;
        }

        function buildPreferenceEntries(sourceData) {
            const preferences = sourceData?.Preferences && typeof sourceData.Preferences === "object"
                && !Array.isArray(sourceData.Preferences)
                ? sourceData.Preferences
                : {};
            const knownPreferences = Array.isArray(wizardPreferencesCatalog.known_preferences)
                ? wizardPreferencesCatalog.known_preferences
                : [];
            const entries = [];
            const knownPrefNames = new Set();

            knownPreferences.forEach((item) => {
                if (!item?.pref) return;
                knownPrefNames.add(item.pref);

                const configured = hasOwn(preferences, item.pref);
                const categoryId = allSettingsCategoryCatalog.preference_section_to_category_id?.[item.section_id]
                    || "raw-unmapped";
                entries.push({
                    id: item.pref,
                    label: item.pref,
                    kind: "preference",
                    kindLabel: t("profiles.settings_list_kind_preference"),
                    categoryId,
                    categoryLabel: categoryTitle(categoryId),
                    configured,
                    guided: false,
                    deprecated: false,
                    rawFallback: false,
                    unknown: false,
                    target: `known-preference:${item.pref}`,
                    value: configured
                        ? formatPreferenceEntry(preferences[item.pref])
                        : t("profiles.settings_list_value_not_configured"),
                });
            });

            Object.entries(preferences).forEach(([prefName, entry]) => {
                if (knownPrefNames.has(prefName)) return;

                const sectionId = resolvePreferenceSection(prefName);
                const categoryId = allSettingsCategoryCatalog.preference_section_to_category_id?.[sectionId]
                    || "raw-unmapped";
                entries.push({
                    id: prefName,
                    label: prefName,
                    kind: "preference",
                    kindLabel: t("profiles.settings_list_kind_preference"),
                    categoryId,
                    categoryLabel: categoryTitle(categoryId),
                    configured: true,
                    guided: false,
                    deprecated: false,
                    rawFallback: false,
                    unknown: false,
                    target: sectionId ? `pref-section:${sectionId}` : "pref-section:general",
                    value: formatPreferenceEntry(entry),
                });
            });

            return entries;
        }

        function buildUnknownPolicyEntries(sourceData, knownPolicyIds) {
            return Object.keys(sourceData || {})
                .filter((key) => key !== "Preferences" && !knownPolicyIds.has(key))
                .map((key) => ({
                    id: key,
                    label: key,
                    kind: "policy",
                    kindLabel: t("profiles.settings_list_kind_policy"),
                    categoryId: "raw-unmapped",
                    categoryLabel: categoryTitle("raw-unmapped"),
                    configured: true,
                    guided: false,
                    deprecated: false,
                    rawFallback: false,
                    unknown: true,
                    target: "settings-schema-shell-step-8",
                    value: formatStructuredValue(sourceData[key]),
                }));
        }

        function getIssuesByEntryId(entries) {
            const entryIds = new Set(entries.map((entry) => entry.id));
            const issuesByEntryId = new Map();
            (Array.isArray(getValidationIssues?.()) ? getValidationIssues() : []).forEach((issue) => {
                let entryId = "";
                if (entryIds.has(issue?.policy)) {
                    entryId = issue.policy;
                } else if (issue?.policy === "Preferences" && Array.isArray(issue.path)) {
                    entryId = issue.path.find((part) => entryIds.has(part)) || "";
                }
                if (!entryId) return;
                const existing = issuesByEntryId.get(entryId) || [];
                existing.push(issue);
                issuesByEntryId.set(entryId, existing);
            });
            return issuesByEntryId;
        }

        function sortEntries(entries) {
            const categoryOrder = Object.fromEntries(
                (Array.isArray(allSettingsCategoryCatalog.categories)
                    ? allSettingsCategoryCatalog.categories
                    : []
                ).map((category, index) => [category.id, index]),
            );

            return entries.sort((left, right) => {
                const categoryDelta = (categoryOrder[left.categoryId] ?? Number.MAX_SAFE_INTEGER)
                    - (categoryOrder[right.categoryId] ?? Number.MAX_SAFE_INTEGER);
                if (categoryDelta !== 0) return categoryDelta;
                if (left.configured !== right.configured) return left.configured ? -1 : 1;
                if (left.kind !== right.kind) return left.kind.localeCompare(right.kind);
                return left.label.localeCompare(right.label);
            });
        }

        function kindLabel(kind) {
            return kind === "preference"
                ? t("profiles.settings_list_kind_preference")
                : t("profiles.settings_list_kind_policy");
        }

        function stateLabel(configured) {
            return configured
                ? t("profiles.settings_list_state_configured")
                : t("profiles.settings_list_state_available");
        }

        function renderSummary(entries, visibleEntries = entries) {
            if (!allSettingsListSummaryEl) return;

            const configured = entries.filter((entry) => entry.configured).length;
            const policies = entries.filter((entry) => entry.kind === "policy").length;
            const preferences = entries.filter((entry) => entry.kind === "preference").length;
            const summaryKey = activeFilter === "all"
                ? "profiles.settings_list_summary"
                : "profiles.settings_list_summary_filtered";
            allSettingsListSummaryEl.textContent = t(summaryKey)
                .replace("{total}", String(entries.length))
                .replace("{visible}", String(visibleEntries.length))
                .replace("{configured}", String(configured))
                .replace("{policies}", String(policies))
                .replace("{preferences}", String(preferences));
        }

        function renderRows(entries) {
            if (!allSettingsListEl) return;

            allSettingsListEl.innerHTML = entries
                .map((entry) => {
                    const currentEntryKey = entryKey(entry);
                    const selected = currentEntryKey === selectedEntryKey;
                    return `
                    <button
                        type="button"
                        class="all-settings-list-row${selected ? " is-selected" : ""}"
                        data-settings-entry-id="${escapeHtml(entry.id)}"
                        data-settings-entry-kind="${escapeHtml(entry.kind)}"
                        data-settings-entry-category="${escapeHtml(entry.categoryId)}"
                        data-settings-entry-state="${entry.configured ? "configured" : "available"}"
                        data-settings-entry-guided="${entry.guided ? "true" : "false"}"
                        data-settings-entry-invalid="${entry.invalid ? "true" : "false"}"
                        data-settings-entry-deprecated="${entry.deprecated ? "true" : "false"}"
                        data-settings-entry-raw="${entry.rawFallback ? "true" : "false"}"
                        data-settings-entry-unknown="${entry.unknown ? "true" : "false"}"
                        aria-current="${selected ? "true" : "false"}">
                        <span class="all-settings-list-cell all-settings-list-cell--setting"
                            data-label="${escapeHtml(t("profiles.settings_list_column_setting"))}">
                            <span class="all-settings-list-setting-key">${escapeHtml(entry.label)}</span>
                        </span>
                        <span class="all-settings-list-cell"
                            data-label="${escapeHtml(t("profiles.settings_list_column_kind"))}">
                            ${escapeHtml(kindLabel(entry.kind))}
                        </span>
                        <span class="all-settings-list-cell"
                            data-label="${escapeHtml(t("profiles.settings_list_column_category"))}">
                            ${escapeHtml(categoryTitle(entry.categoryId))}
                        </span>
                        <span class="all-settings-list-cell"
                            data-label="${escapeHtml(t("profiles.settings_list_column_state"))}">
                            <span class="all-settings-list-state" data-state="${entry.configured ? "configured" : "available"}">
                                ${escapeHtml(stateLabel(entry.configured))}
                            </span>
                        </span>
                        <span class="all-settings-list-cell all-settings-list-cell--value"
                            data-label="${escapeHtml(t("profiles.settings_list_column_value"))}">
                            ${escapeHtml(entry.value)}
                        </span>
                    </button>
                `;
                })
                .join("");
        }

        function entryMatchesFilter(entry, filterValue) {
            if (filterValue === "configured") return entry.configured;
            if (filterValue === "available") return !entry.configured;
            if (filterValue === "guided-covered") return entry.guided;
            if (filterValue === "all-settings-only") return !entry.guided;
            if (filterValue === "invalid") return entry.invalid;
            if (filterValue === "deprecated") return entry.deprecated;
            if (filterValue === "raw") return entry.rawFallback;
            if (filterValue === "unknown") return entry.unknown;
            return true;
        }

        function entryMatchesReview(entry, reviewKind) {
            if (reviewKind === "unknown") return entry.unknown && entry.configured;
            if (reviewKind === "deprecated") return entry.deprecated && entry.configured;
            if (reviewKind === "raw") return entry.rawFallback && entry.configured;
            if (reviewKind === "invalid") return entry.invalid;
            return false;
        }

        function buildReviewItems(entries) {
            return [
                {
                    kind: "unknown",
                    title: t("profiles.settings_review_unknown_title"),
                    body: t("profiles.settings_review_unknown_body"),
                    tone: "warn",
                    entries: entries.filter((entry) => entryMatchesReview(entry, "unknown")),
                },
                {
                    kind: "deprecated",
                    title: t("profiles.settings_review_deprecated_title"),
                    body: t("profiles.settings_review_deprecated_body"),
                    tone: "warn",
                    entries: entries.filter((entry) => entryMatchesReview(entry, "deprecated")),
                },
                {
                    kind: "raw",
                    title: t("profiles.settings_review_raw_title"),
                    body: t("profiles.settings_review_raw_body"),
                    tone: "neutral",
                    entries: entries.filter((entry) => entryMatchesReview(entry, "raw")),
                },
                {
                    kind: "invalid",
                    title: t("profiles.settings_review_invalid_title"),
                    body: t("profiles.settings_review_invalid_body"),
                    tone: "error",
                    entries: entries.filter((entry) => entryMatchesReview(entry, "invalid")),
                },
            ];
        }

        function renderReview(entries) {
            if (!allSettingsReviewSummaryEl && !allSettingsReviewActionsEl) return;

            const reviewItems = buildReviewItems(entries);
            const total = reviewItems.reduce((count, item) => count + item.entries.length, 0);
            if (allSettingsReviewSummaryEl) {
                allSettingsReviewSummaryEl.textContent = t(
                    total > 0
                        ? "profiles.settings_review_summary_attention"
                        : "profiles.settings_review_summary_clear",
                ).replace("{count}", String(total));
            }
            if (!allSettingsReviewActionsEl) return;

            allSettingsReviewActionsEl.innerHTML = reviewItems
                .map((item) => {
                    const count = item.entries.length;
                    const disabled = count <= 0;
                    return `
                        <button
                            type="button"
                            class="all-settings-review-card"
                            data-settings-review-filter="${escapeHtml(item.kind)}"
                            data-settings-review-count="${count}"
                            data-tone="${escapeHtml(item.tone)}"
                            ${disabled ? "disabled" : ""}>
                            <span class="all-settings-review-card-top">
                                <span class="all-settings-review-card-title">${escapeHtml(item.title)}</span>
                                <span class="all-settings-review-card-count">${count}</span>
                            </span>
                            <span class="all-settings-review-card-body">${escapeHtml(item.body)}</span>
                            <span class="all-settings-review-card-action">
                                ${escapeHtml(t(disabled ? "profiles.settings_review_clear" : "profiles.settings_review_open"))}
                            </span>
                        </button>
                    `;
                })
                .join("");
        }

        function updateFilterButtons(entries) {
            allSettingsFilterButtons.forEach((button) => {
                const filterValue = button.dataset.settingsListFilter || "all";
                const count = entries.filter((entry) => entryMatchesFilter(entry, filterValue)).length;
                button.classList.toggle("is-active", filterValue === activeFilter);
                button.setAttribute("aria-pressed", filterValue === activeFilter ? "true" : "false");
                const countEl = button.querySelector("[data-settings-list-filter-count]");
                if (countEl) {
                    countEl.textContent = String(count);
                }
            });
        }

        function applyFilter(entries) {
            const visibleEntries = entries.filter((entry) => entryMatchesFilter(entry, activeFilter));
            const entriesByKey = new Map(entries.map((entry) => [`${entry.kind}:${entry.id}`, entry]));
            if (allSettingsListEl) {
                allSettingsListEl.querySelectorAll("[data-settings-entry-id]").forEach((row) => {
                    const entry = entriesByKey.get(
                        `${row.dataset.settingsEntryKind || ""}:${row.dataset.settingsEntryId || ""}`,
                    );
                    row.hidden = !entry || !entryMatchesFilter(entry, activeFilter);
                });
            }
            if (allSettingsListEmptyEl) {
                allSettingsListEmptyEl.hidden = visibleEntries.length > 0;
                allSettingsListEmptyEl.textContent = activeFilter === "all"
                    ? t("profiles.settings_list_empty")
                    : t("profiles.settings_list_filtered_empty");
            }
            renderSummary(entries, visibleEntries);
            updateFilterButtons(entries);
        }

        function render() {
            if (!allSettingsListEl) return;
            const entries = collectEntries();
            lastEntries = entries;
            const entryKeys = new Set(entries.map((entry) => entryKey(entry)));
            if (!selectedEntryKey || !entryKeys.has(selectedEntryKey)) {
                const fallbackEntry = entries.find((entry) => entry.configured) || entries[0] || null;
                selectedEntryKey = fallbackEntry ? entryKey(fallbackEntry) : "";
            }

            renderRows(entries);
            renderReview(entries);
            applyFilter(entries);
            onSelectionChange?.(
                entries.find((entry) => entryKey(entry) === selectedEntryKey) || null,
            );
        }

        function collectEntries() {
            const sourceState = readWizardSchemaSource();
            const sourceData = sourceState.ok && sourceState.data && typeof sourceState.data === "object"
                ? sourceState.data
                : {};
            const policyEntries = buildPolicyEntries(sourceData);
            const entries = sortEntries([
                ...policyEntries,
                ...buildPreferenceEntries(sourceData),
                ...buildUnknownPolicyEntries(sourceData, new Set(policyEntries.map((entry) => entry.id))),
            ]);
            const issuesByEntryId = getIssuesByEntryId(entries);
            entries.forEach((entry) => {
                entry.issues = issuesByEntryId.get(entry.id) || [];
                entry.invalid = entry.issues.length > 0;
            });
            return entries;
        }

        function getSearchEntries() {
            return collectEntries();
        }

        function findRenderedRow(kind, id) {
            return Array.from(allSettingsListEl?.querySelectorAll("[data-settings-entry-id]") || [])
                .find((row) =>
                    row.dataset.settingsEntryKind === kind
                    && row.dataset.settingsEntryId === id
                ) || null;
        }

        function selectEntry(kind, id) {
            const entries = collectEntries();
            const match = entries.find((entry) => entry.kind === kind && entry.id === id);
            if (!match) return null;
            activeFilter = "all";
            selectedEntryKey = entryKey(match);
            render();
            return findRenderedRow(kind, id);
        }

        function findTarget(target) {
            const normalizedTarget = String(target || "").trim();
            if (!normalizedTarget.startsWith("all-settings-entry:")) return null;
            const parts = normalizedTarget.split(":");
            const kind = parts[1] || "";
            const id = parts.slice(2).join(":");
            if (!kind || !id) return null;
            return selectEntry(kind, id);
        }

        allSettingsListEl?.addEventListener("click", (event) => {
            const row = event.target.closest("[data-settings-entry-id]");
            if (!row) return;
            selectedEntryKey = `${row.dataset.settingsEntryKind || ""}:${row.dataset.settingsEntryId || ""}`;
            allSettingsListEl.querySelectorAll("[data-settings-entry-id]").forEach((entryRow) => {
                const isSelected = entryRow === row;
                entryRow.classList.toggle("is-selected", isSelected);
                entryRow.setAttribute("aria-current", isSelected ? "true" : "false");
            });
            render();
        });

        allSettingsFilterButtons.forEach((button) => {
            button.addEventListener("click", () => {
                activeFilter = button.dataset.settingsListFilter || "all";
                render();
            });
        });

        allSettingsReviewActionsEl?.addEventListener("click", (event) => {
            const target = event.target instanceof Element ? event.target : event.target?.parentElement;
            const action = target?.closest("[data-settings-review-filter]");
            if (!action || action.disabled) return;
            const reviewKind = action.dataset.settingsReviewFilter || "all";
            const reviewItem = buildReviewItems(lastEntries).find((item) => item.kind === reviewKind);
            const firstEntry = reviewItem?.entries?.[0] || null;
            activeFilter = reviewKind;
            if (firstEntry) {
                selectedEntryKey = entryKey(firstEntry);
            }
            render();
            window.requestAnimationFrame?.(() => {
                allSettingsListEl
                    ?.querySelector(".all-settings-list-row.is-selected")
                    ?.scrollIntoView({ block: "nearest", inline: "nearest" });
            });
        });

        return {
            render,
            getSearchEntries,
            findTarget,
        };
    }

    window.BPMProfilesAllSettingsList = { create };
})();
