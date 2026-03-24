(() => {
    const utils = {
        humanizeIdentifier(value) {
            if (typeof value !== "string" || !value) return "";

            return value
                .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
                .replace(/[_:-]+/g, " ")
                .replace(/\b(?:wizard|pref|policy|field)\b/gi, " ")
                .replace(/\s+/g, " ")
                .trim();
        },

        normalizeSearchText(value) {
            return String(value || "")
                .toLowerCase()
                .normalize("NFKD")
                .replace(/[\u0300-\u036f]/g, "")
                .replace(/[^\p{L}\p{N}]+/gu, " ")
                .replace(/\s+/g, " ")
                .trim();
        },

        escapeHtml(value) {
            return String(value || "")
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#39;");
        },

        linesToArray(text) {
            return text
                .split("\n")
                .map((line) => line.trim())
                .filter(Boolean);
        },

        cloneJsonValue(value, fallback) {
            if (value === undefined) return fallback;
            try {
                return JSON.parse(JSON.stringify(value));
            } catch {
                return fallback;
            }
        },

        textToList(text) {
            return text
                .split(/\n|,/)
                .map((entry) => entry.trim())
                .filter(Boolean);
        },

        formatBooleanSelectValue(value) {
            if (value === true) return "true";
            if (value === false) return "false";
            return "";
        },

        parseBooleanSelectValue(value) {
            if (value === "true") return true;
            if (value === "false") return false;
            return null;
        },

        formatSearchBarSelectValue(value) {
            if (value === true) return "separate";
            if (value === false) return "unified";
            return "";
        },

        parseSearchBarSelectValue(value) {
            if (value === "separate") return true;
            if (value === "unified") return false;
            return null;
        },

        stablePreferenceValueKey(value) {
            if (value === undefined) return "__undefined__";
            try {
                return JSON.stringify(value);
            } catch {
                return String(value);
            }
        },

        serializePreferenceValue(value) {
            if (typeof value === "string") return value;
            if (typeof value === "number" || typeof value === "boolean") return String(value);

            try {
                return JSON.stringify(value);
            } catch {
                return "";
            }
        },

        parsePreferenceValue(rawValue, explicitType, translate = (_key, fallback) => fallback) {
            const raw = rawValue.trim();

            if (explicitType === "boolean") {
                if (raw === "true") return { ok: true, value: true };
                if (raw === "false") return { ok: true, value: false };
                return {
                    ok: false,
                    message: translate(
                        "profiles.wizard_preferences_error_boolean",
                        "Boolean values must be true or false.",
                    ),
                };
            }

            if (explicitType === "number") {
                if (!raw) {
                    return {
                        ok: false,
                        message: translate(
                            "profiles.wizard_preferences_error_number",
                            "Number values must be valid numeric input.",
                        ),
                    };
                }
                const numeric = Number(raw);
                if (Number.isNaN(numeric)) {
                    return {
                        ok: false,
                        message: translate(
                            "profiles.wizard_preferences_error_number",
                            "Number values must be valid numeric input.",
                        ),
                    };
                }
                return { ok: true, value: numeric };
            }

            if (explicitType === "string") {
                return { ok: true, value: rawValue };
            }

            if (raw === "true") return { ok: true, value: true };
            if (raw === "false") return { ok: true, value: false };

            if (/^-?\d+(?:\.\d+)?$/.test(raw)) {
                return { ok: true, value: Number(raw) };
            }

            if (
                (raw.startsWith("{") && raw.endsWith("}"))
                || (raw.startsWith("[") && raw.endsWith("]"))
            ) {
                try {
                    return { ok: true, value: JSON.parse(raw) };
                } catch {
                    // Fall through to string when raw JSON-like text is not valid JSON.
                }
            }

            return { ok: true, value: rawValue };
        },

        serializePreferenceSelectValue(value) {
            if (typeof value === "boolean") return value ? "true" : "false";
            if (typeof value === "number") return String(value);
            if (typeof value === "string") return value;
            if (value == null) return "";
            try {
                return JSON.stringify(value);
            } catch {
                return String(value);
            }
        },

        normalizePreferenceName(prefName) {
            return typeof prefName === "string" ? prefName.trim() : "";
        },

        formatSchemaLabel(value) {
            return value === "release-148" ? "Release 148" : "ESR 140";
        },
    };

    window.BPMProfilesUtils = utils;
})();
