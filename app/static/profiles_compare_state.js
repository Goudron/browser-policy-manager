(() => {
    const missingValueLabel = "Not set";

    function isPlainObject(value) {
        return Boolean(value) && typeof value === "object" && !Array.isArray(value);
    }

    function normalizeValue(value) {
        if (Array.isArray(value)) {
            return value.map(normalizeValue);
        }
        if (isPlainObject(value)) {
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

    function asPlainObject(value) {
        return isPlainObject(value) ? value : {};
    }

    function collectProfileSettingKeys(leftFlags = {}, rightFlags = {}) {
        const left = asPlainObject(leftFlags);
        const right = asPlainObject(rightFlags);
        const policyIds = Array.from(new Set([
            ...Object.keys(left).filter((key) => key !== "Preferences"),
            ...Object.keys(right).filter((key) => key !== "Preferences"),
        ])).sort();
        const leftPreferences = asPlainObject(left.Preferences);
        const rightPreferences = asPlainObject(right.Preferences);
        const preferenceNames = Array.from(new Set([
            ...Object.keys(leftPreferences),
            ...Object.keys(rightPreferences),
        ])).sort();

        return [
            ...policyIds.map((policyId) => ({
                id: `policy:${policyId}`,
                kind: "policy",
                label: policyId,
                policyId,
                settingKey: policyId,
            })),
            ...preferenceNames.map((preferenceName) => ({
                id: `preference:${preferenceName}`,
                kind: "preference",
                label: preferenceName,
                preferenceName,
                settingKey: `Preferences.${preferenceName}`,
            })),
        ];
    }

    function readSettingValue(flags = {}, rowKey = {}) {
        const source = asPlainObject(flags);
        if (rowKey.kind === "preference") {
            const preferences = asPlainObject(source.Preferences);
            const preferenceName = rowKey.preferenceName;
            return {
                present: Object.prototype.hasOwnProperty.call(preferences, preferenceName),
                value: preferences[preferenceName],
            };
        }

        const policyId = rowKey.policyId;
        return {
            present: Object.prototype.hasOwnProperty.call(source, policyId),
            value: source[policyId],
        };
    }

    function formatCompareValue(entry, options = {}) {
        const label = options.missingLabel || missingValueLabel;
        if (!entry?.present) return label;
        const value = entry.value;
        if (typeof value === "string") return value;
        if (value === null) return "null";
        if (typeof value === "number" || typeof value === "boolean") {
            return String(value);
        }
        return snapshotToString(value);
    }

    window.BPMProfilesCompareState = {
        collectDiffPaths,
        collectProfileSettingKeys,
        formatCompareValue,
        isPlainObject,
        normalizeValue,
        readSettingValue,
        snapshotToString,
    };
})();
