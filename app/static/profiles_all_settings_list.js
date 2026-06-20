(() => {
    const VISIBLE_ENTRY_BUDGET = 7;
    const VISIBLE_ENTRY_WINDOW_SIZE = 50;

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
            getComplianceInfo,
            getManualEdits,
            getCurrentLang,
            onSelectionChange,
            onModeChange,
            allSettingsRouteState = window.BPMProfilesAllSettingsState?.create?.(),
            settingsInventory = window.BPMProfilesSettingsInventory?.create?.({
                dependencies: {
                    t,
                    getActiveWizardSchemaVersion,
                    getValidationIssues,
                },
                allSettingsCategoryCatalog,
                wizardPreferencesCatalog,
                wizardSchemaShellCatalog,
            }),
        } = dependencies;
        const {
            allSettingsConfiguredSummaryEl,
            allSettingsSourceFiltersEl,
            allSettingsListSummaryEl,
            allSettingsReviewSummaryEl,
            allSettingsReviewActionsEl,
            allSettingsListEl,
            allSettingsListEmptyEl,
            allSettingsListBudgetEl,
            allSettingsFilterButtons = [],
            allSettingsSourceFilterButtons = [],
        } = elements;
        const routeState = allSettingsRouteState || window.BPMProfilesAllSettingsState.create();
        const listWindowOffsets = new Map();
        let cachedInventoryKey = "";
        let cachedInventoryEntries = [];

        function entryKey(entry) {
            return `${entry.kind}:${entry.id}`;
        }

        function getFilterValues() {
            return [
                ...allSettingsFilterButtons.map((button) => button.dataset.settingsListFilter || "all"),
                ...allSettingsSourceFilterButtons.map((button) => button.dataset.settingsSourceFilter || "all"),
            ];
        }

        function categoryTitle(categoryId) {
            const category = allSettingsCategoryCatalog.categories_by_id?.[categoryId]
                || allSettingsCategoryCatalog.categories_by_id?.["raw-unmapped"];
            return category
                ? (t(category.title_key) || category.fallback || category.id)
                : "";
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

        function sourceLabel(source) {
            const sourceKeys = {
                baseline: "profiles.settings_source_baseline",
                cis: "profiles.settings_source_cis",
                manual: "profiles.settings_source_manual",
                imported: "profiles.settings_source_imported",
                "raw-fallback": "profiles.settings_source_raw",
                unknown: "profiles.settings_review_source_unknown",
                catalog: "profiles.settings_review_source_catalog",
            };
            return t(sourceKeys[source] || "profiles.settings_source_manual");
        }

        function entryAttentionBadges(entry) {
            const badges = [];
            if (entry.attentionFlags?.cisReviewRequired) {
                badges.push(["cis-review", t("profiles.settings_review_reason_cis_empty")]);
            }
            if (entry.invalid) {
                badges.push(["invalid", formatText("profiles.settings_review_reason_invalid", {
                    count: Number(entry.validationIssueCount || entry.attentionFlags?.validationIssueCount || 1),
                })]);
            }
            if (entry.unknown) {
                badges.push(["unknown", t("profiles.settings_review_reason_unknown")]);
            }
            if (entry.deprecated) {
                badges.push(["deprecated", t("profiles.settings_review_reason_deprecated")]);
            }
            if (entry.rawFallback) {
                badges.push(["raw", t("profiles.settings_review_reason_raw")]);
            }
            return badges;
        }

        function renderEntryBadges(entry) {
            const sourceBadges = (Array.isArray(entry.sources) ? entry.sources : [])
                .filter((source, index, sources) => source && sources.indexOf(source) === index)
                .map((source) => {
                    const label = sourceLabel(source);
                    return `
                    <span
                        class="all-settings-list-badge"
                        data-settings-entry-source="${escapeHtml(source)}"
                        aria-label="${escapeHtml(formatText("profiles.settings_a11y_entry_source", { source: label }))}">
                        ${escapeHtml(label)}
                    </span>
                `;
                });
            const attentionBadges = entryAttentionBadges(entry)
                .map(([tone, label]) => `
                    <span
                        class="all-settings-list-badge has-attention"
                        data-settings-entry-attention="${escapeHtml(tone)}"
                        aria-label="${escapeHtml(label)}">
                        ${escapeHtml(label)}
                    </span>
                `);
            const state = stateLabel(entry.configured);
            const kind = kindLabel(entry.kind);
            const category = categoryTitle(entry.categoryId);
            return `
                <span class="all-settings-list-badges">
                    <span
                        class="all-settings-list-badge"
                        data-settings-entry-state-badge="${entry.configured ? "configured" : "available"}"
                        aria-label="${escapeHtml(formatText("profiles.settings_a11y_entry_state", { state }))}">
                        ${escapeHtml(state)}
                    </span>
                    <span
                        class="all-settings-list-badge"
                        data-settings-entry-kind-badge="${escapeHtml(entry.kind)}"
                        aria-label="${escapeHtml(formatText("profiles.settings_a11y_entry_kind", { kind }))}">
                        ${escapeHtml(kind)}
                    </span>
                    <span
                        class="all-settings-list-badge"
                        data-settings-entry-category-badge="${escapeHtml(entry.categoryId)}"
                        aria-label="${escapeHtml(formatText("profiles.settings_a11y_entry_category", { category }))}">
                        ${escapeHtml(category)}
                    </span>
                    ${sourceBadges.join("")}
                    ${attentionBadges.join("")}
                </span>
            `;
        }

        function formatText(key, replacements = {}) {
            return Object.entries(replacements).reduce(
                (text, [name, value]) => text.replace(`{${name}}`, String(value)),
                t(key),
            );
        }

        function normalizeCacheValue(value, seen = new WeakSet()) {
            if (value === null || typeof value !== "object") return value;
            if (seen.has(value)) return "[Circular]";
            seen.add(value);
            if (Array.isArray(value)) {
                return value.map((item) => normalizeCacheValue(item, seen));
            }
            return Object.keys(value)
                .sort()
                .reduce((normalized, key) => {
                    normalized[key] = normalizeCacheValue(value[key], seen);
                    return normalized;
                }, {});
        }

        function stableStringify(value) {
            const serialized = JSON.stringify(normalizeCacheValue(value));
            return serialized === undefined ? "" : serialized;
        }

        function getInventoryLocaleKey() {
            return String(
                getCurrentLang?.()
                || documentRef?.documentElement?.lang
                || window.__BPM_INITIAL_LANG__
                || "",
            );
        }

        function buildInventoryCacheKey(sourceData) {
            return stableStringify({
                sourceData,
                schemaVersion: getActiveWizardSchemaVersion?.() || "",
                validationIssues: Array.isArray(getValidationIssues?.()) ? getValidationIssues() : [],
                locale: getInventoryLocaleKey(),
                complianceInfo: getComplianceInfo?.() || null,
                manualEdits: Array.isArray(getManualEdits?.()) ? getManualEdits() : [],
            });
        }

        function translateCatalogText(key, fallback = "") {
            if (!key) return fallback;
            const translated = t(key);
            return translated && translated !== key ? translated : fallback;
        }

        function categoryBody(category) {
            return translateCatalogText(category?.body_key, category?.body_fallback || "");
        }

        function configuredDomainCategories(entries) {
            const catalogCategories = Array.isArray(allSettingsCategoryCatalog.categories)
                ? allSettingsCategoryCatalog.categories
                : [];
            if (catalogCategories.length) return catalogCategories;
            return Array.from(new Set(entries.map((entry) => entry.categoryId).filter(Boolean)))
                .map((id) => ({
                    id,
                    title_key: "",
                    fallback: categoryTitle(id) || id,
                    body_key: "",
                    body_fallback: "",
                }));
        }

        function buildCategorySummaries(entries) {
            const configuredEntries = entries.filter((entry) => entry.configured);
            const availableEntries = entries.filter((entry) => !entry.configured);
            return configuredDomainCategories(entries).map((category) => {
                const categoryEntries = configuredEntries.filter((entry) => entry.categoryId === category.id);
                const availableCount = availableEntries.filter((entry) => entry.categoryId === category.id).length;
                const attentionCount = categoryEntries.filter((entry) => entryNeedsReview(entry)).length;
                const totalCount = categoryEntries.length + availableCount;
                const policyEntries = entries.filter((entry) => entry.kind === "policy" && entry.categoryId === category.id);
                const rawFallbackCount = policyEntries.filter((entry) => entry.rawFallback).length;
                const deprecatedCount = policyEntries.filter((entry) => entry.deprecated).length;
                const mappedCount = policyEntries.filter((entry) => !entry.rawFallback).length;
                return {
                    id: category.id,
                    title: translateCatalogText(category.title_key, category.fallback || category.id),
                    body: categoryBody(category),
                    configuredCount: categoryEntries.length,
                    availableCount,
                    attentionCount,
                    totalCount,
                    policyCount: policyEntries.length,
                    mappedCount,
                    rawFallbackCount,
                    deprecatedCount,
                };
            });
        }

        function buildConfiguredDomainSummaries(entries) {
            return buildCategorySummaries(entries);
        }

        function renderDomainSummaryCards(container, summaries, snapshot, options = {}) {
            if (!container) return;
            const {
                actionAttribute = "data-settings-domain-card",
                disableEmpty = false,
                activeCategory = snapshot.activeCategory,
            } = options;
            container.innerHTML = summaries
                .map((item) => {
                    const active = item.id === activeCategory;
                    const disabled = disableEmpty && item.configuredCount <= 0;
                    const cardLabel = formatText("profiles.settings_a11y_domain_card", {
                        title: item.title,
                        configured: item.configuredCount,
                        attention: item.attentionCount,
                        available: item.availableCount,
                        mapped: item.mappedCount,
                        raw: item.rawFallbackCount,
                        deprecated: item.deprecatedCount,
                    });
                    return `
                        <button
                            type="button"
                            class="all-settings-domain-card${active ? " is-active" : ""}"
                            ${actionAttribute}="${escapeHtml(item.id)}"
                            data-settings-domain-configured-count="${item.configuredCount}"
                            data-settings-domain-hidden-available-count="${item.availableCount}"
                            data-settings-domain-attention-count="${item.attentionCount}"
                            data-settings-domain-total-count="${item.totalCount}"
                            aria-label="${escapeHtml(cardLabel)}"
                            ${disabled ? "disabled" : ""}>
                            <span class="all-settings-domain-card-title">${escapeHtml(item.title)}</span>
                            ${item.body ? `<span class="all-settings-domain-card-body">${escapeHtml(item.body)}</span>` : ""}
                            <span class="all-settings-domain-card-counts">
                                <span class="all-settings-domain-card-count">
                                    <strong>${item.configuredCount}</strong>
                                    ${escapeHtml(t("profiles.settings_configured_domain_configured"))}
                                </span>
                                <span class="all-settings-domain-card-count${item.attentionCount > 0 ? " has-attention" : ""}">
                                    <strong>${item.attentionCount}</strong>
                                    ${escapeHtml(t("profiles.settings_configured_domain_attention"))}
                                </span>
                                <span class="all-settings-domain-card-count">
                                    <strong>${item.availableCount}</strong>
                                    ${escapeHtml(t("profiles.settings_configured_domain_available"))}
                                </span>
                            </span>
                            <span class="all-settings-domain-card-coverage">
                                <span
                                    class="all-settings-domain-card-count"
                                    data-settings-domain-mapped-count="${item.mappedCount}">
                                    <strong>${item.mappedCount}</strong>
                                    ${escapeHtml(t("profiles.wizard_shell_badge_mapped"))}
                                </span>
                                <span
                                    class="all-settings-domain-card-count${item.rawFallbackCount > 0 ? " has-attention" : ""}"
                                    data-settings-domain-raw-count="${item.rawFallbackCount}">
                                    <strong>${item.rawFallbackCount}</strong>
                                    ${escapeHtml(t("profiles.wizard_shell_badge_raw"))}
                                </span>
                                <span
                                    class="all-settings-domain-card-count${item.deprecatedCount > 0 ? " has-attention" : ""}"
                                    data-settings-domain-deprecated-count="${item.deprecatedCount}">
                                    <strong>${item.deprecatedCount}</strong>
                                    ${escapeHtml(t("profiles.wizard_shell_badge_deprecated"))}
                                </span>
                            </span>
                        </button>
                    `;
                })
                .join("");
        }

        function renderConfiguredSummary() {
            if (!allSettingsConfiguredSummaryEl) return;

            const snapshot = routeState.getSnapshot();
            if (snapshot.activeMode !== "configured") {
                allSettingsConfiguredSummaryEl.hidden = true;
                allSettingsConfiguredSummaryEl.innerHTML = "";
                return;
            }

            allSettingsConfiguredSummaryEl.hidden = false;
            renderDomainSummaryCards(
                allSettingsConfiguredSummaryEl,
                buildCategorySummaries(routeState.getEntries()),
                snapshot,
                { actionAttribute: "data-settings-domain-card", disableEmpty: true },
            );
        }

        function renderSummary(entries, visibleEntries = entries) {
            if (!allSettingsListSummaryEl) return;

            const snapshot = routeState.getSnapshot();
            const counts = snapshot.counts || {};
            const total = Number(counts.total ?? entries.length);
            const visible = Number(counts.visible ?? visibleEntries.length);
            const summaryKey = snapshot.activeFilter === "all" && visible === total
                ? "profiles.settings_list_summary"
                : "profiles.settings_list_summary_filtered";
            allSettingsListSummaryEl.textContent = t(summaryKey)
                .replace("{total}", String(total))
                .replace("{visible}", String(visible))
                .replace("{configured}", String(counts.configured ?? 0))
                .replace("{policies}", String(counts.policies ?? 0))
                .replace("{preferences}", String(counts.preferences ?? 0));
        }

        function listBudgetGroupId(snapshot = routeState.getSnapshot()) {
            return [
                "entries",
                snapshot.activeMode || "review",
                snapshot.activeCategory || "all",
                snapshot.activeFilter || "all",
                snapshot.searchQuery || "",
            ].join(":");
        }

        function clampWindowOffset(offset, total) {
            const normalizedOffset = Number.isFinite(Number(offset)) ? Number(offset) : 0;
            if (total <= VISIBLE_ENTRY_WINDOW_SIZE) return 0;
            const maxOffset = Math.floor((total - 1) / VISIBLE_ENTRY_WINDOW_SIZE) * VISIBLE_ENTRY_WINDOW_SIZE;
            return Math.min(Math.max(0, normalizedOffset), maxOffset);
        }

        function getListWindow(visibleEntries, snapshot = routeState.getSnapshot()) {
            const total = visibleEntries.length;
            const groupId = listBudgetGroupId(snapshot);
            const expanded = snapshot.expandedGroups?.includes(groupId);
            if (total <= VISIBLE_ENTRY_BUDGET) {
                listWindowOffsets.set(groupId, 0);
                return {
                    entries: visibleEntries,
                    expanded: false,
                    from: total > 0 ? 1 : 0,
                    to: total,
                    total,
                    groupId,
                    canPageBack: false,
                    canPageForward: false,
                };
            }

            if (expanded) {
                let offset = clampWindowOffset(listWindowOffsets.get(groupId), total);
                listWindowOffsets.set(groupId, offset);
                const entries = visibleEntries.slice(offset, offset + VISIBLE_ENTRY_WINDOW_SIZE);
                return {
                    entries,
                    expanded: true,
                    from: offset + 1,
                    to: offset + entries.length,
                    total,
                    groupId,
                    canPageBack: offset > 0,
                    canPageForward: offset + VISIBLE_ENTRY_WINDOW_SIZE < total,
                };
            }

            listWindowOffsets.set(groupId, 0);
            const entries = visibleEntries.slice(0, VISIBLE_ENTRY_BUDGET);
            const selectedEntry = visibleEntries.find((entry) => entryKey(entry) === snapshot.selectedEntryKey);
            if (selectedEntry && !entries.some((entry) => entryKey(entry) === entryKey(selectedEntry))) {
                entries.push(selectedEntry);
            }
            return {
                entries,
                expanded: false,
                from: 1,
                to: entries.length,
                total,
                groupId,
                canPageBack: false,
                canPageForward: false,
            };
        }

        function renderListBudget(listWindow) {
            if (!allSettingsListBudgetEl) return;

            const total = listWindow.total;
            if (total <= VISIBLE_ENTRY_BUDGET) {
                allSettingsListBudgetEl.hidden = true;
                allSettingsListBudgetEl.innerHTML = "";
                return;
            }

            const shown = listWindow.to - listWindow.from + 1;
            allSettingsListBudgetEl.hidden = false;
            allSettingsListBudgetEl.innerHTML = `
                <span class="all-settings-list-budget-count" aria-live="polite">
                    ${escapeHtml(listWindow.expanded
                        ? formatText("profiles.settings_list_window", {
                            from: listWindow.from,
                            to: listWindow.to,
                            total,
                        })
                        : formatText("profiles.settings_list_budget", {
                            visible: shown,
                            total,
                        }))}
                </span>
                <span class="all-settings-list-budget-actions">
                    ${listWindow.expanded && listWindow.canPageBack
                        ? `
                            <button
                                type="button"
                                class="button-base ghost-button all-settings-list-budget-toggle"
                                data-settings-list-budget-action="prev"
                                data-settings-list-budget-toggle="${escapeHtml(listWindow.groupId)}"
                                aria-label="${escapeHtml(t("profiles.settings_a11y_list_previous_page"))}">
                                ${escapeHtml(t("profiles.settings_list_previous_page"))}
                            </button>
                        `
                        : ""}
                    ${listWindow.expanded && listWindow.canPageForward
                        ? `
                            <button
                                type="button"
                                class="button-base ghost-button all-settings-list-budget-toggle"
                                data-settings-list-budget-action="next"
                                data-settings-list-budget-toggle="${escapeHtml(listWindow.groupId)}"
                                aria-label="${escapeHtml(t("profiles.settings_a11y_list_next_page"))}">
                                ${escapeHtml(t("profiles.settings_list_next_page"))}
                            </button>
                        `
                        : ""}
                    <button
                        type="button"
                        class="button-base ghost-button all-settings-list-budget-toggle"
                        data-settings-list-budget-action="${listWindow.expanded ? "collapse" : "expand"}"
                        data-settings-list-budget-toggle="${escapeHtml(listWindow.groupId)}"
                        data-settings-list-budget-expanded="${listWindow.expanded ? "true" : "false"}"
                        aria-label="${escapeHtml(listWindow.expanded
                            ? t("profiles.settings_a11y_list_show_less")
                            : formatText("profiles.settings_a11y_list_show_more", { count: total - shown }))}">
                        ${escapeHtml(listWindow.expanded
                            ? t("profiles.settings_list_show_less")
                            : formatText("profiles.settings_list_show_more", { count: total - shown }))}
                    </button>
                </span>
            `;
        }

        function renderRows(entries) {
            if (!allSettingsListEl) return;

            allSettingsListEl.innerHTML = entries
                .map((entry) => {
                    const currentEntryKey = entryKey(entry);
                    const selected = currentEntryKey === routeState.getSnapshot().selectedEntryKey;
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
                            ${renderEntryBadges(entry)}
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
            if (String(filterValue || "").startsWith("source:")) {
                const requestedSource = String(filterValue).slice("source:".length);
                const source = requestedSource === "raw" ? "raw-fallback" : requestedSource;
                return Array.isArray(entry.sources) && entry.sources.includes(source);
            }
            if (filterValue === "configured") return entry.configured;
            if (filterValue === "available") return !entry.configured;
            if (filterValue === "guided-covered") return entry.guided;
            if (filterValue === "all-settings-only") return !entry.guided;
            if (filterValue === "invalid") return entry.invalid;
            if (filterValue === "deprecated") return entry.deprecated;
            if (filterValue === "raw") return entry.rawFallback;
            if (filterValue === "unknown") return entry.unknown;
            if (filterValue === "cis-review") return Boolean(entry.attentionFlags?.cisReviewRequired);
            return true;
        }

        function filterHiddenInMode(filterValue, mode) {
            return mode !== "catalog" && ["configured", "available"].includes(filterValue);
        }

        function entryNeedsReview(entry) {
            if (!entry?.configured) return false;
            return Boolean(
                entry?.attentionFlags?.reviewRequired
                || entry?.invalid
                || entry?.deprecated
                || entry?.rawFallback
                || entry?.unknown
            );
        }

        function entryMatchesMode(entry, mode) {
            if (mode === "review") return entryNeedsReview(entry);
            if (mode === "configured") return entry.configured;
            return true;
        }

        function entryMatchesCategory(entry, categoryId, mode) {
            if (mode !== "configured") return true;
            const normalizedCategoryId = String(categoryId || "all");
            if (normalizedCategoryId === "all") return true;
            return entry.categoryId === normalizedCategoryId;
        }

        function setActiveMode(mode, options = {}) {
            routeState.setActiveMode(mode);
            onModeChange?.(routeState.getSnapshot().activeMode, options);
        }

        function entryMatchesReview(entry, reviewKind) {
            if (!entry?.configured) return false;
            if (reviewKind === "cis-review") return Boolean(entry.attentionFlags?.cisReviewRequired);
            if (reviewKind === "unknown") return entry.unknown;
            if (reviewKind === "deprecated") return entry.deprecated;
            if (reviewKind === "raw") return entry.rawFallback;
            if (reviewKind === "invalid") return entry.invalid;
            return false;
        }

        function buildReviewItems(entries) {
            return [
                {
                    kind: "cis-review",
                    title: t("profiles.settings_review_cis_title"),
                    body: t("profiles.settings_review_cis_body"),
                    tone: "error",
                    entries: entries.filter((entry) => entryMatchesReview(entry, "cis-review")),
                },
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

        function formatReviewText(key, replacements = {}) {
            return formatText(key, replacements);
        }

        function reviewSourceLabel(entry) {
            const sources = Array.isArray(entry?.sources) ? entry.sources : [];
            const sourcePriority = [
                "cis",
                "baseline",
                "manual",
                "imported",
                "unknown",
                "raw-fallback",
                "catalog",
            ];
            const source = sourcePriority.find((candidate) => sources.includes(candidate))
                || entry?.source
                || sources[0]
                || "manual";
            const sourceKeys = {
                cis: "profiles.settings_review_source_cis",
                baseline: "profiles.settings_review_source_baseline",
                manual: "profiles.settings_review_source_manual",
                imported: "profiles.settings_review_source_imported",
                unknown: "profiles.settings_review_source_unknown",
                "raw-fallback": "profiles.settings_review_source_raw",
                catalog: "profiles.settings_review_source_catalog",
            };
            return t(sourceKeys[source] || "profiles.settings_review_source_manual");
        }

        function getCisReviewDecision(entry) {
            const decisions = Array.isArray(entry?.sourceDetails?.decisions)
                ? entry.sourceDetails.decisions
                : [];
            return decisions.find((decision) => decision?.review_required)
                || entry?.sourceDetails?.primaryDecision
                || entry?.cis?.primaryDecision
                || null;
        }

        function formatDecisionPath(path) {
            return Array.isArray(path)
                ? path.filter(Boolean).map((part) => String(part)).join(".")
                : "";
        }

        function reviewPathLabel(entry, reviewKind) {
            if (reviewKind !== "cis-review") return "";
            const decision = getCisReviewDecision(entry);
            const path = formatDecisionPath(decision?.path)
                || formatDecisionPath(entry?.sourceDetails?.path);
            return path
                ? formatReviewText("profiles.settings_review_path", { path })
                : "";
        }

        function reviewReasonLabel(entry, reviewKind) {
            if (reviewKind === "cis-review") {
                const decision = getCisReviewDecision(entry);
                const recommendationIds = Array.isArray(decision?.recommendation_ids)
                    ? decision.recommendation_ids
                    : (Array.isArray(entry?.sourceDetails?.recommendationIds)
                    ? entry.sourceDetails.recommendationIds
                    : (Array.isArray(entry?.cis?.recommendationIds) ? entry.cis.recommendationIds : []));
                const reason = String(decision?.reason || "").trim();
                if (reason && recommendationIds.length) {
                    return formatReviewText("profiles.settings_review_reason_cis_manual", {
                        ids: recommendationIds.slice(0, 3).join(", "),
                        reason,
                    });
                }
                if (reason) {
                    return formatReviewText("profiles.settings_review_reason_cis_manual_no_ids", {
                        reason,
                    });
                }
                if (recommendationIds.length) {
                    return formatReviewText("profiles.settings_review_reason_cis", {
                        ids: recommendationIds.slice(0, 3).join(", "),
                    });
                }
                return t("profiles.settings_review_reason_cis_empty");
            }
            if (reviewKind === "invalid") {
                return formatReviewText("profiles.settings_review_reason_invalid", {
                    count: Number(entry?.validationIssueCount || entry?.attentionFlags?.validationIssueCount || 1),
                });
            }
            if (reviewKind === "unknown") return t("profiles.settings_review_reason_unknown");
            if (reviewKind === "deprecated") return t("profiles.settings_review_reason_deprecated");
            if (reviewKind === "raw") return t("profiles.settings_review_reason_raw");
            return t("profiles.settings_review_reason_attention");
        }

        function renderReviewQueue(item) {
            const count = item.entries.length;
            if (count <= 0) {
                return `
                    <span class="all-settings-review-card-empty">
                        ${escapeHtml(t("profiles.settings_review_empty_group"))}
                    </span>
                `;
            }

            const previewEntries = item.entries.slice(0, 3).map((entry) => {
                const pathLabel = reviewPathLabel(entry, item.kind);
                return `
                    <span
                        class="all-settings-review-card-entry"
                        data-settings-review-entry="${escapeHtml(`${item.kind}:${entry.id}`)}">
                        <span class="all-settings-review-card-entry-key">${escapeHtml(entry.label || entry.id)}</span>
                        <span class="all-settings-review-card-entry-meta">
                            <span class="all-settings-review-card-pill">${escapeHtml(reviewSourceLabel(entry))}</span>
                            ${pathLabel ? `<span class="all-settings-review-card-path">${escapeHtml(pathLabel)}</span>` : ""}
                        </span>
                        <span class="all-settings-review-card-reason">${escapeHtml(reviewReasonLabel(entry, item.kind))}</span>
                    </span>
                `;
            });
            const hiddenCount = count - previewEntries.length;
            return `
                <span
                    class="all-settings-review-card-queue"
                    data-settings-review-queue="${escapeHtml(item.kind)}"
                    aria-label="${escapeHtml(formatText("profiles.settings_a11y_review_queue", {
                        title: item.title,
                        count,
                    }))}">
                    ${previewEntries.join("")}
                    ${hiddenCount > 0
                        ? `<span
                            class="all-settings-review-card-more"
                            aria-label="${escapeHtml(formatReviewText("profiles.settings_a11y_review_more", { count: hiddenCount }))}">
                                ${escapeHtml(formatReviewText("profiles.settings_review_more", { count: hiddenCount }))}
                            </span>`
                        : ""}
                </span>
            `;
        }

        function renderReviewSuccessState() {
            return `
                <div class="all-settings-review-success" data-settings-review-empty-state>
                    <span class="all-settings-review-success-title">
                        ${escapeHtml(t("profiles.settings_review_success_title"))}
                    </span>
                    <span class="all-settings-review-success-body">
                        ${escapeHtml(t("profiles.settings_review_success_body"))}
                    </span>
                    <span class="all-settings-review-success-actions">
                        <button
                            type="button"
                            class="button-base primary-button all-settings-review-success-action"
                            data-settings-review-mode="configured">
                            ${escapeHtml(t("profiles.settings_review_success_configured"))}
                        </button>
                        <button
                            type="button"
                            class="button-base ghost-button all-settings-review-success-action"
                            data-settings-review-mode="catalog">
                            ${escapeHtml(t("profiles.settings_review_success_catalog"))}
                        </button>
                    </span>
                </div>
            `;
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

            if (total <= 0) {
                allSettingsReviewActionsEl.innerHTML = renderReviewSuccessState();
                return;
            }

            allSettingsReviewActionsEl.innerHTML = reviewItems
                .map((item) => {
                    const count = item.entries.length;
                    const disabled = count <= 0;
                    const cardLabel = formatReviewText("profiles.settings_a11y_review_card", {
                        title: item.title,
                        count,
                    });
                    return `
                        <button
                            type="button"
                            class="all-settings-review-card"
                            data-settings-review-filter="${escapeHtml(item.kind)}"
                            data-settings-review-count="${count}"
                            data-tone="${escapeHtml(item.tone)}"
                            aria-label="${escapeHtml(cardLabel)}"
                            ${disabled ? "disabled" : ""}>
                            <span class="all-settings-review-card-top">
                                <span class="all-settings-review-card-title">${escapeHtml(item.title)}</span>
                                <span class="all-settings-review-card-count">${count}</span>
                            </span>
                            <span class="all-settings-review-card-body">${escapeHtml(item.body)}</span>
                            ${renderReviewQueue(item)}
                            <span class="all-settings-review-card-action">
                                ${escapeHtml(t(disabled ? "profiles.settings_review_clear" : "profiles.settings_review_open"))}
                            </span>
                        </button>
                    `;
                })
                .join("");
        }

        function updateFilterButtons(entries) {
            const snapshot = routeState.getSnapshot();
            const activeFilter = snapshot.activeFilter;
            const filterCounts = snapshot.counts?.filters || {};
            allSettingsFilterButtons.forEach((button) => {
                const filterValue = button.dataset.settingsListFilter || "all";
                button.hidden = filterHiddenInMode(filterValue, snapshot.activeMode);
                const count = filterCounts[filterValue] ?? entries.filter((entry) => entryMatchesFilter(entry, filterValue)).length;
                button.classList.toggle("is-active", filterValue === activeFilter);
                button.setAttribute("aria-pressed", filterValue === activeFilter ? "true" : "false");
                const label = button.querySelector("span:not([data-settings-list-filter-count])")?.textContent?.trim() || filterValue;
                button.setAttribute(
                    "aria-label",
                    formatText("profiles.settings_a11y_filter_count", { filter: label, count }),
                );
                const countEl = button.querySelector("[data-settings-list-filter-count]");
                if (countEl) {
                    countEl.textContent = String(count);
                    countEl.setAttribute("aria-label", formatText("profiles.settings_a11y_count", { count }));
                }
            });
        }

        function updateSourceFilterButtons() {
            if (!allSettingsSourceFiltersEl) return;

            const snapshot = routeState.getSnapshot();
            const showSourceFilters = snapshot.activeMode === "configured";
            allSettingsSourceFiltersEl.hidden = !showSourceFilters;
            if (!showSourceFilters) return;

            const sourceCounts = snapshot.counts?.filters || {};
            allSettingsSourceFilterButtons.forEach((button) => {
                const filterValue = button.dataset.settingsSourceFilter || "source:manual";
                const active = snapshot.activeFilter === filterValue;
                const count = sourceCounts[filterValue] ?? 0;
                button.classList.toggle("is-active", active);
                button.setAttribute("aria-pressed", active ? "true" : "false");
                const requestedSource = filterValue.replace(/^source:/, "");
                const source = requestedSource === "raw" ? "raw-fallback" : requestedSource;
                const label = button.querySelector("span:not([data-settings-source-filter-count])")?.textContent?.trim()
                    || sourceLabel(source);
                button.setAttribute(
                    "aria-label",
                    formatText("profiles.settings_a11y_source_filter", { source: label, count }),
                );
                const countEl = button.querySelector("[data-settings-source-filter-count]");
                if (countEl) {
                    countEl.textContent = String(count);
                    countEl.setAttribute("aria-label", formatText("profiles.settings_a11y_count", { count }));
                }
            });
        }

        function applyFilter(entries) {
            const snapshot = routeState.getSnapshot();
            const activeFilter = snapshot.activeFilter;
            const visibleEntries = routeState.getVisibleEntries();
            const listWindow = getListWindow(visibleEntries, snapshot);
            const visibleKeys = new Set(listWindow.entries.map((entry) => entryKey(entry)));
            const entriesByKey = new Map(entries.map((entry) => [`${entry.kind}:${entry.id}`, entry]));
            renderRows(listWindow.entries);
            if (allSettingsListEl) {
                allSettingsListEl.querySelectorAll("[data-settings-entry-id]").forEach((row) => {
                    const entry = entriesByKey.get(
                        `${row.dataset.settingsEntryKind || ""}:${row.dataset.settingsEntryId || ""}`,
                    );
                    row.hidden = !entry || !visibleKeys.has(entryKey(entry));
                });
            }
            if (allSettingsListEmptyEl) {
                allSettingsListEmptyEl.hidden = visibleEntries.length > 0;
                allSettingsListEmptyEl.textContent = activeFilter === "all"
                    ? t("profiles.settings_list_empty")
                    : t("profiles.settings_list_filtered_empty");
            }
            renderListBudget(listWindow);
            renderSummary(entries, visibleEntries);
            updateFilterButtons(entries);
            updateSourceFilterButtons();
        }

        function render() {
            if (!allSettingsListEl) return;
            const entries = collectEntries();
            const snapshot = routeState.getSnapshot();
            if (filterHiddenInMode(snapshot.activeFilter, snapshot.activeMode)) {
                routeState.setActiveFilter("all");
            }
            routeState.updateEntries(entries, {
                entryKey,
                filterValues: getFilterValues(),
                matchesMode: entryMatchesMode,
                matchesCategory: entryMatchesCategory,
                matchesFilter: entryMatchesFilter,
            });

            renderConfiguredSummary();
            renderReview(entries);
            applyFilter(entries);
            onSelectionChange?.(
                routeState.getSelectedEntry(entries, entryKey),
            );
        }

        function collectEntries() {
            const sourceState = readWizardSchemaSource();
            const sourceData = sourceState.ok && sourceState.data && typeof sourceState.data === "object"
                ? sourceState.data
                : {};
            const cacheKey = buildInventoryCacheKey(sourceData);
            if (cacheKey === cachedInventoryKey) {
                return cachedInventoryEntries.slice();
            }
            const nextEntries = settingsInventory?.collect?.(sourceData) || [];
            cachedInventoryKey = cacheKey;
            cachedInventoryEntries = nextEntries;
            return cachedInventoryEntries.slice();
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

        function revealTargetForSelectedRow(row) {
            window.requestAnimationFrame?.(() => {
                row?.scrollIntoView?.({ block: "nearest", inline: "nearest" });
            });
            return documentRef.getElementById("all-settings-detail-panel") || row;
        }

        function selectEntry(kind, id) {
            const entries = collectEntries();
            const match = entries.find((entry) => entry.kind === kind && entry.id === id);
            if (!match) return null;
            setActiveMode("catalog", { updateUrl: false });
            routeState.setActiveFilter("all");
            routeState.setSelectedEntryKey(entryKey(match), {
                categoryId: match.categoryId,
                target: `all-settings-entry:${match.kind}:${match.id}`,
            });
            const targetGroupId = listBudgetGroupId(routeState.getSnapshot());
            if (routeState.getSnapshot().expandedGroups?.includes(targetGroupId)) {
                const matchIndex = entries.findIndex((entry) => entryKey(entry) === entryKey(match));
                listWindowOffsets.set(
                    targetGroupId,
                    clampWindowOffset(Math.floor(matchIndex / VISIBLE_ENTRY_WINDOW_SIZE) * VISIBLE_ENTRY_WINDOW_SIZE, entries.length),
                );
            }
            render();
            return revealTargetForSelectedRow(findRenderedRow(kind, id));
        }

        function findTarget(target) {
            const normalizedTarget = String(target || "").trim();
            routeState.setFocusedTarget(normalizedTarget);
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
            routeState.setSelectedEntryKey(`${row.dataset.settingsEntryKind || ""}:${row.dataset.settingsEntryId || ""}`, {
                categoryId: row.dataset.settingsEntryCategory || "",
                target: `all-settings-entry:${row.dataset.settingsEntryKind || ""}:${row.dataset.settingsEntryId || ""}`,
            });
            allSettingsListEl.querySelectorAll("[data-settings-entry-id]").forEach((entryRow) => {
                const isSelected = entryRow === row;
                entryRow.classList.toggle("is-selected", isSelected);
                entryRow.setAttribute("aria-current", isSelected ? "true" : "false");
            });
            render();
        });

        allSettingsFilterButtons.forEach((button) => {
            button.addEventListener("click", () => {
                routeState.setActiveFilter(button.dataset.settingsListFilter || "all");
                render();
            });
        });

        allSettingsSourceFilterButtons.forEach((button) => {
            button.addEventListener("click", () => {
                routeState.setActiveFilter(button.dataset.settingsSourceFilter || "source:manual");
                render();
            });
        });

        allSettingsListBudgetEl?.addEventListener("click", (event) => {
            const action = event.target?.closest?.("[data-settings-list-budget-toggle]");
            if (!action || action.disabled) return;
            const groupId = action.dataset.settingsListBudgetToggle || listBudgetGroupId();
            const actionType = action.dataset.settingsListBudgetAction || "toggle";
            const currentOffset = clampWindowOffset(listWindowOffsets.get(groupId), routeState.getVisibleEntries().length);
            if (actionType === "prev") {
                listWindowOffsets.set(groupId, Math.max(0, currentOffset - VISIBLE_ENTRY_WINDOW_SIZE));
                routeState.setExpanded(groupId, true);
            } else if (actionType === "next") {
                listWindowOffsets.set(groupId, currentOffset + VISIBLE_ENTRY_WINDOW_SIZE);
                routeState.setExpanded(groupId, true);
            } else if (actionType === "expand") {
                routeState.setExpanded(groupId, true);
            } else if (actionType === "collapse") {
                listWindowOffsets.set(groupId, 0);
                routeState.setExpanded(groupId, false);
            } else {
                routeState.toggleExpanded(groupId);
            }
            render();
        });

        allSettingsConfiguredSummaryEl?.addEventListener("click", (event) => {
            const target = event.target instanceof Element ? event.target : event.target?.parentElement;
            const action = target?.closest("[data-settings-domain-card]");
            if (!action || action.disabled) return;
            const categoryId = action.dataset.settingsDomainCard || "";
            routeState.setActiveCategory(categoryId);
            routeState.setActiveFilter("all");
            const firstEntry = routeState.getModeEntries()
                .find((entry) => entry.configured && entry.categoryId === categoryId);
            if (firstEntry) {
                routeState.setSelectedEntryKey(entryKey(firstEntry), {
                    categoryId: firstEntry.categoryId,
                    target: `all-settings-entry:${firstEntry.kind}:${firstEntry.id}`,
                });
            }
            render();
            window.requestAnimationFrame?.(() => {
                allSettingsListEl
                    ?.querySelector(".all-settings-list-row.is-selected")
                    ?.scrollIntoView({ block: "nearest", inline: "nearest" });
            });
        });

        allSettingsReviewActionsEl?.addEventListener("click", (event) => {
            const target = event.target instanceof Element ? event.target : event.target?.parentElement;
            const modeAction = target?.closest("[data-settings-review-mode]");
            if (modeAction && !modeAction.disabled) {
                const mode = modeAction.dataset.settingsReviewMode || "configured";
                setActiveMode(mode, { updateUrl: true });
                routeState.setActiveFilter("all");
                render();
                window.requestAnimationFrame?.(() => {
                    allSettingsListEl
                        ?.querySelector(".all-settings-list-row.is-selected")
                        ?.scrollIntoView({ block: "nearest", inline: "nearest" });
                });
                return;
            }

            const action = target?.closest("[data-settings-review-filter]");
            if (!action || action.disabled) return;
            const reviewKind = action.dataset.settingsReviewFilter || "all";
            const reviewItem = buildReviewItems(routeState.getEntries()).find((item) => item.kind === reviewKind);
            const firstEntry = reviewItem?.entries?.[0] || null;
            setActiveMode("review", { updateUrl: false });
            routeState.setActiveFilter(reviewKind);
            if (firstEntry) {
                routeState.setSelectedEntryKey(entryKey(firstEntry), {
                    categoryId: firstEntry.categoryId,
                    target: `all-settings-entry:${firstEntry.kind}:${firstEntry.id}`,
                });
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
