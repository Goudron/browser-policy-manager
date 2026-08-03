/* Safe presentation helper for the released user-controlled external-sources mode. */
(() => {
  "use strict";

  const API_VERSION = 1;
  const VALID_LOCALE = /^[a-z]{2}(?:-[A-Z]{2})?$/;

  function isObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }

  function exactKeys(value, expected) {
    if (!isObject(value)) {
      return false;
    }
    const actual = Object.keys(value).sort();
    return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
  }

  function validSnapshot(snapshot, locale) {
    return exactKeys(snapshot, [
      "api_version", "available", "enabled", "locale", "reason_code", "state_epoch",
    ]) && snapshot.api_version === API_VERSION && snapshot.locale === locale &&
      VALID_LOCALE.test(snapshot.locale) && typeof snapshot.available === "boolean" &&
      typeof snapshot.enabled === "boolean" && (!snapshot.enabled || snapshot.available) &&
      typeof snapshot.reason_code === "string" && snapshot.reason_code.length > 0 &&
      snapshot.reason_code.length <= 128 && Number.isSafeInteger(snapshot.state_epoch) &&
      snapshot.state_epoch >= 0;
  }

  function renderWebMode(widget, snapshot) {
    const locale = widget && widget.dataset ? widget.dataset.assistantLocale : "";
    if (!validSnapshot(snapshot, locale)) {
      return false;
    }
    const control = widget.querySelector("[data-assistant-web-control]");
    const toggle = widget.querySelector("[data-assistant-web-toggle]");
    if (!control || !toggle) {
      return false;
    }
    toggle.checked = snapshot.enabled;
    toggle.disabled = !snapshot.available;
    toggle.setAttribute("aria-disabled", String(!snapshot.available));
    widget.dataset.assistantWebAvailable = String(snapshot.available);
    widget.dataset.assistantWebEnabled = String(snapshot.enabled);
    return true;
  }

  window.BPMDocumentationAssistantWebMode = Object.freeze({
    renderWebMode,
    validSnapshot,
  });
})();
