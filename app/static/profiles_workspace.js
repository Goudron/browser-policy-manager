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
            nameInput,
            ownerInput,
            descriptionInput,
            nameHintEl,
            currentNameEl,
            currentMetaEl,
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
            wizardExportSaveActionEl,
            wizardExportValidateActionEl,
            wizardExportJsonEl,
            wizardExportYamlEl,
            wizardExportFirefoxPoliciesEl,
            wizardFinishEl,
        } = elements;
        const defaultSchemaVersion = getDefaultSchemaVersion(documentRef);

        function syncWorkspaceOverview() {
            const schemaVersion = documentRef.getElementById("profile-type").value || defaultSchemaVersion;
            const mode = documentRef.getElementById("mode").value || "json";
            overviewSchemaEl.textContent = formatSchemaLabel(schemaVersion);
            overviewModeEl.textContent = mode.toUpperCase();

            if (getCurrentProfile()?.is_deleted) {
                overviewContextEl.textContent = t("profiles.overview_deleted");
            } else if (getCurrentId()) {
                overviewContextEl.textContent = t("profiles.overview_existing");
            } else {
                overviewContextEl.textContent = t("profiles.overview_draft");
            }

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

        function readFormState() {
            return {
                name: nameInput.value.trim(),
                owner: ownerInput.value.trim() || null,
                description: descriptionInput.value.trim() || null,
                schemaVersion: documentRef.getElementById("profile-type").value,
            };
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

        function setBaselineFromCurrentUi() {
            setBaselineSnapshot(snapshotToString(buildSnapshot()));
            refreshWorkspaceSignal();
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
            validationPreviewEl.className = tone === "error"
                ? "max-w-full text-xs text-red-700"
                : tone === "success"
                    ? "max-w-full text-xs text-emerald-700"
                    : "max-w-full text-xs text-slate-500";
        }

        function updateLibrarySummary(stats) {
            const filtered = Number(stats?.filtered || 0);
            const total = Number(stats?.total || 0);
            setLibraryStats({ filtered, total });
            listSummaryEl.textContent = `${filtered}`;
            listTotalSummaryEl.textContent = `${total}`;
            workspaceProfileCountEl.textContent = `${total}`;
            documentRef.getElementById("workspace-profile-label").textContent = libraryCountLabel(total, getCurrentLang());
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

        function setDraftState(message) {
            setCurrentProfile(null);
            setCurrentId(null);
            setWizardStarter("blank");
            currentNameEl.textContent = t("profiles.none_selected");
            currentMetaEl.textContent = message || "";
            stateBadgeEl.textContent = t("profiles.badge_draft");
            stateBadgeEl.className = "state-chip state-chip--draft";
            nameInput.disabled = false;
            nameHintEl.textContent = t("profiles.name_hint");
            setWorkspaceHelper(
                t("profiles.helper_no_selection_title"),
                t("profiles.helper_no_selection_body"),
            );
            setValidationPreview();
            syncWizardFieldsFromForm();
            syncWorkspaceOverview();
            updateDownloadLinks();
            updateWizardContext();
            syncWizardNetworkFromEditor();
            syncWizardPreferencesFromEditor();
            syncWizardExtensionsFromEditor();
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
            setValidationPreview();
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

        function renderList(items) {
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
                const selected = profile.id === getCurrentId();
                li.innerHTML = `
                    <button class="profile-list-button px-4 py-3 text-left ${selected ? "profile-list-button--selected" : ""}">
                        <div class="flex items-start justify-between gap-3">
                            <div class="min-w-0">
                                <div class="truncate text-sm font-semibold text-slate-900">${profile.name}</div>
                                <div class="mt-2 flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-[0.16em] text-slate-400">
                                    <span>${formatSchemaLabel(profile.schema_version)}</span>
                                    <span>${formatTimestamp(profile.updated_at)}</span>
                                </div>
                            </div>
                            <span class="profile-list-status ${profile.is_deleted
                                ? "profile-list-status--deleted"
                                : "profile-list-status--active"}">
                                ${profile.is_deleted ? t("profiles.badge_deleted") : t("profiles.badge_active")}
                            </span>
                        </div>
                        <div class="profile-list-footer">
                            <span class="text-xs text-slate-500">${selected
                                ? t("profiles.list_selected_hint")
                                : t("profiles.list_click_hint")}</span>
                            <span class="profile-open-cta ${selected ? "profile-open-cta--selected" : ""}">${selected
                                ? t("profiles.list_open_selected")
                                : t("profiles.list_open")}</span>
                        </div>
                    </button>
                `;
                li.querySelector("button").addEventListener("click", async () => {
                    await loadProfile(profile.id);
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

        async function loadProfile(id) {
            const editor = getEditor();
            try {
                if (!(await confirmIfDirty())) return;
                const profile = await getProfile(id);
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
                    setCurrentRaw(created.flags || {});
                    await reloadList();
                    await loadProfile(created.id);
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
