(() => {
    function normalizeCompareBaseSnapshot(snapshot, fallbackProfile = null, defaultSchemaVersion = "") {
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

    function normalizeCompareBaseProfile(profile, fallbackSnapshot = null, defaultSchemaVersion = "") {
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

    function getWorkflowLifecycleState({
        dirty,
        invalid,
        currentId,
        currentProfile,
        hasDraftName,
        labels,
    }) {
        if (currentProfile?.is_deleted) {
            return {
                selectionState: "archived",
                workflowState: "archived",
                title: labels.archivedTitle,
                copy: labels.archivedCopy,
            };
        }
        if (!currentId && !hasDraftName) {
            return {
                selectionState: "empty",
                workflowState: "empty",
                title: labels.emptyTitle,
                copy: labels.emptyCopy,
            };
        }
        if (!currentId) {
            return {
                selectionState: "draft",
                workflowState: "draft",
                title: labels.draftTitle,
                copy: labels.draftCopy,
            };
        }
        if (invalid) {
            return {
                selectionState: "active",
                workflowState: "invalid",
                title: labels.invalidTitle,
                copy: labels.invalidCopy,
            };
        }
        if (dirty) {
            return {
                selectionState: "active",
                workflowState: "dirty",
                title: labels.dirtyTitle,
                copy: labels.dirtyCopy,
            };
        }
        return {
            selectionState: "active",
            workflowState: "ready",
            title: labels.readyTitle,
            copy: labels.readyCopy,
        };
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

    function buildUpdatePayload(form, parsedFlags, compliancePayload, expectedRevisionPayload = {}) {
        return {
            description: form.description,
            owner: form.owner,
            schema_version: form.schemaVersion,
            flags: parsedFlags,
            compliance: compliancePayload,
            ...expectedRevisionPayload,
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

    window.BPMProfilesWorkspaceState = {
        buildCreatePayload,
        buildUpdatePayload,
        collectDiffPaths,
        getWorkflowLifecycleState,
        isPlainObject,
        normalizeCompareBaseProfile,
        normalizeCompareBaseSnapshot,
        normalizeValue,
        snapshotToString,
    };
})();
