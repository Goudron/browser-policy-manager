/* Safe, transport-free rendering contract for a future validated assistant final event.
 * Loading this file does not inspect a model, fetch data, or enable the disabled dialogue controls. */
(() => {
  "use strict";

  const API_VERSION = 1;
  const MAX_SOURCES = 8;
  const MAX_TEXT = 4000;
  const MAX_EXCERPT = 1200;
  const MAX_LABEL = 240;
  const OPAQUE_SOURCE_ID = /^src_[A-Za-z0-9_-]{16,128}$/;
  const ANCHOR_ID = /^[A-Za-z][A-Za-z0-9_-]{0,127}$/;
  const VERSION = /^\d+\.\d+\.\d+$/;
  const DISPOSITIONS = new Set(["answer", "clarify", "abstain", "refuse"]);

  const text = (value) => (typeof value === "string" ? value : "");
  const isObject = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
  const replace = (template, values) => text(template).replace(/\{([a-z_]+)\}/g, (_match, key) => text(values[key]));

  function validText(value, limit) {
    return typeof value === "string" && value.length > 0 && value.length <= limit && !/[\u0000-\u001F\u007F]/.test(value);
  }

  function validOptionalText(value, limit) {
    return typeof value === "string" && value.length <= limit && !/[\u0000-\u001F\u007F]/.test(value);
  }

  function sourceUrl(source, locale) {
    if (source.provenance === "local") {
      const parsed = new URL(source.published_url, window.location.origin);
      if (
        parsed.origin !== window.location.origin ||
        !parsed.pathname.startsWith(`/help/${locale}/`) ||
        parsed.search || parsed.hash
      ) {
        return null;
      }
      return `${parsed.pathname}${source.anchor === "root" ? "" : `#${source.anchor}`}`;
    }
    if (source.provenance !== "external") {
      return null;
    }
    try {
      const parsed = new URL(source.published_url);
      if (parsed.protocol !== "https:" || parsed.username || parsed.password) {
        return null;
      }
      return parsed.href;
    } catch {
      return null;
    }
  }

  function validSource(source, locale, bpmVersion) {
    if (!isObject(source) || Object.keys(source).length !== 9) {
      return false;
    }
    if (
      !OPAQUE_SOURCE_ID.test(text(source.source_id)) ||
      source.locale !== locale ||
      source.bpm_version !== bpmVersion ||
      !validText(source.title, MAX_LABEL) ||
      !validText(source.guide, MAX_LABEL) ||
      !validText(source.anchor, MAX_LABEL) ||
      !validOptionalText(source.excerpt, MAX_EXCERPT) ||
      (source.anchor !== "root" && !ANCHOR_ID.test(source.anchor)) ||
      !["local", "external"].includes(source.provenance)
    ) {
      return false;
    }
    return sourceUrl(source, locale) !== null;
  }

  function validPayload(payload) {
    if (!isObject(payload) || Object.keys(payload).length !== 6) {
      return false;
    }
    if (
      payload.api_version !== API_VERSION ||
      !DISPOSITIONS.has(payload.disposition) ||
      !validText(payload.locale, 16) ||
      !VERSION.test(text(payload.bpm_version)) ||
      !Array.isArray(payload.sources) ||
      payload.sources.length > MAX_SOURCES
    ) {
      return false;
    }
    if (payload.disposition === "answer") {
      return validText(payload.text, MAX_TEXT) && payload.sources.length > 0 &&
        payload.sources.some((source) => source.provenance === "local") &&
        payload.sources.every((source) => validSource(source, payload.locale, payload.bpm_version));
    }
    return payload.text === "" && payload.sources.length === 0;
  }

  function appendText(parent, tagName, value) {
    const node = document.createElement(tagName);
    node.textContent = value;
    parent.append(node);
    return node;
  }

  function renderSource(list, dialogue, source, locale, bpmVersion) {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.textContent = source.title;
    link.href = sourceUrl(source, locale);
    if (source.provenance === "external") {
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    }
    item.append(link);
    appendText(
      item,
      "p",
      source.provenance === "local" ? dialogue.citation_local : dialogue.citation_external,
    );
    appendText(item, "p", replace(dialogue.source_guide, { guide: source.guide }));
    appendText(item, "p", replace(dialogue.source_topic, { topic: source.title }));
    appendText(item, "p", replace(dialogue.source_anchor, { anchor: source.anchor }));
    appendText(item, "p", replace(dialogue.source_version, { version: bpmVersion }));
    if (source.excerpt) {
      const details = document.createElement("details");
      appendText(details, "summary", dialogue.source_excerpt);
      appendText(details, "p", source.excerpt);
      item.append(details);
    }
    list.append(item);
  }

  function modeLabel(dialogue, disposition) {
    if (disposition === "answer") {
      return dialogue.answer;
    }
    if (disposition === "clarify") {
      return dialogue.clarification;
    }
    if (disposition === "abstain") {
      return dialogue.no_evidence;
    }
    return dialogue.out_of_scope;
  }

  function renderValidatedFinal(root, messages, payload) {
    if (!root || !isObject(messages) || !isObject(messages.dialogue) || !validPayload(payload)) {
      return false;
    }
    const dialogue = messages.dialogue;
    if (
      !["answer", "clarification", "no_evidence", "out_of_scope", "citation_local", "citation_external", "source_guide", "source_topic", "source_anchor", "source_version", "source_excerpt"].every(
        (key) => validText(dialogue[key], MAX_LABEL),
      )
    ) {
      return false;
    }
    const modeRegion = root.querySelector("[data-assistant-answer-mode-region]");
    const sourcesRegion = root.querySelector("[data-assistant-sources]");
    const sourceList = root.querySelector("[data-assistant-source-list]");
    const status = root.querySelector("[data-assistant-status]");
    if (!modeRegion || !sourcesRegion || !sourceList || !status) {
      return false;
    }
    modeRegion.replaceChildren();
    sourceList.replaceChildren();
    appendText(modeRegion, "p", modeLabel(dialogue, payload.disposition));
    if (payload.disposition === "answer") {
      appendText(modeRegion, "p", payload.text);
      payload.sources.forEach((source) => renderSource(sourceList, dialogue, source, payload.locale, payload.bpm_version));
      sourcesRegion.hidden = false;
    } else {
      sourcesRegion.hidden = true;
    }
    modeRegion.hidden = false;
    root.dataset.assistantAnswerMode = payload.disposition;
    status.textContent = modeLabel(dialogue, payload.disposition);
    return true;
  }

  window.BPMDocumentationAssistantRenderer = Object.freeze({ renderValidatedFinal });
})();
