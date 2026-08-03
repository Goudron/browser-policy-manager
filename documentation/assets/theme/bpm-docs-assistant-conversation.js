(() => {
  "use strict";

  const STORAGE_PREFIX = "bpm.documentation-assistant.floating.v1.";
  const MAX_TURNS = 8;
  const MAX_MESSAGE_LENGTH = 4000;
  const TURN_KEYS = ["assistant", "user"];
  const STATE_KEYS = ["expanded", "locale", "tab_id", "turns", "version", "web_enabled"];
  const LEGACY_STATE_KEYS = ["expanded", "locale", "turns", "version"];
  const VALID_LOCALE = /^[a-z]{2}(?:-[A-Z]{2})?$/;
  const VALID_TAB_ID = /^[A-Za-z0-9_-]{20,64}$/;
  const pendingTurns = new WeakMap();

  function storageKey(locale) {
    return `${STORAGE_PREFIX}${locale}`;
  }

  function exactKeys(value, expected) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      return false;
    }
    const actual = Object.keys(value).sort();
    return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
  }

  function validText(value) {
    return typeof value === "string" && value.length > 0 && value.length <= MAX_MESSAGE_LENGTH && !/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/.test(value);
  }

  function validTurn(turn) {
    return exactKeys(turn, TURN_KEYS) && validText(turn.user) && validText(turn.assistant);
  }

  function validState(state, locale) {
    return exactKeys(state, STATE_KEYS) &&
      state.version === 1 && state.locale === locale && typeof state.expanded === "boolean" &&
      typeof state.web_enabled === "boolean" && VALID_TAB_ID.test(state.tab_id) &&
      Array.isArray(state.turns) && state.turns.length <= MAX_TURNS && state.turns.every(validTurn);
  }

  function newTabId() {
    if (!window.crypto || typeof window.crypto.getRandomValues !== "function") {
      return null;
    }
    const bytes = window.crypto.getRandomValues(new Uint8Array(16));
    return `tab_${Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("")}`;
  }

  function emptyState(locale) {
    const tabId = newTabId();
    return tabId === null
      ? null
      : { version: 1, locale, expanded: false, tab_id: tabId, turns: [], web_enabled: false };
  }

  function readState(locale) {
    try {
      const stored = window.sessionStorage.getItem(storageKey(locale));
      if (!stored) {
        const state = emptyState(locale);
        if (state !== null) {
          writeState(state);
        }
        return state;
      }
      const parsed = JSON.parse(stored);
      if (validState(parsed, locale)) {
        return parsed;
      }
      if (
        exactKeys(parsed, LEGACY_STATE_KEYS) && parsed.version === 1 &&
        parsed.locale === locale && typeof parsed.expanded === "boolean" &&
        Array.isArray(parsed.turns) && parsed.turns.length <= MAX_TURNS &&
        parsed.turns.every(validTurn)
      ) {
        const tabId = newTabId();
        const migrated = tabId === null
          ? null
          : { ...parsed, tab_id: tabId, web_enabled: false };
        if (migrated !== null) {
          writeState(migrated);
        }
        return migrated;
      }
      const state = emptyState(locale);
      if (state !== null) {
        writeState(state);
      }
      return state;
    } catch {
      return emptyState(locale);
    }
  }

  function writeState(state) {
    if (!validState(state, state.locale)) {
      return false;
    }
    try {
      window.sessionStorage.setItem(storageKey(state.locale), JSON.stringify(state));
      return true;
    } catch {
      return false;
    }
  }

  function localeFor(widget) {
    const locale = widget && widget.dataset ? widget.dataset.assistantLocale : "";
    return VALID_LOCALE.test(locale) ? locale : null;
  }

  function renderMessage(transcript, role, value) {
    const item = document.createElement("li");
    const message = document.createElement("p");
    item.className = `bpm-docs-assistant-message bpm-docs-assistant-message--${role}`;
    item.dataset.assistantMessageRole = role;
    message.textContent = value;
    item.append(message);
    transcript.append(item);
  }

  function renderTurns(widget, turns) {
    const transcript = widget.querySelector("[data-assistant-transcript]");
    if (!transcript) {
      return false;
    }
    transcript.replaceChildren();
    const pending = pendingTurns.get(widget);
    const visibleTurns = pending ? [...turns, pending] : turns;
    visibleTurns.forEach((turn) => {
      renderMessage(transcript, "user", turn.user);
      renderMessage(transcript, "assistant", turn.assistant);
    });
    transcript.scrollTop = transcript.scrollHeight;
    return true;
  }

  function setExpanded(widget, expanded) {
    const locale = localeFor(widget);
    if (!locale || typeof expanded !== "boolean") {
      return false;
    }
    const state = readState(locale);
    if (state === null) {
      return false;
    }
    state.expanded = expanded;
    return writeState(state);
  }

  function restore(widget) {
    const locale = localeFor(widget);
    if (!locale) {
      return null;
    }
    const state = readState(locale);
    if (state === null) {
      return null;
    }
    // A pending generation cannot safely survive a navigation; completed pairs do.
    pendingTurns.delete(widget);
    renderTurns(widget, state.turns);
    return state;
  }

  function recordCompletedTurn(widget, turn) {
    const locale = localeFor(widget);
    if (!locale || !validTurn(turn)) {
      return false;
    }
    const state = readState(locale);
    if (state === null) {
      return false;
    }
    pendingTurns.delete(widget);
    state.turns = [...state.turns, { user: turn.user, assistant: turn.assistant }].slice(-MAX_TURNS);
    if (!writeState(state)) {
      return false;
    }
    return renderTurns(widget, state.turns);
  }

  function clear(widget) {
    const locale = localeFor(widget);
    if (!locale) {
      return false;
    }
    const state = readState(locale);
    if (state === null) {
      return false;
    }
    pendingTurns.delete(widget);
    state.turns = [];
    if (!writeState(state)) {
      return false;
    }
    return renderTurns(widget, state.turns);
  }

  function showPendingTurn(widget, turn) {
    const locale = localeFor(widget);
    if (!locale || !validTurn(turn)) {
      return false;
    }
    const state = readState(locale);
    if (state === null) {
      return false;
    }
    pendingTurns.set(widget, { user: turn.user, assistant: turn.assistant });
    return renderTurns(widget, state.turns);
  }

  function replacePendingTurn(widget, assistant) {
    const locale = localeFor(widget);
    const pending = pendingTurns.get(widget);
    if (!locale || !pending || !validText(assistant)) {
      return false;
    }
    const state = readState(locale);
    if (state === null) {
      return false;
    }
    pendingTurns.set(widget, { user: pending.user, assistant });
    return renderTurns(widget, state.turns);
  }

  function webState(widget) {
    const locale = localeFor(widget);
    const state = locale ? readState(locale) : null;
    return state === null
      ? null
      : { enabled: state.web_enabled, tabId: state.tab_id };
  }

  function setWebEnabled(widget, enabled) {
    const locale = localeFor(widget);
    if (!locale || typeof enabled !== "boolean") {
      return false;
    }
    const state = readState(locale);
    if (state === null) {
      return false;
    }
    state.web_enabled = enabled;
    return writeState(state);
  }

  function setReady(widget, ready) {
    const status = widget.querySelector("[data-assistant-status]");
    const question = widget.querySelector("[data-assistant-question]");
    const clearButton = widget.querySelector("[data-assistant-clear]");
    const installButton = widget.querySelector("[data-assistant-install]");
    if (!status || !question || !clearButton || !installButton || typeof ready !== "boolean") {
      return false;
    }
    widget.dataset.assistantState = ready ? "ready" : "unavailable";
    status.textContent = ready ? widget.dataset.assistantLabelReady : widget.dataset.assistantLabelUnavailable;
    question.disabled = !ready;
    question.setAttribute("aria-disabled", String(!ready));
    clearButton.hidden = !ready;
    installButton.hidden = ready;
    return true;
  }

  function setupWidget(widget) {
    restore(widget);
  }

  document.querySelectorAll("[data-documentation-assistant-widget]").forEach(setupWidget);
  window.BPMDocumentationAssistantConversation = Object.freeze({
    clear,
    recordCompletedTurn,
    replacePendingTurn,
    restore,
    setExpanded,
    setReady,
    setWebEnabled,
    showPendingTurn,
    webState,
  });
})();
