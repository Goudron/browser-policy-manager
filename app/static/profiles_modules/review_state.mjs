/** Pure configured-value classification for review summaries. */
export function hasMeaningfulValue(value) {
    if (typeof value === "boolean" || typeof value === "number") return true;
    if (typeof value === "string") return value.trim().length > 0;
    if (Array.isArray(value)) return value.some((entry) => hasMeaningfulValue(entry));
    if (value && typeof value === "object") return Object.values(value).some((entry) => hasMeaningfulValue(entry));
    return false;
}

export function countConfiguredObjectEntries(value) {
    const currentObject = value && typeof value === "object" && !Array.isArray(value) ? value : {};
    return Object.values(currentObject).filter((entry) => hasMeaningfulValue(entry)).length;
}
