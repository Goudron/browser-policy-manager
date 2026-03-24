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
    }) {
        const {
            t,
            humanizeIdentifier,
            normalizeSearchText,
            getActiveWizardSchemaVersion,
            setWizardStep,
        } = dependencies;
        const getCurrentLang = state.getCurrentLang || (() => "en");

        const {
            wizardSettingsSearchInputEl,
            wizardSettingsSearchMetaEl,
            wizardSettingsSearchResultsEl,
            wizardSettingsSearchClearEl,
        } = elements;

        let wizardSettingsSearchIndex = [];

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
                control: t("profiles.wizard_settings_search_kind_control", "Control"),
                preference_section: t("profiles.wizard_settings_search_kind_preferences_section", "Preferences section"),
                preference_preset: t("profiles.wizard_settings_search_kind_preference_preset", "Preference preset"),
                preference_bundle: t("profiles.wizard_settings_search_kind_preference_bundle", "Preference bundle"),
                known_preference: t("profiles.wizard_settings_search_kind_known_preference", "Known preference"),
                search_engine_preset: t("profiles.wizard_settings_search_kind_search_preset", "Search engine preset"),
                policy_blueprint: t("profiles.wizard_settings_search_kind_policy_blueprint", "Schema policy"),
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

        function buildIndex() {
            const sections = Array.isArray(wizardSettingsCatalog.sections) ? wizardSettingsCatalog.sections : [];
            const entries = [];

            sections.forEach((section) => {
                const preferenceSection = section.preferences && typeof section.preferences === "object"
                    ? section.preferences
                    : null;

                Object.entries(section.ui_docs || {}).forEach(([mapId, docs]) => {
                    const areas = Object.fromEntries(
                        ((section.ui_maps && section.ui_maps[mapId]) || []).map((item) => [
                            item.id,
                            t(item.label_key, item.fallback),
                        ]),
                    );

                    (docs || []).forEach((item) => {
                        entries.push(
                            createSettingsSearchEntry({
                                title: t(item.label_key, item.fallback),
                                description: areas[item.area_id] || "",
                                target: item.target,
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
                            target: `pref-section:${preferenceSection.id}`,
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
                    (preferenceSection.docs || []).forEach((item) => {
                        const presetId = String(item.target || "").replace("preference-preset:", "");
                        const preset = presetsById[presetId] || {};
                        entries.push(
                            createSettingsSearchEntry({
                                title: t(item.label_key, item.fallback),
                                description: t(preset.description_key, preset.pref || ""),
                                target: item.target,
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
                                target: `preference-bundle:${bundle.id}`,
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
                                target: `pref-section:${preferenceSection.id}`,
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
                        target: preset.target,
                        sectionId: "search",
                        areaLabel: t("profiles.wizard_search_presets_title", "Quick presets"),
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
                                ? t("profiles.wizard_shell_raw_body", "Policies we preserve through the document editor until we build dedicated UI for them.")
                                : t("profiles.wizard_shell_additional_body", "Policies already classified into this step, but still better handled as advanced controls."),
                            target: item.target,
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
                wizardSettingsSearchMetaEl.textContent = t(
                    "profiles.wizard_settings_search_hint",
                    "Search by control, Firefox Settings area, policy key, preference key, or preset.",
                );
                return;
            }

            if (matches.length === 0) {
                wizardSettingsSearchMetaEl.textContent = t(
                    "profiles.wizard_settings_search_empty",
                    "No matching settings found in the wizard.",
                );
                return;
            }

            const single = matches.length === 1;
            wizardSettingsSearchMetaEl.textContent = getCurrentLang() === "ru"
                ? `${matches.length} ${single ? "совпадение" : "совпадений"} в мастере.`
                : `${matches.length} ${single ? "match" : "matches"} in the wizard.`;
        }

        function renderResults() {
            if (!wizardSettingsSearchInputEl || !wizardSettingsSearchResultsEl || !wizardSettingsSearchClearEl) return;

            const query = wizardSettingsSearchInputEl.value || "";
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
                button.innerHTML = `
                    <span class="wizard-settings-search-result-top">
                        <span class="wizard-settings-search-result-title">${entry.title}</span>
                        <span class="wizard-settings-search-result-step">${entry.stepNumber ? `${t("profiles.wizard_settings_search_step", "Step")} ${entry.stepNumber} • ${entry.stepLabel}` : entry.stepLabel}</span>
                    </span>
                    <span class="wizard-settings-search-result-meta">${[entry.kindLabel, entry.areaLabel, entry.description].filter(Boolean).join(" • ")}</span>
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
            return documentRef.querySelector(`[data-settings-target="${targetKey}"]`);
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
