(function () {
    const documentRef = document;
    const htmlEl = documentRef.documentElement;
    const storageKey = "bpm-theme-mode";
    const savedMode = window.localStorage.getItem(storageKey) || "system";
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const resolvedTheme = savedMode === "system" ? (prefersDark ? "dark" : "light") : savedMode;

    htmlEl.dataset.themeMode = savedMode;
    htmlEl.dataset.theme = resolvedTheme;

    const metaThemeColor = documentRef.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
        metaThemeColor.setAttribute("content", resolvedTheme === "dark" ? "#07111a" : "#f6efe4");
    }
})();
