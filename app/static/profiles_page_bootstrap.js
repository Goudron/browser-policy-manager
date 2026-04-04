(function () {
    const payloadEl = document.getElementById("profiles-initial-locale");
    const bodyEl = document.body;
    function readPayloadText(element) {
        if (!element) {
            return "";
        }
        if ((element.tagName || "").toUpperCase() === "TEMPLATE") {
            return element.innerHTML ? element.innerHTML.trim() : "";
        }
        return element.textContent ? element.textContent.trim() : "";
    }

    window.__BPM_INITIAL_LANG__ = bodyEl ? bodyEl.dataset.initialLang || document.documentElement.lang : document.documentElement.lang;
    window.__BPM_INITIAL_LOCALE__ = {};

    if (!payloadEl) {
        return;
    }

    const payloadText = readPayloadText(payloadEl);
    if (!payloadText) {
        return;
    }

    try {
        window.__BPM_INITIAL_LOCALE__ = JSON.parse(payloadText);
    } catch (_error) {
        window.__BPM_INITIAL_LOCALE__ = {};
    }
})();
