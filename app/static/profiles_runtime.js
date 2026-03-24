(() => {
    function create({
        documentRef = document,
        windowRef = window,
        dependencies = {},
        state = {},
    }) {
        const {
            resolveTheme,
            resolveBrowserLanguage,
            updateThemeColorMeta,
            fromEditorValue,
            toEditorValue,
            renderPreferencePresetButtons,
            renderPreferenceBundleButtons,
            renderKnownPreferenceButtons,
            renderKnownPreferenceOptions,
            renderWizardSchemaShell,
            buildWizardSettingsSearchIndex,
            renderWizardSettingsSearchResults,
            setMeta,
            setDraftState,
            updateLibrarySummary,
            syncWorkspaceOverview,
            refreshWorkspaceSignal,
            updateDownloadLinks,
            setWizardStep,
            getWizardStep,
            rerenderSearchEngineDraftsForLocale,
            syncWizardFieldsFromForm,
            syncWizardNetworkFromEditor,
            syncWizardPoliciesFromEditor,
            syncWizardPreferencesFromEditor,
            syncWizardExtensionsFromEditor,
            setValidationPreview,
            updateActionState,
            saveCurrent,
            resetDraft,
            doSoftDelete,
            doHardDelete,
            doRestore,
            doResetLibrary,
            doValidate,
            reloadList,
            finishWizard,
            applyStarterPreset,
            clearWizardSettingsSearch,
            findSettingsTarget,
            revealSettingsTarget,
            appendSearchEngineDraft,
            applySearchEnginePreset,
            bindAddButtonListeners,
            applyNetworkFromWizard,
            applyQuickPolicyFromWizard,
            applyQuickPolicySelectFromWizard,
            bindExtensionInputListeners,
            applyExtensionsFromWizard,
            applySettingsFilter,
            refreshSchemaNestedDictionaryRows,
            renderSchemaPolicyReviewState,
            applySchemaPolicyFromCard,
            findFinalReviewTarget,
            findNetworkReviewTarget,
            findHomeReviewTarget,
            findSearchReviewTarget,
            findExtensionReviewTarget,
            findBookmarkReviewTarget,
            findWebsiteAccessReviewTarget,
            findPrivacyReviewTarget,
            appendSchemaArrayItem,
            removeSchemaArrayItem,
            appendSchemaNestedArrayItem,
            removeSchemaNestedArrayItem,
            appendSchemaDictionaryEntry,
            removeSchemaDictionaryEntry,
            appendSchemaNestedDictionaryEntry,
            removeSchemaNestedDictionaryEntry,
            currentSnapshotState,
            setStatus,
        } = dependencies;

        const getEditor = state.getEditor || (() => null);
        const setEditor = state.setEditor || (() => {});
        const getCurrentRaw = state.getCurrentRaw || (() => ({}));
        const getCurrentProfile = state.getCurrentProfile || (() => null);
        const getCurrentLang = state.getCurrentLang || (() => "en");
        const setCurrentLang = state.setCurrentLang || (() => {});
        const setLocaleDict = state.setLocaleDict || (() => {});
        const getLibraryStats = state.getLibraryStats || (() => ({ filtered: 0, total: 0 }));
        const getSearchTimer = state.getSearchTimer || (() => null);
        const setSearchTimer = state.setSearchTimer || (() => {});

        const langStorageKey = "bpm-lang-mode";
        const themeStorageKey = "bpm-theme-mode";
        const themeMediaQuery = windowRef.matchMedia("(prefers-color-scheme: dark)");

        const editorEl = documentRef.getElementById("editor");
        const formatButtonEl = documentRef.getElementById("format");
        const modeSelectEl = documentRef.getElementById("mode");
        const saveButtonEl = documentRef.getElementById("save");
        const newProfileButtonEl = documentRef.getElementById("new-profile");
        const softDeleteButtonEl = documentRef.getElementById("soft-delete");
        const hardDeleteButtonEl = documentRef.getElementById("hard-delete");
        const restoreButtonEl = documentRef.getElementById("restore");
        const resetLibraryButtonEl = documentRef.getElementById("reset-library");
        const validateButtonEl = documentRef.getElementById("validate");
        const refreshButtonEl = documentRef.getElementById("refresh");
        const langSelectEl = documentRef.getElementById("lang");
        const themeSelectEl = documentRef.getElementById("theme");
        const searchInputEl = documentRef.getElementById("search");
        const sortSelectEl = documentRef.getElementById("sort");
        const orderSelectEl = documentRef.getElementById("order");
        const includeDeletedEl = documentRef.getElementById("include-deleted");
        const nameInput = documentRef.getElementById("profile-name");
        const ownerInput = documentRef.getElementById("profile-owner");
        const descriptionInput = documentRef.getElementById("profile-description");
        const profileTypeEl = documentRef.getElementById("profile-type");
        const wizardNameEl = documentRef.getElementById("wizard-name");
        const wizardSchemaEl = documentRef.getElementById("wizard-schema");
        const wizardModeEl = documentRef.getElementById("wizard-mode");
        const wizardPrevEl = documentRef.getElementById("wizard-prev");
        const wizardNextEl = documentRef.getElementById("wizard-next");
        const wizardFinishEl = documentRef.getElementById("wizard-finish");
        const wizardSettingsSearchInputEl = documentRef.getElementById("wizard-settings-search-input");
        const wizardSettingsSearchResultsEl = documentRef.getElementById("wizard-settings-search-results");
        const wizardSettingsSearchClearEl = documentRef.getElementById("wizard-settings-search-clear");
        const wizardSearchEngineAddButtonEl = documentRef.getElementById("wizard-search-engine-add");
        const wizardHomepageUrlEl = documentRef.getElementById("wizard-homepage-url");
        const wizardHomepageAdditionalEl = documentRef.getElementById("wizard-homepage-additional");
        const wizardHomepageStartPageEl = documentRef.getElementById("wizard-homepage-start-page");
        const wizardHomepageLockedEl = documentRef.getElementById("wizard-homepage-locked");
        const wizardSearchBarEl = documentRef.getElementById("wizard-search-bar");
        const wizardSearchSuggestEl = documentRef.getElementById("wizard-search-suggest");
        const wizardSearchDefaultEngineEl = documentRef.getElementById("wizard-search-default-engine");
        const wizardSearchPreventInstallsEl = documentRef.getElementById("wizard-search-prevent-installs");
        const wizardSearchRemoveEl = documentRef.getElementById("wizard-search-remove");
        const wizardNewTabPageEl = documentRef.getElementById("wizard-new-tab-page");
        const wizardOverrideFirstRunEl = documentRef.getElementById("wizard-override-first-run");
        const wizardOverridePostUpdateEl = documentRef.getElementById("wizard-override-post-update");
        const wizardProxyModeEl = documentRef.getElementById("wizard-proxy-mode");
        const wizardProxyLockedEl = documentRef.getElementById("wizard-proxy-locked");
        const wizardProxyHttpEl = documentRef.getElementById("wizard-proxy-http");
        const wizardProxySslEl = documentRef.getElementById("wizard-proxy-ssl");
        const wizardProxyFtpEl = documentRef.getElementById("wizard-proxy-ftp");
        const wizardProxySocksEl = documentRef.getElementById("wizard-proxy-socks");
        const wizardProxySocksVersionEl = documentRef.getElementById("wizard-proxy-socks-version");
        const wizardProxyPassthroughEl = documentRef.getElementById("wizard-proxy-passthrough");
        const wizardProxyAutoConfigUrlEl = documentRef.getElementById("wizard-proxy-auto-config-url");
        const wizardProxyUseHttpForAllEl = documentRef.getElementById("wizard-proxy-use-http-for-all");
        const wizardProxyAutoLoginEl = documentRef.getElementById("wizard-proxy-auto-login");
        const wizardProxyUseDnsEl = documentRef.getElementById("wizard-proxy-use-dns");

        const wizardStepButtons = Array.from(documentRef.querySelectorAll(".wizard-step"));
        const wizardStarterButtons = Array.from(documentRef.querySelectorAll("[data-starter-key]"));
        const wizardPolicyInputs = Array.from(documentRef.querySelectorAll("[data-policy-key]"));
        const wizardPolicySelectInputs = Array.from(documentRef.querySelectorAll("[data-policy-select-key]"));
        const wizardSearchEnginePresetButtons = Array.from(documentRef.querySelectorAll("[data-search-engine-preset]"));
        const wizardFirefoxHomeInputs = Array.from(documentRef.querySelectorAll("[data-firefox-home-key]"));
        const wizardFirefoxSuggestInputs = Array.from(documentRef.querySelectorAll("[data-firefox-suggest-key]"));

        function applyThemeMode(mode, persist = true) {
            const normalizedMode = ["system", "light", "dark"].includes(mode) ? mode : "system";
            const resolvedTheme = resolveTheme(normalizedMode, themeMediaQuery);

            documentRef.documentElement.dataset.themeMode = normalizedMode;
            documentRef.documentElement.dataset.theme = resolvedTheme;
            themeSelectEl.value = normalizedMode;
            updateThemeColorMeta(documentRef, resolvedTheme);

            if (persist) {
                windowRef.localStorage.setItem(themeStorageKey, normalizedMode);
            }

            const editor = getEditor();
            if (editor && windowRef.monaco) {
                windowRef.monaco.editor.setTheme(resolvedTheme === "dark" ? "vs-dark" : "vs");
            }
        }

        async function loadLocale(lang) {
            try {
                const res = await windowRef.fetch(`/i18n/${lang}.json`);
                if (!res.ok) throw new Error(await res.text());
                const nextLocale = await res.json();
                setLocaleDict(nextLocale);
                setCurrentLang(lang);
                documentRef.documentElement.lang = lang;

                documentRef.querySelectorAll("[data-i18n]").forEach((el) => {
                    const key = el.getAttribute("data-i18n");
                    if (nextLocale[key]) el.textContent = nextLocale[key];
                });
                documentRef.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
                    const key = el.getAttribute("data-i18n-placeholder");
                    if (nextLocale[key]) el.placeholder = nextLocale[key];
                });
                documentRef.querySelectorAll("[data-i18n-title]").forEach((el) => {
                    const key = el.getAttribute("data-i18n-title");
                    if (nextLocale[key]) el.title = nextLocale[key];
                });
                renderPreferencePresetButtons();
                renderPreferenceBundleButtons();
                renderKnownPreferenceButtons();
                renderKnownPreferenceOptions();
                renderWizardSchemaShell();
                buildWizardSettingsSearchIndex();
                renderWizardSettingsSearchResults();

                if (getCurrentProfile()) {
                    setMeta(getCurrentProfile());
                } else {
                    setDraftState();
                }
                updateLibrarySummary(getLibraryStats());
                syncWorkspaceOverview();
                refreshWorkspaceSignal();
                setWizardStep(getWizardStep());
                rerenderSearchEngineDraftsForLocale();
            } catch (e) {
                console.warn("i18n load failed:", e);
            }
        }

        async function applyLanguageMode(mode, persist = true) {
            const normalizedMode = ["system", "en", "ru"].includes(mode) ? mode : "system";
            const resolvedLanguage = normalizedMode === "system"
                ? resolveBrowserLanguage(windowRef.navigator)
                : normalizedMode;

            documentRef.documentElement.dataset.langMode = normalizedMode;
            langSelectEl.value = normalizedMode;

            if (persist) {
                windowRef.localStorage.setItem(langStorageKey, normalizedMode);
            }

            await loadLocale(resolvedLanguage);
        }

        function debounceReload() {
            const searchTimer = getSearchTimer();
            if (searchTimer) windowRef.clearTimeout(searchTimer);
            setSearchTimer(windowRef.setTimeout(() => {
                setSearchTimer(null);
                reloadList();
            }, 220));
        }

        function syncEditorBackedUi() {
            syncWizardNetworkFromEditor();
            syncWizardPoliciesFromEditor();
            syncWizardPreferencesFromEditor();
            syncWizardExtensionsFromEditor();
        }

        function wireNetworkControls() {
            [
                wizardHomepageUrlEl,
                wizardHomepageAdditionalEl,
                wizardHomepageStartPageEl,
                wizardHomepageLockedEl,
                wizardSearchBarEl,
                wizardSearchSuggestEl,
                wizardSearchDefaultEngineEl,
                wizardSearchPreventInstallsEl,
                wizardSearchRemoveEl,
                wizardNewTabPageEl,
                wizardOverrideFirstRunEl,
                wizardOverridePostUpdateEl,
                wizardProxyModeEl,
                wizardProxyLockedEl,
                wizardProxyHttpEl,
                wizardProxySslEl,
                wizardProxyFtpEl,
                wizardProxySocksEl,
                wizardProxySocksVersionEl,
                wizardProxyPassthroughEl,
                wizardProxyAutoConfigUrlEl,
                wizardProxyUseHttpForAllEl,
                wizardProxyAutoLoginEl,
                wizardProxyUseDnsEl,
                ...wizardFirefoxHomeInputs,
                ...wizardFirefoxSuggestInputs,
            ].forEach((input) => {
                input.addEventListener("input", applyNetworkFromWizard);
                input.addEventListener("change", applyNetworkFromWizard);
            });
        }

        function wireSchemaEvents() {
            documentRef.addEventListener("change", (event) => {
                const schemaControl = event.target.closest(
                    "[data-schema-policy-field], [data-schema-nested-field], [data-schema-nested-dict-key], [data-schema-branch-mode], [data-schema-dict-key]",
                );
                if (!schemaControl) return;
                const card = schemaControl.closest("[data-schema-policy-card]");
                if (!card) return;
                const nestedDictContainer = schemaControl.closest('[data-schema-nested-kind="nested-dictionary-object"]');
                if (nestedDictContainer) {
                    refreshSchemaNestedDictionaryRows(nestedDictContainer);
                }
                renderSchemaPolicyReviewState(card);
                applySchemaPolicyFromCard(card);
            });

            documentRef.addEventListener("input", (event) => {
                const schemaControl = event.target.closest(
                    "[data-schema-policy-field], [data-schema-nested-field], [data-schema-nested-dict-key], [data-schema-dict-key]",
                );
                if (!schemaControl) return;
                const card = schemaControl.closest("[data-schema-policy-card]");
                if (!card) return;
                const nestedDictContainer = schemaControl.closest('[data-schema-nested-kind="nested-dictionary-object"]');
                if (nestedDictContainer) {
                    refreshSchemaNestedDictionaryRows(nestedDictContainer);
                }
                renderSchemaPolicyReviewState(card);
            });
        }

        function wireDocumentClicks() {
            documentRef.addEventListener("click", (event) => {
                const exportSaveActionButton = event.target.closest("#wizard-export-save-action");
                if (exportSaveActionButton) {
                    saveButtonEl.click();
                    return;
                }

                const exportValidateActionButton = event.target.closest("#wizard-export-validate-action");
                if (exportValidateActionButton) {
                    validateButtonEl.click();
                    return;
                }

                const finalReviewJumpButton = event.target.closest("[data-final-review-jump]");
                if (finalReviewJumpButton) {
                    const targetEl = findFinalReviewTarget(finalReviewJumpButton.dataset.finalReviewJump || "");
                    if (targetEl) {
                        revealSettingsTarget(targetEl);
                    }
                    return;
                }

                const networkReviewJumpButton = event.target.closest("[data-network-review-jump]");
                if (networkReviewJumpButton) {
                    const targetEl = findNetworkReviewTarget(networkReviewJumpButton.dataset.networkReviewJump || "");
                    if (targetEl) {
                        revealSettingsTarget(targetEl);
                    }
                    return;
                }

                const homeReviewJumpButton = event.target.closest("[data-home-review-jump]");
                if (homeReviewJumpButton) {
                    const targetEl = findHomeReviewTarget(homeReviewJumpButton.dataset.homeReviewJump || "");
                    if (targetEl) {
                        revealSettingsTarget(targetEl);
                    }
                    return;
                }

                const searchReviewJumpButton = event.target.closest("[data-search-review-jump]");
                if (searchReviewJumpButton) {
                    const targetEl = findSearchReviewTarget(searchReviewJumpButton.dataset.searchReviewJump || "");
                    if (targetEl) {
                        revealSettingsTarget(targetEl);
                    }
                    return;
                }

                const extensionReviewJumpButton = event.target.closest("[data-extension-review-jump]");
                if (extensionReviewJumpButton) {
                    const targetEl = findExtensionReviewTarget(extensionReviewJumpButton.dataset.extensionReviewJump || "");
                    if (targetEl) {
                        revealSettingsTarget(targetEl);
                    }
                    return;
                }

                const bookmarkReviewJumpButton = event.target.closest("[data-bookmark-review-jump]");
                if (bookmarkReviewJumpButton) {
                    const targetEl = findBookmarkReviewTarget(bookmarkReviewJumpButton.dataset.bookmarkReviewJump || "");
                    if (targetEl) {
                        revealSettingsTarget(targetEl);
                    }
                    return;
                }

                const websiteAccessReviewJumpButton = event.target.closest("[data-website-access-review-jump]");
                if (websiteAccessReviewJumpButton) {
                    const targetEl = findWebsiteAccessReviewTarget(websiteAccessReviewJumpButton.dataset.websiteAccessReviewJump || "");
                    if (targetEl) {
                        revealSettingsTarget(targetEl);
                    }
                    return;
                }

                const privacyReviewJumpButton = event.target.closest("[data-privacy-review-jump]");
                if (privacyReviewJumpButton) {
                    const targetEl = findPrivacyReviewTarget(privacyReviewJumpButton.dataset.privacyReviewJump || "");
                    if (targetEl) {
                        revealSettingsTarget(targetEl);
                    }
                    return;
                }

                const filterButton = event.target.closest("[data-settings-filter]");
                if (filterButton) {
                    const navEl = filterButton.closest("[data-settings-nav]");
                    applySettingsFilter(navEl, filterButton.dataset.settingsFilter || "all");
                    return;
                }

                const jumpButton = event.target.closest("[data-settings-jump-target]");
                if (jumpButton) {
                    const targetEl = findSettingsTarget(jumpButton.dataset.settingsJumpTarget || "");
                    if (targetEl) {
                        revealSettingsTarget(targetEl);
                    }
                    return;
                }

                const shellJumpButton = event.target.closest("[data-wizard-shell-jump]");
                if (shellJumpButton) {
                    const targetEl = findSettingsTarget(shellJumpButton.dataset.settingsJumpTarget || "");
                    if (targetEl) {
                        revealSettingsTarget(targetEl);
                    }
                    return;
                }

                const shellTargetButton = event.target.closest("[data-wizard-shell-target]");
                if (shellTargetButton) {
                    revealSettingsTarget(shellTargetButton);
                    return;
                }

                const schemaArrayAddButton = event.target.closest("[data-schema-array-add]");
                if (schemaArrayAddButton) {
                    appendSchemaArrayItem(schemaArrayAddButton.closest("[data-schema-policy-card]"));
                    return;
                }

                const schemaNestedArrayAddButton = event.target.closest("[data-schema-nested-array-add]");
                if (schemaNestedArrayAddButton) {
                    const container = schemaNestedArrayAddButton.closest('[data-schema-nested-kind="nested-array-of-objects"]');
                    const card = schemaNestedArrayAddButton.closest("[data-schema-policy-card]");
                    appendSchemaNestedArrayItem(container);
                    if (card) {
                        renderSchemaPolicyReviewState(card);
                        applySchemaPolicyFromCard(card);
                    }
                    return;
                }

                const schemaArrayRemoveButton = event.target.closest("[data-schema-array-remove]");
                if (schemaArrayRemoveButton) {
                    removeSchemaArrayItem(
                        schemaArrayRemoveButton.closest("[data-schema-policy-card]"),
                        schemaArrayRemoveButton.dataset.schemaArrayIndex,
                    );
                    return;
                }

                const schemaNestedArrayRemoveButton = event.target.closest("[data-schema-nested-array-remove]");
                if (schemaNestedArrayRemoveButton) {
                    const row = schemaNestedArrayRemoveButton.closest("[data-schema-nested-array-row]");
                    const container = schemaNestedArrayRemoveButton.closest('[data-schema-nested-kind="nested-array-of-objects"]');
                    const card = schemaNestedArrayRemoveButton.closest("[data-schema-policy-card]");
                    removeSchemaNestedArrayItem(container, row);
                    if (card) {
                        renderSchemaPolicyReviewState(card);
                        applySchemaPolicyFromCard(card);
                    }
                    return;
                }

                const schemaDictAddButton = event.target.closest("[data-schema-dict-add]");
                if (schemaDictAddButton) {
                    appendSchemaDictionaryEntry(schemaDictAddButton.closest("[data-schema-policy-card]"));
                    return;
                }

                const schemaNestedDictAddButton = event.target.closest("[data-schema-nested-dict-add]");
                if (schemaNestedDictAddButton) {
                    const container = schemaNestedDictAddButton.closest('[data-schema-nested-kind="nested-dictionary-object"]');
                    const card = schemaNestedDictAddButton.closest("[data-schema-policy-card]");
                    appendSchemaNestedDictionaryEntry(container);
                    if (card) {
                        renderSchemaPolicyReviewState(card);
                        applySchemaPolicyFromCard(card);
                    }
                    return;
                }

                const schemaDictRemoveButton = event.target.closest("[data-schema-dict-remove]");
                if (schemaDictRemoveButton) {
                    removeSchemaDictionaryEntry(
                        schemaDictRemoveButton.closest("[data-schema-policy-card]"),
                        schemaDictRemoveButton.dataset.schemaDictIndex,
                    );
                    return;
                }

                const schemaNestedDictRemoveButton = event.target.closest("[data-schema-nested-dict-remove]");
                if (schemaNestedDictRemoveButton) {
                    const row = schemaNestedDictRemoveButton.closest("[data-schema-nested-dict-row]");
                    const container = schemaNestedDictRemoveButton.closest('[data-schema-nested-kind="nested-dictionary-object"]');
                    const card = schemaNestedDictRemoveButton.closest("[data-schema-policy-card]");
                    removeSchemaNestedDictionaryEntry(container, row);
                    if (card) {
                        renderSchemaPolicyReviewState(card);
                        applySchemaPolicyFromCard(card);
                    }
                    return;
                }

                const searchResultButton = event.target.closest("[data-settings-search-target]");
                if (searchResultButton) {
                    const targetEl = findSettingsTarget(searchResultButton.dataset.settingsSearchTarget || "");
                    if (targetEl) {
                        revealSettingsTarget(targetEl);
                    }
                }
            });
        }

        function start() {
            windowRef.require(["vs/editor/editor.main"], () => {
                const monacoRef = windowRef.monaco;
                const editor = monacoRef.editor.create(editorEl, {
                    value: "{}",
                    language: "json",
                    automaticLayout: true,
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineHeight: 22,
                    padding: { top: 18, bottom: 18 },
                    smoothScrolling: true,
                    roundedSelection: true,
                    scrollBeyondLastLine: false,
                    theme: documentRef.documentElement.dataset.theme === "dark" ? "vs-dark" : "vs",
                });
                setEditor(editor);

                formatButtonEl.addEventListener("click", () => {
                    try {
                        const mode = modeSelectEl.value;
                        const parsed = fromEditorValue(editor.getValue(), mode);
                        editor.setValue(toEditorValue(parsed, mode));
                        setStatus("Editor content formatted.", "success");
                    } catch (e) {
                        setStatus(`Format error: ${e.message || e}`, "error");
                    }
                });

                modeSelectEl.addEventListener("change", (event) => {
                    const mode = event.target.value;
                    windowRef.localStorage.setItem("bpm-editor-mode", mode);
                    monacoRef.editor.setModelLanguage(editor.getModel(), mode === "yaml" ? "yaml" : "json");
                    editor.setValue(toEditorValue(getCurrentRaw(), mode));
                    syncWizardFieldsFromForm();
                    syncEditorBackedUi();
                    syncWorkspaceOverview();
                    setStatus(`Switched editor to ${mode.toUpperCase()}.`, "info");
                });

                saveButtonEl.addEventListener("click", saveCurrent);
                newProfileButtonEl.addEventListener("click", resetDraft);
                softDeleteButtonEl.addEventListener("click", doSoftDelete);
                hardDeleteButtonEl.addEventListener("click", doHardDelete);
                restoreButtonEl.addEventListener("click", doRestore);
                resetLibraryButtonEl.addEventListener("click", doResetLibrary);
                validateButtonEl.addEventListener("click", doValidate);
                refreshButtonEl.addEventListener("click", reloadList);

                langSelectEl.addEventListener("change", async (event) => {
                    await applyLanguageMode(event.target.value);
                });
                themeSelectEl.addEventListener("change", (event) => {
                    applyThemeMode(event.target.value);
                });
                searchInputEl.addEventListener("input", debounceReload);
                sortSelectEl.addEventListener("change", reloadList);
                orderSelectEl.addEventListener("change", reloadList);
                includeDeletedEl.addEventListener("change", reloadList);
                nameInput.addEventListener("input", () => {
                    syncWizardFieldsFromForm();
                    updateActionState();
                });
                ownerInput.addEventListener("input", () => {
                    syncWizardFieldsFromForm();
                    updateActionState();
                });
                descriptionInput.addEventListener("input", () => {
                    syncWizardFieldsFromForm();
                    updateActionState();
                });
                profileTypeEl.addEventListener("change", () => {
                    syncWizardFieldsFromForm();
                    updateActionState();
                });
                editor.onDidChangeModelContent(() => {
                    setValidationPreview();
                    syncEditorBackedUi();
                    renderWizardSchemaShell();
                    updateActionState();
                });

                wizardStepButtons.forEach((button) => {
                    button.addEventListener("click", () => setWizardStep(button.dataset.step));
                });
                wizardPrevEl.addEventListener("click", () => setWizardStep(getWizardStep() - 1));
                wizardNextEl.addEventListener("click", () => {
                    setWizardStep(getWizardStep() + 1);
                });
                wizardFinishEl.addEventListener("click", finishWizard);
                wizardNameEl.addEventListener("input", () => {
                    nameInput.value = wizardNameEl.value;
                    updateActionState();
                });
                wizardSchemaEl.addEventListener("change", () => {
                    profileTypeEl.value = wizardSchemaEl.value;
                    syncWizardFieldsFromForm();
                    updateActionState();
                });
                wizardModeEl.addEventListener("change", () => {
                    modeSelectEl.value = wizardModeEl.value;
                    modeSelectEl.dispatchEvent(new windowRef.Event("change"));
                    updateActionState();
                });
                wizardStarterButtons.forEach((button) => {
                    button.addEventListener("click", () => {
                        applyStarterPreset(button.dataset.starterKey);
                    });
                });
                wizardSettingsSearchInputEl?.addEventListener("input", () => {
                    renderWizardSettingsSearchResults();
                });
                wizardSettingsSearchInputEl?.addEventListener("keydown", (event) => {
                    if (event.key === "Escape") {
                        clearWizardSettingsSearch();
                        return;
                    }
                    if (event.key !== "Enter") return;

                    const firstMatch = wizardSettingsSearchResultsEl?.querySelector("[data-settings-search-target]");
                    if (!firstMatch) return;
                    event.preventDefault();
                    const targetEl = findSettingsTarget(firstMatch.dataset.settingsSearchTarget || "");
                    if (targetEl) {
                        revealSettingsTarget(targetEl);
                    }
                });
                wizardSettingsSearchClearEl?.addEventListener("click", () => {
                    clearWizardSettingsSearch();
                    wizardSettingsSearchInputEl?.focus();
                });
                wizardSearchEngineAddButtonEl.addEventListener("click", () => {
                    appendSearchEngineDraft();
                });
                wizardSearchEnginePresetButtons.forEach((button) => {
                    button.addEventListener("click", () => {
                        applySearchEnginePreset(button.dataset.searchEnginePreset);
                    });
                });
                bindAddButtonListeners();
                wireNetworkControls();
                wizardPolicyInputs.forEach((input) => {
                    input.addEventListener("change", () => {
                        applyQuickPolicyFromWizard(input.dataset.policyKey, input.checked);
                    });
                });
                wizardPolicySelectInputs.forEach((input) => {
                    input.addEventListener("change", () => {
                        applyQuickPolicySelectFromWizard(input.dataset.policySelectKey, input.value);
                    });
                });
                bindExtensionInputListeners(applyExtensionsFromWizard);
                documentRef.querySelectorAll("[data-settings-nav]").forEach((navEl) => {
                    applySettingsFilter(navEl, "all");
                });
                wireSchemaEvents();
                wireDocumentClicks();

                windowRef.addEventListener("keydown", (event) => {
                    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
                        event.preventDefault();
                        saveCurrent();
                    }
                });

                windowRef.addEventListener("beforeunload", (event) => {
                    if (!currentSnapshotState().dirty) return;
                    event.preventDefault();
                    event.returnValue = "";
                });

                const legacySavedLang = windowRef.localStorage.getItem("bpm-lang");
                const savedLangMode = windowRef.localStorage.getItem(langStorageKey) || legacySavedLang || "system";
                const savedMode = windowRef.localStorage.getItem("bpm-editor-mode") || "json";
                const savedThemeMode = windowRef.localStorage.getItem(themeStorageKey) || "system";
                langSelectEl.value = savedLangMode;
                modeSelectEl.value = savedMode;
                themeSelectEl.value = savedThemeMode;
                monacoRef.editor.setModelLanguage(editor.getModel(), savedMode === "yaml" ? "yaml" : "json");
                editor.setValue(toEditorValue({}, savedMode));
                applyThemeMode(savedThemeMode, false);
                syncWizardFieldsFromForm();
                syncEditorBackedUi();
                setWizardStep(1);

                const handleSystemThemeChange = () => {
                    const activeMode = windowRef.localStorage.getItem(themeStorageKey) || "system";
                    if (activeMode === "system") {
                        applyThemeMode("system", false);
                    }
                };

                if (typeof themeMediaQuery.addEventListener === "function") {
                    themeMediaQuery.addEventListener("change", handleSystemThemeChange);
                } else if (typeof themeMediaQuery.addListener === "function") {
                    themeMediaQuery.addListener(handleSystemThemeChange);
                }

                resetDraft();
                reloadList();
                applyLanguageMode(savedLangMode, false);
                updateDownloadLinks();
                syncWorkspaceOverview();
            });
        }

        return {
            applyThemeMode,
            applyLanguageMode,
            loadLocale,
            start,
        };
    }

    window.BPMProfilesRuntime = { create };
})();
