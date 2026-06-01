(() => {
    function resolveTheme(mode, themeMediaQuery) {
        if (mode === "light" || mode === "dark") return mode;
        return themeMediaQuery.matches ? "dark" : "light";
    }

    const localeResolutionRules = [
        { code: "en", fallback: "en", matches: ["en", "en-*"] },
        { code: "ru", fallback: "en", matches: ["ru", "ru-*"] },
        { code: "de", fallback: "en", matches: ["de", "de-*"] },
        { code: "zh-CN", fallback: "en", matches: ["zh-CN", "zh-Hans", "zh-Hans-*", "zh"] },
        { code: "fr", fallback: "en", matches: ["fr", "fr-*"] },
        { code: "es-ES", fallback: "en", matches: ["es-ES", "es", "es-*"] },
    ];

    function normalizeLanguageTag(languageTag) {
        return String(languageTag || "").trim().replace(/_/g, "-").toLowerCase();
    }

    function languageMatchesRule(languageTag, rule) {
        const normalizedTag = normalizeLanguageTag(languageTag);
        const normalizedRule = normalizeLanguageTag(rule);
        if (!normalizedTag || !normalizedRule) return false;
        if (normalizedRule.endsWith("-*")) {
            const prefix = normalizedRule.slice(0, -2);
            return normalizedTag.startsWith(`${prefix}-`);
        }
        return normalizedTag === normalizedRule;
    }

    function resolveTargetLanguage(languageTag) {
        const matchedRule = localeResolutionRules.find((localeRule) => (
            localeRule.matches.some((rule) => languageMatchesRule(languageTag, rule))
        ));
        return matchedRule ? matchedRule.code : "en";
    }

    function resolveAvailableLanguage(languageCode, availableLanguageModes) {
        if (!availableLanguageModes || availableLanguageModes.includes(languageCode)) {
            return languageCode;
        }
        const rule = localeResolutionRules.find((localeRule) => localeRule.code === languageCode);
        const fallback = rule ? rule.fallback : "en";
        if (availableLanguageModes.includes(fallback)) {
            return fallback;
        }
        return availableLanguageModes.includes("en") ? "en" : availableLanguageModes[0];
    }

    function resolveBrowserLanguage(navigatorRef = navigator, availableLanguageModes = null) {
        const languageCandidates = [
            ...(Array.isArray(navigatorRef.languages) ? navigatorRef.languages : []),
            navigatorRef.language,
        ].filter(Boolean);
        const activeLanguageModes = Array.isArray(availableLanguageModes)
            ? availableLanguageModes.filter((mode) => mode !== "system")
            : null;
        let fallbackLanguage = null;

        for (const languageTag of languageCandidates.length ? languageCandidates : ["en"]) {
            const targetLanguage = resolveTargetLanguage(languageTag);
            if (!activeLanguageModes || activeLanguageModes.includes(targetLanguage)) {
                return targetLanguage;
            }
            if (!fallbackLanguage) {
                fallbackLanguage = resolveAvailableLanguage(targetLanguage, activeLanguageModes);
            }
        }
        return fallbackLanguage || resolveAvailableLanguage("en", activeLanguageModes);
    }

    function updateThemeColorMeta(documentRef, resolvedTheme) {
        const metaThemeColor = documentRef.querySelector('meta[name="theme-color"]');
        if (!metaThemeColor) return;
        metaThemeColor.setAttribute("content", resolvedTheme === "dark" ? "#07111a" : "#f6efe4");
    }

    function syncThemeSensitiveControls(documentRef, resolvedTheme) {
        const isDark = resolvedTheme === "dark";
        const fieldBackground = isDark ? "rgba(15, 23, 42, 0.86)" : "rgba(255, 255, 255, 0.88)";
        const fieldBackgroundHover = isDark ? "rgba(15, 23, 42, 0.94)" : "rgba(255, 255, 255, 0.96)";
        const fieldBorder = isDark ? "rgba(148, 163, 184, 0.16)" : "rgba(15, 23, 42, 0.12)";
        const fieldColor = isDark ? "#f8fafc" : "#122033";
        const ghostBackground = isDark ? "rgba(15, 23, 42, 0.86)" : "rgba(248, 250, 252, 0.78)";
        const ghostBackgroundHover = isDark ? "rgba(30, 41, 59, 0.96)" : "rgba(255, 255, 255, 0.92)";
        const ghostBorder = isDark ? "rgba(148, 163, 184, 0.14)" : "rgba(148, 163, 184, 0.18)";
        const ghostColor = isDark ? "#e2e8f0" : "#122033";
        const selectArrow = isDark
            ? "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='none'%3E%3Cpath d='M5 7.5L10 12.5L15 7.5' stroke='%23cbd5e1' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E\")"
            : "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='none'%3E%3Cpath d='M5 7.5L10 12.5L15 7.5' stroke='%235d6b7f' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E\")";

        documentRef.querySelectorAll(".soft-input").forEach((input) => {
            input.style.background = fieldBackground;
            input.style.backgroundColor = fieldBackground;
            input.style.borderColor = fieldBorder;
            input.style.color = fieldColor;
            input.style.colorScheme = isDark ? "dark" : "light";
            input.dataset.themeHoverBackground = fieldBackgroundHover;
        });

        documentRef.querySelectorAll("select.soft-input").forEach((selectEl) => {
            selectEl.style.backgroundImage = selectArrow;
            selectEl.style.backgroundRepeat = "no-repeat";
            selectEl.style.backgroundPosition = "right 0.9rem center";
            selectEl.style.backgroundSize = "1rem";
        });

        documentRef.querySelectorAll(".ghost-button.soft-input").forEach((button) => {
            button.style.background = ghostBackground;
            button.style.backgroundColor = ghostBackground;
            button.style.borderColor = ghostBorder;
            button.style.color = ghostColor;
            button.style.colorScheme = isDark ? "dark" : "light";
            button.dataset.themeHoverBackground = ghostBackgroundHover;
        });
    }

    function libraryCountLabel(count, currentLang, translate = (_key, fallback) => fallback) {
        if (currentLang === "ru") {
            const mod10 = count % 10;
            const mod100 = count % 100;
            if (mod10 === 1 && mod100 !== 11) {
                return translate("profiles.library_count_one", "Профиль в библиотеке");
            }
            if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
                return translate("profiles.library_count_few", "Профиля в библиотеке");
            }
            return translate("profiles.library_count_many", "Профилей в библиотеке");
        }
        return count === 1
            ? translate("profiles.library_count_one", "Profile in library")
            : translate("profiles.library_count_many", "Profiles in library");
    }

    window.BPMProfilesPlatform = {
        resolveTheme,
        resolveBrowserLanguage,
        resolveTargetLanguage,
        updateThemeColorMeta,
        syncThemeSensitiveControls,
        libraryCountLabel,
    };
})();
