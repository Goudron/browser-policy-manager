(() => {
    function create({
        documentRef = document,
        elements = {},
        dependencies = {},
    }) {
        const windowRef = documentRef.defaultView || window;
        function readEmbeddedInitialLocale() {
            const payloadEl = documentRef.getElementById("profiles-initial-locale");
            const payloadText = (payloadEl?.tagName || "").toUpperCase() === "TEMPLATE"
                ? (payloadEl?.innerHTML ? payloadEl.innerHTML.trim() : "")
                : (payloadEl?.textContent ? payloadEl.textContent.trim() : "");
            if (!payloadText) {
                return {};
            }
            try {
                const parsed = JSON.parse(payloadText);
                return parsed && typeof parsed === "object" ? parsed : {};
            } catch {
                return {};
            }
        }
        const {
            fromEditorValue,
            formatBooleanSelectValue,
            parseBooleanSelectValue,
            getDefaultSchemaVersion,
        } = dependencies;
        const {
            statusEl,
            workspaceHelperTitleEl,
            workspaceHelperCopyEl,
            wizardSchemaEl,
        } = elements;

        let editor = null;
        let currentId = null;
        let currentProfile = null;
        let currentRaw = {};
        const initialLang = typeof windowRef.__BPM_INITIAL_LANG__ === "string" && windowRef.__BPM_INITIAL_LANG__
            ? windowRef.__BPM_INITIAL_LANG__
            : (documentRef.documentElement.lang || "en");
        const bootLocale = windowRef.__BPM_INITIAL_LOCALE__ && typeof windowRef.__BPM_INITIAL_LOCALE__ === "object"
            ? windowRef.__BPM_INITIAL_LOCALE__
            : {};
        const initialLocale = Object.keys(bootLocale).length > 0
            ? bootLocale
            : readEmbeddedInitialLocale();

        windowRef.__BPM_INITIAL_LANG__ = initialLang;
        windowRef.__BPM_INITIAL_LOCALE__ = initialLocale;

        let currentLang = initialLang;
        let localeDict = initialLocale;
        let searchTimer = null;
        let baselineSnapshot = null;
        let cloneSourceProfile = null;
        let lifecycleSessionNote = null;
        let isBusy = false;
        let libraryStats = { filtered: 0, total: 0 };
        let validationPreviewTone = "neutral";

        let renderExtensionReviewSummaryRef = () => { };
        let renderManualHomeAndSearchSectionStatusesRef = () => { };
        let renderNetworkReviewSummaryRef = () => { };
        let renderHomeReviewSummaryRef = () => { };
        let renderSearchReviewSummaryRef = () => { };
        let renderAiReviewSummaryRef = () => { };
        let renderBookmarkReviewSummaryRef = () => { };
        let renderWebsiteAccessReviewSummaryRef = () => { };
        let renderPrivacyReviewSummaryRef = () => { };
        let buildWizardSettingsSearchIndexRef = () => { };
        let renderWizardSettingsSearchResultsRef = () => { };
        let setWizardStepRef = () => { };
        let updateWizardSummaryRef = () => { };
        let currentSnapshotStateRef = () => ({ dirty: true, invalid: true });
        let saveCurrentRef = async () => false;
        const defaultSchemaVersion = getDefaultSchemaVersion(documentRef);
        let readFormStateRef = () => ({
            name: "",
            owner: null,
            description: null,
            schemaVersion: defaultSchemaVersion,
        });

        function t(key, fallback = "") {
            if (Object.prototype.hasOwnProperty.call(localeDict, key)) {
                return localeDict[key];
            }
            const bootLocale = windowRef.__BPM_INITIAL_LOCALE__;
            if (bootLocale && Object.prototype.hasOwnProperty.call(bootLocale, key)) {
                return bootLocale[key];
            }
            return fallback;
        }

        function getActiveWizardSchemaVersion() {
            return documentRef.getElementById("profile-type").value || wizardSchemaEl.value || defaultSchemaVersion;
        }

        function readWizardSchemaSource() {
            if (!editor) return { ok: true, data: currentRaw && typeof currentRaw === "object" ? currentRaw : {} };

            try {
                const parsed = fromEditorValue(editor.getValue(), documentRef.getElementById("mode").value);
                return { ok: true, data: parsed && typeof parsed === "object" ? parsed : {} };
            } catch {
                return { ok: false, data: {} };
            }
        }

        function setWorkspaceHelper(title, body) {
            workspaceHelperTitleEl.textContent = title;
            workspaceHelperCopyEl.textContent = body;
        }

        function syncBooleanSelectGroup(inputs, source, keyAttr) {
            inputs.forEach((input) => {
                input.disabled = false;
                input.value = formatBooleanSelectValue(source?.[input.dataset[keyAttr]]);
            });
        }

        function applyBooleanSelectGroup(inputs, target, keyAttr) {
            inputs.forEach((input) => {
                const key = input.dataset[keyAttr];
                const nextValue = parseBooleanSelectValue(input.value);
                if (!key || nextValue === null) return;
                target[key] = nextValue;
            });
        }

        function setStatus(msg, tone = "info") {
            const classes = {
                info: "status-banner status-banner--info rounded-2xl border px-4 py-3 text-sm",
                success: "status-banner status-banner--success rounded-2xl border px-4 py-3 text-sm",
                error: "status-banner status-banner--error rounded-2xl border px-4 py-3 text-sm",
                warn: "status-banner status-banner--warn rounded-2xl border px-4 py-3 text-sm",
            };
            statusEl.className = classes[tone] || classes.info;
            statusEl.textContent = msg;
        }

        function getEditor() {
            return editor;
        }

        function setEditor(value) {
            editor = value;
        }

        function getCurrentId() {
            return currentId;
        }

        function setCurrentId(value) {
            currentId = value;
        }

        function getCurrentProfile() {
            return currentProfile;
        }

        function setCurrentProfile(value) {
            currentProfile = value;
        }

        function getCurrentRaw() {
            return currentRaw;
        }

        function setCurrentRaw(value) {
            currentRaw = value;
        }

        function getCurrentLang() {
            return currentLang;
        }

        function setCurrentLang(value) {
            currentLang = value || "en";
        }

        function setLocaleDict(value) {
            localeDict = value && typeof value === "object" ? value : {};
        }

        function getSearchTimer() {
            return searchTimer;
        }

        function setSearchTimer(value) {
            searchTimer = value;
        }

        function getBaselineSnapshot() {
            return baselineSnapshot;
        }

        function setBaselineSnapshot(value) {
            baselineSnapshot = value;
        }

        function getCloneSourceProfile() {
            return cloneSourceProfile;
        }

        function setCloneSourceProfile(value) {
            cloneSourceProfile = value;
        }

        function getLifecycleSessionNote() {
            return lifecycleSessionNote;
        }

        function setLifecycleSessionNote(value) {
            lifecycleSessionNote = value;
        }

        function getIsBusy() {
            return isBusy;
        }

        function setIsBusy(value) {
            isBusy = value;
        }

        function getLibraryStats() {
            return libraryStats;
        }

        function setLibraryStats(value) {
            libraryStats = value;
        }

        function getValidationPreviewTone() {
            return validationPreviewTone;
        }

        function setValidationPreviewTone(value) {
            validationPreviewTone = value;
        }

        function renderExtensionReviewSummary(...args) {
            return renderExtensionReviewSummaryRef(...args);
        }

        function setRenderExtensionReviewSummary(fn) {
            renderExtensionReviewSummaryRef = fn || (() => { });
        }

        function renderManualHomeAndSearchSectionStatuses(...args) {
            return renderManualHomeAndSearchSectionStatusesRef(...args);
        }

        function setRenderManualHomeAndSearchSectionStatuses(fn) {
            renderManualHomeAndSearchSectionStatusesRef = fn || (() => { });
        }

        function renderNetworkReviewSummary(...args) {
            return renderNetworkReviewSummaryRef(...args);
        }

        function setRenderNetworkReviewSummary(fn) {
            renderNetworkReviewSummaryRef = fn || (() => { });
        }

        function renderHomeReviewSummary(...args) {
            return renderHomeReviewSummaryRef(...args);
        }

        function setRenderHomeReviewSummary(fn) {
            renderHomeReviewSummaryRef = fn || (() => { });
        }

        function renderSearchReviewSummary(...args) {
            return renderSearchReviewSummaryRef(...args);
        }

        function setRenderSearchReviewSummary(fn) {
            renderSearchReviewSummaryRef = fn || (() => { });
        }

        function renderAiReviewSummary(...args) {
            return renderAiReviewSummaryRef(...args);
        }

        function setRenderAiReviewSummary(fn) {
            renderAiReviewSummaryRef = fn || (() => { });
        }

        function renderBookmarkReviewSummary(...args) {
            return renderBookmarkReviewSummaryRef(...args);
        }

        function setRenderBookmarkReviewSummary(fn) {
            renderBookmarkReviewSummaryRef = fn || (() => { });
        }

        function renderWebsiteAccessReviewSummary(...args) {
            return renderWebsiteAccessReviewSummaryRef(...args);
        }

        function setRenderWebsiteAccessReviewSummary(fn) {
            renderWebsiteAccessReviewSummaryRef = fn || (() => { });
        }

        function renderPrivacyReviewSummary(...args) {
            return renderPrivacyReviewSummaryRef(...args);
        }

        function setRenderPrivacyReviewSummary(fn) {
            renderPrivacyReviewSummaryRef = fn || (() => { });
        }

        function buildWizardSettingsSearchIndex(...args) {
            return buildWizardSettingsSearchIndexRef(...args);
        }

        function setBuildWizardSettingsSearchIndex(fn) {
            buildWizardSettingsSearchIndexRef = fn || (() => { });
        }

        function renderWizardSettingsSearchResults(...args) {
            return renderWizardSettingsSearchResultsRef(...args);
        }

        function setRenderWizardSettingsSearchResults(fn) {
            renderWizardSettingsSearchResultsRef = fn || (() => { });
        }

        function setWizardStep(...args) {
            return setWizardStepRef(...args);
        }

        function setSetWizardStep(fn) {
            setWizardStepRef = fn || (() => { });
        }

        function updateWizardSummary(...args) {
            return updateWizardSummaryRef(...args);
        }

        function setUpdateWizardSummary(fn) {
            updateWizardSummaryRef = fn || (() => { });
        }

        function currentSnapshotState(...args) {
            return currentSnapshotStateRef(...args);
        }

        function setCurrentSnapshotState(fn) {
            currentSnapshotStateRef = fn || (() => ({ dirty: true, invalid: true }));
        }

        function saveCurrent(...args) {
            return saveCurrentRef(...args);
        }

        function setSaveCurrent(fn) {
            saveCurrentRef = fn || (async () => false);
        }

        function readFormState(...args) {
            return readFormStateRef(...args);
        }

        function setReadFormState(fn) {
            readFormStateRef = fn || (() => ({
                name: "",
                owner: null,
                description: null,
                schemaVersion: "esr-140.9",
            }));
        }

        return {
            t,
            getActiveWizardSchemaVersion,
            readWizardSchemaSource,
            setWorkspaceHelper,
            syncBooleanSelectGroup,
            applyBooleanSelectGroup,
            setStatus,
            getEditor,
            setEditor,
            getCurrentId,
            setCurrentId,
            getCurrentProfile,
            setCurrentProfile,
            getCurrentRaw,
            setCurrentRaw,
            getCurrentLang,
            setCurrentLang,
            setLocaleDict,
            getSearchTimer,
            setSearchTimer,
            getBaselineSnapshot,
            setBaselineSnapshot,
            getCloneSourceProfile,
            setCloneSourceProfile,
            getLifecycleSessionNote,
            setLifecycleSessionNote,
            getIsBusy,
            setIsBusy,
            getLibraryStats,
            setLibraryStats,
            getValidationPreviewTone,
            setValidationPreviewTone,
            renderExtensionReviewSummary,
            setRenderExtensionReviewSummary,
            renderManualHomeAndSearchSectionStatuses,
            setRenderManualHomeAndSearchSectionStatuses,
            renderNetworkReviewSummary,
            setRenderNetworkReviewSummary,
            renderHomeReviewSummary,
            setRenderHomeReviewSummary,
            renderSearchReviewSummary,
            setRenderSearchReviewSummary,
            renderAiReviewSummary,
            setRenderAiReviewSummary,
            renderBookmarkReviewSummary,
            setRenderBookmarkReviewSummary,
            renderWebsiteAccessReviewSummary,
            setRenderWebsiteAccessReviewSummary,
            renderPrivacyReviewSummary,
            setRenderPrivacyReviewSummary,
            buildWizardSettingsSearchIndex,
            setBuildWizardSettingsSearchIndex,
            renderWizardSettingsSearchResults,
            setRenderWizardSettingsSearchResults,
            setWizardStep,
            setSetWizardStep,
            updateWizardSummary,
            setUpdateWizardSummary,
            currentSnapshotState,
            setCurrentSnapshotState,
            saveCurrent,
            setSaveCurrent,
            readFormState,
            setReadFormState,
        };
    }

    window.BPMProfilesShared = { create };
})();
