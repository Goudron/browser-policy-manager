import {
    AUTH_BOOLEAN_FIELDS,
    AUTH_LIST_FIELDS,
    AUTH_MAP_FIELDS,
    inspectAuthentication,
    inspectCertificates,
    inspectSecurityDevices,
    moveListEntry,
    omitEmptyAuthenticationFields,
    omitEmptyCertificateFields,
    omitEmptySecurityDeviceFields,
    validateAuthenticationHost,
    validateCertificateReference,
    validateSecurityDeviceName,
} from "./profiles_modules/certificate_policy.mjs";

    function create({
        documentRef = document,
        elements = {},
        dependencies = {},
        state = {},
        wizardSchemaShellCatalog = {},
    }) {
        const {
            t,
            fromEditorValue,
            toEditorValue,
            getActiveWizardSchemaVersion,
            setStatus,
        } = dependencies;
        const getEditor = state.getEditor || (() => null);
        const getCurrentProfile = state.getCurrentProfile || (() => null);
        const setCurrentRaw = state.setCurrentRaw || (() => {});

        const {
            wizardCertificateSystemTrustEl,
            wizardCertificateEnterpriseRootsEl,
            wizardCertificateErrorBypassEl,
            wizardCertificateWindowsSsoEl,
            wizardCertificateEntraSsoEl,
            wizardCertificateEntraRowEl,
            wizardCertificateTrustSchemaStatusEl,
            wizardCertificateProvenanceStatusEl,
            wizardCertificateCisStatusEl,
            wizardCertificateInstallFormEl,
            wizardCertificateInstallReferenceEl,
            wizardCertificateInstallListEl,
            wizardCertificateInstallEmptyEl,
            wizardCertificateInstallRawEl,
            wizardCertificateInstallRawValueEl,
            wizardCertificateAuthenticationFormEl,
            wizardCertificateAuthenticationFieldEl,
            wizardCertificateAuthenticationHostEl,
            wizardCertificateAuthenticationLockedEl,
            wizardCertificateAuthenticationPrivateBrowsingEl,
            wizardCertificateAuthenticationListEl,
            wizardCertificateAuthenticationEmptyEl,
            wizardCertificateAuthenticationRawEl,
            wizardCertificateAuthenticationRawValueEl,
            wizardSecurityDeviceAddFormEl,
            wizardSecurityDeviceNameEl,
            wizardSecurityDevicePathEl,
            wizardSecurityDeviceAddListEl,
            wizardSecurityDeviceAddEmptyEl,
            wizardSecurityDeviceDeleteFormEl,
            wizardSecurityDeviceDeleteNameEl,
            wizardSecurityDeviceDeleteListEl,
            wizardSecurityDeviceDeleteEmptyEl,
            wizardSecurityDevicesRawEl,
            wizardSecurityDevicesRawValueEl,
        } = elements;

        const preferenceName = "security.enterprise_roots.enabled";
        const knownPreferenceFields = new Set(["Status", "Type", "Value"]);
        const certificatePolicyPrefixes = [
            "/Authentication",
            "/Certificates",
            "/DisableSecurityBypass",
            "/MicrosoftEntraSSO",
            "/SecurityDevices",
            "/WindowsSSO",
            "/Preferences/security.enterprise_roots.enabled",
        ];

        function isPlainObject(value) {
            return Boolean(value) && typeof value === "object" && !Array.isArray(value);
        }

        function hasOnlyKnownFields(value, fields) {
            return isPlainObject(value) && Object.keys(value).every((key) => fields.has(key));
        }

        function valueToChoice(value) {
            if (value === undefined) return "";
            if (typeof value === "boolean") return String(value);
            return "custom";
        }

        function setChoice(element, value, { supported = true } = {}) {
            if (!element) return;
            element.disabled = !supported || value === "custom";
            element.value = value;
            element.closest("label")?.classList.toggle("is-unavailable", !supported);
        }

        function supportedPolicies() {
            const channel = wizardSchemaShellCatalog.channels?.[getActiveWizardSchemaVersion?.()];
            const policyIds = channel?.certificate_trust_posture?.policy_ids;
            return new Set(Array.isArray(policyIds) ? policyIds : []);
        }

        function preferenceChoice(source) {
            const preference = source?.Preferences?.[preferenceName];
            if (preference === undefined) return "";
            if (!hasOnlyKnownFields(preference, knownPreferenceFields) || preference.Type !== "boolean") {
                return "custom";
            }
            return valueToChoice(preference.Value);
        }

        function nestedChoice(source, policyId, fieldName, allowedFields) {
            const policy = source?.[policyId];
            if (policy === undefined) return "";
            if (!hasOnlyKnownFields(policy, allowedFields)) return "custom";
            return valueToChoice(policy[fieldName]);
        }

        function policyChoice(source, policyId) {
            return valueToChoice(source?.[policyId]);
        }

        function renderSchemaAvailability(supported) {
            const entraSupported = supported.has("MicrosoftEntraSSO");
            if (wizardCertificateEntraRowEl) wizardCertificateEntraRowEl.hidden = !entraSupported;
            if (!wizardCertificateTrustSchemaStatusEl) return;
            wizardCertificateTrustSchemaStatusEl.textContent = entraSupported
                ? t("profiles.wizard_certificate_schema_available")
                : t("profiles.wizard_certificate_schema_unavailable")
                    .replace("{setting}", t("profiles.wizard_certificate_entra_sso_label"));
        }

        function setHidden(element, hidden) {
            if (element) element.hidden = hidden;
        }

        function setText(element, value) {
            if (element) element.textContent = String(value ?? "");
        }

        function readSource() {
            const editor = getEditor();
            if (!editor) return null;
            const mode = documentRef.getElementById("mode")?.value || "";
            const parsed = fromEditorValue(editor.getValue(), mode);
            return { editor, mode, source: isPlainObject(parsed) ? { ...parsed } : {} };
        }

        function commitSource(state, messageKey = "profiles.wizard_schema_policy_applied") {
            setCurrentRaw(state.source);
            state.editor.setValue(toEditorValue(state.source, state.mode));
            syncFromEditor();
            setStatus(t(messageKey), "info");
        }

        function rawValue(value) {
            try {
                return JSON.stringify(value, null, 2);
            } catch {
                return String(value);
            }
        }

        function renderRawFallback(panel, valueEl, inspected) {
            const raw = inspected.kind === "raw_fallback";
            setHidden(panel, !raw);
            if (raw) setText(valueEl, rawValue(inspected.value));
            return raw;
        }

        function createAction(labelKey, handler, { disabled = false } = {}) {
            const button = documentRef.createElement("button");
            button.type = "button";
            button.className = "button-base ghost-button";
            button.textContent = t(labelKey);
            button.disabled = disabled;
            button.addEventListener("click", handler);
            return button;
        }

        function escapePointerSegment(value) {
            return String(value).replaceAll("~", "~0").replaceAll("/", "~1");
        }

        function isCertificatePath(path) {
            return typeof path === "string" && certificatePolicyPrefixes.some((prefix) => (
                path === prefix || path.startsWith(`${prefix}/`)
            ));
        }

        function sourceLabel(source) {
            const key = {
                baseline: "profiles.wizard_certificate_source_baseline",
                cis: "profiles.wizard_certificate_source_cis",
                manual: "profiles.wizard_certificate_source_manual",
                converted: "profiles.wizard_certificate_source_converted",
                imported: "profiles.wizard_certificate_source_imported",
                raw: "profiles.wizard_certificate_source_raw",
            }[source];
            return key ? t(key) : t("profiles.wizard_certificate_source_manual");
        }

        function sourcesForPath(path) {
            const paths = getCurrentProfile()?.certificate_provenance?.paths;
            if (!paths || typeof paths !== "object" || Array.isArray(paths)) return ["manual"];
            const prefix = `${path.replace(/\/$/, "")}/`;
            const sources = new Set(
                Object.entries(paths)
                    .filter(([candidate]) => candidate === path || candidate.startsWith(prefix))
                    .map(([, source]) => source)
                    .filter((source) => ["baseline", "cis", "manual", "converted", "imported", "raw"].includes(source)),
            );
            const order = ["converted", "baseline", "cis", "manual", "imported", "raw"];
            const resolved = order.filter((source) => sources.has(source));
            return resolved.length ? resolved : ["manual"];
        }

        function renderAttributionStatus() {
            const paths = getCurrentProfile()?.certificate_provenance?.paths;
            if (!wizardCertificateProvenanceStatusEl) return;
            if (!paths || typeof paths !== "object" || Array.isArray(paths)) {
                wizardCertificateProvenanceStatusEl.textContent = t("profiles.wizard_certificate_sources_empty");
                return;
            }
            const counts = {};
            Object.entries(paths).forEach(([path, source]) => {
                if (isCertificatePath(path) && ["baseline", "cis", "manual", "converted", "imported", "raw"].includes(source)) {
                    counts[source] = (counts[source] || 0) + 1;
                }
            });
            const order = ["converted", "baseline", "cis", "manual", "imported", "raw"];
            const summary = order
                .filter((source) => counts[source])
                .map((source) => `${sourceLabel(source)} (${counts[source]})`)
                .join(", ");
            wizardCertificateProvenanceStatusEl.textContent = summary
                ? t("profiles.wizard_certificate_sources_summary").replace("{sources}", summary)
                : t("profiles.wizard_certificate_sources_empty");
        }

        function renderCertificateCisStatus() {
            if (!wizardCertificateCisStatusEl) return;
            const decisions = getCurrentProfile()?.compliance?.decisions;
            const reviewCount = Array.isArray(decisions)
                ? decisions.filter((decision) => decision?.review_required && isCertificatePath(decision?.path)).length
                : 0;
            wizardCertificateCisStatusEl.textContent = reviewCount
                ? t("profiles.wizard_certificate_cis_review_required").replace("{count}", String(reviewCount))
                : t("profiles.wizard_certificate_cis_review_clear");
        }

        function appendListRow(container, { label, value, sourcePath = null, actions = [], onEdit = null }) {
            if (!container) return;
            const row = documentRef.createElement("div");
            row.className = "wizard-managed-list-row";
            row.setAttribute("role", "listitem");
            const identity = documentRef.createElement("div");
            identity.className = "wizard-managed-list-value";
            const title = documentRef.createElement("strong");
            title.textContent = label;
            const detail = documentRef.createElement("code");
            detail.textContent = value;
            identity.append(title, detail);
            if (sourcePath) {
                const attribution = documentRef.createElement("span");
                attribution.className = "wizard-input-hint";
                attribution.textContent = t("profiles.wizard_certificate_sources_summary")
                    .replace("{sources}", sourcesForPath(sourcePath).map(sourceLabel).join(", "));
                identity.append(attribution);
            }
            const controls = documentRef.createElement("div");
            controls.className = "wizard-managed-list-actions";
            actions.forEach((action) => controls.append(action));
            if (typeof onEdit === "function") {
                const edit = createAction("profiles.wizard_certificate_edit", () => {
                    const input = documentRef.createElement("input");
                    input.type = "text";
                    input.className = "soft-input";
                    input.value = value;
                    input.autocomplete = "off";
                    input.spellcheck = false;
                    identity.replaceChildren(title, input);
                    const save = createAction("profiles.save", () => onEdit(input.value));
                    const cancel = createAction("profiles.wizard_certificate_cancel", () => syncFromEditor());
                    controls.replaceChildren(save, cancel);
                    input.focus();
                });
                controls.append(edit);
            }
            row.append(identity, controls);
            container.append(row);
        }

        function setTypedControlsDisabled(controls, disabled) {
            controls.forEach((control) => {
                if (control) control.disabled = disabled;
            });
        }

        function updateTypedPolicy(policyId, inspect, updater) {
            let state;
            try {
                state = readSource();
            } catch (error) {
                setStatus(t("profiles.error_schema_policy").replace("{detail}", error?.message || error), "error");
                return false;
            }
            if (!state) return false;
            const inspected = inspect(state.source[policyId]);
            if (inspected.kind !== "typed") {
                syncFromEditor();
                setStatus(t("profiles.wizard_certificate_raw_fallback"), "warn");
                return false;
            }
            const next = updater(inspected.value);
            if (next === false) return false;
            if (next === undefined) delete state.source[policyId];
            else state.source[policyId] = next;
            commitSource(state);
            return true;
        }

        function renderCertificateReferences(source) {
            if (typeof documentRef.createElement !== "function") return;
            const inspected = inspectCertificates(source.Certificates);
            const raw = renderRawFallback(
                wizardCertificateInstallRawEl,
                wizardCertificateInstallRawValueEl,
                inspected,
            );
            setTypedControlsDisabled([wizardCertificateInstallReferenceEl], raw);
            if (wizardCertificateInstallListEl) wizardCertificateInstallListEl.replaceChildren();
            const entries = raw ? [] : (inspected.value.Install || []);
            setHidden(wizardCertificateInstallEmptyEl, entries.length > 0 || raw);
            entries.forEach((reference, index) => {
                const duplicate = inspected.duplicates.some((item) => item.index === index);
                appendListRow(wizardCertificateInstallListEl, {
                    label: duplicate ? t("profiles.wizard_certificate_duplicate") : t("profiles.wizard_certificate_reference_label"),
                    value: reference,
                    sourcePath: `/Certificates/Install/${index}`,
                    actions: [
                        createAction("profiles.wizard_certificate_move_up", () => moveCertificateReference(index, -1), { disabled: index === 0 }),
                        createAction("profiles.wizard_certificate_move_down", () => moveCertificateReference(index, 1), { disabled: index === entries.length - 1 }),
                        createAction("profiles.wizard_certificate_remove", () => removeCertificateReference(index)),
                    ],
                    onEdit: (nextReference) => editCertificateReference(index, nextReference),
                });
            });
        }

        function renderAuthentication(source) {
            if (typeof documentRef.createElement !== "function") return;
            const inspected = inspectAuthentication(source.Authentication);
            const raw = renderRawFallback(
                wizardCertificateAuthenticationRawEl,
                wizardCertificateAuthenticationRawValueEl,
                inspected,
            );
            setTypedControlsDisabled([
                wizardCertificateAuthenticationFieldEl,
                wizardCertificateAuthenticationHostEl,
                wizardCertificateAuthenticationLockedEl,
                wizardCertificateAuthenticationPrivateBrowsingEl,
            ], raw);
            if (wizardCertificateAuthenticationListEl) wizardCertificateAuthenticationListEl.replaceChildren();
            setHidden(wizardCertificateAuthenticationEmptyEl, raw || Object.keys(inspected.value || {}).length > 0);
            if (raw) {
                setChoice(wizardCertificateAuthenticationLockedEl, "custom");
                setChoice(wizardCertificateAuthenticationPrivateBrowsingEl, "custom");
                return;
            }
            AUTH_LIST_FIELDS.forEach((field) => {
                const entries = inspected.value[field] || [];
                entries.forEach((host, index) => appendListRow(wizardCertificateAuthenticationListEl, {
                    label: `${t("profiles.wizard_certificate_auth_field_prefix")}: ${field}`,
                    value: host,
                    sourcePath: `/Authentication/${field}/${index}`,
                    actions: [
                        createAction("profiles.wizard_certificate_move_up", () => moveAuthenticationListEntry(field, index, -1), { disabled: index === 0 }),
                        createAction("profiles.wizard_certificate_move_down", () => moveAuthenticationListEntry(field, index, 1), { disabled: index === entries.length - 1 }),
                        createAction("profiles.wizard_certificate_remove", () => removeAuthenticationListEntry(field, index)),
                    ],
                    onEdit: (nextHost) => editAuthenticationListEntry(field, index, nextHost),
                }));
            });
            AUTH_MAP_FIELDS.forEach((field) => {
                Object.keys(inspected.value[field] || {}).forEach((host) => appendListRow(wizardCertificateAuthenticationListEl, {
                    label: `${t("profiles.wizard_certificate_auth_field_prefix")}: ${field}`,
                    value: host,
                    sourcePath: `/Authentication/${field}/${escapePointerSegment(host)}`,
                    actions: [createAction("profiles.wizard_certificate_remove", () => removeAuthenticationMapEntry(field, host))],
                    onEdit: (nextHost) => editAuthenticationMapEntry(field, host, nextHost),
                }));
            });
            setChoice(wizardCertificateAuthenticationLockedEl, valueToChoice(inspected.value.Locked));
            setChoice(wizardCertificateAuthenticationPrivateBrowsingEl, valueToChoice(inspected.value.PrivateBrowsing));
        }

        function moveObjectEntry(value, name, direction) {
            const entries = Object.entries(value);
            const index = entries.findIndex(([entryName]) => entryName === name);
            const moved = moveListEntry(entries, index, direction);
            return moved.ok ? Object.fromEntries(moved.value) : { ...value };
        }

        function renderSecurityDevices(source) {
            if (typeof documentRef.createElement !== "function") return;
            const inspected = inspectSecurityDevices(source.SecurityDevices);
            const raw = renderRawFallback(wizardSecurityDevicesRawEl, wizardSecurityDevicesRawValueEl, inspected);
            setTypedControlsDisabled([
                wizardSecurityDeviceNameEl,
                wizardSecurityDevicePathEl,
                wizardSecurityDeviceDeleteNameEl,
            ], raw);
            if (wizardSecurityDeviceAddListEl) wizardSecurityDeviceAddListEl.replaceChildren();
            if (wizardSecurityDeviceDeleteListEl) wizardSecurityDeviceDeleteListEl.replaceChildren();
            if (raw) {
                setHidden(wizardSecurityDeviceAddEmptyEl, true);
                setHidden(wizardSecurityDeviceDeleteEmptyEl, true);
                return;
            }
            const add = inspected.value.Add || {};
            const deleted = inspected.value.Delete || [];
            setHidden(wizardSecurityDeviceAddEmptyEl, Object.keys(add).length > 0);
            setHidden(wizardSecurityDeviceDeleteEmptyEl, deleted.length > 0);
            Object.entries(add).forEach(([name, path], index, entries) => appendListRow(wizardSecurityDeviceAddListEl, {
                label: name,
                value: path,
                sourcePath: `/SecurityDevices/Add/${escapePointerSegment(name)}`,
                actions: [
                    createAction("profiles.wizard_certificate_move_up", () => moveSecurityDeviceAdd(name, -1), { disabled: index === 0 }),
                    createAction("profiles.wizard_certificate_move_down", () => moveSecurityDeviceAdd(name, 1), { disabled: index === entries.length - 1 }),
                    createAction("profiles.wizard_certificate_remove", () => removeSecurityDeviceAdd(name)),
                ],
                onEdit: (nextPath) => editSecurityDeviceAdd(name, nextPath),
            }));
            deleted.forEach((name, index) => appendListRow(wizardSecurityDeviceDeleteListEl, {
                label: t("profiles.wizard_certificate_device_delete_name"),
                value: name,
                sourcePath: `/SecurityDevices/Delete/${index}`,
                actions: [
                    createAction("profiles.wizard_certificate_move_up", () => moveSecurityDeviceDelete(index, -1), { disabled: index === 0 }),
                    createAction("profiles.wizard_certificate_move_down", () => moveSecurityDeviceDelete(index, 1), { disabled: index === deleted.length - 1 }),
                    createAction("profiles.wizard_certificate_remove", () => removeSecurityDeviceDelete(index)),
                ],
                onEdit: (nextName) => editSecurityDeviceDelete(index, nextName),
            }));
        }

        function syncFromEditor() {
            const editor = getEditor();
            if (!editor) return;
            let source = {};
            try {
                source = fromEditorValue(editor.getValue(), documentRef.getElementById("mode")?.value || "");
                if (!isPlainObject(source)) source = {};
            } catch {
                source = {};
            }

            const supported = supportedPolicies();
            setChoice(wizardCertificateSystemTrustEl, preferenceChoice(source));
            setChoice(
                wizardCertificateEnterpriseRootsEl,
                nestedChoice(source, "Certificates", "ImportEnterpriseRoots", new Set(["Install", "ImportEnterpriseRoots"])),
                { supported: supported.has("Certificates") },
            );
            setChoice(
                wizardCertificateErrorBypassEl,
                nestedChoice(source, "DisableSecurityBypass", "InvalidCertificate", new Set(["InvalidCertificate", "SafeBrowsing"])),
                { supported: supported.has("DisableSecurityBypass") },
            );
            setChoice(
                wizardCertificateWindowsSsoEl,
                policyChoice(source, "WindowsSSO"),
                { supported: supported.has("WindowsSSO") },
            );
            setChoice(
                wizardCertificateEntraSsoEl,
                policyChoice(source, "MicrosoftEntraSSO"),
                { supported: supported.has("MicrosoftEntraSSO") },
            );
            renderSchemaAvailability(supported);
            renderAttributionStatus();
            renderCertificateCisStatus();
            renderCertificateReferences(source);
            renderAuthentication(source);
            renderSecurityDevices(source);
        }

        function choiceValue(element) {
            if (!element || !["", "true", "false"].includes(element.value)) return null;
            return element.value === "" ? undefined : element.value === "true";
        }

        function setNestedBoolean(source, policyId, fieldName, value, allowedFields) {
            const current = source[policyId];
            if (current !== undefined && !hasOnlyKnownFields(current, allowedFields)) return false;
            const next = isPlainObject(current) ? { ...current } : {};
            if (value === undefined) {
                delete next[fieldName];
            } else {
                next[fieldName] = value;
            }
            if (Object.keys(next).length) {
                source[policyId] = next;
            } else {
                delete source[policyId];
            }
            return true;
        }

        function setBooleanPolicy(source, policyId, value) {
            const current = source[policyId];
            if (current !== undefined && typeof current !== "boolean") return false;
            if (value === undefined) {
                delete source[policyId];
            } else {
                source[policyId] = value;
            }
            return true;
        }

        function setPreferenceBoolean(source, value) {
            const preferences = source.Preferences;
            if (preferences !== undefined && !isPlainObject(preferences)) return false;
            const nextPreferences = isPlainObject(preferences) ? { ...preferences } : {};
            const current = nextPreferences[preferenceName];
            if (current !== undefined && (!hasOnlyKnownFields(current, knownPreferenceFields) || current.Type !== "boolean")) {
                return false;
            }
            if (value === undefined) {
                delete nextPreferences[preferenceName];
            } else {
                nextPreferences[preferenceName] = {
                    ...(isPlainObject(current) ? current : {}),
                    Status: current?.Status || "default",
                    Type: "boolean",
                    Value: value,
                };
            }
            if (Object.keys(nextPreferences).length) {
                source.Preferences = nextPreferences;
            } else {
                delete source.Preferences;
            }
            return true;
        }

        function applyChoice(choice) {
            const editor = getEditor();
            if (!editor) return;
            const value = choiceValue(choice.element);
            if (value === null) return;
            const supported = supportedPolicies();
            if (choice.policyId && !supported.has(choice.policyId)) return;
            try {
                const mode = documentRef.getElementById("mode")?.value || "";
                const parsed = fromEditorValue(editor.getValue(), mode);
                const source = isPlainObject(parsed) ? { ...parsed } : {};
                const applied = choice.apply(source, value);
                if (!applied) {
                    syncFromEditor();
                    setStatus(t("profiles.wizard_certificate_choice_custom"), "warn");
                    return;
                }
                setCurrentRaw(source);
                editor.setValue(toEditorValue(source, mode));
                syncFromEditor();
                setStatus(t("profiles.wizard_schema_policy_applied"), "info");
            } catch (error) {
                setStatus(t("profiles.error_schema_policy").replace("{detail}", error?.message || error), "error");
            }
        }

        function certificateValidationError(verdict) {
            return t("profiles.wizard_certificate_invalid_value")
                .replace("{rule}", String(verdict?.code || "invalid_value").replaceAll("_", "-"));
        }

        function addCertificateReference() {
            const reference = wizardCertificateInstallReferenceEl?.value ?? "";
            const verdict = validateCertificateReference(reference);
            if (!verdict.valid) {
                setStatus(certificateValidationError(verdict), "error");
                wizardCertificateInstallReferenceEl?.focus();
                return;
            }
            if (updateTypedPolicy("Certificates", inspectCertificates, (value) => omitEmptyCertificateFields({
                ...value,
                Install: [...(value.Install || []), reference],
            }))) {
                wizardCertificateInstallReferenceEl.value = "";
            }
        }

        function removeCertificateReference(index) {
            updateTypedPolicy("Certificates", inspectCertificates, (value) => omitEmptyCertificateFields({
                ...value,
                Install: (value.Install || []).filter((_, itemIndex) => itemIndex !== index),
            }));
        }

        function editCertificateReference(index, reference) {
            const verdict = validateCertificateReference(reference);
            if (!verdict.valid) {
                setStatus(certificateValidationError(verdict), "error");
                return;
            }
            updateTypedPolicy("Certificates", inspectCertificates, (value) => {
                const install = [...(value.Install || [])];
                if (index < 0 || index >= install.length) return false;
                install[index] = reference;
                return omitEmptyCertificateFields({ ...value, Install: install });
            });
        }

        function moveCertificateReference(index, direction) {
            updateTypedPolicy("Certificates", inspectCertificates, (value) => {
                const moved = moveListEntry(value.Install || [], index, direction);
                if (!moved.ok) return false;
                return omitEmptyCertificateFields({ ...value, Install: moved.value });
            });
        }

        function addAuthenticationHost() {
            const field = wizardCertificateAuthenticationFieldEl?.value || "";
            const host = wizardCertificateAuthenticationHostEl?.value ?? "";
            if (![...AUTH_LIST_FIELDS, ...AUTH_MAP_FIELDS].includes(field)) return;
            const verdict = validateAuthenticationHost(host);
            if (!verdict.valid) {
                setStatus(certificateValidationError(verdict), "error");
                wizardCertificateAuthenticationHostEl?.focus();
                return;
            }
            const applied = updateTypedPolicy("Authentication", inspectAuthentication, (value) => {
                if (AUTH_LIST_FIELDS.includes(field)) {
                    return omitEmptyAuthenticationFields({
                        ...value,
                        [field]: [...(value[field] || []), host],
                    });
                }
                if (value[field]?.[host] === true) {
                    setStatus(t("profiles.wizard_certificate_duplicate"), "warn");
                    return false;
                }
                return omitEmptyAuthenticationFields({
                    ...value,
                    [field]: { ...(value[field] || {}), [host]: true },
                });
            });
            if (applied) wizardCertificateAuthenticationHostEl.value = "";
        }

        function removeAuthenticationListEntry(field, index) {
            updateTypedPolicy("Authentication", inspectAuthentication, (value) => omitEmptyAuthenticationFields({
                ...value,
                [field]: (value[field] || []).filter((_, itemIndex) => itemIndex !== index),
            }));
        }

        function moveAuthenticationListEntry(field, index, direction) {
            updateTypedPolicy("Authentication", inspectAuthentication, (value) => {
                const moved = moveListEntry(value[field] || [], index, direction);
                if (!moved.ok) return false;
                return omitEmptyAuthenticationFields({ ...value, [field]: moved.value });
            });
        }

        function editAuthenticationListEntry(field, index, host) {
            const verdict = validateAuthenticationHost(host);
            if (!verdict.valid) {
                setStatus(certificateValidationError(verdict), "error");
                return;
            }
            updateTypedPolicy("Authentication", inspectAuthentication, (value) => {
                const entries = [...(value[field] || [])];
                if (index < 0 || index >= entries.length) return false;
                entries[index] = host;
                return omitEmptyAuthenticationFields({ ...value, [field]: entries });
            });
        }

        function removeAuthenticationMapEntry(field, host) {
            updateTypedPolicy("Authentication", inspectAuthentication, (value) => {
                const next = { ...(value[field] || {}) };
                delete next[host];
                return omitEmptyAuthenticationFields({ ...value, [field]: next });
            });
        }

        function editAuthenticationMapEntry(field, host, nextHost) {
            const verdict = validateAuthenticationHost(nextHost);
            if (!verdict.valid) {
                setStatus(certificateValidationError(verdict), "error");
                return;
            }
            updateTypedPolicy("Authentication", inspectAuthentication, (value) => {
                const current = { ...(value[field] || {}) };
                if (!Object.prototype.hasOwnProperty.call(current, host)) return false;
                if (nextHost !== host && Object.prototype.hasOwnProperty.call(current, nextHost)) {
                    setStatus(t("profiles.wizard_certificate_duplicate"), "warn");
                    return false;
                }
                const entries = Object.entries(current).map(([name, enabled]) => [name === host ? nextHost : name, enabled]);
                return omitEmptyAuthenticationFields({ ...value, [field]: Object.fromEntries(entries) });
            });
        }

        function setAuthenticationBoolean(field, element) {
            const value = choiceValue(element);
            if (value === null || !AUTH_BOOLEAN_FIELDS.includes(field)) return;
            updateTypedPolicy("Authentication", inspectAuthentication, (current) => {
                const next = { ...current };
                if (value === undefined) delete next[field];
                else next[field] = value;
                return omitEmptyAuthenticationFields(next);
            });
        }

        function addSecurityDevice() {
            const name = wizardSecurityDeviceNameEl?.value ?? "";
            const path = wizardSecurityDevicePathEl?.value ?? "";
            const nameVerdict = validateSecurityDeviceName(name);
            const pathVerdict = validateCertificateReference(path);
            if (!nameVerdict.valid || !pathVerdict.valid) {
                setStatus(certificateValidationError(!nameVerdict.valid ? nameVerdict : pathVerdict), "error");
                (!nameVerdict.valid ? wizardSecurityDeviceNameEl : wizardSecurityDevicePathEl)?.focus();
                return;
            }
            const applied = updateTypedPolicy("SecurityDevices", inspectSecurityDevices, (value) => {
                if (Object.prototype.hasOwnProperty.call(value.Add || {}, name)) {
                    setStatus(t("profiles.wizard_certificate_device_exists"), "warn");
                    return false;
                }
                return omitEmptySecurityDeviceFields({
                    ...value,
                    Add: { ...(value.Add || {}), [name]: path },
                });
            });
            if (applied) {
                wizardSecurityDeviceNameEl.value = "";
                wizardSecurityDevicePathEl.value = "";
            }
        }

        function removeSecurityDeviceAdd(name) {
            updateTypedPolicy("SecurityDevices", inspectSecurityDevices, (value) => {
                const next = { ...(value.Add || {}) };
                delete next[name];
                return omitEmptySecurityDeviceFields({ ...value, Add: next });
            });
        }

        function editSecurityDeviceAdd(name, path) {
            const verdict = validateCertificateReference(path);
            if (!verdict.valid) {
                setStatus(certificateValidationError(verdict), "error");
                return;
            }
            updateTypedPolicy("SecurityDevices", inspectSecurityDevices, (value) => {
                if (!Object.prototype.hasOwnProperty.call(value.Add || {}, name)) return false;
                return omitEmptySecurityDeviceFields({
                    ...value,
                    Add: { ...value.Add, [name]: path },
                });
            });
        }

        function moveSecurityDeviceAdd(name, direction) {
            updateTypedPolicy("SecurityDevices", inspectSecurityDevices, (value) => {
                const index = Object.keys(value.Add || {}).indexOf(name);
                const target = index + direction;
                if (index < 0 || target < 0 || target >= Object.keys(value.Add || {}).length) return false;
                const next = moveObjectEntry(value.Add || {}, name, direction);
                return omitEmptySecurityDeviceFields({ ...value, Add: next });
            });
        }

        function addSecurityDeviceDelete() {
            const name = wizardSecurityDeviceDeleteNameEl?.value ?? "";
            const verdict = validateSecurityDeviceName(name);
            if (!verdict.valid) {
                setStatus(certificateValidationError(verdict), "error");
                wizardSecurityDeviceDeleteNameEl?.focus();
                return;
            }
            const applied = updateTypedPolicy("SecurityDevices", inspectSecurityDevices, (value) => omitEmptySecurityDeviceFields({
                ...value,
                Delete: [...(value.Delete || []), name],
            }));
            if (applied) wizardSecurityDeviceDeleteNameEl.value = "";
        }

        function removeSecurityDeviceDelete(index) {
            updateTypedPolicy("SecurityDevices", inspectSecurityDevices, (value) => omitEmptySecurityDeviceFields({
                ...value,
                Delete: (value.Delete || []).filter((_, itemIndex) => itemIndex !== index),
            }));
        }

        function editSecurityDeviceDelete(index, name) {
            const verdict = validateSecurityDeviceName(name);
            if (!verdict.valid) {
                setStatus(certificateValidationError(verdict), "error");
                return;
            }
            updateTypedPolicy("SecurityDevices", inspectSecurityDevices, (value) => {
                const entries = [...(value.Delete || [])];
                if (index < 0 || index >= entries.length) return false;
                entries[index] = name;
                return omitEmptySecurityDeviceFields({ ...value, Delete: entries });
            });
        }

        function moveSecurityDeviceDelete(index, direction) {
            updateTypedPolicy("SecurityDevices", inspectSecurityDevices, (value) => {
                const moved = moveListEntry(value.Delete || [], index, direction);
                if (!moved.ok) return false;
                return omitEmptySecurityDeviceFields({ ...value, Delete: moved.value });
            });
        }

        wizardCertificateInstallFormEl?.addEventListener("submit", (event) => {
            event.preventDefault();
            addCertificateReference();
        });
        wizardCertificateAuthenticationFormEl?.addEventListener("submit", (event) => {
            event.preventDefault();
            addAuthenticationHost();
        });
        wizardCertificateAuthenticationLockedEl?.addEventListener("change", () => {
            setAuthenticationBoolean("Locked", wizardCertificateAuthenticationLockedEl);
        });
        wizardCertificateAuthenticationPrivateBrowsingEl?.addEventListener("change", () => {
            setAuthenticationBoolean("PrivateBrowsing", wizardCertificateAuthenticationPrivateBrowsingEl);
        });
        wizardSecurityDeviceAddFormEl?.addEventListener("submit", (event) => {
            event.preventDefault();
            addSecurityDevice();
        });
        wizardSecurityDeviceDeleteFormEl?.addEventListener("submit", (event) => {
            event.preventDefault();
            addSecurityDeviceDelete();
        });

        [
            {
                element: wizardCertificateSystemTrustEl,
                apply: setPreferenceBoolean,
            },
            {
                element: wizardCertificateEnterpriseRootsEl,
                policyId: "Certificates",
                apply: (source, value) => setNestedBoolean(
                    source, "Certificates", "ImportEnterpriseRoots", value, new Set(["Install", "ImportEnterpriseRoots"]),
                ),
            },
            {
                element: wizardCertificateErrorBypassEl,
                policyId: "DisableSecurityBypass",
                apply: (source, value) => setNestedBoolean(
                    source, "DisableSecurityBypass", "InvalidCertificate", value, new Set(["InvalidCertificate", "SafeBrowsing"]),
                ),
            },
            {
                element: wizardCertificateWindowsSsoEl,
                policyId: "WindowsSSO",
                apply: (source, value) => setBooleanPolicy(source, "WindowsSSO", value),
            },
            {
                element: wizardCertificateEntraSsoEl,
                policyId: "MicrosoftEntraSSO",
                apply: (source, value) => setBooleanPolicy(source, "MicrosoftEntraSSO", value),
            },
        ].forEach((choice) => {
            choice.element?.addEventListener("change", () => applyChoice(choice));
        });

        return {
            syncFromEditor,
        };
    }

    export { create };
