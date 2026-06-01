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
            parseEditorPolicyDocument,
            listProfiles,
            getProfileLibraryStats,
            getProfile,
            createProfile,
            importFirefoxPoliciesJson,
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
            setWizardComplianceLayer,
            setWizardComplianceSnapshot,
            getWizardComplianceMergeInfo,
            markWizardBaselineSnapshot,
            renderCurrentStepActions,
            syncWizardNetworkFromEditor,
            syncWizardPreferencesFromEditor,
            syncWizardExtensionsFromEditor,
            syncWizardPoliciesFromEditor,
            setWizardStep,
            getWizardStep,
            renderAllSettingsList,
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
        const setValidationIssues = state.setValidationIssues || (() => {});

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
            editorProfileIdEl,
            editorModeGuidedEl,
            editorModeSettingsEl,
            editorModeJsonEl,
            editorModeLinksHintEl,
            profileDerivedNoteEl,
            profileCloneHandoffPanelEl,
            profileCloneHandoffCopyEl,
            profileCloneHandoffListEl,
            profileLifecycleCopyEl,
            profileLifecycleListEl,
            profileCompliancePanelEl,
            profileComplianceCopyEl,
            profileComplianceListEl,
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
            importFirefoxPoliciesButtonEl,
            importFirefoxPoliciesFileEl,
            importFirefoxPoliciesStatusEl,
            overviewSchemaEl,
            overviewModeEl,
            overviewStatusEl,
            overviewContextEl,
            dockStatusTextEl,
            dockStateSummaryEl,
            dockStateTitleEl,
            dockStateCopyEl,
            saveConflictPanelEl,
            saveConflictCopyEl,
            saveConflictMetaEl,
            saveConflictReloadEl,
            saveConflictSaveCopyEl,
            saveConflictOverwriteEl,
            wizardExportSaveActionEl,
            wizardExportValidateActionEl,
            wizardExportReadyCardEl,
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
        const routeMode = documentRef.body?.dataset.profilesRouteMode || "new";
        const advancedFocusTarget = documentRef.body?.dataset.advancedFocusTarget || "";
        const defaultSchemaVersion = getDefaultSchemaVersion(documentRef);
        const compareBaseStorageKey = "bpm-library-compare-base";
        let compareProfileState = null;
        let saveConflictState = null;

        function normalizeSettingsModeFocusTarget(focusTarget) {
            const normalizedTarget = String(focusTarget || "").trim();
            if (!normalizedTarget || normalizedTarget === "editor") return "";
            if (
                normalizedTarget === "raw"
                || normalizedTarget === "deprecated"
                || normalizedTarget === "unknown"
                || normalizedTarget.startsWith("raw:")
                || normalizedTarget.startsWith("deprecated:")
                || normalizedTarget.startsWith("unknown:")
            ) {
                return "settings-schema-shell-step-8";
            }
            return normalizedTarget;
        }

        function normalizeJsonModeFocusTarget(focusTarget) {
            const normalizedTarget = String(focusTarget || "").trim();
            if (!normalizedTarget) return "editor";
            if (normalizedTarget === "settings-schema-shell-step-8") return "raw";
            if (
                normalizedTarget === "editor"
                || normalizedTarget.startsWith("policy:")
                || normalizedTarget === "raw"
                || normalizedTarget === "deprecated"
                || normalizedTarget === "unknown"
                || normalizedTarget.startsWith("raw:")
                || normalizedTarget.startsWith("deprecated:")
                || normalizedTarget.startsWith("unknown:")
            ) {
                return normalizedTarget;
            }
            return "editor";
        }

        function isJsonModeFocusTarget(focusTarget) {
            return normalizeJsonModeFocusTarget(focusTarget) !== "editor"
                || String(focusTarget || "").trim() === "editor";
        }

        function setImportStatus(message, tone = "info") {
            if (!importFirefoxPoliciesStatusEl) return;
            importFirefoxPoliciesStatusEl.textContent = message;
            importFirefoxPoliciesStatusEl.dataset.statusTone = tone;
        }

        function inferImportProfileName(file) {
            const rawName = file?.name || "policies.json";
            const withoutExtension = rawName.replace(/\.json$/i, "").trim();
            if (!withoutExtension || withoutExtension.toLowerCase() === "policies") {
                return t("profiles.import_firefox_policies_default_name");
            }
            return withoutExtension;
        }

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

        function normalizeCompareBaseSnapshot(snapshot, fallbackProfile = null) {
            const source = snapshot && typeof snapshot === "object" ? snapshot : {};
            const fallback = fallbackProfile && typeof fallbackProfile === "object" ? fallbackProfile : {};
            const profileId = Number(source.id ?? fallback.id ?? 0);
            if (!Number.isInteger(profileId) || profileId <= 0) return null;
            return {
                id: profileId,
                name: source.name || fallback.name || "",
                owner: source.owner ?? fallback.owner ?? null,
                description: source.description ?? fallback.description ?? null,
                schemaVersion: source.schemaVersion || source.schema_version || fallback.schema_version || defaultSchemaVersion,
                flags: source.flags && typeof source.flags === "object" ? source.flags : {},
            };
        }

        function normalizeCompareBaseProfile(profile, fallbackSnapshot = null) {
            const source = profile && typeof profile === "object" ? profile : {};
            const fallback = fallbackSnapshot && typeof fallbackSnapshot === "object" ? fallbackSnapshot : {};
            const profileId = Number(source.id ?? fallback.id ?? 0);
            if (!Number.isInteger(profileId) || profileId <= 0) return null;
            return {
                id: profileId,
                name: source.name || fallback.name || "",
                owner: source.owner ?? fallback.owner ?? null,
                description: source.description ?? fallback.description ?? null,
                schema_version: source.schema_version || source.schemaVersion || fallback.schemaVersion || defaultSchemaVersion,
                is_deleted: source.is_deleted === true,
                updated_at: source.updated_at || null,
            };
        }

        function readStoredCompareBase() {
            try {
                const payloadText = windowRef.localStorage?.getItem(compareBaseStorageKey) || "";
                if (!payloadText) return null;
                const parsed = JSON.parse(payloadText);
                const snapshot = normalizeCompareBaseSnapshot(parsed?.snapshot, parsed?.profile);
                const profile = normalizeCompareBaseProfile(parsed?.profile, snapshot);
                if (!snapshot || !profile) return null;
                return { profile, snapshot };
            } catch {
                return null;
            }
        }

        function writeStoredCompareBase(profile, snapshot = null) {
            const normalizedSnapshot = normalizeCompareBaseSnapshot(snapshot, profile);
            const normalizedProfile = normalizeCompareBaseProfile(profile, normalizedSnapshot);
            if (!normalizedSnapshot || !normalizedProfile) return;
            try {
                windowRef.localStorage?.setItem(compareBaseStorageKey, JSON.stringify({
                    profile: normalizedProfile,
                    snapshot: normalizedSnapshot,
                }));
            } catch {
                // Ignore storage write failures so compare never blocks the editor flow.
            }
        }

        function clearStoredCompareBase(profileId = null) {
            try {
                if (!windowRef.localStorage) return;
                if (!profileId) {
                    windowRef.localStorage.removeItem(compareBaseStorageKey);
                    return;
                }
                const storedBase = readStoredCompareBase();
                if (storedBase?.profile?.id === profileId) {
                    windowRef.localStorage.removeItem(compareBaseStorageKey);
                }
            } catch {
                // Ignore storage cleanup failures.
            }
        }

        function persistCompareBaseProfile(profile, snapshot = null) {
            const normalizedProfile = normalizeCompareBaseProfile(profile, snapshot);
            if (!normalizedProfile?.id) return;
            const normalizedSnapshot = normalizeCompareBaseSnapshot(snapshot, normalizedProfile)
                || buildProfileSnapshot(profile);
            if (!normalizedSnapshot) return;
            writeStoredCompareBase(normalizedProfile, normalizedSnapshot);
            if (compareProfileState?.profile?.id === normalizedProfile.id) {
                compareProfileState = null;
            }
        }

        function getComparableBaseState() {
            if (getCurrentId()) {
                return {
                    source: "current",
                    profile: normalizeCompareBaseProfile(getCurrentProfile(), buildProfileSnapshot(getCurrentProfile())),
                    snapshot: buildSnapshot(),
                };
            }
            const storedBase = readStoredCompareBase();
            if (!storedBase?.profile?.id || !storedBase?.snapshot) return null;
            return {
                source: "stored",
                profile: storedBase.profile,
                snapshot: storedBase.snapshot,
            };
        }

        function getComparableBaseId() {
            return getCurrentId() || readStoredCompareBase()?.profile?.id || null;
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
            if (editorProfileIdEl) {
                editorProfileIdEl.textContent = getCurrentId()
                    ? `#${getCurrentId()}`
                    : t("profiles.badge_draft");
            }

            renderCloneContext();
            renderCloneHandoffPanel();
            renderLifecycleReview();
            refreshEditorModeLinks();
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

        function buildExpectedRevisionPayload() {
            const revision = Number(getCurrentProfile()?.revision);
            if (!Number.isInteger(revision) || revision < 1) return {};
            return { expected_revision: revision };
        }

        function isRevisionConflictError(error) {
            return Number(error?.status) === 409;
        }

        function clearSaveConflictState() {
            saveConflictState = null;
            if (saveConflictPanelEl) {
                saveConflictPanelEl.hidden = true;
            }
            if (saveConflictMetaEl) {
                saveConflictMetaEl.textContent = "";
            }
        }

        function showSaveConflictState(error) {
            const profileId = Number(error?.detail?.profile_id || getCurrentId() || 0);
            const currentRevision = Number(error?.detail?.current_revision || 0);
            const expectedRevision = Number(error?.detail?.expected_revision || 0);
            saveConflictState = {
                profileId: Number.isInteger(profileId) && profileId > 0 ? profileId : getCurrentId(),
                currentRevision: Number.isInteger(currentRevision) && currentRevision > 0 ? currentRevision : null,
                expectedRevision: Number.isInteger(expectedRevision) && expectedRevision > 0 ? expectedRevision : null,
            };

            const message = t("profiles.status_revision_conflict");
            if (saveConflictPanelEl) {
                saveConflictPanelEl.hidden = false;
            }
            if (saveConflictCopyEl) {
                saveConflictCopyEl.textContent = t("profiles.conflict_body");
            }
            if (saveConflictMetaEl) {
                saveConflictMetaEl.textContent = saveConflictState.currentRevision && saveConflictState.expectedRevision
                    ? t("profiles.conflict_revision_detail")
                        .replace("{current}", String(saveConflictState.currentRevision))
                        .replace("{expected}", String(saveConflictState.expectedRevision))
                    : "";
            }
            setStatus(message, "error");
            setValidationPreview(message, "error");
        }

        function buildUpdatePayload(form, parsedFlags, compliancePayload, options = {}) {
            const { includeExpectedRevision = true } = options;
            return {
                description: form.description,
                owner: form.owner,
                schema_version: form.schemaVersion,
                flags: parsedFlags,
                compliance: compliancePayload,
                ...(includeExpectedRevision ? buildExpectedRevisionPayload() : {}),
            };
        }

        function buildCreatePayload(form, parsedFlags, compliancePayload, options = {}) {
            const { name = form.name } = options;
            return {
                name,
                description: form.description,
                owner: form.owner,
                schema_version: form.schemaVersion,
                flags: parsedFlags,
                compliance: compliancePayload,
            };
        }

        function buildConflictCopyName(form) {
            const sourceName = form.name || getCurrentProfile()?.name || t("profiles.conflict_copy_source_fallback");
            const revision = saveConflictState?.expectedRevision || getCurrentProfile()?.revision || "";
            const stamp = formatTimestamp(new Date());
            return t("profiles.conflict_copy_name")
                .replace("{name}", sourceName)
                .replace("{revision}", String(revision || "?"))
                .replace("{time}", stamp);
        }

        function hasComparableBase() {
            return Boolean(getComparableBaseId());
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
                "Homepage",
                "NewTabPage",
                "OverrideFirstRunPage",
                "OverridePostUpdatePage",
                "FirefoxHome",
                "SearchBar",
                "SearchEngines",
                "SearchSuggestEnabled",
                "FirefoxSuggest",
            ].includes(policyKey)) return "step_two";
            if ([
                "Permissions",
                "Cookies",
                "DisableTelemetry",
                "DisableFirefoxStudies",
                "DisablePrivateBrowsing",
                "OfferToSaveLogins",
                "OfferToSaveLoginsDefault",
                "PasswordManagerEnabled",
                "BlockAboutConfig",
                "BlockAboutProfiles",
                "DisableDeveloperTools",
                "DisableBuiltinPDFViewer",
                "SanitizeOnShutdown",
                "HttpsOnlyMode",
                "IPProtectionAvailable",
                "LocalNetworkAccess",
                "XSLTEnabled",
            ].includes(policyKey)) return "step_three";
            if ([
                "DisableFirefoxAccounts",
                "UserMessaging",
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
            ].includes(policyKey)) return "step_four";
            if (["AIControls", "GenerativeAI", "VisualSearchEnabled"].includes(policyKey)) return "step_five";
            return "step_two";
        }

        function resolveCompareAreaForPreference(key) {
            const prefKey = String(key || "");
            if (/proxy|network|dns|update|download|browser|homepage|newtab|firstrun|postupdate|home|search|suggest|urlbar/i.test(prefKey)) return "step_two";
            if (/cookie|permission|privacy|telemetry|password|https|sanitize|private/i.test(prefKey)) return "step_three";
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

            const comparableBaseState = (() => {
                try {
                    return getComparableBaseState();
                } catch {
                    return null;
                }
            })();

            if (!comparableBaseState) {
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

            const currentSnapshot = comparableBaseState.snapshot;
            if (!currentSnapshot) {
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
            compareCurrentCopyEl.textContent = comparableBaseState.profile?.id
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
            if (tone !== "error") {
                setValidationIssues([]);
            }
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
            if (listSummaryEl) {
                listSummaryEl.textContent = `${filtered}`;
                listSummaryEl.removeAttribute("aria-hidden");
            }
            if (listTotalSummaryEl) {
                listTotalSummaryEl.textContent = `${total}`;
                listTotalSummaryEl.removeAttribute("aria-hidden");
            }
            if (workspaceProfileCountEl) {
                workspaceProfileCountEl.textContent = `${total}`;
                workspaceProfileCountEl.removeAttribute("aria-hidden");
            }
            const workspaceProfileLabelEl = documentRef.getElementById("workspace-profile-label");
            if (workspaceProfileLabelEl) {
                workspaceProfileLabelEl.textContent = libraryCountLabel(total, getCurrentLang(), t);
                workspaceProfileLabelEl.removeAttribute("aria-hidden");
            }
            workspaceProfileCountEl?.closest(".compact-counter")?.classList.remove("compact-counter--pending");
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
            if (dockStatusTextEl) {
                dockStatusTextEl.textContent = workspaceSignalEl.textContent;
            }
            if (advancedReviewSaveStateEl) {
                advancedReviewSaveStateEl.textContent = workspaceSignalEl.textContent;
                advancedReviewSaveStateEl.dataset.reviewTone = invalid ? "error" : (dirty ? "warn" : "success");
            }
            return { dirty, invalid };
        }

        function setButtonDisabled(el, disabled) {
            if (!el) return;
            el.disabled = disabled;
            el.classList.toggle("pointer-events-none", disabled);
            el.classList.toggle("opacity-50", disabled);
        }

        function setLinkUnavailable(el, unavailable) {
            if (!el) return;
            el.classList.toggle("pointer-events-none", unavailable);
            el.classList.toggle("opacity-50", unavailable);
        }

        function setLinkHref(el, href) {
            if (!el) return;
            el.href = href;
        }

        function setEditorModeLinkState(el, { href = "#", available = true, active = false } = {}) {
            if (!el) return;
            el.href = href || "#";
            el.setAttribute("aria-disabled", available ? "false" : "true");
            if (available) {
                el.removeAttribute("title");
            } else {
                el.setAttribute("title", t("profiles.editor_chrome_save_first"));
            }
            if (active) {
                el.setAttribute("aria-current", "page");
            } else {
                el.removeAttribute("aria-current");
            }
            el.classList.toggle("pointer-events-none", !available);
            el.classList.toggle("opacity-50", !available);
            el.classList.toggle("primary-button", active);
            el.classList.toggle("ghost-button", !active);
            el.classList.toggle("text-white", active);
            el.classList.toggle("text-slate-700", !active);
        }

        function buildEditorModeHref(modeKey) {
            const currentId = getCurrentId();
            const includeDeleted = getCurrentProfile()?.is_deleted === true
                || documentRef.body?.dataset.includeDeleted === "true";
            const includeDeletedSuffix = includeDeleted ? "include_deleted=true" : "";
            if (modeKey === "guided") {
                if (!currentId) return "/profiles/new";
                return includeDeleted
                    ? `/profiles/${currentId}/edit?${includeDeletedSuffix}`
                    : `/profiles/${currentId}/edit`;
            }
            if (!currentId) return null;
            const returnPath = routeMode === "settings"
                ? `/profiles/${currentId}/settings${includeDeleted ? `?${includeDeletedSuffix}` : ""}`
                : (routeMode === "json"
                    ? `/profiles/${currentId}/json${includeDeleted ? `?${includeDeletedSuffix}` : ""}`
                    : `/profiles/${currentId}/edit${includeDeleted ? `?${includeDeletedSuffix}` : ""}`);
            if (modeKey === "settings") {
                const settingsFocusTarget = normalizeSettingsModeFocusTarget(advancedFocusTarget);
                const params = [];
                if (includeDeleted) {
                    params.push(includeDeletedSuffix);
                }
                params.push(`return=${encodeURIComponent(returnPath)}`);
                if (settingsFocusTarget) {
                    params.push(`focus=${encodeURIComponent(settingsFocusTarget)}`);
                }
                return `/profiles/${currentId}/settings?${params.join("&")}`;
            }
            const jsonFocusTarget = normalizeJsonModeFocusTarget(advancedFocusTarget);
            const params = [];
            if (includeDeleted) {
                params.push(includeDeletedSuffix);
            }
            params.push(`focus=${encodeURIComponent(jsonFocusTarget)}`);
            return `/profiles/${currentId}/json?${params.join("&")}`;
        }

        function refreshEditorModeLinks() {
            const hasSavedProfile = Boolean(getCurrentId());
            const guidedActive = routeMode === "new" || routeMode === "edit";
            const advancedMode = routeMode === "settings"
                ? "settings"
                : (isJsonModeFocusTarget(advancedFocusTarget) ? "json" : "settings");

            setEditorModeLinkState(editorModeGuidedEl, {
                href: buildEditorModeHref("guided"),
                available: true,
                active: guidedActive,
            });
            setEditorModeLinkState(editorModeSettingsEl, {
                href: buildEditorModeHref("settings"),
                available: hasSavedProfile,
                active: routeMode === "settings" || (routeMode === "json" && advancedMode === "settings"),
            });
            setEditorModeLinkState(editorModeJsonEl, {
                href: buildEditorModeHref("json"),
                available: hasSavedProfile,
                active: routeMode === "json" && advancedMode === "json",
            });
            if (editorModeLinksHintEl) {
                editorModeLinksHintEl.classList.toggle("support-hidden", hasSavedProfile);
            }
        }

        function updateActionState() {
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
            if (importFirefoxPoliciesButtonEl) {
                setButtonDisabled(importFirefoxPoliciesButtonEl, getIsBusy());
            }
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
                setLinkUnavailable(downloadFirefoxPolicies, true);
                setLinkUnavailable(wizardExportFirefoxPoliciesEl, true);
            } else {
                setLinkUnavailable(downloadFirefoxPolicies, false);
                setLinkUnavailable(wizardExportFirefoxPoliciesEl, false);
            }

            renderFinalExportStepSummary(dirty, invalid);
            syncWorkspaceOverview();
            renderCurrentStepActions?.();
        }

        function updateDownloadLinks() {
            const firefoxPoliciesLink = documentRef.getElementById("download-firefox-policies");
            if (!getCurrentId() || getCurrentProfile()?.is_deleted) {
                setLinkHref(firefoxPoliciesLink, "#");
                setLinkHref(wizardExportFirefoxPoliciesEl, "#");
                updateActionState();
                return;
            }
            const firefoxPoliciesHref = `/api/export/profiles/${getCurrentId()}/firefox/policies.json`;
            setLinkHref(firefoxPoliciesLink, firefoxPoliciesHref);
            setLinkHref(wizardExportFirefoxPoliciesEl, firefoxPoliciesHref);
            updateActionState();
        }

        function setDraftState(message, options = {}) {
            const { preserveCloneSource = false } = options;
            clearSaveConflictState();
            setCurrentProfile(null);
            setCurrentId(null);
            setWizardComplianceSnapshot(null);
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
            if (profileCompliancePanelEl) {
                profileCompliancePanelEl.hidden = true;
            }
            syncWizardFieldsFromForm();
            syncWorkspaceOverview();
            updateDownloadLinks();
            updateWizardContext();
            syncWizardNetworkFromEditor();
            syncWizardPreferencesFromEditor();
            syncWizardExtensionsFromEditor();
            renderList(getLibraryStats().items || []);
        }

        function formatComplianceLayerLabel(layer) {
            if (layer === "cis_l1") return t("profiles.wizard_cis_l1_title");
            if (layer === "cis_l2") return t("profiles.wizard_cis_l2_title");
            return t("profiles.wizard_cis_none_title");
        }

        function renderProfileComplianceSummary(profile) {
            if (!profileCompliancePanelEl || !profileComplianceCopyEl || !profileComplianceListEl) return;
            const compliance = profile?.compliance;
            if (!compliance || !compliance.layer || compliance.layer === "none") {
                profileCompliancePanelEl.hidden = true;
                profileComplianceListEl.innerHTML = "";
                return;
            }

            const decisions = Array.isArray(compliance.decisions) ? compliance.decisions : [];
            const raisedCount = decisions.filter((decision) =>
                decision.decision === "added_from_cis" || decision.decision === "cis_replaced_base",
            ).length;
            const manualCount = decisions.filter((decision) => decision.review_required).length;
            const exceptionCount = decisions.filter((decision) =>
                Boolean(decision.exception_note || decision.exceptionNote),
            ).length;

            const levelLabel = formatComplianceLayerLabel(compliance.layer);
            const version = compliance.benchmark_version || compliance.benchmarkVersion || "";
            const items = [
                t("profiles.compliance_summary_level").replace("{level}", levelLabel),
            ];
            if (version) {
                items.push(t("profiles.compliance_summary_version").replace("{version}", version));
            }
            items.push(t("profiles.compliance_summary_raised").replace("{count}", String(raisedCount)));
            items.push(t("profiles.compliance_summary_manual").replace("{count}", String(manualCount)));
            items.push(t("profiles.compliance_summary_exceptions").replace("{count}", String(exceptionCount)));

            profileComplianceCopyEl.textContent = t("profiles.compliance_summary_body");
            profileComplianceListEl.innerHTML = items
                .map((item) => `<div class="wizard-baseline-summary-item">${item}</div>`)
                .join("");
            profileCompliancePanelEl.hidden = false;
        }

        function setMeta(profile) {
            clearSaveConflictState();
            setCurrentProfile(profile);
            if (!profile) {
                setDraftState();
                return;
            }

            persistCompareBaseProfile(profile, buildProfileSnapshot(profile));

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

            setWizardStarter("keep_current", { preserveComplianceLayer: true });
            setWizardComplianceSnapshot(profile.compliance || null);
            if (profile?.compliance?.layer) {
                setWizardComplianceLayer(profile.compliance.layer, { skipApply: true, allowKeepCurrent: true });
            } else {
                setWizardComplianceLayer("none", { skipApply: true, allowKeepCurrent: true });
            }

            renderProfileComplianceSummary(profile);
            syncWizardFieldsFromForm();
            syncWorkspaceOverview();
            updateDownloadLinks();
            updateWizardContext();
            syncWizardNetworkFromEditor();
            syncWizardPreferencesFromEditor();
            syncWizardExtensionsFromEditor();
            updateActionState();
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
            setWizardComplianceSnapshot(sourceProfile?.compliance || null);
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
            renderProfileComplianceSummary(sourceProfile);
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
            if (!listEl) return;
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

            for (const profile of items) {
                const li = documentRef.createElement("li");
                li.className = "library-table-row";
                const selected = profile.id === getComparableBaseId();
                const canCompare = hasComparableBase() && !selected;
                const compareActive = compareProfileState?.profile?.id === profile.id;
                const canClone = Boolean(profile?.id);
                const openLabel = selected
                    ? t("profiles.list_open_selected")
                    : t("profiles.list_open");
                const compareLabel = compareActive
                    ? t("profiles.compare_selected")
                    : t("profiles.compare_action");
                const statusLabel = profile.is_deleted
                    ? t("profiles.badge_deleted")
                    : t("profiles.badge_active");
                const validationLabel = profile.validation_state === "invalid"
                    ? t("profiles.library_validation_invalid")
                    : profile.validation_state === "not_validated"
                        ? t("profiles.library_validation_not_validated")
                        : t("profiles.library_validation_valid");
                const validationClass = profile.validation_state === "invalid"
                    ? "profile-list-status--invalid"
                    : profile.validation_state === "not_validated"
                        ? "profile-list-status--not-validated"
                        : "profile-list-status--valid";
                const profileOwner = profile.owner || t("profiles.library_owner_unassigned");
                const profileDescription = profile.description || t("profiles.library_description_empty");
                const editHref = `/profiles/${profile.id}/edit`;
                const settingsHref = `/profiles/${profile.id}/settings${profile.is_deleted ? "?include_deleted=true" : ""}`;
                const jsonHref = `/profiles/${profile.id}/json${profile.is_deleted ? "?include_deleted=true" : ""}`;
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
                                <span class="profile-list-status ${validationClass}">
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
                                ${canClone ? `
                                    <button
                                        type="button"
                                        class="button-base ghost-button library-row-secondary-action profile-clone-button"
                                        data-clone-profile-id="${profile.id}">
                                        ${t("profiles.library_action_duplicate")}
                                    </button>
                                ` : ""}
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
                                ${canCompare ? `
                                    <button
                                        type="button"
                                        class="button-base ghost-button library-row-secondary-action profile-compare-button ${compareActive ? "profile-compare-button--active" : ""}"
                                        data-compare-profile-id="${profile.id}">
                                        ${compareLabel}
                                    </button>
                                ` : ""}
                            </div>
                        </div>
                    </div>
                `;
                const compareButton = li.querySelector("[data-compare-profile-id]");
                compareButton?.addEventListener("click", async () => {
                    await compareWithProfile(profile.id);
                });
                const openButton = li.querySelector(".library-row-open-button");
                openButton?.addEventListener("click", () => {
                    void (async () => {
                        try {
                            const comparableProfile = profile?.flags && typeof profile.flags === "object"
                                ? profile
                                : await getProfile(profile.id);
                            persistCompareBaseProfile(comparableProfile, buildProfileSnapshot(comparableProfile));
                            refreshCompareBaselineUi();
                        } catch {
                            // Ignore compare baseline prefetch failures and keep the navigation flow intact.
                        }
                    })();
                });
                const cloneButton = li.querySelector("[data-clone-profile-id]");
                cloneButton?.addEventListener("click", async () => {
                    await cloneFromProfile(profile.id, { includeDeleted: profile.is_deleted === true });
                });
                listEl.appendChild(li);
            }
        }

        const hasLibrarySurface = Boolean(
            listEl
            || listSummaryEl
            || listTotalSummaryEl
            || workspaceProfileCountEl
            || refreshButtonEl,
        );

        async function reloadList(options = {}) {
            const { announceStatus = hasLibrarySurface } = options;
            try {
                if (announceStatus) {
                    setStatus(t("profiles.status_loading_list"), "info");
                }
                const [items, stats] = await Promise.all([
                    listProfiles(),
                    getProfileLibraryStats(),
                ]);
                renderList(items);
                updateLibrarySummary(stats);
                if (announceStatus) {
                    setStatus(t("profiles.status_list_ready"), "info");
                }
            } catch (e) {
                setStatus(t("profiles.error_list").replace("{detail}", e.message || e), "error");
            }
        }

        async function loadProfile(id, options = {}) {
            const {
                keepCloneSource = false,
                skipConfirm = false,
                syncLibrary = hasLibrarySurface,
                announceLoaded = true,
            } = options;
            const editor = getEditor();
            try {
                if (!skipConfirm && !(await confirmIfDirty())) return;
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
                if (syncLibrary) {
                    const [items, stats] = await Promise.all([
                        listProfiles(),
                        getProfileLibraryStats(),
                    ]);
                    renderList(items);
                    updateLibrarySummary(stats);
                }
                documentRef.getElementById("overview-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
                if (announceLoaded) {
                    setStatus(t("profiles.status_profile_loaded").replace("{name}", profile.name), "success");
                }
            } catch (e) {
                setStatus(t("profiles.error_load").replace("{detail}", e.message || e), "error");
            }
        }

        async function cloneFromProfile(id, options = {}) {
            const editor = getEditor();
            try {
                if (!(await confirmIfDirty())) return;
                const profile = await getProfile(id, windowRef.fetch, options.includeDeleted === true);
                const schemaVersion = profile.schema_version || defaultSchemaVersion;
                const flags = profile.flags && typeof profile.flags === "object" ? profile.flags : {};
                documentRef.getElementById("profile-type").value = schemaVersion;
                documentRef.getElementById("mode").value = "json";
                setCurrentRaw(flags);
                editor?.setValue(toEditorValue(flags, documentRef.getElementById("mode").value));
                setCloneDraftState(profile);
                if (profile?.compliance?.layer) {
                    setWizardComplianceLayer(profile.compliance.layer, { skipApply: true, allowKeepCurrent: true });
                } else {
                    setWizardComplianceLayer("none", { skipApply: true, allowKeepCurrent: true });
                }
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
            if (importFirefoxPoliciesButtonEl) {
                setButtonDisabled(importFirefoxPoliciesButtonEl, true);
            }
        }

        async function saveCurrent(options = {}) {
            const { overwriteRevision = false } = options;
            const editor = getEditor();
            try {
                setBusyState(true, getCurrentId() ? "profiles.saving" : "profiles.creating");
                const form = readFormState();
                const mode = documentRef.getElementById("mode").value;
                const parsedFlags = fromEditorValue(editor.getValue(), mode);
                const complianceInfo = typeof getWizardComplianceMergeInfo === "function"
                    ? getWizardComplianceMergeInfo()
                    : { layer: "none" };
                const compliancePayload = complianceInfo.layer && complianceInfo.layer !== "none"
                    ? {
                        framework: "cis",
                        benchmark_id: complianceInfo.benchmark_id || "cis-firefox-esr-gpo",
                        benchmark_version: complianceInfo.benchmark_version || "1.0.0",
                        layer: complianceInfo.layer,
                        summary: complianceInfo.summary || {},
                        decisions: complianceInfo.decisions || [],
                    }
                    : null;

                if (!getCurrentId() && !form.name) {
                    setBusyState(false);
                    setStatus(t("profiles.create_name_required"), "warn");
                    nameInput.focus();
                    return false;
                }

                if (!getCurrentId()) {
                    const created = await createProfile(buildCreatePayload(form, parsedFlags, compliancePayload));
                    setLifecycleSessionNote(null);
                    setCurrentRaw(created.flags || {});
                    await reloadList();
                    await loadProfile(created.id, { keepCloneSource: Boolean(getCloneSourceProfile()?.name) });
                    clearSaveConflictState();
                    setStatus(t("profiles.status_profile_created").replace("{name}", created.name), "success");
                    setValidationPreview(t("profiles.validation_ready"), "success");
                    setBusyState(false);
                    return true;
                }

                const updated = await patchProfile(
                    getCurrentId(),
                    buildUpdatePayload(form, parsedFlags, compliancePayload, {
                        includeExpectedRevision: !overwriteRevision,
                    }),
                );
                setLifecycleSessionNote(null);
                setCurrentRaw(updated.flags || {});
                setMeta(updated);
                setBaselineFromCurrentUi();
                await reloadList();
                clearSaveConflictState();
                setStatus(t("profiles.status_profile_saved").replace("{name}", updated.name), "success");
                setValidationPreview(t("profiles.validation_ready"), "success");
                return true;
            } catch (e) {
                if (isRevisionConflictError(e)) {
                    showSaveConflictState(e);
                    return false;
                }
                setStatus(t("profiles.error_save").replace("{detail}", e.message || e), "error");
                return false;
            } finally {
                setBusyState(false);
            }
        }

        async function saveConflictAsCopy() {
            const editor = getEditor();
            if (!saveConflictState?.profileId && !getCurrentId()) {
                setStatus(t("profiles.select_profile_first"), "warn");
                return false;
            }

            try {
                setBusyState(true, "profiles.creating");
                const form = readFormState();
                const mode = documentRef.getElementById("mode").value;
                const parsedFlags = fromEditorValue(editor.getValue(), mode);
                const complianceInfo = typeof getWizardComplianceMergeInfo === "function"
                    ? getWizardComplianceMergeInfo()
                    : { layer: "none" };
                const compliancePayload = complianceInfo.layer && complianceInfo.layer !== "none"
                    ? {
                        framework: "cis",
                        benchmark_id: complianceInfo.benchmark_id || "cis-firefox-esr-gpo",
                        benchmark_version: complianceInfo.benchmark_version || "1.0.0",
                        layer: complianceInfo.layer,
                        summary: complianceInfo.summary || {},
                        decisions: complianceInfo.decisions || [],
                    }
                    : null;
                const copyName = buildConflictCopyName(form);
                const created = await createProfile(
                    buildCreatePayload(form, parsedFlags, compliancePayload, { name: copyName }),
                );

                setCloneSourceProfile(null);
                setLifecycleSessionNote(null);
                setCurrentRaw(created.flags || {});
                await reloadList();
                await loadProfile(created.id, { skipConfirm: true });
                clearSaveConflictState();
                setStatus(t("profiles.conflict_copy_created").replace("{name}", created.name), "success");
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
                const currentProfile = getCurrentProfile();
                const archivedProfile = {
                    ...(currentProfile && typeof currentProfile === "object" ? currentProfile : {}),
                    id: getCurrentId(),
                    name: currentProfile?.name || nameInput.value.trim() || t("profiles.none_selected"),
                    owner: currentProfile?.owner || ownerInput.value.trim() || null,
                    description: currentProfile?.description || descriptionInput.value.trim() || null,
                    schema_version: currentProfile?.schema_version
                        || documentRef.getElementById("profile-type").value
                        || defaultSchemaVersion,
                    flags: getCurrentRaw() && typeof getCurrentRaw() === "object" ? getCurrentRaw() : {},
                    updated_at: new Date().toISOString(),
                    deleted_at: new Date().toISOString(),
                    is_deleted: true,
                };
                await softDeleteProfile(getCurrentId());
                await reloadList();
                setCurrentRaw(archivedProfile.flags || {});
                setMeta(archivedProfile);
                setBaselineFromCurrentUi();
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
                const deletedProfileId = getCurrentId();
                await hardDeleteProfile(deletedProfileId);
                clearStoredCompareBase(deletedProfileId);
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
                const document = parseEditorPolicyDocument(
                    editor.getValue(),
                    documentRef.getElementById("mode").value,
                );
                const res = await validateFlags(profileKey, document);
                if (res.ok) {
                    setValidationIssues([]);
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
                setValidationIssues(Array.isArray(e.detail?.issues) ? e.detail.issues : []);
                setStatus(t("profiles.error_validation_failed").replace("{detail}", e.message || e), "error");
                setValidationPreview(e.message || String(e), "error");
            } finally {
                renderAllSettingsList?.();
                setBusyState(false);
            }
        }

        async function doImportFirefoxPoliciesJson(file) {
            if (!file) {
                setImportStatus(t("profiles.import_firefox_policies_ready"));
                return null;
            }
            if (!(await confirmIfDirty())) {
                setImportStatus(t("profiles.import_firefox_policies_cancelled"), "warn");
                return null;
            }

            try {
                setBusyState(true, "profiles.importing_firefox_policies");
                const profileName = inferImportProfileName(file);
                setImportStatus(
                    t("profiles.import_firefox_policies_reading")
                        .replace("{file}", file.name || "policies.json")
                        .replace("{name}", profileName),
                    "info",
                );

                const rawText = await file.text();
                let document;
                try {
                    document = JSON.parse(rawText);
                } catch (parseError) {
                    throw new Error(
                        t("profiles.error_import_firefox_policies_parse")
                            .replace("{detail}", parseError.message || parseError),
                    );
                }

                const schemaVersion = documentRef.getElementById("profile-type").value || defaultSchemaVersion;
                const imported = await importFirefoxPoliciesJson({
                    name: profileName,
                    description: t("profiles.import_firefox_policies_description")
                        .replace("{name}", file.name || "policies.json"),
                    schema_version: schemaVersion,
                    document,
                });

                setCloneSourceProfile(null);
                setLifecycleSessionNote(null);
                setImportStatus(
                    t("profiles.status_import_firefox_policies_done")
                        .replace("{name}", imported.name)
                        .replace("{schema}", formatSchemaLabel(imported.schema_version))
                        .replace(
                            "{validation}",
                            imported.validation_state === "invalid"
                                ? t("profiles.library_validation_invalid")
                                : imported.validation_state === "not_validated"
                                    ? t("profiles.library_validation_not_validated")
                                    : t("profiles.library_validation_valid"),
                        ),
                    "success",
                );
                await reloadList();
                await loadProfile(imported.id, { skipConfirm: true });
                setStatus(
                    t("profiles.status_import_firefox_policies_done")
                        .replace("{name}", imported.name)
                        .replace("{schema}", formatSchemaLabel(imported.schema_version))
                        .replace(
                            "{validation}",
                            imported.validation_state === "invalid"
                                ? t("profiles.library_validation_invalid")
                                : imported.validation_state === "not_validated"
                                    ? t("profiles.library_validation_not_validated")
                                    : t("profiles.library_validation_valid"),
                        ),
                    "success",
                );
                setValidationPreview(t("profiles.validation_ready"), "success");
                return imported;
            } catch (e) {
                const message = e.message || String(e);
                setImportStatus(
                    t("profiles.error_import_firefox_policies").replace("{detail}", message),
                    "error",
                );
                setStatus(
                    t("profiles.error_import_firefox_policies").replace("{detail}", message),
                    "error",
                );
                return null;
            } finally {
                if (importFirefoxPoliciesFileEl) {
                    importFirefoxPoliciesFileEl.value = "";
                }
                setBusyState(false);
            }
        }

        compareClearEl?.addEventListener("click", () => {
            clearCompareProfile();
        });

        saveConflictReloadEl?.addEventListener("click", async () => {
            const profileId = saveConflictState?.profileId || getCurrentId();
            if (!profileId) return;
            await loadProfile(profileId, { skipConfirm: true });
            clearSaveConflictState();
            setStatus(t("profiles.conflict_reloaded"), "success");
        });

        saveConflictSaveCopyEl?.addEventListener("click", async () => {
            await saveConflictAsCopy();
        });

        saveConflictOverwriteEl?.addEventListener("click", async () => {
            if (!getCurrentId()) return;
            if (!windowRef.confirm(t("profiles.conflict_overwrite_confirm"))) return;
            await saveCurrent({ overwriteRevision: true });
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

        function refreshCompareBaselineUi() {
            if (compareProfileState?.profile?.id === getComparableBaseId()) {
                compareProfileState = null;
            }
            renderComparePanel();
            renderList(getLibraryStats().items || []);
        }

        windowRef.addEventListener?.("storage", (event) => {
            if (event.key !== compareBaseStorageKey) return;
            refreshCompareBaselineUi();
        });
        windowRef.addEventListener?.("focus", refreshCompareBaselineUi);
        documentRef.addEventListener?.("visibilitychange", () => {
            if (documentRef.visibilityState === "visible") {
                refreshCompareBaselineUi();
            }
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
            cloneFromProfile,
            readFormState,
            buildCreatePayload,
            buildSnapshot,
            buildProfileSnapshot,
            buildCompareDiff,
            saveCurrent,
            saveConflictAsCopy,
            doSoftDelete,
            doHardDelete,
            doRestore,
            doResetLibrary,
            doValidate,
            doImportFirefoxPoliciesJson,
        };
    }

    window.BPMProfilesWorkspace = { create };
})();
