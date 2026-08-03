/* Explicit local-model lifecycle controls.  This file does not start chat, retrieval or downloads
 * while a page loads.  It first inspects the local model only after a deliberate user action. */
(() => {
  "use strict";

  const currentScript = document.currentScript;
  const copyUrl = currentScript && currentScript.src
    ? new URL("../assistant-copy.json", currentScript.src)
    : null;
  const apiUrl = "/api/local-model";
  const pollIntervalMs = 1500;

  const text = (value) => (typeof value === "string" ? value : "");
  const replace = (template, values) => text(template).replace(/\{([a-z_]+)\}/g, (_match, key) => text(values[key]));

  function appendText(parent, tagName, value) {
    const node = document.createElement(tagName);
    node.textContent = value;
    parent.append(node);
    return node;
  }

  function actionButton(label, action) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", action);
    return button;
  }

  function stateMessage(messages, snapshot) {
    const operation = snapshot.operation || { state: "idle" };
    if (operation.state === "running" && operation.kind === "install") {
      return messages.states.downloading;
    }
    if (operation.state === "cancelled") {
      return messages.states.cancelled;
    }
    if (operation.state === "failed") {
      return messages.states.degraded;
    }
    if (operation.state === "removed" || snapshot.verification.state === "not-installed") {
      return messages.states["not-installed"];
    }
    if (operation.state === "running" && operation.kind === "verify") {
      return { title: messages.model.verifying, detail: "" };
    }
    if (snapshot.verification.verified) {
      return { title: messages.model.installed, detail: messages.model.optional };
    }
    return messages.states["not-installed"];
  }

  function disclosureLines(manager, messages, snapshot) {
    const disclosure = snapshot.disclosure || {};
    const list = manager.disclosure;
    list.replaceChildren();
    const size = new Intl.NumberFormat(manager.locale).format(Number(disclosure.byte_count || 0)) + " B";
    appendText(list, "p", replace(messages.model.source, disclosure));
    appendText(list, "p", text(disclosure.source));
    appendText(list, "p", replace(messages.model.size, { size }));
    appendText(list, "p", text(messages.model.cpu));
    appendText(list, "p", text(messages.model.no_sla));
    appendText(list, "p", `SHA-256: ${text(disclosure.sha256)}`);
    appendText(list, "p", text(disclosure.model_id));
  }

  function render(manager, snapshot) {
    const messages = manager.copy.messages;
    const operation = snapshot.operation || { state: "idle" };
    const message = stateMessage(messages, snapshot);
    const progress = operation.state === "running" && operation.kind === "install" && operation.total_bytes
      ? ` ${operation.progress_percent}% (${operation.downloaded_bytes}/${operation.total_bytes} B)`
      : "";
    manager.status.textContent = `${text(message.title)}${message.detail ? `. ${text(message.detail)}` : ""}${progress}`;
    disclosureLines(manager, messages, snapshot);
    manager.actions.replaceChildren();
    manager.details.hidden = false;
    manager.inspect.disabled = false;

    if (operation.state === "running") {
      if (operation.cancellable) {
        manager.actions.append(actionButton(messages.actions.cancel, () => manager.cancel(operation.operation_id)));
      }
      window.setTimeout(() => manager.inspectStatus(true), pollIntervalMs);
      return;
    }
    if (snapshot.verification.verified) {
      manager.actions.append(actionButton(messages.actions.verify, () => manager.start("verify")));
      manager.actions.append(actionButton(messages.actions.remove, () => {
        if (window.confirm(messages.model.remove_confirm)) {
          manager.start("remove");
        }
      }));
      return;
    }
    const installLabel = operation.state === "failed" ? messages.actions.retry : messages.actions.install;
    manager.actions.append(actionButton(installLabel, () => {
      if (window.confirm(messages.model.confirm_install)) {
        manager.start("install");
      }
    }));
    if (snapshot.verification.state === "present-unverified") {
      manager.actions.append(actionButton(messages.actions.verify, () => manager.start("verify")));
    }
  }

  async function decode(response) {
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(text(payload.detail && payload.detail.reason_code) || "model_request_rejected");
    }
    return payload;
  }

  function managerFor(root) {
    const manager = {
      root,
      locale: root.dataset.localModelLocale,
      inspect: root.querySelector("[data-local-model-inspect]"),
      details: root.querySelector("[data-local-model-details]"),
      status: root.querySelector("[data-local-model-status]"),
      fallback: root.querySelector("[data-local-model-fallback]"),
      disclosure: root.querySelector("[data-local-model-disclosure]"),
      actions: root.querySelector("[data-local-model-actions]"),
      copy: null,
      csrfToken: "",
      loading: false,
    };

    manager.ensureCopy = async () => {
      if (manager.copy) {
        return;
      }
      if (!copyUrl) {
        throw new Error("model_copy_unavailable");
      }
      const response = await fetch(copyUrl, { credentials: "same-origin" });
      if (!response.ok) {
        throw new Error("model_copy_unavailable");
      }
      const copy = await response.json();
      if (!copy || copy.locale !== manager.locale || !copy.messages || !copy.messages.model) {
        throw new Error("model_copy_unavailable");
      }
      manager.copy = copy;
    };

    manager.fail = (reasonCode) => {
      manager.details.hidden = false;
      manager.status.textContent = manager.copy
        ? `${manager.copy.messages.states.degraded.title} (${reasonCode})`
        : text(manager.fallback && manager.fallback.textContent);
      manager.actions.replaceChildren();
      manager.inspect.disabled = false;
    };

    manager.inspectStatus = async (polling) => {
      if (manager.loading) {
        return;
      }
      manager.loading = true;
      manager.inspect.disabled = true;
      try {
        await manager.ensureCopy();
        const response = await fetch(`${apiUrl}?locale=${encodeURIComponent(manager.locale)}`, {
          credentials: "same-origin",
          headers: { Accept: "application/json" },
        });
        const snapshot = await decode(response);
        manager.csrfToken = text(snapshot.csrf_token);
        render(manager, snapshot);
      } catch (error) {
        manager.fail(error instanceof Error ? error.message : "model_request_rejected");
      } finally {
        manager.loading = false;
        if (!polling) {
          manager.inspect.disabled = false;
        }
      }
    };

    manager.start = async (operation) => {
      const body = { api_version: 1, locale: manager.locale, csrf_token: manager.csrfToken };
      if (operation === "install") {
        body.confirm_install = true;
      } else if (operation === "remove") {
        body.confirm_remove = true;
      }
      manager.inspect.disabled = true;
      try {
        const response = await fetch(`${apiUrl}/${operation}`, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        });
        const result = await decode(response);
        manager.csrfToken = text(result.csrf_token);
        await manager.inspectStatus(true);
      } catch (error) {
        manager.fail(error instanceof Error ? error.message : "model_request_rejected");
      }
    };

    manager.cancel = async (operationId) => {
      manager.inspect.disabled = true;
      try {
        const response = await fetch(`${apiUrl}/cancel`, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            api_version: 1,
            locale: manager.locale,
            csrf_token: manager.csrfToken,
            operation_id: operationId,
          }),
        });
        const result = await decode(response);
        manager.csrfToken = text(result.csrf_token);
        await manager.inspectStatus(true);
      } catch (error) {
        manager.fail(error instanceof Error ? error.message : "model_request_rejected");
      }
    };

    manager.inspect.addEventListener("click", () => manager.inspectStatus(false));
    return manager;
  }

  document.querySelectorAll("[data-local-model-manager]").forEach(managerFor);
})();
