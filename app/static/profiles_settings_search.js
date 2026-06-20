(() => {
    function create({
        documentRef = document,
        elements = {},
        dependencies = {},
        state = {},
        wizardSettingsCatalog = {},
        wizardSearchSectionSteps = {},
        searchEnginePresetCatalog = [],
        searchEnginePresets = {},
        wizardSchemaShellCatalog = {},
        settingsTargetAliases = {},
    }) {
        const {
            t,
            escapeHtml,
            humanizeIdentifier,
            normalizeSearchText,
            setWizardStep,
            getAllSettingsSearchEntries,
            findAllSettingsEntryTarget,
        } = dependencies;
        const getCurrentLang = state.getCurrentLang || (() => "en");
        const allSettingsRouteState = state.allSettingsRouteState || null;
        const isAllSettingsRoute = documentRef.body?.dataset.profilesTemplateKind === "settings";

        const {
            wizardSettingsSearchInputEl,
            wizardSettingsSearchMetaEl,
            wizardSettingsSearchResultsEl,
            wizardSettingsSearchClearEl,
            wizardSettingsSearchScopeEl,
            wizardSettingsSearchScopeButtons = [],
        } = elements;

        let wizardSettingsSearchIndex = [];
        let shellPolicyTargetByAlias = {};
        let activeSearchScope = "all";

        function getAllSettingsInventoryEntries() {
            return Array.isArray(getAllSettingsSearchEntries?.()) ? getAllSettingsSearchEntries() : [];
        }

        function buildShellPolicyTargetIndex(allSettingsEntries = []) {
            const targetIndex = {};

            allSettingsEntries.forEach((entry) => {
                if (entry?.kind !== "policy" || !entry.id || !entry.target) return;
                targetIndex[`policy:${entry.id}`] = entry.target;
            });

            shellPolicyTargetByAlias = targetIndex;
        }

        function resolveTargetAlias(target) {
            const normalizedTarget = String(target || "").trim();
            if (!normalizedTarget) return "";
            return settingsTargetAliases[normalizedTarget]
                || shellPolicyTargetByAlias[normalizedTarget]
                || normalizedTarget;
        }

        function createSettingsSearchEntry({
            title = "",
            description = "",
            target = "",
            sectionId = "",
            areaLabel = "",
            kind = "control",
            searchGroup = "actions",
            searchScopes = [],
            keywords = [],
        }) {
            const stepMeta = wizardSearchSectionSteps[sectionId] || { step: 0, key: "", fallback: "" };
            const stepLabel = t(stepMeta.key, stepMeta.fallback);
            const kindLabelMap = {
                control: t("profiles.wizard_settings_search_kind_control"),
                preference_section: t("profiles.wizard_settings_search_kind_preferences_section"),
                preference_preset: t("profiles.wizard_settings_search_kind_preference_preset"),
                preference_bundle: t("profiles.wizard_settings_search_kind_preference_bundle"),
                known_preference: t("profiles.wizard_settings_search_kind_known_preference"),
                search_engine_preset: t("profiles.wizard_settings_search_kind_search_preset"),
                policy_blueprint: t("profiles.wizard_settings_search_kind_policy_blueprint"),
                all_settings_policy: t("profiles.wizard_settings_search_kind_all_settings_policy"),
                all_settings_preference: t("profiles.wizard_settings_search_kind_all_settings_preference"),
            };

            const searchFields = [
                title,
                description,
                areaLabel,
                stepLabel,
                kindLabelMap[kind] || kind,
                target,
                humanizeIdentifier(target),
                ...keywords,
            ];

            return {
                title,
                description,
                target,
                sectionId,
                areaLabel,
                kind,
                searchGroup,
                searchScopes: Array.from(new Set(["all", ...searchScopes])),
                stepNumber: stepMeta.step || 0,
                stepLabel,
                kindLabel: kindLabelMap[kind] || kind,
                searchText: normalizeSearchText(searchFields.filter(Boolean).join(" ")),
            };
        }

        function currentStateLabel(entry) {
            return entry?.configured
                ? t("profiles.settings_list_state_configured")
                : t("profiles.settings_list_state_available");
        }

        function entryNeedsReview(entry) {
            return Boolean(
                entry?.configured
                && (
                    entry?.attentionFlags?.reviewRequired
                    || entry?.invalid
                    || entry?.deprecated
                    || entry?.rawFallback
                    || entry?.unknown
                )
            );
        }

        function buildAllSettingsInventoryEntries(allSettingsEntries = getAllSettingsInventoryEntries()) {
            return allSettingsEntries
                .map((entry) => {
                    const stateLabel = currentStateLabel(entry);
                    const reviewFlags = [
                        entry.guided ? t("profiles.settings_filter_guided_covered") : t("profiles.settings_filter_all_settings_only"),
                        entry.invalid ? t("profiles.settings_filter_invalid") : "",
                        entry.deprecated ? t("profiles.settings_filter_deprecated") : "",
                        entry.rawFallback ? t("profiles.settings_filter_raw") : "",
                        entry.unknown ? t("profiles.settings_filter_unknown") : "",
                    ].filter(Boolean);
                    const valueLabel = entry.configured
                        ? entry.value
                        : t("profiles.settings_list_value_not_configured");
                    const searchScopes = ["catalog"];
                    if (entry.configured) searchScopes.push("configured");
                    if (entryNeedsReview(entry)) searchScopes.push("review");

                    return createSettingsSearchEntry({
                        title: entry.label || entry.id,
                        description: [stateLabel, valueLabel].filter(Boolean).join(" • "),
                        target: `all-settings-entry:${entry.kind}:${entry.id}`,
                        sectionId: entry.categoryId || "",
                        areaLabel: entry.categoryLabel || "",
                        kind: entry.kind === "preference"
                            ? "all_settings_preference"
                            : "all_settings_policy",
                        searchGroup: entry.kind === "preference"
                            ? "preferences"
                            : (entry.configured ? "configured_settings" : "available_policies"),
                        searchScopes,
                        keywords: [
                            entry.id || "",
                            entry.label || "",
                            entry.kind || "",
                            entry.kindLabel || "",
                            entry.categoryId || "",
                            entry.categoryLabel || "",
                            stateLabel,
                            valueLabel,
                            entry.target || "",
                            ...reviewFlags,
                        ],
                    });
                });
        }

        function buildPolicyBlueprintSearchEntries(allSettingsEntries = []) {
            return allSettingsEntries
                .filter((entry) => entry?.kind === "policy" && entry.schemaItem)
                .map((entry) => {
                    const item = entry.schemaItem;
                    return createSettingsSearchEntry({
                        title: item.label || entry.label || entry.id,
                        description: item.support_level === "fallback"
                            ? t("profiles.wizard_shell_raw_body")
                            : t("profiles.wizard_shell_additional_body"),
                        target: resolveTargetAlias(entry.target),
                        sectionId: entry.schemaStepId || entry.categoryId || "",
                        areaLabel: item.subsection_label || entry.categoryLabel || "",
                        kind: "policy_blueprint",
                        searchScopes: ["catalog"],
                        keywords: [
                            item.id || entry.id || "",
                            item.widget || "",
                            item.complexity || "",
                            entry.categoryId || "",
                            entry.categoryLabel || "",
                            ...(Array.isArray(item.tags) ? item.tags : []),
                        ],
                    });
                });
        }

        function buildIndex() {
            const sections = Array.isArray(wizardSettingsCatalog.sections) ? wizardSettingsCatalog.sections : [];
            const allSettingsEntries = getAllSettingsInventoryEntries();
            const entries = buildAllSettingsInventoryEntries(allSettingsEntries);
            buildShellPolicyTargetIndex(allSettingsEntries);

            sections.forEach((section) => {
                const preferenceSection = section.preferences && typeof section.preferences === "object"
                    ? section.preferences
                    : null;

                Object.entries(section.ui_controls || {}).forEach(([mapId, controls]) => {
                    const areas = Object.fromEntries(
                        ((section.ui_maps && section.ui_maps[mapId]) || []).map((item) => [
                            item.id,
                            t(item.label_key, item.fallback),
                        ]),
                    );

                    (controls || []).forEach((item) => {
                        entries.push(
                            createSettingsSearchEntry({
                                title: t(item.label_key, item.fallback),
                                description: areas[item.area_id] || "",
                                target: resolveTargetAlias(item.target),
                                sectionId: section.id,
                                areaLabel: areas[item.area_id] || "",
                                kind: "control",
                                keywords: [mapId],
                            }),
                        );
                    });
                });

                if (preferenceSection) {
                    const guiGroups = Object.fromEntries(
                        (preferenceSection.gui_groups || []).map((group) => [
                            group.id,
                            t(group.label_key, group.fallback),
                        ]),
                    );
                    const sectionTitle = t(preferenceSection.title_key, preferenceSection.id);
                    const sectionBody = t(preferenceSection.body_key, preferenceSection.id);

                    entries.push(
                        createSettingsSearchEntry({
                            title: sectionTitle,
                            description: sectionBody,
                            target: resolveTargetAlias(`pref-section:${preferenceSection.id}`),
                            sectionId: section.id,
                            areaLabel: sectionTitle,
                            kind: "preference_section",
                            searchGroup: "preferences",
                            searchScopes: ["catalog"],
                            keywords: [
                                ...(preferenceSection.prefixes || []),
                                ...Object.values(guiGroups),
                            ],
                        }),
                    );

                    const presetsById = Object.fromEntries(
                        (preferenceSection.presets || []).map((preset) => [preset.id, preset]),
                    );
                    (preferenceSection.controls || []).forEach((item) => {
                        const presetId = String(item.target || "").replace("preference-preset:", "");
                        const preset = presetsById[presetId] || {};
                        entries.push(
                            createSettingsSearchEntry({
                                title: t(item.label_key, item.fallback),
                                description: t(preset.description_key, preset.pref || ""),
                                target: resolveTargetAlias(item.target),
                                sectionId: section.id,
                                areaLabel: guiGroups[item.area_id] || "",
                                kind: "preference_preset",
                                searchGroup: "preferences",
                                searchScopes: ["catalog"],
                                keywords: [
                                    preset.pref || "",
                                    preset.status || "",
                                    preset.type || "",
                                    guiGroups[item.area_id] || "",
                                    presetId,
                                ],
                            }),
                        );
                    });

                    (preferenceSection.bundles || []).forEach((bundle) => {
                        entries.push(
                            createSettingsSearchEntry({
                                title: t(bundle.label_key, bundle.id),
                                description: t(bundle.description_key, bundle.id),
                                target: resolveTargetAlias(`preference-bundle:${bundle.id}`),
                                sectionId: section.id,
                                areaLabel: guiGroups[bundle.area_id] || sectionTitle,
                                kind: "preference_bundle",
                                searchGroup: "preferences",
                                searchScopes: ["catalog"],
                                keywords: [
                                    bundle.id,
                                    guiGroups[bundle.area_id] || "",
                                    ...((bundle.items || []).map((item) => item.pref)),
                                ],
                            }),
                        );
                    });

                    (preferenceSection.known_preferences || []).forEach((knownPreference) => {
                        entries.push(
                            createSettingsSearchEntry({
                                title: knownPreference.pref,
                                description: t(
                                    knownPreference.description_key,
                                    knownPreference.description_fallback
                                        || knownPreference.fallback
                                        || knownPreference.pref,
                                ),
                                target: resolveTargetAlias(`pref-section:${preferenceSection.id}`),
                                sectionId: section.id,
                                areaLabel: sectionTitle,
                                kind: "known_preference",
                                searchGroup: "preferences",
                                searchScopes: ["catalog"],
                                keywords: [
                                    knownPreference.status || "",
                                    knownPreference.type || "",
                                    knownPreference.description_fallback || "",
                                    ...(knownPreference.preset_ids || []),
                                ],
                            }),
                        );
                    });
                }
            });

            searchEnginePresetCatalog.forEach((preset) => {
                const engineMeta = searchEnginePresets[preset.id] || {};
                entries.push(
                    createSettingsSearchEntry({
                        title: t(preset.title_key, preset.id),
                        description: t(preset.description_key, engineMeta.Description || ""),
                        target: resolveTargetAlias(preset.target),
                        sectionId: "search",
                        areaLabel: t("profiles.wizard_search_presets_title"),
                        kind: "search_engine_preset",
                        keywords: [
                            engineMeta.Name || "",
                            engineMeta.URLTemplate || "",
                            engineMeta.Alias || "",
                            preset.id,
                        ],
                    }),
                );
            });

            entries.push(...buildPolicyBlueprintSearchEntries(allSettingsEntries));

            wizardSettingsSearchIndex = entries;
        }

        function scoreEntry(entry, tokens, normalizedQuery) {
            let score = 0;
            const normalizedTitle = normalizeSearchText(entry.title);
            const normalizedDescription = normalizeSearchText(entry.description);
            const normalizedArea = normalizeSearchText(entry.areaLabel);

            if (normalizedTitle === normalizedQuery) score += 120;
            if (normalizedTitle.startsWith(normalizedQuery)) score += 80;
            if (normalizedTitle.includes(normalizedQuery)) score += 60;
            if (normalizedArea.includes(normalizedQuery)) score += 40;
            if (normalizedDescription.includes(normalizedQuery)) score += 24;
            if (entry.searchText.includes(normalizedQuery)) score += 18;
            score += tokens.length * 2;
            score -= entry.stepNumber;
            return score;
        }

        function groupPriority(group) {
            const priorities = {
                configured_settings: 0,
                preferences: 1,
                available_policies: 2,
                actions: 3,
            };
            return priorities[group] ?? 9;
        }

        function dedupeTargets(matches) {
            const byTarget = new Map();
            matches.forEach((entry) => {
                const target = String(entry.target || "").trim();
                if (!target) return;
                const existing = byTarget.get(target);
                if (
                    !existing
                    || groupPriority(entry.searchGroup) < groupPriority(existing.searchGroup)
                    || (
                        groupPriority(entry.searchGroup) === groupPriority(existing.searchGroup)
                        && entry.score > existing.score
                    )
                ) {
                    byTarget.set(target, entry);
                }
            });
            return Array.from(byTarget.values())
                .sort((left, right) =>
                    right.score - left.score
                    || groupPriority(left.searchGroup) - groupPriority(right.searchGroup)
                    || left.stepNumber - right.stepNumber
                    || left.title.localeCompare(right.title)
                );
        }

        function matchesSearchScope(entry, scope) {
            if (!isAllSettingsRoute || scope === "all") return true;
            return Array.isArray(entry.searchScopes) && entry.searchScopes.includes(scope);
        }

        function findMatches(query, options = {}) {
            const normalizedQuery = normalizeSearchText(query);
            if (!normalizedQuery) return [];

            const tokens = normalizedQuery.split(" ").filter(Boolean);
            const matches = wizardSettingsSearchIndex
                .filter((entry) => tokens.every((token) => entry.searchText.includes(token)))
                .filter((entry) => matchesSearchScope(entry, options.scope || "all"))
                .map((entry) => ({
                    ...entry,
                    score: scoreEntry(entry, tokens, normalizedQuery),
                }))
                .sort((left, right) =>
                    right.score - left.score
                    || groupPriority(left.searchGroup) - groupPriority(right.searchGroup)
                    || left.stepNumber - right.stepNumber
                    || left.title.localeCompare(right.title)
                );
            const deduped = options.dedupeTargets ? dedupeTargets(matches) : matches;
            return deduped.slice(0, options.limit || 8);
        }

        function allSettingsSearchGroups() {
            return [
                {
                    id: "configured_settings",
                    label: t("profiles.settings_search_group_configured"),
                },
                {
                    id: "available_policies",
                    label: t("profiles.settings_search_group_available_policies"),
                },
                {
                    id: "preferences",
                    label: t("profiles.settings_search_group_preferences"),
                },
                {
                    id: "actions",
                    label: t("profiles.settings_search_group_actions"),
                },
            ];
        }

        function createResultButton(entry) {
            const button = documentRef.createElement("button");
            button.type = "button";
            button.className = "button-base ghost-button wizard-settings-search-result";
            button.dataset.settingsSearchTarget = entry.target;
            button.setAttribute(
                "aria-label",
                [entry.title, entry.stepLabel, entry.kindLabel, entry.areaLabel].filter(Boolean).join(". "),
            );
            button.innerHTML = `
                <span class="wizard-settings-search-result-top">
                    <span class="wizard-settings-search-result-title">${escapeHtml(entry.title)}</span>
                    <span class="wizard-settings-search-result-step">${escapeHtml(entry.stepNumber ? `${t("profiles.wizard_settings_search_step")} ${entry.stepNumber} • ${entry.stepLabel}` : entry.stepLabel)}</span>
                </span>
                <span class="wizard-settings-search-result-meta">${escapeHtml([entry.kindLabel, entry.areaLabel, entry.description].filter(Boolean).join(" • "))}</span>
            `;
            return button;
        }

        function renderFlatResults(matches) {
            matches.forEach((entry) => {
                wizardSettingsSearchResultsEl.appendChild(createResultButton(entry));
            });
        }

        function renderGroupedResults(matches) {
            allSettingsSearchGroups().forEach((group) => {
                const groupMatches = matches
                    .filter((entry) => entry.searchGroup === group.id)
                    .slice(0, 4);
                if (!groupMatches.length) return;

                const groupEl = documentRef.createElement("div");
                groupEl.className = "wizard-settings-search-group";
                groupEl.dataset.settingsSearchGroup = group.id;
                groupEl.innerHTML = `
                    <div class="wizard-settings-search-group-title">${escapeHtml(group.label)}</div>
                `;
                groupMatches.forEach((entry) => {
                    groupEl.appendChild(createResultButton(entry));
                });
                wizardSettingsSearchResultsEl.appendChild(groupEl);
            });
        }

        function syncScopeButtons() {
            if (!wizardSettingsSearchScopeEl) return;
            wizardSettingsSearchScopeEl.hidden = !isAllSettingsRoute;
            wizardSettingsSearchScopeButtons.forEach((button) => {
                const scope = button.dataset.settingsSearchScope || "all";
                const active = scope === activeSearchScope;
                button.classList.toggle("is-active", active);
                button.setAttribute("aria-pressed", active ? "true" : "false");
            });
        }

        function updateMeta(query, matches) {
            if (!wizardSettingsSearchMetaEl) return;

            const trimmedQuery = query.trim();
            if (!trimmedQuery) {
                wizardSettingsSearchMetaEl.textContent = isAllSettingsRoute
                    ? t("profiles.settings_search_hint")
                    : t("profiles.wizard_settings_search_hint");
                return;
            }

            if (matches.length === 0) {
                wizardSettingsSearchMetaEl.textContent = isAllSettingsRoute
                    ? t("profiles.settings_search_empty")
                    : t("profiles.wizard_settings_search_empty");
                return;
            }

            if (isAllSettingsRoute) {
                wizardSettingsSearchMetaEl.textContent = t(
                    matches.length === 1
                        ? "profiles.settings_search_match_one"
                        : "profiles.settings_search_match_many",
                ).replace("{count}", String(matches.length));
                return;
            }
            wizardSettingsSearchMetaEl.textContent = t("profiles.wizard_settings_search_match_count")
                .replace("{count}", String(matches.length));
        }

        function renderResults() {
            if (!wizardSettingsSearchInputEl || !wizardSettingsSearchResultsEl || !wizardSettingsSearchClearEl) return;

            const query = wizardSettingsSearchInputEl.value || "";
            allSettingsRouteState?.setSearchQuery(query);
            buildIndex();
            const matches = findMatches(query, {
                dedupeTargets: isAllSettingsRoute,
                limit: isAllSettingsRoute ? 24 : 8,
                scope: activeSearchScope,
            });
            wizardSettingsSearchResultsEl.innerHTML = "";
            wizardSettingsSearchResultsEl.hidden = !query.trim() || matches.length === 0;
            wizardSettingsSearchClearEl.hidden = !query.trim();
            updateMeta(query, matches);
            syncScopeButtons();

            if (isAllSettingsRoute) {
                renderGroupedResults(matches);
            } else {
                renderFlatResults(matches);
            }
        }

        function firstResultButton() {
            return wizardSettingsSearchResultsEl?.querySelector?.("[data-settings-search-target]") || null;
        }

        function activateSearchResult(button) {
            if (!button) return false;
            const targetEl = findTarget(button.dataset.settingsSearchTarget || "");
            if (!targetEl) return false;
            revealTarget(targetEl);
            return true;
        }

        function clear() {
            if (!wizardSettingsSearchInputEl) return;
            wizardSettingsSearchInputEl.value = "";
            wizardSettingsSearchInputEl.dispatchEvent(new window.Event("input", { bubbles: true }));
            wizardSettingsSearchInputEl.dispatchEvent(new window.Event("search", { bubbles: true }));
            renderResults();
        }

        function findTarget(targetKey) {
            const normalizedTarget = String(targetKey || "").trim();
            if (!normalizedTarget) return null;
            allSettingsRouteState?.setFocusedTarget(normalizedTarget);
            if (
                isAllSettingsRoute
                && (
                    normalizedTarget.startsWith("preference-preset:")
                    || normalizedTarget.startsWith("preference-bundle:")
                )
            ) {
                const action = documentRef.querySelector(`[data-settings-target="${normalizedTarget}"]`);
                action?.click?.();
                return documentRef.getElementById("all-settings-list-panel")
                    || documentRef.getElementById("all-settings-detail-panel");
            }
            if (isAllSettingsRoute) {
                const entryTarget = resolveAllSettingsEntryTarget(normalizedTarget);
                if (entryTarget) {
                    return findAllSettingsEntryTarget?.(entryTarget) || null;
                }
            }
            return documentRef.querySelector(`[data-settings-target="${normalizedTarget}"]`)
                || documentRef.querySelector(`[data-settings-target="${resolveTargetAlias(normalizedTarget)}"]`);
        }

        function resolveAllSettingsEntryTarget(targetKey) {
            const normalizedTarget = String(targetKey || "").trim();
            if (!normalizedTarget) return "";
            if (normalizedTarget.startsWith("all-settings-entry:")) return normalizedTarget;
            const resolvedTarget = resolveTargetAlias(normalizedTarget);
            if (resolvedTarget.startsWith("all-settings-entry:")) return resolvedTarget;
            const entries = getAllSettingsInventoryEntries();
            const entry = entries.find((item) =>
                item?.target === normalizedTarget
                || item?.target === resolvedTarget
                || (normalizedTarget.startsWith("policy:") && item?.kind === "policy" && item?.id === normalizedTarget.slice("policy:".length))
                || (normalizedTarget.startsWith("known-preference:") && item?.kind === "preference" && item?.id === normalizedTarget.slice("known-preference:".length))
                || (normalizedTarget.startsWith("preference:") && item?.kind === "preference" && item?.id === normalizedTarget.slice("preference:".length))
                || (
                    normalizedTarget.startsWith("pref-section:")
                    && item?.kind === "preference"
                    && item?.editor?.preferenceSectionId === normalizedTarget.slice("pref-section:".length)
                )
            );
            return entry ? `all-settings-entry:${entry.kind}:${entry.id}` : "";
        }

        function revealTarget(targetEl) {
            if (!targetEl) return;

            const panel = targetEl.closest(".wizard-panel");
            if (panel?.id?.startsWith("wizard-step-")) {
                const nextStep = Number(panel.id.replace("wizard-step-", ""));
                if (!Number.isNaN(nextStep)) {
                    setWizardStep(nextStep);
                }
            }

            targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
            targetEl.classList.add("settings-target-highlight");
            window.setTimeout(() => {
                targetEl.classList.remove("settings-target-highlight");
            }, 1800);

            const focusTarget = targetEl.matches("input, select, textarea, button, [tabindex]")
                ? targetEl
                : targetEl.querySelector(
                    "[data-settings-detail-primary-focus], .all-settings-detail-editor [data-schema-policy-field], .all-settings-detail-editor [data-schema-branch-mode], input, select, textarea, button, [tabindex]",
                );
            focusTarget?.focus?.({ preventScroll: true });
        }

        function applyFilter(navEl, areaId) {
            if (!navEl) return;

            navEl.querySelectorAll("[data-settings-filter]").forEach((button) => {
                button.classList.toggle("is-active", button.dataset.settingsFilter === areaId);
            });
            navEl.querySelectorAll("[data-settings-area-id]").forEach((button) => {
                const matches = areaId === "all" || button.dataset.settingsAreaId === areaId;
                button.hidden = !matches;
            });
        }

        wizardSettingsSearchInputEl?.addEventListener("input", () => {
            renderResults();
        });
        wizardSettingsSearchInputEl?.addEventListener("search", () => {
            renderResults();
        });
        wizardSettingsSearchInputEl?.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                clear();
                return;
            }
            if (event.key === "Enter") {
                if (activateSearchResult(firstResultButton())) {
                    event.preventDefault();
                }
                return;
            }
            if (event.key === "ArrowDown") {
                const firstResult = firstResultButton();
                if (firstResult) {
                    event.preventDefault();
                    firstResult.focus?.();
                }
            }
        });
        wizardSettingsSearchClearEl?.addEventListener("click", () => {
            clear();
            wizardSettingsSearchInputEl?.focus();
        });
        wizardSettingsSearchScopeButtons.forEach((button) => {
            button.addEventListener("click", () => {
                activeSearchScope = button.dataset.settingsSearchScope || "all";
                renderResults();
            });
        });

        return {
            buildIndex,
            renderResults,
            clear,
            findTarget,
            revealTarget,
            applyFilter,
        };
    }

    window.BPMProfilesSettingsSearch = { create };
})();
