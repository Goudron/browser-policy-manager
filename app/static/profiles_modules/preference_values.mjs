/** Pure preference value normalization and serialization helpers. */
export function cloneJsonValue(value, fallback) {
    if (value === undefined) return fallback;
    try {
        return JSON.parse(JSON.stringify(value));
    } catch {
        return fallback;
    }
}

export function textToList(text) {
    return text.split(/\n|,/).map((entry) => entry.trim()).filter(Boolean);
}

export function formatBooleanSelectValue(value) {
    if (value === true) return "true";
    if (value === false) return "false";
    return "";
}

export function parseBooleanSelectValue(value) {
    if (value === "true") return true;
    if (value === "false") return false;
    return null;
}

export function stablePreferenceValueKey(value) {
    if (value === undefined) return "__undefined__";
    try {
        return JSON.stringify(value);
    } catch {
        return String(value);
    }
}

export function serializePreferenceValue(value) {
    if (typeof value === "string") return value;
    if (typeof value === "number" || typeof value === "boolean") return String(value);
    try {
        return JSON.stringify(value);
    } catch {
        return "";
    }
}

export function parsePreferenceValue(rawValue, explicitType, translate = (_key, fallback) => fallback) {
    const raw = rawValue.trim();
    if (explicitType === "boolean") {
        if (raw === "true") return { ok: true, value: true };
        if (raw === "false") return { ok: true, value: false };
        return { ok: false, message: translate("profiles.wizard_preferences_error_boolean", "Boolean values must be true or false.") };
    }
    if (explicitType === "number") {
        if (!raw || Number.isNaN(Number(raw))) {
            return { ok: false, message: translate("profiles.wizard_preferences_error_number", "Number values must be valid numeric input.") };
        }
        return { ok: true, value: Number(raw) };
    }
    if (explicitType === "string") return { ok: true, value: rawValue };
    if (raw === "true") return { ok: true, value: true };
    if (raw === "false") return { ok: true, value: false };
    if (/^-?\d+(?:\.\d+)?$/.test(raw)) return { ok: true, value: Number(raw) };
    if ((raw.startsWith("{") && raw.endsWith("}")) || (raw.startsWith("[") && raw.endsWith("]"))) {
        try {
            return { ok: true, value: JSON.parse(raw) };
        } catch {
            // JSON-like invalid input remains a string for backwards compatibility.
        }
    }
    return { ok: true, value: rawValue };
}

export function serializePreferenceSelectValue(value) {
    if (typeof value === "boolean") return value ? "true" : "false";
    if (typeof value === "number") return String(value);
    if (typeof value === "string") return value;
    if (value == null) return "";
    try {
        return JSON.stringify(value);
    } catch {
        return String(value);
    }
}

export function normalizePreferenceName(prefName) {
    return typeof prefName === "string" ? prefName.trim() : "";
}
