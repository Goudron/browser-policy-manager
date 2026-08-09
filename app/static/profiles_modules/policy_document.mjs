/** Firefox policies.json serialization. Translation remains an injected adapter concern. */
export function isPlainObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function toFirefoxPoliciesDocument(flagsObj) {
    if (isPlainObject(flagsObj) && isPlainObject(flagsObj.policies)) return { policies: flagsObj.policies };
    return { policies: isPlainObject(flagsObj) ? flagsObj : {} };
}

export function toInternalFlags(documentObj, {
    invalidRootMessage = "Expected policies.json root object",
    invalidPoliciesMessage = "Expected policies to be an object",
} = {}) {
    if (documentObj === null || documentObj === undefined) return {};
    if (!isPlainObject(documentObj)) throw new Error(invalidRootMessage);
    if (!Object.prototype.hasOwnProperty.call(documentObj, "policies")) return documentObj;
    if (!isPlainObject(documentObj.policies)) throw new Error(invalidPoliciesMessage);
    return documentObj.policies;
}

export function fromSerializedEditorValue(text) {
    if (!text || !text.trim()) return {};
    return JSON.parse(text);
}

export function parseEditorPolicyDocument(text, options = {}) {
    return toFirefoxPoliciesDocument(toInternalFlags(fromSerializedEditorValue(text), options));
}

export function toEditorValue(obj) {
    return JSON.stringify(toFirefoxPoliciesDocument(obj), null, 2);
}

export function fromEditorValue(text, options = {}) {
    return toInternalFlags(fromSerializedEditorValue(text), options);
}

export function getPolicyValue(flagsObj, policyKey, options = {}) {
    return toInternalFlags(flagsObj, options)[policyKey];
}

export function setPolicyValue(flagsObj, policyKey, value, options = {}) {
    const flags = { ...toInternalFlags(flagsObj, options) };
    if (value === undefined) delete flags[policyKey];
    else flags[policyKey] = value;
    return flags;
}
