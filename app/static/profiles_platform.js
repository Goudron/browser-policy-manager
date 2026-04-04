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
            const mod10 = count % 10;
            const mod100 = count % 100;
            if (mod10 === 1 && mod100 !== 11) {
                return "Профиль в библиотеке";
            }
            if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
                return "Профиля в библиотеке";
            }
            return "Профилей в библиотеке";
        }
        return count === 1 ? "Profile in library" : "Profiles in library";
    }

    window.BPMProfilesPlatform = {
        resolveTheme,
        resolveBrowserLanguage,
        updateThemeColorMeta,
        libraryCountLabel,
    };
})();
