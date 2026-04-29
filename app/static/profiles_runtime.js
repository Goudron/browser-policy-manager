(() => {
    function create({
        documentRef = document,
        windowRef = window,
        dependencies = {},
        state = {},
    }) {
        const {
            t,
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
            doImportFirefoxPoliciesJson,
            reloadList,
            finishWizard,
            applyScenarioPreset,
            applyStarterPreset,
            setWizardComplianceLayer,
            undoCurrentStepChanges,
            resetCurrentStepToBaseline,
            setPreviewStarter,
            clearPreviewStarter,
            clearWizardSettingsSearch,
            findSettingsTarget,
            revealSettingsTarget,
            getFinalReviewSelection,
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
            findAiReviewTarget,
            findExtensionReviewTarget,
            findBookmarkReviewTarget,
            findWebsiteAccessReviewTarget,
            findPrivacyReviewTarget,
            appendSchemaListItem,
            removeSchemaListItem,
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
        const workspaceScopeStorageKey = "bpm-workspace-scope";
        const themeMediaQuery = windowRef.matchMedia("(prefers-color-scheme: dark)");
        let localeRequestId = 0;
        let wizardConditionalVisibilityBound = false;
        let documentClicksBound = false;
        let jumpButtonsBound = false;
        let wizardNavBound = false;
        let lastAdvancedReturnTriggerEl = null;

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
        const importFirefoxPoliciesButtonEl = documentRef.getElementById("import-firefox-policies");
        const importFirefoxPoliciesFileEl = documentRef.getElementById("import-firefox-policies-file");
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
        const wizardStepUndoEl = documentRef.getElementById("wizard-step-undo");
        const wizardStepResetEl = documentRef.getElementById("wizard-step-reset");
        const workspaceScopeGuidedEl = documentRef.getElementById("workspace-scope-guided");
        const workspaceScopeAdvancedEl = documentRef.getElementById("workspace-scope-advanced");
        const workspaceScopeSummaryEl = documentRef.getElementById("workspace-scope-summary");
        const workspaceScopeSummaryTitleEl = documentRef.getElementById("workspace-scope-summary-title");
        const workspaceScopeSummaryCopyEl = documentRef.getElementById("workspace-scope-summary-copy");
        const workspaceScopeGuidedCardEl = documentRef.getElementById("workspace-scope-guided-card");
        const workspaceScopeAdvancedCardEl = documentRef.getElementById("workspace-scope-advanced-card");
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
        const wizardScenarioButtons = Array.from(documentRef.querySelectorAll("[data-scenario-key]"));
        const wizardStarterButtons = Array.from(documentRef.querySelectorAll("[data-starter-key]"));
        const wizardCisLayerButtons = Array.from(documentRef.querySelectorAll("[data-cis-layer-key]"));
        const wizardPolicyInputs = Array.from(documentRef.querySelectorAll("[data-policy-key]"));
        const wizardPolicySelectInputs = Array.from(documentRef.querySelectorAll("[data-policy-select-key]"));
        const wizardSearchEnginePresetButtons = Array.from(documentRef.querySelectorAll("[data-search-engine-preset]"));
        const wizardFirefoxHomeInputs = Array.from(documentRef.querySelectorAll("[data-firefox-home-key]"));
        const wizardFirefoxSuggestInputs = Array.from(documentRef.querySelectorAll("[data-firefox-suggest-key]"));
        const wizardProxyModeGroups = Array.from(documentRef.querySelectorAll("[data-proxy-mode-group]"));
        const advancedContextStepEl = documentRef.getElementById("advanced-context-step");
        const advancedContextCopyEl = documentRef.getElementById("advanced-context-copy");
        const advancedContextListEl = documentRef.getElementById("advanced-context-list");
        const advancedContextReturnEl = documentRef.getElementById("advanced-context-return");
        const advancedContextEmptyEl = documentRef.getElementById("advanced-context-empty");
        const wizardExportShareableTextEl = documentRef.getElementById("wizard-export-shareable-text");
        const wizardExportShareableStatusEl = documentRef.getElementById("wizard-export-shareable-status");
        let advancedHandoffContext = null;

        function getDisclosurePanelPairs() {
            return [
                ["wizard-firefox-home-fine-tuning-panel", "wizard-firefox-home-fine-tuning-toggle"],
                ["wizard-search-defaults-fine-tuning-panel", "wizard-search-defaults-fine-tuning-toggle"],
                ["wizard-search-suggest-fine-tuning-panel", "wizard-search-suggest-fine-tuning-toggle"],
                ["wizard-site-data-fine-tuning-panel", "wizard-site-data-fine-tuning-toggle"],
                ["wizard-extension-fine-tuning-panel", "wizard-extension-fine-tuning-toggle"],
                ["wizard-extension-curated-panel", "wizard-extension-curated-toggle"],
                ["wizard-sync-fine-tuning-panel", "wizard-sync-fine-tuning-toggle"],
                ["wizard-website-fine-tuning-panel", "wizard-website-fine-tuning-toggle"],
                ["wizard-network-enterprise-fine-tuning-panel", "wizard-network-enterprise-fine-tuning-toggle"],
            ];
        }

        function focusElementForA11y(targetEl) {
            if (!targetEl || typeof targetEl.focus !== "function") return;
            const needsTabIndex = !targetEl.matches("a[href], button, input, select, textarea, [tabindex]");
            if (needsTabIndex) {
                targetEl.setAttribute("tabindex", "-1");
            }
            targetEl.focus({ preventScroll: true });
        }

        function syncContextualA11yLabels() {
            documentRef.querySelectorAll(".wizard-stage-status, .wizard-search-engine-preset-status").forEach((el) => {
                el.setAttribute("role", "status");
                el.setAttribute("aria-live", "polite");
            });

            documentRef.querySelectorAll([
                "#profile-derived-note",
                "#profile-clone-handoff-copy",
                "#profile-lifecycle-copy",
                "#compare-empty-copy",
                "#compare-changes-copy",
                "#compare-guided-areas-copy",
                "#advanced-context-copy",
                "#wizard-clone-handoff-copy",
                "#wizard-shared-device-workflow-copy",
                "#wizard-step-memory-copy",
            ].join(", ")).forEach((el) => {
                el.setAttribute("role", "status");
                el.setAttribute("aria-live", "polite");
            });

            documentRef.querySelectorAll([
                "#profile-clone-handoff-list",
                "#profile-lifecycle-list",
                "#compare-changes-list",
                "#compare-guided-areas-list",
                "#advanced-context-list",
                "#wizard-clone-handoff-list",
                "#wizard-shared-device-workflow-list",
            ].join(", ")).forEach((el) => {
                el.setAttribute("role", "list");
            });

            wizardStepButtons.forEach((button) => {
                const stepIndex = button.querySelector(".wizard-step-index")?.textContent?.trim() || "";
                const labelText = button.querySelector(".wizard-step-label")?.textContent?.trim() || "";
                const copyText = button.querySelector(".wizard-step-copy")?.textContent?.trim() || "";
                const labelParts = [stepIndex, labelText, copyText].filter(Boolean);
                if (labelParts.length) {
                    button.setAttribute("aria-label", labelParts.join(". "));
                }
            });

            [...wizardScenarioButtons, ...wizardStarterButtons].forEach((button) => {
                const badgeText = button.querySelector(".wizard-starter-badge")?.textContent?.trim() || "";
                const titleText = button.querySelector(".wizard-starter-title")?.textContent?.trim() || "";
                const copyText = button.querySelector(".wizard-starter-copy")?.textContent?.trim() || "";
                const noteText = button.querySelector(".wizard-starter-note")?.textContent?.trim() || "";
                const labelParts = [badgeText, titleText, copyText, noteText].filter(Boolean);
                if (labelParts.length) {
                    button.setAttribute("aria-label", labelParts.join(". "));
                }
            });

            const actionButtons = Array.from(documentRef.querySelectorAll([
                "[data-final-review-jump]",
                "[data-network-review-jump]",
                "[data-home-review-jump]",
                "[data-search-review-jump]",
                "[data-extension-review-jump]",
                "[data-ai-review-jump]",
                "[data-bookmark-review-jump]",
                "[data-website-access-review-jump]",
                "[data-privacy-review-jump]",
            ].join(", ")));

            actionButtons.forEach((button) => {
                const actionText = button.textContent.trim();
                const keyText = button.closest(".wizard-summary-row")?.querySelector(".wizard-summary-key")?.textContent?.trim() || "";
                const valueEl = button.closest(".wizard-summary-row")?.querySelector(".wizard-summary-value[id]");
                if (actionText && keyText) {
                    button.setAttribute("aria-label", `${actionText} ${keyText}`);
                }
                if (valueEl?.id) {
                    button.setAttribute("aria-describedby", valueEl.id);
                }
            });

            const contextualActionButtons = Array.from(documentRef.querySelectorAll([
                "[data-step-memory-jump]",
                "[data-clone-handoff-step]",
                "[data-clone-handoff-compare]",
                "[data-export-assist-action]",
                "[data-workspace-scope-target]",
            ].join(", ")));

            contextualActionButtons.forEach((button) => {
                const actionText = button.textContent.trim();
                const itemCopy = button.closest(".wizard-export-plan-item, .wizard-step-memory-item")
                    ?.querySelector(".wizard-export-plan-copy, .wizard-step-memory-item-copy")
                    ?.textContent?.trim() || "";
                const itemTitle = button.closest(".wizard-step-memory-item")
                    ?.querySelector(".wizard-step-memory-item-title")
                    ?.textContent?.trim() || "";
                const contextText = [itemTitle, itemCopy].filter(Boolean).join(". ");
                const copyEl = button.closest(".profile-clone-handoff-panel, .profile-lifecycle-panel, .wizard-workflow-card, .wizard-step-actions")
                    ?.querySelector("#profile-clone-handoff-copy, #profile-lifecycle-copy, #wizard-clone-handoff-copy, #wizard-shared-device-workflow-copy, #wizard-step-memory-copy");
                if (actionText && contextText) {
                    button.setAttribute("aria-label", `${actionText}. ${contextText}`);
                }
                if (copyEl?.id) {
                    button.setAttribute("aria-describedby", copyEl.id);
                }
            });

            const disclosureButtons = Array.from(documentRef.querySelectorAll([
                "#wizard-firefox-home-fine-tuning-toggle",
                "#wizard-search-defaults-fine-tuning-toggle",
                "#wizard-search-suggest-fine-tuning-toggle",
                "#wizard-site-data-fine-tuning-toggle",
                "#wizard-network-enterprise-fine-tuning-toggle",
                "#wizard-sync-fine-tuning-toggle",
                "#wizard-extension-fine-tuning-toggle",
                "#wizard-extension-curated-toggle",
                "#wizard-website-fine-tuning-toggle",
                "[data-extension-profile-toggle]",
            ].join(", ")));

            disclosureButtons.forEach((button) => {
                const actionText = button.textContent.trim();
                const cardTitle = button.closest("[data-extension-profile-card]")?.querySelector(".wizard-toggle-title")?.textContent?.trim() || "";
                const sectionTitle = button.closest(".wizard-section-group")?.querySelector(".wizard-section-title")?.textContent?.trim() || "";
                const contextText = cardTitle || sectionTitle;
                const statusEl = button.closest(".wizard-section-group")?.querySelector(".wizard-stage-status[id], .wizard-search-engine-preset-status[id]");
                if (actionText && contextText) {
                    button.setAttribute("aria-label", `${actionText} ${contextText}`);
                }
                if (statusEl?.id) {
                    button.setAttribute("aria-describedby", statusEl.id);
                }
            });

            const presetButtons = Array.from(documentRef.querySelectorAll(".wizard-search-engine-preset"));
            presetButtons.forEach((button) => {
                const titleText = button.querySelector(".wizard-search-engine-title")?.textContent?.trim() || "";
                const copyText = button.querySelector(".wizard-search-engine-preset-copy")?.textContent?.trim() || "";
                const sectionTitle = button.closest(".wizard-section-group")?.querySelector(".wizard-section-title")?.textContent?.trim() || "";
                const statusEl = button.closest(".wizard-section-group")?.querySelector(".wizard-stage-status[id], .wizard-search-engine-preset-status[id]");
                const statusText = statusEl?.textContent?.trim() || "";
                const labelParts = [titleText, copyText, sectionTitle, statusText].filter(Boolean);
                if (labelParts.length) {
                    button.setAttribute("aria-label", labelParts.join(". "));
                }
                if (statusEl?.id) {
                    button.setAttribute("aria-describedby", statusEl.id);
                }
            });
        }

        function getCompositeButtons(containerEl) {
            if (!containerEl) return [];
            if (containerEl.matches(".wizard-stepper")) {
                return Array.from(containerEl.querySelectorAll(".wizard-step"));
            }
            if (containerEl.matches(".wizard-scenario-grid")) {
                return Array.from(containerEl.querySelectorAll("[data-scenario-key]"));
            }
            if (containerEl.matches(".wizard-starter-grid")) {
                return Array.from(containerEl.querySelectorAll("[data-starter-key]"));
            }
            if (containerEl.matches(".wizard-search-engine-preset-grid")) {
                return Array.from(containerEl.querySelectorAll(".wizard-search-engine-preset"));
            }
            return [];
        }

        function wireCompositeButtonNavigation() {
            documentRef.addEventListener("keydown", (event) => {
                if (event.defaultPrevented) return;
                const supportedKeys = ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"];
                if (!supportedKeys.includes(event.key)) return;

                const activeButton = event.target?.closest([
                    ".wizard-step",
                    ".wizard-starter-card",
                    ".wizard-search-engine-preset",
                ].join(", "));
                if (!activeButton) return;

                const containerEl = activeButton.closest([
                    ".wizard-stepper",
                    ".wizard-scenario-grid",
                    ".wizard-starter-grid",
                    ".wizard-search-engine-preset-grid",
                ].join(", "));
                const buttons = getCompositeButtons(containerEl).filter((button) =>
                    !button.disabled && button.closest("[hidden]") === null
                );
                if (buttons.length <= 1) return;

                const currentIndex = buttons.indexOf(activeButton);
                if (currentIndex < 0) return;

                let nextIndex = currentIndex;
                if (event.key === "Home") {
                    nextIndex = 0;
                } else if (event.key === "End") {
                    nextIndex = buttons.length - 1;
                } else if (event.key === "ArrowRight" || event.key === "ArrowDown") {
                    nextIndex = (currentIndex + 1) % buttons.length;
                } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
                    nextIndex = (currentIndex - 1 + buttons.length) % buttons.length;
                }

                if (nextIndex === currentIndex) return;
                event.preventDefault();
                focusElementForA11y(buttons[nextIndex]);
            });
        }

        function getWizardStepLabel(stepNumber) {
            if (!stepNumber) return "";
            return documentRef
                .querySelector(`.wizard-step[data-step="${stepNumber}"] .wizard-step-label`)
                ?.textContent
                ?.trim() || "";
        }

        function buildAdvancedHandoffContext(stepNumber, options = {}) {
            const normalizedStep = Number(stepNumber);
            if (Number.isNaN(normalizedStep) || normalizedStep <= 0) {
                return null;
            }

            return {
                step: normalizedStep,
                title: options.stepTitle || getWizardStepLabel(normalizedStep),
                items: Array.isArray(options.items) ? options.items.filter(Boolean).slice(0, 2) : [],
                remaining: Math.max(0, Number(options.remaining) || 0),
            };
        }

        function renderAdvancedHandoffContext() {
            if (!advancedContextStepEl || !advancedContextCopyEl || !advancedContextListEl || !advancedContextReturnEl) return;

            if (!advancedHandoffContext) {
                advancedContextStepEl.textContent = t("profiles.workspace_scope_advanced");
                advancedContextStepEl.setAttribute("data-i18n", "profiles.workspace_scope_advanced");
                advancedContextCopyEl.textContent = t("profiles.advanced_context_body");
                advancedContextCopyEl.setAttribute("data-i18n", "profiles.advanced_context_body");
                advancedContextListEl.innerHTML = "";
                advancedContextListEl.hidden = true;
                advancedContextReturnEl.hidden = true;
                advancedContextReturnEl.dataset.advancedReturnStep = "";
                if (advancedContextEmptyEl) {
                    advancedContextEmptyEl.hidden = false;
                }
                return;
            }

            const title = advancedHandoffContext.title || t("profiles.workspace_scope_advanced");
            advancedContextStepEl.textContent = title;
            advancedContextStepEl.removeAttribute("data-i18n");
            advancedContextCopyEl.textContent = t("profiles.advanced_context_from_step").replace("{step}", title);
            advancedContextCopyEl.removeAttribute("data-i18n");

            const listItems = advancedHandoffContext.items.slice();
            if (advancedHandoffContext.remaining > 0) {
                listItems.push(
                    t("profiles.advanced_context_more").replace("{count}", String(advancedHandoffContext.remaining)),
                );
            }

            advancedContextListEl.innerHTML = listItems
                .map((item) => `<li class="advanced-context-item">${item}</li>`)
                .join("");
            advancedContextListEl.hidden = listItems.length <= 0;
            advancedContextReturnEl.hidden = false;
            advancedContextReturnEl.dataset.advancedReturnStep = String(advancedHandoffContext.step);
            if (advancedContextEmptyEl) {
                advancedContextEmptyEl.hidden = true;
            }
        }

        function setAdvancedHandoffContext(context) {
            advancedHandoffContext = context;
            renderAdvancedHandoffContext();
        }

        function resolveFinalReviewSelectionFromButton(button) {
            if (!button) return { target: null, context: null };
            const jumpKind = button.dataset.finalReviewJump || "";
            const jumpKey = button.dataset.finalReviewKey || "";
            if (typeof getFinalReviewSelection === "function") {
                return getFinalReviewSelection(jumpKind, jumpKey ? { key: jumpKey } : {});
            }
            return {
                target: findFinalReviewTarget(jumpKind),
                context: null,
            };
        }

        function applyAdvancedContextForFinalReviewSelection(selection) {
            if (!selection?.context) return;
            const targetEl = selection.target;
            const targetsAdvanced = targetEl?.closest?.('[data-workspace-scope-panel="advanced"]')
                || targetEl === editorEl;
            if (!targetsAdvanced) return;
            setAdvancedHandoffContext(buildAdvancedHandoffContext(selection.context.step, {
                stepTitle: selection.context.stepTitle || "",
                items: Array.isArray(selection.context.items) ? selection.context.items : [],
                remaining: Number(selection.context.remaining) || 0,
            }));
        }

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

            function guardLocaleStep(label, fn) {
                try {
                    fn();
                } catch (error) {
                    console.warn(`i18n step failed: ${label}`, error);
                }
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
                guardLocaleStep("renderPreferencePresetButtons", () => renderPreferencePresetButtons());
                guardLocaleStep("renderPreferenceBundleButtons", () => renderPreferenceBundleButtons());
                guardLocaleStep("renderKnownPreferenceButtons", () => renderKnownPreferenceButtons());
                guardLocaleStep("renderKnownPreferenceOptions", () => renderKnownPreferenceOptions());
                guardLocaleStep("renderWizardSchemaShell", () => renderWizardSchemaShell());
                guardLocaleStep("buildWizardSettingsSearchIndex", () => buildWizardSettingsSearchIndex());
                guardLocaleStep("renderWizardSettingsSearchResults", () => renderWizardSettingsSearchResults());
                guardLocaleStep("workspaceLocaleRefresh", () => {
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
                    syncWizardNetworkFromEditor();
                    syncWizardPoliciesFromEditor();
                    syncWizardPreferencesFromEditor();
                    syncWizardExtensionsFromEditor();
                    renderAdvancedHandoffContext();
                    syncContextualA11yLabels();
                });
            } catch (e) {
                console.warn("i18n load failed:", e);
            }
        }

        async function applyLanguageMode(mode, persist = true) {
            const normalizedMode = ["system", "en", "ru"].includes(mode) ? mode : "system";
            const resolvedLanguage = normalizedMode === "system"
                ? resolveBrowserLanguage(windowRef.navigator)
                : normalizedMode;
            const requestId = ++localeRequestId;

            documentRef.documentElement.dataset.langMode = normalizedMode;
            langSelectEl.value = normalizedMode;

            if (persist) {
                windowRef.localStorage.setItem(langStorageKey, normalizedMode);
            }

            await loadLocale(resolvedLanguage, requestId);
            await reloadList();
        }

        function debounceReload() {
            const searchTimer = getSearchTimer();
            if (searchTimer) windowRef.clearTimeout(searchTimer);
            setSearchTimer(windowRef.setTimeout(() => {
                setSearchTimer(null);
                reloadList();
            }, 220));
        }

        function applyWorkspaceScope(scope, { persist = true, focus = false } = {}) {
            const normalizedScope = scope === "advanced" ? "advanced" : "guided";
            documentRef.documentElement.dataset.workspaceScope = normalizedScope;
            if (workspaceScopeSummaryEl) {
                workspaceScopeSummaryEl.dataset.workspaceScopeState = normalizedScope;
            }

            [
                { el: workspaceScopeGuidedEl, value: "guided" },
                { el: workspaceScopeAdvancedEl, value: "advanced" },
            ].forEach(({ el, value }) => {
                if (!el) return;
                const isActive = normalizedScope === value;
                el.classList.toggle("workspace-scope-button--active", isActive);
                el.setAttribute("aria-pressed", isActive ? "true" : "false");
            });
            [
                { el: workspaceScopeGuidedCardEl, value: "guided" },
                { el: workspaceScopeAdvancedCardEl, value: "advanced" },
            ].forEach(({ el, value }) => {
                if (!el) return;
                el.classList.toggle("workspace-scope-mode-card--active", normalizedScope === value);
            });
            if (workspaceScopeSummaryTitleEl) {
                const titleKey = normalizedScope === "advanced"
                    ? "profiles.workspace_scope_current_advanced_title"
                    : "profiles.workspace_scope_current_guided_title";
                workspaceScopeSummaryTitleEl.textContent = t(titleKey);
                workspaceScopeSummaryTitleEl.setAttribute("data-i18n", titleKey);
            }
            if (workspaceScopeSummaryCopyEl) {
                const copyKey = normalizedScope === "advanced"
                    ? "profiles.workspace_scope_current_advanced_copy"
                    : "profiles.workspace_scope_current_guided_copy";
                workspaceScopeSummaryCopyEl.textContent = t(copyKey);
                workspaceScopeSummaryCopyEl.setAttribute("data-i18n", copyKey);
            }

            if (persist) {
                windowRef.localStorage.setItem(workspaceScopeStorageKey, normalizedScope);
            }

            if (normalizedScope === "advanced") {
                windowRef.requestAnimationFrame(() => {
                    const editor = getEditor();
                    if (editor && typeof editor.layout === "function") {
                        editor.layout();
                    }
                });
            }

            if (!focus) return;
            const focusTarget = normalizedScope === "advanced"
                ? (documentRef.getElementById("details-panel") || documentRef.getElementById("editor-panel"))
                : (documentRef.getElementById("wizard-panel") || documentRef.getElementById("overview-panel"));
            focusElementForA11y(focusTarget);
            focusTarget?.scrollIntoView({ behavior: "smooth", block: "start" });
        }

        function revealWorkspaceTarget(targetEl) {
            if (!targetEl) return;

            const panel = targetEl.closest(".wizard-panel");
            if (panel?.id?.startsWith("wizard-step-")) {
                const nextStep = Number(panel.id.replace("wizard-step-", ""));
                if (!Number.isNaN(nextStep)) {
                    setWizardStep(nextStep);
                }
            }

            if (targetEl.closest('[data-workspace-scope-panel="advanced"]')) {
                if (openAdvancedRouteFromVisual(null, deriveAdvancedFocusTarget(targetEl))) return;
                applyWorkspaceScope("advanced");
            }
            const homeSurfaceGroup = targetEl.closest("[data-home-surface-group]");
            if (homeSurfaceGroup?.dataset.homeSurfaceCollapsed === "true") {
                homeSurfaceGroup.querySelector("[data-home-surface-toggle]")?.click();
            }
            const disclosurePanel = targetEl.closest(".wizard-disclosure-panel");
            if (disclosurePanel?.hidden) {
                documentRef.querySelector(`[data-wizard-disclosure-toggle][aria-controls="${disclosurePanel.id}"]`)?.click();
            }
            const detailsPanel = targetEl.closest("details");
            if (detailsPanel && !detailsPanel.open) {
                detailsPanel.open = true;
            }
            getDisclosurePanelPairs().forEach(([panelId, toggleId]) => {
                const panelEl = documentRef.getElementById(panelId);
                if (!panelEl || !targetEl.closest(`#${panelId}`) || panelEl.hidden === false) return;
                documentRef.getElementById(toggleId)?.click();
            });
            windowRef.requestAnimationFrame(() => {
                windowRef.requestAnimationFrame(() => {
                    targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
                    targetEl.classList.add("settings-target-highlight");
                    windowRef.setTimeout(() => {
                        targetEl.classList.remove("settings-target-highlight");
                    }, 1800);

                    const focusTarget = targetEl.matches("input, select, textarea, button")
                        ? targetEl
                        : targetEl.querySelector("input, select, textarea, button");
                    focusElementForA11y(focusTarget || targetEl);
                });
            });
        }

        async function copyTextToClipboard(value) {
            const text = String(value || "");
            if (!text.trim()) return false;
            if (windowRef.navigator?.clipboard?.writeText) {
                try {
                    await windowRef.navigator.clipboard.writeText(text);
                    return true;
                } catch (_error) {
                    // Fall back to document copy below.
                }
            }

            const helperEl = documentRef.createElement("textarea");
            helperEl.value = text;
            helperEl.setAttribute("readonly", "readonly");
            helperEl.setAttribute("aria-hidden", "true");
            helperEl.style.position = "fixed";
            helperEl.style.opacity = "0";
            helperEl.style.pointerEvents = "none";
            documentRef.body.appendChild(helperEl);
            helperEl.focus();
            helperEl.select();
            helperEl.setSelectionRange(0, helperEl.value.length);
            let copied = false;
            try {
                copied = Boolean(documentRef.execCommand("copy"));
            } catch (_error) {
                copied = false;
            }
            helperEl.remove();
            return copied;
        }

        function syncEditorBackedUi() {
            syncWizardNetworkFromEditor();
            syncWizardPoliciesFromEditor();
            syncWizardPreferencesFromEditor();
            syncWizardExtensionsFromEditor();
        }

        function syncProxyModeGroupsFromWizard() {
            const activeMode = typeof wizardProxyModeEl?.value === "string"
                ? wizardProxyModeEl.value.trim()
                : "";

            wizardProxyModeGroups.forEach((groupEl) => {
                const supportedModes = String(groupEl?.dataset.proxyModeGroup || "")
                    .split(/\s+/)
                    .map((value) => value.trim())
                    .filter(Boolean);
                const isActive = Boolean(activeMode) && supportedModes.includes(activeMode);
                groupEl.hidden = !isActive;
                groupEl.setAttribute("aria-hidden", isActive ? "false" : "true");
                groupEl.querySelectorAll("input, select, textarea, button").forEach((input) => {
                    input.disabled = !isActive;
                });
            });
        }

        function syncProxyStatusFromWizard() {
            const statusEl = documentRef.getElementById("wizard-proxy-section-status");
            if (!statusEl) return;

            const mode = typeof wizardProxyModeEl?.value === "string"
                ? wizardProxyModeEl.value.trim()
                : "";
            const hasManualEndpoint = [
                wizardProxyHttpEl?.value,
                wizardProxySslEl?.value,
                wizardProxyFtpEl?.value,
                wizardProxySocksEl?.value,
            ].some((value) => typeof value === "string" && value.trim());
            const autoConfigUrl = typeof wizardProxyAutoConfigUrlEl?.value === "string"
                ? wizardProxyAutoConfigUrlEl.value.trim()
                : "";

            if (!mode) {
                statusEl.textContent = t("profiles.wizard_proxy_section_state_empty");
                return;
            }
            if (mode === "none") {
                statusEl.textContent = t("profiles.wizard_proxy_section_state_none");
                return;
            }
            if (mode === "system") {
                statusEl.textContent = t("profiles.wizard_proxy_section_state_system");
                return;
            }
            if (mode === "autoDetect") {
                statusEl.textContent = t("profiles.wizard_proxy_section_state_auto_detect");
                return;
            }
            if (mode === "autoConfig") {
                statusEl.textContent = autoConfigUrl
                    ? t("profiles.wizard_proxy_section_state_auto_config_ready")
                    : t("profiles.wizard_proxy_section_state_auto_config_missing");
                return;
            }
            if (mode === "manual") {
                statusEl.textContent = hasManualEndpoint
                    ? t("profiles.wizard_proxy_section_state_manual_ready")
                    : t("profiles.wizard_proxy_section_state_manual_missing");
            }
        }

        function syncProxyWizardUi() {
            syncProxyModeGroupsFromWizard();
            syncProxyStatusFromWizard();
        }

        function syncSchemaBranchCardFromDom(cardEl) {
            if (!cardEl) return;
            const branchModeEl = cardEl.querySelector("[data-schema-branch-mode]");
            const activeMode = typeof branchModeEl?.value === "string" ? branchModeEl.value.trim() : "";
            cardEl.querySelectorAll("[data-schema-branch-section]").forEach((sectionEl) => {
                const sectionMode = String(sectionEl.dataset.schemaBranchSection || "").trim();
                const isActive = Boolean(activeMode) && sectionMode === activeMode;
                sectionEl.hidden = !isActive;
                sectionEl.setAttribute("aria-hidden", isActive ? "false" : "true");
                sectionEl.querySelectorAll("input, select, textarea, button").forEach((input) => {
                    input.disabled = !isActive;
                });
            });
        }

        function syncAllSchemaBranchCardsFromDom() {
            documentRef.querySelectorAll("[data-schema-policy-kind='branch']").forEach((cardEl) => {
                syncSchemaBranchCardFromDom(cardEl);
            });
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
            ].filter(Boolean).forEach((input) => {
                input.addEventListener("input", applyNetworkFromWizard);
                input.addEventListener("change", applyNetworkFromWizard);
            });

            wizardProxyModeEl?.addEventListener("input", syncProxyWizardUi);
            wizardProxyModeEl?.addEventListener("change", syncProxyWizardUi);
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

        function wireWizardConditionalVisibility() {
            if (wizardConditionalVisibilityBound) return;
            wizardConditionalVisibilityBound = true;

            const handleProxyModeChange = (event) => {
                const target = event.target;
                if (!target || target.id !== "wizard-proxy-mode") return;
                syncProxyWizardUi();
                if (getEditor()) {
                    applyNetworkFromWizard();
                }
            };

            const handleSchemaBranchModeChange = (event) => {
                const target = event.target;
                if (!target || !target.matches("[data-schema-branch-mode]")) return;
                syncSchemaBranchCardFromDom(target.closest("[data-schema-policy-card]"));
            };

            documentRef.addEventListener("input", handleProxyModeChange);
            documentRef.addEventListener("change", handleProxyModeChange);
            documentRef.addEventListener("input", handleSchemaBranchModeChange);
            documentRef.addEventListener("change", handleSchemaBranchModeChange);
        }

        function isGuardedProfileRouteHref(anchorEl) {
            const href = anchorEl?.getAttribute?.("href") || "";
            if (!href || href.startsWith("#")) return false;
            if (anchorEl.target && anchorEl.target !== "_self") return false;
            try {
                const url = new URL(href, windowRef.location.origin);
                if (url.origin !== windowRef.location.origin) return false;
                return url.pathname === "/profiles" || url.pathname.startsWith("/profiles/");
            } catch {
                return false;
            }
        }

        function confirmRouteNavigationIfDirty() {
            if (!currentSnapshotState().dirty) return true;
            return windowRef.confirm(t("profiles.confirm_discard"));
        }

        function guardProfileRouteNavigation(event) {
            const anchorEl = event.target.closest?.("a[href]");
            if (!anchorEl || !isGuardedProfileRouteHref(anchorEl)) return false;
            if (confirmRouteNavigationIfDirty()) return false;
            event.preventDefault();
            event.stopPropagation();
            return true;
        }

        function wireDocumentClicks() {
            if (documentClicksBound) return;
            documentClicksBound = true;

            documentRef.addEventListener("click", (event) => {
                if (guardProfileRouteNavigation(event)) return;

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

                const exportAssistButton = event.target.closest("[data-export-assist-action]");
                if (exportAssistButton) {
                    const action = exportAssistButton.dataset.exportAssistAction || "";
                    if (action === "save") {
                        saveButtonEl.click();
                    } else if (action === "validate") {
                        validateButtonEl.click();
                    } else if (action === "restore") {
                        restoreButtonEl.click();
                    }
                    return;
                }

                const shareableCopyButton = event.target.closest("#wizard-export-shareable-copy");
                if (shareableCopyButton) {
                    copyTextToClipboard(wizardExportShareableTextEl?.value || "").then((copied) => {
                        if (wizardExportShareableStatusEl) {
                            wizardExportShareableStatusEl.textContent = copied
                                ? t("profiles.wizard_export_shareable_status_copied")
                                : t("profiles.wizard_export_shareable_status_failed");
                            wizardExportShareableStatusEl.removeAttribute("data-i18n");
                            wizardExportShareableStatusEl.dataset.summaryTone = copied ? "ready" : "attention";
                        }
                        setStatus(
                            copied
                                ? t("profiles.status_shareable_summary_copied")
                                : t("profiles.wizard_export_shareable_status_failed"),
                            copied ? "success" : "error",
                        );
                    });
                    return;
                }

                const finalReviewJumpButton = event.target.closest("[data-final-review-jump]");
                if (finalReviewJumpButton) {
                    const jumpKind = finalReviewJumpButton.dataset.finalReviewJump || "";
                    const selection = resolveFinalReviewSelectionFromButton(finalReviewJumpButton);
                    const targetEl = selection.target
                        || resolveJumpTargetFallback("final", jumpKind);
                    if (targetEl) {
                        if (targetEl.closest?.('[data-workspace-scope-panel="advanced"]') || targetEl === editorEl) {
                            lastAdvancedReturnTriggerEl = finalReviewJumpButton;
                        }
                        applyAdvancedContextForFinalReviewSelection(selection);
                        revealWorkspaceTarget(targetEl);
                    }
                    return;
                }

                const networkReviewJumpButton = event.target.closest("[data-network-review-jump]");
                if (networkReviewJumpButton) {
                    const jumpKind = networkReviewJumpButton.dataset.networkReviewJump || "";
                    const targetEl = findNetworkReviewTarget(jumpKind)
                        || resolveJumpTargetFallback("final", "network");
                    if (targetEl) {
                        revealWorkspaceTarget(targetEl);
                    }
                    return;
                }

                const homeReviewJumpButton = event.target.closest("[data-home-review-jump]");
                if (homeReviewJumpButton) {
                    const jumpKind = homeReviewJumpButton.dataset.homeReviewJump || "";
                    const targetEl = findHomeReviewTarget(jumpKind)
                        || resolveJumpTargetFallback("final", "home");
                    if (targetEl) {
                        revealWorkspaceTarget(targetEl);
                    }
                    return;
                }

                const searchReviewJumpButton = event.target.closest("[data-search-review-jump]");
                if (searchReviewJumpButton) {
                    const jumpKind = searchReviewJumpButton.dataset.searchReviewJump || "";
                    const targetEl = findSearchReviewTarget(jumpKind)
                        || resolveJumpTargetFallback("search", jumpKind);
                    if (targetEl) {
                        revealWorkspaceTarget(targetEl);
                    }
                    return;
                }

                const aiReviewJumpButton = event.target.closest("[data-ai-review-jump]");
                if (aiReviewJumpButton) {
                    const jumpKind = aiReviewJumpButton.dataset.aiReviewJump || "";
                    const targetEl = findAiReviewTarget(jumpKind)
                        || resolveJumpTargetFallback("ai", jumpKind);
                    if (targetEl) {
                        revealWorkspaceTarget(targetEl);
                    }
                    return;
                }

                const extensionReviewJumpButton = event.target.closest("[data-extension-review-jump]");
                if (extensionReviewJumpButton) {
                    const targetEl = findExtensionReviewTarget(extensionReviewJumpButton.dataset.extensionReviewJump || "");
                    if (targetEl) {
                        revealWorkspaceTarget(targetEl);
                    }
                    return;
                }

                const bookmarkReviewJumpButton = event.target.closest("[data-bookmark-review-jump]");
                if (bookmarkReviewJumpButton) {
                    const targetEl = findBookmarkReviewTarget(bookmarkReviewJumpButton.dataset.bookmarkReviewJump || "");
                    if (targetEl) {
                        revealWorkspaceTarget(targetEl);
                    }
                    return;
                }

                const websiteAccessReviewJumpButton = event.target.closest("[data-website-access-review-jump]");
                if (websiteAccessReviewJumpButton) {
                    const jumpKind = websiteAccessReviewJumpButton.dataset.websiteAccessReviewJump || "";
                    const targetEl = findWebsiteAccessReviewTarget(jumpKind)
                        || resolveJumpTargetFallback("website", jumpKind);
                    if (targetEl) {
                        revealWorkspaceTarget(targetEl);
                    }
                    return;
                }

                const privacyReviewJumpButton = event.target.closest("[data-privacy-review-jump]");
                if (privacyReviewJumpButton) {
                    const jumpKind = privacyReviewJumpButton.dataset.privacyReviewJump || "";
                    const targetEl = findPrivacyReviewTarget(jumpKind)
                        || resolveJumpTargetFallback("privacy", jumpKind);
                    if (targetEl) {
                        revealWorkspaceTarget(targetEl);
                    }
                    return;
                }

                const stepMemoryJumpButton = event.target.closest("[data-step-memory-jump]");
                if (stepMemoryJumpButton) {
                    const nextStep = Number(stepMemoryJumpButton.dataset.stepMemoryJump || "");
                    if (!Number.isNaN(nextStep) && nextStep > 0) {
                        setWizardStep(nextStep);
                        const targetEl = documentRef.getElementById(`wizard-step-${nextStep}`);
                        if (targetEl) {
                            revealWorkspaceTarget(targetEl);
                        }
                    }
                    return;
                }

                const scopeTargetButton = event.target.closest("[data-workspace-scope-target]");
                if (scopeTargetButton) {
                    if ((scopeTargetButton.dataset.workspaceScopeTarget || "guided") === "advanced") {
                        if (openAdvancedRouteFromVisual(event, scopeTargetButton.dataset.advancedFocusTarget || "context")) return;
                        lastAdvancedReturnTriggerEl = scopeTargetButton;
                        setAdvancedHandoffContext(buildAdvancedHandoffContext(getWizardStep()));
                    }
                    applyWorkspaceScope(scopeTargetButton.dataset.workspaceScopeTarget || "guided", { focus: true });
                    return;
                }

                const advancedStartActionButton = event.target.closest("[data-advanced-start-action]");
                if (advancedStartActionButton) {
                    const action = advancedStartActionButton.dataset.advancedStartAction || "";
                    if (action === "details") {
                        if (openAdvancedRouteFromVisual(event, "details")) return;
                        applyWorkspaceScope("advanced", { focus: true });
                        const targetEl = documentRef.getElementById("details-panel");
                        if (targetEl) {
                            targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
                            focusElementForA11y(targetEl);
                        }
                    } else if (action === "editor") {
                        if (openAdvancedRouteFromVisual(event, "editor")) return;
                        applyWorkspaceScope("advanced", { focus: true });
                        const targetEl = documentRef.getElementById("editor-panel");
                        if (targetEl) {
                            targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
                            focusElementForA11y(targetEl);
                        }
                    } else if (action === "validate") {
                        validateButtonEl.click();
                    }
                    return;
                }

                if (event.target.closest("#advanced-context-return")) {
                    const step = Number(advancedContextReturnEl?.dataset.advancedReturnStep || 0);
                    if (step > 0) {
                        setWizardStep(step);
                        applyWorkspaceScope("guided", { focus: true });
                        const targetEl = documentRef.getElementById(`wizard-step-${step}`);
                        if (targetEl) {
                            windowRef.requestAnimationFrame(() => {
                                targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
                                if (lastAdvancedReturnTriggerEl && documentRef.contains(lastAdvancedReturnTriggerEl)) {
                                    focusElementForA11y(lastAdvancedReturnTriggerEl);
                                } else {
                                    focusElementForA11y(targetEl);
                                }
                            });
                        }
                    } else {
                        applyWorkspaceScope("guided", { focus: true });
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
                        revealWorkspaceTarget(targetEl);
                    }
                    return;
                }

                const shellJumpButton = event.target.closest("[data-wizard-shell-jump]");
                if (shellJumpButton) {
                    const targetEl = findSettingsTarget(shellJumpButton.dataset.settingsJumpTarget || "");
                    if (targetEl) {
                        revealWorkspaceTarget(targetEl);
                    }
                    return;
                }

                const shellTargetButton = event.target.closest("[data-wizard-shell-target]");
                if (shellTargetButton) {
                    revealWorkspaceTarget(shellTargetButton);
                    return;
                }

                const schemaArrayAddButton = event.target.closest("[data-schema-array-add]");
                if (schemaArrayAddButton) {
                    appendSchemaArrayItem(schemaArrayAddButton.closest("[data-schema-policy-card]"));
                    return;
                }

                const schemaListAddButton = event.target.closest("[data-schema-list-add]");
                if (schemaListAddButton) {
                    const container = schemaListAddButton.closest("[data-schema-policy-field], [data-schema-nested-field]");
                    const card = schemaListAddButton.closest("[data-schema-policy-card]");
                    appendSchemaListItem(container);
                    if (card) {
                        renderSchemaPolicyReviewState(card);
                        applySchemaPolicyFromCard(card);
                    }
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

                const schemaListRemoveButton = event.target.closest("[data-schema-list-remove]");
                if (schemaListRemoveButton) {
                    const row = schemaListRemoveButton.closest("[data-schema-list-row]");
                    const container = schemaListRemoveButton.closest("[data-schema-policy-field], [data-schema-nested-field]");
                    const card = schemaListRemoveButton.closest("[data-schema-policy-card]");
                    removeSchemaListItem(container, row);
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
                        revealWorkspaceTarget(targetEl);
                    }
                }
            });

            documentRef.addEventListener("click", () => {
                windowRef.requestAnimationFrame(() => {
                    syncContextualA11yLabels();
                });
            });
        }

        function resolveJumpTargetFallback(group, kind) {
            const first = (...selectors) => {
                for (const selector of selectors) {
                    const match = documentRef.querySelector(selector);
                    if (match) return match;
                }
                return null;
            };

            if (group === "final") {
                if (kind === "network") {
                    return first(
                        '[data-settings-target="field:wizard-proxy-mode"]',
                        '#wizard-dns-over-https-card',
                        '#wizard-authentication-card',
                        '#wizard-certificates-card',
                        '#wizard-windows-sso-card',
                    );
                }
                if (kind === "home") {
                    return first(
                        '[data-settings-target="field:wizard-homepage-url"]',
                        '[data-settings-target="field:wizard-override-first-run"]',
                        '[data-settings-target="field:firefox-home-search"]',
                        '#wizard-user-messaging-card',
                    );
                }
                if (kind === "search") {
                    return first(
                        '[data-settings-target="field:wizard-search-default-engine"]',
                        '[data-settings-target="field:wizard-search-remove"]',
                        '[data-settings-target="field:firefox-suggest-web"]',
                    );
                }
                if (kind === "features") {
                    return first(
                        '[data-settings-target="policy:RequestedLocales"]',
                        '[data-settings-target="policy:TranslateEnabled"]',
                        '[data-settings-target="field:wizard-extension-default-mode"]',
                        '[data-settings-target="policy:WebsiteFilter"]',
                    );
                }
                if (kind === "ai") {
                    return first(
                        '[data-settings-target="policy:AIControls"]',
                        '[data-settings-target="policy:VisualSearchEnabled"]',
                        '[data-settings-target="policy:GenerativeAI"]',
                    );
                }
                if (kind === "privacy") {
                    return first(
                        '[data-settings-target="policy:IPProtectionAvailable"]',
                        '[data-settings-target="policy:Permissions"]',
                        '[data-settings-target="policy:Cookies"]',
                    );
                }
            }

            if (group === "search") {
                if (kind === "defaults") {
                    return first('[data-settings-target="field:wizard-search-default-engine"]');
                }
                if (kind === "hidden") {
                    return first('[data-settings-target="field:wizard-search-remove"]');
                }
                if (kind === "suggest") {
                    return first('[data-settings-target="field:firefox-suggest-web"]');
                }
            }

            if (group === "privacy") {
                if (kind === "permissions") {
                    return first('[data-settings-target="policy:Permissions"]');
                }
                if (kind === "cookies") {
                    return first('[data-settings-target="policy:Cookies"]');
                }
            }

            if (group === "website") {
                if (kind === "blocked_sites" || kind === "exceptions") {
                    return first('[data-settings-target="policy:WebsiteFilter"]');
                }
                if (kind === "handlers") {
                    return first('[data-settings-target="policy:Handlers"]', '[data-settings-target="shell-policy:6:Handlers"]');
                }
            }

            if (group === "ai") {
                if (kind === "feature_controls") {
                    return first('[data-settings-target="policy:AIControls"]', '[data-settings-target="policy:GenerativeAI"]');
                }
                if (kind === "visual_search") {
                    return first('[data-settings-target="policy:VisualSearchEnabled"]');
                }
                if (kind === "generative_ai") {
                    return first('[data-settings-target="policy:AIControls"]', '[data-settings-target="policy:GenerativeAI"]');
                }
            }

            return null;
        }

        function bindJumpButtons() {
            if (jumpButtonsBound) return;
            jumpButtonsBound = true;

            const bind = (selector, resolveTarget) => {
                documentRef.querySelectorAll(selector).forEach((button) => {
                    button.addEventListener("click", (event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        const targetEl = resolveTarget(button);
                        if (targetEl) {
                            revealWorkspaceTarget(targetEl);
                        }
                    });
                });
            };

            const bindDirectJump = (buttonId, targetSelector) => {
                const button = documentRef.getElementById(buttonId);
                if (!button) return;
                button.addEventListener("click", (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    const targetEl = documentRef.querySelector(targetSelector);
                    if (targetEl) {
                        revealWorkspaceTarget(targetEl);
                    }
                });
            };

            bind("[data-final-review-jump]", (button) =>
                resolveFinalReviewSelectionFromButton(button).target
                || resolveJumpTargetFallback("final", button.dataset.finalReviewJump || ""),
            );
            bind("[data-network-review-jump]", (button) =>
                findNetworkReviewTarget(button.dataset.networkReviewJump || ""),
            );
            bind("[data-home-review-jump]", (button) =>
                findHomeReviewTarget(button.dataset.homeReviewJump || ""),
            );
            bind("[data-search-review-jump]", (button) =>
                findSearchReviewTarget(button.dataset.searchReviewJump || "")
                || resolveJumpTargetFallback("search", button.dataset.searchReviewJump || ""),
            );
            bind("[data-ai-review-jump]", (button) =>
                findAiReviewTarget(button.dataset.aiReviewJump || "")
                || resolveJumpTargetFallback("ai", button.dataset.aiReviewJump || ""),
            );
            bind("[data-extension-review-jump]", (button) =>
                findExtensionReviewTarget(button.dataset.extensionReviewJump || ""),
            );
            bind("[data-bookmark-review-jump]", (button) =>
                findBookmarkReviewTarget(button.dataset.bookmarkReviewJump || ""),
            );
            bind("[data-website-access-review-jump]", (button) =>
                findWebsiteAccessReviewTarget(button.dataset.websiteAccessReviewJump || "")
                || resolveJumpTargetFallback("website", button.dataset.websiteAccessReviewJump || ""),
            );
            bind("[data-privacy-review-jump]", (button) =>
                findPrivacyReviewTarget(button.dataset.privacyReviewJump || "")
                || resolveJumpTargetFallback("privacy", button.dataset.privacyReviewJump || ""),
            );

            bindDirectJump("wizard-export-summary-network-jump", '[data-settings-target="field:wizard-proxy-mode"]');
            bindDirectJump("wizard-export-summary-home-jump", '[data-settings-target="field:wizard-homepage-url"]');
            bindDirectJump("wizard-export-summary-search-jump", '[data-settings-target="field:wizard-search-default-engine"]');
            bindDirectJump("wizard-export-summary-features-jump", '[data-settings-target="policy:RequestedLocales"]');
            bindDirectJump("wizard-export-summary-ai-jump", '[data-settings-target="policy:AIControls"]', '[data-settings-target="policy:VisualSearchEnabled"]');
            bindDirectJump("wizard-export-summary-privacy-jump", '[data-settings-target="policy:Permissions"]');
            bindDirectJump("wizard-extension-next-rollout", "#wizard-extension-governance-presets");
            bindDirectJump("wizard-extension-next-curated", "#wizard-extension-curated-section");
            bindDirectJump("wizard-extension-next-fine-tuning", "#wizard-extension-fine-tuning-toggle");
            bindDirectJump("wizard-website-next-filter", '[data-settings-target="policy:WebsiteFilter"]');
            bindDirectJump("wizard-website-next-handlers", '[data-settings-target="policy:Handlers"]');
            bindDirectJump("wizard-website-next-fine-tuning", "#wizard-website-fine-tuning-toggle");
        }

        function wireDisclosureEscape() {
            documentRef.addEventListener("keydown", (event) => {
                if (event.key !== "Escape" || event.defaultPrevented) return;

                const activeEl = documentRef.activeElement;
                const openPair = getDisclosurePanelPairs().find(([panelId]) => {
                    const panelEl = documentRef.getElementById(panelId);
                    return panelEl && panelEl.hidden === false && activeEl && panelEl.contains(activeEl);
                });
                if (!openPair) return;

                const [panelId, toggleId] = openPair;
                const panelEl = documentRef.getElementById(panelId);
                const toggleEl = documentRef.getElementById(toggleId);
                if (!panelEl || !toggleEl) return;

                event.preventDefault();
                toggleEl.click();
                windowRef.requestAnimationFrame(() => {
                    focusElementForA11y(toggleEl);
                });
            });
        }

        function bindCoreControls() {
            langSelectEl?.addEventListener("change", async (event) => {
                await applyLanguageMode(event.target.value);
            });
            themeSelectEl?.addEventListener("change", (event) => {
                applyThemeMode(event.target.value);
            });
            refreshButtonEl?.addEventListener("click", reloadList);
            searchInputEl?.addEventListener("input", debounceReload);
            sortSelectEl?.addEventListener("change", reloadList);
            orderSelectEl?.addEventListener("change", reloadList);
            includeDeletedEl?.addEventListener("change", reloadList);
        }

        function bindWizardNavigation() {
            if (wizardNavBound) return;
            wizardNavBound = true;

            function scrollWizardStepToTop(stepNumber) {
                const targetEl = documentRef.getElementById(`wizard-step-${Number(stepNumber)}`);
                if (!targetEl) return;
                windowRef.requestAnimationFrame(() => {
                    targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
                    focusElementForA11y(targetEl);
                });
            }

            function navigateWizardStep(nextStep) {
                setWizardStep(nextStep);
                scrollWizardStepToTop(getWizardStep());
            }

            wizardStepButtons.forEach((button) => {
                button.addEventListener("click", () => navigateWizardStep(button.dataset.step));
            });
            wizardPrevEl?.addEventListener("click", () => navigateWizardStep(getWizardStep() - 1));
            wizardNextEl?.addEventListener("click", () => {
                navigateWizardStep(getWizardStep() + 1);
            });
            wizardFinishEl?.addEventListener("click", finishWizard);
            wizardStepUndoEl?.addEventListener("click", () => {
                undoCurrentStepChanges();
            });
            wizardStepResetEl?.addEventListener("click", () => {
                resetCurrentStepToBaseline();
            });
        }

        async function initializeShellState() {
            const legacySavedLang = windowRef.localStorage.getItem("bpm-lang");
            const savedLangMode = windowRef.localStorage.getItem(langStorageKey) || legacySavedLang || "system";
            const savedThemeMode = windowRef.localStorage.getItem(themeStorageKey) || "system";
            const savedWorkspaceScope = windowRef.localStorage.getItem(workspaceScopeStorageKey) || "guided";
            const routeMode = readProfilesRouteContext().routeMode;
            const initialWorkspaceScope = routeMode === "advanced" ? "advanced" : (
                savedWorkspaceScope === "advanced" ? "guided" : savedWorkspaceScope
            );

            if (langSelectEl) {
                langSelectEl.value = savedLangMode;
            }
            if (themeSelectEl) {
                themeSelectEl.value = savedThemeMode;
            }

            applyThemeMode(savedThemeMode, false);
            applyWorkspaceScope(initialWorkspaceScope, { persist: false });
            await applyLanguageMode(savedLangMode, false);
        }

        function readProfilesRouteContext() {
            const bodyEl = documentRef.body;
            const routeMode = bodyEl?.dataset.profilesRouteMode || "library";
            const rawProfileId = bodyEl?.dataset.editingProfileId || "";
            const profileId = Number(rawProfileId);
            return {
                routeMode,
                editingProfileId: Number.isInteger(profileId) && profileId > 0 ? profileId : null,
                returnUrl: bodyEl?.dataset.advancedReturnUrl || "",
                focusTarget: bodyEl?.dataset.advancedFocusTarget || "",
            };
        }

        function buildAdvancedRouteHref(profileId, focusTarget = "") {
            if (!profileId) return "";
            const href = new URL(`/profiles/${profileId}/advanced`, windowRef.location.origin);
            href.searchParams.set("return", `/profiles/${profileId}/edit`);
            if (focusTarget) {
                href.searchParams.set("focus", focusTarget);
            }
            return `${href.pathname}${href.search}`;
        }

        function getAdvancedRouteHref(focusTarget = "") {
            const { editingProfileId } = readProfilesRouteContext();
            const profileId = editingProfileId || getCurrentProfile()?.id || null;
            return buildAdvancedRouteHref(profileId, focusTarget);
        }

        function deriveAdvancedFocusTarget(targetEl, fallback = "") {
            if (!targetEl) return fallback;
            const settingsTarget = targetEl.closest?.("[data-settings-target]")?.dataset.settingsTarget || "";
            if (settingsTarget) return settingsTarget;
            if (targetEl === editorEl || targetEl.id === "editor" || targetEl.id === "editor-panel") return "editor";
            if (targetEl.id === "details-panel") return "details";
            if (targetEl.id === "advanced-download-strip") return "download";
            if (targetEl.id === "advanced-context-panel") return "context";
            if (targetEl.id) return targetEl.id;
            return targetEl.closest?.("[id]")?.id || fallback;
        }

        function openAdvancedRouteFromVisual(event = null, focusTarget = "") {
            const { routeMode } = readProfilesRouteContext();
            if (routeMode === "advanced") return false;
            event?.preventDefault?.();
            const href = getAdvancedRouteHref(focusTarget);
            if (!href) {
                setStatus(t("profiles.wizard_export_plan_save_first"), "warn");
                return true;
            }
            if (!confirmRouteNavigationIfDirty()) {
                return true;
            }
            windowRef.location.assign(href);
            return true;
        }

        function resolveAdvancedFocusTarget(focusTarget) {
            const target = String(focusTarget || "").trim();
            if (!target) return null;
            if (target === "editor") return documentRef.getElementById("editor-panel") || editorEl;
            if (target === "details") return documentRef.getElementById("details-panel");
            if (target === "download") return documentRef.getElementById("advanced-download-strip");
            if (target === "context") return documentRef.getElementById("advanced-context-panel");
            return findSettingsTarget(target) || documentRef.getElementById(target) || null;
        }

        function applyAdvancedFocusTarget(focusTarget) {
            const targetEl = resolveAdvancedFocusTarget(focusTarget);
            if (!targetEl) return;
            revealWorkspaceTarget(targetEl);
        }

        async function bootstrapProfileRouteState() {
            const { routeMode, editingProfileId, focusTarget } = readProfilesRouteContext();
            if ((routeMode === "edit" || routeMode === "advanced") && editingProfileId) {
                await resetDraft(true);
                await loadProfile(editingProfileId, { skipConfirm: true });
                if (routeMode === "advanced") {
                    setAdvancedHandoffContext(null);
                    applyWorkspaceScope("advanced", { focus: true, persist: false });
                    applyAdvancedFocusTarget(focusTarget);
                }
                return;
            }

            await resetDraft(true);
            await reloadList();
        }

        function start() {
            // Keep the library usable even if Monaco initialization is slow or fails.
            bindCoreControls();
            bindWizardNavigation();
            wireWizardConditionalVisibility();
            wireDocumentClicks();
            syncProxyWizardUi();
            const shellReady = initializeShellState().catch((error) => {
                console.warn("shell initialization failed", error);
            });

            const monacoReady = windowRef.__BPM_MONACO_READY__;
            if (!monacoReady || typeof monacoReady.then !== "function") {
                setStatus(t("profiles.error_loading").replace("{detail}", "Monaco bundle is not ready"), "error");
                return;
            }

            monacoReady.then(async (monacoRef) => {
                await shellReady;
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

                const savedMode = "json";
                let activeEditorMode = savedMode;

                modeSelectEl.value = savedMode;
                windowRef.localStorage.setItem("bpm-editor-mode", savedMode);
                monacoRef.editor.setModelLanguage(editor.getModel(), "json");
                editor.setValue(toEditorValue({}, savedMode));
                syncProxyWizardUi();
                syncWizardFieldsFromForm();
                syncEditorBackedUi();
                setWizardStep(1);

                formatButtonEl.addEventListener("click", () => {
                    try {
                        const mode = modeSelectEl.value;
                        const parsed = fromEditorValue(editor.getValue(), mode);
                        editor.setValue(toEditorValue(parsed, mode));
                        setStatus(t("profiles.editor_formatted"), "success");
                    } catch (e) {
                        setStatus(t("profiles.error_format").replace("{detail}", e.message || e), "error");
                    }
                });

                modeSelectEl.addEventListener("change", (event) => {
                    const mode = event.target.value;
                    let currentFlags = getCurrentRaw();
                    try {
                        currentFlags = fromEditorValue(editor.getValue(), activeEditorMode);
                    } catch {
                        currentFlags = getCurrentRaw();
                    }
                    windowRef.localStorage.setItem("bpm-editor-mode", mode);
                    monacoRef.editor.setModelLanguage(editor.getModel(), mode === "yaml" ? "yaml" : "json");
                    editor.setValue(toEditorValue(currentFlags, mode));
                    activeEditorMode = mode;
                    syncWizardFieldsFromForm();
                    syncEditorBackedUi();
                    syncAllSchemaBranchCardsFromDom();
                    syncWorkspaceOverview();
                    setStatus(t("profiles.editor_mode_switched").replace("{mode}", mode.toUpperCase()), "info");
                });

                saveButtonEl.addEventListener("click", saveCurrent);
                newProfileButtonEl?.addEventListener("click", resetDraft);
                softDeleteButtonEl.addEventListener("click", doSoftDelete);
                hardDeleteButtonEl.addEventListener("click", doHardDelete);
                restoreButtonEl.addEventListener("click", doRestore);
                resetLibraryButtonEl.addEventListener("click", doResetLibrary);
                validateButtonEl.addEventListener("click", doValidate);
                importFirefoxPoliciesButtonEl?.addEventListener("click", () => {
                    importFirefoxPoliciesFileEl?.click();
                });
                importFirefoxPoliciesFileEl?.addEventListener("change", async (event) => {
                    const file = event.target.files?.[0] || null;
                    await doImportFirefoxPoliciesJson?.(file);
                });
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
                    syncAllSchemaBranchCardsFromDom();
                    updateActionState();
                });

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
                wizardScenarioButtons.forEach((button) => {
                    button.addEventListener("click", () => {
                        applyScenarioPreset(button.dataset.scenarioKey);
                    });
                    button.addEventListener("mouseenter", () => {
                        setPreviewStarter(button.dataset.scenarioKey ? ({
                            shared_devices: "classroom_kiosk",
                            hardened: "soc_hard",
                            extension_rollout: "basic_corporate",
                            targeted_edits: getCurrentProfile()?.id ? "keep_current" : "blank",
                            corporate_default: "basic_corporate",
                        }[button.dataset.scenarioKey] || "basic_corporate") : "basic_corporate");
                    });
                    button.addEventListener("focus", () => {
                        setPreviewStarter(button.dataset.scenarioKey ? ({
                            shared_devices: "classroom_kiosk",
                            hardened: "soc_hard",
                            extension_rollout: "basic_corporate",
                            targeted_edits: getCurrentProfile()?.id ? "keep_current" : "blank",
                            corporate_default: "basic_corporate",
                        }[button.dataset.scenarioKey] || "basic_corporate") : "basic_corporate");
                    });
                    button.addEventListener("mouseleave", clearPreviewStarter);
                    button.addEventListener("blur", clearPreviewStarter);
                });
                wizardStarterButtons.forEach((button) => {
                    button.addEventListener("click", () => {
                        applyStarterPreset(button.dataset.starterKey);
                    });
                    button.addEventListener("mouseenter", () => {
                        setPreviewStarter(button.dataset.starterKey);
                    });
                    button.addEventListener("focus", () => {
                        setPreviewStarter(button.dataset.starterKey);
                    });
                    button.addEventListener("mouseleave", clearPreviewStarter);
                    button.addEventListener("blur", clearPreviewStarter);
                });
                wizardCisLayerButtons.forEach((button) => {
                    button.addEventListener("click", () => {
                        setWizardComplianceLayer(button.dataset.cisLayerKey);
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
                        revealWorkspaceTarget(targetEl);
                    }
                });
                wizardSettingsSearchClearEl?.addEventListener("click", () => {
                    clearWizardSettingsSearch();
                    wizardSettingsSearchInputEl?.focus();
                });
                workspaceScopeGuidedEl?.addEventListener("click", () => {
                    setAdvancedHandoffContext(null);
                    applyWorkspaceScope("guided", { focus: true });
                });
                workspaceScopeAdvancedEl?.addEventListener("click", (event) => {
                    if (openAdvancedRouteFromVisual(event, "context")) return;
                    setAdvancedHandoffContext(null);
                    applyWorkspaceScope("advanced", { focus: true });
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
                wireWizardConditionalVisibility();
                wireCompositeButtonNavigation();
                wireDisclosureEscape();
                bindJumpButtons();
                if (wizardProxyModeEl) {
                    wizardProxyModeEl.oninput = syncProxyWizardUi;
                    wizardProxyModeEl.onchange = syncProxyWizardUi;
                }
                syncProxyWizardUi();
                syncAllSchemaBranchCardsFromDom();
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
                    try {
                        applySettingsFilter(navEl, "all");
                    } catch (error) {
                        console.warn("settings filter init failed", error);
                    }
                });
                wireSchemaEvents();
                syncContextualA11yLabels();

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

                await bootstrapProfileRouteState();
                updateDownloadLinks();
                syncWorkspaceOverview();
            }).catch((error) => {
                setStatus(t("profiles.error_loading").replace("{detail}", error?.message || error), "error");
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
