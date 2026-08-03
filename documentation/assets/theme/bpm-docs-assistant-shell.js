(() => {
  "use strict";

  function setupWidget(widget) {
    const toggle = widget.querySelector("[data-assistant-toggle]");
    const panel = widget.querySelector("[data-assistant-panel]");
    const collapse = widget.querySelector("[data-assistant-collapse]");
    if (!toggle || !panel || !collapse) {
      return;
    }

    const conversation = window.BPMDocumentationAssistantConversation;

    function setExpanded(expanded, restoreFocus, userInitiated) {
      widget.dataset.assistantExpanded = String(expanded);
      toggle.setAttribute("aria-expanded", String(expanded));
      panel.hidden = !expanded;
      if (conversation && typeof conversation.setExpanded === "function") {
        conversation.setExpanded(widget, expanded);
      }
      if (restoreFocus) {
        (expanded ? collapse : toggle).focus({ preventScroll: true });
      }
      if (userInitiated) {
        widget.dispatchEvent(new CustomEvent("bpm-documentation-assistant-toggle", {
          bubbles: false,
          detail: { expanded },
        }));
      }
    }

    const restored = conversation && typeof conversation.restore === "function" ? conversation.restore(widget) : null;
    if (restored) {
      setExpanded(restored.expanded, false);
    }
    toggle.addEventListener("click", () => setExpanded(panel.hidden, true, true));
    collapse.addEventListener("click", () => setExpanded(false, true, true));
    widget.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !panel.hidden) {
        event.preventDefault();
        setExpanded(false, true, true);
      }
    });
  }

  document.querySelectorAll("[data-documentation-assistant-widget]").forEach(setupWidget);
})();
