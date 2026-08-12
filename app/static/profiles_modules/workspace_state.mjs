/** Pure workspace lifecycle and request-payload helpers. */
export function isPlainObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function normalizeValue(value) {
    if (Array.isArray(value)) return value.map(normalizeValue);
    if (isPlainObject(value)) {
        return Object.keys(value).sort().reduce((normalized, key) => {
            normalized[key] = normalizeValue(value[key]);
            return normalized;
        }, {});
    }
    return value;
}

export function snapshotToString(snapshot) {
    return JSON.stringify(normalizeValue(snapshot));
}

export function getWorkflowLifecycleState({ dirty, invalid, currentId, currentProfile, hasDraftName, labels }) {
    if (currentProfile?.is_deleted) return { selectionState: "archived", workflowState: "archived", title: labels.archivedTitle, copy: labels.archivedCopy };
    if (!currentId && !hasDraftName) return { selectionState: "empty", workflowState: "empty", title: labels.emptyTitle, copy: labels.emptyCopy };
    if (!currentId) return { selectionState: "draft", workflowState: "draft", title: labels.draftTitle, copy: labels.draftCopy };
    if (invalid) return { selectionState: "active", workflowState: "invalid", title: labels.invalidTitle, copy: labels.invalidCopy };
    if (dirty) return { selectionState: "active", workflowState: "dirty", title: labels.dirtyTitle, copy: labels.dirtyCopy };
    return { selectionState: "active", workflowState: "ready", title: labels.readyTitle, copy: labels.readyCopy };
}

export function buildUpdatePayload(form, parsedFlags, compliancePayload, expectedRevisionPayload = {}) {
    return { description: form.description, flags: parsedFlags, compliance: compliancePayload, ...expectedRevisionPayload };
}

export function buildCreatePayload(form, parsedFlags, compliancePayload, { name = form.name } = {}) {
    return { name, description: form.description, schema_version: form.schemaVersion, flags: parsedFlags, compliance: compliancePayload };
}
