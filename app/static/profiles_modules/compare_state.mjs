/** Pure comparison state helpers.  Browser wiring remains in profiles_compare_state.js. */
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

export function collectDiffPaths(baseValue, otherValue, path = [], changes = []) {
    const normalizedBase = normalizeValue(baseValue);
    const normalizedOther = normalizeValue(otherValue);
    if (isPlainObject(normalizedBase) || isPlainObject(normalizedOther)) {
        const baseObject = isPlainObject(normalizedBase) ? normalizedBase : {};
        const otherObject = isPlainObject(normalizedOther) ? normalizedOther : {};
        const keys = Array.from(new Set([...Object.keys(baseObject), ...Object.keys(otherObject)])).sort();
        keys.forEach((key) => collectDiffPaths(baseObject[key], otherObject[key], [...path, key], changes));
        return changes;
    }
    if (snapshotToString(normalizedBase) !== snapshotToString(normalizedOther)) changes.push(path);
    return changes;
}

function asPlainObject(value) {
    return isPlainObject(value) ? value : {};
}

export function collectProfileSettingKeys(leftFlags = {}, rightFlags = {}) {
    const left = asPlainObject(leftFlags);
    const right = asPlainObject(rightFlags);
    const policyIds = Array.from(new Set([
        ...Object.keys(left).filter((key) => key !== "Preferences"),
        ...Object.keys(right).filter((key) => key !== "Preferences"),
    ])).sort();
    const leftPreferences = asPlainObject(left.Preferences);
    const rightPreferences = asPlainObject(right.Preferences);
    const preferenceNames = Array.from(new Set([...Object.keys(leftPreferences), ...Object.keys(rightPreferences)])).sort();
    return [
        ...policyIds.map((policyId) => ({ id: `policy:${policyId}`, kind: "policy", label: policyId, policyId, settingKey: policyId })),
        ...preferenceNames.map((preferenceName) => ({
            id: `preference:${preferenceName}`,
            kind: "preference",
            label: preferenceName,
            preferenceName,
            settingKey: `Preferences.${preferenceName}`,
        })),
    ];
}

export function readSettingValue(flags = {}, rowKey = {}) {
    const source = asPlainObject(flags);
    if (rowKey.kind === "preference") {
        const preferences = asPlainObject(source.Preferences);
        return {
            present: Object.prototype.hasOwnProperty.call(preferences, rowKey.preferenceName),
            value: preferences[rowKey.preferenceName],
        };
    }
    return {
        present: Object.prototype.hasOwnProperty.call(source, rowKey.policyId),
        value: source[rowKey.policyId],
    };
}

export function formatCompareValue(entry, { missingLabel = "Not set" } = {}) {
    if (!entry?.present) return missingLabel;
    if (typeof entry.value === "string") return entry.value;
    if (entry.value === null) return "null";
    if (typeof entry.value === "number" || typeof entry.value === "boolean") return String(entry.value);
    return snapshotToString(entry.value);
}
