(() => {
    function toEditorValue(obj, mode) {
        if (mode === "yaml") {
            return window.jsyaml.dump(obj || {}, {
                skipInvalid: true,
                sortKeys: false,
            });
        }
        return JSON.stringify(obj || {}, null, 2);
    }

    function fromEditorValue(text, mode) {
        if (!text || !text.trim()) return {};
        return mode === "yaml" ? window.jsyaml.load(text) : JSON.parse(text);
    }

    async function readError(res) {
        const raw = await res.text();
        try {
            const parsed = JSON.parse(raw);
            const issues = parsed.detail?.issues;
            if (Array.isArray(issues) && issues.length) {
                return issues
                    .slice(0, 3)
                    .map((issue) => `${issue.policy || "document"}: ${issue.message}`)
                    .join(" • ");
            }
            if (typeof parsed.detail === "string") return parsed.detail;
            if (parsed.detail?.message) return parsed.detail.message;
            if (parsed.message) return parsed.message;
            return raw;
        } catch {
            return raw;
        }
    }

    function readProfileListFilters(documentRef) {
        return {
            q: documentRef.getElementById("search")?.value.trim() || "",
            includeDeleted: documentRef.getElementById("include-deleted")?.checked || false,
            sort: documentRef.getElementById("sort")?.value || "updated_at",
            order: documentRef.getElementById("order")?.value || "desc",
        };
    }

    async function listProfiles(filters = null, fetchImpl = fetch, locationRef = window.location, documentRef = document) {
        const resolvedFilters = filters || readProfileListFilters(documentRef);
        const url = new URL("/api/profiles", locationRef.origin);
        if (resolvedFilters.q) url.searchParams.set("q", resolvedFilters.q);
        if (resolvedFilters.includeDeleted) url.searchParams.set("include_deleted", "true");
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
        if (resolvedFilters.includeDeleted) url.searchParams.set("include_deleted", "true");
        const res = await fetchImpl(url.toString());
        if (!res.ok) throw new Error(await readError(res));
        return await res.json();
    }

    async function getProfile(id, fetchImpl = fetch) {
        const res = await fetchImpl(`/api/profiles/${id}`);
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

    async function patchProfile(id, payload, fetchImpl = fetch) {
        const res = await fetchImpl(`/api/profiles/${id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(await readError(res));
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
        if (!res.ok) throw new Error(await readError(res));
        return await res.json();
    }

    window.BPMProfilesData = {
        toEditorValue,
        fromEditorValue,
        readError,
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
    };
})();
