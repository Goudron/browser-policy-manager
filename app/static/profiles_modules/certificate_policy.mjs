/**
 * Lossless helpers for the Guided Certificates & trust step.
 *
 * Firefox owns certificate parsing, path resolution and device loading.  BPM
 * deliberately handles references only: it never opens, uploads, hashes or
 * otherwise inspects a certificate or PKCS#11 module file.  These helpers
 * therefore preserve each accepted string exactly as supplied.
 */

export function isPlainObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

const CONTROL_CHARACTER = /[\u0000-\u001F\u007F]/u;
const AUTH_LIST_FIELDS = ["SPNEGO", "Delegated", "NTLM"];
const AUTH_MAP_FIELDS = ["AllowNonFQDN", "AllowProxies"];
const AUTH_BOOLEAN_FIELDS = ["Locked", "PrivateBrowsing"];
const CERTIFICATE_FIELDS = new Set(["Install", "ImportEnterpriseRoots"]);
const SECURITY_DEVICE_FIELDS = new Set(["Add", "Delete"]);
const AUTHENTICATION_FIELDS = new Set([
    ...AUTH_LIST_FIELDS,
    ...AUTH_MAP_FIELDS,
    ...AUTH_BOOLEAN_FIELDS,
]);

export { AUTH_LIST_FIELDS, AUTH_MAP_FIELDS, AUTH_BOOLEAN_FIELDS };

export function validateCertificateReference(value) {
    if (typeof value !== "string") return { valid: false, code: "not_string" };
    if (!value) return { valid: false, code: "empty" };
    if (CONTROL_CHARACTER.test(value)) return { valid: false, code: "control_character" };
    if (value !== value.trim()) return { valid: false, code: "outer_whitespace" };
    if (value.length > 4096) return { valid: false, code: "too_long" };
    // Relative filenames, POSIX paths, Windows drive paths and UNC paths are
    // all Firefox-supported references.  Do not canonicalise any of them.
    return { valid: true };
}

export function validateSecurityDeviceName(value) {
    if (typeof value !== "string") return { valid: false, code: "not_string" };
    if (!value) return { valid: false, code: "empty" };
    if (CONTROL_CHARACTER.test(value)) return { valid: false, code: "control_character" };
    if (value !== value.trim()) return { valid: false, code: "outer_whitespace" };
    if (value.length > 256) return { valid: false, code: "too_long" };
    return { valid: true };
}

export function validateAuthenticationHost(value) {
    if (typeof value !== "string") return { valid: false, code: "not_string" };
    if (!value) return { valid: false, code: "empty" };
    if (CONTROL_CHARACTER.test(value)) return { valid: false, code: "control_character" };
    if (value !== value.trim()) return { valid: false, code: "outer_whitespace" };
    if (/\s/u.test(value)) return { valid: false, code: "whitespace" };
    if (value.length > 2048) return { valid: false, code: "too_long" };
    // Mozilla permits both host names and URI-like SPNEGO entries.  Firefox
    // performs the authoritative grammar check; BPM refuses only unsafe typed
    // input, never rewrites it.
    return { valid: true };
}

function rawFallback(reason, value) {
    return { kind: "raw_fallback", reason, value };
}

function hasOnlyFields(value, fields) {
    return isPlainObject(value) && Object.keys(value).every((field) => fields.has(field));
}

function listOfStrings(value) {
    return Array.isArray(value) && value.every((entry) => typeof entry === "string");
}

function mapOfStrings(value) {
    return isPlainObject(value) && Object.values(value).every((entry) => typeof entry === "string");
}

function mapOfTrue(value) {
    return isPlainObject(value) && Object.values(value).every((entry) => entry === true);
}

/** Inspect only policy JSON shape; no referenced file is touched. */
export function inspectCertificates(value) {
    if (value === undefined) return { kind: "typed", value: {} };
    if (!hasOnlyFields(value, CERTIFICATE_FIELDS)) return rawFallback("unknown_or_non_object", value);
    if (value.Install !== undefined && !listOfStrings(value.Install)) return rawFallback("install_not_string_list", value);
    if (value.ImportEnterpriseRoots !== undefined && typeof value.ImportEnterpriseRoots !== "boolean") {
        return rawFallback("enterprise_roots_not_boolean", value);
    }
    return {
        kind: "typed",
        value: {
            ...(value.Install === undefined ? {} : { Install: [...value.Install] }),
            ...(value.ImportEnterpriseRoots === undefined ? {} : { ImportEnterpriseRoots: value.ImportEnterpriseRoots }),
        },
        duplicates: collectDuplicates(value.Install || []),
        invalidReferences: (value.Install || []).map((entry, index) => ({ entry, index, verdict: validateCertificateReference(entry) }))
            .filter(({ verdict }) => !verdict.valid),
    };
}

/** SecurityDevices has only Add and Delete in the typed Firefox policy shape. */
export function inspectSecurityDevices(value) {
    if (value === undefined) return { kind: "typed", value: {} };
    if (!hasOnlyFields(value, SECURITY_DEVICE_FIELDS)) return rawFallback("unknown_or_non_object", value);
    if (value.Add !== undefined && !mapOfStrings(value.Add)) return rawFallback("add_not_string_map", value);
    if (value.Delete !== undefined && !listOfStrings(value.Delete)) return rawFallback("delete_not_string_list", value);
    const add = value.Add || {};
    const deleteList = value.Delete || [];
    return {
        kind: "typed",
        value: {
            ...(value.Add === undefined ? {} : { Add: { ...add } }),
            ...(value.Delete === undefined ? {} : { Delete: [...deleteList] }),
        },
        duplicates: collectDuplicates(deleteList),
        duplicateNames: Object.keys(add).filter((name, index, names) => names.indexOf(name) !== index),
        invalidAdd: Object.entries(add)
            .map(([name, path]) => ({ name, path, nameVerdict: validateSecurityDeviceName(name), pathVerdict: validateCertificateReference(path) }))
            .filter(({ nameVerdict, pathVerdict }) => !nameVerdict.valid || !pathVerdict.valid),
        invalidDelete: deleteList.map((name, index) => ({ name, index, verdict: validateSecurityDeviceName(name) }))
            .filter(({ verdict }) => !verdict.valid),
    };
}

export function inspectAuthentication(value) {
    if (value === undefined) return { kind: "typed", value: {} };
    if (!hasOnlyFields(value, AUTHENTICATION_FIELDS)) return rawFallback("unknown_or_non_object", value);
    if (AUTH_LIST_FIELDS.some((field) => value[field] !== undefined && !listOfStrings(value[field]))) {
        return rawFallback("host_list_not_string_list", value);
    }
    if (AUTH_MAP_FIELDS.some((field) => value[field] !== undefined && !mapOfTrue(value[field]))) {
        return rawFallback("host_map_not_true_map", value);
    }
    if (AUTH_BOOLEAN_FIELDS.some((field) => value[field] !== undefined && typeof value[field] !== "boolean")) {
        return rawFallback("boolean_not_boolean", value);
    }
    const next = {};
    AUTH_LIST_FIELDS.forEach((field) => {
        if (value[field] !== undefined) next[field] = [...value[field]];
    });
    AUTH_MAP_FIELDS.forEach((field) => {
        if (value[field] !== undefined) next[field] = { ...value[field] };
    });
    AUTH_BOOLEAN_FIELDS.forEach((field) => {
        if (value[field] !== undefined) next[field] = value[field];
    });
    return {
        kind: "typed",
        value: next,
        duplicates: Object.fromEntries(AUTH_LIST_FIELDS.map((field) => [field, collectDuplicates(value[field] || [])])),
        invalidHosts: [
            ...AUTH_LIST_FIELDS.flatMap((field) => (value[field] || []).map((entry, index) => ({ field, entry, index, verdict: validateAuthenticationHost(entry) }))),
            ...AUTH_MAP_FIELDS.flatMap((field) => Object.keys(value[field] || {}).map((entry) => ({ field, entry, verdict: validateAuthenticationHost(entry) }))),
        ].filter(({ verdict }) => !verdict.valid),
    };
}

export function collectDuplicates(entries) {
    const seen = new Map();
    const duplicates = [];
    entries.forEach((entry, index) => {
        const first = seen.get(entry);
        if (first === undefined) seen.set(entry, index);
        else duplicates.push({ value: entry, first, index });
    });
    return duplicates;
}

export function moveListEntry(entries, index, direction) {
    if (!Array.isArray(entries)) return { ok: false, value: entries };
    const target = index + direction;
    if (!Number.isInteger(index) || !Number.isInteger(direction) || ![-1, 1].includes(direction)
        || index < 0 || index >= entries.length || target < 0 || target >= entries.length) {
        return { ok: false, value: [...entries] };
    }
    const value = [...entries];
    [value[index], value[target]] = [value[target], value[index]];
    return { ok: true, value };
}

export function omitEmptyObject(value) {
    return isPlainObject(value) && Object.keys(value).length ? value : undefined;
}

export function omitEmptyCertificateFields(value) {
    const next = {};
    if (Array.isArray(value?.Install) && value.Install.length) next.Install = [...value.Install];
    if (typeof value?.ImportEnterpriseRoots === "boolean") next.ImportEnterpriseRoots = value.ImportEnterpriseRoots;
    return omitEmptyObject(next);
}

export function omitEmptySecurityDeviceFields(value) {
    const next = {};
    if (isPlainObject(value?.Add) && Object.keys(value.Add).length) next.Add = { ...value.Add };
    if (Array.isArray(value?.Delete) && value.Delete.length) next.Delete = [...value.Delete];
    return omitEmptyObject(next);
}

export function omitEmptyAuthenticationFields(value) {
    const next = {};
    AUTH_LIST_FIELDS.forEach((field) => {
        if (Array.isArray(value?.[field]) && value[field].length) next[field] = [...value[field]];
    });
    AUTH_MAP_FIELDS.forEach((field) => {
        if (isPlainObject(value?.[field]) && Object.keys(value[field]).length) next[field] = { ...value[field] };
    });
    AUTH_BOOLEAN_FIELDS.forEach((field) => {
        if (typeof value?.[field] === "boolean") next[field] = value[field];
    });
    return omitEmptyObject(next);
}
