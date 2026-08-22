    function create({
        documentRef = document,
        elements = {},
        dependencies = {},
        state = {},
    }) {
        const {
            t,
            linesToArray,
            fromEditorValue,
            toEditorValue,
            setStatus,
            renderExtensionReviewSummary,
            updateWizardSummary,
            getActiveWizardSchemaVersion,
            getComplianceInfo = () => null,
            getManualEdits = () => [],
        } = dependencies;
        const getEditor = state.getEditor || (() => null);
        const setCurrentRaw = state.setCurrentRaw || (() => {});
        const getCurrentProfile = state.getCurrentProfile || (() => null);
        const setCurrentProfile = state.setCurrentProfile || (() => {});

        const {
            wizardExtensionAmoSearchFormEl,
            wizardExtensionAmoQueryEl,
            wizardExtensionAmoSearchSubmitEl,
            wizardExtensionAmoSearchStatusEl,
            wizardExtensionAmoManualFocusEl,
            wizardExtensionAmoSearchResultsEl,
            wizardExtensionAmoSelectedRulesEl,
            wizardExtensionRuleAddFormEl,
            wizardExtensionRuleGuidEl,
            wizardExtensionRuleInstallUrlEl,
            wizardExtensionRuleStatusEl,
            wizardExtensionRulesEl,
            wizardExtensionRawRulesEl,
            wizardExtensionUpdateEl,
            wizardExtensionInstallDefaultEl,
            wizardExtensionInstallAllowEl,
            wizardExtensionInstallEl,
            wizardExtensionLockedEl,
            wizardExtensionUninstallEl,
            wizardSyncSectionStatusEl,
            wizardSyncFineTuningToggleEl,
            wizardSyncFineTuningPanelEl,
            wizardLanguageSectionStatusEl,
            wizardLanguageAiHandoffEl,
            wizardAiEsrcEmptyStateEl,
            wizardAiReleaseContentEl,
            wizardAiPostureBarEl,
            wizardAiPostureBodyEl,
            wizardAiPosturePresetsEl,
            wizardAiPolicyControlsEl,
            wizardAiSectionStatusEl,
            wizardAiControlsCardEl,
            wizardGenerativeAiCardEl,
            wizardVisualSearchEnabledCardEl,
            wizardAiGovernanceCopyEl,
        } = elements;
        let syncPanelPreference = null;
        let amoSearchAbortController = null;
        let amoSearchSequence = 0;
        const amoSelectedRules = new Map();
        const aiPosturePresetButtons = Array.from(document.querySelectorAll("[data-ai-posture-preset]"));
        const syncFocusPresetButtons = Array.from(documentRef.querySelectorAll("[data-sync-focus-preset]"));
        const languagePresetButtons = Array.from(documentRef.querySelectorAll("[data-language-preset]"));

        function setText(el, value) {
            if (el) {
                el.textContent = String(value);
            }
        }

        function isVerifiedFirefoxGuid(value) {
            return typeof value === "string" && (
                /^[A-Za-z0-9][A-Za-z0-9._-]{0,126}@[A-Za-z0-9][A-Za-z0-9.-]{0,126}$/.test(value)
                || /^\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}$/.test(value)
            );
        }

        function amoLocale() {
            const rawLocale = documentRef.getElementById("profiles-initial-locale")?.textContent;
            try {
                const parsed = JSON.parse(rawLocale || '"en"');
                if (["en", "ru", "de", "es-ES", "fr", "zh-CN"].includes(parsed)) return parsed;
            } catch {
                // The query stays local when the authored locale bootstrap is malformed.
            }
            return "en";
        }

        function setAmoSearchStatus(messageKey) {
            setText(wizardExtensionAmoSearchStatusEl, t(messageKey));
        }

        function clearAmoSearchResults() {
            if (!wizardExtensionAmoSearchResultsEl) return;
            wizardExtensionAmoSearchResultsEl.replaceChildren();
            wizardExtensionAmoSearchResultsEl.hidden = true;
        }

        function setAmoManualRecoveryVisible(visible) {
            if (wizardExtensionAmoManualFocusEl) wizardExtensionAmoManualFocusEl.hidden = !visible;
        }

        function focusManualExtensionEntry() {
            wizardExtensionRuleAddFormEl?.scrollIntoView({ behavior: "smooth", block: "center" });
            wizardExtensionRuleGuidEl?.focus({ preventScroll: true });
        }

        function setAmoSearchUnavailable() {
            clearAmoSearchResults();
            setAmoSearchStatus("profiles.wizard_extensions_amo_search_unavailable");
            setAmoManualRecoveryVisible(true);
        }

        function extensionSettingsFromEditor() {
            const editor = getEditor();
            if (!editor) return null;
            const mode = documentRef.getElementById("mode")?.value || "";
            const parsed = fromEditorValue(editor.getValue(), mode);
            const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
            const extensionSettings = normalized.ExtensionSettings && typeof normalized.ExtensionSettings === "object"
                ? { ...normalized.ExtensionSettings }
                : {};
            return { editor, mode, normalized, extensionSettings };
        }

        function renderAmoSelectedRules() {
            if (!wizardExtensionAmoSelectedRulesEl) return;
            wizardExtensionAmoSelectedRulesEl.replaceChildren();
            wizardExtensionAmoSelectedRulesEl.hidden = amoSelectedRules.size === 0;

            amoSelectedRules.forEach((result, guid) => {
                const card = documentRef.createElement("div");
                card.className = "wizard-extension-amo-rule";
                card.dataset.extensionAmoRule = guid;

                const identity = documentRef.createElement("div");
                identity.className = "wizard-extension-amo-identity";
                const name = documentRef.createElement("strong");
                name.textContent = result.name || guid;
                const meta = documentRef.createElement("span");
                meta.className = "wizard-extension-amo-guid";
                meta.textContent = result.version
                    ? `${guid} • ${t("profiles.wizard_extensions_amo_version").replace("{version}", result.version)}`
                    : guid;
                identity.append(name, meta);

                const modeLabel = documentRef.createElement("label");
                modeLabel.className = "wizard-input-stack";
                const labelText = documentRef.createElement("span");
                labelText.className = "field-label";
                labelText.textContent = t("profiles.wizard_extensions_amo_rule_mode_label");
                const select = documentRef.createElement("select");
                select.className = "soft-input";
                select.dataset.extensionAmoRuleMode = guid;
                [
                    ["allowed", "profiles.wizard_extension_profile_mode_allowed"],
                    ["blocked", "profiles.wizard_extension_profile_mode_blocked"],
                ].forEach(([value, key]) => {
                    const option = documentRef.createElement("option");
                    option.value = value;
                    option.textContent = t(key);
                    select.append(option);
                });
                select.value = result.mode === "blocked" ? "blocked" : "allowed";
                select.addEventListener("change", () => {
                    applyAmoRuleMode(guid, select.value);
                });
                modeLabel.append(labelText, select);
                card.append(identity, modeLabel);
                wizardExtensionAmoSelectedRulesEl.append(card);
            });
        }

        function syncAmoSelectedRulesFromPolicy(extensionSettings) {
            Object.entries(extensionSettings).forEach(([guid, settings]) => {
                if (!isVerifiedFirefoxGuid(guid) || !settings || typeof settings !== "object") return;
                if (!Object.prototype.hasOwnProperty.call(settings, "installation_mode")) return;
                const current = amoSelectedRules.get(guid);
                amoSelectedRules.set(guid, {
                    guid,
                    name: current?.name || guid,
                    version: current?.version || "",
                    mode: settings.installation_mode === "blocked" ? "blocked" : "allowed",
                });
            });
            renderAmoSelectedRules();
        }

        function applyAmoRuleMode(guid, selectedMode) {
            if (!isVerifiedFirefoxGuid(guid) || !["allowed", "blocked"].includes(selectedMode)) return;
            const current = amoSelectedRules.get(guid) || { guid, name: guid, version: "" };
            amoSelectedRules.set(guid, { ...current, mode: selectedMode });
            setExtensionRuleMode(guid, selectedMode, { source: "amo-assisted-manual" });
        }

        function selectAmoResult(result) {
            if (!result || !isVerifiedFirefoxGuid(result.guid)) return;
            amoSelectedRules.set(result.guid, {
                guid: result.guid,
                name: typeof result.name === "string" ? result.name : result.guid,
                version: typeof result.version === "string" ? result.version : "",
                mode: "allowed",
            });
            setExtensionRuleMode(result.guid, "allowed", { source: "amo-assisted-manual" });
            setAmoSearchStatus("profiles.wizard_extensions_amo_rule_created");
        }

        function renderAmoSearchResults(results) {
            clearAmoSearchResults();
            if (!wizardExtensionAmoSearchResultsEl) return;
            results.forEach((result) => {
                if (!result || !isVerifiedFirefoxGuid(result.guid)) return;
                const row = documentRef.createElement("div");
                row.className = "wizard-extension-amo-result";
                row.setAttribute("role", "listitem");
                const identity = documentRef.createElement("div");
                identity.className = "wizard-extension-amo-identity";
                const name = documentRef.createElement("strong");
                name.textContent = typeof result.name === "string" ? result.name : result.guid;
                const meta = documentRef.createElement("span");
                meta.className = "wizard-extension-amo-guid";
                meta.textContent = typeof result.version === "string" && result.version
                    ? `${result.guid} • ${t("profiles.wizard_extensions_amo_version").replace("{version}", result.version)}`
                    : result.guid;
                identity.append(name, meta);
                const selectButton = documentRef.createElement("button");
                selectButton.type = "button";
                selectButton.className = "button-base ghost-button";
                selectButton.textContent = t("profiles.wizard_extensions_amo_select_action");
                selectButton.addEventListener("click", () => selectAmoResult(result));
                row.append(identity, selectButton);
                wizardExtensionAmoSearchResultsEl.append(row);
            });
            wizardExtensionAmoSearchResultsEl.hidden = wizardExtensionAmoSearchResultsEl.childElementCount === 0;
        }

        async function searchAmoByName() {
            const query = wizardExtensionAmoQueryEl?.value.trim() || "";
            if (!query) {
                clearAmoSearchResults();
                setAmoSearchStatus("profiles.wizard_extensions_amo_query_required");
                wizardExtensionAmoQueryEl?.focus();
                return;
            }
            amoSearchAbortController?.abort();
            const controller = new AbortController();
            amoSearchAbortController = controller;
            const searchSequence = ++amoSearchSequence;
            clearAmoSearchResults();
            setAmoManualRecoveryVisible(false);
            setAmoSearchStatus("profiles.wizard_extensions_amo_search_loading");
            try {
                const response = await fetch(
                    `/api/profiles/extensions/amo-search?q=${encodeURIComponent(query)}&locale=${encodeURIComponent(amoLocale())}`,
                    { credentials: "same-origin", signal: controller.signal },
                );
                const payload = await response.json();
                if (searchSequence !== amoSearchSequence || controller.signal.aborted) return;
                if (!response.ok || payload?.availability !== "available") {
                    setAmoSearchUnavailable();
                    return;
                }
                const results = Array.isArray(payload.results) ? payload.results : [];
                if (!results.length) {
                    setAmoSearchStatus("profiles.wizard_extensions_amo_search_empty");
                    return;
                }
                renderAmoSearchResults(results);
                setAmoSearchStatus("profiles.wizard_extensions_amo_search_results");
            } catch (error) {
                if (controller.signal.aborted) return;
                setAmoSearchUnavailable();
            }
        }

        const extensionRuleFields = [
            "blocked_install_message",
            "install_sources",
            "installation_mode",
            "allowed_types",
            "install_url",
            "updates_disabled",
            "update_url",
            "default_area",
            "private_browsing",
            "restricted_domains",
            "temporarily_allow_weak_signatures",
        ];
        const extensionRule153Fields = [
            "allowed_permissions",
            "blocked_permissions",
            "runtime_allowed_hosts",
            "runtime_blocked_hosts",
        ];
        const extensionRuleListFields = new Set([
            "install_sources",
            "allowed_types",
            "restricted_domains",
            "allowed_permissions",
            "blocked_permissions",
            "runtime_allowed_hosts",
            "runtime_blocked_hosts",
        ]);
        const extensionRuleBooleanFields = new Set([
            "updates_disabled",
            "private_browsing",
            "temporarily_allow_weak_signatures",
        ]);
        const extensionRuleTextFields = new Set([
            "blocked_install_message",
            "install_url",
            "update_url",
        ]);

        function supportsExtension153Fields() {
            const channel = String(getActiveWizardSchemaVersion?.() || "");
            return channel === "release-153" || channel === "esr-153.0";
        }

        function supportedExtensionRuleFields() {
            return supportsExtension153Fields()
                ? [...extensionRuleFields, ...extensionRule153Fields]
                : [...extensionRuleFields];
        }

        function editorPolicyDocument() {
            const editor = getEditor();
            if (!editor) return null;
            const mode = documentRef.getElementById("mode")?.value || "";
            const parsed = fromEditorValue(editor.getValue(), mode);
            return {
                editor,
                mode,
                document: parsed && typeof parsed === "object" && !Array.isArray(parsed)
                    ? { ...parsed }
                    : {},
            };
        }

        function writeExtensionPolicyDocument(editorState, { source = "manual", paths = [] } = {}) {
            recordExtensionSources(paths, source);
            setCurrentRaw(editorState.document);
            editorState.editor.setValue(toEditorValue(editorState.document, editorState.mode));
            renderExtensionRules(editorState.document);
            renderAmoSelectedRules();
            renderExtensionReviewSummary(editorState.document);
            updateWizardSummary();
        }

        function extensionLines(value) {
            if (typeof value !== "string") return [];
            return value.split(/\r?\n/).filter((entry) => entry.length > 0);
        }

        function valueToExtensionLines(value) {
            return Array.isArray(value) && value.every((entry) => typeof entry === "string")
                ? value.join("\n")
                : "";
        }

        function valueToBooleanControl(value) {
            if (value === true) return "true";
            if (value === false) return "false";
            return "";
        }

        function controlToBoolean(value) {
            if (value === "true") return true;
            if (value === "false") return false;
            return undefined;
        }

        function extensionRuleIsStructured(value) {
            if (!value || typeof value !== "object" || Array.isArray(value)) return false;
            const supported = new Set(supportedExtensionRuleFields());
            return Object.entries(value).every(([field, fieldValue]) => {
                if (!supported.has(field)) return false;
                if (extensionRuleListFields.has(field)) {
                    return Array.isArray(fieldValue) && fieldValue.every((entry) => typeof entry === "string");
                }
                if (extensionRuleBooleanFields.has(field)) return typeof fieldValue === "boolean";
                if (field === "installation_mode") {
                    return ["allowed", "blocked", "force_installed", "normal_installed"].includes(fieldValue);
                }
                if (field === "default_area") return ["navbar", "menupanel"].includes(fieldValue);
                return extensionRuleTextFields.has(field) && typeof fieldValue === "string";
            });
        }

        function sourceMatchesPath(value, path) {
            const candidate = Array.isArray(value?.path) ? value.path.map(String) : [];
            return path.every((part, index) => candidate[index] === part)
                || candidate.every((part, index) => path[index] === part);
        }

        const extensionSourceOrder = [
            "converted",
            "preset",
            "cis",
            "manual",
            "amo-assisted-manual",
            "imported",
            "raw",
        ];

        function extensionPointer(parts) {
            return `/${parts.map((part) => String(part)
                .replaceAll("~", "~0")
                .replaceAll("/", "~1")).join("/")}`;
        }

        function extensionValuePaths(documentValue) {
            const values = new Map();
            const walk = (value, path) => {
                if (Array.isArray(value)) {
                    if (!value.length) values.set(extensionPointer(path), value);
                    else value.forEach((entry, index) => walk(entry, [...path, index]));
                    return;
                }
                if (value && typeof value === "object") {
                    const keys = Object.keys(value).sort();
                    if (!keys.length) values.set(extensionPointer(path), value);
                    else keys.forEach((key) => walk(value[key], [...path, key]));
                    return;
                }
                values.set(extensionPointer(path), value);
            };
            ["ExtensionSettings", "ExtensionUpdate", "Extensions", "InstallAddonsPermission"].forEach((policy) => {
                if (Object.prototype.hasOwnProperty.call(documentValue || {}, policy)) {
                    walk(documentValue[policy], [policy]);
                }
            });
            return values;
        }

        function changedExtensionValuePaths(before, after) {
            const beforeValues = extensionValuePaths(before);
            const afterValues = extensionValuePaths(after);
            return Array.from(afterValues.keys()).filter((path) =>
                !beforeValues.has(path)
                || JSON.stringify(beforeValues.get(path)) !== JSON.stringify(afterValues.get(path)));
        }

        function extensionProvenancePaths() {
            const provenance = getCurrentProfile()?.extension_provenance;
            const paths = provenance?.paths;
            return paths && typeof paths === "object" && !Array.isArray(paths) ? paths : {};
        }

        function recordExtensionSources(paths, source) {
            if (!paths.length || !extensionSourceOrder.includes(source)) return;
            const profile = getCurrentProfile();
            if (!profile || typeof profile !== "object") return;
            const prior = extensionProvenancePaths();
            setCurrentProfile({
                ...profile,
                extension_provenance: {
                    contract_id: "bpm096-profile-extension-provenance",
                    contract_version: 1,
                    paths: paths.reduce((next, path) => ({ ...next, [path]: source }), { ...prior }),
                },
            });
        }

        function legacyExtensionRuleSource(path) {
            const manualEdits = Array.isArray(getManualEdits?.()) ? getManualEdits() : [];
            if (manualEdits.some((entry) => sourceMatchesPath(entry, path))) return "manual";
            const compliance = getComplianceInfo?.();
            const decisions = Array.isArray(compliance?.decisions) ? compliance.decisions : [];
            const decision = decisions.find((entry) => sourceMatchesPath(entry, path));
            if (!decision) return "manual";
            const selected = String(decision.selected_source || decision.selectedSource || "");
            if (selected === "cis") return "cis";
            if (selected === "base" || selected === "baseline") return "preset";
            return "cis";
        }

        function extensionRuleSources(path, { raw = false } = {}) {
            if (raw) return ["raw"];
            const pointer = extensionPointer(path);
            const prefix = `${pointer}/`;
            const available = new Set(
                Object.entries(extensionProvenancePaths())
                    .filter(([candidate]) => candidate === pointer || candidate.startsWith(prefix))
                    .map(([, source]) => source)
                    .filter((source) => extensionSourceOrder.includes(source)),
            );
            if (available.size) return extensionSourceOrder.filter((source) => available.has(source));
            return [legacyExtensionRuleSource(path)];
        }

        function extensionRuleSource(path, { raw = false } = {}) {
            return extensionRuleSources(path, { raw })[0] || "manual";
        }

        function extensionRuleSourceText(source) {
            const key = {
                manual: "profiles.wizard_extension_source_manual",
                cis: "profiles.wizard_extension_source_cis",
                preset: "profiles.wizard_extension_source_preset",
                converted: "profiles.wizard_extension_source_converted",
                "amo-assisted-manual": "profiles.wizard_extension_source_amo_assisted_manual",
                imported: "profiles.wizard_extension_source_imported",
                raw: "profiles.wizard_extension_source_raw",
            }[source] || "profiles.wizard_extension_source_manual";
            return t(key);
        }

        function labelElement(labelKey, control) {
            const label = documentRef.createElement("label");
            label.className = "wizard-input-stack";
            const labelText = documentRef.createElement("span");
            labelText.className = "field-label";
            labelText.textContent = t(labelKey);
            label.append(labelText, control);
            return label;
        }

        function createTextControl(guid, field, value, labelKey, { multiline = false } = {}) {
            const control = multiline
                ? documentRef.createElement("textarea")
                : documentRef.createElement("input");
            if (multiline) {
                control.rows = 3;
                control.spellcheck = false;
            } else {
                control.type = "text";
            }
            control.className = "soft-input";
            control.value = value;
            control.dataset.extensionRuleField = field;
            control.dataset.extensionRuleGuid = guid;
            return labelElement(labelKey, control);
        }

        function createSelectControl(guid, field, value, labelKey, options) {
            const select = documentRef.createElement("select");
            select.className = "soft-input";
            select.dataset.extensionRuleField = field;
            select.dataset.extensionRuleGuid = guid;
            options.forEach(([optionValue, optionKey]) => {
                const option = documentRef.createElement("option");
                option.value = optionValue;
                option.textContent = t(optionKey);
                select.append(option);
            });
            select.value = value;
            return labelElement(labelKey, select);
        }

        function extensionRuleConflicts(guid, value, documentValue) {
            const conflicts = [];
            const mode = value?.installation_mode;
            const extensions = documentValue?.Extensions && typeof documentValue.Extensions === "object"
                && !Array.isArray(documentValue.Extensions)
                ? documentValue.Extensions
                : {};
            const uninstall = Array.isArray(extensions.Uninstall) ? extensions.Uninstall : [];
            if (guid === "*" && ["force_installed", "normal_installed"].includes(mode)) {
                conflicts.push("profiles.wizard_extension_rule_conflict_global_install");
            }
            if (uninstall.includes(guid) && ["force_installed", "normal_installed"].includes(mode)) {
                conflicts.push("profiles.wizard_extension_rule_conflict_uninstall");
            }
            if (value?.install_url && ["allowed", "blocked"].includes(mode)) {
                conflicts.push("profiles.wizard_extension_rule_conflict_install_url");
            }
            const allowedPermissions = Array.isArray(value?.allowed_permissions) ? value.allowed_permissions : [];
            const blockedPermissions = Array.isArray(value?.blocked_permissions) ? value.blocked_permissions : [];
            if (allowedPermissions.some((permission) => blockedPermissions.includes(permission))) {
                conflicts.push("profiles.wizard_extension_rule_conflict_permission");
            }
            return conflicts;
        }

        function renderTypedExtensionRule(guid, value, documentValue) {
            const card = documentRef.createElement("section");
            card.className = "wizard-section-group wizard-subsection-card wizard-extension-rule-card";
            card.dataset.extensionRule = guid;
            const sources = extensionRuleSources(["ExtensionSettings", guid]);
            card.dataset.extensionRuleSource = sources[0] || "manual";
            card.dataset.extensionRuleSources = sources.join(",");
            if (guid === "*") card.dataset.extensionRuleDefault = "true";

            const heading = documentRef.createElement("div");
            heading.className = "wizard-extension-rule-head";
            const identity = documentRef.createElement("div");
            identity.className = "wizard-extension-amo-identity";
            const title = documentRef.createElement("strong");
            title.textContent = guid === "*"
                ? t("profiles.wizard_extension_rule_global_title")
                : guid;
            const source = documentRef.createElement("span");
            source.className = "wizard-extension-rule-source";
            source.dataset.extensionRuleSource = card.dataset.extensionRuleSource;
            source.textContent = sources.map((entry) => extensionRuleSourceText(entry)).join(" · ");
            identity.append(title, source);
            const remove = documentRef.createElement("button");
            remove.type = "button";
            remove.className = "button-base ghost-button";
            remove.dataset.extensionRuleRemove = guid;
            remove.textContent = t("profiles.wizard_extension_rule_remove");
            remove.addEventListener("click", () => removeExtensionRule(guid));
            heading.append(identity, remove);
            card.append(heading);

            const fields = documentRef.createElement("div");
            fields.className = "wizard-grid wizard-extension-rule-fields";
            fields.append(
                createSelectControl(guid, "installation_mode", value.installation_mode || "",
                    "profiles.wizard_extension_profile_mode_label", [
                        ["", "profiles.wizard_extension_profile_mode_inherit"],
                        ["allowed", "profiles.wizard_extension_profile_mode_allowed"],
                        ["blocked", "profiles.wizard_extension_profile_mode_blocked"],
                        ["force_installed", "profiles.wizard_extension_profile_mode_force"],
                        ["normal_installed", "profiles.wizard_extension_profile_mode_normal"],
                    ]),
                createTextControl(guid, "install_url", value.install_url || "",
                    "profiles.wizard_extension_profile_url_label"),
                createTextControl(guid, "update_url", value.update_url || "",
                    "profiles.wizard_extension_rule_update_url_label"),
                createSelectControl(guid, "updates_disabled", valueToBooleanControl(value.updates_disabled),
                    "profiles.wizard_extension_profile_updates_label", [
                        ["", "profiles.wizard_extension_inherit"],
                        ["true", "profiles.wizard_extension_disabled"],
                        ["false", "profiles.wizard_extension_enabled"],
                    ]),
                createSelectControl(guid, "private_browsing", valueToBooleanControl(value.private_browsing),
                    "profiles.wizard_extension_profile_private_label", [
                        ["", "profiles.wizard_extension_inherit"],
                        ["true", "profiles.wizard_extension_enabled"],
                        ["false", "profiles.wizard_extension_disabled"],
                    ]),
                createSelectControl(guid, "default_area", value.default_area || "",
                    "profiles.wizard_extension_rule_default_area_label", [
                        ["", "profiles.wizard_extension_inherit"],
                        ["navbar", "profiles.wizard_extension_rule_default_area_navbar"],
                        ["menupanel", "profiles.wizard_extension_rule_default_area_menupanel"],
                    ]),
                createSelectControl(guid, "temporarily_allow_weak_signatures",
                    valueToBooleanControl(value.temporarily_allow_weak_signatures),
                    "profiles.wizard_extension_rule_weak_signatures_label", [
                        ["", "profiles.wizard_extension_inherit"],
                        ["true", "profiles.wizard_extension_enabled"],
                        ["false", "profiles.wizard_extension_disabled"],
                    ]),
                createTextControl(guid, "blocked_install_message", value.blocked_install_message || "",
                    "profiles.wizard_extension_rule_blocked_message_label", { multiline: true }),
                createTextControl(guid, "install_sources", valueToExtensionLines(value.install_sources),
                    "profiles.wizard_extension_rule_install_sources_label", { multiline: true }),
                createTextControl(guid, "allowed_types", valueToExtensionLines(value.allowed_types),
                    "profiles.wizard_extension_rule_allowed_types_label", { multiline: true }),
                createTextControl(guid, "restricted_domains", valueToExtensionLines(value.restricted_domains),
                    "profiles.wizard_extension_rule_restricted_domains_label", { multiline: true }),
            );
            if (supportsExtension153Fields()) {
                fields.append(
                    createTextControl(guid, "allowed_permissions", valueToExtensionLines(value.allowed_permissions),
                        "profiles.wizard_extension_rule_allowed_permissions_label", { multiline: true }),
                    createTextControl(guid, "blocked_permissions", valueToExtensionLines(value.blocked_permissions),
                        "profiles.wizard_extension_rule_blocked_permissions_label", { multiline: true }),
                    createTextControl(guid, "runtime_allowed_hosts", valueToExtensionLines(value.runtime_allowed_hosts),
                        "profiles.wizard_extension_rule_runtime_allowed_hosts_label", { multiline: true }),
                    createTextControl(guid, "runtime_blocked_hosts", valueToExtensionLines(value.runtime_blocked_hosts),
                        "profiles.wizard_extension_rule_runtime_blocked_hosts_label", { multiline: true }),
                );
            }
            card.append(fields);
            const conflicts = extensionRuleConflicts(guid, value, documentValue);
            if (conflicts.length) {
                card.dataset.extensionRuleConflict = "true";
                const conflict = documentRef.createElement("div");
                conflict.className = "wizard-extension-rule-conflict";
                conflict.setAttribute("role", "alert");
                conflict.textContent = conflicts.map((key) => t(key)).join(" ");
                card.append(conflict);
            }
            return card;
        }

        function renderRawExtensionRule(guid, value, { policy = "ExtensionSettings" } = {}) {
            const card = documentRef.createElement("section");
            card.className = "wizard-section-group wizard-subsection-card wizard-extension-raw-rule";
            card.dataset.extensionRawRule = guid;
            card.dataset.extensionRuleSource = "raw";
            const title = documentRef.createElement("strong");
            title.textContent = policy === "ExtensionSettings" ? guid : policy;
            const source = documentRef.createElement("span");
            source.className = "wizard-extension-rule-source";
            source.textContent = extensionRuleSourceText("raw");
            const textarea = documentRef.createElement("textarea");
            textarea.className = "soft-input";
            textarea.rows = 6;
            textarea.spellcheck = false;
            textarea.dataset.extensionRawRule = guid;
            textarea.dataset.extensionRawPolicy = policy;
            textarea.value = JSON.stringify(value, null, 2);
            textarea.addEventListener("change", () => applyRawExtensionRule(textarea));
            card.append(title, source, textarea);
            return card;
        }

        function syncSharedExtensionControls(documentValue) {
            const extensions = documentValue.Extensions && typeof documentValue.Extensions === "object"
                && !Array.isArray(documentValue.Extensions)
                ? documentValue.Extensions
                : {};
            const installPermission = documentValue.InstallAddonsPermission
                && typeof documentValue.InstallAddonsPermission === "object"
                && !Array.isArray(documentValue.InstallAddonsPermission)
                ? documentValue.InstallAddonsPermission
                : {};
            if (wizardExtensionUpdateEl) {
                wizardExtensionUpdateEl.value = valueToBooleanControl(documentValue.ExtensionUpdate);
            }
            if (wizardExtensionInstallDefaultEl) {
                wizardExtensionInstallDefaultEl.value = valueToBooleanControl(installPermission.Default);
            }
            if (wizardExtensionInstallAllowEl) {
                wizardExtensionInstallAllowEl.value = valueToExtensionLines(installPermission.Allow);
            }
            if (wizardExtensionInstallEl) wizardExtensionInstallEl.value = valueToExtensionLines(extensions.Install);
            if (wizardExtensionLockedEl) wizardExtensionLockedEl.value = valueToExtensionLines(extensions.Locked);
            if (wizardExtensionUninstallEl) wizardExtensionUninstallEl.value = valueToExtensionLines(extensions.Uninstall);
        }

        function renderExtensionRules(documentValue) {
            if (!wizardExtensionRulesEl || !wizardExtensionRawRulesEl) return;
            wizardExtensionRulesEl.replaceChildren();
            wizardExtensionRawRulesEl.replaceChildren();
            const settings = documentValue.ExtensionSettings;
            if (settings !== undefined && (!settings || typeof settings !== "object" || Array.isArray(settings))) {
                wizardExtensionRawRulesEl.append(
                    renderRawExtensionRule("ExtensionSettings", settings, { policy: "ExtensionSettings" }),
                );
            } else {
                const entries = Object.entries(settings || {}).sort(([left], [right]) =>
                    left === "*" ? -1 : right === "*" ? 1 : left.localeCompare(right));
                entries.forEach(([guid, value]) => {
                    if (extensionRuleIsStructured(value)) {
                        wizardExtensionRulesEl.append(renderTypedExtensionRule(guid, value, documentValue));
                    } else {
                        wizardExtensionRawRulesEl.append(renderRawExtensionRule(guid, value));
                    }
                });
            }
            ["Extensions", "InstallAddonsPermission"].forEach((policy) => {
                const value = documentValue[policy];
                if (value === undefined) return;
                const expectedObject = value && typeof value === "object" && !Array.isArray(value);
                if (!expectedObject) {
                    wizardExtensionRawRulesEl.append(renderRawExtensionRule(policy, value, { policy }));
                }
            });
            syncSharedExtensionControls(documentValue);
            const ruleCount = wizardExtensionRulesEl.querySelectorAll("[data-extension-rule]").length;
            const rawCount = wizardExtensionRawRulesEl.childElementCount;
            if (wizardExtensionRuleStatusEl) {
                wizardExtensionRuleStatusEl.textContent = ruleCount || rawCount
                    ? t("profiles.wizard_extension_rule_status_count")
                        .replace("{count}", String(ruleCount + rawCount))
                    : t("profiles.wizard_extension_rule_status_empty");
            }
        }

        function applyExtensionRuleEditor() {
            const editorState = editorPolicyDocument();
            if (!editorState) return;
            const documentValue = editorState.document;
            const beforeDocument = JSON.parse(JSON.stringify(documentValue));
            const currentSettings = documentValue.ExtensionSettings;
            if (currentSettings !== undefined && (!currentSettings || typeof currentSettings !== "object" || Array.isArray(currentSettings))) {
                setStatus(t("profiles.wizard_extension_rule_raw_required"), "error");
                return;
            }
            const nextSettings = { ...(currentSettings || {}) };
            documentRef.querySelectorAll("[data-extension-rule]").forEach((card) => {
                const guid = String(card.dataset.extensionRule || "");
                const currentRule = nextSettings[guid];
                if (!guid || !extensionRuleIsStructured(currentRule)) return;
                const nextRule = { ...currentRule };
                supportedExtensionRuleFields().forEach((field) => delete nextRule[field]);
                card.querySelectorAll("[data-extension-rule-field]").forEach((control) => {
                    const field = String(control.dataset.extensionRuleField || "");
                    if (!supportedExtensionRuleFields().includes(field)) return;
                    const raw = control.value;
                    if (extensionRuleListFields.has(field)) {
                        const values = extensionLines(raw);
                        if (values.length) nextRule[field] = values;
                    } else if (extensionRuleBooleanFields.has(field)) {
                        const value = controlToBoolean(raw);
                        if (value !== undefined) nextRule[field] = value;
                    } else if (raw !== "") {
                        nextRule[field] = raw;
                    }
                });
                if (Object.keys(nextRule).length) nextSettings[guid] = nextRule;
                else delete nextSettings[guid];
            });
            if (Object.keys(nextSettings).length) documentValue.ExtensionSettings = nextSettings;
            else delete documentValue.ExtensionSettings;

            const extensions = documentValue.Extensions;
            if (extensions === undefined || (extensions && typeof extensions === "object" && !Array.isArray(extensions))) {
                const nextExtensions = { ...(extensions || {}) };
                [
                    [wizardExtensionInstallEl, "Install"],
                    [wizardExtensionLockedEl, "Locked"],
                    [wizardExtensionUninstallEl, "Uninstall"],
                ].forEach(([control, field]) => {
                    if (!control) return;
                    const values = extensionLines(control.value);
                    if (values.length) nextExtensions[field] = values;
                    else delete nextExtensions[field];
                });
                if (Object.keys(nextExtensions).length) documentValue.Extensions = nextExtensions;
                else delete documentValue.Extensions;
            }
            const permissions = documentValue.InstallAddonsPermission;
            if (permissions === undefined || (permissions && typeof permissions === "object" && !Array.isArray(permissions))) {
                const nextPermissions = { ...(permissions || {}) };
                const defaultValue = controlToBoolean(wizardExtensionInstallDefaultEl?.value || "");
                const allowedValues = extensionLines(wizardExtensionInstallAllowEl?.value || "");
                if (defaultValue === undefined) delete nextPermissions.Default;
                else nextPermissions.Default = defaultValue;
                if (allowedValues.length) nextPermissions.Allow = allowedValues;
                else delete nextPermissions.Allow;
                if (Object.keys(nextPermissions).length) documentValue.InstallAddonsPermission = nextPermissions;
                else delete documentValue.InstallAddonsPermission;
            }
            const updateValue = controlToBoolean(wizardExtensionUpdateEl?.value || "");
            if (updateValue === undefined) delete documentValue.ExtensionUpdate;
            else documentValue.ExtensionUpdate = updateValue;
            writeExtensionPolicyDocument(editorState, {
                source: "manual",
                paths: changedExtensionValuePaths(beforeDocument, documentValue),
            });
            setStatus(t("profiles.wizard_extensions_applied"), "info");
        }

        function setExtensionRuleMode(guid, selectedMode, { source = "manual" } = {}) {
            const editorState = editorPolicyDocument();
            if (!editorState || !isVerifiedFirefoxGuid(guid)) return;
            const settings = editorState.document.ExtensionSettings;
            if (settings !== undefined && (!settings || typeof settings !== "object" || Array.isArray(settings))) return;
            const current = settings?.[guid];
            if (current !== undefined && !extensionRuleIsStructured(current)) return;
            const nextSettings = { ...(settings || {}) };
            nextSettings[guid] = { ...(current || {}), installation_mode: selectedMode };
            editorState.document.ExtensionSettings = nextSettings;
            const known = amoSelectedRules.get(guid);
            if (known) amoSelectedRules.set(guid, { ...known, mode: selectedMode });
            writeExtensionPolicyDocument(editorState, {
                source,
                paths: [extensionPointer(["ExtensionSettings", guid, "installation_mode"])],
            });
        }

        function addExtensionRule(guid, installUrl = "") {
            const normalizedGuid = String(guid || "").trim();
            const normalizedInstallUrl = String(installUrl || "").trim();
            if (normalizedGuid !== "*" && !isVerifiedFirefoxGuid(normalizedGuid)) {
                setText(wizardExtensionRuleStatusEl, t("profiles.wizard_extension_rule_guid_invalid"));
                wizardExtensionRuleGuidEl?.focus();
                return;
            }
            const editorState = editorPolicyDocument();
            if (!editorState) return;
            const beforeDocument = JSON.parse(JSON.stringify(editorState.document));
            const settings = editorState.document.ExtensionSettings;
            if (settings !== undefined && (!settings || typeof settings !== "object" || Array.isArray(settings))) {
                setText(wizardExtensionRuleStatusEl, t("profiles.wizard_extension_rule_raw_required"));
                return;
            }
            const nextSettings = { ...(settings || {}) };
            if (!Object.prototype.hasOwnProperty.call(nextSettings, normalizedGuid)) {
                nextSettings[normalizedGuid] = {};
            }
            if (normalizedInstallUrl && normalizedGuid !== "*") {
                nextSettings[normalizedGuid] = {
                    ...nextSettings[normalizedGuid],
                    install_url: normalizedInstallUrl,
                };
            }
            editorState.document.ExtensionSettings = nextSettings;
            if (wizardExtensionRuleGuidEl) wizardExtensionRuleGuidEl.value = "";
            if (wizardExtensionRuleInstallUrlEl) wizardExtensionRuleInstallUrlEl.value = "";
            writeExtensionPolicyDocument(editorState, {
                source: "manual",
                paths: changedExtensionValuePaths(beforeDocument, editorState.document),
            });
            const selector = "[data-extension-rule=\"" + CSS.escape(normalizedGuid) + "\"]";
            wizardExtensionRulesEl?.querySelector(selector)
                ?.querySelector("[data-extension-rule-field=installation_mode]")?.focus();
        }

        function removeExtensionRule(guid) {
            const editorState = editorPolicyDocument();
            if (!editorState) return;
            const settings = editorState.document.ExtensionSettings;
            if (!settings || typeof settings !== "object" || Array.isArray(settings)) return;
            const nextSettings = { ...settings };
            delete nextSettings[guid];
            if (Object.keys(nextSettings).length) editorState.document.ExtensionSettings = nextSettings;
            else delete editorState.document.ExtensionSettings;
            amoSelectedRules.delete(guid);
            writeExtensionPolicyDocument(editorState);
        }

        function applyRawExtensionRule(textarea) {
            const editorState = editorPolicyDocument();
            if (!editorState) return;
            const beforeDocument = JSON.parse(JSON.stringify(editorState.document));
            try {
                const parsed = JSON.parse(textarea.value);
                const policy = textarea.dataset.extensionRawPolicy || "ExtensionSettings";
                const guid = textarea.dataset.extensionRawRule || "";
                if (policy === "ExtensionSettings" && guid !== "ExtensionSettings") {
                    const settings = editorState.document.ExtensionSettings;
                    if (!settings || typeof settings !== "object" || Array.isArray(settings)) return;
                    editorState.document.ExtensionSettings = { ...settings, [guid]: parsed };
                } else {
                    editorState.document[policy] = parsed;
                }
                writeExtensionPolicyDocument(editorState, {
                    source: "raw",
                    paths: changedExtensionValuePaths(beforeDocument, editorState.document),
                });
            } catch {
                setStatus(t("profiles.wizard_extension_rule_raw_invalid"), "error");
            }
        }

        function hasMeaningfulValue(value) {
            if (typeof value === "boolean" || typeof value === "number") return true;
            if (typeof value === "string") return value.trim().length > 0;
            if (Array.isArray(value)) return value.some((entry) => hasMeaningfulValue(entry));
            if (value && typeof value === "object") return Object.values(value).some((entry) => hasMeaningfulValue(entry));
            return false;
        }

        function countConfiguredObjectEntries(value) {
            const currentObject = value && typeof value === "object" && !Array.isArray(value) ? value : {};
            return Object.values(currentObject).filter((entry) => hasMeaningfulValue(entry)).length;
        }

        function countHandlerRuleBucket(bucket) {
            return bucket && typeof bucket === "object" && !Array.isArray(bucket)
                ? Object.keys(bucket).filter(Boolean).length
                : 0;
        }

        function isAiWizardAvailable() {
            return hasUsableAiControlsCard()
                || hasUsableGenerativeAiCard()
                || hasUsableAiPolicyCard(wizardVisualSearchEnabledCardEl);
        }

        function setPanelExpanded(panelEl, toggleEl, expanded, showLabel, hideLabel) {
            if (panelEl) {
                panelEl.hidden = !expanded;
            }
            if (toggleEl) {
                toggleEl.setAttribute("aria-expanded", expanded ? "true" : "false");
                toggleEl.textContent = expanded ? hideLabel : showLabel;
            }
        }

        function focusTargetForA11y(targetEl) {
            if (!targetEl) return;
            const focusTarget = targetEl.matches("input, select, textarea, button, [tabindex]")
                ? targetEl
                : targetEl.querySelector("input, select, textarea, button, [tabindex]");
            const resolvedTarget = focusTarget || targetEl;
            if (!resolvedTarget.matches("input, select, textarea, button, [tabindex]")) {
                resolvedTarget.setAttribute("tabindex", "-1");
            }
            resolvedTarget.focus?.({ preventScroll: true });
        }

        function renderPresetButtonState(buttons, activeKey, datasetKey) {
            buttons.forEach((button) => {
                const isActive = button.dataset[datasetKey] === activeKey;
                button.classList.toggle("wizard-search-engine-preset--applied", isActive);
                button.classList.toggle("wizard-search-engine-preset--partial", false);
                button.classList.toggle("wizard-search-engine-preset--conflict", false);
                button.setAttribute("aria-pressed", isActive ? "true" : "false");
            });
        }

        function getStepSixSummaryData(parsed) {
            const bookmarkEntries = Array.isArray(parsed?.Bookmarks)
                ? parsed.Bookmarks.filter((item) => item && typeof item === "object" && !Array.isArray(item) && Object.keys(item).length > 0)
                : [];
            const managedFolders = Array.isArray(parsed?.ManagedBookmarks)
                ? parsed.ManagedBookmarks.filter((item) => item && typeof item === "object" && !Array.isArray(item) && Object.keys(item).length > 0)
                : [];
            const nestedRows = managedFolders.filter((item) => Array.isArray(item.children) && item.children.length > 0);
            const userMessagingControls = countConfiguredObjectEntries(parsed?.UserMessaging);
            const requestedLocales = Array.isArray(parsed?.RequestedLocales)
                ? parsed.RequestedLocales.filter((entry) => typeof entry === "string" && entry.trim()).length
                : 0;
            const generativeAiControls = countConfiguredObjectEntries(parsed?.GenerativeAI);
            const aiControls = parsed?.AIControls && typeof parsed.AIControls === "object" && !Array.isArray(parsed.AIControls)
                ? parsed.AIControls
                : {};
            const aiControlsManaged = countConfiguredObjectEntries(aiControls);
            const aiDefaultControl = aiControls.Default && typeof aiControls.Default === "object" && !Array.isArray(aiControls.Default)
                ? aiControls.Default
                : {};
            const websiteFilter = parsed?.WebsiteFilter && typeof parsed.WebsiteFilter === "object" && !Array.isArray(parsed.WebsiteFilter)
                ? parsed.WebsiteFilter
                : {};
            const handlers = parsed?.Handlers && typeof parsed.Handlers === "object" && !Array.isArray(parsed.Handlers)
                ? parsed.Handlers
                : {};

            return {
                accountsManaged: typeof parsed?.DisableFirefoxAccounts === "boolean",
                accountsDisabled: parsed?.DisableFirefoxAccounts === true,
                userMessagingControls,
                requestedLocales,
                translateManaged: typeof parsed?.TranslateEnabled === "boolean",
                translateEnabled: parsed?.TranslateEnabled === true,
                visualSearchManaged: typeof parsed?.VisualSearchEnabled === "boolean",
                visualSearchEnabled: parsed?.VisualSearchEnabled === true,
                aiControlsManaged,
                aiDefaultBlocked: aiDefaultControl.Value === "blocked",
                aiDefaultAvailable: aiDefaultControl.Value === "available",
                aiDefaultLocked: aiDefaultControl.Locked === true,
                generativeAiControls,
                bookmarkEntries: bookmarkEntries.length,
                managedBookmarkFolders: managedFolders.length,
                nestedBookmarkFolders: nestedRows.length,
                blockedSites: Array.isArray(websiteFilter.Block) ? websiteFilter.Block.length : 0,
                exceptionSites: Array.isArray(websiteFilter.Exceptions) ? websiteFilter.Exceptions.length : 0,
                handlerMimeRules: countHandlerRuleBucket(handlers.mimeTypes),
                handlerSchemeRules: countHandlerRuleBucket(handlers.schemes),
                handlerExtensionRules: countHandlerRuleBucket(handlers.extensions),
                intranetSingleWordManaged: parsed?.GoToIntranetSiteForSingleWordEntryInAddressBar === true,
            };
        }

        function hasUsableAiControlsCard() {
            return hasUsableAiPolicyCard(wizardAiControlsCardEl);
        }

        function hasUsableGenerativeAiCard() {
            return hasUsableAiPolicyCard(wizardGenerativeAiCardEl);
        }

        function buildAiControlsValue(presetKey) {
            if (presetKey === "disable") {
                return {
                    Default: {
                        Value: "blocked",
                        Locked: true,
                    },
                };
            }
            if (presetKey === "availability") {
                return {
                    Default: {
                        Value: "available",
                        Locked: true,
                    },
                };
            }
            if (presetKey === "mixed") {
                return {
                    Default: {
                        Value: "available",
                        Locked: true,
                    },
                    SidebarChatbot: {
                        Value: "blocked",
                        Locked: true,
                    },
                    SmartWindow: {
                        Value: "blocked",
                        Locked: true,
                    },
                };
            }
            return null;
        }

        function buildGenerativeAiValue(presetKey) {
            if (presetKey === "disable") {
                return {
                    Enabled: false,
                    Chatbot: false,
                    LinkPreviews: false,
                    TabGroups: false,
                    Locked: true,
                };
            }
            if (presetKey === "availability") {
                return {
                    Enabled: true,
                    Locked: true,
                };
            }
            if (presetKey === "mixed") {
                return {
                    Enabled: true,
                    Chatbot: true,
                    LinkPreviews: true,
                    TabGroups: true,
                    Locked: true,
                };
            }
            return null;
        }

        function resolveAiPosturePreset(summary) {
            const managedAiControls = summary.aiControlsManaged > 0 || summary.generativeAiControls > 0;
            if ((summary.aiDefaultBlocked || summary.generativeAiControls > 0) && summary.visualSearchManaged && !summary.visualSearchEnabled) {
                return "disable";
            }
            if (managedAiControls && summary.visualSearchManaged) {
                return "mixed";
            }
            if (managedAiControls) {
                return "availability";
            }
            return "defaults";
        }

        function resolveSyncFocusPreset(summary) {
            if (summary.accountsManaged && summary.userMessagingControls > 0) return "managed";
            if (summary.userMessagingControls > 0) return "guidance";
            if (summary.accountsManaged) return "accounts";
            return "defaults";
        }

        function resolveLanguagePreset(summary) {
            if (summary.requestedLocales > 0 && summary.translateManaged && summary.translateEnabled) {
                return "managed";
            }
            if (summary.requestedLocales > 0) {
                return "locales";
            }
            if (summary.translateManaged && !summary.translateEnabled) {
                return "translation_off";
            }
            return "defaults";
        }

        function applyLanguagePreset(presetKey) {
            const editor = getEditor();
            if (!editor) return;

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                const existingLocales = Array.isArray(parsed?.RequestedLocales)
                    ? parsed.RequestedLocales.filter((entry) => typeof entry === "string" && entry.trim())
                    : [];

                delete normalized.RequestedLocales;
                delete normalized.TranslateEnabled;

                if (presetKey === "locales") {
                    normalized.RequestedLocales = existingLocales.length ? existingLocales : ["en-US", "ru"];
                } else if (presetKey === "translation_off") {
                    normalized.TranslateEnabled = false;
                } else if (presetKey === "managed") {
                    normalized.RequestedLocales = existingLocales.length ? existingLocales : ["en-US", "ru"];
                    normalized.TranslateEnabled = true;
                }

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                renderStepSixWorkspace(normalized);
                updateWizardSummary();
                setStatus(t("profiles.wizard_policy_applied"), "info");
            } catch (e) {
                setStatus(t("profiles.error_wizard_policy").replace("{detail}", e.message || e), "error");
            }
        }

        function revealLanguageTarget(kind) {
            const targetEl = kind === "translate"
                ? documentRef.getElementById("wizard-translate-enabled-card")
                : documentRef.getElementById("wizard-requested-locales-card");
            if (!targetEl) return;
            targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
            targetEl.classList.add("settings-target-highlight");
            window.setTimeout(() => {
                targetEl.classList.remove("settings-target-highlight");
            }, 1800);
            targetEl.querySelector("input, select, textarea, button")?.focus?.({ preventScroll: true });
        }

        function revealSyncFocus(kind) {
            if (kind === "guidance" || kind === "managed") {
                if (wizardSyncFineTuningPanelEl?.hidden !== false) {
                    syncPanelPreference = true;
                    setPanelExpanded(
                        wizardSyncFineTuningPanelEl,
                        wizardSyncFineTuningToggleEl,
                        true,
                        t("profiles.wizard_fine_tuning_show"),
                        t("profiles.wizard_fine_tuning_hide"),
                    );
                }
                const messagingTarget = documentRef.getElementById("wizard-user-messaging-card");
                if (!messagingTarget) return;
                messagingTarget.scrollIntoView({ behavior: "smooth", block: "center" });
                messagingTarget.classList.add("settings-target-highlight");
                window.setTimeout(() => {
                    messagingTarget.classList.remove("settings-target-highlight");
                }, 1800);
                focusTargetForA11y(messagingTarget);
                return;
            }

            const accountTarget = documentRef.querySelector('[data-policy-key="DisableFirefoxAccounts"]')
                || documentRef.querySelector('[data-wizard-step-id="users_language_sync"] [data-policy-key]')
                || wizardSyncSectionStatusEl;
            if (!accountTarget) return;
            accountTarget.scrollIntoView({ behavior: "smooth", block: "center" });
            accountTarget.classList.add("settings-target-highlight");
            window.setTimeout(() => {
                accountTarget.classList.remove("settings-target-highlight");
            }, 1800);
            focusTargetForA11y(accountTarget);
        }

        function renderStepSixExperience(parsed) {
            const summary = getStepSixSummaryData(parsed && typeof parsed === "object" ? parsed : {});

            const syncFragments = [];
            if (summary.accountsManaged) {
                syncFragments.push(
                    summary.accountsDisabled
                        ? t("profiles.wizard_sync_section_state_accounts_disabled")
                        : t("profiles.wizard_sync_section_state_accounts_enabled"),
                );
            }
            if (summary.userMessagingControls > 0) {
                syncFragments.push(
                    t("profiles.wizard_sync_section_state_user_messaging")
                        .replace("{count}", String(summary.userMessagingControls)),
                );
            }
            setText(
                wizardSyncSectionStatusEl,
                syncFragments.length
                    ? syncFragments.join(" • ")
                    : t("profiles.wizard_sync_section_state_empty"),
            );
            renderPresetButtonState(
                syncFocusPresetButtons,
                resolveSyncFocusPreset(summary),
                "syncFocusPreset",
            );

            const languageFragments = [];
            if (summary.requestedLocales > 0) {
                languageFragments.push(
                    t("profiles.wizard_language_section_state_locales")
                        .replace("{count}", String(summary.requestedLocales)),
                );
            }
            if (summary.translateManaged) {
                languageFragments.push(
                    summary.translateEnabled
                        ? t("profiles.wizard_language_section_state_translate_enabled")
                        : t("profiles.wizard_language_section_state_translate_disabled"),
                );
            }
            setText(
                wizardLanguageSectionStatusEl,
                languageFragments.length
                    ? languageFragments.join(" • ")
                    : t("profiles.wizard_language_section_state_empty"),
            );
            setText(
                wizardLanguageAiHandoffEl,
                summary.generativeAiControls > 0 || summary.visualSearchManaged
                    ? t("profiles.wizard_language_ai_handoff_go_ai")
                    : (
                        summary.requestedLocales > 0 || summary.translateManaged
                            ? t("profiles.wizard_language_ai_handoff_skip")
                            : t("profiles.wizard_language_ai_handoff_optional")
                    ),
            );
            renderPresetButtonState(
                languagePresetButtons,
                resolveLanguagePreset(summary),
                "languagePreset",
            );
            const showFineTuning = t("profiles.wizard_fine_tuning_show");
            const hideFineTuning = t("profiles.wizard_fine_tuning_hide");
            setPanelExpanded(
                wizardSyncFineTuningPanelEl,
                wizardSyncFineTuningToggleEl,
                syncPanelPreference === null ? summary.userMessagingControls > 0 : syncPanelPreference,
                showFineTuning,
                hideFineTuning,
            );
        }

        function renderStepSevenAiExperience(parsed) {
            const summary = getStepSixSummaryData(parsed && typeof parsed === "object" ? parsed : {});
            const releaseAiAvailable = isAiWizardAvailable();
            const aiFragments = [];

            if (wizardAiEsrcEmptyStateEl) {
                wizardAiEsrcEmptyStateEl.hidden = releaseAiAvailable;
            }
            if (wizardAiReleaseContentEl) {
                wizardAiReleaseContentEl.hidden = !releaseAiAvailable;
            }
            if (wizardAiPostureBarEl) {
                wizardAiPostureBarEl.hidden = !releaseAiAvailable;
            }
            if (wizardAiPostureBodyEl) {
                wizardAiPostureBodyEl.hidden = !releaseAiAvailable;
            }
            if (wizardAiPosturePresetsEl) {
                wizardAiPosturePresetsEl.hidden = !releaseAiAvailable;
            }
            if (wizardAiPolicyControlsEl) {
                wizardAiPolicyControlsEl.hidden = !releaseAiAvailable;
            }
            if (!releaseAiAvailable) {
                setText(wizardAiSectionStatusEl, t("profiles.wizard_ai_esr_state"));
                if (wizardAiGovernanceCopyEl) {
                    wizardAiGovernanceCopyEl.textContent = t("profiles.wizard_ai_esr_body");
                }
                renderPresetButtonState(aiPosturePresetButtons, null, "aiPosturePreset");
                return;
            }

            if (summary.aiControlsManaged > 0) {
                aiFragments.push(
                    t("profiles.wizard_ai_section_state_feature_controls")
                        .replace("{count}", String(summary.aiControlsManaged)),
                );
            } else if (summary.generativeAiControls > 0) {
                aiFragments.push(
                    t("profiles.wizard_ai_section_state_controls")
                        .replace("{count}", String(summary.generativeAiControls)),
                );
            }
            if (summary.visualSearchManaged) {
                aiFragments.push(
                    summary.visualSearchEnabled
                        ? t("profiles.wizard_ai_section_state_visual_search_enabled")
                        : t("profiles.wizard_ai_section_state_visual_search_disabled"),
                );
            }

            setText(
                wizardAiSectionStatusEl,
                aiFragments.length
                    ? aiFragments.join(" • ")
                    : t("profiles.wizard_ai_section_state_empty"),
            );
            renderPresetButtonState(
                aiPosturePresetButtons,
                resolveAiPosturePreset(summary),
                "aiPosturePreset",
            );
            if (wizardAiGovernanceCopyEl) {
                const hasManagedAiPosture = summary.aiControlsManaged > 0 || summary.generativeAiControls > 0 || summary.visualSearchManaged;
                wizardAiGovernanceCopyEl.textContent = hasManagedAiPosture
                    ? t("profiles.wizard_ai_controls_active")
                    : t("profiles.wizard_ai_controls_body");
            }
        }

        function isAiPolicyUnsupported(policyCardEl) {
            const cardEl = policyCardEl?.matches?.("[data-schema-policy-card]")
                ? policyCardEl
                : policyCardEl?.querySelector("[data-schema-policy-card]");
            return cardEl?.dataset?.schemaPolicyKind === "unsupported";
        }

        function hasUsableAiPolicyCard(policyCardEl) {
            const cardEl = policyCardEl?.matches?.("[data-schema-policy-card]")
                ? policyCardEl
                : policyCardEl?.querySelector("[data-schema-policy-card]");
            return Boolean(cardEl) && cardEl.dataset.schemaPolicyKind !== "unsupported";
        }

        function applyAiPosturePreset(presetKey) {
            const editor = getEditor();
            if (!editor) return;

            if (presetKey !== "defaults" && !hasUsableAiControlsCard() && !hasUsableGenerativeAiCard()) {
                revealAiTarget(presetKey === "mixed" ? "mixed" : "availability");
                setStatus(t("profiles.wizard_ai_policy_unavailable"), "info");
                return;
            }

            try {
                const mode = documentRef.getElementById("mode").value;
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};

                // Reflect the chosen posture immediately so the guided step reacts
                // even before the editor round-trip finishes.
                renderPresetButtonState(aiPosturePresetButtons, presetKey, "aiPosturePreset");

                if (presetKey === "defaults") {
                    delete normalized.AIControls;
                    delete normalized.GenerativeAI;
                    delete normalized.VisualSearchEnabled;
                } else {
                    if (hasUsableAiControlsCard()) {
                        normalized.AIControls = buildAiControlsValue(presetKey);
                        delete normalized.GenerativeAI;
                    } else if (hasUsableGenerativeAiCard()) {
                        normalized.GenerativeAI = buildGenerativeAiValue(presetKey);
                    }

                    if (presetKey === "disable" || presetKey === "mixed") {
                        normalized.VisualSearchEnabled = false;
                    } else if (presetKey === "availability") {
                        delete normalized.VisualSearchEnabled;
                    }
                }

                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                renderStepSixExperience(normalized);
                renderStepSevenAiExperience(normalized);
                updateWizardSummary();
                setStatus(t("profiles.wizard_ai_applied"), "info");
                if (presetKey !== "defaults") {
                    revealAiTarget(presetKey === "mixed" ? "mixed" : "availability");
                }
            } catch (e) {
                setStatus(t("profiles.error_wizard_policy").replace("{detail}", e.message || e), "error");
            }
        }

        function revealAiTarget(kind) {
            let targetEl = null;
            if (kind === "availability" || kind === "disable") {
                targetEl = wizardAiControlsCardEl
                    || wizardGenerativeAiCardEl;
            } else if (kind === "surfaces") {
                targetEl = wizardVisualSearchEnabledCardEl;
            } else if (kind === "mixed") {
                targetEl = wizardAiControlsCardEl
                    || wizardGenerativeAiCardEl
                    || wizardVisualSearchEnabledCardEl;
            }
            if (!targetEl) return;
            targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
            targetEl.classList.add("settings-target-highlight");
            window.setTimeout(() => {
                targetEl.classList.remove("settings-target-highlight");
            }, 1800);
            focusTargetForA11y(targetEl);
        }

        function toggleSectionPanel(panelKey) {
            if (panelKey === "sync") {
                syncPanelPreference = !(wizardSyncFineTuningPanelEl?.hidden === false);
            }
            const editor = getEditor();
            if (!editor) return;
            try {
                const parsed = fromEditorValue(editor.getValue(), document.getElementById("mode").value);
                const normalized = parsed && typeof parsed === "object" ? parsed : {};
                renderStepSixExperience(normalized);
                renderStepSevenAiExperience(normalized);
            } catch {
                renderStepSixExperience({});
                renderStepSevenAiExperience({});
            }
        }

        function syncFromEditor() {
            const current = editorPolicyDocument();
            if (current) {
                const settings = current.document.ExtensionSettings;
                if (settings && typeof settings === "object" && !Array.isArray(settings)) {
                    Array.from(amoSelectedRules.keys()).forEach((guid) => {
                        if (!extensionRuleIsStructured(settings[guid])) amoSelectedRules.delete(guid);
                    });
                    syncAmoSelectedRulesFromPolicy(settings);
                } else {
                    amoSelectedRules.clear();
                    renderAmoSelectedRules();
                }
                renderExtensionRules(current.document);
                renderStepSixExperience(current.document);
                renderStepSevenAiExperience(current.document);
                renderExtensionReviewSummary(current.document);
                updateWizardSummary();
            }
        }

        function applyFromWizard() {
            applyExtensionRuleEditor();
        }

        function bindInputListeners(applyExtensionsFromWizard) {
            wizardExtensionAmoSearchFormEl?.addEventListener("submit", (event) => {
                event.preventDefault();
                searchAmoByName();
            });
            wizardExtensionAmoManualFocusEl?.addEventListener("click", () => {
                focusManualExtensionEntry();
            });
            wizardExtensionRuleAddFormEl?.addEventListener("submit", (event) => {
                event.preventDefault();
                addExtensionRule(
                    wizardExtensionRuleGuidEl?.value || "",
                    wizardExtensionRuleInstallUrlEl?.value || "",
                );
            });
            const applyRuleEditor = () => applyExtensionRuleEditor();
            wizardExtensionRulesEl?.addEventListener("input", applyRuleEditor);
            wizardExtensionRulesEl?.addEventListener("change", applyRuleEditor);
            [
                wizardExtensionUpdateEl,
                wizardExtensionInstallDefaultEl,
                wizardExtensionInstallAllowEl,
                wizardExtensionInstallEl,
                wizardExtensionLockedEl,
                wizardExtensionUninstallEl,
            ].filter(Boolean).forEach((input) => {
                input.addEventListener("input", applyRuleEditor);
                input.addEventListener("change", applyRuleEditor);
            });
            if (wizardSyncFineTuningToggleEl) {
                wizardSyncFineTuningToggleEl.addEventListener("click", () => {
                    toggleSectionPanel("sync");
                });
            }
            syncFocusPresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    revealSyncFocus(button.dataset.syncFocusPreset || "defaults");
                });
            });
            aiPosturePresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    const presetKey = button.dataset.aiPosturePreset || "defaults";
                    applyAiPosturePreset(presetKey);
                });
            });
            languagePresetButtons.forEach((button) => {
                button.addEventListener("click", () => {
                    const presetKey = button.dataset.languagePreset || "defaults";
                    applyLanguagePreset(presetKey);
                    if (presetKey === "translation_off") {
                        revealLanguageTarget("translate");
                        return;
                    }
                    revealLanguageTarget("locales");
                });
            });
        }

        return {
            syncFromEditor,
            applyFromWizard,
            bindInputListeners,
        };
    }

    export { create };
