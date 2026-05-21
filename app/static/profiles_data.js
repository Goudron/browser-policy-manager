(() => {
    function isPlainObject(value) {
        return Boolean(value) && typeof value === "object" && !Array.isArray(value);
    }

    function toFirefoxPoliciesDocument(flagsObj) {
        if (isPlainObject(flagsObj) && isPlainObject(flagsObj.policies)) {
            return { policies: flagsObj.policies };
        }
        return { policies: isPlainObject(flagsObj) ? flagsObj : {} };
    }

    function toInternalFlags(documentObj) {
        if (documentObj === null || documentObj === undefined) return {};
        if (!isPlainObject(documentObj)) {
            throw new Error("Expected policies.json root object");
        }
        if (!Object.prototype.hasOwnProperty.call(documentObj, "policies")) {
            return documentObj;
        }
        if (!isPlainObject(documentObj.policies)) {
            throw new Error("Expected policies to be an object");
        }
        return documentObj.policies;
    }

    function parseEditorPolicyDocument(text, mode) {
        const parsed = fromSerializedEditorValue(text, mode);
        return toFirefoxPoliciesDocument(toInternalFlags(parsed));
    }

    function getPolicyValue(flagsObj, policyKey) {
        const flags = toInternalFlags(flagsObj);
        return flags[policyKey];
    }

    function setPolicyValue(flagsObj, policyKey, value) {
        const flags = { ...toInternalFlags(flagsObj) };
        if (value === undefined) {
            delete flags[policyKey];
        } else {
            flags[policyKey] = value;
        }
        return flags;
    }

    function fromSerializedEditorValue(text, mode) {
        if (!text || !text.trim()) return {};
        return mode === "yaml" ? window.jsyaml.load(text) : JSON.parse(text);
    }

    function toEditorValue(obj, mode) {
        const documentObj = toFirefoxPoliciesDocument(obj);
        if (mode === "yaml") {
            return window.jsyaml.dump(documentObj, {
                skipInvalid: true,
                sortKeys: false,
            });
        }
        return JSON.stringify(documentObj, null, 2);
    }

    function fromEditorValue(text, mode) {
        return toInternalFlags(fromSerializedEditorValue(text, mode));
    }

    async function readErrorPayload(res) {
        const raw = await res.text();
        try {
            const parsed = JSON.parse(raw);
            const issues = parsed.detail?.issues;
            if (Array.isArray(issues) && issues.length) {
                return {
                    message: issues
                        .slice(0, 3)
                        .map((issue) => `${issue.policy || "document"}: ${issue.message}`)
                        .join(" • "),
                    detail: parsed.detail,
                    raw,
                };
            }
            if (typeof parsed.detail === "string") {
                return { message: parsed.detail, detail: parsed.detail, raw };
            }
            if (parsed.detail?.message) {
                return { message: parsed.detail.message, detail: parsed.detail, raw };
            }
            if (parsed.message) {
                return { message: parsed.message, detail: parsed.detail, raw };
            }
            return { message: raw, detail: parsed.detail, raw };
        } catch {
            return { message: raw, detail: null, raw };
        }
    }

    async function readError(res) {
        const payload = await readErrorPayload(res);
        return payload.message;
    }

    async function profileRequestError(res) {
        const payload = await readErrorPayload(res);
        const error = new Error(payload.message);
        error.status = res.status;
        error.detail = payload.detail;
        error.payload = payload;
        return error;
    }

    function readProfileListFilters(documentRef) {
        return {
            q: documentRef.getElementById("search")?.value.trim() || "",
            schemaVersion: documentRef.getElementById("library-schema-filter")?.value || "",
            lifecycle: documentRef.getElementById("library-lifecycle-filter")?.value || "active",
            validationState: documentRef.getElementById("library-validation-filter")?.value || "",
            includeDeleted: documentRef.getElementById("include-deleted")?.checked || false,
            sort: documentRef.getElementById("sort")?.value || "updated_at",
            order: documentRef.getElementById("order")?.value || "desc",
        };
    }

    async function listProfiles(filters = null, fetchImpl = fetch, locationRef = window.location, documentRef = document) {
        const resolvedFilters = filters || readProfileListFilters(documentRef);
        const url = new URL("/api/profiles", locationRef.origin);
        if (resolvedFilters.q) url.searchParams.set("q", resolvedFilters.q);
        if (resolvedFilters.schemaVersion) url.searchParams.set("schema_version", resolvedFilters.schemaVersion);
        if (resolvedFilters.validationState) url.searchParams.set("validation_state", resolvedFilters.validationState);
        url.searchParams.set("lifecycle", resolvedFilters.lifecycle || "active");
        if (resolvedFilters.lifecycle === "archived" || resolvedFilters.lifecycle === "all" || resolvedFilters.includeDeleted) {
            url.searchParams.set("include_deleted", "true");
        }
        url.searchParams.set("sort", resolvedFilters.sort || "updated_at");
        url.searchParams.set("order", resolvedFilters.order || "desc");
        const res = await fetchImpl(url.toString());
        if (!res.ok) throw new Error(await readError(res));
        return await res.json();
    }

    async function getProfileLibraryStats(filters = null, fetchImpl = fetch, locationRef = window.location, documentRef = document) {
        const resolvedFilters = filters || readProfileListFilters(documentRef);
        const url = new URL("/api/profiles/stats", locationRef.origin);
        if (resolvedFilters.q) url.searchParams.set("q", resolvedFilters.q);
        if (resolvedFilters.schemaVersion) url.searchParams.set("schema_version", resolvedFilters.schemaVersion);
        if (resolvedFilters.validationState) url.searchParams.set("validation_state", resolvedFilters.validationState);
        url.searchParams.set("lifecycle", resolvedFilters.lifecycle || "active");
        if (resolvedFilters.lifecycle === "archived" || resolvedFilters.lifecycle === "all" || resolvedFilters.includeDeleted) {
            url.searchParams.set("include_deleted", "true");
        }
        const res = await fetchImpl(url.toString());
        if (!res.ok) throw new Error(await readError(res));
        return await res.json();
    }

    async function getProfile(id, fetchImpl = fetch, includeDeleted = false) {
        const suffix = includeDeleted ? "?include_deleted=true" : "";
        const res = await fetchImpl(`/api/profiles/${id}${suffix}`);
        if (!res.ok) throw new Error(await readError(res));
        return await res.json();
    }

    async function createProfile(body, fetchImpl = fetch) {
        const res = await fetchImpl("/api/profiles", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(await readError(res));
        return await res.json();
    }

    async function importFirefoxPoliciesJson(body, fetchImpl = fetch) {
        const res = await fetchImpl("/api/profiles/import/firefox/policies.json", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(await readError(res));
        return await res.json();
    }

    async function patchProfile(id, payload, fetchImpl = fetch) {
        const res = await fetchImpl(`/api/profiles/${id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        if (!res.ok) throw await profileRequestError(res);
        return await res.json();
    }

    async function softDeleteProfile(id, fetchImpl = fetch) {
        const res = await fetchImpl(`/api/profiles/${id}`, { method: "DELETE" });
        if (!res.ok) throw new Error(await readError(res));
    }

    async function hardDeleteProfile(id, fetchImpl = fetch) {
        const res = await fetchImpl(`/api/profiles/${id}/hard`, { method: "DELETE" });
        if (!res.ok) throw new Error(await readError(res));
    }

    async function restoreProfile(id, fetchImpl = fetch) {
        const res = await fetchImpl(`/api/profiles/${id}/restore`, { method: "POST" });
        if (!res.ok) throw new Error(await readError(res));
        return await res.json();
    }

    async function resetProfilesLibrary(fetchImpl = fetch) {
        const res = await fetchImpl("/api/profiles/reset", { method: "DELETE" });
        if (!res.ok) throw new Error(await readError(res));
        return await res.json();
    }

    async function validateFlags(profileKey, flagsObj, fetchImpl = fetch) {
        const res = await fetchImpl(`/api/validate/${encodeURIComponent(profileKey)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ document: flagsObj }),
        });
        if (!res.ok) throw await profileRequestError(res);
        return await res.json();
    }

    window.BPMProfilesData = {
        toEditorValue,
        fromEditorValue,
        parseEditorPolicyDocument,
        toInternalFlags,
        toFirefoxPoliciesDocument,
        getPolicyValue,
        setPolicyValue,
        readError,
        profileRequestError,
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
    };
})();
