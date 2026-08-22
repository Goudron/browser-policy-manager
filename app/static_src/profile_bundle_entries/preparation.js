const PREPARE_NEW_PROFILE_PATH = "/api/profiles/prepare/new";
const PREVIEW_DUPLICATE_PROFILE_PATH = "/api/profiles/prepare/duplicate/preview";
const PREPARE_DUPLICATE_PROFILE_PATH = "/api/profiles/prepare/duplicate";
const IDEMPOTENCY_STORAGE_PREFIX = "bpm096:prepare:";

const form = typeof document === "undefined" ? null : document.getElementById("profile-preparation-form");

if (typeof HTMLFormElement !== "undefined" && form instanceof HTMLFormElement) {
    const state = document.getElementById("profile-preparation-state");
    const action = document.getElementById("profile-preparation-submit");
    const actionError = document.getElementById("profile-preparation-action-error");
    const controls = Array.from(form.querySelectorAll("input, select"));
    const cisControl = document.getElementById("profile-preparation-cis");
    const schemaControl = document.getElementById("profile-preparation-schema");
    const nameControl = document.getElementById("profile-preparation-name");
    const starterControl = document.getElementById("profile-preparation-starter");
    const preparationMode = document.body.dataset.preparationMode;
    const sourceId = Number(document.body.dataset.preparationSourceId);
    const sourceRevision = Number(document.body.dataset.preparationSourceRevision);
    const storageKey = `${IDEMPOTENCY_STORAGE_PREFIX}${location.pathname}${location.search}`;
    let submitting = false;
    let idempotencyKey = sessionStorage.getItem(storageKey);
    let duplicatePlanIsValid = preparationMode !== "duplicate";
    let duplicatePlanRequest = 0;

    function errorElement(control) {
        const identifier = control.getAttribute("aria-errormessage");
        return identifier ? document.getElementById(identifier) : null;
    }

    function setControlError(control, message = "") {
        const error = errorElement(control);
        control.setCustomValidity(message);
        control.toggleAttribute("aria-invalid", Boolean(message));
        if (error) {
            error.textContent = message;
            error.hidden = !message;
        }
    }

    function validateControl(control) {
        const value = control instanceof HTMLInputElement ? control.value.trim() : control.value;
        const selectedOption = control instanceof HTMLSelectElement ? control.selectedOptions[0] : null;
        const message = !value
            ? control.dataset.requiredMessage || ""
            : selectedOption?.disabled
                ? control.dataset.unavailableMessage || ""
                : "";
        setControlError(control, message);
        return !message;
    }

    function updateCisAvailability() {
        if (!(cisControl instanceof HTMLSelectElement) || !(schemaControl instanceof HTMLSelectElement)) {
            return;
        }
        for (const option of cisControl.options) {
            if (!option.value) continue;
            const availableSchemas = option.dataset.availableSchemaVersions?.split(",") || [];
            option.disabled = availableSchemas.length > 0 && !availableSchemas.includes(schemaControl.value);
        }
        if (cisControl.selectedOptions[0]?.disabled) {
            setControlError(cisControl, cisControl.dataset.unavailableMessage || "");
        } else {
            validateControl(cisControl);
        }
    }

    function clearActionError() {
        if (actionError) {
            actionError.textContent = "";
            actionError.hidden = true;
        }
        action?.removeAttribute("aria-invalid");
    }

    function showTerminalBlocker(message = action?.dataset.blockerMessage || "", options = {}) {
        const { disabled = false, focus = true } = options;
        if (actionError) {
            actionError.textContent = message;
            actionError.hidden = !message;
        }
        if (state) state.textContent = message;
        form.dataset.preparationFormState = "rejected";
        action?.setAttribute("aria-invalid", "true");
        if (action instanceof HTMLButtonElement && disabled) action.disabled = true;
        if (focus && !action?.disabled) action?.focus();
    }

    function rejectForCode(code, options = {}) {
        const { disabled = false } = options;
        form.dataset.preparationFormState = "rejected";
        if (state) state.textContent = "";
        const fieldFailure = {
            preparation_name_conflict: [nameControl, "conflictMessage"],
            preparation_schema_unavailable: [schemaControl, "unavailableMessage"],
            preparation_starter_unavailable: [starterControl, "unavailableMessage"],
            preparation_cis_unavailable: [cisControl, "unavailableMessage"],
        }[code];
        if (fieldFailure?.[0] instanceof HTMLElement) {
            const [control, messageKey] = fieldFailure;
            setControlError(control, control.dataset[messageKey] || "");
            control.focus();
            return;
        }
        if (
            code === "preparation_source_stale"
            || code === "preparation_duplicate_source_not_found"
            || code === "preparation_duplicate_source_not_eligible"
        ) {
            showTerminalBlocker(action?.dataset.sourceStaleMessage || "", { disabled, focus: !disabled });
            return;
        }
        if (code === "preparation_idempotency_key_reused") {
            showTerminalBlocker(action?.dataset.idempotencyReusedMessage || "", { disabled, focus: !disabled });
            return;
        }
        showTerminalBlocker(action?.dataset.blockerMessage || "", { disabled, focus: !disabled });
    }

    function setSubmitting(active) {
        submitting = active;
        form.dataset.preparationFormState = active ? "submitting" : "rejected";
        form.setAttribute("aria-busy", String(active));
        for (const control of controls) control.disabled = active;
        if (action instanceof HTMLButtonElement) action.disabled = active;
        if (active && state) state.textContent = action?.dataset.submittingMessage || "";
    }

    function finishRejected(code) {
        if (submitting) setSubmitting(false);
        const terminalDuplicateFailure = (
            code !== "preparation_name_conflict" && !code.endsWith("_unavailable")
        );
        rejectForCode(code, {
            disabled: preparationMode === "duplicate" && terminalDuplicateFailure,
        });
    }

    function currentIdempotencyKey() {
        if (!idempotencyKey) {
            idempotencyKey = globalThis.crypto?.randomUUID?.() || null;
            if (idempotencyKey) sessionStorage.setItem(storageKey, idempotencyKey);
        }
        return idempotencyKey;
    }

    function newProfilePayload() {
        if (
            !(nameControl instanceof HTMLInputElement)
            || !(schemaControl instanceof HTMLSelectElement)
            || !(starterControl instanceof HTMLSelectElement)
            || !(cisControl instanceof HTMLSelectElement)
        ) {
            return null;
        }
        const key = currentIdempotencyKey();
        if (!key) return null;
        return {
            name: nameControl.value.trim(),
            target_schema_id: schemaControl.value,
            starter_id: starterControl.value,
            cis_baseline_id: cisControl.value,
            preparation_idempotency_key: key,
        };
    }

    function duplicatePayload(includeIdempotencyKey = false) {
        if (
            !Number.isInteger(sourceId)
            || sourceId <= 0
            || !Number.isInteger(sourceRevision)
            || sourceRevision <= 0
            || !(schemaControl instanceof HTMLSelectElement)
            || !(starterControl instanceof HTMLSelectElement)
            || !(cisControl instanceof HTMLSelectElement)
        ) {
            return null;
        }
        const payload = {
            target_schema_id: schemaControl.value,
            starter_id: starterControl.value,
            cis_baseline_id: cisControl.value,
            source_id: sourceId,
            expected_source_revision: sourceRevision,
        };
        if (!includeIdempotencyKey) return payload;
        const key = currentIdempotencyKey();
        return key && nameControl instanceof HTMLInputElement
            ? { ...payload, name: nameControl.value.trim(), preparation_idempotency_key: key }
            : null;
    }

    function duplicatePreviewFailureCode(reasonCode) {
        const fieldFailures = {
            duplicate_target_schema_unavailable: "preparation_schema_unavailable",
            duplicate_preset_unavailable: "preparation_starter_unavailable",
            duplicate_cis_unavailable: "preparation_cis_unavailable",
        };
        if (fieldFailures[reasonCode]) return fieldFailures[reasonCode];
        if (reasonCode?.startsWith("duplicate_source_")) return "preparation_source_stale";
        if (reasonCode?.startsWith("duplicate_conversion_")) return "preparation_conversion_blocked";
        return "preparation_composition_blocked";
    }

    function setDuplicatePlanBusy(active) {
        form.ariaBusy = active;
        if (action instanceof HTMLButtonElement) action.disabled = active || !duplicatePlanIsValid;
    }

    async function refreshDuplicatePlan() {
        if (preparationMode !== "duplicate" || submitting) return;

        const payload = duplicatePayload();
        const controlsValid = [schemaControl, starterControl, cisControl].every(
            (control) => control instanceof HTMLElement && validateControl(control)
        );
        duplicatePlanRequest += 1;
        const request = duplicatePlanRequest;
        clearActionError();
        duplicatePlanIsValid = false;
        setDuplicatePlanBusy(true);

        if (!payload || !controlsValid) {
            form.dataset.preparationFormState = "rejected";
            setDuplicatePlanBusy(false);
            return;
        }

        try {
            const response = await fetch(PREVIEW_DUPLICATE_PROFILE_PATH, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const result = await response.json().catch(() => null);
            if (request !== duplicatePlanRequest) return;
            if (!response.ok) {
                setDuplicatePlanBusy(false);
                rejectForCode(
                    typeof result?.detail?.code === "string"
                        ? result.detail.code
                        : "preparation_transaction_failed",
                    { disabled: true }
                );
                return;
            }
            if (result?.status !== "valid") {
                setDuplicatePlanBusy(false);
                rejectForCode(duplicatePreviewFailureCode(result?.reason_code), { disabled: true });
                return;
            }
            duplicatePlanIsValid = true;
            form.dataset.preparationFormState = "ready";
            setDuplicatePlanBusy(false);
        } catch (error) {
            if (request !== duplicatePlanRequest) return;
            setDuplicatePlanBusy(false);
            rejectForCode("preparation_transaction_failed", { disabled: true });
        }
    }

    document.addEventListener("bpm:preparation-state", (event) => {
        const detail = event instanceof CustomEvent ? event.detail : null;
        if (!detail || typeof detail.code !== "string") return;
        rejectForCode(detail.code);
    });

    schemaControl?.addEventListener("change", updateCisAvailability);
    for (const control of controls) {
        control.addEventListener("input", () => validateControl(control));
        control.addEventListener("change", () => {
            validateControl(control);
            if (
                preparationMode === "duplicate"
                && (control === schemaControl || control === starterControl || control === cisControl)
            ) {
                void refreshDuplicatePlan();
            }
        });
        control.addEventListener("invalid", (event) => {
            event.preventDefault();
            validateControl(control);
        });
    }
    updateCisAvailability();
    if (preparationMode === "duplicate") void refreshDuplicatePlan();

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (submitting) return;

        clearActionError();
        const firstInvalid = controls.find((control) => !validateControl(control));
        if (firstInvalid) {
            form.dataset.preparationFormState = "rejected";
            if (state) state.textContent = firstInvalid.validationMessage;
            firstInvalid.focus();
            return;
        }

        const payload = preparationMode === "duplicate"
            ? duplicatePayload(true)
            : newProfilePayload();
        if (!payload) {
            finishRejected("preparation_transaction_failed");
            return;
        }
        if (preparationMode === "duplicate" && !duplicatePlanIsValid) {
            void refreshDuplicatePlan();
            return;
        }

        setSubmitting(true);
        try {
            const response = await fetch(
                preparationMode === "duplicate"
                    ? PREPARE_DUPLICATE_PROFILE_PATH
                    : PREPARE_NEW_PROFILE_PATH,
                {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
                }
            );
            const result = await response.json().catch(() => null);
            if (!response.ok) {
                finishRejected(
                    typeof result?.detail?.code === "string"
                        ? result.detail.code
                        : "preparation_transaction_failed"
                );
                return;
            }

            const destination = Number.isInteger(result?.id) && result.id > 0
                ? `/profiles/${result.id}/edit`
                : null;
            if (!destination) {
                finishRejected("preparation_transaction_failed");
                return;
            }

            form.dataset.preparationFormState = "succeeded";
            sessionStorage.removeItem(storageKey);
            window.location.assign(destination);
        } catch (_error) {
            finishRejected("preparation_transaction_failed");
        } finally {
            if (form.dataset.preparationFormState !== "succeeded" && submitting) {
                setSubmitting(false);
            }
        }
    });
}
