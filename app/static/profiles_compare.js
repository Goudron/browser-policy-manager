(() => {
    const sideKeys = ["left", "right"];
    const compareProfileResultsLimit = 40;

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function buildProfileSearchFilters(query) {
        return {
            q: String(query || "").trim(),
            lifecycle: "active",
            includeDeleted: false,
            limit: compareProfileResultsLimit,
            sort: "updated_at",
            order: "desc",
        };
    }

    function readEmbeddedJson(documentRef, elementId) {
        const element = documentRef.getElementById(elementId);
        try {
            return element ? JSON.parse(element.textContent || "{}") : {};
        } catch {
            return {};
        }
    }

    function buildPreferenceLabelLookup(preferencesCatalog = {}, locale = {}) {
        const knownPreferences = Array.isArray(preferencesCatalog.known_preferences)
            ? preferencesCatalog.known_preferences
            : [];
        return knownPreferences.reduce((lookup, item) => {
            if (!item?.pref) return lookup;
            const translated = item.label_key && typeof locale[item.label_key] === "string"
                ? locale[item.label_key]
                : "";
            lookup[item.pref] = translated || item.fallback || item.pref;
            return lookup;
        }, {});
    }

    function resolvePreselectedProfileIds(locationRef = window.location) {
        const href = String(locationRef?.href || "");
        const query = href.includes("?") ? href.slice(href.indexOf("?") + 1).split("#")[0] : "";
        const URLConstructor = window.URL || (typeof URL !== "undefined" ? URL : null);
        const params = URLConstructor
            ? new URLConstructor(href || "http://bpm.local/profiles/compare").searchParams
            : {
                get(key) {
                    return query
                        .split("&")
                        .map((part) => part.split("="))
                        .find(([name]) => decodeURIComponent(name || "") === key)?.[1] || null;
                },
            };
        const resolveId = (key) => {
            const value = Number(params.get(key) || 0);
            return Number.isInteger(value) && value > 0 ? value : null;
        };
        return {
            left: resolveId("left"),
            right: resolveId("right"),
        };
    }

    function formatProfileSummary(profile, formatSchemaLabel = (value) => value || "") {
        const schema = formatSchemaLabel(profile?.schema_version || "");
        const updated = profile?.updated_at ? String(profile.updated_at) : "";
        return [schema, updated].filter(Boolean).join(" • ");
    }

    function formatProfileSchema(profile, formatSchemaLabel = (value) => value || "") {
        return formatSchemaLabel(profile?.schema_version || "") || "";
    }

    function formatProfileUpdatedAt(profile) {
        return profile?.updated_at ? String(profile.updated_at) : "";
    }

    function resolveCompareValueState(entry, otherEntry, compareState) {
        if (!entry?.present) return "missing";
        if (!otherEntry?.present) return "different";
        return compareState.snapshotToString(entry.value) === compareState.snapshotToString(otherEntry.value)
            ? "equal"
            : "different";
    }

    function resolveSettingPresentation(rowKey, options = {}) {
        if (rowKey.kind === "preference") {
            const preferenceLabels = options.preferenceLabels || {};
            const preferenceName = rowKey.preferenceName || rowKey.label || "";
            return {
                label: preferenceLabels[preferenceName] || preferenceName,
                kindLabel: options.preferenceKindLabel || "Managed preference",
                settingKey: rowKey.settingKey || `Preferences.${preferenceName}`,
            };
        }
        return {
            label: rowKey.label,
            kindLabel: options.policyKindLabel || "Policy",
            settingKey: rowKey.settingKey,
        };
    }

    function renderSettingIdentity(compareRow) {
        let settingKey = "";
        if (compareRow.settingKey && compareRow.settingKey !== compareRow.label) {
            settingKey = compareRow.settingKey;
        }
        return `
            <span class="compare-setting-cell__kind" data-compare-setting-kind="${escapeHtml(compareRow.kind)}">
                ${escapeHtml(compareRow.kindLabel)}
            </span>
            <span class="compare-setting-cell__label" data-compare-setting-label>${escapeHtml(compareRow.label)}</span>
            ${settingKey ? `<span class="compare-setting-cell__meta" data-compare-setting-key>${escapeHtml(settingKey)}</span>` : ""}
        `;
    }

    function resolveValueStateLabel(state, options = {}) {
        const labels = options.stateLabels || {};
        const fallbackLabels = {
            missing: "Missing",
            equal: "Same value",
            different: "Different value",
        };
        return labels[state] || fallbackLabels[state] || state;
    }

    function buildCompareRows(leftProfile, rightProfile, compareState = window.BPMProfilesCompareState, options = {}) {
        if (!leftProfile || !rightProfile || !compareState) return [];
        const leftFlags = leftProfile.flags && typeof leftProfile.flags === "object" ? leftProfile.flags : {};
        const rightFlags = rightProfile.flags && typeof rightProfile.flags === "object" ? rightProfile.flags : {};
        const rowKeys = compareState.collectProfileSettingKeys(leftFlags, rightFlags);
        const missingLabel = options.missingLabel || "Missing";

        return rowKeys.map((rowKey) => {
            const leftEntry = compareState.readSettingValue(leftFlags, rowKey);
            const rightEntry = compareState.readSettingValue(rightFlags, rowKey);
            const leftState = resolveCompareValueState(leftEntry, rightEntry, compareState);
            const rightState = resolveCompareValueState(rightEntry, leftEntry, compareState);
            const presentation = resolveSettingPresentation(rowKey, options);
            return {
                ...rowKey,
                label: presentation.label,
                kindLabel: presentation.kindLabel,
                settingKey: presentation.settingKey,
                left: {
                    state: leftState,
                    stateLabel: resolveValueStateLabel(leftState, options),
                    value: leftEntry.present ? leftEntry.value : null,
                    displayValue: compareState.formatCompareValue(leftEntry, { missingLabel }),
                },
                right: {
                    state: rightState,
                    stateLabel: resolveValueStateLabel(rightState, options),
                    value: rightEntry.present ? rightEntry.value : null,
                    displayValue: compareState.formatCompareValue(rightEntry, { missingLabel }),
                },
                changed: leftState !== "equal" || rightState !== "equal",
            };
        });
    }

    function getSideState(state, side) {
        return state[side] || state.left;
    }

    function createInitialState() {
        return {
            left: {
                items: [],
                loading: false,
                error: "",
                query: "",
                selected: null,
                requestId: 0,
            },
            right: {
                items: [],
                loading: false,
                error: "",
                query: "",
                selected: null,
                requestId: 0,
            },
        };
    }

    function start({
        documentRef = document,
        windowRef = window,
    } = {}) {
        const rootEl = documentRef.getElementById("compare-page");
        if (!rootEl) return null;

        const data = windowRef.BPMProfilesData;
        const compareState = windowRef.BPMProfilesCompareState;
        const platform = windowRef.BPMProfilesPlatform;
        if (!data || !compareState || !platform) return null;
        const { resolveBrowserLanguage } = platform;
        const { resolveTheme, updateThemeColorMeta, syncThemeSensitiveControls } = platform;
        const utils = windowRef.BPMProfilesUtils || {};
        let locale = windowRef.__BPM_INITIAL_LOCALE__ || {};
        const preferencesCatalog = readEmbeddedJson(documentRef, "compare-preferences-catalog");
        let preferenceLabels = buildPreferenceLabelLookup(preferencesCatalog, locale);
        const state = createInitialState();
        const preselectedIds = resolvePreselectedProfileIds(windowRef.location);
        const searchTimers = new Map();
        let localeRequestId = 0;
        const langStorageKey = "bpm-lang-mode";
        const themeStorageKey = "bpm-theme-mode";
        const langSelectEl = documentRef.getElementById("lang");
        const themeSelectEl = documentRef.getElementById("theme");
        const tableRowsEl = documentRef.getElementById("compare-settings-rows");
        const elements = Object.fromEntries(sideKeys.map((side) => [
            side,
            {
                search: documentRef.getElementById(`compare-${side}-search`),
                results: documentRef.getElementById(`compare-${side}-results`),
                selected: documentRef.getElementById(`compare-${side}-profile`),
            },
        ]));

        function t(key) {
            return typeof locale[key] === "string" && locale[key] ? locale[key] : "";
        }

        function applyLocaleText(nextLocale) {
            documentRef.querySelectorAll("[data-i18n]").forEach((el) => {
                const key = el.getAttribute("data-i18n");
                if (key && nextLocale[key]) el.textContent = nextLocale[key];
            });
            documentRef.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
                const key = el.getAttribute("data-i18n-placeholder");
                if (key && nextLocale[key]) el.placeholder = nextLocale[key];
            });
            documentRef.querySelectorAll("[data-i18n-title]").forEach((el) => {
                const key = el.getAttribute("data-i18n-title");
                if (key && nextLocale[key]) el.title = nextLocale[key];
            });
            documentRef.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
                const key = el.getAttribute("data-i18n-aria-label");
                if (key && nextLocale[key]) el.setAttribute("aria-label", nextLocale[key]);
            });
        }

        function refreshLocaleDependentViews() {
            preferenceLabels = buildPreferenceLabelLookup(preferencesCatalog, locale);
            sideKeys.forEach((side) => {
                renderSelected(side);
                renderResults(side);
            });
            renderCompareTable();
        }

        function applyThemeMode(mode, persist = true) {
            const normalizedMode = ["system", "light", "dark"].includes(mode) ? mode : "system";
            const resolvedTheme = resolveTheme(
                normalizedMode,
                windowRef.matchMedia("(prefers-color-scheme: dark)"),
            );

            documentRef.documentElement.dataset.themeMode = normalizedMode;
            documentRef.documentElement.dataset.theme = resolvedTheme;
            if (themeSelectEl) {
                themeSelectEl.value = normalizedMode;
            }
            updateThemeColorMeta(documentRef, resolvedTheme);
            syncThemeSensitiveControls?.(documentRef, resolvedTheme);

            if (persist) {
                windowRef.localStorage.setItem(themeStorageKey, normalizedMode);
            }
        }

        async function loadLocale(lang, requestId = 0) {
            try {
                let nextLocale = null;
                if (lang === windowRef.__BPM_INITIAL_LANG__ && windowRef.__BPM_INITIAL_LOCALE__) {
                    nextLocale = windowRef.__BPM_INITIAL_LOCALE__;
                } else {
                    const res = await windowRef.fetch(`/i18n/${lang}.json`);
                    if (!res.ok) throw new Error(await res.text());
                    nextLocale = await res.json();
                }
                if (requestId && requestId !== localeRequestId) return;

                locale = nextLocale;
                documentRef.documentElement.lang = lang;
                windowRef.__BPM_INITIAL_LANG__ = lang;
                windowRef.__BPM_INITIAL_LOCALE__ = nextLocale;
                applyLocaleText(nextLocale);
                refreshLocaleDependentViews();
            } catch (error) {
                console.warn("compare i18n load failed:", error);
            }
        }

        async function applyLanguageMode(mode, persist = true) {
            const enabledLanguageModes = langSelectEl
                ? Array.from(langSelectEl.options)
                    .filter((option) => !option.disabled)
                    .map((option) => option.value)
                : ["system", "en", "ru"];
            const normalizedMode = enabledLanguageModes.includes(mode) ? mode : "system";
            const resolvedLanguage = normalizedMode === "system"
                ? resolveBrowserLanguage(windowRef.navigator, enabledLanguageModes)
                : normalizedMode;
            const requestId = ++localeRequestId;

            documentRef.documentElement.dataset.langMode = normalizedMode;
            if (langSelectEl) {
                langSelectEl.value = normalizedMode;
            }

            if (persist) {
                windowRef.localStorage.setItem(langStorageKey, normalizedMode);
            }

            await loadLocale(resolvedLanguage, requestId);
        }

        function renderCompareTable() {
            if (!tableRowsEl) return;
            const leftProfile = state.left.selected;
            const rightProfile = state.right.selected;
            tableRowsEl.innerHTML = "";

            if (!leftProfile || !rightProfile) {
                const row = documentRef.createElement("tr");
                row.innerHTML = `
                    <td class="px-3 py-3 text-slate-500" colspan="3" data-i18n="profiles.compare_table_empty">
                        ${escapeHtml(t("profiles.compare_table_empty") || "Choose Profile A and Profile B to compare their settings.")}
                    </td>
                `;
                tableRowsEl.appendChild(row);
                return;
            }

            const rows = buildCompareRows(leftProfile, rightProfile, compareState, {
                missingLabel: t("profiles.compare_state_missing") || "Missing",
                policyKindLabel: t("profiles.compare_kind_policy") || "Policy",
                preferenceKindLabel: t("profiles.compare_kind_preference") || "Managed preference",
                preferenceLabels,
                stateLabels: {
                    missing: t("profiles.compare_state_missing") || "Missing",
                    equal: t("profiles.compare_state_equal") || "Same value",
                    different: t("profiles.compare_state_different") || "Different value",
                },
            });
            if (!rows.length) {
                const row = documentRef.createElement("tr");
                row.innerHTML = `
                    <td class="px-3 py-3 text-slate-500" colspan="3">
                        ${escapeHtml(t("profiles.compare_table_no_settings") || "Neither profile has settings to compare.")}
                    </td>
                `;
                tableRowsEl.appendChild(row);
                return;
            }

            rows.forEach((compareRow) => {
                const row = documentRef.createElement("tr");
                const settingColumnLabel = t("profiles.compare_setting_column") || "Setting";
                const leftColumnLabel = t("profiles.compare_left_column") || "Profile A value";
                const rightColumnLabel = t("profiles.compare_right_column") || "Profile B value";
                row.dataset.compareRowId = compareRow.id;
                row.dataset.compareRowKind = compareRow.kind;
                row.dataset.compareRowChanged = compareRow.changed ? "true" : "false";
                row.innerHTML = `
                    <th scope="row" class="compare-setting-cell px-3 py-3 align-top" data-label="${escapeHtml(settingColumnLabel)}">
                        ${renderSettingIdentity(compareRow)}
                    </th>
                    <td class="compare-value-cell compare-value-cell--${compareRow.left.state} px-3 py-3 align-top" data-label="${escapeHtml(leftColumnLabel)}" data-compare-column="left" data-compare-value-state="${compareRow.left.state}">
                        <span class="compare-value-state" data-compare-value-state-label="${compareRow.left.state}">
                            ${escapeHtml(compareRow.left.stateLabel)}
                        </span>
                        <code class="compare-value-code">${escapeHtml(compareRow.left.displayValue)}</code>
                    </td>
                    <td class="compare-value-cell compare-value-cell--${compareRow.right.state} px-3 py-3 align-top" data-label="${escapeHtml(rightColumnLabel)}" data-compare-column="right" data-compare-value-state="${compareRow.right.state}">
                        <span class="compare-value-state" data-compare-value-state-label="${compareRow.right.state}">
                            ${escapeHtml(compareRow.right.stateLabel)}
                        </span>
                        <code class="compare-value-code">${escapeHtml(compareRow.right.displayValue)}</code>
                    </td>
                `;
                tableRowsEl.appendChild(row);
            });
        }

        function renderSelected(side) {
            const selectedEl = elements[side]?.selected;
            if (!selectedEl) return;
            const selected = getSideState(state, side).selected;
            if (!selected) {
                selectedEl.classList.remove("compare-selected-profile--active");
                selectedEl.innerHTML = `
                    <span class="compare-selected-profile__empty" data-i18n="profiles.compare_profile_empty">
                        ${escapeHtml(t("profiles.compare_profile_empty") || "No profile selected")}
                    </span>
                `;
                return;
            }
            const schema = formatProfileSchema(selected, utils.formatSchemaLabel);
            const updated = formatProfileUpdatedAt(selected);
            selectedEl.classList.add("compare-selected-profile--active");
            selectedEl.innerHTML = `
                <span class="compare-selected-profile__name">${escapeHtml(selected.name || t("profiles.none_selected") || "None selected")}</span>
                <span class="compare-selected-profile__meta">
                    ${schema ? `<span>${escapeHtml(schema)}</span>` : ""}
                    ${updated ? `<span>${escapeHtml(updated)}</span>` : ""}
                </span>
            `;
        }

        function renderProfileOption(profile, sideState, side) {
            const selected = sideState.selected?.id === profile.id;
            const button = documentRef.createElement("button");
            const schema = formatProfileSchema(profile, utils.formatSchemaLabel);
            const updated = formatProfileUpdatedAt(profile);
            button.type = "button";
            button.className = "compare-profile-option button-base soft-input mt-2 w-full text-left";
            button.dataset.compareResultSide = side;
            button.dataset.compareProfileId = String(profile.id);
            button.setAttribute("data-compare-profile-option", "true");
            button.setAttribute("role", "option");
            button.setAttribute("aria-selected", selected ? "true" : "false");

            const nameEl = documentRef.createElement("span");
            nameEl.className = "compare-profile-option__name";
            nameEl.setAttribute("data-compare-profile-name", "");
            nameEl.textContent = profile.name || t("profiles.none_selected") || "None selected";

            const metaEl = documentRef.createElement("span");
            metaEl.className = "compare-profile-option__meta";
            if (schema) {
                const schemaEl = documentRef.createElement("span");
                schemaEl.className = "compare-profile-option__schema";
                schemaEl.setAttribute("data-compare-profile-schema", "");
                schemaEl.textContent = schema;
                metaEl.append(schemaEl);
            }
            if (updated) {
                const updatedEl = documentRef.createElement("span");
                updatedEl.className = "compare-profile-option__updated";
                updatedEl.setAttribute("data-compare-profile-updated", "");
                updatedEl.textContent = updated;
                metaEl.append(updatedEl);
            }

            button.append(nameEl, metaEl);
            return button;
        }

        function renderResults(side) {
            const resultsEl = elements[side]?.results;
            if (!resultsEl) return;
            const sideState = getSideState(state, side);
            resultsEl.innerHTML = "";
            resultsEl.dataset.compareResultsCount = String(sideState.items.length);
            resultsEl.classList.toggle("compare-profile-results--overflow", sideState.items.length > compareProfileResultsLimit);

            if (sideState.loading) {
                resultsEl.innerHTML = `
                    <div class="text-sm text-slate-500" data-compare-results-state="loading">
                        ${escapeHtml(t("profiles.compare_search_loading") || "Loading profiles...")}
                    </div>
                `;
                return;
            }

            if (sideState.error) {
                resultsEl.innerHTML = `
                    <div class="text-sm text-red-700" role="alert" data-compare-results-state="error">
                        ${escapeHtml(sideState.error)}
                    </div>
                `;
                return;
            }

            if (!sideState.items.length) {
                resultsEl.innerHTML = `
                    <div class="text-sm text-slate-500" data-compare-results-state="empty">
                        ${escapeHtml(t("profiles.compare_search_empty") || "No active profiles found.")}
                    </div>
                `;
                return;
            }

            sideState.items.slice(0, compareProfileResultsLimit).forEach((profile) => {
                const button = renderProfileOption(profile, sideState, side);
                button.classList.add("compare-profile-option");
                resultsEl.appendChild(button);
            });
        }

        function renderSide(side) {
            renderSelected(side);
            renderResults(side);
            renderCompareTable();
        }

        async function loadProfilesForSide(side) {
            const sideState = getSideState(state, side);
            const requestId = sideState.requestId + 1;
            sideState.requestId = requestId;
            sideState.query = elements[side]?.search?.value || "";
            sideState.loading = true;
            sideState.error = "";
            renderSide(side);

            try {
                const items = await data.listProfiles(
                    buildProfileSearchFilters(sideState.query),
                    windowRef.fetch,
                    windowRef.location,
                    documentRef,
                );
                if (sideState.requestId !== requestId) return;
                sideState.items = Array.isArray(items) ? items : [];
            } catch (error) {
                if (sideState.requestId !== requestId) return;
                sideState.items = [];
                sideState.error = error?.message || String(error);
            } finally {
                if (sideState.requestId === requestId) {
                    sideState.loading = false;
                    renderSide(side);
                }
            }
        }

        async function selectProfileForSide(side, profileId, options = {}) {
            if (!profileId) return;
            const sideState = getSideState(state, side);
            sideState.error = "";
            try {
                const profile = await data.getProfile(profileId, windowRef.fetch, false);
                sideState.selected = profile;
                renderSide(side);
            } catch (error) {
                sideState.selected = null;
                if (!options.silent) {
                    sideState.error = error?.message || String(error);
                }
                renderSide(side);
            }
        }

        async function preselectProfileForSide(side, profileId) {
            await selectProfileForSide(side, profileId, { silent: true });
        }

        function scheduleLoad(side) {
            windowRef.clearTimeout(searchTimers.get(side));
            searchTimers.set(side, windowRef.setTimeout(() => {
                loadProfilesForSide(side);
            }, 180));
        }

        async function initializePreferences() {
            const savedLangMode = windowRef.localStorage.getItem(langStorageKey) || "system";
            const savedThemeMode = windowRef.localStorage.getItem(themeStorageKey) || "system";
            if (langSelectEl) {
                langSelectEl.value = savedLangMode;
            }
            if (themeSelectEl) {
                themeSelectEl.value = savedThemeMode;
            }
            applyThemeMode(savedThemeMode, false);
            await applyLanguageMode(savedLangMode, false);
        }

        langSelectEl?.addEventListener("change", async (event) => {
            await applyLanguageMode(event.target.value);
        });
        themeSelectEl?.addEventListener("change", (event) => {
            applyThemeMode(event.target.value);
        });

        sideKeys.forEach((side) => {
            elements[side]?.search?.addEventListener("input", () => scheduleLoad(side));
            elements[side]?.results?.addEventListener("click", (event) => {
                const button = event.target?.closest?.("[data-compare-profile-id]");
                if (!button) return;
                const profileId = Number(button.dataset.compareProfileId || 0);
                selectProfileForSide(side, profileId);
            });
            loadProfilesForSide(side);
        });

        sideKeys.forEach((side) => {
            preselectProfileForSide(side, preselectedIds[side]);
        });

        initializePreferences().catch((error) => {
            console.warn("compare preferences bootstrap failed:", error);
        });

        return {
            applyLanguageMode,
            applyThemeMode,
            loadProfilesForSide,
            loadLocale,
            preselectProfileForSide,
            refreshLocaleDependentViews,
            renderCompareTable,
            renderSide,
            selectProfileForSide,
            state,
        };
    }

    window.BPMProfilesCompare = {
        buildProfileSearchFilters,
        buildCompareRows,
        buildPreferenceLabelLookup,
        createInitialState,
        escapeHtml,
        formatProfileSummary,
        formatProfileSchema,
        formatProfileUpdatedAt,
        ready: true,
        readEmbeddedJson,
        resolvePreselectedProfileIds,
        resolveSettingPresentation,
        renderSettingIdentity,
        resolveValueStateLabel,
        start,
    };

    if (window.document) {
        start({ documentRef: window.document, windowRef: window });
    }
})();
