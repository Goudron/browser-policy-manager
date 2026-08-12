/** Read-only Library entry contract for a catalog-derived conversion recommendation. */

export const RECOMMENDATION_STATE_ID = "schema-conversion.older-esr-recommendation";
export const RECOMMENDATION_ACTION_ID = "conversion-preview";

export function resolveLibraryConversionRecommendation(profile) {
    const recommendation = profile?.recommendation;
    if (!profile || !recommendation || profile.is_deleted) return null;
    if (recommendation.recommendation_id !== RECOMMENDATION_STATE_ID) return null;
    if (recommendation.action?.action_id !== RECOMMENDATION_ACTION_ID) return null;
    if (recommendation.profile_revision !== profile.revision) return null;
    if (recommendation.source?.artifact_id !== profile.schema_version) return null;
    if (!recommendation.target?.artifact_id || !recommendation.action?.preview_target_artifact_id) return null;
    if (recommendation.target.artifact_id !== recommendation.action.preview_target_artifact_id) return null;
    return recommendation;
}

export function buildLibraryConversionPreviewHref(profile, recommendation, origin) {
    if (!profile?.id || !recommendation) return null;
    const url = new URL(`/profiles/${profile.id}/edit`, origin);
    url.searchParams.set("schema_conversion", "preview");
    url.searchParams.set("target_artifact_id", recommendation.action.preview_target_artifact_id);
    url.searchParams.set("recommendation_id", recommendation.recommendation_id);
    return `${url.pathname}${url.search}`;
}

export function recommendationCopy({ sourceSchema, targetSchema, t = (_key, fallback) => fallback }) {
    const translate = (key, fallback) => t(key, fallback)
        .replace("{source_schema}", sourceSchema)
        .replace("{target_schema}", targetSchema);
    return {
        action: translate(
            "profiles.schema_conversion_recommendation_action",
            "Review update to {target_schema}",
        ),
        consequence: translate(
            "profiles.schema_conversion_recommendation_consequence",
            "This opens a conversion preview from {source_schema} to {target_schema}. Your profile will not change until you review and confirm.",
        ),
        accessibleName: translate(
            "profiles.schema_conversion_recommendation_accessible_name",
            "Review schema conversion preview from {source_schema} to {target_schema}",
        ),
    };
}

export function buildLibraryConversionRecommendationMarkup({
    profile,
    recommendation,
    sourceSchema,
    targetSchema,
    origin,
    escapeHtml,
    t,
}) {
    if (resolveLibraryConversionRecommendation(profile) !== recommendation) return "";
    if (typeof escapeHtml !== "function") return "";
    const href = buildLibraryConversionPreviewHref(profile, recommendation, origin);
    if (!href) return "";
    const copy = recommendationCopy({ sourceSchema, targetSchema, t });
    const consequenceId = `library-conversion-recommendation-consequence-${profile.id}`;
    return `
        <div
            class="library-conversion-recommendation"
            data-schema-conversion-state="${recommendation.recommendation_id}"
            data-schema-conversion-source-line="${escapeHtml(recommendation.source.line_id)}"
            data-schema-conversion-target-line="${escapeHtml(recommendation.target.line_id)}">
            <a
                class="library-conversion-recommendation-action"
                href="${escapeHtml(href)}"
                data-schema-conversion-preview-entry
                data-schema-conversion-profile-id="${profile.id}"
                data-schema-conversion-target-artifact-id="${escapeHtml(recommendation.action.preview_target_artifact_id)}"
                aria-describedby="${consequenceId}"
                aria-label="${escapeHtml(copy.accessibleName)}">
                ${escapeHtml(copy.action)}
            </a>
            <p
                id="${consequenceId}"
                class="library-conversion-recommendation-consequence">
                ${escapeHtml(copy.consequence)}
            </p>
        </div>
    `;
}
