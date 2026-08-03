(() => {
  "use strict";

  const API_VERSION = 1;
  const STATE_MESSAGE = Object.freeze({
    loading: ["states", "loading"],
    indexing: ["states", "indexing"],
    busy: ["resource_states", "queued"],
    cancelled: ["states", "cancelled"],
    timeout: ["resource_states", "timeout"],
    degraded: ["resource_states", "resource_limit"],
    unloading: ["resource_states", "unloading"],
    unloaded: ["resource_states", "unloaded"],
    "search-only": ["resource_states", "search_only"],
    duplicate: ["resource_states", "duplicate"],
  });
  const RETRY_STATES = new Set(["timeout", "degraded", "unloaded", "search-only"]);
  const stateEpochs = new WeakMap();

  function exactKeys(value, expected) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      return false;
    }
    const actual = Object.keys(value).sort();
    return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
  }

  function validSnapshot(snapshot) {
    return (
      exactKeys(snapshot, ["api_version", "locale", "state", "state_epoch"]) &&
      snapshot.api_version === API_VERSION &&
      typeof snapshot.locale === "string" &&
      /^[a-z]{2}(?:-[A-Z]{2})?$/.test(snapshot.locale) &&
      Object.hasOwn(STATE_MESSAGE, snapshot.state) &&
      Number.isSafeInteger(snapshot.state_epoch) &&
      snapshot.state_epoch >= 0
    );
  }

  function stateMessage(snapshot, messages) {
    if (!messages || typeof messages !== "object" || Array.isArray(messages)) {
      return null;
    }
    const [group, key] = STATE_MESSAGE[snapshot.state];
    const message = messages[group] && messages[group][key];
    if (typeof message !== "string" || !message.trim()) {
      return null;
    }
    if (RETRY_STATES.has(snapshot.state)) {
      const retry = messages.actions && messages.actions.retry;
      if (typeof retry !== "string" || !retry.trim()) {
        return null;
      }
      return `${message} ${retry}`;
    }
    return message;
  }

  function renderResourceState(root, snapshot, messages) {
    if (!root || typeof root.querySelector !== "function" || !validSnapshot(snapshot)) {
      return false;
    }
    const message = stateMessage(snapshot, messages);
    const status = root.querySelector("[data-assistant-status]");
    const recovery = root.querySelector("[data-assistant-recovery]");
    const recoveryMessage = root.querySelector("[data-assistant-recovery-message]");
    const recoverySearch = root.querySelector("[data-assistant-recovery-search]");
    if (!message || !status || !recovery || !recoveryMessage || !recoverySearch) {
      return false;
    }
    const previousEpoch = stateEpochs.get(root);
    if (previousEpoch !== undefined && snapshot.state_epoch <= previousEpoch) {
      return false;
    }

    stateEpochs.set(root, snapshot.state_epoch);
    root.dataset.assistantState = snapshot.state;
    status.textContent = message;
    recoveryMessage.textContent = message;
    recovery.hidden = false;
    recoverySearch.hidden = false;
    return true;
  }

  window.BPMDocumentationAssistantStateMachine = Object.freeze({
    renderResourceState,
  });
})();
