(() => {
    function create({
        documentRef = document,
        elements = {},
        t,
        escapeHtml,
        readWizardSchemaSource,
        getActiveWizardSchemaVersion,
        wizardSchemaShellCatalog,
        wizardSchemaShellViews,
        managedExtensionProfiles = [],
        getManagedExtensionProfileById,
        getManagedExtensionField,
        getAuthenticationObjectSummary,
        formatAuthenticationObjectState,
        getCertificatesObjectSummary,
        formatCertificatesObjectState,
        getDnsOverHttpsObjectSummary,
        formatDnsOverHttpsObjectState,
        getWebsiteFilterObjectSummary,
        formatWebsiteFilterObjectState,
        getPermissionsObjectSummary,
        formatPermissionsObjectState,
        getCookiesObjectSummary,
        formatCookiesObjectState,
        getHandlersObjectSummary,
        formatHandlersObjectState,
        getUserMessagingObjectSummary,
        formatUserMessagingObjectState,
        findSettingsTarget,
        state = {},
    }) {
        const {
            validationPreviewEl,
            wizardExtensionSettingsCardEl,
            wizardSearchEngineListEl,
            wizardExtensionSummaryCuratedEl,
            wizardExtensionSummaryArbitraryEl,
            wizardExtensionSummaryCustomUrlsEl,
            wizardExtensionSummaryCuratedJumpEl,
            wizardExtensionSummaryArbitraryJumpEl,
            wizardExtensionSummaryCustomUrlsJumpEl,
            wizardNetworkSummaryAuthenticationEl,
            wizardNetworkSummaryCertificatesEl,
            wizardNetworkSummaryDnsEl,
            wizardNetworkSummaryWindowsSsoEl,
            wizardNetworkSummaryAuthenticationJumpEl,
            wizardNetworkSummaryCertificatesJumpEl,
            wizardNetworkSummaryDnsJumpEl,
            wizardNetworkSummaryWindowsSsoJumpEl,
            wizardHomeSummaryHomepageEl,
            wizardHomeSummaryOverridesEl,
            wizardHomeSummaryFirefoxHomeEl,
            wizardHomeSummaryUserMessagingEl,
            wizardHomeSummaryHomepageJumpEl,
            wizardHomeSummaryOverridesJumpEl,
            wizardHomeSummaryFirefoxHomeJumpEl,
            wizardHomeSummaryUserMessagingJumpEl,
            wizardSearchSummaryDefaultsEl,
            wizardSearchSummaryHiddenEl,
            wizardSearchSummaryCustomEl,
            wizardSearchSummarySuggestEl,
            wizardSearchSummaryDefaultsJumpEl,
            wizardSearchSummaryHiddenJumpEl,
            wizardSearchSummaryCustomJumpEl,
            wizardSearchSummarySuggestJumpEl,
            wizardBookmarkSummaryLinksEl,
            wizardBookmarkSummaryFoldersEl,
            wizardBookmarkSummaryNestedEl,
            wizardBookmarkSummaryLinksJumpEl,
            wizardBookmarkSummaryFoldersJumpEl,
            wizardBookmarkSummaryNestedJumpEl,
            wizardAiSummaryAvailabilityEl,
            wizardAiSummaryProvidersEl,
            wizardAiSummarySurfacesEl,
            wizardAiSummaryAvailabilityJumpEl,
            wizardAiSummaryProvidersJumpEl,
            wizardAiSummarySurfacesJumpEl,
            wizardWebsiteAccessSummaryBlockedEl,
            wizardWebsiteAccessSummaryExceptionsEl,
            wizardWebsiteAccessSummaryHandlersEl,
            wizardWebsiteAccessSummaryBlockedJumpEl,
            wizardWebsiteAccessSummaryExceptionsJumpEl,
            wizardWebsiteAccessSummaryHandlersJumpEl,
            wizardPrivacySummaryPermissionsConfiguredEl,
            wizardPrivacySummaryPermissionsLockedEl,
            wizardPrivacySummaryCookiesEl,
            wizardPrivacySummaryPermissionsConfiguredJumpEl,
            wizardPrivacySummaryPermissionsLockedJumpEl,
            wizardPrivacySummaryCookiesJumpEl,
            wizardPrivacyUserDataSectionStatusEl,
            wizardLockdownSectionStatusEl,
            wizardPrivacySiteSectionStatusEl,
            wizardExportProfileStateEl,
            wizardExportWorkspaceStateEl,
            wizardExportValidationStateEl,
            wizardExportReadyStateEl,
            wizardExportPolicyCountEl,
            wizardExportPreferencesCountEl,
            wizardExportRawCountEl,
            wizardExportDeprecatedCountEl,
            wizardExportUnknownCountEl,
            wizardExportRawJumpEl,
            wizardExportDeprecatedJumpEl,
            wizardExportUnknownJumpEl,
            wizardExportReadyCopyEl,
            wizardExportChecklistEl,
            wizardExportSummaryNetworkEl,
            wizardExportSummaryHomeEl,
            wizardExportSummarySearchEl,
            wizardExportSummaryFeaturesEl,
            wizardExportSummaryAiEl,
            wizardExportSummaryPrivacyEl,
            wizardExportSummaryNetworkJumpEl,
            wizardExportSummaryHomeJumpEl,
            wizardExportSummarySearchJumpEl,
            wizardExportSummaryFeaturesJumpEl,
            wizardExportSummaryAiJumpEl,
            wizardExportSummaryPrivacyJumpEl,
            editorEl,
            overviewPanelEl,
        } = elements;

        const getCurrentId = state.getCurrentId || (() => null);
        const getCurrentProfile = state.getCurrentProfile || (() => null);
        const getCurrentRaw = state.getCurrentRaw || (() => ({}));
        const getValidationPreviewTone = state.getValidationPreviewTone || (() => "neutral");
        const workspaceSignalEl = state.workspaceSignalEl || null;

        function setText(el, value) {
            if (el) {
                el.textContent = String(value);
            }
        }

        function formatHttpsOnlyModeLabel(value) {
            if (value === "allowed") {
                return t("profiles.wizard_https_only_mode_allowed");
            }
            if (value === "disallowed") {
                return t("profiles.wizard_https_only_mode_disallowed");
            }
            if (value === "enabled") {
                return t("profiles.wizard_https_only_mode_enabled");
            }
            if (value === "force_enabled") {
                return t("profiles.wizard_https_only_mode_force_enabled");
            }
            return value;
        }

        function setSummaryTone(el, tone = "") {
            const row = el?.closest(".wizard-summary-row");
            if (!row) return;
            if (!tone) {
                delete row.dataset.summaryTone;
                return;
            }
            row.dataset.summaryTone = tone;
        }

        function setSummaryValue(el, value, tone = "") {
            setText(el, value);
            setSummaryTone(el, tone);
        }

        function hasMeaningfulValue(value) {
            if (typeof value === "boolean" || typeof value === "number") return true;
            if (typeof value === "string") return value.trim().length > 0;
            if (Array.isArray(value)) return value.some((entry) => hasMeaningfulValue(entry));
            if (value && typeof value === "object") return Object.values(value).some((entry) => hasMeaningfulValue(entry));
            return false;
        }

        function countConfiguredObjectEntries(value) {
            const currentObject = value && typeof value === "object" && !Array.isArray(value) ? value : {};
            return Object.values(currentObject).filter((entry) => hasMeaningfulValue(entry)).length;
        }

        function formatCountText(key, count) {
            return t(key).replace("{count}", String(count));
        }

        function buildHumanSummaryText(fragments) {
            return fragments.length
                ? fragments.join("; ")
                : t("profiles.wizard_export_guided_empty");
        }

        function buildCompactStateText(fragments, emptyKey = "profiles.wizard_review_default") {
            return fragments.length ? fragments.join(" • ") : t(emptyKey);
        }

        function formatCountLabel(key, count) {
            return t(key).replace("{count}", String(count));
        }

        function formatHomepageStartPageLabel(value) {
            if (value === "none") return t("profiles.wizard_homepage_start_none");
            if (value === "homepage") return t("profiles.wizard_homepage_start_homepage");
            if (value === "previous-session") return t("profiles.wizard_homepage_start_previous");
            if (value === "homepage-locked") return t("profiles.wizard_homepage_start_locked");
            return value;
        }

        function formatSearchBarLabel(value) {
            if (value === "unified") return t("profiles.wizard_search_bar_unified");
            if (value === "separate") return t("profiles.wizard_search_bar_separate");
            return value;
        }

        function buildFirefoxHomeDecisionFragments(summary) {
            const visible = [];
            const hidden = [];
            [
                [summary.firefoxHomeSearchValue, t("profiles.wizard_firefox_home_search_label")],
                [summary.firefoxHomeTopSitesValue, t("profiles.wizard_firefox_home_top_sites_label")],
                [summary.firefoxHomePocketValue, t("profiles.wizard_firefox_home_pocket_label")],
            ].forEach(([value, label]) => {
                if (value === true) visible.push(label);
                if (value === false) hidden.push(label);
            });

            const parts = [];
            if (visible.length) {
                parts.push(
                    t("profiles.wizard_review_firefox_home_visible")
                        .replace("{value}", visible.join(", ")),
                );
            }
            if (hidden.length) {
                parts.push(
                    t("profiles.wizard_review_firefox_home_hidden")
                        .replace("{value}", hidden.join(", ")),
                );
            }
            if (summary.firefoxHomeSecondaryRules > 0) {
                parts.push(
                    t("profiles.wizard_review_firefox_home_more")
                        .replace("{count}", String(summary.firefoxHomeSecondaryRules)),
                );
            }
            if (summary.firefoxHomeLocked) {
                parts.push(t("profiles.wizard_review_locked"));
            }
            return parts;
        }

        function formatBooleanManagedValue(value) {
            if (value === true) return t("profiles.wizard_review_enabled");
            if (value === false) return t("profiles.wizard_review_disabled");
            return t("profiles.wizard_review_default");
        }

        function getExtensionReviewSummaryData(parsed) {
            const extensionSettings = parsed?.ExtensionSettings && typeof parsed.ExtensionSettings === "object"
                ? parsed.ExtensionSettings
                : {};
            const curatedIds = new Set(managedExtensionProfiles.map((profile) => profile.id));
            const curatedProfiles = managedExtensionProfiles.reduce((count, profile) => {
                const settings = extensionSettings[profile.id];
                if (settings && typeof settings === "object" && !Array.isArray(settings) && Object.keys(settings).length > 0) {
                    return count + 1;
                }
                return count;
            }, 0);

            let arbitraryRules = 0;
            let customInstallUrls = 0;

            Object.entries(extensionSettings).forEach(([entryKey, entryValue]) => {
                if (!entryValue || typeof entryValue !== "object" || Array.isArray(entryValue) || Object.keys(entryValue).length === 0) {
                    return;
                }
                if (entryKey !== "*" && !curatedIds.has(entryKey)) {
                    arbitraryRules += 1;
                }

                const installUrl = typeof entryValue.install_url === "string" ? entryValue.install_url.trim() : "";
                if (!installUrl) return;

                const managedProfile = getManagedExtensionProfileById(entryKey);
                if (!managedProfile || installUrl !== managedProfile.defaultUrl) {
                    customInstallUrls += 1;
                }
            });

            return {
                curatedProfiles,
                arbitraryRules,
                customInstallUrls,
            };
        }

        function findExtensionReviewTarget(kind) {
            if (kind === "curated") {
                for (const profile of managedExtensionProfiles) {
                    const modeEl = getManagedExtensionField(profile.id, "mode");
                    const cardEl = modeEl?.closest(".wizard-section-group");
                    if (cardEl?.dataset.extensionProfileState && cardEl.dataset.extensionProfileState !== "missing") {
                        return cardEl;
                    }
                }
                return findSettingsTarget("field:extension-profile-ublock");
            }

            if (kind === "arbitrary") {
                return wizardExtensionSettingsCardEl?.querySelector('[data-extension-settings-row-kind="arbitrary"]')
                    || wizardExtensionSettingsCardEl;
            }

            if (kind === "custom_urls") {
                for (const profile of managedExtensionProfiles) {
                    const modeEl = getManagedExtensionField(profile.id, "mode");
                    const cardEl = modeEl?.closest(".wizard-section-group");
                    if (cardEl?.dataset.extensionProfileState === "custom_url") {
                        return cardEl;
                    }
                }
                return wizardExtensionSettingsCardEl?.querySelector('[data-extension-settings-row-state="custom_url"]')
                    || wizardExtensionSettingsCardEl;
            }

            return null;
        }

        function renderExtensionReviewJumpButtons(summary) {
            [
                { el: wizardExtensionSummaryCuratedJumpEl, count: summary.curatedProfiles, kind: "curated" },
                { el: wizardExtensionSummaryArbitraryJumpEl, count: summary.arbitraryRules, kind: "arbitrary" },
                { el: wizardExtensionSummaryCustomUrlsJumpEl, count: summary.customInstallUrls, kind: "custom_urls" },
            ].forEach(({ el, count, kind }) => {
                if (!el) return;
                el.disabled = !count || !findExtensionReviewTarget(kind);
            });
        }

        function renderExtensionReviewSummary(parsed) {
            const summary = getExtensionReviewSummaryData(parsed);
            setSummaryValue(
                wizardExtensionSummaryCuratedEl,
                summary.curatedProfiles,
                summary.curatedProfiles > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardExtensionSummaryArbitraryEl,
                summary.arbitraryRules,
                summary.arbitraryRules > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardExtensionSummaryCustomUrlsEl,
                summary.customInstallUrls,
                summary.customInstallUrls > 0 ? "active" : "default",
            );
            renderExtensionReviewJumpButtons(summary);
        }

        function getNetworkReviewSummaryData(parsed) {
            const authentication = getAuthenticationObjectSummary(parsed?.Authentication, []);
            const certificates = getCertificatesObjectSummary(parsed?.Certificates, []);
            const dnsOverHttps = getDnsOverHttpsObjectSummary(parsed?.DNSOverHTTPS, []);
            const windowsSsoExplicit = typeof parsed?.WindowsSSO === "boolean" ? 1 : 0;
            const windowsSsoValue = typeof parsed?.WindowsSSO === "boolean" ? parsed.WindowsSSO : null;

            return {
                authentication,
                certificates,
                dnsOverHttps,
                authenticationControls: authentication.configuredControls,
                certificateEntries: certificates.configuredEntries,
                dnsEntries: dnsOverHttps.configuredEntries,
                windowsSsoExplicit,
                windowsSsoValue,
            };
        }

        function findNetworkReviewTarget(kind) {
            const authenticationCardEl = documentRef.querySelector('[data-schema-policy-id="Authentication"][data-schema-policy-kind="object-card"]');
            const certificatesCardEl = documentRef.querySelector('[data-schema-policy-id="Certificates"][data-schema-policy-kind="object-card"]');
            const dnsOverHttpsCardEl = documentRef.querySelector('[data-schema-policy-id="DNSOverHTTPS"][data-schema-policy-kind="object-card"]');
            const windowsSsoCardEl = documentRef.querySelector('[data-schema-policy-id="WindowsSSO"][data-schema-policy-kind="boolean-select"]');

            if (kind === "authentication") {
                return authenticationCardEl || findSettingsTarget("shell-policy:2:Authentication");
            }
            if (kind === "certificates") {
                return certificatesCardEl || findSettingsTarget("shell-policy:2:Certificates");
            }
            if (kind === "dns") {
                return dnsOverHttpsCardEl || findSettingsTarget("shell-policy:2:DNSOverHTTPS");
            }
            if (kind === "windows_sso") {
                return windowsSsoCardEl || findSettingsTarget("shell-policy:2:WindowsSSO");
            }
            return null;
        }

        function renderNetworkReviewJumpButtons(summary) {
            [
                { el: wizardNetworkSummaryAuthenticationJumpEl, count: summary.authenticationControls, kind: "authentication" },
                { el: wizardNetworkSummaryCertificatesJumpEl, count: summary.certificateEntries, kind: "certificates" },
                { el: wizardNetworkSummaryDnsJumpEl, count: summary.dnsEntries, kind: "dns" },
                { el: wizardNetworkSummaryWindowsSsoJumpEl, count: summary.windowsSsoExplicit, kind: "windows_sso" },
            ].forEach(({ el, count, kind }) => {
                if (!el) return;
                el.disabled = !count || !findNetworkReviewTarget(kind);
            });
        }

        function renderNetworkReviewSummary(parsed) {
            const summary = getNetworkReviewSummaryData(parsed);
            setSummaryValue(
                wizardNetworkSummaryAuthenticationEl,
                formatAuthenticationObjectState(summary.authentication),
                summary.authenticationControls > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardNetworkSummaryCertificatesEl,
                formatCertificatesObjectState(summary.certificates),
                summary.certificateEntries > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardNetworkSummaryDnsEl,
                formatDnsOverHttpsObjectState(summary.dnsOverHttps),
                summary.dnsEntries > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardNetworkSummaryWindowsSsoEl,
                formatBooleanManagedValue(summary.windowsSsoValue),
                summary.windowsSsoExplicit > 0 ? "active" : "default",
            );
            renderNetworkReviewJumpButtons(summary);
        }

        function getHomeReviewSummaryData(parsed) {
            const homepage = parsed?.Homepage && typeof parsed.Homepage === "object" && !Array.isArray(parsed.Homepage)
                ? parsed.Homepage
                : {};
            const firefoxHome = parsed?.FirefoxHome && typeof parsed.FirefoxHome === "object" && !Array.isArray(parsed.FirefoxHome)
                ? parsed.FirefoxHome
                : {};
            const userMessaging = getUserMessagingObjectSummary(parsed?.UserMessaging, []);
            const additionalCount = Array.isArray(homepage.Additional) ? homepage.Additional.length : 0;
            const showCount = Object.entries(firefoxHome).filter(([, value]) => value === true).length;
            const hideCount = Object.entries(firefoxHome).filter(([, value]) => value === false).length;
            const firefoxHomeSecondaryRules = [
                "SponsoredTopSites",
                "Highlights",
                "Stories",
                "SponsoredPocket",
                "SponsoredStories",
                "Snippets",
            ].filter((key) => typeof firefoxHome[key] === "boolean").length;

            const homepageUrl = typeof homepage.URL === "string" ? homepage.URL.trim() : "";
            const startPage = typeof homepage.StartPage === "string" ? homepage.StartPage.trim() : "";
            const homepageControls = (homepageUrl ? 1 : 0)
                + additionalCount
                + (startPage ? 1 : 0)
                + (homepage.Locked === true ? 1 : 0);
            const newTabManaged = typeof parsed?.NewTabPage === "boolean";
            const overrideFirstRunPage = typeof parsed?.OverrideFirstRunPage === "string" ? parsed.OverrideFirstRunPage.trim() : "";
            const overridePostUpdatePage = typeof parsed?.OverridePostUpdatePage === "string" ? parsed.OverridePostUpdatePage.trim() : "";
            const overrideSurfaces = (newTabManaged ? 1 : 0)
                + (overrideFirstRunPage ? 1 : 0)
                + (overridePostUpdatePage ? 1 : 0);
            const firefoxHomeManaged = showCount + hideCount + firefoxHomeSecondaryRules + (firefoxHome.Locked === true ? 1 : 0);

            return {
                homepageUrl,
                additionalCount,
                startPage,
                homepageLocked: homepage.Locked === true,
                newTabManaged,
                newTabValue: typeof parsed?.NewTabPage === "boolean" ? parsed.NewTabPage : null,
                overrideFirstRunPage,
                overridePostUpdatePage,
                firefoxHomeShowCount: showCount,
                firefoxHomeHideCount: hideCount,
                firefoxHomeSearchValue: typeof firefoxHome.Search === "boolean" ? firefoxHome.Search : null,
                firefoxHomeTopSitesValue: typeof firefoxHome.TopSites === "boolean" ? firefoxHome.TopSites : null,
                firefoxHomePocketValue: typeof firefoxHome.Pocket === "boolean" ? firefoxHome.Pocket : null,
                firefoxHomeSecondaryRules,
                firefoxHomeLocked: firefoxHome.Locked === true,
                homepageControls,
                overrideSurfaces,
                firefoxHomeManaged,
                userMessagingControls: userMessaging.configuredSurfaces,
                userMessaging,
            };
        }

        function formatHomepageReviewValue(summary) {
            const parts = [];
            if (summary.homepageUrl) {
                parts.push(t("profiles.wizard_review_homepage_set"));
            }
            if (summary.additionalCount > 0) {
                parts.push(formatCountLabel("profiles.wizard_review_extra_tabs", summary.additionalCount));
            }
            if (summary.startPage) {
                parts.push(
                    t("profiles.wizard_review_start_page")
                        .replace("{value}", formatHomepageStartPageLabel(summary.startPage)),
                );
            }
            if (summary.homepageLocked) {
                parts.push(t("profiles.wizard_review_locked"));
            }
            return buildCompactStateText(parts);
        }

        function formatHomeOverridesReviewValue(summary) {
            const parts = [];
            if (summary.newTabManaged) {
                parts.push(
                    summary.newTabValue === true
                        ? t("profiles.wizard_review_new_tab_enabled")
                        : t("profiles.wizard_review_new_tab_disabled"),
                );
            }
            if (summary.overrideFirstRunPage) {
                parts.push(t("profiles.wizard_review_first_run_page"));
            }
            if (summary.overridePostUpdatePage) {
                parts.push(t("profiles.wizard_review_post_update_page"));
            }
            return buildCompactStateText(parts);
        }

        function formatFirefoxHomeReviewValue(summary) {
            if (!summary.firefoxHomeManaged) {
                return t("profiles.wizard_review_default");
            }
            return buildCompactStateText(buildFirefoxHomeDecisionFragments(summary));
        }

        function findHomeReviewTarget(kind) {
            const userMessagingCardEl = documentRef.querySelector('[data-schema-policy-id="UserMessaging"][data-schema-policy-kind="object-card"]');

            if (kind === "homepage") {
                return findSettingsTarget("field:wizard-homepage-url");
            }
            if (kind === "overrides") {
                return findSettingsTarget("field:wizard-override-first-run")
                    || findSettingsTarget("field:wizard-new-tab-page");
            }
            if (kind === "firefox_home") {
                return findSettingsTarget("field:firefox-home-search");
            }
            if (kind === "user_messaging") {
                return userMessagingCardEl || findSettingsTarget("shell-policy:3:UserMessaging");
            }
            return null;
        }

        function renderHomeReviewJumpButtons(summary) {
            [
                { el: wizardHomeSummaryHomepageJumpEl, count: summary.homepageControls, kind: "homepage" },
                { el: wizardHomeSummaryOverridesJumpEl, count: summary.overrideSurfaces, kind: "overrides" },
                { el: wizardHomeSummaryFirefoxHomeJumpEl, count: summary.firefoxHomeManaged, kind: "firefox_home" },
                { el: wizardHomeSummaryUserMessagingJumpEl, count: summary.userMessagingControls, kind: "user_messaging" },
            ].forEach(({ el, count, kind }) => {
                if (!el) return;
                el.disabled = !count || !findHomeReviewTarget(kind);
            });
        }

        function renderHomeReviewSummary(parsed) {
            const summary = getHomeReviewSummaryData(parsed);
            setSummaryValue(
                wizardHomeSummaryHomepageEl,
                formatHomepageReviewValue(summary),
                summary.homepageControls > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardHomeSummaryOverridesEl,
                formatHomeOverridesReviewValue(summary),
                summary.overrideSurfaces > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardHomeSummaryFirefoxHomeEl,
                formatFirefoxHomeReviewValue(summary),
                summary.firefoxHomeManaged > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardHomeSummaryUserMessagingEl,
                formatUserMessagingObjectState(summary.userMessaging),
                summary.userMessagingControls > 0 ? "active" : "default",
            );
            renderHomeReviewJumpButtons(summary);
        }

        function getSearchReviewSummaryData(parsed) {
            const searchEngines = parsed?.SearchEngines && typeof parsed.SearchEngines === "object" && !Array.isArray(parsed.SearchEngines)
                ? parsed.SearchEngines
                : {};
            const firefoxSuggest = parsed?.FirefoxSuggest && typeof parsed.FirefoxSuggest === "object" && !Array.isArray(parsed.FirefoxSuggest)
                ? parsed.FirefoxSuggest
                : {};

            const defaultControls = (typeof parsed?.SearchBar === "string" && parsed.SearchBar.trim() ? 1 : 0)
                + (typeof parsed?.SearchSuggestEnabled === "boolean" ? 1 : 0)
                + (typeof searchEngines.Default === "string" && searchEngines.Default.trim() ? 1 : 0)
                + (typeof searchEngines.PreventInstalls === "boolean" ? 1 : 0);
            const hiddenEngines = Array.isArray(searchEngines.Remove) ? searchEngines.Remove.length : 0;
            const customEngines = Array.isArray(searchEngines.Add) ? searchEngines.Add.length : 0;
            const suggestEnabledCount = Object.values(firefoxSuggest).filter((value) => value === true).length;
            const suggestDisabledCount = Object.values(firefoxSuggest).filter((value) => value === false).length;
            const suggestControls = suggestEnabledCount + suggestDisabledCount;

            return {
                searchBarValue: typeof parsed?.SearchBar === "string" ? parsed.SearchBar.trim() : "",
                searchSuggestEnabledValue: typeof parsed?.SearchSuggestEnabled === "boolean" ? parsed.SearchSuggestEnabled : null,
                defaultEngine: typeof searchEngines.Default === "string" ? searchEngines.Default.trim() : "",
                preventInstallsValue: typeof searchEngines.PreventInstalls === "boolean" ? searchEngines.PreventInstalls : null,
                webSuggestionsValue: typeof firefoxSuggest.WebSuggestions === "boolean" ? firefoxSuggest.WebSuggestions : null,
                sponsoredSuggestionsValue: typeof firefoxSuggest.SponsoredSuggestions === "boolean" ? firefoxSuggest.SponsoredSuggestions : null,
                improveSuggestValue: typeof firefoxSuggest.ImproveSuggest === "boolean" ? firefoxSuggest.ImproveSuggest : null,
                lockedValue: typeof firefoxSuggest.Locked === "boolean" ? firefoxSuggest.Locked : null,
                defaultControls,
                hiddenEngines,
                customEngines,
                suggestControls,
                suggestEnabledCount,
                suggestDisabledCount,
            };
        }

        function formatSearchDefaultsReviewValue(summary) {
            const parts = [];
            if (summary.defaultEngine) {
                parts.push(
                    t("profiles.wizard_review_default_engine")
                        .replace("{value}", summary.defaultEngine),
                );
            }
            if (summary.searchBarValue) {
                parts.push(
                    t("profiles.wizard_review_search_bar")
                        .replace("{value}", formatSearchBarLabel(summary.searchBarValue)),
                );
            }
            if (summary.searchSuggestEnabledValue === true) {
                parts.push(t("profiles.wizard_review_search_suggestions_on"));
            } else if (summary.searchSuggestEnabledValue === false) {
                parts.push(t("profiles.wizard_review_search_suggestions_off"));
            }
            if (summary.preventInstallsValue === true) {
                parts.push(t("profiles.wizard_review_search_engine_installs_blocked"));
            } else if (summary.preventInstallsValue === false) {
                parts.push(t("profiles.wizard_review_search_engine_installs_allowed"));
            }
            return buildCompactStateText(parts);
        }

        function formatHiddenEnginesReviewValue(summary) {
            return summary.hiddenEngines > 0
                ? formatCountLabel("profiles.wizard_review_hidden_engines", summary.hiddenEngines)
                : t("profiles.wizard_review_default");
        }

        function formatCustomEnginesReviewValue(summary) {
            return summary.customEngines > 0
                ? formatCountLabel("profiles.wizard_review_managed_engines", summary.customEngines)
                : t("profiles.wizard_review_default");
        }

        function formatSearchSuggestReviewValue(summary) {
            if (!summary.suggestControls) {
                return t("profiles.wizard_review_default");
            }
            const parts = [];
            if (summary.webSuggestionsValue === true) {
                parts.push(t("profiles.wizard_review_firefox_suggest_web_on"));
            } else if (summary.webSuggestionsValue === false) {
                parts.push(t("profiles.wizard_review_firefox_suggest_web_off"));
            }
            if (summary.sponsoredSuggestionsValue === true) {
                parts.push(t("profiles.wizard_review_firefox_suggest_sponsored_on"));
            } else if (summary.sponsoredSuggestionsValue === false) {
                parts.push(t("profiles.wizard_review_firefox_suggest_sponsored_off"));
            }
            if (summary.improveSuggestValue === true) {
                parts.push(t("profiles.wizard_review_firefox_suggest_improve_on"));
            } else if (summary.improveSuggestValue === false) {
                parts.push(t("profiles.wizard_review_firefox_suggest_improve_off"));
            }
            if (summary.lockedValue === true) {
                parts.push(t("profiles.wizard_review_locked"));
            }
            return buildCompactStateText(parts);
        }

        function findSearchReviewTarget(kind) {
            if (kind === "defaults") {
                return findSettingsTarget("field:wizard-search-default-engine")
                    || findSettingsTarget("field:wizard-search-bar");
            }
            if (kind === "hidden") {
                return findSettingsTarget("field:wizard-search-remove");
            }
            if (kind === "custom") {
                return wizardSearchEngineListEl || documentRef.getElementById("wizard-search-engine-add");
            }
            if (kind === "suggest") {
                return findSettingsTarget("field:firefox-suggest-web");
            }
            return null;
        }

        function renderSearchReviewJumpButtons(summary) {
            [
                { el: wizardSearchSummaryDefaultsJumpEl, count: summary.defaultControls, kind: "defaults" },
                { el: wizardSearchSummaryHiddenJumpEl, count: summary.hiddenEngines, kind: "hidden" },
                { el: wizardSearchSummaryCustomJumpEl, count: summary.customEngines, kind: "custom" },
                { el: wizardSearchSummarySuggestJumpEl, count: summary.suggestControls, kind: "suggest" },
            ].forEach(({ el, count, kind }) => {
                if (!el) return;
                el.disabled = !count || !findSearchReviewTarget(kind);
            });
        }

        function renderSearchReviewSummary(parsed) {
            const summary = getSearchReviewSummaryData(parsed);
            setSummaryValue(
                wizardSearchSummaryDefaultsEl,
                formatSearchDefaultsReviewValue(summary),
                summary.defaultControls > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardSearchSummaryHiddenEl,
                formatHiddenEnginesReviewValue(summary),
                summary.hiddenEngines > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardSearchSummaryCustomEl,
                formatCustomEnginesReviewValue(summary),
                summary.customEngines > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardSearchSummarySuggestEl,
                formatSearchSuggestReviewValue(summary),
                summary.suggestControls > 0 ? "active" : "default",
            );
            renderSearchReviewJumpButtons(summary);
        }

        function getBookmarkReviewSummaryData(parsed) {
            const bookmarkEntries = Array.isArray(parsed?.Bookmarks)
                ? parsed.Bookmarks.filter((item) => item && typeof item === "object" && !Array.isArray(item) && Object.keys(item).length > 0)
                : [];
            const managedFolders = Array.isArray(parsed?.ManagedBookmarks)
                ? parsed.ManagedBookmarks.filter((item) => item && typeof item === "object" && !Array.isArray(item) && Object.keys(item).length > 0)
                : [];
            const nestedRows = managedFolders.filter((item) => Array.isArray(item.children) && item.children.length > 0);

            return {
                bookmarkEntries: bookmarkEntries.length,
                managedFolders: managedFolders.length,
                nestedRows: nestedRows.length,
            };
        }

        function findBookmarkReviewTarget(kind) {
            const bookmarksCardEl = documentRef.querySelector('[data-schema-policy-id="Bookmarks"][data-schema-policy-kind="array-of-objects"]');
            const managedBookmarksCardEl = documentRef.querySelector('[data-schema-policy-id="ManagedBookmarks"][data-schema-policy-kind="array-of-objects"]');

            if (kind === "bookmarks") {
                return bookmarksCardEl?.querySelector('[data-schema-array-row-state="toolbar"], [data-schema-array-row-state="menu"], [data-schema-array-row-state="draft"]')
                    || bookmarksCardEl
                    || findSettingsTarget("shell-policy:6:Bookmarks");
            }
            if (kind === "managed") {
                return managedBookmarksCardEl?.querySelector('[data-schema-array-row-state="children"], [data-schema-array-row-state="name_only"], [data-schema-array-row-state="tree_only"], [data-schema-array-row-state="invalid"]')
                    || managedBookmarksCardEl
                    || findSettingsTarget("shell-policy:6:ManagedBookmarks");
            }
            if (kind === "nested") {
                return managedBookmarksCardEl?.querySelector('[data-schema-array-row-state="children"], [data-schema-array-row-state="tree_only"]')
                    || managedBookmarksCardEl
                    || findSettingsTarget("shell-policy:6:ManagedBookmarks");
            }
            return null;
        }

        function renderBookmarkReviewJumpButtons(summary) {
            [
                { el: wizardBookmarkSummaryLinksJumpEl, count: summary.bookmarkEntries, kind: "bookmarks" },
                { el: wizardBookmarkSummaryFoldersJumpEl, count: summary.managedFolders, kind: "managed" },
                { el: wizardBookmarkSummaryNestedJumpEl, count: summary.nestedRows, kind: "nested" },
            ].forEach(({ el, count, kind }) => {
                if (!el) return;
                el.disabled = !count || !findBookmarkReviewTarget(kind);
            });
        }

        function renderBookmarkReviewSummary(parsed) {
            const summary = getBookmarkReviewSummaryData(parsed);
            setSummaryValue(
                wizardBookmarkSummaryLinksEl,
                summary.bookmarkEntries > 0
                    ? formatCountLabel("profiles.wizard_review_bookmarks", summary.bookmarkEntries)
                    : t("profiles.wizard_review_default"),
                summary.bookmarkEntries > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardBookmarkSummaryFoldersEl,
                summary.managedFolders > 0
                    ? formatCountLabel("profiles.wizard_review_bookmark_folders", summary.managedFolders)
                    : t("profiles.wizard_review_default"),
                summary.managedFolders > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardBookmarkSummaryNestedEl,
                summary.nestedRows > 0
                    ? formatCountLabel("profiles.wizard_review_bookmark_nested", summary.nestedRows)
                    : t("profiles.wizard_review_default"),
                summary.nestedRows > 0 ? "active" : "default",
            );
            renderBookmarkReviewJumpButtons(summary);
        }

        function countHandlerRuleBucket(bucket) {
            return bucket && typeof bucket === "object" && !Array.isArray(bucket)
                ? Object.keys(bucket).filter(Boolean).length
                : 0;
        }

        function getWebsiteAccessReviewSummaryData(parsed) {
            const websiteFilter = parsed?.WebsiteFilter && typeof parsed.WebsiteFilter === "object" && !Array.isArray(parsed.WebsiteFilter)
                ? parsed.WebsiteFilter
                : {};
            const handlers = parsed?.Handlers && typeof parsed.Handlers === "object" && !Array.isArray(parsed.Handlers)
                ? parsed.Handlers
                : {};
            const websiteFilterSummary = getWebsiteFilterObjectSummary(websiteFilter, []);
            const handlersSummary = getHandlersObjectSummary(handlers, []);

            return {
                blockedSites: websiteFilterSummary.blockedCount,
                exceptions: websiteFilterSummary.exceptionCount,
                handlerRules: handlersSummary.totalRules,
                websiteFilterSummary,
                handlersSummary,
            };
        }

        function findWebsiteAccessReviewTarget(kind) {
            const websiteFilterCardEl = documentRef.querySelector('[data-schema-policy-id="WebsiteFilter"][data-schema-policy-kind="object-card"]');
            const handlersCardEl = documentRef.querySelector('[data-schema-policy-id="Handlers"][data-schema-policy-kind="object-card"]');

            if (kind === "blocked" || kind === "exceptions") {
                return websiteFilterCardEl || findSettingsTarget("shell-policy:6:WebsiteFilter");
            }
            if (kind === "handlers") {
                return handlersCardEl
                    || documentRef.querySelector('[data-wizard-shell-policy-id="Handlers"]')
                    || findSettingsTarget("shell-policy:6:Handlers");
            }
            return null;
        }

        function renderWebsiteAccessReviewJumpButtons(summary) {
            [
                { el: wizardWebsiteAccessSummaryBlockedJumpEl, count: summary.blockedSites, kind: "blocked" },
                { el: wizardWebsiteAccessSummaryExceptionsJumpEl, count: summary.exceptions, kind: "exceptions" },
                { el: wizardWebsiteAccessSummaryHandlersJumpEl, count: summary.handlerRules, kind: "handlers" },
            ].forEach(({ el, count, kind }) => {
                if (!el) return;
                el.disabled = !count || !findWebsiteAccessReviewTarget(kind);
            });
        }

        function renderWebsiteAccessReviewSummary(parsed) {
            const summary = getWebsiteAccessReviewSummaryData(parsed);
            setSummaryValue(
                wizardWebsiteAccessSummaryBlockedEl,
                summary.blockedSites > 0
                    ? formatCountLabel("profiles.wizard_review_blocked_sites_short", summary.blockedSites)
                    : t("profiles.wizard_review_default"),
                summary.blockedSites > 0 ? "strict" : "default",
            );
            setSummaryValue(
                wizardWebsiteAccessSummaryExceptionsEl,
                summary.exceptions > 0
                    ? formatCountLabel("profiles.wizard_review_allowed_exceptions_short", summary.exceptions)
                    : t("profiles.wizard_review_default"),
                summary.exceptions > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardWebsiteAccessSummaryHandlersEl,
                formatHandlersObjectState(summary.handlersSummary),
                summary.handlerRules > 0 ? "active" : "default",
            );
            renderWebsiteAccessReviewJumpButtons(summary);
        }

        function getAiReviewSummaryData(parsed) {
            const generativeAi = parsed?.GenerativeAI && typeof parsed.GenerativeAI === "object" && !Array.isArray(parsed.GenerativeAI)
                ? parsed.GenerativeAI
                : {};
            return {
                generativeAiControls: countConfiguredObjectEntries(generativeAi),
                visualSearchManaged: typeof parsed?.VisualSearchEnabled === "boolean",
                visualSearchEnabled: parsed?.VisualSearchEnabled === true,
            };
        }

        function findAiReviewTarget(kind) {
            const generativeAiCardEl = documentRef.querySelector('[data-schema-policy-id="GenerativeAI"][data-schema-policy-kind="object-card"]');
            const visualSearchCardEl = documentRef.querySelector('[data-schema-policy-id="VisualSearchEnabled"][data-schema-policy-kind="boolean-card"]')
                || documentRef.querySelector('[data-schema-policy-id="VisualSearchEnabled"][data-schema-policy-kind="object-card"]');

            if (kind === "availability") {
                return generativeAiCardEl
                    || findSettingsTarget("policy:GenerativeAI")
                    || findSettingsTarget("shell-policy:7:GenerativeAI");
            }
            if (kind === "providers") {
                return documentRef.getElementById("wizard-ai-providers-section-anchor")
                    || documentRef.getElementById("wizard-ai-providers-section-status")
                    || documentRef.getElementById("wizard-step-7");
            }
            if (kind === "surfaces") {
                return visualSearchCardEl
                    || findSettingsTarget("policy:VisualSearchEnabled")
                    || findSettingsTarget("shell-policy:7:VisualSearchEnabled");
            }
            return null;
        }

        function renderAiReviewJumpButtons(summary) {
            [
                { el: wizardAiSummaryAvailabilityJumpEl, enabled: summary.generativeAiControls > 0, kind: "availability" },
                { el: wizardAiSummaryProvidersJumpEl, enabled: true, kind: "providers" },
                { el: wizardAiSummarySurfacesJumpEl, enabled: summary.visualSearchManaged, kind: "surfaces" },
            ].forEach(({ el, enabled, kind }) => {
                if (!el) return;
                el.disabled = !enabled || !findAiReviewTarget(kind);
            });
        }

        function renderAiReviewSummary(parsed) {
            const summary = getAiReviewSummaryData(parsed);

            setSummaryValue(
                wizardAiSummaryAvailabilityEl,
                summary.generativeAiControls > 0
                    ? formatCountLabel("profiles.wizard_ai_review_availability_state", summary.generativeAiControls)
                    : t("profiles.wizard_review_default"),
                summary.generativeAiControls > 0 ? "active" : "default",
            );
            setSummaryValue(
                wizardAiSummaryProvidersEl,
                t("profiles.wizard_ai_review_providers_state_empty"),
                "default",
            );
            setSummaryValue(
                wizardAiSummarySurfacesEl,
                summary.visualSearchManaged
                    ? (
                        summary.visualSearchEnabled
                            ? t("profiles.wizard_ai_review_surfaces_on")
                            : t("profiles.wizard_ai_review_surfaces_off")
                    )
                    : t("profiles.wizard_review_default"),
                summary.visualSearchManaged ? "active" : "default",
            );

            renderAiReviewJumpButtons(summary);
        }

        function getPermissionCategorySummary(categoryValue) {
            const currentObject = categoryValue && typeof categoryValue === "object" && !Array.isArray(categoryValue) ? categoryValue : {};
            const allowCount = Array.isArray(currentObject.Allow) ? currentObject.Allow.length : 0;
            const blockCount = Array.isArray(currentObject.Block) ? currentObject.Block.length : 0;
            const blockNewRequests = currentObject.BlockNewRequests === true;
            const locked = currentObject.Locked === true;
            const hasDefault = typeof currentObject.Default === "string" && currentObject.Default.trim().length > 0;

            return {
                hasRules: allowCount > 0 || blockCount > 0 || blockNewRequests || locked || hasDefault,
                hasStrictControl: blockNewRequests || locked,
            };
        }

        function getCookiesReviewCount(cookiesValue) {
            const currentObject = cookiesValue && typeof cookiesValue === "object" && !Array.isArray(cookiesValue) ? cookiesValue : {};
            let count = 0;

            ["Allow", "AllowSession", "Block"].forEach((field) => {
                count += Array.isArray(currentObject[field]) ? currentObject[field].length : 0;
            });
            if (currentObject.Locked === true) count += 1;
            if (typeof currentObject.Behavior === "string" && currentObject.Behavior.trim()) count += 1;
            if (typeof currentObject.BehaviorPrivateBrowsing === "string" && currentObject.BehaviorPrivateBrowsing.trim()) count += 1;

            return count;
        }

        function getPrivacyReviewSummaryData(parsed) {
            const permissions = parsed?.Permissions && typeof parsed.Permissions === "object" && !Array.isArray(parsed.Permissions)
                ? parsed.Permissions
                : {};
            const permissionsSummary = getPermissionsObjectSummary(permissions, []);
            const cookiesSummary = getCookiesObjectSummary(parsed?.Cookies, []);

            let configuredPermissionCategories = 0;
            let lockedPermissionCategories = 0;

            Object.values(permissions).forEach((categoryValue) => {
                const summary = getPermissionCategorySummary(categoryValue);
                if (summary.hasRules) configuredPermissionCategories += 1;
                if (summary.hasStrictControl) lockedPermissionCategories += 1;
            });

            return {
                configuredPermissionCategories,
                lockedPermissionCategories,
                cookieRuleCount: getCookiesReviewCount(parsed?.Cookies),
                permissionsSummary,
                cookiesSummary,
            };
        }

        function getPrivacyUserDataSectionStatus(parsed) {
            const fragments = [];

            if (parsed?.DisableTelemetry === true) {
                fragments.push(t("profiles.wizard_privacy_section_state_telemetry"));
            }
            if (parsed?.DisableFirefoxStudies === true) {
                fragments.push(t("profiles.wizard_privacy_section_state_studies"));
            }
            if (parsed?.DisablePrivateBrowsing === true) {
                fragments.push(t("profiles.wizard_privacy_section_state_private_browsing"));
            }
            if (typeof parsed?.OfferToSaveLogins === "boolean") {
                fragments.push(
                    parsed.OfferToSaveLogins
                        ? t("profiles.wizard_privacy_section_state_logins_on")
                        : t("profiles.wizard_privacy_section_state_logins_off"),
                );
            }
            if (typeof parsed?.PasswordManagerEnabled === "boolean") {
                fragments.push(
                    parsed.PasswordManagerEnabled
                        ? t("profiles.wizard_privacy_section_state_password_manager_on")
                        : t("profiles.wizard_privacy_section_state_password_manager_off"),
                );
            }

            return fragments.length
                ? fragments.join(" • ")
                : t("profiles.wizard_privacy_section_state_empty");
        }

        function getLockdownSectionStatus(parsed) {
            const fragments = [];

            if (parsed?.BlockAboutConfig === true) {
                fragments.push(t("profiles.wizard_lockdown_section_state_about_config"));
            }
            if (parsed?.BlockAboutProfiles === true) {
                fragments.push(t("profiles.wizard_lockdown_section_state_about_profiles"));
            }
            if (parsed?.DisableDeveloperTools === true) {
                fragments.push(t("profiles.wizard_lockdown_section_state_devtools"));
            }
            if (parsed?.DisableBuiltinPDFViewer === true) {
                fragments.push(t("profiles.wizard_lockdown_section_state_pdf"));
            }
            if (typeof parsed?.HttpsOnlyMode === "string" && parsed.HttpsOnlyMode.trim()) {
                fragments.push(
                    t("profiles.wizard_lockdown_section_state_https_only")
                        .replace("{value}", formatHttpsOnlyModeLabel(parsed.HttpsOnlyMode.trim())),
                );
            }

            return fragments.length
                ? fragments.join(" • ")
                : t("profiles.wizard_lockdown_section_state_empty");
        }

        function getPrivacySiteSectionStatus(summary) {
            const fragments = [];

            if (summary.configuredPermissionCategories > 0) {
                fragments.push(
                    t("profiles.wizard_privacy_site_section_state_permissions")
                        .replace("{value}", formatPermissionsObjectState(summary.permissionsSummary)),
                );
            }
            if (summary.cookieRuleCount > 0) {
                fragments.push(
                    t("profiles.wizard_privacy_site_section_state_cookies")
                        .replace("{value}", formatCookiesObjectState(summary.cookiesSummary)),
                );
            }

            return fragments.length
                ? fragments.join(" • ")
                : t("profiles.wizard_privacy_site_section_state_empty");
        }

        function renderPrivacySectionStatuses(parsed, summary) {
            setText(wizardPrivacyUserDataSectionStatusEl, getPrivacyUserDataSectionStatus(parsed));
            setText(wizardLockdownSectionStatusEl, getLockdownSectionStatus(parsed));
            setText(wizardPrivacySiteSectionStatusEl, getPrivacySiteSectionStatus(summary));
        }

        function getFeatureReviewSummaryData(parsed) {
            const extensions = parsed?.Extensions && typeof parsed.Extensions === "object" && !Array.isArray(parsed.Extensions)
                ? parsed.Extensions
                : {};
            const extensionSettings = parsed?.ExtensionSettings && typeof parsed.ExtensionSettings === "object" && !Array.isArray(parsed.ExtensionSettings)
                ? parsed.ExtensionSettings
                : {};
            const requestedLocales = Array.isArray(parsed?.RequestedLocales)
                ? parsed.RequestedLocales.filter((entry) => typeof entry === "string" && entry.trim())
                : [];
            const generativeAi = parsed?.GenerativeAI && typeof parsed.GenerativeAI === "object" && !Array.isArray(parsed.GenerativeAI)
                ? parsed.GenerativeAI
                : {};
            const extensionReview = getExtensionReviewSummaryData(parsed);
            const websiteReview = getWebsiteAccessReviewSummaryData(parsed);
            const bookmarkReview = getBookmarkReviewSummaryData(parsed);

            return {
                accountsManaged: typeof parsed?.DisableFirefoxAccounts === "boolean" ? 1 : 0,
                accountsDisabled: parsed?.DisableFirefoxAccounts === true,
                requestedLocales: requestedLocales.length,
                translateManaged: typeof parsed?.TranslateEnabled === "boolean" ? 1 : 0,
                translateEnabled: parsed?.TranslateEnabled === true,
                visualSearchManaged: typeof parsed?.VisualSearchEnabled === "boolean" ? 1 : 0,
                visualSearchEnabled: parsed?.VisualSearchEnabled === true,
                generativeAiControls: countConfiguredObjectEntries(generativeAi),
                extensionReview,
                managedAddonControls: (Array.isArray(extensions.Install) ? extensions.Install.length : 0)
                    + (Array.isArray(extensions.Locked) ? extensions.Locked.length : 0)
                    + (Array.isArray(extensions.Uninstall) ? extensions.Uninstall.length : 0)
                    + (typeof extensionSettings["*"]?.installation_mode === "string" && extensionSettings["*"].installation_mode.trim() ? 1 : 0)
                    + extensionReview.curatedProfiles
                    + extensionReview.arbitraryRules,
                websiteHandlingRules: websiteReview.blockedSites + websiteReview.exceptions + websiteReview.handlerRules,
                bookmarkGroups: bookmarkReview.bookmarkEntries + bookmarkReview.managedFolders,
                websiteReview,
                bookmarkReview,
            };
        }

        function getExportGuidedSummaryData(parsed) {
            const proxyConfigured = countConfiguredObjectEntries(parsed?.Proxy) > 0;
            const network = getNetworkReviewSummaryData(parsed);
            const home = getHomeReviewSummaryData(parsed);
            const search = getSearchReviewSummaryData(parsed);
            const features = getFeatureReviewSummaryData(parsed);
            const privacy = getPrivacyReviewSummaryData(parsed);

            const networkFragments = [];
            if (proxyConfigured) {
                networkFragments.push(t("profiles.wizard_export_guided_network_proxy"));
            }
            if (network.dnsEntries > 0) {
                networkFragments.push(formatDnsOverHttpsObjectState(network.dnsOverHttps));
            }
            if (network.authenticationControls > 0) {
                networkFragments.push(formatAuthenticationObjectState(network.authentication));
            }
            if (network.certificateEntries > 0) {
                networkFragments.push(formatCertificatesObjectState(network.certificates));
            }
            if (network.windowsSsoExplicit > 0) {
                networkFragments.push(
                    network.windowsSsoValue === true
                        ? t("profiles.wizard_export_guided_network_sso_on")
                        : t("profiles.wizard_export_guided_network_sso_off"),
                );
            }

            const homeFragments = [];
            if (home.homepageControls > 0) {
                homeFragments.push(formatHomepageReviewValue(home));
            }
            if (home.overrideSurfaces > 0) {
                homeFragments.push(formatHomeOverridesReviewValue(home));
            }
            if (home.firefoxHomeManaged > 0) {
                homeFragments.push(formatFirefoxHomeReviewValue(home));
            }
            if (home.userMessagingControls > 0) {
                homeFragments.push(formatUserMessagingObjectState(home.userMessaging));
            }

            const searchFragments = [];
            if (search.defaultControls > 0) {
                searchFragments.push(formatSearchDefaultsReviewValue(search));
            }
            if (search.hiddenEngines > 0) {
                searchFragments.push(formatHiddenEnginesReviewValue(search));
            }
            if (search.customEngines > 0) {
                searchFragments.push(formatCustomEnginesReviewValue(search));
            }
            if (search.suggestControls > 0) {
                searchFragments.push(formatSearchSuggestReviewValue(search));
            }

            const featureFragments = [];
            if (features.accountsManaged > 0) {
                featureFragments.push(
                    features.accountsDisabled
                        ? t("profiles.wizard_export_guided_features_accounts_off")
                        : t("profiles.wizard_export_guided_features_accounts_on"),
                );
            }
            if (features.requestedLocales > 0) {
                featureFragments.push(formatCountText("profiles.wizard_export_guided_features_locales", features.requestedLocales));
            }
            if (features.translateManaged > 0) {
                featureFragments.push(
                    features.translateEnabled
                        ? t("profiles.wizard_export_guided_features_translate_on")
                        : t("profiles.wizard_export_guided_features_translate_off"),
                );
            }

            const aiFragments = [];
            if (features.visualSearchManaged > 0) {
                aiFragments.push(
                    features.visualSearchEnabled
                        ? t("profiles.wizard_export_guided_ai_visual_search_on")
                        : t("profiles.wizard_export_guided_ai_visual_search_off"),
                );
            }
            if (features.generativeAiControls > 0) {
                aiFragments.push(formatCountText("profiles.wizard_export_guided_ai_controls", features.generativeAiControls));
            }
            if (features.managedAddonControls > 0) {
                featureFragments.push(
                    buildCompactStateText([
                        features.extensionReview.curatedProfiles > 0
                            ? formatCountText("profiles.wizard_export_guided_features_addons_curated", features.extensionReview.curatedProfiles)
                            : "",
                        features.extensionReview.arbitraryRules > 0
                            ? formatCountText("profiles.wizard_export_guided_features_addons_arbitrary", features.extensionReview.arbitraryRules)
                            : "",
                        features.extensionReview.customInstallUrls > 0
                            ? formatCountText("profiles.wizard_export_guided_features_addons_urls", features.extensionReview.customInstallUrls)
                            : "",
                    ].filter(Boolean)),
                );
            }
            if (features.websiteHandlingRules > 0) {
                featureFragments.push(
                    buildCompactStateText([
                        features.websiteReview.blockedSites > 0
                            ? formatCountText("profiles.wizard_review_blocked_sites_short", features.websiteReview.blockedSites)
                            : "",
                        features.websiteReview.exceptions > 0
                            ? formatCountText("profiles.wizard_review_allowed_exceptions_short", features.websiteReview.exceptions)
                            : "",
                        features.websiteReview.handlerRules > 0
                            ? formatHandlersObjectState(features.websiteReview.handlersSummary)
                            : "",
                    ].filter(Boolean)),
                );
            }
            if (features.bookmarkGroups > 0) {
                featureFragments.push(
                    buildCompactStateText([
                        features.bookmarkReview.bookmarkEntries > 0
                            ? formatCountText("profiles.wizard_review_bookmarks", features.bookmarkReview.bookmarkEntries)
                            : "",
                        features.bookmarkReview.managedFolders > 0
                            ? formatCountText("profiles.wizard_review_bookmark_folders", features.bookmarkReview.managedFolders)
                            : "",
                    ].filter(Boolean)),
                );
            }

            const privacyFragments = [];
            if (privacy.configuredPermissionCategories > 0) {
                privacyFragments.push(formatPermissionsObjectState(privacy.permissionsSummary));
            }
            if (privacy.cookieRuleCount > 0) {
                privacyFragments.push(formatCookiesObjectState(privacy.cookiesSummary));
            }

            return {
                networkText: buildHumanSummaryText(networkFragments),
                homeText: buildHumanSummaryText(homeFragments),
                searchText: buildHumanSummaryText(searchFragments),
                featuresText: buildHumanSummaryText(featureFragments),
                aiText: buildHumanSummaryText(aiFragments),
                privacyText: buildHumanSummaryText(privacyFragments),
                networkTone: networkFragments.length ? "active" : "default",
                homeTone: homeFragments.length ? "active" : "default",
                searchTone: searchFragments.length ? "active" : "default",
                featuresTone: featureFragments.length ? "active" : "default",
                aiTone: aiFragments.length ? "active" : "default",
                privacyTone: (privacy.lockedPermissionCategories > 0 || privacy.cookiesSummary.state === "strict")
                    ? "strict"
                    : (privacyFragments.length ? "active" : "default"),
            };
        }

        function findPrivacyReviewTarget(kind) {
            const permissionsCardEl = documentRef.querySelector('[data-schema-policy-id="Permissions"][data-schema-policy-kind="object-card"]');
            const cookiesCardEl = documentRef.querySelector('[data-schema-policy-id="Cookies"][data-schema-policy-kind="object-card"]');

            if (kind === "permissions") {
                return permissionsCardEl
                    || documentRef.querySelector('[data-wizard-shell-policy-id="Permissions"]')
                    || findSettingsTarget("shell-policy:5:Permissions");
            }
            if (kind === "cookies") {
                return cookiesCardEl
                    || documentRef.querySelector('[data-wizard-shell-policy-id="Cookies"]')
                    || findSettingsTarget("shell-policy:5:Cookies");
            }
            return null;
        }

        function renderPrivacyReviewJumpButtons(summary) {
            [
                { el: wizardPrivacySummaryPermissionsConfiguredJumpEl, count: summary.configuredPermissionCategories, kind: "permissions" },
                { el: wizardPrivacySummaryPermissionsLockedJumpEl, count: summary.lockedPermissionCategories, kind: "permissions" },
                { el: wizardPrivacySummaryCookiesJumpEl, count: summary.cookieRuleCount, kind: "cookies" },
            ].forEach(({ el, count, kind }) => {
                if (!el) return;
                el.disabled = !count || !findPrivacyReviewTarget(kind);
            });
        }

        function renderPrivacyReviewSummary(parsed) {
            const summary = getPrivacyReviewSummaryData(parsed);
            renderPrivacySectionStatuses(parsed, summary);
            setSummaryValue(
                wizardPrivacySummaryPermissionsConfiguredEl,
                formatPermissionsObjectState(summary.permissionsSummary),
                summary.permissionsSummary.state === "strict"
                    ? "strict"
                    : (summary.configuredPermissionCategories > 0 ? "active" : "default"),
            );
            setSummaryValue(
                wizardPrivacySummaryPermissionsLockedEl,
                summary.lockedPermissionCategories > 0
                    ? formatCountLabel("profiles.wizard_review_strict_permission_areas", summary.lockedPermissionCategories)
                    : t("profiles.wizard_review_default"),
                summary.lockedPermissionCategories > 0 ? "strict" : "default",
            );
            setSummaryValue(
                wizardPrivacySummaryCookiesEl,
                formatCookiesObjectState(summary.cookiesSummary),
                summary.cookiesSummary.state === "strict"
                    ? "strict"
                    : (summary.cookieRuleCount > 0 ? "active" : "default"),
            );
            renderPrivacyReviewJumpButtons(summary);
        }

        function getActiveSchemaPolicyIndex() {
            const channelData = wizardSchemaShellCatalog.channels?.[getActiveWizardSchemaVersion()];
            const index = {};

            Object.values(channelData?.steps || {}).forEach((stepData) => {
                ["recommended", "additional", "raw_fallback"].forEach((bucketKey) => {
                    (stepData?.[bucketKey] || []).forEach((item) => {
                        index[item.id] = item;
                    });
                });
            });

            return index;
        }

        function getFinalExportSummaryData(parsed, dirty, invalid) {
            const policyIndex = getActiveSchemaPolicyIndex();
            const preferences = parsed?.Preferences && typeof parsed.Preferences === "object" && !Array.isArray(parsed.Preferences)
                ? parsed.Preferences
                : {};
            const topLevelKeys = Object.keys(parsed || {}).filter((key) => key !== "Preferences" && parsed[key] !== undefined);
            const rawFallbackKeys = [];
            const deprecatedKeys = [];
            const unknownKeys = [];

            topLevelKeys.forEach((key) => {
                const item = policyIndex[key];
                if (!item) {
                    unknownKeys.push(key);
                    return;
                }
                if (item.support_level === "fallback") {
                    rawFallbackKeys.push(key);
                }
                if (item.deprecated) {
                    deprecatedKeys.push(key);
                }
            });

            const currentId = getCurrentId();
            const currentProfile = getCurrentProfile();
            let profileState = t("profiles.wizard_export_profile_draft");
            let profileTone = "strict";
            if (currentId && currentProfile?.is_deleted) {
                profileState = t("profiles.wizard_export_profile_archived")
                    .replace("{id}", String(currentId));
                profileTone = "attention";
            } else if (currentId) {
                profileState = t("profiles.wizard_export_profile_saved")
                    .replace("{id}", String(currentId));
                profileTone = "ready";
            }

            const validationTone = getValidationPreviewTone();
            let validationState = "";
            let validationStateTone = "default";
            if (invalid) {
                validationState = t("profiles.wizard_export_validation_invalid");
                validationStateTone = "attention";
            } else if (validationTone === "error" || validationTone === "success") {
                validationState = validationPreviewEl?.textContent || "";
                validationStateTone = validationTone === "success" ? "ready" : "attention";
            } else {
                validationState = t("profiles.wizard_export_validation_pending");
            }

            let exportState = "";
            let exportReadyCopy = "";
            let exportTone = "attention";
            if (currentProfile?.is_deleted) {
                exportState = t("profiles.wizard_export_state_archived");
                exportReadyCopy = exportState;
            } else if (!currentId) {
                exportState = t("profiles.wizard_export_state_unsaved_new");
                exportReadyCopy = t("profiles.wizard_export_ready_create");
            } else if (invalid) {
                exportState = t("profiles.wizard_export_state_invalid_dirty");
                exportReadyCopy = exportState;
            } else if (dirty) {
                exportState = t("profiles.wizard_export_state_unsaved_existing");
                exportReadyCopy = exportState;
            } else {
                exportState = t("profiles.wizard_export_state_ready");
                exportReadyCopy = t("profiles.wizard_export_ready_saved");
                exportTone = "ready";
            }

            return {
                profileState,
                profileTone,
                workspaceState: workspaceSignalEl?.textContent || "",
                validationState,
                validationStateTone,
                exportState,
                exportTone,
                exportReadyCopy,
                policyCount: topLevelKeys.length,
                preferencesCount: Object.keys(preferences).length,
                rawFallbackKeys,
                deprecatedKeys,
                unknownKeys,
            };
        }

        function findFinalReviewTarget(kind, summary = null) {
            const resolvedSummary = summary || getFinalExportSummaryData(readWizardSchemaSource().data || {}, false, false);
            const policyIndex = getActiveSchemaPolicyIndex();

            if (kind === "network") {
                return findSettingsTarget("field:wizard-proxy-mode")
                    || findNetworkReviewTarget("dns")
                    || findNetworkReviewTarget("authentication")
                    || findNetworkReviewTarget("certificates")
                    || findNetworkReviewTarget("windows_sso");
            }
            if (kind === "home") {
                return findHomeReviewTarget("homepage")
                    || findHomeReviewTarget("overrides")
                    || findHomeReviewTarget("firefox_home")
                    || findHomeReviewTarget("user_messaging");
            }
            if (kind === "search") {
                return findSearchReviewTarget("defaults")
                    || findSearchReviewTarget("custom")
                    || findSearchReviewTarget("hidden")
                    || findSearchReviewTarget("suggest");
            }
            if (kind === "features") {
                return findSettingsTarget("policy:DisableFirefoxAccounts")
                    || findSettingsTarget("policy:RequestedLocales")
                    || findSettingsTarget("policy:TranslateEnabled")
                    || findSettingsTarget("field:wizard-extension-default-mode")
                    || findSettingsTarget("policy:WebsiteFilter")
                    || findSettingsTarget("shell-policy:6:ExtensionSettings");
            }
            if (kind === "ai") {
                return findSettingsTarget("policy:GenerativeAI")
                    || findSettingsTarget("policy:VisualSearchEnabled")
                    || findSettingsTarget("shell-policy:7:GenerativeAI");
            }
            if (kind === "privacy") {
                return findSettingsTarget("policy:Permissions")
                    || findSettingsTarget("policy:Cookies")
                    || findPrivacyReviewTarget("permissions")
                    || findPrivacyReviewTarget("cookies");
            }
            if (kind === "raw") {
                const key = resolvedSummary.rawFallbackKeys[0];
                const item = key ? policyIndex[key] : null;
                return item?.target ? findSettingsTarget(item.target) : (wizardSchemaShellViews["8"]?.raw || editorEl);
            }
            if (kind === "deprecated") {
                const key = resolvedSummary.deprecatedKeys[0];
                const item = key ? policyIndex[key] : null;
                return item?.target ? findSettingsTarget(item.target) : (wizardSchemaShellViews["8"]?.raw || editorEl);
            }
            if (kind === "unknown") {
                return editorEl || overviewPanelEl;
            }
            return null;
        }

        function renderFinalReviewJumpButtons(summary) {
            [
                { el: wizardExportSummaryNetworkJumpEl, kind: "network" },
                { el: wizardExportSummaryHomeJumpEl, kind: "home" },
                { el: wizardExportSummarySearchJumpEl, kind: "search" },
                { el: wizardExportSummaryFeaturesJumpEl, kind: "features" },
                { el: wizardExportSummaryAiJumpEl, kind: "ai" },
                { el: wizardExportSummaryPrivacyJumpEl, kind: "privacy" },
            ].forEach(({ el, kind }) => {
                if (!el) return;
                el.disabled = !findFinalReviewTarget(kind, summary);
            });

            [
                { el: wizardExportRawJumpEl, count: summary.rawFallbackKeys.length, kind: "raw" },
                { el: wizardExportDeprecatedJumpEl, count: summary.deprecatedKeys.length, kind: "deprecated" },
                { el: wizardExportUnknownJumpEl, count: summary.unknownKeys.length, kind: "unknown" },
            ].forEach(({ el, count, kind }) => {
                if (!el) return;
                el.disabled = !count || !findFinalReviewTarget(kind, summary);
            });
        }

        function renderFinalExportChecklist(summary, dirty, invalid) {
            if (!wizardExportChecklistEl) return;

            const currentId = getCurrentId();
            const currentProfile = getCurrentProfile();
            const items = [];

            if (currentProfile?.is_deleted) {
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_archived") });
            } else if (!currentId) {
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_draft") });
            } else {
                items.push({ tone: "accent", label: t("profiles.wizard_export_check_saved_record") });
            }

            if (invalid) {
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_invalid") });
            } else {
                items.push({ tone: "accent", label: t("profiles.wizard_export_check_syntax_ok") });
            }

            if (dirty) {
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_unsaved") });
            } else {
                items.push({ tone: "accent", label: t("profiles.wizard_export_check_synced") });
            }

            if (summary.rawFallbackKeys.length > 0) {
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_raw") });
            }
            if (summary.deprecatedKeys.length > 0) {
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_deprecated") });
            }
            if (summary.unknownKeys.length > 0) {
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_unknown") });
            }

            if (
                currentId
                && !currentProfile?.is_deleted
                && !dirty
                && !invalid
                && summary.rawFallbackKeys.length === 0
                && summary.deprecatedKeys.length === 0
                && summary.unknownKeys.length === 0
            ) {
                items.unshift({ tone: "accent", label: t("profiles.wizard_export_check_ready") });
            }

            wizardExportChecklistEl.innerHTML = items
                .map((item) => `<span class="wizard-shell-badge wizard-shell-badge--${item.tone}">${escapeHtml(item.label)}</span>`)
                .join("");
        }

        function renderFinalExportStepSummary(dirty, invalid) {
            const sourceState = readWizardSchemaSource();
            const currentRaw = getCurrentRaw();
            const parsed = sourceState.ok
                ? sourceState.data
                : (currentRaw && typeof currentRaw === "object" ? currentRaw : {});
            const summary = getFinalExportSummaryData(parsed, dirty, invalid);
            const guidedSummary = getExportGuidedSummaryData(parsed);

            setSummaryValue(wizardExportProfileStateEl, summary.profileState, summary.profileTone);
            setSummaryValue(
                wizardExportWorkspaceStateEl,
                summary.workspaceState,
                dirty ? "strict" : "ready",
            );
            setSummaryValue(
                wizardExportValidationStateEl,
                summary.validationState,
                summary.validationStateTone,
            );
            setSummaryValue(wizardExportReadyStateEl, summary.exportState, summary.exportTone);
            setText(wizardExportPolicyCountEl, summary.policyCount);
            setText(wizardExportPreferencesCountEl, summary.preferencesCount);
            setText(wizardExportRawCountEl, summary.rawFallbackKeys.length);
            setText(wizardExportDeprecatedCountEl, summary.deprecatedKeys.length);
            setText(wizardExportUnknownCountEl, summary.unknownKeys.length);
            setText(wizardExportReadyCopyEl, summary.exportReadyCopy);
            setSummaryValue(wizardExportSummaryNetworkEl, guidedSummary.networkText, guidedSummary.networkTone);
            setSummaryValue(wizardExportSummaryHomeEl, guidedSummary.homeText, guidedSummary.homeTone);
            setSummaryValue(wizardExportSummarySearchEl, guidedSummary.searchText, guidedSummary.searchTone);
            setSummaryValue(wizardExportSummaryFeaturesEl, guidedSummary.featuresText, guidedSummary.featuresTone);
            setSummaryValue(wizardExportSummaryAiEl, guidedSummary.aiText, guidedSummary.aiTone);
            setSummaryValue(wizardExportSummaryPrivacyEl, guidedSummary.privacyText, guidedSummary.privacyTone);
            renderFinalReviewJumpButtons(summary);
            renderFinalExportChecklist(summary, dirty, invalid);
        }

        return {
            findExtensionReviewTarget,
            findNetworkReviewTarget,
            findHomeReviewTarget,
            findSearchReviewTarget,
            findBookmarkReviewTarget,
            findWebsiteAccessReviewTarget,
            findPrivacyReviewTarget,
            findFinalReviewTarget,
            renderExtensionReviewSummary,
            renderNetworkReviewSummary,
            renderHomeReviewSummary,
            renderSearchReviewSummary,
            renderAiReviewSummary,
            renderBookmarkReviewSummary,
            renderWebsiteAccessReviewSummary,
            renderPrivacyReviewSummary,
            renderFinalExportStepSummary,
        };
    }

    window.BPMProfilesReview = { create };
})();
