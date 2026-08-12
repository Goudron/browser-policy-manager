/**
 * Shared, route-owned Firefox schema conversion review.
 *
 * The conversion plan is deliberately held only in this closure.  The DOM,
 * URLs, and any future telemetry receive aggregate counts, lifecycle
 * artifact IDs, and stable state/reason codes only -- never policy values,
 * policy identifiers, paths, profile metadata, or plan/document digests.
 */

import { RECOMMENDATION_STATE_ID } from "./conversion_recommendation.mjs";

export const CONVERSION_REVIEW_STATES = Object.freeze({
    idle: "schema-conversion.manual-target-selection",
    pending: "schema-conversion.preview-pending",
    available: "schema-conversion.preview-available",
    blocked: "schema-conversion.preview-blocked",
    unavailable: "schema-conversion.preview-unavailable",
    unsaved: "schema-conversion.unsaved-work-decision",
    confirmation: "schema-conversion.confirmation-ready",
    applying: "schema-conversion.apply-in-progress",
    success: "schema-conversion.apply-success",
    stale: "schema-conversion.stale-revision",
    changed: "schema-conversion.plan-or-validation-changed",
    sourceInactive: "schema-conversion.source-not-active",
    targetUnavailable: "schema-conversion.target-unavailable",
    sourceInvalid: "schema-conversion.source-invalid",
    failed: "schema-conversion.apply-failed-retry",
    retirement: "schema-conversion.retirement-operator-boundary",
});

const STALE_CODES = new Set([
    "conversion_revision_stale",
    "conversion_source_identity_stale",
    "conversion_plan_stale",
    "conversion_schema_identity_stale",
    "conversion_recipe_registry_stale",
]);
const PLAN_CHANGED_CODES = new Set([
    "conversion_source_identity_stale",
    "conversion_plan_stale",
    "conversion_schema_identity_stale",
    "conversion_recipe_registry_stale",
]);
const TARGET_CODES = new Set([
    "conversion_target_unsupported",
    "conversion_target_identical",
    "conversion_target_schema_missing",
    "schema_channel_retired",
]);
const SOURCE_CODES = new Set([
    "conversion_source_invalid",
    "conversion_source_schema_missing",
]);
const RETIREMENT_CODES = new Set([
    "schema_channel_retired_requires_migration",
    "retirement_successor_missing",
    "retirement_successor_not_immediate",
    "retirement_successor_family_mismatch",
    "retirement_total_convertibility_unproven",
    "retirement_manifest_stale",
    "retirement_manifest_identity_mismatch",
    "retirement_backup_unverified",
    "retirement_preflight_stale",
    "retirement_transaction_failed",
    "retirement_partial_state_detected",
    "retirement_downgrade_unsupported",
]);

function asText(value) {
    return typeof value === "string" ? value : "";
}

function count(value) {
    return Number.isFinite(Number(value)) ? Math.max(0, Number(value)) : 0;
}

export function supportedConversionTargets(catalog, sourceArtifactId) {
    const options = Array.isArray(catalog?.options) ? catalog.options : [];
    return options.filter((option) => (
        option
        && option.support_state === "supported"
        && option.selectable === true
        && typeof option.artifact_id === "string"
        && option.artifact_id !== sourceArtifactId
    ));
}

export function recommendedConversionTarget(catalog, sourceArtifactId) {
    const options = Array.isArray(catalog?.options) ? catalog.options : [];
    const source = options.find((option) => option?.artifact_id === sourceArtifactId);
    const targetId = asText(source?.recommendation_target);
    return supportedConversionTargets(catalog, sourceArtifactId)
        .find((option) => option.artifact_id === targetId)?.artifact_id || "";
}

export function readConversionReviewQuery(search) {
    const params = new URLSearchParams(search || "");
    if (params.get("schema_conversion") !== "preview") return null;
    const targetArtifactId = asText(params.get("target_artifact_id"));
    if (!targetArtifactId) return null;
    return {
        targetArtifactId,
        recommendationId: asText(params.get("recommendation_id")),
    };
}

export function buildConversionApplyPayload(plan) {
    const source = plan?.source;
    const target = plan?.target;
    const profile = plan?.profile;
    const sourceArtifact = source?.artifact;
    const targetArtifact = target?.artifact;
    const registry = plan?.recipe_registry;
    if (
        !plan?.available
        || plan?.compatibility?.applicable !== true
        || plan?.target_validation?.status !== "valid"
        || !profile?.id
        || !profile?.revision
        || !sourceArtifact?.line_id
        || !sourceArtifact?.artifact_id
        || !targetArtifact?.line_id
        || !targetArtifact?.artifact_id
        || !registry?.registry_version
        || !registry?.registry_digest
        || !plan?.plan_digest
        || !source?.document_digest
        || !source?.compliance_digest
        || !profile?.metadata_digest
        || !sourceArtifact?.validation_schema_sha256
        || !targetArtifact?.validation_schema_sha256
    ) return null;

    return {
        kind: "profile-conversion-apply-request",
        contract_version: 1,
        profile_id: profile.id,
        expected_revision: profile.revision,
        source: {
            line_id: sourceArtifact.line_id,
            artifact_id: sourceArtifact.artifact_id,
        },
        target: {
            line_id: targetArtifact.line_id,
            artifact_id: targetArtifact.artifact_id,
        },
        target_artifact_id: targetArtifact.artifact_id,
        plan_digest: plan.plan_digest,
        source_document_digest: source.document_digest,
        source_compliance_digest: source.compliance_digest,
        source_metadata_digest: profile.metadata_digest,
        source_validation_schema_sha256: sourceArtifact.validation_schema_sha256,
        target_validation_schema_sha256: targetArtifact.validation_schema_sha256,
        recipe_registry_version: registry.registry_version,
        recipe_registry_digest: registry.registry_digest,
    };
}

export function reviewStateForError(error, selectedTargetArtifactId = "") {
    const detail = error?.detail && typeof error.detail === "object" ? error.detail : {};
    const code = asText(detail.code);
    if (code === "conversion_revision_stale") return CONVERSION_REVIEW_STATES.stale;
    if (PLAN_CHANGED_CODES.has(code)) return CONVERSION_REVIEW_STATES.changed;
    if (code === "conversion_profile_not_found" || code === "conversion_source_not_active") {
        return CONVERSION_REVIEW_STATES.sourceInactive;
    }
    if (RETIREMENT_CODES.has(code)) return CONVERSION_REVIEW_STATES.retirement;
    if (SOURCE_CODES.has(code)) return CONVERSION_REVIEW_STATES.sourceInvalid;
    if (TARGET_CODES.has(code)) return CONVERSION_REVIEW_STATES.targetUnavailable;
    if (code === "schema_channel_unknown") {
        return detail?.parameters?.target_artifact_id === selectedTargetArtifactId
            ? CONVERSION_REVIEW_STATES.targetUnavailable
            : CONVERSION_REVIEW_STATES.sourceInvalid;
    }
    if (code === "conversion_plan_blocked") return CONVERSION_REVIEW_STATES.blocked;
    if (code === "conversion_apply_failed") return CONVERSION_REVIEW_STATES.failed;
    return CONVERSION_REVIEW_STATES.unavailable;
}

export function aggregatePlanSummary(plan) {
    const counts = plan?.compatibility?.counts || {};
    const blockerCodes = Array.from(new Set([
        ...(Array.isArray(plan?.blockers) ? plan.blockers : []),
        ...(Array.isArray(plan?.target_validation?.issues) ? plan.target_validation.issues : []),
    ].map((entry) => asText(entry?.code)).filter(Boolean)));
    return {
        unchanged: count(counts.unchanged_byte) + count(counts.unchanged_semantic),
        transformed: count(counts.transformed),
        blocked: count(counts.blocked) + count(counts.blockers),
        warnings: count(counts.warnings),
        validationStatus: asText(plan?.target_validation?.status),
        validationIssues: Array.isArray(plan?.target_validation?.issues)
            ? plan.target_validation.issues.length
            : 0,
        complianceDisposition: asText(plan?.compliance?.disposition),
        complianceCurrent: plan?.compliance?.target_claims_current === true,
        blockerCodes,
    };
}

function stateCopy(state, errorCode = "", { exactSavedStateReloaded = true } = {}) {
    const copies = {
        [CONVERSION_REVIEW_STATES.idle]: [
            "Choose a supported target schema.",
            "Selecting a target requests a read-only preview. Your saved profile will not change.",
        ],
        [CONVERSION_REVIEW_STATES.pending]: [
            "Preparing conversion preview", "Checking the current saved profile without changing it.",
        ],
        [CONVERSION_REVIEW_STATES.available]: [
            "Conversion preview ready", "Review the planned aggregate changes and confirm before converting.",
        ],
        [CONVERSION_REVIEW_STATES.blocked]: [
            "Conversion preview is blocked", "Nothing was converted. Resolve a listed condition or choose another target.",
        ],
        [CONVERSION_REVIEW_STATES.unavailable]: [
            "Conversion preview is unavailable", "Nothing was converted. Retry after the exact schema artifact is available, or choose another target.",
        ],
        [CONVERSION_REVIEW_STATES.unsaved]: [
            "Unsaved editor work", "Save before previewing, discard the browser-local changes, or cancel. No preview or conversion will run first.",
        ],
        [CONVERSION_REVIEW_STATES.confirmation]: [
            "Confirm schema conversion", "The saved profile changes only after you explicitly confirm this exact preview.",
        ],
        [CONVERSION_REVIEW_STATES.applying]: [
            "Converting profile", "Waiting for the server's atomic result. Do not close this review or submit again.",
        ],
        [CONVERSION_REVIEW_STATES.success]: exactSavedStateReloaded
            ? ["Profile conversion saved", "The exact saved profile state has been reloaded. Return when you are ready."]
            : ["Profile conversion saved", "The server saved the conversion, but this page could not reload its exact saved state. Reload the profile before continuing."],
        [CONVERSION_REVIEW_STATES.stale]: [
            "Profile changed since this preview", "Nothing was converted. Reload the saved profile and create a fresh preview.",
        ],
        [CONVERSION_REVIEW_STATES.changed]: [
            "Conversion plan changed", "Nothing was converted. Create and review a fresh preview before confirming again.",
        ],
        [CONVERSION_REVIEW_STATES.sourceInactive]: [
            "Conversion requires an active profile", "No profile changes were made. Restore the profile first or return to the Library.",
        ],
        [CONVERSION_REVIEW_STATES.targetUnavailable]: [
            "Target schema unavailable", "No profile changes were made. Choose a supported target and create a new preview.",
        ],
        [CONVERSION_REVIEW_STATES.sourceInvalid]: [
            "Source profile cannot be converted", "No profile changes were made. Resolve the source validation or schema recovery condition first.",
        ],
        [CONVERSION_REVIEW_STATES.failed]: [
            "Conversion was not saved", "The conversion failed and no profile changes were committed. Reload and create a fresh preview before retrying.",
        ],
        [CONVERSION_REVIEW_STATES.retirement]: [
            "Database upgrade required for retired ESR profiles", "Profile conversion is unavailable here. An administrator must complete the verified backup, preflight, and database upgrade.",
        ],
    };
    const [title, consequence] = copies[state];
    return { title, consequence, errorCode };
}

const STATE_COPY_KEYS = Object.freeze({
    [CONVERSION_REVIEW_STATES.idle]: [
        "profiles.schema_conversion_target_label",
        "profiles.schema_conversion_target_consequence",
    ],
    [CONVERSION_REVIEW_STATES.pending]: [
        "profiles.schema_conversion_preview_pending",
        "profiles.schema_conversion_preview_pending_consequence",
    ],
    [CONVERSION_REVIEW_STATES.available]: [
        "profiles.schema_conversion_preview_available",
        "profiles.schema_conversion_preview_available_consequence",
    ],
    [CONVERSION_REVIEW_STATES.blocked]: [
        "profiles.schema_conversion_preview_blocked",
        "profiles.schema_conversion_preview_blocked_consequence",
    ],
    [CONVERSION_REVIEW_STATES.unavailable]: [
        "profiles.schema_conversion_preview_unavailable",
        "profiles.schema_conversion_preview_unavailable_consequence",
    ],
    [CONVERSION_REVIEW_STATES.unsaved]: [
        "profiles.schema_conversion_unsaved_title",
        "profiles.schema_conversion_unsaved_consequence",
    ],
    [CONVERSION_REVIEW_STATES.confirmation]: [
        "profiles.schema_conversion_apply_action",
        "profiles.schema_conversion_apply_consequence",
    ],
    [CONVERSION_REVIEW_STATES.applying]: [
        "profiles.schema_conversion_apply_in_progress",
        "profiles.schema_conversion_apply_in_progress_consequence",
    ],
    [CONVERSION_REVIEW_STATES.success]: [
        "profiles.schema_conversion_success",
        "profiles.schema_conversion_success_consequence",
    ],
    [CONVERSION_REVIEW_STATES.stale]: [
        "profiles.schema_conversion_revision_stale",
        "profiles.schema_conversion_revision_stale_consequence",
    ],
    [CONVERSION_REVIEW_STATES.changed]: [
        "profiles.schema_conversion_plan_changed",
        "profiles.schema_conversion_plan_changed_consequence",
    ],
    [CONVERSION_REVIEW_STATES.sourceInactive]: [
        "profiles.schema_conversion_source_not_active",
        "profiles.schema_conversion_source_not_active_consequence",
    ],
    [CONVERSION_REVIEW_STATES.targetUnavailable]: [
        "profiles.schema_conversion_target_unavailable",
        "profiles.schema_conversion_target_unavailable_consequence",
    ],
    [CONVERSION_REVIEW_STATES.sourceInvalid]: [
        "profiles.schema_conversion_source_invalid",
        "profiles.schema_conversion_source_invalid_consequence",
    ],
    [CONVERSION_REVIEW_STATES.failed]: [
        "profiles.schema_conversion_apply_failed",
        "profiles.schema_conversion_apply_failed_consequence",
    ],
    [CONVERSION_REVIEW_STATES.retirement]: [
        "profiles.schema_retirement_upgrade_required",
        "profiles.schema_retirement_upgrade_required_consequence",
    ],
});

function localizedStateCopy(state, translate, replacements, options) {
    const fallback = stateCopy(state, "", options);
    const [titleKey, consequenceKey] = STATE_COPY_KEYS[state];
    return {
        title: translate(titleKey, fallback.title, replacements),
        consequence: translate(consequenceKey, fallback.consequence, replacements),
    };
}

function isTerminalAlert(state) {
    return new Set([
        CONVERSION_REVIEW_STATES.blocked,
        CONVERSION_REVIEW_STATES.unavailable,
        CONVERSION_REVIEW_STATES.stale,
        CONVERSION_REVIEW_STATES.changed,
        CONVERSION_REVIEW_STATES.sourceInactive,
        CONVERSION_REVIEW_STATES.targetUnavailable,
        CONVERSION_REVIEW_STATES.sourceInvalid,
        CONVERSION_REVIEW_STATES.failed,
        CONVERSION_REVIEW_STATES.retirement,
    ]).has(state);
}

export function create({
    documentRef = document,
    windowRef = window,
    schemaChannelsCatalog = {},
    dependencies = {},
    state = {},
} = {}) {
    const {
        t = (_key, fallback = "") => fallback,
        formatSchemaLabel = (value) => value,
        previewProfileConversion = async () => { throw new Error("Conversion preview is unavailable"); },
        applyProfileConversion = async () => { throw new Error("Conversion apply is unavailable"); },
        loadProfile = async () => {},
        saveCurrent = async () => false,
        currentSnapshotState = () => ({ dirty: false, invalid: false }),
    } = dependencies;
    const getCurrentProfile = state.getCurrentProfile || (() => null);
    const host = documentRef.getElementById("schema-conversion-review");
    const opener = documentRef.getElementById("schema-conversion-review-open");
    let selectedTargetArtifactId = "";
    let activePlan = null;
    let currentState = CONVERSION_REVIEW_STATES.idle;
    let pending = false;
    let openerEl = null;
    let autoPreviewScheduled = false;
    let exactSavedStateReloaded = true;
    let savedResultRevision = "";

    function translate(key, fallback, replacements = {}) {
        let value = t(key, fallback) || fallback;
        Object.entries(replacements).forEach(([name, replacement]) => {
            value = value.replace(`{${name}}`, String(replacement));
        });
        return value;
    }

    function profileIsActive(profile) {
        return Boolean(profile?.id) && profile?.is_deleted !== true;
    }

    function targetsForCurrentProfile() {
        return supportedConversionTargets(schemaChannelsCatalog, getCurrentProfile()?.schema_version);
    }

    function hasTarget(targetArtifactId) {
        return targetsForCurrentProfile().some((option) => option.artifact_id === targetArtifactId);
    }

    function focusReviewHeading() {
        const heading = host?.querySelector("#schema-conversion-review-title");
        if (!heading || typeof heading.focus !== "function") return;
        heading.setAttribute("tabindex", "-1");
        heading.focus({ preventScroll: true });
    }

    function focusTerminalSummary() {
        const summary = host?.querySelector("[data-schema-conversion-terminal]");
        if (!summary || typeof summary.focus !== "function") return;
        summary.setAttribute("tabindex", "-1");
        summary.focus({ preventScroll: true });
    }

    function clearPlan() {
        activePlan = null;
    }

    function reviewTargetLabel(artifactId) {
        return formatSchemaLabel(artifactId) || artifactId;
    }

    function render() {
        if (!host) return;
        const profile = getCurrentProfile();
        const targets = targetsForCurrentProfile();
        const sourceLabel = reviewTargetLabel(profile?.schema_version || "");
        const targetLabel = reviewTargetLabel(selectedTargetArtifactId);
        const summary = aggregatePlanSummary(activePlan);
        const copy = localizedStateCopy(currentState, translate, {
            source_schema: sourceLabel,
            target_schema: targetLabel,
            blocker_count: summary.blockerCodes.length,
            result_revision: savedResultRevision,
        }, { exactSavedStateReloaded });
        const isApplicable = activePlan?.compatibility?.applicable === true
            && activePlan?.target_validation?.status === "valid"
            && activePlan?.blockers?.length === 0;
        const canConfirm = currentState === CONVERSION_REVIEW_STATES.available && isApplicable;
        const confirmationVisible = currentState === CONVERSION_REVIEW_STATES.confirmation;
        const applying = currentState === CONVERSION_REVIEW_STATES.applying;
        const terminalAlert = isTerminalAlert(currentState);
        const detailsVisible = Boolean(activePlan);
        const targetOptions = targets.map((option) => {
            const selected = option.artifact_id === selectedTargetArtifactId ? " selected" : "";
            return `<option value="${option.artifact_id}"${selected}>${reviewTargetLabel(option.artifact_id)}</option>`;
        }).join("");
        const blockerMarkup = summary.blockerCodes.length
            ? `<ul class="schema-conversion-review-list" data-schema-conversion-blockers>${summary.blockerCodes
                .map((code) => `<li>${translate("profiles.schema_conversion_blocker_code", "Blocked condition: {code}", { code })}</li>`)
                .join("")}</ul>`
            : "";
        const unavailableTarget = selectedTargetArtifactId && !hasTarget(selectedTargetArtifactId);
        const statusRole = terminalAlert ? "alert" : "status";

        host.hidden = false;
        host.dataset.schemaConversionState = currentState;
        host.setAttribute("aria-busy", pending || applying ? "true" : "false");
        host.innerHTML = `
            <div class="schema-conversion-review-heading">
                <div>
                    <div class="section-kicker" data-i18n="profiles.schema_conversion_kicker">${translate("profiles.schema_conversion_kicker", "Profile schema")}</div>
                    <h2 id="schema-conversion-review-title" class="editor-chrome-title" data-i18n="profiles.schema_conversion_review_title">${translate("profiles.schema_conversion_review_title", "Review schema conversion")}</h2>
                </div>
                <button type="button" class="button-base ghost-button" data-schema-conversion-cancel${applying ? " disabled" : ""}>${translate("profiles.schema_conversion_cancel", "Cancel")}</button>
            </div>
            <div class="schema-conversion-review-summary">
                <div><span>${translate("profiles.schema_conversion_source", "Source schema")}</span><strong data-schema-conversion-source>${sourceLabel}</strong></div>
                <div><span>${translate("profiles.schema_conversion_target", "Target schema")}</span><strong data-schema-conversion-target>${targetLabel || translate("profiles.schema_conversion_target_choose", "Choose a target")}</strong></div>
            </div>
            <label class="field-label" for="schema-conversion-target-select">${translate("profiles.schema_conversion_target_select", "Target schema")}
                <select id="schema-conversion-target-select" data-schema-conversion-target-select class="soft-input" aria-label="${translate("profiles.schema_conversion_target_accessible_name", "Choose target schema for conversion")}" aria-describedby="schema-conversion-target-consequence"${applying ? " disabled" : ""}>
                    <option value="">${translate("profiles.schema_conversion_target_choose", "Choose a target")}</option>
                    ${targetOptions}
                </select>
            </label>
            <p id="schema-conversion-target-consequence" class="wizard-input-hint">${translate("profiles.schema_conversion_target_consequence", "Selecting a target requests a read-only preview. It does not change the saved profile.")}</p>
            ${unavailableTarget ? `<div class="schema-conversion-review-status" role="alert" data-schema-conversion-terminal>${localizedStateCopy(CONVERSION_REVIEW_STATES.targetUnavailable, translate, {}, {}).consequence}</div>` : ""}
            <div class="schema-conversion-review-status" role="${statusRole}" aria-live="${terminalAlert ? "assertive" : "polite"}"${terminalAlert ? " data-schema-conversion-terminal" : ""}>
                <strong>${copy.title}</strong>
                <span>${copy.consequence}</span>
            </div>
            ${detailsVisible ? `
                <div class="schema-conversion-review-details" data-schema-conversion-plan-summary>
                    <h3>${translate("profiles.schema_conversion_plan_summary", "Planned changes")}</h3>
                    <ul class="schema-conversion-review-list">
                        <li>${translate("profiles.schema_conversion_unchanged_count", "Unchanged settings: {count}", { count: summary.unchanged })}</li>
                        <li>${translate("profiles.schema_conversion_transformed_count", "Transformed settings: {count}", { count: summary.transformed })}</li>
                        <li>${translate("profiles.schema_conversion_blocked_count", "Blocked settings: {count}", { count: summary.blocked })}</li>
                        <li>${translate("profiles.schema_conversion_warning_count", "Warnings: {count}", { count: summary.warnings })}</li>
                    </ul>
                    <h3>${translate("profiles.schema_conversion_validation", "Validation and compliance")}</h3>
                    <ul class="schema-conversion-review-list">
                        <li>${translate("profiles.schema_conversion_validation_status", "Target validation: {status} ({count} issues)", { status: summary.validationStatus || "not run", count: summary.validationIssues })}</li>
                        <li>${translate("profiles.schema_conversion_compliance_status", "Compliance outcome: {disposition}", { disposition: summary.complianceDisposition || "not available" })}</li>
                    </ul>
                    ${blockerMarkup}
                </div>
            ` : ""}
            ${currentState === CONVERSION_REVIEW_STATES.unsaved ? `
                <div class="schema-conversion-review-actions" data-schema-conversion-unsaved-actions>
                    <button type="button" class="button-base primary-button" data-schema-conversion-save-preview>${translate("profiles.schema_conversion_save_and_preview", "Save and preview")}</button>
                    <button type="button" class="button-base ghost-button" data-schema-conversion-discard-preview>${translate("profiles.schema_conversion_discard_and_preview", "Discard and preview")}</button>
                </div>
            ` : ""}
            ${canConfirm ? `
                <div class="schema-conversion-review-actions">
                    <button type="button" class="button-base primary-button" data-schema-conversion-confirm>${translate("profiles.schema_conversion_continue_to_confirmation", "Continue to confirmation")}</button>
                </div>
            ` : ""}
            ${confirmationVisible ? `
                <div class="schema-conversion-review-confirmation" data-schema-conversion-confirmation>
                    <label><input type="checkbox" data-schema-conversion-confirm-check /> ${translate("profiles.schema_conversion_confirm_acknowledgement", "I reviewed this exact preview and want to convert the saved profile.")}</label>
                    <p id="schema-conversion-confirmation-consequence" class="wizard-input-hint">${translate("profiles.schema_conversion_confirm_consequence", "Conversion updates the schema, policy document, compliance result, and revision. It cannot run without this confirmation.")}</p>
                    <button type="button" class="button-base primary-button" data-schema-conversion-apply disabled aria-label="${translate("profiles.schema_conversion_apply_accessible_name", "Confirm conversion to {target_schema}", { target_schema: targetLabel })}" aria-describedby="schema-conversion-confirmation-consequence">${translate("profiles.schema_conversion_apply", "Convert profile")}</button>
                </div>
            ` : ""}
            ${(currentState === CONVERSION_REVIEW_STATES.stale || currentState === CONVERSION_REVIEW_STATES.changed || currentState === CONVERSION_REVIEW_STATES.failed) ? `
                <div class="schema-conversion-review-actions"><button type="button" class="button-base primary-button" data-schema-conversion-refresh>${translate("profiles.schema_conversion_fresh_preview", "Create fresh preview")}</button></div>
            ` : ""}
            ${currentState === CONVERSION_REVIEW_STATES.success ? `
                <div class="schema-conversion-review-actions"><button type="button" class="button-base primary-button" data-schema-conversion-return>${exactSavedStateReloaded
                    ? translate("profiles.schema_conversion_return", "Return to profile")
                    : translate("profiles.schema_conversion_reload", "Reload profile")}</button></div>
            ` : ""}
        `;

        host.querySelector("[data-schema-conversion-target-select]")?.addEventListener("change", async (event) => {
            const nextTarget = asText(event.currentTarget.value);
            await selectTarget(nextTarget, { requireUnsavedDecision: true });
        });
        host.querySelector("[data-schema-conversion-cancel]")?.addEventListener("click", cancel);
        host.querySelector("[data-schema-conversion-return]")?.addEventListener("click", () => {
            if (currentState === CONVERSION_REVIEW_STATES.success && !exactSavedStateReloaded) {
                windowRef.location.reload();
                return;
            }
            cancel();
        });
        host.querySelector("[data-schema-conversion-save-preview]")?.addEventListener("click", saveAndPreview);
        host.querySelector("[data-schema-conversion-discard-preview]")?.addEventListener("click", discardAndPreview);
        host.querySelector("[data-schema-conversion-confirm]")?.addEventListener("click", showConfirmation);
        host.querySelector("[data-schema-conversion-confirm-check]")?.addEventListener("change", (event) => {
            const applyButton = host.querySelector("[data-schema-conversion-apply]");
            if (applyButton) applyButton.disabled = !event.currentTarget.checked;
        });
        host.querySelector("[data-schema-conversion-apply]")?.addEventListener("click", apply);
        host.querySelector("[data-schema-conversion-refresh]")?.addEventListener("click", () => requestPreview());
    }

    function cancel() {
        if (pending || currentState === CONVERSION_REVIEW_STATES.applying) return;
        clearPlan();
        if (host) host.hidden = true;
        openerEl?.focus?.();
    }

    function setState(nextState) {
        currentState = nextState;
        render();
        if (isTerminalAlert(nextState)) {
            windowRef.requestAnimationFrame?.(focusTerminalSummary);
        }
    }

    async function ensureSafeToPreview() {
        const snapshot = currentSnapshotState() || {};
        if (snapshot.invalid) {
            setState(CONVERSION_REVIEW_STATES.sourceInvalid);
            return false;
        }
        if (!snapshot.dirty) return true;
        setState(CONVERSION_REVIEW_STATES.unsaved);
        return false;
    }

    async function selectTarget(nextTarget, { requireUnsavedDecision = true } = {}) {
        selectedTargetArtifactId = nextTarget;
        clearPlan();
        if (!nextTarget) {
            setState(CONVERSION_REVIEW_STATES.idle);
            return;
        }
        if (!hasTarget(nextTarget)) {
            setState(CONVERSION_REVIEW_STATES.targetUnavailable);
            return;
        }
        if (requireUnsavedDecision && !(await ensureSafeToPreview())) return;
        await requestPreview();
    }

    function buildDiscardPreviewHref() {
        const url = new URL(windowRef.location.href);
        url.searchParams.set("schema_conversion", "preview");
        url.searchParams.set("target_artifact_id", selectedTargetArtifactId);
        return `${url.pathname}${url.search}${url.hash}`;
    }

    async function saveAndPreview() {
        if (pending) return;
        const saved = await saveCurrent();
        if (!saved) {
            setState(CONVERSION_REVIEW_STATES.unsaved);
            return;
        }
        await requestPreview();
    }

    function discardAndPreview() {
        if (pending || !selectedTargetArtifactId) return;
        windowRef.location.assign(buildDiscardPreviewHref());
    }

    async function requestPreview() {
        const profile = getCurrentProfile();
        if (!profileIsActive(profile)) {
            setState(CONVERSION_REVIEW_STATES.sourceInactive);
            return;
        }
        if (!selectedTargetArtifactId || !hasTarget(selectedTargetArtifactId)) {
            setState(selectedTargetArtifactId
                ? CONVERSION_REVIEW_STATES.targetUnavailable
                : CONVERSION_REVIEW_STATES.idle);
            return;
        }
        pending = true;
        setState(CONVERSION_REVIEW_STATES.pending);
        try {
            const plan = await previewProfileConversion(profile.id, selectedTargetArtifactId);
            if (plan?.profile?.id !== profile.id || plan?.target?.artifact?.artifact_id !== selectedTargetArtifactId) {
                throw new Error("Conversion preview identity did not match the selected profile and target");
            }
            activePlan = plan;
            const summary = aggregatePlanSummary(plan);
            setState(
                plan.compatibility?.applicable === true
                && plan.target_validation?.status === "valid"
                && summary.blockerCodes.length === 0
                    ? CONVERSION_REVIEW_STATES.available
                    : CONVERSION_REVIEW_STATES.blocked,
            );
        } catch (error) {
            clearPlan();
            setState(reviewStateForError(error, selectedTargetArtifactId));
        } finally {
            pending = false;
            render();
        }
    }

    function showConfirmation() {
        if (!buildConversionApplyPayload(activePlan)) {
            clearPlan();
            setState(CONVERSION_REVIEW_STATES.changed);
            return;
        }
        setState(CONVERSION_REVIEW_STATES.confirmation);
    }

    async function apply() {
        if (pending || currentState !== CONVERSION_REVIEW_STATES.confirmation) return;
        const applyPayload = buildConversionApplyPayload(activePlan);
        const profile = getCurrentProfile();
        if (!applyPayload || !profileIsActive(profile) || applyPayload.profile_id !== profile.id) {
            clearPlan();
            setState(CONVERSION_REVIEW_STATES.changed);
            return;
        }
        pending = true;
        setState(CONVERSION_REVIEW_STATES.applying);
        try {
            const result = await applyProfileConversion(profile.id, applyPayload);
            if (
                result?.status !== "applied"
                || result?.profile_id !== profile.id
                || result?.result_revision !== applyPayload.expected_revision + 1
                || result?.target?.artifact_id !== selectedTargetArtifactId
            ) {
                throw new Error("Conversion apply result did not match the reviewed plan");
            }
            savedResultRevision = result.result_revision;
            const reloaded = await loadProfile(profile.id, {
                skipConfirm: true,
                syncLibrary: false,
                announceLoaded: false,
            });
            exactSavedStateReloaded = reloaded?.id === result.profile_id
                && reloaded?.revision === result.result_revision
                && reloaded?.schema_version === result.target.artifact_id;
            clearPlan();
            setState(CONVERSION_REVIEW_STATES.success);
        } catch (error) {
            clearPlan();
            setState(reviewStateForError(error, selectedTargetArtifactId));
        } finally {
            pending = false;
            render();
        }
    }

    function open({ targetArtifactId = "", recommendationId = "", autoPreview = false } = {}) {
        const profile = getCurrentProfile();
        if (!profileIsActive(profile)) {
            selectedTargetArtifactId = "";
            setState(CONVERSION_REVIEW_STATES.sourceInactive);
            return;
        }
        openerEl = documentRef.activeElement === opener ? opener : openerEl || opener;
        const requestedTarget = asText(targetArtifactId);
        const catalogTarget = recommendedConversionTarget(schemaChannelsCatalog, profile.schema_version);
        selectedTargetArtifactId = hasTarget(requestedTarget)
            ? requestedTarget
            : (hasTarget(catalogTarget) ? catalogTarget : "");
        exactSavedStateReloaded = true;
        savedResultRevision = "";
        clearPlan();
        setState(selectedTargetArtifactId ? CONVERSION_REVIEW_STATES.idle : CONVERSION_REVIEW_STATES.targetUnavailable);
        windowRef.requestAnimationFrame?.(focusReviewHeading);
        if (!selectedTargetArtifactId) return;
        if (autoPreview || recommendationId === RECOMMENDATION_STATE_ID) {
            selectTarget(selectedTargetArtifactId, { requireUnsavedDecision: true });
        }
    }

    function consumePreviewQuery() {
        const query = readConversionReviewQuery(windowRef.location.search);
        if (!query || autoPreviewScheduled) return;
        autoPreviewScheduled = true;
        const consume = (attemptsLeft = 30) => {
            const snapshot = currentSnapshotState() || {};
            // Runtime construction starts the shared review while the editor
            // workspace is still loading.  An invalid snapshot at this point
            // is not a source-validation result and must not turn a Library
            // handoff into a terminal source-invalid state before its preview
            // request has even been made.
            if (profileIsActive(getCurrentProfile()) && snapshot.invalid !== true) {
                open({ ...query, autoPreview: true });
                const cleanUrl = new URL(windowRef.location.href);
                cleanUrl.searchParams.delete("schema_conversion");
                cleanUrl.searchParams.delete("target_artifact_id");
                cleanUrl.searchParams.delete("recommendation_id");
                windowRef.history?.replaceState?.({}, "", `${cleanUrl.pathname}${cleanUrl.search}${cleanUrl.hash}`);
                return;
            }
            if (attemptsLeft > 0) windowRef.setTimeout(() => consume(attemptsLeft - 1), 100);
        };
        consume();
    }

    function start() {
        if (!host) return;
        opener?.addEventListener("click", () => open());
        consumePreviewQuery();
    }

    return {
        start,
        open,
        requestPreview,
        selectTarget,
        cancel,
        showConfirmation,
        apply,
        getState: () => currentState,
    };
}
