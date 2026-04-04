(() => {
    function create({
        documentRef = document,
        windowRef = window,
        elements = {},
        dependencies = {},
        state = {},
    }) {
        const {
            t,
            formatSchemaLabel,
            getDefaultSchemaVersion,
            libraryCountLabel,
            toEditorValue,
            fromEditorValue,
            listProfiles,
            getProfileLibraryStats,
            getProfile,
            createProfile,
            patchProfile,
            softDeleteProfile,
            hardDeleteProfile,
            restoreProfile,
            resetProfilesLibrary,
            validateFlags,
            renderFinalExportStepSummary,
            updateWizardSummary,
            setWorkspaceHelper,
            syncWizardFieldsFromForm,
            updateWizardContext,
            setWizardStarter,
            markWizardBaselineSnapshot,
            renderCurrentStepActions,
            syncWizardNetworkFromEditor,
            syncWizardPreferencesFromEditor,
            syncWizardExtensionsFromEditor,
            syncWizardPoliciesFromEditor,
            setWizardStep,
            getWizardStep,
            setStatus,
        } = dependencies;

        const getEditor = state.getEditor || (() => null);
        const getCurrentId = state.getCurrentId || (() => null);
        const setCurrentId = state.setCurrentId || (() => {});
        const getCurrentProfile = state.getCurrentProfile || (() => null);
        const setCurrentProfile = state.setCurrentProfile || (() => {});
        const getCloneSourceProfile = state.getCloneSourceProfile || (() => null);
        const setCloneSourceProfile = state.setCloneSourceProfile || (() => {});
        const getLifecycleSessionNote = state.getLifecycleSessionNote || (() => null);
        const setLifecycleSessionNote = state.setLifecycleSessionNote || (() => {});
        const getCurrentRaw = state.getCurrentRaw || (() => ({}));
        const setCurrentRaw = state.setCurrentRaw || (() => {});
        const getCurrentLang = state.getCurrentLang || (() => "en");
        const getIsBusy = state.getIsBusy || (() => false);
        const setIsBusy = state.setIsBusy || (() => {});
        const getBaselineSnapshot = state.getBaselineSnapshot || (() => null);
        const setBaselineSnapshot = state.setBaselineSnapshot || (() => {});
        const getLibraryStats = state.getLibraryStats || (() => ({ filtered: 0, total: 0 }));
        const setLibraryStats = state.setLibraryStats || (() => {});
        const setValidationPreviewTone = state.setValidationPreviewTone || (() => {});

        const {
            listEl,
            listSummaryEl,
            listTotalSummaryEl,
            compareClearEl,
            compareEmptyEl,
            compareEmptyCopyEl,
            compareActiveEl,
            compareCurrentNameEl,
            compareCurrentCopyEl,
            compareOtherNameEl,
            compareOtherCopyEl,
            compareMetadataCountEl,
            comparePolicyCountEl,
            comparePreferenceCountEl,
            compareChangesCopyEl,
            compareChangesListEl,
            compareGuidedAreasCopyEl,
            compareGuidedAreasListEl,
            nameInput,
            ownerInput,
            descriptionInput,
            nameHintEl,
            currentNameEl,
            currentMetaEl,
            profileDerivedNoteEl,
            profileCloneHandoffPanelEl,
            profileCloneHandoffCopyEl,
            profileCloneHandoffListEl,
            profileLifecycleCopyEl,
            profileLifecycleListEl,
            stateBadgeEl,
            workspaceProfileCountEl,
            workspaceSignalEl,
            validationPreviewEl,
            saveButtonEl,
            deleteButtonEl,
            hardDeleteButtonEl,
            restoreButtonEl,
            resetLibraryButtonEl,
            validateButtonEl,
            refreshButtonEl,
            overviewSchemaEl,
            overviewModeEl,
            overviewStatusEl,
            overviewContextEl,
            dockStatusTextEl,
            dockStateSummaryEl,
            dockStateTitleEl,
            dockStateCopyEl,
            wizardExportSaveActionEl,
            wizardExportValidateActionEl,
            wizardExportReadyCardEl,
            wizardExportJsonEl,
            wizardExportYamlEl,
            wizardExportFirefoxPoliciesEl,
            advancedReviewStripEl,
            advancedReviewSaveStateEl,
            advancedReviewValidationStateEl,
            advancedReviewDownloadStateEl,
            wizardFinishEl,
            wizardSummaryLifecycleListEl,
            wizardCloneHandoffPanelEl,
            wizardCloneHandoffCopyEl,
            wizardCloneHandoffListEl,
        } = elements;
        const overviewPanelEl = documentRef.getElementById("overview-panel");
        const commandDeckEl = documentRef.getElementById("command-deck");
        const defaultSchemaVersion = getDefaultSchemaVersion(documentRef);
        let compareProfileState = null;

        function setSelectionUiState(nextState) {
            [overviewPanelEl, commandDeckEl].forEach((el) => {
                if (!el) return;
                el.classList.toggle("selection-state-panel--empty", nextState === "empty");
                el.classList.toggle("selection-state-panel--draft", nextState === "draft");
                el.classList.toggle("selection-state-panel--active", nextState === "active");
                el.classList.toggle("selection-state-panel--archived", nextState === "archived");
            });
        }

        function setWorkflowStateUi(nextState) {
            [commandDeckEl, wizardExportReadyCardEl].forEach((el) => {
                if (!el) return;
                el.dataset.workflowState = nextState;
            });
        }

        function getCloneSourceLabel(sourceProfile = getCloneSourceProfile()) {
            if (!sourceProfile?.name) return "";
            return t("profiles.clone_source_value")
                .replace("{name}", sourceProfile.name);
        }

        function renderCloneContext() {
            const cloneLabel = getCloneSourceLabel();
            if (profileDerivedNoteEl) {
                profileDerivedNoteEl.hidden = !cloneLabel;
                profileDerivedNoteEl.textContent = cloneLabel;
            }
        }

        function buildCloneHandoffItems() {
            const cloneSource = getCloneSourceProfile();
            if (!cloneSource?.name) return [];

            const raw = getCurrentRaw();
            const items = [];
            const pushItem = (label, action) => items.push({ label, action });

            pushItem(
                t("profiles.clone_handoff_item_identity"),
                { kind: "step", value: 1, label: t("profiles.clone_handoff_open_step") },
            );

            const hasHomeSurface = Boolean(
                raw?.Homepage
                || raw?.NewTabPage !== undefined
                || raw?.OverrideFirstRunPage
                || raw?.OverridePostUpdatePage
                || raw?.FirefoxHome,
            );
            if (hasHomeSurface) {
                pushItem(
                    t("profiles.clone_handoff_item_home"),
                    { kind: "step", value: 3, label: t("profiles.clone_handoff_open_step") },
                );
            }

            const hasPrivacySurface = Boolean(
                raw?.DisableTelemetry !== undefined
                || raw?.DisableFirefoxStudies !== undefined
                || raw?.DisablePrivateBrowsing !== undefined
                || raw?.OfferToSaveLogins !== undefined
                || raw?.PasswordManagerEnabled !== undefined
                || raw?.SanitizeOnShutdown
                || raw?.Permissions
                || raw?.Cookies,
            );
            if (hasPrivacySurface) {
                pushItem(
                    t("profiles.clone_handoff_item_privacy"),
                    { kind: "step", value: 5, label: t("profiles.clone_handoff_open_step") },
                );
            }

            const hasFeatureSurface = Boolean(
                raw?.ExtensionSettings
                || raw?.InstallAddonsPermission
                || raw?.WebsiteFilter
                || raw?.Handlers
                || raw?.RequestedLocales
                || raw?.TranslateEnabled !== undefined
                || raw?.DisableFirefoxAccounts !== undefined
                || raw?.UserMessaging,
            );
            if (hasFeatureSurface) {
                pushItem(
                    t("profiles.clone_handoff_item_features"),
                    { kind: "step", value: 6, label: t("profiles.clone_handoff_open_step") },
                );
            }

            pushItem(
                t("profiles.clone_handoff_item_compare").replace("{name}", cloneSource.name),
                { kind: "compare", value: cloneSource.id, label: t("profiles.clone_handoff_compare") },
            );

            return items.slice(0, 4);
        }

        function renderCloneHandoffPanel() {
            const cloneSource = getCloneSourceProfile();
            const visible = Boolean(cloneSource?.name);
            const items = buildCloneHandoffItems();
            const renderItems = (listEl) => {
                if (!listEl) return;
                listEl.innerHTML = items.map((item) => {
                    const attrs = item.action?.kind === "compare"
                        ? `data-clone-handoff-compare="${String(item.action.value || "")}"`
                        : `data-clone-handoff-step="${String(item.action?.value || "")}"`;
                    const describedById = listEl.id === "wizard-clone-handoff-list"
                        ? "wizard-clone-handoff-copy"
                        : "profile-clone-handoff-copy";
                    const ariaLabel = [item.action?.label || "", item.label].filter(Boolean).join(". ");
                    return `<div class="wizard-export-plan-item" data-plan-tone="default" role="listitem"><div class="wizard-export-plan-copy">${item.label}</div><button type="button" class="button-base ghost-button wizard-export-plan-action" aria-label="${escapeHtml(ariaLabel)}" aria-describedby="${describedById}" ${attrs}>${item.action?.label || ""}</button></div>`;
                }).join("");
            };

            [profileCloneHandoffPanelEl, wizardCloneHandoffPanelEl].forEach((panelEl) => {
                if (panelEl) {
                    panelEl.hidden = !visible;
                }
            });
            if (profileCloneHandoffCopyEl) {
                profileCloneHandoffCopyEl.textContent = visible
                    ? t("profiles.clone_handoff_active").replace("{name}", cloneSource.name)
                    : t("profiles.clone_handoff_body");
            }
            if (wizardCloneHandoffCopyEl) {
                wizardCloneHandoffCopyEl.textContent = visible
                    ? t("profiles.clone_handoff_active").replace("{name}", cloneSource.name)
                    : t("profiles.clone_handoff_body");
            }
            renderItems(profileCloneHandoffListEl);
            renderItems(wizardCloneHandoffListEl);
        }

        function buildLifecycleReviewItems() {
            const currentProfile = getCurrentProfile();
            const cloneSource = getCloneSourceProfile();
            const sessionNote = getLifecycleSessionNote();
            const items = [];

            items.push({
                title: t("profiles.lifecycle_item_created"),
                copy: currentProfile?.created_at
                    ? t("profiles.lifecycle_item_created_value").replace("{value}", formatTimestamp(currentProfile.created_at))
                    : t("profiles.lifecycle_item_created_draft"),
                tone: currentProfile?.created_at ? "ready" : "default",
            });

            items.push({
                title: t("profiles.lifecycle_item_saved"),
                copy: currentProfile?.updated_at
                    ? t("profiles.lifecycle_item_saved_value").replace("{value}", formatTimestamp(currentProfile.updated_at))
                    : t("profiles.lifecycle_item_saved_draft"),
                tone: currentProfile?.updated_at ? "ready" : "default",
            });

            items.push({
                title: t("profiles.lifecycle_item_state"),
                copy: currentProfile?.is_deleted
                    ? t("profiles.lifecycle_item_state_archived")
                    : (getCurrentId()
                        ? t("profiles.lifecycle_item_state_saved")
                        : (cloneSource?.name
                            ? t("profiles.lifecycle_item_state_clone_draft")
                            : t("profiles.lifecycle_item_state_new_draft"))),
                tone: currentProfile?.is_deleted ? "strict" : (getCurrentId() ? "ready" : "default"),
            });

            items.push({
                title: t("profiles.lifecycle_item_origin"),
                copy: cloneSource?.name
                    ? t("profiles.lifecycle_item_origin_clone").replace("{name}", cloneSource.name)
                    : t("profiles.lifecycle_item_origin_independent"),
                tone: cloneSource?.name ? "ready" : "default",
            });

            if (sessionNote?.type === "restored" && sessionNote.profileId === getCurrentId()) {
                items.push({
                    title: t("profiles.lifecycle_item_recent"),
                    copy: t("profiles.lifecycle_item_recent_restored").replace("{value}", formatTimestamp(sessionNote.at)),
                    tone: "ready",
                });
            }

            return items;
        }

        function renderLifecycleReview() {
            const items = buildLifecycleReviewItems();
            const hasSavedProfile = Boolean(getCurrentId() || getCurrentProfile()?.created_at);
            const copy = hasSavedProfile
                ? t("profiles.lifecycle_review_active")
                : t("profiles.lifecycle_review_body");

            if (profileLifecycleCopyEl) {
                profileLifecycleCopyEl.textContent = copy;
            }

            const renderItemNodes = () => items.map((item) => {
                const rowEl = documentRef.createElement("div");
                rowEl.className = "wizard-export-plan-item";
                rowEl.dataset.planTone = item.tone || "default";
                rowEl.setAttribute("role", "listitem");

                const copyEl = documentRef.createElement("div");
                copyEl.className = "wizard-export-plan-copy";
                const titleEl = documentRef.createElement("div");
                titleEl.textContent = item.title;
                const bodyEl = documentRef.createElement("div");
                bodyEl.className = "wizard-input-hint";
                bodyEl.textContent = item.copy;
                copyEl.append(titleEl, bodyEl);
                rowEl.append(copyEl);
                return rowEl;
            });

            if (profileLifecycleListEl) {
                profileLifecycleListEl.replaceChildren(...renderItemNodes());
            }
            if (wizardSummaryLifecycleListEl) {
                wizardSummaryLifecycleListEl.replaceChildren(...renderItemNodes());
            }
        }

        function getWorkflowLifecycleState(dirty, invalid) {
            const currentId = getCurrentId();
            const currentProfile = getCurrentProfile();
            const hasDraftName = Boolean(nameInput.value.trim());

            if (currentProfile?.is_deleted) {
                return {
                    selectionState: "archived",
                    workflowState: "archived",
                    title: t("profiles.dock_state_archived_title"),
                    copy: t("profiles.wizard_export_state_archived"),
                };
            }
            if (!currentId && !hasDraftName) {
                return {
                    selectionState: "empty",
                    workflowState: "empty",
                    title: t("profiles.dock_state_empty_title"),
                    copy: t("profiles.selection_empty_status"),
                };
            }
            if (!currentId) {
                return {
                    selectionState: "draft",
                    workflowState: "draft",
                    title: t("profiles.dock_state_draft_title"),
                    copy: t("profiles.wizard_export_state_unsaved_new"),
                };
            }
            if (invalid) {
                return {
                    selectionState: "active",
                    workflowState: "invalid",
                    title: t("profiles.dock_state_invalid_title"),
                    copy: t("profiles.wizard_export_state_invalid_dirty"),
                };
            }
            if (dirty) {
                return {
                    selectionState: "active",
                    workflowState: "dirty",
                    title: t("profiles.dock_state_dirty_title"),
                    copy: t("profiles.wizard_export_state_unsaved_existing"),
                };
            }
            return {
                selectionState: "active",
                workflowState: "ready",
                title: t("profiles.dock_state_ready_title"),
                copy: t("profiles.wizard_export_download_hint_ready"),
            };
        }

        function syncWorkspaceOverview() {
            const schemaVersion = documentRef.getElementById("profile-type").value || defaultSchemaVersion;
            const mode = documentRef.getElementById("mode").value || "json";
            overviewSchemaEl.textContent = formatSchemaLabel(schemaVersion);
            overviewModeEl.textContent = mode.toUpperCase();

            if (getCurrentProfile()?.is_deleted) {
                overviewContextEl.textContent = t("profiles.overview_deleted");
            } else if (getCloneSourceProfile()?.name) {
                overviewContextEl.textContent = t("profiles.overview_cloned")
                    .replace("{name}", getCloneSourceProfile().name);
            } else if (getCurrentId()) {
                overviewContextEl.textContent = t("profiles.overview_existing");
            } else {
                overviewContextEl.textContent = t("profiles.overview_draft");
            }

            renderCloneContext();
            renderCloneHandoffPanel();
            renderLifecycleReview();
            updateWizardSummary();
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

        function normalizeValue(value) {
            if (Array.isArray(value)) {
                return value.map(normalizeValue);
            }
            if (value && typeof value === "object") {
                return Object.keys(value)
                    .sort()
                    .reduce((acc, key) => {
                        acc[key] = normalizeValue(value[key]);
                        return acc;
                    }, {});
            }
            return value;
        }

        function snapshotToString(snapshot) {
            return JSON.stringify(normalizeValue(snapshot));
        }

        function escapeHtml(value) {
            return String(value ?? "")
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll('"', "&quot;")
                .replaceAll("'", "&#39;");
        }

        function readFormState() {
            return {
                name: nameInput.value.trim(),
                owner: ownerInput.value.trim() || null,
                description: descriptionInput.value.trim() || null,
                schemaVersion: documentRef.getElementById("profile-type").value,
            };
        }

        function hasComparableBase() {
            return Boolean(getCurrentId());
        }

        function buildSnapshot() {
            const editor = getEditor();
            const form = readFormState();
            return {
                id: getCurrentId(),
                name: form.name,
                owner: form.owner,
                description: form.description,
                schemaVersion: form.schemaVersion,
                flags: fromEditorValue(editor.getValue(), documentRef.getElementById("mode").value),
            };
        }

        function buildProfileSnapshot(profile) {
            return {
                id: profile?.id ?? null,
                name: profile?.name || "",
                owner: profile?.owner || null,
                description: profile?.description || null,
                schemaVersion: profile?.schema_version || defaultSchemaVersion,
                flags: profile?.flags || {},
            };
        }

        function isPlainObject(value) {
            return Boolean(value) && typeof value === "object" && !Array.isArray(value);
        }

        function collectDiffPaths(baseValue, otherValue, path = [], changes = []) {
            const normalizedBase = normalizeValue(baseValue);
            const normalizedOther = normalizeValue(otherValue);

            if (isPlainObject(normalizedBase) && isPlainObject(normalizedOther)) {
                const keys = Array.from(new Set([
                    ...Object.keys(normalizedBase),
                    ...Object.keys(normalizedOther),
                ])).sort();
                keys.forEach((key) => {
                    collectDiffPaths(normalizedBase[key], normalizedOther[key], [...path, key], changes);
                });
                return changes;
            }

            if (snapshotToString(normalizedBase) !== snapshotToString(normalizedOther)) {
                changes.push(path);
            }
            return changes;
        }

        function buildCompareDiff(baseSnapshot, otherSnapshot) {
            // Keep comparison snapshot-driven so new profile fields flow into diffing automatically.
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
                "Authentication",
                "WindowsSSO",
                "DNSOverHTTPS",
                "DisableAppUpdate",
                "DisableSystemAddonUpdate",
                "AppAutoUpdate",
                "DontCheckDefaultBrowser",
                "PromptForDownloadLocation",
            ].includes(policyKey)) return "step_two";
            if ([
                "Homepage",
                "NewTabPage",
                "OverrideFirstRunPage",
                "OverridePostUpdatePage",
                "FirefoxHome",
                "UserMessaging",
            ].includes(policyKey)) return "step_three";
            if ([
                "SearchEngines",
                "SearchSuggestEnabled",
                "FirefoxSuggest",
            ].includes(policyKey)) return "step_four";
            if ([
                "Permissions",
                "Cookies",
                "DisableTelemetry",
                "DisableFirefoxStudies",
                "DisablePrivateBrowsing",
                "OfferToSaveLogins",
                "OfferToSaveLoginsDefault",
                "SanitizeOnShutdown",
                "HttpsOnlyMode",
            ].includes(policyKey)) return "step_five";
            if ([
                "DisableFirefoxAccounts",
                "RequestedLocales",
                "TranslateEnabled",
                "Extensions",
                "ExtensionSettings",
                "InstallAddonsPermission",
                "WebsiteFilter",
                "Handlers",
                "Bookmarks",
                "ManagedBookmarks",
                "GoToIntranetSiteForSingleWordEntryInAddressBar",
            ].includes(policyKey)) return "step_six";
            if (["GenerativeAI", "VisualSearchEnabled"].includes(policyKey)) return "step_seven";
            return "step_two";
        }

        function resolveCompareAreaForPreference(key) {
            const prefKey = String(key || "");
            if (/proxy|network|dns|update|download|browser/i.test(prefKey)) return "step_two";
            if (/homepage|newtab|firstrun|postupdate|home/i.test(prefKey)) return "step_three";
            if (/search|suggest|urlbar/i.test(prefKey)) return "step_four";
            if (/cookie|permission|privacy|telemetry|password|https|sanitize|private/i.test(prefKey)) return "step_five";
            if (/locale|language|translate|extension|account|bookmark|handler|website|intranet/i.test(prefKey)) return "step_six";
            if (/ai|visualsearch|chatbot|model|provider/i.test(prefKey)) return "step_seven";
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
                "step_six",
                "step_seven",
            ].map((areaKey) => {
                const items = areaMap.get(areaKey) || [];
                if (!items.length) return null;
                return {
                    title: t(`profiles.compare_guided_area_${areaKey}`),
                    items,
                };
            }).filter(Boolean);
        }

        function renderComparePanel() {
            if (!compareEmptyEl || !compareActiveEl || !compareEmptyCopyEl) return;

            if (!hasComparableBase()) {
                compareEmptyEl.hidden = false;
                compareActiveEl.hidden = true;
                compareClearEl.hidden = true;
                compareEmptyCopyEl.textContent = t("profiles.compare_empty_need_base");
                return;
            }

            if (!compareProfileState) {
                compareEmptyEl.hidden = false;
                compareActiveEl.hidden = true;
                compareClearEl.hidden = true;
                compareEmptyCopyEl.textContent = t("profiles.compare_empty_pick_other");
                return;
            }

            let currentSnapshot = null;
            try {
                currentSnapshot = buildSnapshot();
            } catch {
                compareEmptyEl.hidden = false;
                compareActiveEl.hidden = true;
                compareClearEl.hidden = true;
                compareEmptyCopyEl.textContent = t("profiles.compare_empty_invalid");
                return;
            }

            const diff = buildCompareDiff(currentSnapshot, compareProfileState.snapshot);
            compareEmptyEl.hidden = true;
            compareActiveEl.hidden = false;
            compareClearEl.hidden = false;
            compareCurrentNameEl.textContent = currentSnapshot.name || t("profiles.compare_current_draft");
            compareCurrentCopyEl.textContent = getCurrentId()
                ? t("profiles.compare_current_saved_copy").replace("{schema}", formatSchemaLabel(currentSnapshot.schemaVersion))
                : t("profiles.compare_current_draft_copy").replace("{schema}", formatSchemaLabel(currentSnapshot.schemaVersion));
            compareOtherNameEl.textContent = compareProfileState.profile.name || t("profiles.none_selected");
            compareOtherCopyEl.textContent = t("profiles.compare_other_copy").replace(
                "{schema}",
                formatSchemaLabel(compareProfileState.snapshot.schemaVersion),
            );
            compareMetadataCountEl.textContent = `${diff.metadataChanges.length}`;
            comparePolicyCountEl.textContent = `${diff.policyEntries.size}`;
            comparePreferenceCountEl.textContent = `${diff.preferenceEntries.size}`;
            compareChangesCopyEl.textContent = diff.sampleChanges.length
                ? t("profiles.compare_changes_active")
                : t("profiles.compare_changes_none");
            compareChangesListEl.innerHTML = "";
            if (compareGuidedAreasCopyEl) {
                compareGuidedAreasCopyEl.textContent = diff.sampleChanges.length
                    ? t("profiles.compare_guided_areas_active")
                    : t("profiles.compare_guided_areas_none");
            }
            if (compareGuidedAreasListEl) {
                compareGuidedAreasListEl.innerHTML = "";
            }
            if (!diff.sampleChanges.length) {
                const item = documentRef.createElement("li");
                item.className = "compare-changes-item";
                item.setAttribute("role", "listitem");
                item.textContent = t("profiles.compare_no_diff");
                compareChangesListEl.appendChild(item);
                if (compareGuidedAreasListEl) {
                    const groupedItem = documentRef.createElement("li");
                    groupedItem.className = "compare-changes-item";
                    groupedItem.setAttribute("role", "listitem");
                    groupedItem.textContent = t("profiles.compare_no_diff");
                    compareGuidedAreasListEl.appendChild(groupedItem);
                }
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
            if (compareGuidedAreasListEl) {
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
        }

        function clearCompareProfile(notify = true) {
            compareProfileState = null;
            renderComparePanel();
            renderList(getLibraryStats().items || []);
            if (notify) {
                setStatus(t("profiles.status_compare_cleared"), "info");
            }
        }

        async function compareWithProfile(id) {
            try {
                const profile = await getProfile(id);
                compareProfileState = {
                    profile,
                    snapshot: buildProfileSnapshot(profile),
                };
                renderComparePanel();
                renderList(getLibraryStats().items || []);
                try {
                    buildSnapshot();
                    setStatus(t("profiles.status_compare_ready").replace("{name}", profile.name), "info");
                } catch {
                    setStatus(t("profiles.compare_empty_invalid"), "warn");
                }
                documentRef.getElementById("compare-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
            } catch (e) {
                setStatus(t("profiles.error_compare").replace("{detail}", e.message || e), "error");
            }
        }

        function setBaselineFromCurrentUi() {
            setBaselineSnapshot(snapshotToString(buildSnapshot()));
            markWizardBaselineSnapshot?.();
            updateActionState();
        }

        function currentSnapshotState() {
            try {
                const currentSnapshot = snapshotToString(buildSnapshot());
                return {
                    dirty: getBaselineSnapshot() !== null && currentSnapshot !== getBaselineSnapshot(),
                    invalid: false,
                };
            } catch {
                return { dirty: true, invalid: true };
            }
        }

        function setValidationPreview(message = "", tone = "neutral") {
            setValidationPreviewTone(tone);
            const nextMessage = message || t("profiles.validation_idle");
            validationPreviewEl.textContent = nextMessage;
            if (advancedReviewValidationStateEl) {
                advancedReviewValidationStateEl.textContent = nextMessage;
                advancedReviewValidationStateEl.dataset.reviewTone = tone || "neutral";
            }
            validationPreviewEl.className = tone === "error"
                ? "max-w-full text-xs text-red-700"
                : tone === "success"
                    ? "max-w-full text-xs text-emerald-700"
                    : "max-w-full text-xs text-slate-500";
        }

        function updateLibrarySummary(stats) {
            const filtered = Number(stats?.filtered || 0);
            const total = Number(stats?.total || 0);
            const nextStats = { ...getLibraryStats(), filtered, total };
            setLibraryStats(nextStats);
            listSummaryEl.textContent = `${filtered}`;
            listSummaryEl.removeAttribute("aria-hidden");
            listTotalSummaryEl.textContent = `${total}`;
            listTotalSummaryEl.removeAttribute("aria-hidden");
            workspaceProfileCountEl.textContent = `${total}`;
            workspaceProfileCountEl.removeAttribute("aria-hidden");
            const workspaceProfileLabelEl = documentRef.getElementById("workspace-profile-label");
            workspaceProfileLabelEl.textContent = libraryCountLabel(total, getCurrentLang());
            workspaceProfileLabelEl.removeAttribute("aria-hidden");
            workspaceProfileCountEl.closest(".compact-counter")?.classList.remove("compact-counter--pending");
        }

        function refreshWorkspaceSignal() {
            const { dirty, invalid } = currentSnapshotState();
            if (invalid) {
                workspaceSignalEl.textContent = t("profiles.signal_invalid");
                workspaceSignalEl.className = "signal-chip signal-chip--invalid";
                overviewStatusEl.className = "text-base font-semibold text-red-700";
            } else if (dirty) {
                workspaceSignalEl.textContent = t("profiles.signal_dirty");
                workspaceSignalEl.className = "signal-chip signal-chip--dirty";
                overviewStatusEl.className = "text-base font-semibold text-amber-800";
            } else {
                workspaceSignalEl.textContent = t("profiles.signal_saved");
                workspaceSignalEl.className = "signal-chip signal-chip--saved";
                overviewStatusEl.className = "text-base font-semibold text-slate-900";
            }
            overviewStatusEl.textContent = workspaceSignalEl.textContent;
            dockStatusTextEl.textContent = workspaceSignalEl.textContent;
            if (advancedReviewSaveStateEl) {
                advancedReviewSaveStateEl.textContent = workspaceSignalEl.textContent;
                advancedReviewSaveStateEl.dataset.reviewTone = invalid ? "error" : (dirty ? "warn" : "success");
            }
            return { dirty, invalid };
        }

        function setButtonDisabled(el, disabled) {
            el.disabled = disabled;
            el.classList.toggle("pointer-events-none", disabled);
            el.classList.toggle("opacity-50", disabled);
        }

        function updateActionState() {
            const downloadJson = documentRef.getElementById("download-json");
            const downloadYaml = documentRef.getElementById("download-yaml");
            const downloadFirefoxPolicies = documentRef.getElementById("download-firefox-policies");
            const { dirty, invalid } = refreshWorkspaceSignal();
            const canFinish = !getIsBusy() && !invalid && (Boolean(getCurrentId()) || Boolean(nameInput.value.trim()));
            const exportAvailable = Boolean(getCurrentId()) && !getCurrentProfile()?.is_deleted;
            const lifecycleState = getWorkflowLifecycleState(dirty, invalid);

            saveButtonEl.textContent = getCurrentId()
                ? t("profiles.save")
                : t("profiles.create_submit");
            setButtonDisabled(saveButtonEl, getIsBusy() || invalid || (!dirty && !!getCurrentId()));
            setButtonDisabled(deleteButtonEl, getIsBusy() || !getCurrentId() || !!getCurrentProfile()?.is_deleted);
            setButtonDisabled(hardDeleteButtonEl, getIsBusy() || !getCurrentId());
            setButtonDisabled(restoreButtonEl, getIsBusy() || !getCurrentId() || !getCurrentProfile()?.is_deleted);
            setButtonDisabled(resetLibraryButtonEl, getIsBusy());
            setButtonDisabled(validateButtonEl, getIsBusy() || invalid);
            setButtonDisabled(refreshButtonEl, getIsBusy());
            setButtonDisabled(wizardFinishEl, !canFinish);
            if (wizardExportSaveActionEl) {
                wizardExportSaveActionEl.textContent = saveButtonEl.textContent;
                setButtonDisabled(wizardExportSaveActionEl, saveButtonEl.disabled);
            }
            if (wizardExportValidateActionEl) {
                setButtonDisabled(wizardExportValidateActionEl, validateButtonEl.disabled);
            }
            if (dockStateTitleEl) {
                dockStateTitleEl.textContent = lifecycleState.title;
            }
            if (dockStateCopyEl) {
                dockStateCopyEl.textContent = lifecycleState.copy;
            }
            if (dockStateSummaryEl) {
                dockStateSummaryEl.dataset.workflowState = lifecycleState.workflowState;
            }
            if (advancedReviewStripEl) {
                advancedReviewStripEl.dataset.workflowState = lifecycleState.workflowState;
            }
            if (advancedReviewDownloadStateEl) {
                advancedReviewDownloadStateEl.textContent = lifecycleState.copy;
                advancedReviewDownloadStateEl.dataset.reviewTone =
                    lifecycleState.workflowState === "ready" ? "success"
                        : lifecycleState.workflowState === "invalid" || lifecycleState.workflowState === "archived" ? "error"
                            : lifecycleState.workflowState === "dirty" ? "warn"
                                : "neutral";
            }
            setSelectionUiState(lifecycleState.selectionState);
            setWorkflowStateUi(lifecycleState.workflowState);
            renderComparePanel();

            if (!exportAvailable) {
                downloadJson.classList.add("pointer-events-none", "opacity-50");
                downloadYaml.classList.add("pointer-events-none", "opacity-50");
                downloadFirefoxPolicies.classList.add("pointer-events-none", "opacity-50");
                wizardExportJsonEl.classList.add("pointer-events-none", "opacity-50");
                wizardExportYamlEl.classList.add("pointer-events-none", "opacity-50");
                wizardExportFirefoxPoliciesEl.classList.add("pointer-events-none", "opacity-50");
            } else {
                downloadJson.classList.remove("pointer-events-none", "opacity-50");
                downloadYaml.classList.remove("pointer-events-none", "opacity-50");
                downloadFirefoxPolicies.classList.remove("pointer-events-none", "opacity-50");
                wizardExportJsonEl.classList.remove("pointer-events-none", "opacity-50");
                wizardExportYamlEl.classList.remove("pointer-events-none", "opacity-50");
                wizardExportFirefoxPoliciesEl.classList.remove("pointer-events-none", "opacity-50");
            }

            renderFinalExportStepSummary(dirty, invalid);
            syncWorkspaceOverview();
            renderCurrentStepActions?.();
        }

        function updateDownloadLinks() {
            const jsonLink = documentRef.getElementById("download-json");
            const yamlLink = documentRef.getElementById("download-yaml");
            const firefoxPoliciesLink = documentRef.getElementById("download-firefox-policies");
            if (!getCurrentId() || getCurrentProfile()?.is_deleted) {
                jsonLink.href = "#";
                yamlLink.href = "#";
                firefoxPoliciesLink.href = "#";
                wizardExportJsonEl.href = "#";
                wizardExportYamlEl.href = "#";
                wizardExportFirefoxPoliciesEl.href = "#";
                updateActionState();
                return;
            }
            jsonLink.href = `/api/export/profiles/${getCurrentId()}.json`;
            yamlLink.href = `/api/export/profiles/${getCurrentId()}.yaml`;
            firefoxPoliciesLink.href = `/api/export/profiles/${getCurrentId()}/firefox/policies.json`;
            wizardExportJsonEl.href = jsonLink.href;
            wizardExportYamlEl.href = yamlLink.href;
            wizardExportFirefoxPoliciesEl.href = firefoxPoliciesLink.href;
            updateActionState();
        }

        function setDraftState(message, options = {}) {
            const { preserveCloneSource = false } = options;
            setCurrentProfile(null);
            setCurrentId(null);
            if (!preserveCloneSource) {
                setCloneSourceProfile(null);
            }
            setLifecycleSessionNote(null);
            setWizardStarter("blank");
            currentNameEl.textContent = t("profiles.none_selected");
            currentMetaEl.textContent = message || t("profiles.selection_empty_meta");
            stateBadgeEl.textContent = t("profiles.badge_draft");
            stateBadgeEl.className = "state-chip state-chip--draft";
            nameInput.disabled = false;
            nameHintEl.textContent = t("profiles.name_hint");
            setWorkspaceHelper(
                t("profiles.helper_no_selection_title"),
                t("profiles.helper_no_selection_body"),
            );
            setValidationPreview(message ? t("profiles.status_draft_ready") : t("profiles.selection_empty_status"));
            syncWizardFieldsFromForm();
            syncWorkspaceOverview();
            updateDownloadLinks();
            updateWizardContext();
            syncWizardNetworkFromEditor();
            syncWizardPreferencesFromEditor();
            syncWizardExtensionsFromEditor();
            renderList(getLibraryStats().items || []);
        }

        function setMeta(profile) {
            setCurrentProfile(profile);
            if (!profile) {
                setDraftState();
                return;
            }

            setWizardStarter("keep_current");

            currentNameEl.textContent = profile.name;
            currentMetaEl.textContent = [
                `ID ${profile.id}`,
                formatSchemaLabel(profile.schema_version),
                t("profiles.meta_updated").replace("{value}", formatTimestamp(profile.updated_at)),
            ].filter(Boolean).join(" • ");

            if (profile.is_deleted) {
                stateBadgeEl.textContent = t("profiles.badge_deleted");
                stateBadgeEl.className = "state-chip state-chip--deleted";
            } else {
                stateBadgeEl.textContent = t("profiles.badge_active");
                stateBadgeEl.className = "state-chip state-chip--active";
            }

            setWorkspaceHelper(
                t("profiles.helper_selected_title"),
                t("profiles.helper_selected_body"),
            );
            nameInput.value = profile.name || "";
            ownerInput.value = profile.owner || "";
            descriptionInput.value = profile.description || "";
            documentRef.getElementById("profile-type").value = profile.schema_version || defaultSchemaVersion;
            nameInput.disabled = true;
            nameHintEl.textContent = t("profiles.name_locked");
            setValidationPreview(t("profiles.selection_active_status"), "success");
            syncWizardFieldsFromForm();
            syncWorkspaceOverview();
            updateDownloadLinks();
            updateWizardContext();
            syncWizardNetworkFromEditor();
            syncWizardPreferencesFromEditor();
            syncWizardExtensionsFromEditor();
        }

        async function confirmIfDirty() {
            const { dirty } = currentSnapshotState();
            if (!dirty) return true;
            return windowRef.confirm(t("profiles.confirm_discard"));
        }

        async function resetDraft(skipConfirm = false) {
            const editor = getEditor();
            if (!skipConfirm && !(await confirmIfDirty())) return;
            const schemaVersion = documentRef.getElementById("profile-type").value || defaultSchemaVersion;
            setCurrentRaw({});
            nameInput.value = "";
            ownerInput.value = "";
            descriptionInput.value = "";
            documentRef.getElementById("profile-type").value = schemaVersion;
            if (editor) {
                editor.setValue(toEditorValue({}, documentRef.getElementById("mode").value));
            }
            setDraftState(t("profiles.draft_ready_meta"));
            setStatus(t("profiles.status_draft_ready"), "info");
            setBaselineFromCurrentUi();
            syncWizardNetworkFromEditor();
            syncWizardPoliciesFromEditor();
            syncWizardPreferencesFromEditor();
            syncWizardExtensionsFromEditor();
            setWizardStep(1);
            nameInput.focus();
        }

        function setCloneDraftState(sourceProfile) {
            const sourceName = sourceProfile?.name || t("profiles.clone_source_unknown");
            const clonedName = t("profiles.clone_name_pattern").replace("{name}", sourceName);
            setCloneSourceProfile({
                id: sourceProfile?.id || null,
                name: sourceName,
                schema_version: sourceProfile?.schema_version || defaultSchemaVersion,
                is_deleted: sourceProfile?.is_deleted === true,
            });
            setLifecycleSessionNote(null);
            setCurrentProfile(null);
            setCurrentId(null);
            setWizardStarter("keep_current");
            currentNameEl.textContent = clonedName;
            currentMetaEl.textContent = t("profiles.clone_meta").replace("{name}", sourceName);
            stateBadgeEl.textContent = t("profiles.badge_draft");
            stateBadgeEl.className = "state-chip state-chip--draft";
            nameInput.disabled = false;
            nameInput.value = clonedName;
            ownerInput.value = sourceProfile?.owner || "";
            descriptionInput.value = sourceProfile?.description || "";
            documentRef.getElementById("profile-type").value = sourceProfile?.schema_version || defaultSchemaVersion;
            nameHintEl.textContent = t("profiles.name_hint");
            setWorkspaceHelper(
                t("profiles.helper_clone_title").replace("{name}", sourceName),
                t("profiles.helper_clone_body"),
            );
            setValidationPreview(t("profiles.status_draft_ready"));
            syncWizardFieldsFromForm();
            syncWorkspaceOverview();
            updateDownloadLinks();
            updateWizardContext();
            syncWizardNetworkFromEditor();
            syncWizardPoliciesFromEditor();
            syncWizardPreferencesFromEditor();
            syncWizardExtensionsFromEditor();
            renderList(getLibraryStats().items || []);
        }

        function renderList(items) {
            const nextStats = { ...getLibraryStats(), items: Array.isArray(items) ? items : [] };
            setLibraryStats(nextStats);
            listEl.innerHTML = "";

            if (!items.length) {
                const li = documentRef.createElement("li");
                li.className = "list-empty-illustration rounded-[24px] border border-dashed border-slate-200 px-4 py-6 text-center";
                li.innerHTML = `
                    <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/80 bg-white/80 text-2xl shadow-sm">+</div>
                    <div class="text-sm font-semibold text-slate-900">${t("profiles.empty_title")}</div>
                    <div class="mx-auto mt-2 max-w-[240px] text-sm leading-6 text-slate-500">${t("profiles.empty_list")}</div>
                `;
                listEl.appendChild(li);
                return;
            }

            for (const profile of items) {
                const li = documentRef.createElement("li");
                li.className = "library-table-row";
                const selected = profile.id === getCurrentId();
                const canCompare = hasComparableBase() && !selected;
                const compareActive = compareProfileState?.profile?.id === profile.id;
                const canClone = Boolean(profile?.id);
                const openLabel = selected
                    ? t("profiles.list_open_selected")
                    : t("profiles.list_open");
                const compareLabel = compareActive
                    ? t("profiles.compare_selected")
                    : t("profiles.compare_action");
                const cloneLabel = t("profiles.clone_action");
                const statusLabel = profile.is_deleted
                    ? t("profiles.badge_deleted")
                    : t("profiles.badge_active");
                li.innerHTML = `
                    <div class="library-row-grid profile-list-button ${selected ? "profile-list-button--selected" : ""}">
                        <div class="library-row-primary">
                            <button type="button" class="library-row-title-button">
                                ${profile.name}
                            </button>
                        </div>

                        <div class="library-row-meta">
                            <div class="library-row-meta-primary">${formatSchemaLabel(profile.schema_version)}</div>
                        </div>

                        <div class="library-row-updated">
                            <div class="library-row-meta-secondary">${formatTimestamp(profile.updated_at)}</div>
                        </div>

                        <div class="library-row-status-wrap">
                            <span class="profile-list-status ${profile.is_deleted
                                ? "profile-list-status--deleted"
                                : "profile-list-status--active"}">
                                ${statusLabel}
                            </span>
                        </div>

                        <div class="library-row-actions">
                            <button type="button" class="button-base library-row-open-button ${selected ? "library-row-open-button--selected" : ""}">
                                ${openLabel}
                            </button>
                            ${canCompare ? `
                                <button
                                    type="button"
                                    class="button-base ghost-button profile-compare-button ${compareActive ? "profile-compare-button--active" : ""}"
                                    data-compare-profile-id="${profile.id}">
                                    ${compareLabel}
                                </button>
                            ` : ""}
                            ${canClone ? `
                                <button
                                    type="button"
                                    class="button-base ghost-button profile-clone-button"
                                    data-clone-profile-id="${profile.id}">
                                    ${cloneLabel}
                                </button>
                            ` : ""}
                        </div>
                    </div>
                `;
                li.querySelector(".library-row-title-button")?.addEventListener("click", async () => {
                    await loadProfile(profile.id);
                });
                li.querySelector(".library-row-open-button")?.addEventListener("click", async () => {
                    await loadProfile(profile.id);
                });
                const compareButton = li.querySelector("[data-compare-profile-id]");
                compareButton?.addEventListener("click", async () => {
                    await compareWithProfile(profile.id);
                });
                const cloneButton = li.querySelector("[data-clone-profile-id]");
                cloneButton?.addEventListener("click", async () => {
                    await cloneFromProfile(profile.id);
                });
                listEl.appendChild(li);
            }
        }

        async function reloadList() {
            try {
                setStatus(t("profiles.status_loading_list"), "info");
                const [items, stats] = await Promise.all([
                    listProfiles(),
                    getProfileLibraryStats(),
                ]);
                renderList(items);
                updateLibrarySummary(stats);
                setStatus(t("profiles.status_list_ready"), "info");
            } catch (e) {
                setStatus(t("profiles.error_list").replace("{detail}", e.message || e), "error");
            }
        }

        async function loadProfile(id, options = {}) {
            const { keepCloneSource = false } = options;
            const editor = getEditor();
            try {
                if (!(await confirmIfDirty())) return;
                const profile = await getProfile(id);
                if (compareProfileState?.profile?.id === id) {
                    compareProfileState = null;
                }
                if (!keepCloneSource) {
                    setCloneSourceProfile(null);
                }
                setCurrentId(profile.id);
                setCurrentRaw(profile.flags || {});
                setMeta(profile);
                editor.setValue(toEditorValue(getCurrentRaw(), documentRef.getElementById("mode").value));
                syncWizardNetworkFromEditor();
                syncWizardPoliciesFromEditor();
                syncWizardPreferencesFromEditor();
                syncWizardExtensionsFromEditor();
                setBaselineFromCurrentUi();
                const [items, stats] = await Promise.all([
                    listProfiles(),
                    getProfileLibraryStats(),
                ]);
                renderList(items);
                updateLibrarySummary(stats);
                documentRef.getElementById("overview-panel").scrollIntoView({ behavior: "smooth", block: "start" });
                setStatus(t("profiles.status_profile_loaded").replace("{name}", profile.name), "success");
            } catch (e) {
                setStatus(t("profiles.error_load").replace("{detail}", e.message || e), "error");
            }
        }

        async function cloneFromProfile(id) {
            const editor = getEditor();
            try {
                if (!(await confirmIfDirty())) return;
                const profile = await getProfile(id);
                const schemaVersion = profile.schema_version || defaultSchemaVersion;
                const flags = profile.flags && typeof profile.flags === "object" ? profile.flags : {};
                documentRef.getElementById("profile-type").value = schemaVersion;
                documentRef.getElementById("mode").value = "json";
                setCurrentRaw(flags);
                editor.setValue(toEditorValue(flags, documentRef.getElementById("mode").value));
                setCloneDraftState(profile);
                setBaselineFromCurrentUi();
                setWizardStep(1);
                nameInput.focus();
                nameInput.select();
                documentRef.getElementById("overview-panel").scrollIntoView({ behavior: "smooth", block: "start" });
                setStatus(t("profiles.status_profile_cloned").replace("{name}", profile.name), "success");
            } catch (e) {
                setStatus(t("profiles.error_clone").replace("{detail}", e.message || e), "error");
            }
        }

        function setBusyState(nextBusy, labelKey = null) {
            setIsBusy(nextBusy);
            if (!nextBusy) {
                updateActionState();
                return;
            }

            if (labelKey) {
                saveButtonEl.textContent = t(labelKey);
            }
            setButtonDisabled(saveButtonEl, true);
            setButtonDisabled(deleteButtonEl, true);
            setButtonDisabled(hardDeleteButtonEl, true);
            setButtonDisabled(restoreButtonEl, true);
            setButtonDisabled(resetLibraryButtonEl, true);
            setButtonDisabled(validateButtonEl, true);
            setButtonDisabled(refreshButtonEl, true);
        }

        async function saveCurrent() {
            const editor = getEditor();
            try {
                setBusyState(true, getCurrentId() ? "profiles.saving" : "profiles.creating");
                const form = readFormState();
                const mode = documentRef.getElementById("mode").value;
                const parsedFlags = fromEditorValue(editor.getValue(), mode);

                if (!getCurrentId() && !form.name) {
                    setBusyState(false);
                    setStatus(t("profiles.create_name_required"), "warn");
                    nameInput.focus();
                    return false;
                }

                if (!getCurrentId()) {
                const created = await createProfile({
                        name: form.name,
                        description: form.description,
                        owner: form.owner,
                        schema_version: form.schemaVersion,
                        flags: parsedFlags,
                });
                    setLifecycleSessionNote(null);
                    setCurrentRaw(created.flags || {});
                    await reloadList();
                    await loadProfile(created.id, { keepCloneSource: Boolean(getCloneSourceProfile()?.name) });
                    setStatus(t("profiles.status_profile_created").replace("{name}", created.name), "success");
                    setValidationPreview(t("profiles.validation_ready"), "success");
                    setBusyState(false);
                    return true;
                }

                const updated = await patchProfile(getCurrentId(), {
                    description: form.description,
                    owner: form.owner,
                    schema_version: form.schemaVersion,
                    flags: parsedFlags,
                });
                setLifecycleSessionNote(null);
                setCurrentRaw(updated.flags || {});
                setMeta(updated);
                setBaselineFromCurrentUi();
                await reloadList();
                setStatus(t("profiles.status_profile_saved").replace("{name}", updated.name), "success");
                setValidationPreview(t("profiles.validation_ready"), "success");
                return true;
            } catch (e) {
                setStatus(t("profiles.error_save").replace("{detail}", e.message || e), "error");
                return false;
            } finally {
                setBusyState(false);
            }
        }

        async function doSoftDelete() {
            if (!getCurrentId()) {
                setStatus(t("profiles.select_profile_first"), "warn");
                return;
            }
            if (!windowRef.confirm(t("profiles.confirm_soft_delete"))) return;
            try {
                setBusyState(true, "profiles.deleting");
                await softDeleteProfile(getCurrentId());
                await reloadList();
                setCurrentId(null);
                setCurrentProfile(null);
                setCurrentRaw({});
                await resetDraft(true);
                setStatus(t("profiles.soft_delete_done"), "success");
            } catch (e) {
                setStatus(t("profiles.error_delete").replace("{detail}", e.message || e), "error");
            } finally {
                setBusyState(false);
            }
        }

        async function doHardDelete() {
            if (!getCurrentId()) {
                setStatus(t("profiles.select_profile_first"), "warn");
                return;
            }
            if (!windowRef.confirm(t("profiles.confirm_hard_delete"))) return;
            try {
                setBusyState(true, "profiles.deleting");
                await hardDeleteProfile(getCurrentId());
                await reloadList();
                setCurrentId(null);
                setCurrentProfile(null);
                setCurrentRaw({});
                await resetDraft(true);
                setStatus(t("profiles.hard_delete_done"), "success");
            } catch (e) {
                setStatus(t("profiles.error_delete").replace("{detail}", e.message || e), "error");
            } finally {
                setBusyState(false);
            }
        }

        async function doRestore() {
            const editor = getEditor();
            if (!getCurrentId()) {
                setStatus(t("profiles.select_profile_first"), "warn");
                return;
            }
            try {
                setBusyState(true, "profiles.restoring");
                const restored = await restoreProfile(getCurrentId());
                setLifecycleSessionNote({
                    type: "restored",
                    profileId: restored.id,
                    at: new Date().toISOString(),
                });
                setCurrentRaw(restored.flags || {});
                await reloadList();
                setMeta(restored);
                editor.setValue(toEditorValue(getCurrentRaw(), documentRef.getElementById("mode").value));
                syncWizardNetworkFromEditor();
                syncWizardPoliciesFromEditor();
                syncWizardPreferencesFromEditor();
                syncWizardExtensionsFromEditor();
                setBaselineFromCurrentUi();
                setStatus(t("profiles.status_profile_restored").replace("{name}", restored.name), "success");
            } catch (e) {
                setStatus(t("profiles.error_restore").replace("{detail}", e.message || e), "error");
            } finally {
                setBusyState(false);
            }
        }

        async function doResetLibrary() {
            if (!windowRef.confirm(t("profiles.confirm_reset_library"))) return;
            try {
                setBusyState(true, "profiles.resetting_library");
                await resetProfilesLibrary();
                setCurrentId(null);
                setCurrentProfile(null);
                setCurrentRaw({});
                await resetDraft(true);
                await reloadList();
                setStatus(t("profiles.reset_library_done"), "success");
            } catch (e) {
                setStatus(t("profiles.error_reset").replace("{detail}", e.message || e), "error");
            } finally {
                setBusyState(false);
            }
        }

        async function doValidate() {
            const editor = getEditor();
            try {
                setBusyState(true, "profiles.validating");
                const profileKey = documentRef.getElementById("profile-type").value;
                const parsedFlags = fromEditorValue(editor.getValue(), documentRef.getElementById("mode").value);
                const res = await validateFlags(profileKey, parsedFlags);
                if (res.ok) {
                    setStatus(t("profiles.status_validation_ok").replace("{schema}", profileKey), "success");
                    setValidationPreview(t("profiles.validation_ok"), "success");
                } else {
                    setStatus(
                        t("profiles.error_validation_result")
                            .replace("{detail}", res.detail || t("profiles.validation_result_invalid")),
                        "error",
                    );
                    setValidationPreview(res.detail || t("profiles.validation_failed"), "error");
                }
            } catch (e) {
                setStatus(t("profiles.error_validation_failed").replace("{detail}", e.message || e), "error");
                setValidationPreview(e.message || String(e), "error");
            } finally {
                setBusyState(false);
            }
        }

        compareClearEl?.addEventListener("click", () => {
            clearCompareProfile();
        });

        [profileCloneHandoffListEl, wizardCloneHandoffListEl].forEach((listEl) => {
            listEl?.addEventListener("click", async (event) => {
                const compareButton = event.target.closest("[data-clone-handoff-compare]");
                if (compareButton) {
                    const profileId = Number(compareButton.dataset.cloneHandoffCompare || "");
                    if (!Number.isNaN(profileId) && profileId > 0) {
                        await compareWithProfile(profileId);
                    }
                    return;
                }

                const stepButton = event.target.closest("[data-clone-handoff-step]");
                if (stepButton) {
                    const nextStep = Number(stepButton.dataset.cloneHandoffStep || "");
                    if (!Number.isNaN(nextStep) && nextStep > 0) {
                        setWizardStep(nextStep);
                        documentRef.getElementById(`wizard-step-${nextStep}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
                    }
                }
            });
        });

        return {
            syncWorkspaceOverview,
            setValidationPreview,
            updateLibrarySummary,
            refreshWorkspaceSignal,
            updateActionState,
            updateDownloadLinks,
            setDraftState,
            setMeta,
            currentSnapshotState,
            setBaselineFromCurrentUi,
            resetDraft,
            reloadList,
            loadProfile,
            readFormState,
            buildSnapshot,
            buildProfileSnapshot,
            buildCompareDiff,
            saveCurrent,
            doSoftDelete,
            doHardDelete,
            doRestore,
            doResetLibrary,
            doValidate,
        };
    }

    window.BPMProfilesWorkspace = { create };
})();
