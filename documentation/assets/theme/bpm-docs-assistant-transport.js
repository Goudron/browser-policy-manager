(() => {
  "use strict";

  const API_VERSION = 1;
  const API_ROOT = "/api/documentation-assistant";
  const MODEL_API_ROOT = "/api/local-model";
  const MODEL_POLL_INTERVAL_MS = 1500;
  const MAX_QUESTION_LENGTH = 4000;
  const MAX_ANSWER_LENGTH = 4000;
  const MAX_SOURCES = 8;
  const MAX_EXTERNAL_CLAIMS = 3;
  const MAX_EXTERNAL_CLAIM_LENGTH = 600;
  const OPAQUE_ID = /^[A-Za-z0-9_-]{1,128}$/;
  const EXTERNAL_SOURCE_PATHS = Object.freeze({
    "mozilla.github.io": ["/policy-templates/"],
    "support.mozilla.org": ["/"],
    "firefox-source-docs.mozilla.org": [
      "/browser/components/enterprisepolicies/", "/toolkit/components/enterprisepolicies/",
    ],
    "www.mozilla.org": [
      "/en-US/firefox/", "/ru/firefox/", "/de/firefox/", "/zh-CN/firefox/",
      "/fr/firefox/", "/es-ES/firefox/",
    ],
  });
  const DISPOSITIONS = new Set(["answer", "clarify", "abstain", "refuse"]);
  const STATUS_STATES = new Set([
    "disabled", "not-installed", "downloading", "indexing", "loading", "ready", "busy",
    "cancelled", "degraded", "incompatible", "crashed", "web-offline",
  ]);
  const EVENT_TYPES = new Set(["accepted", "progress", "final", "cancelled", "error"]);
  const contexts = new WeakMap();

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

  function validText(value, limit) {
    return typeof value === "string" && value.length > 0 && value.length <= limit &&
      !/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/.test(value);
  }

  function sameOriginPath(value, expectedPrefix) {
    if (typeof value !== "string") {
      return null;
    }
    try {
      const url = new URL(value, window.location.origin);
      if (url.origin !== window.location.origin || !url.pathname.startsWith(expectedPrefix) || url.search || url.hash) {
        return null;
      }
      return `${url.pathname}`;
    } catch {
      return null;
    }
  }

  function validStatus(value, locale) {
    return exactKeys(value, [
      "action_key", "api_version", "assistant_ready", "lexical_search_ready", "locale", "message_key",
      "reason_code", "state", "state_epoch",
    ]) && value.api_version === API_VERSION && value.locale === locale &&
      STATUS_STATES.has(value.state) && typeof value.assistant_ready === "boolean" &&
      typeof value.lexical_search_ready === "boolean" && typeof value.message_key === "string" &&
      typeof value.action_key === "string" && typeof value.reason_code === "string" &&
      Number.isSafeInteger(value.state_epoch) && value.state_epoch >= 0;
  }

  function validAdmission(value) {
    return exactKeys(value, ["api_version", "request_id", "state", "state_epoch", "stream_path", "time_preview"]) &&
      value.api_version === API_VERSION && OPAQUE_ID.test(value.request_id) && value.state === "accepted" &&
      Number.isSafeInteger(value.state_epoch) && value.state_epoch >= 0 &&
      validTimePreview(value.time_preview) &&
      sameOriginPath(value.stream_path, `${API_ROOT}/chat/${value.request_id}/`) ===
        `${API_ROOT}/chat/${value.request_id}/stream`;
  }

  function validTimePreview(value) {
    return exactKeys(value, ["maximum_seconds", "minimum_seconds"]) &&
      Number.isSafeInteger(value.minimum_seconds) && Number.isSafeInteger(value.maximum_seconds) &&
      value.minimum_seconds >= 1 && value.maximum_seconds >= value.minimum_seconds &&
      value.maximum_seconds <= 14400;
  }

  function validCancellation(value, requestId) {
    return exactKeys(value, ["api_version", "reason_code", "request_id", "state", "state_epoch"]) &&
      value.api_version === API_VERSION && value.request_id === requestId && value.state === "cancelled" &&
      typeof value.reason_code === "string" && Number.isSafeInteger(value.state_epoch) &&
      value.state_epoch >= 0;
  }

  function validModelToken(value) {
    return typeof value === "string" && /^[A-Za-z0-9_-]{20,128}$/.test(value);
  }

  function validModelOperation(value) {
    if (!isObject(value) || typeof value.state !== "string") {
      return false;
    }
    if (value.state === "idle") {
      return exactKeys(value, ["state"]);
    }
    if (value.state === "running" && exactKeys(value, ["busy", "state"])) {
      return value.busy === true;
    }
    return exactKeys(value, [
      "cancellable", "downloaded_bytes", "kind", "operation_id", "phase", "progress_percent",
      "reason_code", "state", "total_bytes",
    ]) && ["running", "installed", "removed", "cancelled", "failed"].includes(value.state) &&
      ["install", "verify", "remove"].includes(value.kind) && OPAQUE_ID.test(value.operation_id) &&
      typeof value.reason_code === "string" && typeof value.phase === "string" &&
      typeof value.cancellable === "boolean" && Number.isSafeInteger(value.downloaded_bytes) &&
      Number.isSafeInteger(value.total_bytes) && Number.isSafeInteger(value.progress_percent) &&
      value.downloaded_bytes >= 0 && value.total_bytes >= 0 && value.progress_percent >= 0 &&
      value.progress_percent <= 100 && value.downloaded_bytes <= value.total_bytes;
  }

  function validModelStatus(value) {
    return exactKeys(value, [
      "api_version", "csrf_token", "disclosure", "lexical_search_ready", "operation", "verification",
    ]) && value.api_version === API_VERSION && validModelToken(value.csrf_token) &&
      isObject(value.disclosure) && typeof value.lexical_search_ready === "boolean" &&
      exactKeys(value.verification, ["reason_code", "state", "verified"]) &&
      typeof value.verification.reason_code === "string" && typeof value.verification.state === "string" &&
      typeof value.verification.verified === "boolean" && validModelOperation(value.operation);
  }

  function validModelAction(value) {
    if (!isObject(value) || value.api_version !== API_VERSION || !validModelToken(value.csrf_token) ||
        typeof value.accepted !== "boolean") {
      return false;
    }
    return value.accepted
      ? exactKeys(value, ["accepted", "api_version", "csrf_token", "operation"]) && validModelOperation(value.operation)
      : exactKeys(value, ["accepted", "api_version", "csrf_token", "reason_code"]) &&
        typeof value.reason_code === "string";
  }

  function validEvent(value, eventType, requestId) {
    if (!EVENT_TYPES.has(eventType) || !isObject(value)) {
      return false;
    }
    const baseKeys = [
      "action_key", "api_version", "message_key", "reason_code", "request_id", "state", "state_epoch",
    ];
    const external = eventType === "final" && Object.hasOwn(value, "external_claims");
    const expected = eventType === "final"
      ? [
        "action_key", "api_version", "citations", "disposition", ...(external ? ["external_claims"] : []),
        "message_key", "reason_code", "request_id", "state", "state_epoch", "text",
      ]
      : baseKeys;
    if (!exactKeys(value, expected) || value.api_version !== API_VERSION || value.request_id !== requestId ||
        typeof value.state !== "string" || typeof value.reason_code !== "string" ||
        typeof value.message_key !== "string" || typeof value.action_key !== "string" ||
        !Number.isSafeInteger(value.state_epoch) || value.state_epoch < 0) {
      return false;
    }
    if (eventType !== "final") {
      return true;
    }
    const claimsValid = !external || (
      Array.isArray(value.external_claims) && value.external_claims.length > 0 &&
      value.external_claims.length <= MAX_EXTERNAL_CLAIMS &&
      value.external_claims.every((claim) => exactKeys(claim, ["citations", "text"]) &&
        validText(claim.text, MAX_EXTERNAL_CLAIM_LENGTH) && Array.isArray(claim.citations) &&
        claim.citations.length > 0 && claim.citations.length <= MAX_SOURCES &&
        new Set(claim.citations).size === claim.citations.length &&
        claim.citations.every((sourceId) => OPAQUE_ID.test(sourceId)))
    );
    return claimsValid && DISPOSITIONS.has(value.disposition) && typeof value.text === "string" &&
      value.text.length <= MAX_ANSWER_LENGTH && Array.isArray(value.citations) &&
      value.citations.length <= MAX_SOURCES && value.citations.every((sourceId) => OPAQUE_ID.test(sourceId)) &&
      (value.disposition === "answer" ? validText(value.text, MAX_ANSWER_LENGTH) : value.text === "") &&
      (!external || value.disposition === "answer");
  }

  function approvedExternalUrl(value) {
    if (typeof value !== "string" || value.length > 2048 || /[%\\\s\u0000-\u001F\u007F]/.test(value)) {
      return null;
    }
    try {
      const url = new URL(value);
      const paths = EXTERNAL_SOURCE_PATHS[url.hostname];
      if (url.protocol !== "https:" || !paths || url.username || url.password ||
          (url.port && url.port !== "443") || url.search || url.hash || url.pathname.includes("//") ||
          !paths.some((prefix) => url.pathname.startsWith(prefix))) {
        return null;
      }
      return url.href;
    } catch {
      return null;
    }
  }

  function validSource(value, sourceId, locale) {
    if (!isObject(value) || value.api_version !== API_VERSION || value.source_id !== sourceId ||
        value.locale !== locale || !validText(value.title, 240) || typeof value.excerpt !== "string" ||
        value.excerpt.length > 1200 || /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/.test(value.excerpt)) {
      return false;
    }
    if (exactKeys(value, ["api_version", "excerpt", "locale", "published_url", "source_id", "title"])) {
      return sameOriginPath(value.published_url, `/help/${locale}/`) !== null;
    }
    return exactKeys(value, [
      "api_version", "excerpt", "locale", "provider_id", "published_url", "source_id",
      "source_kind", "title",
    ]) && value.source_kind === "external_untrusted" &&
      value.provider_id === "brave-search-llm-context" && approvedExternalUrl(value.published_url) !== null;
  }

  async function json(response) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  function controls(widget) {
    return {
      clear: widget.querySelector("[data-assistant-clear]"),
      install: widget.querySelector("[data-assistant-install]"),
      question: widget.querySelector("[data-assistant-question]"),
      send: widget.querySelector("[data-assistant-send]"),
      status: widget.querySelector("[data-assistant-status]"),
      stop: widget.querySelector("[data-assistant-stop]"),
    };
  }

  function setVisualState(context, state) {
    const { widget, conversation, controls: ui } = context;
    if (!ui.status || !ui.question || !ui.send || !ui.stop || !ui.clear || !ui.install) {
      return false;
    }
    const terminalRetry = state === "cancelled" || state === "error";
    const ready = state === "ready" || terminalRetry;
    const busy = state === "busy";
    const installing = state === "installing";
    conversation.setReady(widget, ready);
    widget.dataset.assistantState = state;
    ui.send.hidden = !ready;
    ui.send.disabled = !ready;
    ui.send.setAttribute("aria-disabled", String(!ready));
    ui.stop.hidden = !busy;
    ui.stop.disabled = !busy;
    ui.stop.setAttribute("aria-disabled", String(!busy));
    ui.install.hidden = ready || busy;
    ui.install.disabled = ready || busy || installing;
    ui.install.setAttribute("aria-disabled", String(ready || busy || installing));
    if (busy) {
      ui.status.textContent = widget.dataset.assistantLabelBusy;
      ui.clear.hidden = false;
    } else if (installing) {
      ui.status.textContent = widget.dataset.assistantLabelInstalling;
      ui.clear.hidden = true;
    } else if (state === "model-failed") {
      ui.status.textContent = widget.dataset.assistantLabelInstallFailed;
      ui.clear.hidden = true;
    } else if (state === "cancelled") {
      ui.status.textContent = widget.dataset.assistantLabelCancelled;
      ui.clear.hidden = false;
    } else if (state === "error") {
      ui.status.textContent = widget.dataset.assistantLabelUnavailable;
      ui.clear.hidden = false;
    } else if (!ready) {
      ui.status.textContent = widget.dataset.assistantLabelUnavailable;
      ui.clear.hidden = true;
    }
    return true;
  }

  function closeStream(context) {
    if (context.stream) {
      context.stream.close();
      context.stream = null;
    }
    context.requestId = null;
    context.question = "";
  }

  function recoverableFailure(context) {
    context.conversation.replacePendingTurn(
      context.widget, context.widget.dataset.assistantLabelAnswerFailed
    );
    closeStream(context);
    // A terminal transport failure must remain visible, while the ready local runtime may
    // immediately accept a new question.  It never becomes a persisted completed turn.
    setVisualState(context, "error");
  }

  function stopStreamOnly(context) {
    if (context.stream) {
      context.stream.close();
      context.stream = null;
    }
  }

  function stopModelPolling(context) {
    if (context.modelTimer !== null) {
      window.clearTimeout(context.modelTimer);
      context.modelTimer = null;
    }
  }

  function assistantText(widget, disposition) {
    const labels = {
      clarify: widget.dataset.assistantLabelClarify,
      abstain: widget.dataset.assistantLabelAbstain,
      refuse: widget.dataset.assistantLabelRefuse,
    };
    return labels[disposition] || "";
  }

  function timePreviewText(widget, preview) {
    return widget.dataset.assistantLabelTimePreview
      .replace("{minimum}", durationText(widget.dataset.assistantLocale, preview.minimum_seconds))
      .replace("{maximum}", durationText(widget.dataset.assistantLocale, preview.maximum_seconds));
  }

  function russianDurationUnit(value, forms) {
    const remainder = value % 100;
    if (remainder >= 11 && remainder <= 14) {
      return forms[2];
    }
    const last = value % 10;
    return last === 1 ? forms[0] : (last >= 2 && last <= 4 ? forms[1] : forms[2]);
  }

  function durationText(locale, totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    if (locale === "ru") {
      return `${minutes} ${russianDurationUnit(minutes, ["минута", "минуты", "минут"])} ` +
        `${seconds} ${russianDurationUnit(seconds, ["секунда", "секунды", "секунд"] )}`;
    }
    if (locale === "zh-CN") {
      return `${minutes} 分钟 ${seconds} 秒`;
    }
    if (locale === "de") {
      return `${minutes} Min. ${seconds} Sek.`;
    }
    if (locale === "fr") {
      return `${minutes} min ${seconds} s`;
    }
    if (locale === "es-ES") {
      return `${minutes} min ${seconds} s`;
    }
    return `${minutes} min ${seconds} sec`;
  }

  function appendSources(context, sources) {
    if (!sources.length) {
      return;
    }
    const transcript = context.widget.querySelector("[data-assistant-transcript]");
    const message = transcript && transcript.querySelector(".bpm-docs-assistant-message--assistant:last-child");
    if (!message) {
      return;
    }
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    const list = document.createElement("ul");
    summary.textContent = context.widget.dataset.assistantLabelSources;
    sources.forEach((source) => {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.textContent = source.title;
      link.href = sameOriginPath(source.published_url, `/help/${context.locale}/`);
      item.append(link);
      if (source.excerpt) {
        const excerpt = document.createElement("p");
        excerpt.textContent = source.excerpt;
        item.append(excerpt);
      }
      list.append(item);
    });
    details.append(summary, list);
    message.append(details);
  }

  function appendExternalClaims(context, claims, sources) {
    if (!claims.length) {
      return;
    }
    const transcript = context.widget.querySelector("[data-assistant-transcript]");
    const message = transcript && transcript.querySelector(".bpm-docs-assistant-message--assistant:last-child");
    if (!message) {
      return;
    }
    const byId = new Map(sources.map((source) => [source.source_id, source]));
    const region = document.createElement("section");
    const heading = document.createElement("h3");
    heading.textContent = context.widget.dataset.assistantLabelExternalSources;
    region.className = "bpm-docs-assistant-external-claims";
    region.setAttribute("aria-label", context.widget.dataset.assistantLabelExternalSources);
    region.append(heading);
    claims.forEach((claim) => {
      const item = document.createElement("div");
      const text = document.createElement("p");
      const list = document.createElement("ul");
      item.className = "bpm-docs-assistant-external-claim";
      text.textContent = claim.text;
      claim.citations.forEach((sourceId) => {
        const source = byId.get(sourceId);
        const listItem = document.createElement("li");
        const link = document.createElement("a");
        link.textContent = source.title;
        link.href = approvedExternalUrl(source.published_url);
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        listItem.append(link);
        list.append(listItem);
      });
      item.append(text, list);
      region.append(item);
    });
    message.append(region);
  }

  async function sourcesFor(context, requestId, sourceIds, sourceKind = "local") {
    const results = await Promise.all(sourceIds.map(async (sourceId) => {
      try {
        const response = await fetch(`${API_ROOT}/chat/${encodeURIComponent(requestId)}/sources/${encodeURIComponent(sourceId)}`, {
          credentials: "same-origin",
          headers: { Accept: "application/json" },
        });
        const source = await json(response);
        const kindMatches = sourceKind === "local"
          ? !Object.hasOwn(source || {}, "source_kind")
          : source && source.source_kind === "external_untrusted";
        return response.ok && kindMatches && validSource(source, sourceId, context.locale) ? source : null;
      } catch {
        return null;
      }
    }));
    return results.filter((source) => source !== null);
  }

  async function handleFinal(context, event) {
    const responseText = event.disposition === "answer"
      ? event.text
      : assistantText(context.widget, event.disposition);
    if (!validText(responseText, MAX_ANSWER_LENGTH)) {
      recoverableFailure(context);
      return;
    }
    const claims = event.disposition === "answer" && Array.isArray(event.external_claims)
      ? event.external_claims
      : [];
    const externalSourceIds = [...new Set(claims.flatMap((claim) => claim.citations))];
    const [sources, externalSources] = event.disposition === "answer"
      ? await Promise.all([
        sourcesFor(context, event.request_id, event.citations),
        sourcesFor(context, event.request_id, externalSourceIds, "external"),
      ])
      : [];
    if (event.disposition === "answer" &&
        (sources.length !== event.citations.length || externalSources.length !== externalSourceIds.length)) {
      recoverableFailure(context);
      return;
    }
    if (!context.conversation.recordCompletedTurn(context.widget, {
      user: context.question,
      assistant: responseText,
    })) {
      recoverableFailure(context);
      return;
    }
    appendSources(context, sources);
    appendExternalClaims(context, claims, externalSources);
    closeStream(context);
    setVisualState(context, "ready");
  }

  function handleStreamEvent(context, eventType, raw) {
    let event;
    try {
      event = JSON.parse(raw.data);
    } catch {
      recoverableFailure(context);
      return;
    }
    if (!context.requestId || !validEvent(event, eventType, context.requestId) || event.state_epoch < context.epoch) {
      recoverableFailure(context);
      return;
    }
    context.epoch = event.state_epoch;
    if (eventType === "accepted" || eventType === "progress") {
      setVisualState(context, "busy");
      return;
    }
    if (eventType === "final") {
      stopStreamOnly(context);
      void handleFinal(context, event);
      return;
    }
    context.conversation.replacePendingTurn(
      context.widget,
      eventType === "cancelled"
        ? context.widget.dataset.assistantLabelCancelled
        : context.widget.dataset.assistantLabelAnswerFailed,
    );
    closeStream(context);
    setVisualState(context, eventType === "cancelled" ? "cancelled" : "error");
  }

  function openStream(context, streamPath) {
    const stream = new EventSource(streamPath);
    context.stream = stream;
    ["accepted", "progress", "final", "cancelled", "error"].forEach((eventType) => {
      stream.addEventListener(eventType, (event) => handleStreamEvent(context, eventType, event));
    });
    stream.onerror = () => {
      if (context.stream === stream) {
        recoverableFailure(context);
      }
    };
  }

  function installationStatus(context, operation) {
    const labels = {
      preparing_documentation: context.widget.dataset.assistantLabelPreparing,
      verifying: context.widget.dataset.assistantLabelVerifying,
    };
    const label = labels[operation.phase] || context.widget.dataset.assistantLabelInstalling;
    if (operation.phase !== "downloading" || operation.total_bytes === 0) {
      return label;
    }
    return `${label}: ${operation.progress_percent}% (${operation.downloaded_bytes}/${operation.total_bytes} B)`;
  }

  async function modelStatus(context) {
    const response = await fetch(`${MODEL_API_ROOT}?locale=${encodeURIComponent(context.locale)}`, {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    });
    const snapshot = await json(response);
    if (!response.ok || !validModelStatus(snapshot)) {
      return null;
    }
    context.modelCsrfToken = snapshot.csrf_token;
    return snapshot;
  }

  function scheduleModelStatus(context) {
    stopModelPolling(context);
    context.modelTimer = window.setTimeout(() => {
      context.modelTimer = null;
      void loadModelStatus(context);
    }, MODEL_POLL_INTERVAL_MS);
  }

  async function loadModelStatus(context) {
    if (context.modelLoading) {
      return;
    }
    context.modelLoading = true;
    try {
      const snapshot = await modelStatus(context);
      if (snapshot === null) {
        setVisualState(context, "model-failed");
        return;
      }
      const operation = snapshot.operation;
      if (operation.state === "running") {
        setVisualState(context, "installing");
        if (operation.kind === "install") {
          context.controls.status.textContent = installationStatus(context, operation);
        }
        scheduleModelStatus(context);
        return;
      }
      stopModelPolling(context);
      if (operation.state === "failed") {
        setVisualState(context, "model-failed");
        return;
      }
      if (operation.state === "installed" || snapshot.verification.verified) {
        if (context.loading) {
          setVisualState(context, "unavailable");
        } else {
          await loadStatus(context, false);
        }
        return;
      }
      setVisualState(context, "error");
    } catch {
      setVisualState(context, "model-failed");
    } finally {
      context.modelLoading = false;
    }
  }

  async function loadStatus(context, inspectModel = true) {
    if (context.loading || context.requestId) {
      return;
    }
    context.loading = true;
    try {
      const response = await fetch(`${API_ROOT}/status?locale=${encodeURIComponent(context.locale)}`, {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      });
      const status = await json(response);
      if (!response.ok || !validStatus(status, context.locale)) {
        setVisualState(context, "unavailable");
        return;
      }
      context.epoch = status.state_epoch;
      if (status.assistant_ready && ["ready", "web-offline"].includes(status.state)) {
        stopModelPolling(context);
        setVisualState(context, "ready");
      } else if (inspectModel) {
        await loadModelStatus(context);
      } else {
        setVisualState(context, "unavailable");
      }
    } catch {
      setVisualState(context, "unavailable");
    } finally {
      context.loading = false;
    }
  }

  async function startInstallation(context) {
    if (context.loading || context.modelLoading || context.requestId) {
      return;
    }
    context.controls.install.disabled = true;
    context.controls.install.setAttribute("aria-disabled", "true");
    try {
      if (!context.modelCsrfToken) {
        const snapshot = await modelStatus(context);
        if (snapshot === null) {
          setVisualState(context, "model-failed");
          return;
        }
        if (snapshot.operation.state === "running") {
          await loadModelStatus(context);
          return;
        }
      }
      const response = await fetch(`${MODEL_API_ROOT}/install`, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          api_version: API_VERSION,
          locale: context.locale,
          csrf_token: context.modelCsrfToken,
          confirm_install: true,
        }),
      });
      const result = await json(response);
      if (!response.ok || !validModelAction(result) || !result.accepted) {
        setVisualState(context, "model-failed");
        return;
      }
      context.modelCsrfToken = result.csrf_token;
      setVisualState(context, "installing");
      await loadModelStatus(context);
    } catch {
      setVisualState(context, "model-failed");
    }
  }

  async function send(context) {
    if (context.loading || context.requestId) {
      return;
    }
    const question = context.controls.question.value.trim();
    if (!validText(question, MAX_QUESTION_LENGTH)) {
      return;
    }
    context.loading = true;
    setVisualState(context, "busy");
    try {
      const response = await fetch(`${API_ROOT}/chat`, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          api_version: API_VERSION,
          locale: context.locale,
          question,
          tab_id: context.tabId,
          web_mode: "local_only",
        }),
      });
      const admission = await json(response);
      if (!response.ok || !validAdmission(admission)) {
        setVisualState(context, "error");
        return;
      }
      context.requestId = admission.request_id;
      context.question = question;
      context.epoch = admission.state_epoch;
      context.controls.question.value = "";
      if (!context.conversation.showPendingTurn(context.widget, {
        user: question,
        assistant: timePreviewText(context.widget, admission.time_preview),
      })) {
        await cancel(context);
        return;
      }
      openStream(context, admission.stream_path);
    } catch {
      setVisualState(context, "error");
    } finally {
      context.loading = false;
    }
  }

  async function cancel(context) {
    if (!context.requestId) {
      return;
    }
    const requestId = context.requestId;
    try {
      const response = await fetch(`${API_ROOT}/chat/${encodeURIComponent(requestId)}/cancel`, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_version: API_VERSION }),
      });
      const result = await json(response);
      if (!response.ok || !validCancellation(result, requestId)) {
        setVisualState(context, "unavailable");
        return;
      }
    } catch {
      setVisualState(context, "unavailable");
      return;
    }
    context.conversation.replacePendingTurn(
      context.widget, context.widget.dataset.assistantLabelCancelled
    );
    closeStream(context);
    setVisualState(context, "cancelled");
  }

  async function clear(context) {
    if (context.loading) {
      return;
    }
    context.loading = true;
    try {
      const response = await fetch(
        `${API_ROOT}/conversation?locale=${encodeURIComponent(context.locale)}&tab_id=${encodeURIComponent(context.tabId)}`,
        {
          method: "DELETE",
          credentials: "same-origin",
        },
      );
      if (!response.ok || response.status !== 204) {
        setVisualState(context, "unavailable");
        return;
      }
      closeStream(context);
      context.conversation.clear(context.widget);
      context.loading = false;
      await loadStatus(context);
    } catch {
      setVisualState(context, "unavailable");
    } finally {
      context.loading = false;
    }
  }

  function setupWidget(widget) {
    const conversation = window.BPMDocumentationAssistantConversation;
    const locale = widget.dataset.assistantLocale;
    const ui = controls(widget);
    if (!conversation || typeof conversation.setReady !== "function" || typeof conversation.clear !== "function" ||
        typeof conversation.recordCompletedTurn !== "function" || typeof conversation.replacePendingTurn !== "function" ||
        typeof conversation.showPendingTurn !== "function" || typeof conversation.webState !== "function" ||
        !/^[a-z]{2}(?:-[A-Z]{2})?$/.test(locale) ||
        !Object.values(ui).every(Boolean)) {
      return;
    }
    const storedWeb = conversation.webState(widget);
    if (!storedWeb || !OPAQUE_ID.test(storedWeb.tabId)) {
      return;
    }
    const context = {
      widget, conversation, controls: ui, locale, loading: false, modelLoading: false,
      modelCsrfToken: "", modelTimer: null, requestId: null, question: "", epoch: 0, stream: null,
      tabId: storedWeb.tabId,
    };
    contexts.set(widget, context);
    widget.addEventListener("bpm-documentation-assistant-toggle", (event) => {
      if (event.detail && event.detail.expanded) {
        void loadStatus(context);
      } else {
        stopModelPolling(context);
      }
    });
    ui.send.addEventListener("click", () => void send(context));
    ui.stop.addEventListener("click", () => void cancel(context));
    ui.clear.addEventListener("click", () => void clear(context));
    ui.install.addEventListener("click", () => void startInstallation(context));
    ui.question.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        void send(context);
      }
    });
  }

  document.querySelectorAll("[data-documentation-assistant-widget]").forEach(setupWidget);
})();
