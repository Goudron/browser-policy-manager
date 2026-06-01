(() => {
    function start({
        documentRef = document,
        windowRef = window,
    } = {}) {
        const utils = windowRef.BPMProfilesUtils;
        const platform = windowRef.BPMProfilesPlatform;
        const data = windowRef.BPMProfilesData;
        const shared = windowRef.BPMProfilesShared.create({
            documentRef,
            elements: {
                statusEl: documentRef.getElementById("status"),
                workspaceHelperTitleEl: documentRef.getElementById("workspace-helper-title"),
                workspaceHelperCopyEl: documentRef.getElementById("workspace-helper-copy"),
                wizardSchemaEl: null,
            },
            dependencies: {
                fromEditorValue: data.fromEditorValue,
                formatBooleanSelectValue: utils.formatBooleanSelectValue,
                parseBooleanSelectValue: utils.parseBooleanSelectValue,
                getDefaultSchemaVersion: utils.getDefaultSchemaVersion,
            },
        });

        const {
            resolveTheme,
            resolveBrowserLanguage,
            updateThemeColorMeta,
            syncThemeSensitiveControls,
            libraryCountLabel,
        } = platform;
        const {
            formatSchemaLabel,
            getDefaultSchemaVersion,
            escapeHtml,
        } = utils;
        const {
            listProfiles,
            getProfileLibraryStats,
            getProfile,
            importFirefoxPoliciesJson,
            softDeleteProfile,
            restoreProfile,
        } = data;
        const {
            t,
            setStatus,
            getCurrentLang,
            setCurrentLang,
            setLocaleDict,
            getSearchTimer,
            setSearchTimer,
        } = shared;

        const langStorageKey = "bpm-lang-mode";
        const themeStorageKey = "bpm-theme-mode";
        let localeRequestId = 0;
        let compareFirstProfileState = null;
        let compareSecondProfileState = null;

        const listEl = documentRef.getElementById("list");
        const listSummaryEl = documentRef.getElementById("list-summary");
        const listTotalSummaryEl = documentRef.getElementById("list-total-summary");
        const refreshButtonEl = documentRef.getElementById("refresh");
        const searchInputEl = documentRef.getElementById("search");
        const schemaFilterEl = documentRef.getElementById("library-schema-filter");
        const lifecycleFilterEl = documentRef.getElementById("library-lifecycle-filter");
        const validationFilterEl = documentRef.getElementById("library-validation-filter");
        const sortSelectEl = documentRef.getElementById("sort");
        const orderSelectEl = documentRef.getElementById("order");
        const includeDeletedEl = documentRef.getElementById("include-deleted");
        const importFirefoxPoliciesButtonEl = documentRef.getElementById("import-firefox-policies");
        const importFirefoxPoliciesFileEl = documentRef.getElementById("import-firefox-policies-file");
        const importFirefoxPoliciesStatusEl = documentRef.getElementById("import-firefox-policies-status");
        const workspaceProfileCountEl = documentRef.getElementById("workspace-profile-count");
        const workspaceProfileLabelEl = documentRef.getElementById("workspace-profile-label");
        const langSelectEl = documentRef.getElementById("lang");
        const themeSelectEl = documentRef.getElementById("theme");
        const compareClearEl = documentRef.getElementById("compare-clear");
        const compareEmptyEl = documentRef.getElementById("compare-empty");
        const compareEmptyCopyEl = documentRef.getElementById("compare-empty-copy");
        const compareActiveEl = documentRef.getElementById("compare-active");
        const compareCurrentNameEl = documentRef.getElementById("compare-current-name");
        const compareCurrentCopyEl = documentRef.getElementById("compare-current-copy");
        const compareOtherNameEl = documentRef.getElementById("compare-other-name");
        const compareOtherCopyEl = documentRef.getElementById("compare-other-copy");
        const compareMetadataCountEl = documentRef.getElementById("compare-metadata-count");
        const comparePolicyCountEl = documentRef.getElementById("compare-policy-count");
        const comparePreferenceCountEl = documentRef.getElementById("compare-preference-count");
        const compareChangesCopyEl = documentRef.getElementById("compare-changes-copy");
        const compareChangesListEl = documentRef.getElementById("compare-changes-list");
        const compareGuidedAreasCopyEl = documentRef.getElementById("compare-guided-areas-copy");
        const compareGuidedAreasListEl = documentRef.getElementById("compare-guided-areas-list");

        function readFilters() {
            return {
                q: searchInputEl?.value.trim() || "",
                schemaVersion: schemaFilterEl?.value || "",
                lifecycle: lifecycleFilterEl?.value || "active",
                validationState: validationFilterEl?.value || "",
                includeDeleted: includeDeletedEl?.checked || false,
                sort: sortSelectEl?.value || "updated_at",
                order: orderSelectEl?.value || "desc",
            };
        }

        function setImportStatus(message, tone = "info") {
            if (!importFirefoxPoliciesStatusEl) return;
            importFirefoxPoliciesStatusEl.textContent = message;
            importFirefoxPoliciesStatusEl.dataset.statusTone = tone;
        }

        function setImportBusy(isBusy) {
            if (importFirefoxPoliciesButtonEl) {
                importFirefoxPoliciesButtonEl.disabled = isBusy;
                importFirefoxPoliciesButtonEl.setAttribute("aria-busy", isBusy ? "true" : "false");
            }
            if (importFirefoxPoliciesStatusEl) {
                importFirefoxPoliciesStatusEl.setAttribute("aria-busy", isBusy ? "true" : "false");
            }
        }

        function inferImportProfileName(file) {
            const rawName = file?.name || "policies.json";
            const withoutExtension = rawName.replace(/\.json$/i, "").trim();
            if (!withoutExtension || withoutExtension.toLowerCase() === "policies") {
                return t("profiles.import_firefox_policies_default_name");
            }
            return withoutExtension;
        }

        function formatValidationStateLabel(profile) {
            if (profile?.validation_state === "invalid") {
                return t("profiles.library_validation_invalid");
            }
            if (profile?.validation_state === "not_validated") {
                return t("profiles.library_validation_not_validated");
            }
            return t("profiles.library_validation_valid");
        }

        function formatValidationStateClass(profile) {
            if (profile?.validation_state === "invalid") {
                return "profile-list-status--invalid";
            }
            if (profile?.validation_state === "not_validated") {
                return "profile-list-status--not-validated";
            }
            return "profile-list-status--valid";
        }

        function formatTimestamp(value) {
            if (!value) return "—";
            try {
                return new Intl.DateTimeFormat(getCurrentLang(), {
                    dateStyle: "medium",
                    timeStyle: "short",
                }).format(new Date(value));
            } catch {
                return value;
            }
        }

        function buildProfileSnapshot(profile) {
            return {
                id: profile?.id ?? null,
                name: profile?.name || "",
                owner: profile?.owner || null,
                description: profile?.description || null,
                schemaVersion: profile?.schema_version || getDefaultSchemaVersion(documentRef),
                flags: profile?.flags && typeof profile.flags === "object" ? profile.flags : {},
            };
        }

        function normalizeValue(value) {
            if (Array.isArray(value)) {
                return value.map((item) => normalizeValue(item));
            }
            if (value && typeof value === "object") {
                return Object.keys(value).sort().reduce((acc, key) => {
                    acc[key] = normalizeValue(value[key]);
                    return acc;
                }, {});
            }
            return value;
        }

        function snapshotToString(value) {
            return JSON.stringify(normalizeValue(value));
        }

        function isPlainObject(value) {
            return Boolean(value) && typeof value === "object" && !Array.isArray(value);
        }

        function collectDiffPaths(baseValue, otherValue, path = [], changes = []) {
            const normalizedBase = normalizeValue(baseValue);
            const normalizedOther = normalizeValue(otherValue);

            if (isPlainObject(normalizedBase) || isPlainObject(normalizedOther)) {
                const baseObject = isPlainObject(normalizedBase) ? normalizedBase : {};
                const otherObject = isPlainObject(normalizedOther) ? normalizedOther : {};
                const keys = Array.from(new Set([
                    ...Object.keys(baseObject),
                    ...Object.keys(otherObject),
                ])).sort();
                keys.forEach((key) => {
                    collectDiffPaths(baseObject[key], otherObject[key], [...path, key], changes);
                });
                return changes;
            }

            if (snapshotToString(normalizedBase) !== snapshotToString(normalizedOther)) {
                changes.push(path);
            }
            return changes;
        }

        function buildCompareDiff(baseSnapshot, otherSnapshot) {
            const metadataFields = [
                ["name", t("profiles.compare_metadata_name")],
                ["owner", t("profiles.compare_metadata_owner")],
                ["description", t("profiles.compare_metadata_description")],
                ["schemaVersion", t("profiles.compare_metadata_schema")],
            ];
            const metadataChanges = metadataFields
                .filter(([key]) => snapshotToString(baseSnapshot?.[key]) !== snapshotToString(otherSnapshot?.[key]))
                .map(([, label]) => label);
            const changedPaths = collectDiffPaths(baseSnapshot?.flags || {}, otherSnapshot?.flags || {});
            const policyEntries = new Map();
            const preferenceEntries = new Map();

            changedPaths.forEach((path) => {
                if (!Array.isArray(path) || !path.length) return;
                if (path[0] === "Preferences" && path[1]) {
                    if (!preferenceEntries.has(path[1])) {
                        preferenceEntries.set(path[1], path);
                    }
                    return;
                }
                if (!policyEntries.has(path[0])) {
                    policyEntries.set(path[0], path);
                }
            });

            const sampleChanges = [
                ...metadataChanges.slice(0, 2).map((label) => ({
                    title: label,
                    copy: t("profiles.compare_change_metadata_copy"),
                })),
                ...Array.from(policyEntries.entries()).slice(0, 2).map(([key, path]) => ({
                    title: key,
                    copy: path.length > 1
                        ? t("profiles.compare_change_policy_nested")
                        : t("profiles.compare_change_policy_direct"),
                })),
                ...Array.from(preferenceEntries.entries()).slice(0, 2).map(([key]) => ({
                    title: key,
                    copy: t("profiles.compare_change_preference_copy"),
                })),
            ].slice(0, 6);

            return {
                metadataChanges,
                policyEntries,
                preferenceEntries,
                sampleChanges,
            };
        }

        function resolveCompareAreaForPolicy(key) {
            const policyKey = String(key || "");
            if ([
                "Proxy",
                "Certificates",
                "DNSOverHTTPS",
                "WindowsSSO",
                "Authentication",
                "AppAutoUpdate",
                "DisableAppUpdate",
                "DisableSystemAddonUpdate",
                "DontCheckDefaultBrowser",
                "PromptForDownloadLocation",
                "Homepage",
                "NewTabPage",
                "OverrideFirstRunPage",
                "OverridePostUpdatePage",
                "FirefoxHome",
                "DisablePocket",
                "Preferences",
                "SearchBar",
                "SearchSuggestEnabled",
                "SearchEngines",
            ].includes(policyKey)) return "step_two";
            if ([
                "DisableTelemetry",
                "BlockAboutAddons",
                "EnableTrackingProtection",
                "Cookies",
                "Permissions",
                "SanitizeOnShutdown",
                "OfferToSaveLogins",
                "PasswordManagerEnabled",
            ].includes(policyKey)) return "step_three";
            if ([
                "WebsiteFilter",
                "WebsiteFilterExceptions",
                "Handlers",
                "AutoLaunchProtocolsFromOrigins",
                "GoToIntranetSiteForSingleWordEntryInAddressBar",
                "NoDefaultBookmarks",
            ].includes(policyKey)) return "step_four";
            if ([
                "DisableFirefoxAccounts",
                "ExtensionSettings",
                "ExtensionUpdate",
                "InstallAddonsPermission",
                "Bookmarks",
                "ManagedBookmarks",
                "UserMessaging",
                "RequestedLocales",
                "TranslateEnabled",
            ].includes(policyKey)) return "step_four";
            if ([
                "DisableBuiltinAIChat",
                "DisableFirefoxLabs",
                "AIControls",
                "GenerativeAI",
                "VisualSearchEnabled",
            ].includes(policyKey)) return "step_five";
            return "step_one";
        }

        function resolveCompareAreaForPreference(key) {
            const prefKey = String(key || "");
            if (/proxy|network|dns|update|download|browser|homepage|newtab|firefox-home|snippets|topsites|search|suggest|urlbar/i.test(prefKey)) return "step_two";
            if (/cookie|tracking|permission|telemetry|privacy|safe-browsing|password|https|sanitize|private/i.test(prefKey)) return "step_three";
            if (/locale|language|translate|extension|account|bookmark|handler|website|intranet/i.test(prefKey)) return "step_four";
            if (/ai|visualsearch|chatbot|model|provider/i.test(prefKey)) return "step_five";
            return "step_two";
        }

        function buildCompareAreaGroups(diff) {
            const areaMap = new Map();
            const addToArea = (areaKey, label) => {
                if (!areaMap.has(areaKey)) areaMap.set(areaKey, []);
                areaMap.get(areaKey).push(label);
            };

            diff.metadataChanges.forEach((label) => addToArea("step_one", label));
            Array.from(diff.policyEntries.keys()).forEach((key) => addToArea(resolveCompareAreaForPolicy(key), key));
            Array.from(diff.preferenceEntries.keys()).forEach((key) => addToArea(resolveCompareAreaForPreference(key), key));

            return [
                "step_one",
                "step_two",
                "step_three",
                "step_four",
                "step_five",
            ].map((areaKey) => {
                const items = areaMap.get(areaKey) || [];
                if (!items.length) return null;
                return {
                    title: t(`profiles.compare_guided_area_${areaKey}`),
                    items,
                };
            }).filter(Boolean);
        }

        function buildCompareState(profile) {
            if (!profile?.id) return null;
            return {
                profile,
                snapshot: buildProfileSnapshot(profile),
            };
        }

        function renderComparePanel() {
            if (
                !compareEmptyEl
                || !compareActiveEl
                || !compareEmptyCopyEl
                || !compareClearEl
                || !compareCurrentNameEl
                || !compareCurrentCopyEl
                || !compareOtherNameEl
                || !compareOtherCopyEl
                || !compareMetadataCountEl
                || !comparePolicyCountEl
                || !comparePreferenceCountEl
                || !compareChangesCopyEl
                || !compareChangesListEl
                || !compareGuidedAreasCopyEl
                || !compareGuidedAreasListEl
            ) return;

            if (!compareFirstProfileState) {
                compareEmptyEl.hidden = false;
                compareActiveEl.hidden = true;
                compareClearEl.hidden = true;
                compareEmptyCopyEl.textContent = t("profiles.library_compare_empty_pick_first");
                return;
            }

            if (!compareSecondProfileState) {
                compareEmptyEl.hidden = false;
                compareActiveEl.hidden = true;
                compareClearEl.hidden = false;
                compareEmptyCopyEl.textContent = t("profiles.library_compare_empty_pick_second").replace(
                    "{name}",
                    compareFirstProfileState.profile.name || t("profiles.none_selected"),
                );
                return;
            }

            const firstSnapshot = compareFirstProfileState.snapshot;
            const secondSnapshot = compareSecondProfileState.snapshot;
            const diff = buildCompareDiff(firstSnapshot, secondSnapshot);
            compareEmptyEl.hidden = true;
            compareActiveEl.hidden = false;
            compareClearEl.hidden = false;
            compareCurrentNameEl.textContent = compareFirstProfileState.profile.name || t("profiles.none_selected");
            compareCurrentCopyEl.textContent = t("profiles.library_compare_saved_copy")
                .replace("{schema}", formatSchemaLabel(firstSnapshot.schemaVersion));
            compareOtherNameEl.textContent = compareSecondProfileState.profile.name || t("profiles.none_selected");
            compareOtherCopyEl.textContent = t("profiles.library_compare_saved_copy").replace(
                "{schema}",
                formatSchemaLabel(secondSnapshot.schemaVersion),
            );
            compareMetadataCountEl.textContent = `${diff.metadataChanges.length}`;
            comparePolicyCountEl.textContent = `${diff.policyEntries.size}`;
            comparePreferenceCountEl.textContent = `${diff.preferenceEntries.size}`;
            compareChangesCopyEl.textContent = diff.sampleChanges.length
                ? t("profiles.library_compare_changes_active")
                : t("profiles.compare_changes_none");
            compareChangesListEl.innerHTML = "";
            compareGuidedAreasCopyEl.textContent = diff.sampleChanges.length
                ? t("profiles.compare_guided_areas_active")
                : t("profiles.compare_guided_areas_none");
            compareGuidedAreasListEl.innerHTML = "";

            if (!diff.sampleChanges.length) {
                const item = documentRef.createElement("li");
                item.className = "compare-changes-item";
                item.setAttribute("role", "listitem");
                item.textContent = t("profiles.compare_no_diff");
                compareChangesListEl.appendChild(item);

                const groupedItem = documentRef.createElement("li");
                groupedItem.className = "compare-changes-item";
                groupedItem.setAttribute("role", "listitem");
                groupedItem.textContent = t("profiles.compare_no_diff");
                compareGuidedAreasListEl.appendChild(groupedItem);
                return;
            }

            diff.sampleChanges.forEach((change) => {
                const item = documentRef.createElement("li");
                item.className = "compare-changes-item";
                item.setAttribute("role", "listitem");
                item.innerHTML = `
                    <span class="compare-change-title">${change.title}</span>
                    <span class="compare-change-copy">${change.copy}</span>
                `;
                compareChangesListEl.appendChild(item);
            });

            buildCompareAreaGroups(diff).forEach((group) => {
                const item = documentRef.createElement("li");
                item.className = "compare-changes-item";
                item.setAttribute("role", "listitem");
                const preview = group.items.slice(0, 3).join(", ");
                const remaining = group.items.length - Math.min(group.items.length, 3);
                const copy = remaining > 0
                    ? t("profiles.compare_guided_area_more").replace("{items}", preview).replace("{remaining}", String(remaining))
                    : t("profiles.compare_guided_area_preview").replace("{items}", preview);
                item.innerHTML = `
                    <span class="compare-change-title">${group.title} (${group.items.length})</span>
                    <span class="compare-change-copy">${copy}</span>
                `;
                compareGuidedAreasListEl.appendChild(item);
            });
        }

        function clearCompareProfile(notify = true) {
            compareFirstProfileState = null;
            compareSecondProfileState = null;
            renderComparePanel();
            renderList(Array.isArray(windowRef.__BPM_LIBRARY_ITEMS__) ? windowRef.__BPM_LIBRARY_ITEMS__ : []);
            if (notify) {
                setStatus(t("profiles.status_compare_cleared"), "info");
            }
        }

        async function selectProfileForComparison(id) {
            try {
                const profile = await getProfile(id);
                const nextState = buildCompareState(profile);
                if (!nextState) return;

                if (!compareFirstProfileState) {
                    compareFirstProfileState = nextState;
                    compareSecondProfileState = null;
                    setStatus(
                        t("profiles.library_status_compare_first_selected").replace("{name}", profile.name),
                        "info",
                    );
                } else if (compareFirstProfileState.profile.id === profile.id) {
                    compareFirstProfileState = nextState;
                    setStatus(
                        t("profiles.library_status_compare_first_selected").replace("{name}", profile.name),
                        "info",
                    );
                } else {
                    compareSecondProfileState = nextState;
                    setStatus(
                        t("profiles.library_status_compare_ready")
                            .replace("{first}", compareFirstProfileState.profile.name)
                            .replace("{second}", profile.name),
                        "info",
                    );
                }
                renderComparePanel();
                renderList(Array.isArray(windowRef.__BPM_LIBRARY_ITEMS__) ? windowRef.__BPM_LIBRARY_ITEMS__ : []);
                if (compareSecondProfileState) {
                    documentRef.getElementById("compare-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
                }
            } catch (error) {
                setStatus(t("profiles.error_compare").replace("{detail}", error?.message || String(error)), "error");
            }
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

                setLocaleDict(nextLocale);
                setCurrentLang(lang);
                documentRef.documentElement.lang = lang;
                windowRef.__BPM_INITIAL_LANG__ = lang;
                windowRef.__BPM_INITIAL_LOCALE__ = nextLocale;
                applyLocaleText(nextLocale);
            } catch (error) {
                console.warn("library i18n load failed:", error);
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
            await reloadList();
            renderComparePanel();
        }

        function updateLibrarySummary(stats) {
            const filtered = Number(stats?.filtered ?? 0);
            const total = Number(stats?.total ?? filtered);

            if (listSummaryEl) {
                listSummaryEl.textContent = String(filtered);
            }
            if (listTotalSummaryEl) {
                listTotalSummaryEl.textContent = String(total);
            }
            if (workspaceProfileCountEl) {
                workspaceProfileCountEl.textContent = String(total);
            }
            if (workspaceProfileLabelEl) {
                workspaceProfileLabelEl.textContent = libraryCountLabel(total, getCurrentLang(), t);
            }
            workspaceProfileCountEl?.closest(".compact-counter")?.classList.remove("compact-counter--pending");
        }

        function renderList(items) {
            if (!listEl) return;
            windowRef.__BPM_LIBRARY_ITEMS__ = Array.isArray(items) ? items : [];
            listEl.innerHTML = "";

            if (!items.length) {
                const li = documentRef.createElement("li");
                li.className = "list-empty-illustration rounded-[24px] border border-dashed border-slate-200 px-4 py-6 text-center";
                li.innerHTML = `
                    <div class="list-empty-illustration-icon mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/80 bg-white/80 text-2xl shadow-sm">+</div>
                    <div class="text-sm font-semibold text-slate-900">${t("profiles.empty_title")}</div>
                    <div class="mx-auto mt-2 max-w-[240px] text-sm leading-6 text-slate-500">${t("profiles.empty_list")}</div>
                `;
                listEl.appendChild(li);
                return;
            }

            items.forEach((profile) => {
                const li = documentRef.createElement("li");
                li.className = "library-table-row";
                const firstSelected = compareFirstProfileState?.profile?.id === profile.id;
                const secondSelected = compareSecondProfileState?.profile?.id === profile.id;
                const selected = firstSelected || secondSelected;
                const openLabel = t("profiles.list_open");
                const compareLabel = firstSelected
                    ? t("profiles.library_compare_first_selected")
                    : secondSelected
                        ? t("profiles.library_compare_second_selected")
                        : !compareFirstProfileState
                            ? t("profiles.library_compare_select_first")
                            : compareSecondProfileState
                                ? t("profiles.library_compare_use_as_second")
                                : t("profiles.library_compare_select_second");
                const statusLabel = profile.is_deleted
                    ? t("profiles.badge_deleted")
                    : t("profiles.badge_active");
                const validationLabel = formatValidationStateLabel(profile);
                const profileOwner = profile.owner || t("profiles.library_owner_unassigned");
                const profileDescription = profile.description || t("profiles.library_description_empty");
                const editHref = `/profiles/${profile.id}/edit`;
                const settingsHref = `/profiles/${profile.id}/settings${profile.is_deleted ? "?include_deleted=true" : ""}`;
                const jsonHref = `/profiles/${profile.id}/json${profile.is_deleted ? "?include_deleted=true" : ""}`;
                const duplicateHref = `/profiles/new?clone_from=${profile.id}${profile.is_deleted ? "&include_deleted=true" : ""}`;
                const exportHref = `/api/export/profiles/${profile.id}/firefox/policies.json?download=1`;

                li.innerHTML = `
                    <div class="library-row-grid profile-list-button ${selected ? "profile-list-button--selected" : ""}">
                        <div class="library-row-primary">
                            <a class="library-row-title-button" href="${editHref}" target="_blank" rel="noopener">
                                ${escapeHtml(profile.name)}
                            </a>
                            <div class="library-row-identity-meta">#${profile.id}</div>
                        </div>

                        <div class="library-row-context" data-label="${escapeHtml(t("profiles.library_column_context"))}">
                            <div class="library-row-context-owner">${escapeHtml(profileOwner)}</div>
                            <div class="library-row-context-note">${escapeHtml(profileDescription)}</div>
                        </div>

                        <div class="library-row-facts">
                            <div class="library-row-meta" data-label="${escapeHtml(t("profiles.library_column_schema"))}">
                                <div class="library-row-meta-primary">${formatSchemaLabel(profile.schema_version)}</div>
                            </div>

                            <div class="library-row-status-wrap" data-label="${escapeHtml(t("profiles.library_column_status"))}">
                                <span class="profile-list-status ${profile.is_deleted
                                    ? "profile-list-status--deleted"
                                    : "profile-list-status--active"}">
                                    ${statusLabel}
                                </span>
                                <span class="profile-list-status ${formatValidationStateClass(profile)}">
                                    ${validationLabel}
                                </span>
                            </div>

                            <div class="library-row-updated" data-label="${escapeHtml(t("profiles.library_column_updated"))}">
                                <div class="library-row-meta-secondary">${formatTimestamp(profile.updated_at)}</div>
                            </div>
                        </div>

                        <div class="library-row-actions">
                            <a class="button-base library-row-open-button ${selected ? "library-row-open-button--selected" : ""}" href="${editHref}" target="_blank" rel="noopener">
                                ${openLabel}
                            </a>
                            <div class="library-row-action-grid">
                                <a class="button-base ghost-button library-row-secondary-action" href="${settingsHref}" target="_blank" rel="noopener">
                                    ${t("profiles.library_action_all_settings")}
                                </a>
                                <a class="button-base ghost-button library-row-secondary-action" href="${jsonHref}" target="_blank" rel="noopener">
                                    ${t("profiles.library_action_json")}
                                </a>
                                <a class="button-base ghost-button library-row-secondary-action" href="${duplicateHref}" target="_blank" rel="noopener">
                                    ${t("profiles.library_action_duplicate")}
                                </a>
                                ${profile.is_deleted ? `
                                    <span
                                        class="button-base ghost-button library-row-secondary-action library-row-secondary-action--disabled"
                                        aria-disabled="true"
                                        title="${escapeHtml(t("profiles.library_export_unavailable_archived"))}">
                                        ${t("profiles.library_action_export")}
                                    </span>
                                ` : `
                                    <a class="button-base ghost-button library-row-secondary-action" href="${exportHref}" download>
                                        ${t("profiles.library_action_export")}
                                    </a>
                                `}
                                <button
                                    type="button"
                                    class="button-base ghost-button library-row-secondary-action"
                                    data-library-lifecycle-action="${profile.is_deleted ? "restore" : "archive"}"
                                    data-library-profile-id="${profile.id}">
                                    ${profile.is_deleted ? t("profiles.restore") : t("profiles.soft_delete")}
                                </button>
                                <button
                                    type="button"
                                    class="button-base ghost-button library-row-secondary-action profile-compare-button ${selected ? "profile-compare-button--active" : ""}"
                                    data-compare-profile-id="${profile.id}">
                                    ${compareLabel}
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                const compareButton = li.querySelector("[data-compare-profile-id]");
                compareButton?.addEventListener("click", async () => {
                    await selectProfileForComparison(profile.id);
                });
                const lifecycleButton = li.querySelector("[data-library-lifecycle-action]");
                lifecycleButton?.addEventListener("click", async () => {
                    await runLibraryLifecycleAction(profile, lifecycleButton.dataset.libraryLifecycleAction);
                });
                listEl.appendChild(li);
            });
        }

        async function runLibraryLifecycleAction(profile, action) {
            if (!profile?.id) return;
            if (action === "archive") {
                if (!windowRef.confirm(t("profiles.confirm_soft_delete"))) return;
                try {
                    await softDeleteProfile(profile.id, windowRef.fetch);
                    setStatus(t("profiles.library_profile_archived").replace("{name}", profile.name), "success");
                    await reloadList();
                } catch (error) {
                    setStatus(t("profiles.error_delete").replace("{detail}", error.message || error), "error");
                }
                return;
            }
            if (action === "restore") {
                try {
                    const restored = await restoreProfile(profile.id, windowRef.fetch);
                    setStatus(t("profiles.library_profile_restored").replace("{name}", restored.name), "success");
                    await reloadList();
                } catch (error) {
                    setStatus(t("profiles.error_restore").replace("{detail}", error.message || error), "error");
                }
            }
        }

        async function reloadList() {
            try {
                const filters = readFilters();
                const [items, stats] = await Promise.all([
                    listProfiles(filters, windowRef.fetch, windowRef.location, documentRef),
                    getProfileLibraryStats(filters, windowRef.fetch, windowRef.location, documentRef),
                ]);
                renderList(items);
                updateLibrarySummary(stats);
                renderComparePanel();
            } catch (error) {
                console.warn("library list load failed:", error);
            }
        }

        function debounceReload() {
            const searchTimer = getSearchTimer();
            if (searchTimer) {
                windowRef.clearTimeout(searchTimer);
            }
            setSearchTimer(windowRef.setTimeout(() => {
                setSearchTimer(null);
                reloadList();
            }, 220));
        }

        async function doImportFirefoxPoliciesJson(file) {
            if (!file) {
                setImportStatus(t("profiles.import_firefox_policies_ready"));
                return null;
            }

            try {
                setImportBusy(true);
                const profileName = inferImportProfileName(file);
                setImportStatus(
                    t("profiles.import_firefox_policies_reading")
                        .replace("{file}", file.name || "policies.json")
                        .replace("{name}", profileName),
                    "info",
                );
                const rawText = await file.text();
                let documentObj;
                try {
                    documentObj = JSON.parse(rawText);
                } catch (parseError) {
                    throw new Error(
                        t("profiles.error_import_firefox_policies_parse")
                            .replace("{detail}", parseError.message || parseError),
                    );
                }
                const schemaVersion = getDefaultSchemaVersion(documentRef);
                const imported = await importFirefoxPoliciesJson({
                    name: profileName,
                    description: t("profiles.import_firefox_policies_description")
                        .replace("{name}", file.name || "policies.json"),
                    schema_version: schemaVersion,
                    document: documentObj,
                });
                setImportStatus(
                    t("profiles.status_import_firefox_policies_done")
                        .replace("{name}", imported.name)
                        .replace("{schema}", formatSchemaLabel(imported.schema_version))
                        .replace("{validation}", formatValidationStateLabel(imported)),
                    "success",
                );
                setStatus(
                    t("profiles.status_import_firefox_policies_done")
                        .replace("{name}", imported.name)
                        .replace("{schema}", formatSchemaLabel(imported.schema_version))
                        .replace("{validation}", formatValidationStateLabel(imported)),
                    "success",
                );
                await reloadList();
                return imported;
            } catch (error) {
                const message = error?.message || String(error);
                setImportStatus(
                    t("profiles.error_import_firefox_policies").replace("{detail}", message),
                    "error",
                );
                return null;
            } finally {
                if (importFirefoxPoliciesFileEl) {
                    importFirefoxPoliciesFileEl.value = "";
                }
                setImportBusy(false);
            }
        }

        function bindControls() {
            langSelectEl?.addEventListener("change", async (event) => {
                await applyLanguageMode(event.target.value);
            });
            themeSelectEl?.addEventListener("change", (event) => {
                applyThemeMode(event.target.value);
            });
            refreshButtonEl?.addEventListener("click", () => {
                reloadList();
            });
            searchInputEl?.addEventListener("input", debounceReload);
            schemaFilterEl?.addEventListener("change", reloadList);
            lifecycleFilterEl?.addEventListener("change", reloadList);
            validationFilterEl?.addEventListener("change", reloadList);
            sortSelectEl?.addEventListener("change", reloadList);
            orderSelectEl?.addEventListener("change", reloadList);
            includeDeletedEl?.addEventListener("change", reloadList);
            importFirefoxPoliciesButtonEl?.addEventListener("click", () => {
                importFirefoxPoliciesFileEl?.click();
            });
            importFirefoxPoliciesFileEl?.addEventListener("change", async (event) => {
                const file = event.target.files?.[0] || null;
                await doImportFirefoxPoliciesJson(file);
            });
            compareClearEl?.addEventListener("click", () => {
                clearCompareProfile();
            });
        }

        async function initialize() {
            const savedLangMode = windowRef.localStorage.getItem(langStorageKey) || "system";
            const savedThemeMode = windowRef.localStorage.getItem(themeStorageKey) || "system";
            if (langSelectEl) {
                langSelectEl.value = savedLangMode;
            }
            if (themeSelectEl) {
                themeSelectEl.value = savedThemeMode;
            }
            applyThemeMode(savedThemeMode, false);
            setImportStatus(t("profiles.import_firefox_policies_ready"));
            await applyLanguageMode(savedLangMode, false);
            renderComparePanel();
        }

        bindControls();
        initialize().catch((error) => {
            console.warn("library bootstrap failed:", error);
        });
    }

    window.BPMProfilesLibraryBootstrap = {
        start,
    };
})();
