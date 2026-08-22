/**
 * WebsiteFilter pattern parsing is deliberately conservative about writes and
 * deliberately lossless about imported policy values.  Firefox owns the final
 * pattern grammar; this module only rejects values which are unsafe to offer as
 * a typed URL-pattern control and never canonicalizes a value on the user's
 * behalf.
 */

import {
    ALL_URLS,
    validateWebsiteFilterPattern,
} from "./navigation_url.mjs";

export { ALL_URLS, validateWebsiteFilterPattern };

export function isPlainObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

/**
 * Return a presentation-safe verdict without altering the supplied pattern.
 * A `valid` result means it can be written by the typed manager; it does not
 * claim to reimplement Firefox's complete match-pattern parser.
 */

/**
 * Inspect an imported WebsiteFilter object before rendering editable controls.
 * A non-object, extra fields, or non-string list member must stay a raw
 * fallback: coercing it would silently change the exported policy.
 */
export function inspectImportedWebsiteFilter(value) {
    if (value === undefined) {
        return { kind: "typed", value: { Block: [], Exceptions: [] }, rawEntries: [] };
    }
    if (!isPlainObject(value)) {
        return { kind: "raw_fallback", reason: "not_object", value };
    }
    const keys = Object.keys(value);
    if (keys.some((key) => key !== "Block" && key !== "Exceptions")) {
        return { kind: "raw_fallback", reason: "unknown_field", value };
    }

    const block = value.Block === undefined ? [] : value.Block;
    const exceptions = value.Exceptions === undefined ? [] : value.Exceptions;
    if (!Array.isArray(block) || !Array.isArray(exceptions)) {
        return { kind: "raw_fallback", reason: "not_array", value };
    }
    if (![...block, ...exceptions].every((entry) => typeof entry === "string")) {
        return { kind: "raw_fallback", reason: "not_string", value };
    }

    const rawEntries = [];
    [
        ["Block", block],
        ["Exceptions", exceptions],
    ].forEach(([field, entries]) => {
        entries.forEach((entry, index) => {
            const verdict = validateWebsiteFilterPattern(entry);
            if (!verdict.valid) rawEntries.push({ field, index, value: entry, code: verdict.code });
        });
    });
    return {
        kind: "typed",
        value: { Block: [...block], Exceptions: [...exceptions] },
        rawEntries,
    };
}

/**
 * Classify exact duplicate and contradictory rows without de-duplicating or
 * reordering.  These are visible policy decisions, not cleanup opportunities.
 */
export function analyzeWebsiteFilterLists(value) {
    const inspected = inspectImportedWebsiteFilter(value);
    if (inspected.kind !== "typed") {
        return { ...inspected, duplicates: [], conflicts: [] };
    }
    const { Block: block, Exceptions: exceptions } = inspected.value;
    const duplicates = [];
    const seen = new Map();
    [
        ["Block", block],
        ["Exceptions", exceptions],
    ].forEach(([field, entries]) => {
        entries.forEach((entry, index) => {
            const key = `${field}\u0000${entry}`;
            const first = seen.get(key);
            if (first !== undefined) duplicates.push({ field, first, index, value: entry });
            else seen.set(key, index);
        });
    });

    const exceptionPositions = new Map(exceptions.map((entry, index) => [entry, index]));
    const conflicts = block
        .map((entry, index) => exceptionPositions.has(entry)
            ? { kind: "overlap", value: entry, blockIndex: index, exceptionIndex: exceptionPositions.get(entry) }
            : null)
        .filter(Boolean);
    if (exceptionPositions.has(ALL_URLS)) {
        conflicts.push({ kind: "allow_all", value: ALL_URLS, exceptionIndex: exceptionPositions.get(ALL_URLS) });
    }
    return { ...inspected, duplicates, conflicts };
}

export function resolveWebsiteFilterPosture(value) {
    const inspected = inspectImportedWebsiteFilter(value);
    if (inspected.kind !== "typed") return "raw";
    const { Block: block, Exceptions: exceptions } = inspected.value;
    const blocksAll = block.includes(ALL_URLS);
    if (!block.length && !exceptions.length) return "defaults";
    if (blocksAll && exceptions.length) return "allow_only";
    if (blocksAll) return "allow_only";
    if (block.length && exceptions.length) return "mixed";
    if (block.length) return "block_some";
    return "exceptions_only";
}

/** Preserve existing rule order and exact spelling while changing only posture. */
export function applyWebsiteFilterPosture(value, posture) {
    const inspected = inspectImportedWebsiteFilter(value);
    if (inspected.kind !== "typed") return { ok: false, reason: "raw_fallback", value };
    const next = {
        Block: [...inspected.value.Block],
        Exceptions: [...inspected.value.Exceptions],
    };
    if (posture === "defaults") return { ok: true, value: undefined };
    if (posture === "allow_only" && !next.Block.includes(ALL_URLS)) {
        next.Block.unshift(ALL_URLS);
    }
    if (posture === "block_some") {
        next.Block = next.Block.filter((entry) => entry !== ALL_URLS);
    }
    return {
        ok: ["block_some", "allow_only", "mixed"].includes(posture),
        value: omitEmptyWebsiteFilterFields(next),
    };
}

export function omitEmptyWebsiteFilterFields(value) {
    const next = {};
    if (Array.isArray(value?.Block) && value.Block.length) next.Block = [...value.Block];
    if (Array.isArray(value?.Exceptions) && value.Exceptions.length) next.Exceptions = [...value.Exceptions];
    return next;
}
