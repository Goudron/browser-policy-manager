(function () {
    const payloadEl = document.getElementById("profiles-initial-locale");
    const bodyEl = document.body;

    window.__BPM_INITIAL_LANG__ = bodyEl ? bodyEl.dataset.initialLang || document.documentElement.lang : document.documentElement.lang;
    window.__BPM_INITIAL_LOCALE__ = {};

    if (!payloadEl) {
        return;
    }

    const payloadText = payloadEl.textContent ? payloadEl.textContent.trim() : "";
    if (!payloadText) {
        return;
    }

    try {
        window.__BPM_INITIAL_LOCALE__ = JSON.parse(payloadText);
    } catch (_error) {
        window.__BPM_INITIAL_LOCALE__ = {};
    }
})();
