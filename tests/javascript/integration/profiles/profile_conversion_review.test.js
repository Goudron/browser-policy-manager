import assert from "node:assert/strict";
import test from "node:test";

import {
    CONVERSION_REVIEW_STATES,
    aggregatePlanSummary,
    buildConversionApplyPayload,
    create,
    readConversionReviewQuery,
    recommendedConversionTarget,
    reviewStateForError,
    supportedConversionTargets,
} from "../../../../app/static/profiles_modules/conversion_review.mjs";
import {
    applyProfileConversion,
    previewProfileConversion,
} from "../../../../app/static/profiles_data.js";

const catalog = {
    options: [
        {
            artifact_id: "release-153", support_state: "supported", selectable: true,
            recommendation_target: null,
        },
        {
            artifact_id: "esr-153.0", support_state: "supported", selectable: true,
            recommendation_target: null,
        },
        {
            artifact_id: "esr-140.13", support_state: "supported", selectable: true,
            recommendation_target: "esr-153.0",
        },
        {
            artifact_id: "esr-115.38", support_state: "supported", selectable: true,
            recommendation_target: "esr-153.0",
        },
        { artifact_id: "esr-102.15", support_state: "retired", selectable: false },
    ],
};

function conversionPlan() {
    return {
        available: true,
        profile: {
            id: 17,
            revision: 4,
            metadata_digest: "a".repeat(64),
        },
        source: {
            artifact: {
                line_id: "esr-140",
                artifact_id: "esr-140.13",
                validation_schema_sha256: "b".repeat(64),
            },
            document_digest: "c".repeat(64),
            compliance_digest: "d".repeat(64),
        },
        target: {
            artifact: {
                line_id: "esr-153",
                artifact_id: "esr-153.0",
                validation_schema_sha256: "e".repeat(64),
            },
        },
        recipe_registry: {
            registry_version: 1,
            registry_digest: "f".repeat(64),
        },
        compatibility: {
            applicable: true,
            counts: {
                unchanged_byte: 3,
                unchanged_semantic: 1,
                transformed: 0,
                blocked: 0,
                blockers: 0,
                warnings: 1,
            },
        },
        target_validation: { status: "valid", issues: [] },
        compliance: { disposition: "recomputed", target_claims_current: true },
        blockers: [],
        entries: [{ policy_id: "SensitivePolicy", source_paths: ["/SensitivePolicy"] }],
        plan_digest: "0".repeat(64),
    };
}

function fakeReviewHost() {
    let elements = new Map();
    const makeElement = () => {
        const listeners = new Map();
        return {
            attributes: new Map(),
            checked: false,
            disabled: false,
            focusCalls: 0,
            value: "",
            addEventListener(type, listener) { listeners.set(type, listener); },
            async emit(type, values = {}) {
                Object.assign(this, values);
                return listeners.get(type)?.({ currentTarget: this });
            },
            focus() { this.focusCalls += 1; },
            setAttribute(name, value) { this.attributes.set(name, value); },
        };
    };
    return {
        hidden: true,
        dataset: {},
        attributes: new Map(),
        setAttribute(name, value) { this.attributes.set(name, value); },
        getAttribute(name) { return this.attributes.get(name); },
        getElement(selector) { return this.querySelector(selector); },
        querySelector(selector) {
            if (!elements.has(selector)) elements.set(selector, makeElement());
            return elements.get(selector);
        },
        set innerHTML(value) {
            this._innerHTML = value;
            elements = new Map();
        },
        get innerHTML() { return this._innerHTML || ""; },
    };
}

test("catalog target selector is data-derived and excludes only the current or unavailable artifact", () => {
    assert.deepEqual(
        supportedConversionTargets(catalog, "esr-140.13").map((option) => option.artifact_id),
        ["release-153", "esr-153.0", "esr-115.38"],
    );
    assert.equal(recommendedConversionTarget(catalog, "esr-140.13"), "esr-153.0");
    assert.equal(recommendedConversionTarget(catalog, "release-153"), "");
    assert.equal(recommendedConversionTarget({ options: [] }, "esr-140.13"), "");
    assert.deepEqual(supportedConversionTargets(null, "esr-140.13"), []);
    assert.equal(recommendedConversionTarget(null, "esr-140.13"), "");
});

test("Library handoff query carries only the supported conversion trigger fields", () => {
    assert.deepEqual(
        readConversionReviewQuery("?schema_conversion=preview&target_artifact_id=esr-153.0&recommendation_id=schema-conversion.older-esr-recommendation"),
        {
            targetArtifactId: "esr-153.0",
            recommendationId: "schema-conversion.older-esr-recommendation",
        },
    );
    assert.equal(readConversionReviewQuery("?schema_conversion=apply&target_artifact_id=esr-153.0"), null);
    assert.equal(readConversionReviewQuery("?schema_conversion=preview"), null);
    assert.equal(readConversionReviewQuery(), null);
});

test("apply payload is exactly bound to one fresh preview and never contains policy candidates", () => {
    const payload = buildConversionApplyPayload(conversionPlan());

    assert.deepEqual(Object.keys(payload).sort(), [
        "contract_version", "expected_revision", "kind", "plan_digest", "profile_id",
        "recipe_registry_digest", "recipe_registry_version", "source", "source_compliance_digest",
        "source_document_digest", "source_metadata_digest", "source_validation_schema_sha256",
        "target", "target_artifact_id", "target_validation_schema_sha256",
    ]);
    assert.equal(payload.target_artifact_id, "esr-153.0");
    assert.equal(payload.source.artifact_id, "esr-140.13");
    assert.equal("policies" in payload, false);
    assert.equal("entries" in payload, false);
    assert.equal(buildConversionApplyPayload({ ...conversionPlan(), compatibility: { applicable: false } }), null);
    assert.equal(buildConversionApplyPayload({ ...conversionPlan(), target_validation: { status: "invalid" } }), null);
});

test("errors use stable recovery states without depending on HTTP text", () => {
    assert.equal(
        reviewStateForError({ detail: { code: "conversion_revision_stale" } }),
        CONVERSION_REVIEW_STATES.stale,
    );
    assert.equal(
        reviewStateForError({ detail: { code: "conversion_plan_stale" } }),
        CONVERSION_REVIEW_STATES.changed,
    );
    assert.equal(
        reviewStateForError({ detail: { code: "conversion_source_not_active" } }),
        CONVERSION_REVIEW_STATES.sourceInactive,
    );
    assert.equal(
        reviewStateForError(
            { detail: { code: "schema_channel_unknown", parameters: { target_artifact_id: "esr-153.0" } } },
            "esr-153.0",
        ),
        CONVERSION_REVIEW_STATES.targetUnavailable,
    );
    assert.equal(
        reviewStateForError({ detail: { code: "schema_channel_retired_requires_migration" } }),
        CONVERSION_REVIEW_STATES.retirement,
    );
    assert.equal(
        reviewStateForError({ detail: { code: "conversion_plan_blocked" } }),
        CONVERSION_REVIEW_STATES.blocked,
    );
    assert.equal(
        reviewStateForError({ detail: { code: "conversion_apply_failed" } }),
        CONVERSION_REVIEW_STATES.failed,
    );
    assert.equal(
        reviewStateForError({ detail: { code: "conversion_target_identical" } }),
        CONVERSION_REVIEW_STATES.targetUnavailable,
    );
    assert.equal(
        reviewStateForError({ detail: { code: "conversion_source_invalid" } }),
        CONVERSION_REVIEW_STATES.sourceInvalid,
    );
    assert.equal(
        reviewStateForError({ detail: { code: "unclassified" } }),
        CONVERSION_REVIEW_STATES.unavailable,
    );
    assert.equal(
        reviewStateForError(
            { detail: { code: "schema_channel_unknown", parameters: { target_artifact_id: "esr-115.38" } } },
            "esr-153.0",
        ),
        CONVERSION_REVIEW_STATES.sourceInvalid,
    );
});

test("plan review renders only aggregates and query auto-preview cannot apply", async () => {
    const host = fakeReviewHost();
    const profile = { id: 17, revision: 4, schema_version: "esr-140.13", is_deleted: false };
    let previewCalls = 0;
    let applyCalls = 0;
    const windowRef = {
        location: {
            href: "https://bpm.test/profiles/17/edit?schema_conversion=preview&target_artifact_id=esr-153.0&recommendation_id=schema-conversion.older-esr-recommendation",
            search: "?schema_conversion=preview&target_artifact_id=esr-153.0&recommendation_id=schema-conversion.older-esr-recommendation",
        },
        requestAnimationFrame(callback) { callback(); },
        setTimeout(callback) { callback(); return 1; },
        history: { replaceState() {} },
    };
    const documentRef = {
        activeElement: null,
        getElementById(id) {
            return id === "schema-conversion-review" ? host : null;
        },
    };
    const review = create({
        documentRef,
        windowRef,
        schemaChannelsCatalog: catalog,
        dependencies: {
            formatSchemaLabel: (artifactId) => `Schema ${artifactId}`,
            previewProfileConversion: async () => {
                previewCalls += 1;
                return conversionPlan();
            },
            applyProfileConversion: async () => { applyCalls += 1; },
            loadProfile: async () => profile,
        },
        state: { getCurrentProfile: () => profile },
    });

    review.start();
    await new Promise((resolve) => setImmediate(resolve));

    assert.equal(previewCalls, 1);
    assert.equal(applyCalls, 0);
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.available);
    assert.match(host.innerHTML, /Unchanged settings: 4/);
    assert.match(host.innerHTML, /Target validation: valid/);
    assert.match(host.innerHTML, /data-schema-conversion-target-select/);
    assert.doesNotMatch(host.innerHTML, /SensitivePolicy|\/SensitivePolicy|aaaaaaaaaaaaaaaa/);
    assert.doesNotMatch(host.innerHTML, /data-[^=]*digest|data-[^=]*policy/);
});

test("review uses localized state copy and a target-specific accessible apply name", () => {
    const host = fakeReviewHost();
    const profile = { id: 17, revision: 4, schema_version: "esr-140.13", is_deleted: false };
    const translations = {
        "profiles.schema_conversion_target_label": "Zielschema",
        "profiles.schema_conversion_target_consequence": "Die Zielauswahl ändert das gespeicherte Profil nicht.",
        "profiles.schema_conversion_target_accessible_name": "Zielschema für die Migration auswählen",
    };
    const review = create({
        documentRef: {
            activeElement: null,
            getElementById(id) { return id === "schema-conversion-review" ? host : null; },
        },
        windowRef: {
            location: { href: "https://bpm.test/profiles/17/edit", search: "" },
            requestAnimationFrame(callback) { callback(); },
        },
        schemaChannelsCatalog: catalog,
        dependencies: {
            t: (key, fallback) => translations[key] || fallback,
            formatSchemaLabel: (artifactId) => `Schema ${artifactId}`,
        },
        state: { getCurrentProfile: () => profile },
    });

    review.open({ targetArtifactId: "unavailable" });
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.idle);

    assert.match(host.innerHTML, /Zielschema/);
    assert.match(host.innerHTML, /Die Zielauswahl ändert das gespeicherte Profil nicht/);
    assert.match(host.innerHTML, /aria-label="Zielschema für die Migration auswählen"/);
});

test("conversion transport keeps preview target-only and apply explicit", async () => {
    const requests = [];
    const fetchImpl = async (url, options) => {
        requests.push({ url, options });
        return {
            ok: true,
            json: async () => ({ ok: true }),
        };
    };
    const payload = buildConversionApplyPayload(conversionPlan());

    await previewProfileConversion(17, "esr-153.0", fetchImpl);
    await applyProfileConversion(17, payload, fetchImpl);

    assert.deepEqual(requests[0], {
        url: "/api/profiles/17/conversion-preview",
        options: {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ target_artifact_id: "esr-153.0" }),
        },
    });
    assert.equal(requests[1].url, "/api/profiles/17/conversion-apply");
    assert.equal(requests[1].options.method, "POST");
    assert.deepEqual(JSON.parse(requests[1].options.body), payload);
});

test("apply reloads the exact saved target revision before announcing success", async () => {
    const host = fakeReviewHost();
    let currentProfile = { id: 17, revision: 4, schema_version: "esr-140.13", is_deleted: false };
    const savedProfile = { id: 17, revision: 5, schema_version: "esr-153.0", is_deleted: false };
    let applyPayload = null;
    const review = create({
        documentRef: {
            activeElement: null,
            getElementById(id) { return id === "schema-conversion-review" ? host : null; },
        },
        windowRef: {
            location: { href: "https://bpm.test/profiles/17/edit", search: "" },
            requestAnimationFrame(callback) { callback(); },
        },
        schemaChannelsCatalog: catalog,
        dependencies: {
            formatSchemaLabel: (artifactId) => `Schema ${artifactId}`,
            previewProfileConversion: async () => conversionPlan(),
            applyProfileConversion: async (_id, payload) => {
                applyPayload = payload;
                return {
                    status: "applied",
                    profile_id: 17,
                    result_revision: 5,
                    target: { artifact_id: "esr-153.0" },
                };
            },
            loadProfile: async () => {
                currentProfile = savedProfile;
                return savedProfile;
            },
        },
        state: { getCurrentProfile: () => currentProfile },
    });

    review.open({ targetArtifactId: "esr-153.0", autoPreview: true });
    await new Promise((resolve) => setImmediate(resolve));
    review.showConfirmation();
    await review.apply();

    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.success);
    assert.equal(applyPayload.expected_revision, 4);
    assert.equal(applyPayload.target_artifact_id, "esr-153.0");
    assert.match(host.innerHTML, /exact saved profile state has been reloaded/);
    await host.getElement("[data-schema-conversion-return]").emit("click");
    assert.equal(host.hidden, true);
});

test("aggregate summary carries no policy identity or raw conversion data", () => {
    const summary = aggregatePlanSummary({
        ...conversionPlan(),
        blockers: [{ code: "target_validation_failed", policy_id: "SensitivePolicy", paths: ["/SensitivePolicy"] }],
    });

    assert.deepEqual(summary, {
        unchanged: 4,
        transformed: 0,
        blocked: 0,
        warnings: 1,
        validationStatus: "valid",
        validationIssues: 0,
        complianceDisposition: "recomputed",
        complianceCurrent: true,
        blockerCodes: ["target_validation_failed"],
    });
    assert.equal(JSON.stringify(summary).includes("SensitivePolicy"), false);
});

test("a dirty workspace gates automatic preview until the user makes an explicit decision", async () => {
    const host = fakeReviewHost();
    const profile = { id: 17, revision: 4, schema_version: "esr-140.13", is_deleted: false };
    let previewCalls = 0;
    const opener = { focusCalls: 0, focus() { this.focusCalls += 1; } };
    const review = create({
        documentRef: {
            activeElement: opener,
            getElementById(id) {
                if (id === "schema-conversion-review") return host;
                if (id === "schema-conversion-review-open") return opener;
                return null;
            },
        },
        windowRef: {
            location: {
                href: "https://bpm.test/profiles/17/edit?schema_conversion=preview&target_artifact_id=esr-153.0",
                search: "?schema_conversion=preview&target_artifact_id=esr-153.0",
            },
            requestAnimationFrame(callback) { callback(); },
            setTimeout(callback) { callback(); return 1; },
            history: { replaceState() {} },
        },
        schemaChannelsCatalog: catalog,
        dependencies: {
            formatSchemaLabel: (artifactId) => `Schema ${artifactId}`,
            currentSnapshotState: () => ({ dirty: true, invalid: false }),
            previewProfileConversion: async () => { previewCalls += 1; return conversionPlan(); },
        },
        state: { getCurrentProfile: () => profile },
    });

    review.open({
        targetArtifactId: "esr-153.0",
        recommendationId: "schema-conversion.older-esr-recommendation",
        autoPreview: true,
    });
    await new Promise((resolve) => setImmediate(resolve));

    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.unsaved);
    assert.equal(previewCalls, 0);
    assert.match(host.innerHTML, /data-schema-conversion-save-preview/);
    assert.match(host.innerHTML, /data-schema-conversion-discard-preview/);
    assert.match(host.innerHTML, /No preview or conversion will run first/);

    review.cancel();
    assert.equal(host.hidden, true);
    assert.equal(opener.focusCalls, 1);
    assert.equal(previewCalls, 0);
});

test("Library query handoff waits for the initial workspace snapshot instead of misclassifying it as source-invalid", async () => {
    const host = fakeReviewHost();
    const profile = { id: 17, revision: 4, schema_version: "esr-140.13", is_deleted: false };
    const scheduled = [];
    let ready = false;
    let previewCalls = 0;
    const review = create({
        documentRef: {
            activeElement: null,
            getElementById(id) { return id === "schema-conversion-review" ? host : null; },
        },
        windowRef: {
            location: {
                href: "https://bpm.test/profiles/17/edit?schema_conversion=preview&target_artifact_id=esr-153.0&recommendation_id=schema-conversion.older-esr-recommendation",
                search: "?schema_conversion=preview&target_artifact_id=esr-153.0&recommendation_id=schema-conversion.older-esr-recommendation",
            },
            requestAnimationFrame(callback) { callback(); },
            setTimeout(callback) { scheduled.push(callback); return scheduled.length; },
            history: { replaceState() {} },
        },
        schemaChannelsCatalog: catalog,
        dependencies: {
            formatSchemaLabel: (artifactId) => `Schema ${artifactId}`,
            currentSnapshotState: () => (ready
                ? { dirty: false, invalid: false }
                : { dirty: true, invalid: true }),
            previewProfileConversion: async () => { previewCalls += 1; return conversionPlan(); },
        },
        state: { getCurrentProfile: () => profile },
    });

    review.start();
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.idle);
    assert.equal(previewCalls, 0);
    assert.equal(scheduled.length, 1);

    ready = true;
    scheduled.shift()();
    await new Promise((resolve) => setImmediate(resolve));

    assert.equal(previewCalls, 1);
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.available);
});

test("a blocked preview stays aggregate-only and a retry starts a fresh target-only request", async () => {
    const host = fakeReviewHost();
    const profile = { id: 17, revision: 4, schema_version: "esr-140.13", is_deleted: false };
    const requests = [];
    let attempt = 0;
    const review = create({
        documentRef: {
            activeElement: null,
            getElementById(id) { return id === "schema-conversion-review" ? host : null; },
        },
        windowRef: {
            location: { href: "https://bpm.test/profiles/17/edit", search: "" },
            requestAnimationFrame(callback) { callback(); },
        },
        schemaChannelsCatalog: catalog,
        dependencies: {
            formatSchemaLabel: (artifactId) => `Schema ${artifactId}`,
            previewProfileConversion: async (id, targetArtifactId) => {
                requests.push({ id, targetArtifactId });
                attempt += 1;
                const target = {
                    ...conversionPlan().target,
                    artifact: {
                        ...conversionPlan().target.artifact,
                        line_id: targetArtifactId === "esr-115.38" ? "esr-115" : "esr-153",
                        artifact_id: targetArtifactId,
                    },
                };
                if (attempt === 1) {
                    return {
                        ...conversionPlan(),
                        target,
                        compatibility: {
                            applicable: false,
                            counts: {
                                ...conversionPlan().compatibility.counts,
                                blocked: 1,
                                blockers: 1,
                            },
                        },
                        blockers: [{ code: "conversion_policy_blocked", policy_id: "SensitivePolicy" }],
                    };
                }
                return { ...conversionPlan(), target };
            },
        },
        state: { getCurrentProfile: () => profile },
    });

    await review.selectTarget("esr-115.38");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.blocked);
    assert.match(host.innerHTML, /Blocked condition: conversion_policy_blocked/);
    assert.doesNotMatch(host.innerHTML, /SensitivePolicy/);
    assert.doesNotMatch(host.innerHTML, /data-(?:policy|conversion-policy|plan-digest|document-digest)/);

    await review.selectTarget("esr-153.0");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.available);
    assert.deepEqual(requests, [
        { id: 17, targetArtifactId: "esr-115.38" },
        { id: 17, targetArtifactId: "esr-153.0" },
    ]);
});

test("interactive review controls preserve dirty-work, confirmation, and reload boundaries", async () => {
    const host = fakeReviewHost();
    const opener = { addEventListener() {}, focus() {} };
    let profile = { id: 17, revision: 4, schema_version: "esr-140.13", is_deleted: false };
    let snapshot = { dirty: false, invalid: false };
    let saveSucceeds = false;
    let reloads = 0;
    const assigned = [];
    const windowRef = {
        location: {
            href: "https://bpm.test/profiles/17/edit?keep=1#review",
            search: "",
            assign(href) { assigned.push(href); },
            reload() { reloads += 1; },
        },
        requestAnimationFrame(callback) { callback(); },
    };
    const review = create({
        documentRef: {
            activeElement: opener,
            getElementById(id) {
                if (id === "schema-conversion-review") return host;
                if (id === "schema-conversion-review-open") return opener;
                return null;
            },
        },
        windowRef,
        schemaChannelsCatalog: catalog,
        dependencies: {
            formatSchemaLabel: (artifactId) => `Schema ${artifactId}`,
            currentSnapshotState: () => snapshot,
            saveCurrent: async () => saveSucceeds,
            previewProfileConversion: async () => conversionPlan(),
            applyProfileConversion: async () => ({
                status: "applied",
                profile_id: 17,
                result_revision: 5,
                target: { artifact_id: "esr-153.0" },
            }),
            loadProfile: async () => ({ id: 17, revision: 5, schema_version: "stale-editor-value" }),
        },
        state: { getCurrentProfile: () => profile },
    });

    review.open({ targetArtifactId: "esr-153.0" });
    await host.getElement("[data-schema-conversion-target-select]").emit("change", { value: "" });
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.idle);
    await host.getElement("[data-schema-conversion-target-select]").emit("change", { value: "unavailable" });
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.targetUnavailable);

    snapshot = { dirty: false, invalid: true };
    await review.selectTarget("esr-153.0");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.sourceInvalid);

    snapshot = { dirty: true, invalid: false };
    await review.selectTarget("esr-153.0");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.unsaved);
    await host.getElement("[data-schema-conversion-discard-preview]").emit("click");
    assert.deepEqual(assigned, ["/profiles/17/edit?keep=1&schema_conversion=preview&target_artifact_id=esr-153.0#review"]);
    await host.getElement("[data-schema-conversion-save-preview]").emit("click");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.unsaved);

    saveSucceeds = true;
    snapshot = { dirty: false, invalid: false };
    await host.getElement("[data-schema-conversion-save-preview]").emit("click");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.available);
    await host.getElement("[data-schema-conversion-confirm]").emit("click");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.confirmation);
    const check = host.getElement("[data-schema-conversion-confirm-check]");
    await check.emit("change", { checked: true });
    assert.equal(host.getElement("[data-schema-conversion-apply]").disabled, false);
    const querySelector = host.querySelector.bind(host);
    host.querySelector = (selector) => (selector === "[data-schema-conversion-apply]" ? null : querySelector(selector));
    await check.emit("change", { checked: false });
    host.querySelector = querySelector;
    await host.getElement("[data-schema-conversion-apply]").emit("click");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.success);
    assert.match(host.innerHTML, /could not reload its exact saved state/);
    await host.getElement("[data-schema-conversion-return]").emit("click");
    assert.equal(reloads, 1);

    profile = { id: null, revision: 4, schema_version: "esr-140.13", is_deleted: false };
    review.open({ targetArtifactId: "esr-153.0" });
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.sourceInactive);
    await review.requestPreview();
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.sourceInactive);
});

test("review detects stale preview identities, stale applies, and dynamic target withdrawal", async () => {
    const host = fakeReviewHost();
    const profile = { id: 17, revision: 4, schema_version: "esr-140.13", is_deleted: false };
    const mutableCatalog = structuredClone(catalog);
    let previewMode = "mismatch";
    const review = create({
        documentRef: {
            activeElement: null,
            getElementById(id) { return id === "schema-conversion-review" ? host : null; },
        },
        windowRef: {
            location: { href: "https://bpm.test/profiles/17/edit", search: "" },
            requestAnimationFrame(callback) { callback(); },
        },
        schemaChannelsCatalog: mutableCatalog,
        dependencies: {
            previewProfileConversion: async () => (previewMode === "mismatch"
                ? { ...conversionPlan(), profile: { ...conversionPlan().profile, id: 99 } }
                : conversionPlan()),
        },
        state: { getCurrentProfile: () => profile },
    });

    await review.selectTarget("esr-153.0");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.unavailable);
    previewMode = "valid";
    await review.selectTarget("esr-153.0");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.available);
    review.showConfirmation();
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.confirmation);
    profile.is_deleted = true;
    await review.apply();
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.changed);

    profile.is_deleted = false;
    review.open({ targetArtifactId: "esr-153.0" });
    mutableCatalog.options = mutableCatalog.options.filter((option) => option.artifact_id !== "esr-153.0");
    await review.requestPreview();
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.targetUnavailable);
    review.showConfirmation();
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.changed);
});

test("apply refuses a mismatched server result and reports a rejected apply without retaining a plan", async () => {
    const profile = { id: 17, revision: 4, schema_version: "esr-140.13", is_deleted: false };
    const host = fakeReviewHost();
    let applyMode = "mismatch";
    const review = create({
        documentRef: {
            activeElement: null,
            getElementById(id) { return id === "schema-conversion-review" ? host : null; },
        },
        windowRef: {
            location: { href: "https://bpm.test/profiles/17/edit", search: "" },
            requestAnimationFrame(callback) { callback(); },
        },
        schemaChannelsCatalog: catalog,
        dependencies: {
            previewProfileConversion: async () => conversionPlan(),
            applyProfileConversion: async () => {
                if (applyMode === "mismatch") {
                    return {
                        status: "applied",
                        profile_id: 17,
                        result_revision: 7,
                        target: { artifact_id: "esr-153.0" },
                    };
                }
                throw { detail: { code: "conversion_apply_failed" } };
            },
        },
        state: { getCurrentProfile: () => profile },
    });

    await review.selectTarget("esr-153.0");
    review.showConfirmation();
    await review.apply();
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.unavailable);
    applyMode = "rejected";
    await review.selectTarget("esr-153.0");
    review.showConfirmation();
    await review.apply();
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.failed);
    await host.getElement("[data-schema-conversion-refresh]").emit("click");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.available);
});

test("review defaults and absent DOM boundaries remain non-writing recovery paths", async () => {
    const absentReview = create({
        documentRef: { getElementById() { return null; } },
        windowRef: { location: { search: "" } },
    });
    absentReview.start();
    absentReview.open();
    await absentReview.apply();

    const documentFor = (host, opener = null) => ({
        activeElement: null,
        getElementById(id) {
            if (id === "schema-conversion-review") return host;
            if (id === "schema-conversion-review-open") return opener;
            return null;
        },
    });
    const location = { href: "https://bpm.test/profiles/17/edit", search: "" };
    const baseWindow = {
        location,
        requestAnimationFrame(callback) { callback(); },
    };
    const profile = { id: 17, revision: 4, schema_version: "esr-140.13", is_deleted: false };

    const defaultPreviewHost = fakeReviewHost();
    const defaultPreview = create({
        documentRef: documentFor(defaultPreviewHost),
        windowRef: baseWindow,
        schemaChannelsCatalog: catalog,
        state: { getCurrentProfile: () => profile },
    });
    await defaultPreview.selectTarget("esr-153.0");
    assert.equal(defaultPreview.getState(), CONVERSION_REVIEW_STATES.unavailable);

    const defaultApplyHost = fakeReviewHost();
    const defaultApply = create({
        documentRef: documentFor(defaultApplyHost),
        windowRef: baseWindow,
        schemaChannelsCatalog: catalog,
        dependencies: { previewProfileConversion: async () => conversionPlan() },
        state: { getCurrentProfile: () => profile },
    });
    await defaultApply.selectTarget("esr-153.0");
    defaultApply.showConfirmation();
    await defaultApply.apply();
    assert.equal(defaultApply.getState(), CONVERSION_REVIEW_STATES.unavailable);

    const defaultLoadHost = fakeReviewHost();
    const defaultLoad = create({
        documentRef: documentFor(defaultLoadHost),
        windowRef: baseWindow,
        schemaChannelsCatalog: catalog,
        dependencies: {
            previewProfileConversion: async () => conversionPlan(),
            applyProfileConversion: async () => ({
                status: "applied",
                profile_id: 17,
                result_revision: 5,
                target: { artifact_id: "esr-153.0" },
            }),
        },
        state: { getCurrentProfile: () => profile },
    });
    await defaultLoad.selectTarget("esr-153.0");
    defaultLoad.showConfirmation();
    await defaultLoad.apply();
    assert.equal(defaultLoad.getState(), CONVERSION_REVIEW_STATES.success);
    assert.match(defaultLoadHost.innerHTML, /could not reload its exact saved state/);

    const defaultSaveHost = fakeReviewHost();
    const defaultSave = create({
        documentRef: documentFor(defaultSaveHost),
        windowRef: baseWindow,
        schemaChannelsCatalog: catalog,
        dependencies: { currentSnapshotState: () => ({ dirty: true, invalid: false }) },
        state: { getCurrentProfile: () => profile },
    });
    await defaultSave.selectTarget("esr-153.0");
    await defaultSaveHost.getElement("[data-schema-conversion-save-preview]").emit("click");
    assert.equal(defaultSave.getState(), CONVERSION_REVIEW_STATES.unsaved);

    const defaultProfileHost = fakeReviewHost();
    const defaultProfile = create({
        documentRef: documentFor(defaultProfileHost),
        windowRef: baseWindow,
        schemaChannelsCatalog: catalog,
    });
    defaultProfile.open();
    assert.equal(defaultProfile.getState(), CONVERSION_REVIEW_STATES.sourceInactive);
});

test("review handles catalog fallbacks, incomplete summaries, and query handoff retries", async () => {
    const host = fakeReviewHost();
    const opener = {
        listener: null,
        addEventListener(_type, listener) { this.listener = listener; },
    };
    const profile = { id: 17, revision: 4, schema_version: "esr-140.13", is_deleted: false };
    const queryTimers = [];
    let snapshot = { dirty: false, invalid: true };
    const review = create({
        documentRef: {
            activeElement: null,
            getElementById(id) {
                if (id === "schema-conversion-review") return host;
                if (id === "schema-conversion-review-open") return opener;
                return null;
            },
        },
        windowRef: {
            location: {
                href: "https://bpm.test/profiles/17/edit?schema_conversion=preview&target_artifact_id=esr-153.0",
                search: "?schema_conversion=preview&target_artifact_id=esr-153.0",
            },
            requestAnimationFrame(callback) { callback(); },
            setTimeout(callback) { queryTimers.push(callback); return queryTimers.length; },
            history: { replaceState() {} },
        },
        schemaChannelsCatalog: { options: [] },
        dependencies: {
            currentSnapshotState: () => snapshot,
            previewProfileConversion: async () => ({
                ...conversionPlan(),
                compatibility: { applicable: false, counts: conversionPlan().compatibility.counts },
                target_validation: { status: "", issues: [] },
                compliance: {},
            }),
            t: () => "",
        },
        state: { getCurrentProfile: () => profile },
    });

    review.start();
    review.start();
    assert.equal(queryTimers.length, 1);
    opener.listener();
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.targetUnavailable);
    snapshot = null;
    queryTimers.shift()();
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.targetUnavailable);
    review.open({ targetArtifactId: "unavailable" });
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.targetUnavailable);
    assert.match(host.innerHTML, /Choose a target/);
    await review.requestPreview();
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.idle);
});

test("review renders an incomplete plan as blocked without treating it as a saved conversion", async () => {
    const host = fakeReviewHost();
    const profile = { id: 17, revision: 4, schema_version: "", is_deleted: false };
    const review = create({
        documentRef: {
            activeElement: null,
            getElementById(id) { return id === "schema-conversion-review" ? host : null; },
        },
        windowRef: {
            location: { href: "https://bpm.test/profiles/17/edit", search: "" },
            requestAnimationFrame(callback) { callback(); },
        },
        schemaChannelsCatalog: {
            options: [{ artifact_id: "esr-153.0", support_state: "supported", selectable: true }],
        },
        dependencies: {
            currentSnapshotState: () => null,
            previewProfileConversion: async () => ({
                ...conversionPlan(),
                compatibility: { applicable: false, counts: conversionPlan().compatibility.counts },
                target_validation: { status: "", issues: [] },
                compliance: {},
            }),
        },
        state: { getCurrentProfile: () => profile },
    });

    await review.selectTarget("esr-153.0");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.blocked);
    assert.match(host.innerHTML, /Target validation: not run/);
    assert.match(host.innerHTML, /Compliance outcome: not available/);
});

test("review ignores cancellation and recovery controls while a preview request is pending", async () => {
    const host = fakeReviewHost();
    const profile = { id: 17, revision: 4, schema_version: "esr-140.13", is_deleted: false };
    let resolvePreview;
    const review = create({
        documentRef: {
            activeElement: null,
            getElementById(id) { return id === "schema-conversion-review" ? host : null; },
        },
        windowRef: {
            location: { href: "https://bpm.test/profiles/17/edit", search: "" },
            requestAnimationFrame(callback) { callback(); },
        },
        schemaChannelsCatalog: catalog,
        dependencies: {
            previewProfileConversion: () => new Promise((resolve) => { resolvePreview = resolve; }),
        },
        state: { getCurrentProfile: () => profile },
    });

    const selecting = review.selectTarget("esr-153.0");
    await Promise.resolve();
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.pending);
    review.cancel();
    await host.getElement("[data-schema-conversion-save-preview]").emit("click");
    await host.getElement("[data-schema-conversion-discard-preview]").emit("click");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.pending);
    resolvePreview(conversionPlan());
    await selecting;
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.available);
});

test("review tolerates a rerender that omits transient focus targets", async () => {
    const host = fakeReviewHost();
    const querySelector = host.querySelector.bind(host);
    host.querySelector = (selector) => (
        selector === "#schema-conversion-review-title" || selector === "[data-schema-conversion-terminal]"
            ? null
            : querySelector(selector)
    );
    const profile = { id: 17, revision: 4, schema_version: "esr-140.13", is_deleted: false };
    const review = create({
        documentRef: {
            activeElement: null,
            getElementById(id) { return id === "schema-conversion-review" ? host : null; },
        },
        windowRef: {
            location: { href: "https://bpm.test/profiles/17/edit", search: "" },
            requestAnimationFrame(callback) { callback(); },
        },
        schemaChannelsCatalog: catalog,
        state: { getCurrentProfile: () => profile },
    });

    review.open({ targetArtifactId: "esr-153.0" });
    await review.selectTarget("unavailable");
    assert.equal(review.getState(), CONVERSION_REVIEW_STATES.targetUnavailable);
});
