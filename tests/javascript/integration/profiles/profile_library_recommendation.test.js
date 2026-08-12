import assert from "node:assert/strict";
import test from "node:test";

import {
    buildLibraryConversionRecommendationMarkup,
    buildLibraryConversionPreviewHref,
    recommendationCopy,
    resolveLibraryConversionRecommendation,
} from "../../../../app/static/profiles_modules/conversion_recommendation.mjs";

const recommendation = {
    recommendation_id: "schema-conversion.older-esr-recommendation",
    reason_code: "supported_older_esr_to_latest_esr",
    profile_revision: 7,
    source: { line_id: "esr-140", artifact_id: "esr-140.13" },
    target: {
        line_id: "esr-153",
        artifact_id: "esr-153.0",
        label: "Firefox ESR 153",
        i18n_key: "profiles.schema_esr_153",
    },
    action: { action_id: "conversion-preview", preview_target_artifact_id: "esr-153.0" },
};

test("uses only an eligible read-model recommendation and its exact target", () => {
    const profile = {
        id: 41,
        revision: 7,
        schema_version: "esr-140.13",
        is_deleted: false,
        recommendation,
    };

    assert.equal(resolveLibraryConversionRecommendation(profile), recommendation);
    assert.equal(
        buildLibraryConversionPreviewHref(profile, recommendation, "https://bpm.example"),
        "/profiles/41/edit?schema_conversion=preview&target_artifact_id=esr-153.0&recommendation_id=schema-conversion.older-esr-recommendation",
    );
});

test("suppresses malformed, archived, stale, and non-preview recommendations without a write", () => {
    const profile = {
        id: 41,
        revision: 7,
        schema_version: "esr-140.13",
        is_deleted: false,
        recommendation,
    };
    const variants = [
        { ...profile, is_deleted: true },
        { ...profile, recommendation: { ...recommendation, profile_revision: 6 } },
        { ...profile, recommendation: { ...recommendation, source: { ...recommendation.source, artifact_id: "esr-115.38" } } },
        { ...profile, recommendation: { ...recommendation, action: { ...recommendation.action, action_id: "conversion-apply" } } },
        { ...profile, recommendation: null },
    ];

    variants.forEach((variant) => assert.equal(resolveLibraryConversionRecommendation(variant), null));
    assert.equal(buildLibraryConversionPreviewHref(profile, null, "https://bpm.example"), null);
});

test("rejects each malformed recommendation boundary before creating a preview link", () => {
    const profile = {
        id: 41,
        revision: 7,
        schema_version: "esr-140.13",
        is_deleted: false,
        recommendation,
    };
    const invalidRecommendations = [
        { ...recommendation, recommendation_id: "unrelated" },
        { ...recommendation, action: { ...recommendation.action, action_id: "conversion-apply" } },
        { ...recommendation, profile_revision: 6 },
        { ...recommendation, source: { ...recommendation.source, artifact_id: "esr-115.38" } },
        { ...recommendation, target: { ...recommendation.target, artifact_id: "" } },
        { ...recommendation, action: { ...recommendation.action, preview_target_artifact_id: "" } },
        {
            ...recommendation,
            action: { ...recommendation.action, preview_target_artifact_id: "esr-115.38" },
        },
    ];

    assert.equal(resolveLibraryConversionRecommendation(null), null);
    invalidRecommendations.forEach((candidate) => {
        assert.equal(resolveLibraryConversionRecommendation({ ...profile, recommendation: candidate }), null);
    });
    assert.equal(buildLibraryConversionPreviewHref({}, recommendation, "https://bpm.example"), null);
    assert.equal(buildLibraryConversionRecommendationMarkup({
        profile,
        recommendation: invalidRecommendations[0],
        sourceSchema: "Firefox ESR 140",
        targetSchema: "Firefox ESR 153",
        origin: "https://bpm.example",
        escapeHtml: String,
    }), "");
    assert.equal(buildLibraryConversionRecommendationMarkup({
        profile,
        recommendation,
        sourceSchema: "Firefox ESR 140",
        targetSchema: "Firefox ESR 153",
        origin: "https://bpm.example",
    }), "");
    assert.equal(buildLibraryConversionRecommendationMarkup({
        profile: { ...profile, id: null },
        recommendation,
        sourceSchema: "Firefox ESR 140",
        targetSchema: "Firefox ESR 153",
        origin: "https://bpm.example",
        escapeHtml: String,
    }), "");
});

test("keeps the recommendation consequence explicitly read-only", () => {
    const copy = recommendationCopy({ sourceSchema: "Firefox ESR 140", targetSchema: "Firefox ESR 153" });

    assert.equal(copy.action, "Review update to Firefox ESR 153");
    assert.match(copy.consequence, /conversion preview/);
    assert.match(copy.consequence, /will not change until you review and confirm/);
    assert.match(copy.accessibleName, /Firefox ESR 140.*Firefox ESR 153/);
});

test("gets Library recommendation copy from the active locale instead of an English fallback", () => {
    const translations = {
        "profiles.schema_conversion_recommendation_action": "Aktualisierung auf {target_schema} prüfen",
        "profiles.schema_conversion_recommendation_consequence": "Öffnet eine Vorschau von {source_schema} nach {target_schema}. Das Profil bleibt bis zur Bestätigung unverändert.",
        "profiles.schema_conversion_recommendation_accessible_name": "Schemavorschau von {source_schema} nach {target_schema} prüfen",
    };
    const copy = recommendationCopy({
        sourceSchema: "Firefox ESR 140",
        targetSchema: "Firefox ESR 153",
        t: (key, fallback) => translations[key] || fallback,
    });

    assert.equal(copy.action, "Aktualisierung auf Firefox ESR 153 prüfen");
    assert.match(copy.consequence, /Firefox ESR 140.*Firefox ESR 153/);
    assert.match(copy.accessibleName, /Schemavorschau/);
});

test("renders one keyboard-native preview entry with its local consequence", () => {
    const profile = {
        id: 41,
        revision: 7,
        schema_version: "esr-140.13",
        is_deleted: false,
        recommendation,
    };
    const markup = buildLibraryConversionRecommendationMarkup({
        profile,
        recommendation,
        sourceSchema: "Firefox ESR 140",
        targetSchema: "Firefox ESR 153",
        origin: "https://bpm.example",
        escapeHtml: (value) => String(value).replaceAll("&", "&amp;"),
    });

    assert.match(markup, /<a/);
    assert.match(markup, /data-schema-conversion-preview-entry/);
    assert.match(markup, /schema_conversion=preview/);
    assert.match(markup, /target_artifact_id=esr-153.0/);
    assert.match(markup, /aria-describedby="library-conversion-recommendation-consequence-41"/);
    assert.match(markup, /aria-label="Review schema conversion preview/);
    assert.match(markup, /Your profile will not change until you review and confirm/);
    assert.doesNotMatch(markup, /conversion-apply|<button/);
});
