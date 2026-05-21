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
            getActiveWizardSchemaVersion,
            setWizardStep,
            getAllSettingsSearchEntries,
            findAllSettingsEntryTarget,
        } = dependencies;
        const getCurrentLang = state.getCurrentLang || (() => "en");
        const isAllSettingsRoute = documentRef.body?.dataset.profilesTemplateKind === "settings";

        const {
            wizardSettingsSearchInputEl,
            wizardSettingsSearchMetaEl,
            wizardSettingsSearchResultsEl,
            wizardSettingsSearchClearEl,
        } = elements;

        let wizardSettingsSearchIndex = [];
        let shellPolicyTargetByAlias = {};

        function buildShellPolicyTargetIndex() {
            const schemaVersion = getActiveWizardSchemaVersion();
            const shellSteps = Array.isArray(wizardSchemaShellCatalog.steps) ? wizardSchemaShellCatalog.steps : [];
            const channelData = wizardSchemaShellCatalog.channels?.[schemaVersion];
            const targetIndex = {};

            shellSteps.forEach((stepMeta) => {
                const stepData = channelData?.steps?.[String(stepMeta.step)] || {};
                [
                    ...(Array.isArray(stepData.recommended) ? stepData.recommended : []),
                    ...(Array.isArray(stepData.additional) ? stepData.additional : []),
                    ...(Array.isArray(stepData.raw_fallback) ? stepData.raw_fallback : []),
                ].forEach((item) => {
                    if (!item?.id || !item?.target) return;
                    targetIndex[`policy:${item.id}`] = item.target;
                });
            });

            shellPolicyTargetByAlias = targetIndex;
        }

        function resolveTargetAlias(target) {
            const normalizedTarget = String(target || "").trim();
            if (!normalizedTarget) return "";
            if (Object.keys(shellPolicyTargetByAlias).length === 0) {
                buildShellPolicyTargetIndex();
            }
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

        function buildAllSettingsInventoryEntries() {
            return (Array.isArray(getAllSettingsSearchEntries?.()) ? getAllSettingsSearchEntries() : [])
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

                    return createSettingsSearchEntry({
                        title: entry.label || entry.id,
                        description: [stateLabel, valueLabel].filter(Boolean).join(" • "),
                        target: `all-settings-entry:${entry.kind}:${entry.id}`,
                        sectionId: entry.categoryId || "",
                        areaLabel: entry.categoryLabel || "",
                        kind: entry.kind === "preference"
                            ? "all_settings_preference"
                            : "all_settings_policy",
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

        function buildIndex() {
            const sections = Array.isArray(wizardSettingsCatalog.sections) ? wizardSettingsCatalog.sections : [];
            const entries = buildAllSettingsInventoryEntries();
            buildShellPolicyTargetIndex();

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

            const schemaVersion = getActiveWizardSchemaVersion();
            const shellSteps = Array.isArray(wizardSchemaShellCatalog.steps) ? wizardSchemaShellCatalog.steps : [];
            const channelData = wizardSchemaShellCatalog.channels?.[schemaVersion];

            shellSteps.forEach((stepMeta) => {
                const stepData = channelData?.steps?.[String(stepMeta.step)] || {};
                const shellItems = [
                    ...(Array.isArray(stepData.recommended) ? stepData.recommended : []),
                    ...(Array.isArray(stepData.additional) ? stepData.additional : []),
                    ...(Array.isArray(stepData.raw_fallback) ? stepData.raw_fallback : []),
                ];

                shellItems.forEach((item) => {
                    entries.push(
                        createSettingsSearchEntry({
                            title: item.label || item.id,
                            description: item.support_level === "fallback"
                                ? t("profiles.wizard_shell_raw_body")
                                : t("profiles.wizard_shell_additional_body"),
                            target: resolveTargetAlias(item.target),
                            sectionId: stepMeta.id,
                            areaLabel: item.subsection_label || "",
                            kind: "policy_blueprint",
                            keywords: [
                                item.id || "",
                                item.widget || "",
                                item.complexity || "",
                                ...(Array.isArray(item.tags) ? item.tags : []),
                            ],
                        }),
                    );
                });
            });

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

        function findMatches(query) {
            const normalizedQuery = normalizeSearchText(query);
            if (!normalizedQuery) return [];

            const tokens = normalizedQuery.split(" ").filter(Boolean);
            return wizardSettingsSearchIndex
                .filter((entry) => tokens.every((token) => entry.searchText.includes(token)))
                .map((entry) => ({
                    ...entry,
                    score: scoreEntry(entry, tokens, normalizedQuery),
                }))
                .sort((left, right) => right.score - left.score || left.stepNumber - right.stepNumber || left.title.localeCompare(right.title))
                .slice(0, 8);
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

            const single = matches.length === 1;
            if (isAllSettingsRoute) {
                wizardSettingsSearchMetaEl.textContent = t(
                    single
                        ? "profiles.settings_search_match_one"
                        : "profiles.settings_search_match_many",
                ).replace("{count}", String(matches.length));
                return;
            }
            wizardSettingsSearchMetaEl.textContent = getCurrentLang() === "ru"
                ? `${matches.length} ${single ? "совпадение" : "совпадений"} в мастере.`
                : `${matches.length} ${single ? "match" : "matches"} in the wizard.`;
        }

        function renderResults() {
            if (!wizardSettingsSearchInputEl || !wizardSettingsSearchResultsEl || !wizardSettingsSearchClearEl) return;

            const query = wizardSettingsSearchInputEl.value || "";
            buildIndex();
            const matches = findMatches(query);
            wizardSettingsSearchResultsEl.innerHTML = "";
            wizardSettingsSearchResultsEl.hidden = !query.trim() || matches.length === 0;
            wizardSettingsSearchClearEl.hidden = !query.trim();
            updateMeta(query, matches);

            matches.forEach((entry) => {
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
                wizardSettingsSearchResultsEl.appendChild(button);
            });
        }

        function clear() {
            if (!wizardSettingsSearchInputEl) return;
            wizardSettingsSearchInputEl.value = "";
            renderResults();
        }

        function findTarget(targetKey) {
            const normalizedTarget = String(targetKey || "").trim();
            if (!normalizedTarget) return null;
            if (normalizedTarget.startsWith("all-settings-entry:")) {
                return findAllSettingsEntryTarget?.(normalizedTarget) || null;
            }
            return documentRef.querySelector(`[data-settings-target="${normalizedTarget}"]`)
                || documentRef.querySelector(`[data-settings-target="${resolveTargetAlias(normalizedTarget)}"]`);
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

            const focusTarget = targetEl.matches("input, select, textarea, button")
                ? targetEl
                : targetEl.querySelector("input, select, textarea, button");
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
            }
        });
        wizardSettingsSearchClearEl?.addEventListener("click", () => {
            clear();
            wizardSettingsSearchInputEl?.focus();
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
