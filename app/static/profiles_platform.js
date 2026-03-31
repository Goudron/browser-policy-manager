(() => {
    function resolveTheme(mode, themeMediaQuery) {
        if (mode === "light" || mode === "dark") return mode;
        return themeMediaQuery.matches ? "dark" : "light";
    }

    function resolveBrowserLanguage(navigatorRef = navigator) {
        const preferred = (navigatorRef.languages && navigatorRef.languages[0]) || navigatorRef.language || "en";
        return preferred.toLowerCase().startsWith("ru") ? "ru" : "en";
    }

    function updateThemeColorMeta(documentRef, resolvedTheme) {
        const metaThemeColor = documentRef.querySelector('meta[name="theme-color"]');
        if (!metaThemeColor) return;
        metaThemeColor.setAttribute("content", resolvedTheme === "dark" ? "#07111a" : "#f6efe4");
    }

    function libraryCountLabel(count, currentLang) {
        if (currentLang === "ru") {
            return count === 1 ? "профиль в библиотеке" : "профилей в библиотеке";
        }
        return count === 1 ? "profile in library" : "profiles in library";
    }

    window.BPMProfilesPlatform = {
        resolveTheme,
        resolveBrowserLanguage,
        updateThemeColorMeta,
        libraryCountLabel,
    };
})();
