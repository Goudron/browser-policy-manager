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

        function buildDefaultCloneName(profile) {
            const sourceName = profile?.name || t("profiles.clone_source_unknown");
            return t("profiles.clone_name_pattern").replace("{name}", sourceName);
        }

        function buildCloneDraftHref(profile, cloneName) {
            const params = new URLSearchParams();
            params.set("clone_from", String(profile.id));
            params.set("clone_name", cloneName);
            if (profile.is_deleted) {
                params.set("include_deleted", "true");
            }
            return `/profiles/new?${params.toString()}`;
        }

        function profileNameExists(name, sourceProfileId = null) {
            const normalizedName = String(name || "").trim().toLocaleLowerCase();
            if (!normalizedName) return false;
            return (windowRef.__BPM_LIBRARY_ITEMS__ || []).some((profile) => {
                if (sourceProfileId && profile.id === sourceProfileId) return false;
                return String(profile.name || "").trim().toLocaleLowerCase() === normalizedName;
            });
        }

        function updateCloneNameControl(panelEl, profile) {
            const inputEl = panelEl?.querySelector("[data-clone-name-input]");
            const confirmEl = panelEl?.querySelector("[data-clone-name-confirm]");
            const statusEl = panelEl?.querySelector("[data-clone-name-status]");
            if (!inputEl || !confirmEl || !statusEl) return;

            const cloneName = inputEl.value.trim();
            let message = t("profiles.clone_name_ready");
            let isValid = true;
            if (!cloneName) {
                message = t("profiles.clone_name_required");
                isValid = false;
            } else if (profileNameExists(cloneName, profile.id)) {
                message = t("profiles.clone_name_duplicate");
                isValid = false;
            }

            statusEl.textContent = message;
            statusEl.dataset.statusTone = isValid ? "info" : "warn";
            inputEl.setAttribute("aria-invalid", isValid ? "false" : "true");
            confirmEl.href = isValid ? buildCloneDraftHref(profile, cloneName) : "#";
            confirmEl.setAttribute("aria-disabled", isValid ? "false" : "true");
            confirmEl.classList.toggle("pointer-events-none", !isValid);
            confirmEl.classList.toggle("opacity-50", !isValid);
        }

        function closeOtherCloneNamePanels(activePanelEl = null) {
            documentRef.querySelectorAll("[data-clone-name-panel]").forEach((panelEl) => {
                if (panelEl === activePanelEl) return;
                panelEl.hidden = true;
            });
            documentRef.querySelectorAll("[data-clone-profile-id]").forEach((buttonEl) => {
                if (activePanelEl && buttonEl.getAttribute("aria-controls") === activePanelEl.id) return;
                buttonEl.setAttribute("aria-expanded", "false");
            });
        }

        function openCloneNamePanel(panelEl, buttonEl, profile) {
            if (!panelEl) return;
            closeOtherCloneNamePanels(panelEl);
            panelEl.hidden = false;
            buttonEl?.setAttribute("aria-expanded", "true");
            updateCloneNameControl(panelEl, profile);
            const inputEl = panelEl.querySelector("[data-clone-name-input]");
            inputEl?.focus();
            inputEl?.select();
        }

        function closeCloneNamePanel(panelEl, buttonEl) {
            if (!panelEl) return;
            panelEl.hidden = true;
            buttonEl?.setAttribute("aria-expanded", "false");
            buttonEl?.focus();
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
                const openLabel = t("profiles.list_open");
                const statusLabel = profile.is_deleted
                    ? t("profiles.badge_deleted")
                    : t("profiles.badge_active");
                const validationLabel = formatValidationStateLabel(profile);
                const profileDescription = profile.description || t("profiles.library_description_empty");
                const editHref = `/profiles/${profile.id}/edit`;
                const settingsHref = `/profiles/${profile.id}/settings${profile.is_deleted ? "?include_deleted=true" : ""}`;
                const jsonHref = `/profiles/${profile.id}/json${profile.is_deleted ? "?include_deleted=true" : ""}`;
                const exportHref = `/api/export/profiles/${profile.id}/firefox/policies.json?download=1`;
                const clonePanelId = `library-clone-name-panel-${profile.id}`;
                const cloneInputId = `library-clone-name-input-${profile.id}`;
                const cloneStatusId = `library-clone-name-status-${profile.id}`;
                const defaultCloneName = buildDefaultCloneName(profile);

                li.innerHTML = `
                    <div class="library-row-grid profile-list-button">
                        <div class="library-row-primary">
                            <a class="library-row-title-button" href="${editHref}" target="_blank" rel="noopener">
                                ${escapeHtml(profile.name)}
                            </a>
                            <div class="library-row-identity-meta">#${profile.id}</div>
                        </div>

                        <div class="library-row-context" data-label="${escapeHtml(t("profiles.library_column_context"))}">
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
                            <a class="button-base library-row-open-button" href="${editHref}" target="_blank" rel="noopener">
                                ${openLabel}
                            </a>
                            <div class="library-row-action-grid">
                                <a class="button-base ghost-button library-row-secondary-action" href="${settingsHref}" target="_blank" rel="noopener">
                                    ${t("profiles.library_action_all_settings")}
                                </a>
                                <a class="button-base ghost-button library-row-secondary-action" href="${jsonHref}" target="_blank" rel="noopener">
                                    ${t("profiles.library_action_json")}
                                </a>
                                <button
                                    type="button"
                                    class="button-base ghost-button library-row-secondary-action"
                                    data-clone-profile-id="${profile.id}"
                                    aria-controls="${clonePanelId}"
                                    aria-expanded="false">
                                    ${t("profiles.library_action_duplicate")}
                                </button>
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
                            </div>
                            <div
                                id="${clonePanelId}"
                                class="library-clone-name-panel"
                                data-clone-name-panel
                                hidden>
                                <label class="field-label" for="${cloneInputId}">
                                    ${t("profiles.clone_name_label")}
                                </label>
                                <div class="library-clone-name-controls">
                                    <input
                                        id="${cloneInputId}"
                                        type="text"
                                        class="soft-input library-clone-name-input"
                                        value="${escapeHtml(defaultCloneName)}"
                                        aria-describedby="${cloneStatusId}"
                                        data-clone-name-input />
                                    <div class="library-clone-name-actions">
                                        <a
                                            class="button-base primary-button library-clone-name-confirm"
                                            href="${buildCloneDraftHref(profile, defaultCloneName)}"
                                            target="_blank"
                                            rel="noopener"
                                            data-clone-name-confirm>
                                            ${t("profiles.clone_name_confirm")}
                                        </a>
                                        <button
                                            type="button"
                                            class="button-base ghost-button library-clone-name-cancel"
                                            data-clone-name-cancel>
                                            ${t("profiles.clone_name_cancel")}
                                        </button>
                                    </div>
                                </div>
                                <div
                                    id="${cloneStatusId}"
                                    class="library-clone-name-status"
                                    role="status"
                                    aria-live="polite"
                                    data-clone-name-status>
                                    ${t("profiles.clone_name_ready")}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                const lifecycleButton = li.querySelector("[data-library-lifecycle-action]");
                lifecycleButton?.addEventListener("click", async () => {
                    await runLibraryLifecycleAction(profile, lifecycleButton.dataset.libraryLifecycleAction);
                });
                const cloneButton = li.querySelector("[data-clone-profile-id]");
                const clonePanel = li.querySelector("[data-clone-name-panel]");
                cloneButton?.addEventListener("click", () => {
                    if (clonePanel?.hidden === false) {
                        closeCloneNamePanel(clonePanel, cloneButton);
                    } else {
                        openCloneNamePanel(clonePanel, cloneButton, profile);
                    }
                });
                clonePanel?.querySelector("[data-clone-name-input]")?.addEventListener("input", () => {
                    updateCloneNameControl(clonePanel, profile);
                });
                clonePanel?.querySelector("[data-clone-name-confirm]")?.addEventListener("click", (event) => {
                    updateCloneNameControl(clonePanel, profile);
                    if (event.currentTarget.getAttribute("aria-disabled") === "true") {
                        event.preventDefault();
                    }
                });
                clonePanel?.querySelector("[data-clone-name-cancel]")?.addEventListener("click", () => {
                    closeCloneNamePanel(clonePanel, cloneButton);
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
