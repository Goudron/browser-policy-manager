/** URL normalization independent of DOM form reading and browser globals. */
export function buildProfileListUrl(filters = {}, origin) {
    const url = new URL("/api/profiles", origin);
    if (filters.q) url.searchParams.set("q", filters.q);
    if (filters.schemaVersion) url.searchParams.set("schema_version", filters.schemaVersion);
    if (filters.validationState) url.searchParams.set("validation_state", filters.validationState);
    if (filters.limit) url.searchParams.set("limit", String(filters.limit));
    url.searchParams.set("lifecycle", filters.lifecycle || "active");
    if (filters.lifecycle === "archived" || filters.lifecycle === "all" || filters.includeDeleted) url.searchParams.set("include_deleted", "true");
    url.searchParams.set("sort", filters.sort || "updated_at");
    url.searchParams.set("order", filters.order || "desc");
    return url;
}
