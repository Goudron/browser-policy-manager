/**
 * Lossless validation for the URL-shaped values owned by the Guided navigation
 * step.  Firefox remains the authority for its complete policy grammar.  This
 * module deliberately inspects values without serializing a URL object back to
 * the policy: user spelling, case, IDN form, ports, paths and placeholders are
 * never canonicalised by BPM.
 */

export const ALL_URLS = "<all_urls>";

const UNSAFE_SCHEME = /^(?:javascript|data|vbscript|blob|view-source):/iu;
const CONTROL_CHARACTER = /[\u0000-\u001F\u007F]/u;
const DIRECTIONAL_OR_INVISIBLE_CHARACTER = /[\u200B-\u200F\u202A-\u202E\u2060-\u206F]/u;
const NON_ASCII = /[^\x00-\x7F]/u;
const MATCH_PATTERN_SCHEMES = new Set(["http", "https", "ftp", "file", "*"]);
const EXTERNAL_SCHEMES = new Set(["http:", "https:", "ftp:", "file:"]);
const HOST_CHARACTER = /^[\p{L}\p{N}.*_-]+$/u;

/**
 * Classify the M8 policy/field pairs which are navigation values.  Unknown
 * schema fields intentionally return null: they stay schema-owned and are not
 * guessed into a navigation grammar.
 */
export function getNavigationInputKind(policyId, fieldPath = "") {
    const policy = String(policyId || "");
    const path = String(fieldPath || "");

    if (policy === "AllowedDomainsForApps" && (path === "__value__" || path === "")) {
        return "domain-list";
    }
    if (["HttpAllowlist", "LocalFileLinks"].includes(policy) && (path === "__value__" || path === "")) {
        return "http-origin";
    }
    if (policy === "AutoLaunchProtocolsFromOrigins" && path.endsWith("allowed_origins")) {
        return "http-origin";
    }
    if (policy === "Bookmarks" && ["URL", "Favicon"].includes(path)) {
        return "external-url";
    }
    if (policy === "ManagedBookmarks" && (path === "url" || path.endsWith(".url"))) {
        return "external-url";
    }
    if (policy === "Handlers" && path.endsWith("uriTemplate")) {
        return "https-template";
    }
    if (["Homepage", "OverrideFirstRunPage", "OverridePostUpdatePage"].includes(policy)) {
        return "navigation-url";
    }
    return null;
}

/**
 * Validate a value intended for a typed Guided control.  A valid result never
 * means BPM has normalised it or replaced Firefox's schema validation.
 */
export function validateNavigationValue(value, kind = "navigation-url") {
    if (kind === "website-filter") return validateWebsiteFilterPattern(value);
    if (typeof value !== "string") return { valid: false, code: "not_string" };
    if (!value) return { valid: false, code: "empty" };
    if (DIRECTIONAL_OR_INVISIBLE_CHARACTER.test(value)) {
        return { valid: false, code: "unicode_control" };
    }
    if (value !== value.trim() || CONTROL_CHARACTER.test(value) || /\s/u.test(value)) {
        return { valid: false, code: "whitespace" };
    }
    if (value.length > 2048) return { valid: false, code: "too_long" };
    if (UNSAFE_SCHEME.test(value)) return { valid: false, code: "unsafe_scheme" };

    if (kind === "domain-list") return validateDomainList(value);
    if (kind === "https-template") return validateHttpsTemplate(value);
    if (["http-origin", "external-url", "navigation-url"].includes(kind)) {
        return validateUrl(value, kind);
    }
    return { valid: false, code: "unsupported_kind" };
}

/** Return an intentionally narrow external-link descriptor, or null. */
export function getSafeExternalLink(value, kind = "external-url") {
    const verdict = validateNavigationValue(value, kind);
    if (kind === "https-template" || !verdict.valid || verdict.idn || !["http:", "https:"].includes(verdict.protocol)) {
        return null;
    }
    return {
        href: value,
        target: "_blank",
        rel: "noopener noreferrer",
        referrerPolicy: "no-referrer",
    };
}

/**
 * Imported values that do not satisfy the typed guard are retained byte-for-
 * byte in the policy.  Once a person changes the value, it must pass the
 * typed guard before BPM writes it back.
 */
export function inspectImportedNavigationValue(value, kind) {
    const verdict = validateNavigationValue(value, kind);
    return verdict.valid
        ? { kind: "typed", value, verdict }
        : { kind: "raw_fallback", value, verdict };
}

export function retainsImportedRawNavigationValue(value, originalValue, kind) {
    return typeof originalValue === "string"
        && value === originalValue
        && !validateNavigationValue(value, kind).valid;
}

export function formatNavigationValidationMessage(t, fieldLabel, verdict) {
    const rule = String(verdict?.code || "invalid_value").replaceAll("_", "-");
    return t("profiles.wizard_navigation_url_invalid")
        .replace("{field}", fieldLabel || "URL")
        .replace("{rule}", rule);
}

function validateUrl(value, kind) {
    let parsed;
    try {
        parsed = new URL(value);
    } catch {
        return { valid: false, code: "shape" };
    }
    const protocol = parsed.protocol.toLowerCase();
    if (parsed.username || parsed.password) {
        return { valid: false, code: "credentials" };
    }
    if (kind === "navigation-url") {
        if (protocol === "about:") {
            if (!["about:blank", "about:home", "about:newtab"].includes(value.toLowerCase())) {
                return { valid: false, code: "about_page" };
            }
            return { valid: true, kind, protocol, host: "", idn: false };
        }
        if (!EXTERNAL_SCHEMES.has(protocol)) return { valid: false, code: "unsupported_scheme" };
    } else if (kind === "external-url") {
        if (!EXTERNAL_SCHEMES.has(protocol)) return { valid: false, code: "unsupported_scheme" };
    } else if (kind === "http-origin") {
        if (!["http:", "https:"].includes(protocol)) return { valid: false, code: "unsupported_scheme" };
        if (parsed.pathname !== "/" || parsed.search || parsed.hash) return { valid: false, code: "origin_path" };
    }

    if (protocol === "file:") {
        if (parsed.host && parsed.host !== "localhost") return { valid: false, code: "file_host" };
        return { valid: true, kind, protocol, host: parsed.host, idn: false };
    }
    if (!parsed.hostname) return { valid: false, code: "host" };
    return {
        valid: true,
        kind,
        protocol,
        host: parsed.hostname,
        idn: NON_ASCII.test(parsed.hostname) || NON_ASCII.test(value),
    };
}

function validateHttpsTemplate(value) {
    const verdict = validateUrl(value, "external-url");
    if (!verdict.valid) return verdict;
    if (verdict.protocol !== "https:") return { valid: false, code: "unsupported_scheme" };
    if (!value.includes("%s")) return { valid: false, code: "placeholder" };
    return { ...verdict, kind: "https-template" };
}

function validateDomainList(value) {
    const domains = value.split(",");
    if (!domains.length || domains.some((domain) => !domain || domain !== domain.trim())) {
        return { valid: false, code: "domain" };
    }
    for (const domain of domains) {
        if (domain.includes("://") || domain.includes("/") || domain.includes("@") || domain.includes("\\") || !HOST_CHARACTER.test(domain) || domain.includes("..")) {
            return { valid: false, code: "domain" };
        }
    }
    return { valid: true, kind: "domain-list", idn: domains.some((domain) => NON_ASCII.test(domain)) };
}

/** Firefox match-pattern validation used by WebsiteFilter. */
export function validateWebsiteFilterPattern(value) {
    if (typeof value !== "string") {
        return { valid: false, code: "not_string" };
    }
    if (!value) {
        return { valid: false, code: "empty" };
    }
    if (DIRECTIONAL_OR_INVISIBLE_CHARACTER.test(value)) {
        return { valid: false, code: "unicode_control" };
    }
    if (value !== value.trim() || CONTROL_CHARACTER.test(value) || /\s/u.test(value)) {
        return { valid: false, code: "whitespace" };
    }
    if (value.length > 2048) {
        return { valid: false, code: "too_long" };
    }
    if (UNSAFE_SCHEME.test(value) || /^about:/iu.test(value)) {
        return { valid: false, code: "unsafe_scheme" };
    }
    if (value === ALL_URLS) {
        return { valid: true, kind: "all_urls", idn: false };
    }

    const match = /^(?<scheme>[A-Za-z*][A-Za-z0-9+.-]*):\/\/(?<authority>[^/?#]*)(?<path>\/[^?#]*)$/u.exec(value);
    if (!match?.groups) {
        return { valid: false, code: "shape" };
    }
    const scheme = match.groups.scheme.toLowerCase();
    const authority = match.groups.authority;
    if (!MATCH_PATTERN_SCHEMES.has(scheme)) {
        return { valid: false, code: "unsupported_scheme" };
    }
    if (authority.includes("@") || authority.includes("\\")) {
        return { valid: false, code: "unsafe_authority" };
    }

    if (scheme === "file" && authority === "") {
        return { valid: true, kind: "pattern", idn: false, scheme, host: "", port: "" };
    }
    if (!authority) return { valid: false, code: "unsafe_authority" };

    const parsedAuthority = parseMatchPatternAuthority(authority);
    if (!parsedAuthority.valid) return parsedAuthority;
    if (scheme === "file" && parsedAuthority.host !== "*") {
        return { valid: false, code: "file_host" };
    }
    return {
        valid: true,
        kind: "pattern",
        idn: NON_ASCII.test(parsedAuthority.host),
        scheme,
        host: parsedAuthority.host,
        port: parsedAuthority.port,
    };
}

function parseMatchPatternAuthority(authority) {
    let host = authority;
    let port = "";
    if (authority.startsWith("[")) {
        const closing = authority.indexOf("]");
        if (closing < 2) return { valid: false, code: "ipv6" };
        host = authority.slice(0, closing + 1);
        const suffix = authority.slice(closing + 1);
        if (suffix) {
            if (!suffix.startsWith(":")) return { valid: false, code: "port" };
            port = suffix.slice(1);
        }
        if (!/^\[[0-9A-Fa-f:.]+\]$/u.test(host)) return { valid: false, code: "ipv6" };
    } else {
        const colon = authority.lastIndexOf(":");
        if (colon >= 0) {
            host = authority.slice(0, colon);
            port = authority.slice(colon + 1);
        }
        if (!host || !HOST_CHARACTER.test(host) || host.includes("..")) {
            return { valid: false, code: "host" };
        }
    }
    if (port) {
        if (port !== "*" && !/^\d+$/u.test(port)) return { valid: false, code: "port" };
        const numericPort = Number(port);
        if (Number.isFinite(numericPort) && (numericPort < 1 || numericPort > 65535)) {
            return { valid: false, code: "port" };
        }
    }
    return { valid: true, host, port };
}
