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
        getCertificatesObjectSummary,
        getDnsOverHttpsObjectSummary,
        getUserMessagingObjectSummary,
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
            setText(wizardExtensionSummaryCuratedEl, summary.curatedProfiles);
            setText(wizardExtensionSummaryArbitraryEl, summary.arbitraryRules);
            setText(wizardExtensionSummaryCustomUrlsEl, summary.customInstallUrls);
            renderExtensionReviewJumpButtons(summary);
        }

        function getNetworkReviewSummaryData(parsed) {
            const authentication = getAuthenticationObjectSummary(parsed?.Authentication, []);
            const certificates = getCertificatesObjectSummary(parsed?.Certificates, []);
            const dnsOverHttps = getDnsOverHttpsObjectSummary(parsed?.DNSOverHTTPS, []);
            const windowsSsoExplicit = typeof parsed?.WindowsSSO === "boolean" ? 1 : 0;

            return {
                authenticationControls: authentication.configuredControls,
                certificateEntries: certificates.configuredEntries,
                dnsEntries: dnsOverHttps.configuredEntries,
                windowsSsoExplicit,
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
            setText(wizardNetworkSummaryAuthenticationEl, summary.authenticationControls);
            setText(wizardNetworkSummaryCertificatesEl, summary.certificateEntries);
            setText(wizardNetworkSummaryDnsEl, summary.dnsEntries);
            setText(wizardNetworkSummaryWindowsSsoEl, summary.windowsSsoExplicit);
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

            const homepageControls = (typeof homepage.URL === "string" && homepage.URL.trim() ? 1 : 0)
                + (Array.isArray(homepage.Additional) ? homepage.Additional.length : 0)
                + (typeof homepage.StartPage === "string" && homepage.StartPage.trim() ? 1 : 0)
                + (homepage.Locked === true ? 1 : 0);
            const overrideSurfaces = (typeof parsed?.NewTabPage === "boolean" ? 1 : 0)
                + (typeof parsed?.OverrideFirstRunPage === "string" && parsed.OverrideFirstRunPage.trim() ? 1 : 0)
                + (typeof parsed?.OverridePostUpdatePage === "string" && parsed.OverridePostUpdatePage.trim() ? 1 : 0);
            const firefoxHomeManaged = Object.values(firefoxHome).filter((value) => typeof value === "boolean").length;

            return {
                homepageControls,
                overrideSurfaces,
                firefoxHomeManaged,
                userMessagingControls: userMessaging.configuredSurfaces,
            };
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
            setText(wizardHomeSummaryHomepageEl, summary.homepageControls);
            setText(wizardHomeSummaryOverridesEl, summary.overrideSurfaces);
            setText(wizardHomeSummaryFirefoxHomeEl, summary.firefoxHomeManaged);
            setText(wizardHomeSummaryUserMessagingEl, summary.userMessagingControls);
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
            const suggestControls = Object.values(firefoxSuggest).filter((value) => typeof value === "boolean").length;

            return {
                defaultControls,
                hiddenEngines,
                customEngines,
                suggestControls,
            };
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
            setText(wizardSearchSummaryDefaultsEl, summary.defaultControls);
            setText(wizardSearchSummaryHiddenEl, summary.hiddenEngines);
            setText(wizardSearchSummaryCustomEl, summary.customEngines);
            setText(wizardSearchSummarySuggestEl, summary.suggestControls);
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
            setText(wizardBookmarkSummaryLinksEl, summary.bookmarkEntries);
            setText(wizardBookmarkSummaryFoldersEl, summary.managedFolders);
            setText(wizardBookmarkSummaryNestedEl, summary.nestedRows);
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

            return {
                blockedSites: Array.isArray(websiteFilter.Block) ? websiteFilter.Block.length : 0,
                exceptions: Array.isArray(websiteFilter.Exceptions) ? websiteFilter.Exceptions.length : 0,
                handlerRules: countHandlerRuleBucket(handlers.mimeTypes)
                    + countHandlerRuleBucket(handlers.schemes)
                    + countHandlerRuleBucket(handlers.extensions),
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
            setText(wizardWebsiteAccessSummaryBlockedEl, summary.blockedSites);
            setText(wizardWebsiteAccessSummaryExceptionsEl, summary.exceptions);
            setText(wizardWebsiteAccessSummaryHandlersEl, summary.handlerRules);
            renderWebsiteAccessReviewJumpButtons(summary);
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
            setText(wizardPrivacySummaryPermissionsConfiguredEl, summary.configuredPermissionCategories);
            setText(wizardPrivacySummaryPermissionsLockedEl, summary.lockedPermissionCategories);
            setText(wizardPrivacySummaryCookiesEl, summary.cookieRuleCount);
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
            let profileState = t("profiles.wizard_export_profile_draft", "Draft only");
            if (currentId && currentProfile?.is_deleted) {
                profileState = t("profiles.wizard_export_profile_archived", "Archived profile #{id}")
                    .replace("{id}", String(currentId));
            } else if (currentId) {
                profileState = t("profiles.wizard_export_profile_saved", "Saved profile #{id}")
                    .replace("{id}", String(currentId));
            }

            const validationTone = getValidationPreviewTone();
            let validationState = "";
            if (invalid) {
                validationState = t("profiles.wizard_export_validation_invalid", "Document syntax needs attention.");
            } else if (validationTone === "error" || validationTone === "success") {
                validationState = validationPreviewEl?.textContent || "";
            } else {
                validationState = t("profiles.wizard_export_validation_pending", "Validate before export if you want a fresh API check.");
            }

            let exportState = "";
            let exportReadyCopy = "";
            if (currentProfile?.is_deleted) {
                exportState = t("profiles.wizard_export_state_archived", "Archived profiles cannot be exported until restored.");
                exportReadyCopy = exportState;
            } else if (!currentId) {
                exportState = t("profiles.wizard_export_state_unsaved_new", "Save this profile before export.");
                exportReadyCopy = t("profiles.wizard_export_ready_create", "Create and save this profile first, then download JSON or YAML.");
            } else if (invalid) {
                exportState = t("profiles.wizard_export_state_invalid_dirty", "Fix invalid JSON/YAML before saving. Export links still point to the last saved version.");
                exportReadyCopy = exportState;
            } else if (dirty) {
                exportState = t("profiles.wizard_export_state_unsaved_existing", "Unsaved changes are not in the export yet. Save first.");
                exportReadyCopy = exportState;
            } else {
                exportState = t("profiles.wizard_export_state_ready", "Saved version is ready for JSON and YAML download.");
                exportReadyCopy = t("profiles.wizard_export_ready_saved", "The saved version below matches the editor and is ready for JSON or YAML download.");
            }

            return {
                profileState,
                workspaceState: workspaceSignalEl?.textContent || "",
                validationState,
                exportState,
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

            if (kind === "raw") {
                const key = resolvedSummary.rawFallbackKeys[0];
                const item = key ? policyIndex[key] : null;
                return item?.target ? findSettingsTarget(item.target) : (wizardSchemaShellViews["7"]?.raw || editorEl);
            }
            if (kind === "deprecated") {
                const key = resolvedSummary.deprecatedKeys[0];
                const item = key ? policyIndex[key] : null;
                return item?.target ? findSettingsTarget(item.target) : (wizardSchemaShellViews["7"]?.raw || editorEl);
            }
            if (kind === "unknown") {
                return editorEl || overviewPanelEl;
            }
            return null;
        }

        function renderFinalReviewJumpButtons(summary) {
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
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_archived", "Archived profile") });
            } else if (!currentId) {
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_draft", "Draft only") });
            } else {
                items.push({ tone: "accent", label: t("profiles.wizard_export_check_saved_record", "Saved record exists") });
            }

            if (invalid) {
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_invalid", "Invalid document") });
            } else {
                items.push({ tone: "accent", label: t("profiles.wizard_export_check_syntax_ok", "Document parses") });
            }

            if (dirty) {
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_unsaved", "Unsaved edits") });
            } else {
                items.push({ tone: "accent", label: t("profiles.wizard_export_check_synced", "Export matches editor") });
            }

            if (summary.rawFallbackKeys.length > 0) {
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_raw", "Raw fallback present") });
            }
            if (summary.deprecatedKeys.length > 0) {
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_deprecated", "Deprecated policies present") });
            }
            if (summary.unknownKeys.length > 0) {
                items.push({ tone: "warm", label: t("profiles.wizard_export_check_unknown", "Unknown keys present") });
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
                items.unshift({ tone: "accent", label: t("profiles.wizard_export_check_ready", "Ready for clean export") });
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

            setText(wizardExportProfileStateEl, summary.profileState);
            setText(wizardExportWorkspaceStateEl, summary.workspaceState);
            setText(wizardExportValidationStateEl, summary.validationState);
            setText(wizardExportReadyStateEl, summary.exportState);
            setText(wizardExportPolicyCountEl, summary.policyCount);
            setText(wizardExportPreferencesCountEl, summary.preferencesCount);
            setText(wizardExportRawCountEl, summary.rawFallbackKeys.length);
            setText(wizardExportDeprecatedCountEl, summary.deprecatedKeys.length);
            setText(wizardExportUnknownCountEl, summary.unknownKeys.length);
            setText(wizardExportReadyCopyEl, summary.exportReadyCopy);
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
            renderBookmarkReviewSummary,
            renderWebsiteAccessReviewSummary,
            renderPrivacyReviewSummary,
            renderFinalExportStepSummary,
        };
    }

    window.BPMProfilesReview = { create };
})();
