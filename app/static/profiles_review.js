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
            wizardPrivacySummaryPermissionsEl,
            wizardPrivacySummaryCookiesEl,
            wizardPrivacySummaryUserDataEl,
            wizardPrivacySummaryCleanupEl,
            wizardPrivacySummaryUserDataJumpEl,
            wizardPrivacySummaryCleanupJumpEl,
            wizardPrivacySummaryPermissionsJumpEl,
            wizardPrivacySummaryCookiesJumpEl,
            wizardPrivacyUserDataSectionStatusEl,
            wizardLockdownSectionStatusEl,
            wizardPrivacySiteSectionStatusEl,
            wizardPrivacyVpnSectionStatusEl,
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
            wizardExportTechnicalAlertsEl,
            wizardExportRawSummaryJumpEl,
            wizardExportDeprecatedSummaryJumpEl,
            wizardExportUnknownSummaryJumpEl,
            wizardExportRawSummaryCountEl,
            wizardExportDeprecatedSummaryCountEl,
            wizardExportUnknownSummaryCountEl,
            wizardExportReadyCopyEl,
            wizardExportChecklistEl,
            wizardExportNextStepsEl,
            wizardExportReadyNowEl,
            wizardExportIncludedNowEl,
            wizardExportMissingNowEl,
            wizardExportReviewNowEl,
            wizardExportDrilldownEl,
            wizardExportDownloadHintEl,
            wizardExportBaselineCopyEl,
            wizardExportBaselineListEl,
            wizardCisFinalSummaryEl,
            wizardCisExceptionsCountEl,
            wizardCisExceptionsReasonsGroupEl,
            wizardCisExceptionsReasonsEl,
            wizardCisExceptionsDetailsEl,
            wizardCisExceptionsListEl,
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
            wizardExportShareableTextEl,
            wizardExportShareableCopyEl,
            wizardExportShareableStatusEl,
            editorEl,
            overviewPanelEl,
            wizardSummaryNameEl,
            wizardSummarySchemaEl,
            wizardSummaryStarterEl,
            wizardSummaryCisEl,
            wizardSummaryDerivedEl,
        } = elements;

        const getCurrentId = state.getCurrentId || (() => null);
        const getCurrentProfile = state.getCurrentProfile || (() => null);
        const getCloneSourceProfile = state.getCloneSourceProfile || (() => null);
        const getLifecycleSessionNote = state.getLifecycleSessionNote || (() => null);
        const getCurrentRaw = state.getCurrentRaw || (() => ({}));
        const getValidationPreviewTone = state.getValidationPreviewTone || (() => "neutral");
        const getWizardStarter = state.getWizardStarter || (() => "blank");
        const getWizardComplianceMergeInfo = state.getWizardComplianceMergeInfo || (() => ({
            layer: "none",
            label: "",
            summary: {},
            decisions: [],
        }));
        const setWizardComplianceDecisionNote = state.setWizardComplianceDecisionNote || (() => {});
        const getBaselineSummary = state.getBaselineSummary || (() => ({ copy: "", items: [] }));
        const workspaceSignalEl = state.workspaceSignalEl || null;

        function setText(el, value) {
            if (el) {
                el.textContent = String(value);
            }
        }

        function formatLifecycleTimestamp(value) {
            if (!value) return "";
            try {
                return new Intl.DateTimeFormat(documentRef.documentElement.lang || undefined, {
                    dateStyle: "medium",
                    timeStyle: "short",
                }).format(new Date(value));
            } catch {
                return String(value);
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

        function setHintValue(el, value, tone = "") {
            setText(el, value);
            if (!el) return;
            if (!tone) {
                delete el.dataset.summaryTone;
                return;
            }
            el.dataset.summaryTone = tone;
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

        function buildShareableGuidedSummaryText({
            exportSummary,
            guidedSummary,
            baselineSummary,
        }) {
            const profileName = wizardSummaryNameEl?.textContent?.trim()
                || documentRef.getElementById("profile-name")?.value?.trim()
                || t("profiles.wizard_export_shareable_profile_fallback");
            const schemaLabel = wizardSummarySchemaEl?.textContent?.trim() || "";
            const starterLabel = wizardSummaryStarterEl?.textContent?.trim() || "";
            const cisLabel = wizardSummaryCisEl?.textContent?.trim() || "";
            const derivedLabel = wizardSummaryDerivedEl?.textContent?.trim() || "";
            const currentProfile = getCurrentProfile();
            const lifecycleSessionNote = getLifecycleSessionNote();
            const lines = [
                t("profiles.wizard_export_shareable_heading"),
                `${t("profiles.wizard_export_shareable_profile_label")}: ${profileName}`,
            ];

            if (schemaLabel) {
                lines.push(`${t("profiles.wizard_export_shareable_schema_label")}: ${schemaLabel}`);
            }
            if (starterLabel) {
                lines.push(`${t("profiles.wizard_export_shareable_starter_label")}: ${starterLabel}`);
            }
            if (cisLabel) {
                lines.push(`${t("profiles.wizard_export_shareable_cis_label")}: ${cisLabel}`);
            }
            if (derivedLabel || getCloneSourceProfile()?.name) {
                lines.push(`${t("profiles.wizard_summary_derived")}: ${derivedLabel || t("profiles.wizard_summary_derived_value").replace("{name}", getCloneSourceProfile().name)}`);
            }
            if (currentProfile?.created_at) {
                lines.push(`${t("profiles.lifecycle_item_created")}: ${formatLifecycleTimestamp(currentProfile.created_at)}`);
            }
            if (currentProfile?.updated_at) {
                lines.push(`${t("profiles.lifecycle_item_saved")}: ${formatLifecycleTimestamp(currentProfile.updated_at)}`);
            }
            if (currentProfile?.is_deleted) {
                lines.push(`${t("profiles.lifecycle_item_state")}: ${t("profiles.lifecycle_item_state_archived")}`);
            } else if (getCurrentId()) {
                lines.push(`${t("profiles.lifecycle_item_state")}: ${t("profiles.lifecycle_item_state_saved")}`);
            } else if (getCloneSourceProfile()?.name) {
                lines.push(`${t("profiles.lifecycle_item_state")}: ${t("profiles.lifecycle_item_state_clone_draft")}`);
            }
            if (lifecycleSessionNote?.type === "restored" && lifecycleSessionNote.profileId === getCurrentId()) {
                lines.push(`${t("profiles.lifecycle_item_recent")}: ${formatLifecycleTimestamp(lifecycleSessionNote.at)}`);
            }

            lines.push(`${t("profiles.wizard_export_shareable_state_label")}: ${exportSummary.exportState}`);

            const baselineItems = Array.isArray(baselineSummary.items) ? baselineSummary.items.filter(Boolean) : [];
            if (baselineItems.length) {
                lines.push("");
                lines.push(t("profiles.wizard_export_baseline_summary_title"));
                baselineItems.forEach((item) => {
                    lines.push(`- ${item}`);
                });
            }

            const guidedSections = [
                [t("profiles.wizard_export_guided_network"), guidedSummary.networkText, guidedSummary.networkTone],
                [t("profiles.wizard_export_guided_home"), guidedSummary.homeText, guidedSummary.homeTone],
                [t("profiles.wizard_export_guided_search"), guidedSummary.searchText, guidedSummary.searchTone],
                [t("profiles.wizard_export_guided_features"), guidedSummary.featuresText, guidedSummary.featuresTone],
                [t("profiles.wizard_export_guided_ai"), guidedSummary.aiText, guidedSummary.aiTone],
                [t("profiles.wizard_export_guided_privacy"), guidedSummary.privacyText, guidedSummary.privacyTone],
            ].filter(([, text, tone]) => Boolean(text) && tone !== "default");

            lines.push("");
            lines.push(t("profiles.wizard_export_shareable_notice_title"));
            if (guidedSections.length) {
                guidedSections.forEach(([label, text]) => {
                    lines.push(`- ${label}: ${text}`);
                });
            } else {
                lines.push(`- ${t("profiles.wizard_export_shareable_notice_empty")}`);
            }

            lines.push("");
            lines.push(`${t("profiles.wizard_export_shareable_handoff_label")}: ${exportSummary.downloadHint}`);

            return lines.join("\n");
        }

        function buildCompactStateText(fragments, emptyKey = "profiles.wizard_review_default") {
            return fragments.length ? fragments.join(" • ") : t(emptyKey, "Using defaults");
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
            const aiControls = parsed?.AIControls && typeof parsed.AIControls === "object" && !Array.isArray(parsed.AIControls)
                ? parsed.AIControls
                : {};
            const generativeAi = parsed?.GenerativeAI && typeof parsed.GenerativeAI === "object" && !Array.isArray(parsed.GenerativeAI)
                ? parsed.GenerativeAI
                : {};
            return {
                aiControlsManaged: countConfiguredObjectEntries(aiControls),
                generativeAiControls: countConfiguredObjectEntries(generativeAi),
                visualSearchManaged: typeof parsed?.VisualSearchEnabled === "boolean",
                visualSearchEnabled: parsed?.VisualSearchEnabled === true,
            };
        }

        function findAiReviewTarget(kind) {
            const aiControlsCardEl = documentRef.querySelector('[data-schema-policy-id="AIControls"][data-schema-policy-kind="object-card"]');
            const generativeAiCardEl = documentRef.querySelector('[data-schema-policy-id="GenerativeAI"][data-schema-policy-kind="object-card"]');
            const visualSearchCardEl = documentRef.querySelector('[data-schema-policy-id="VisualSearchEnabled"][data-schema-policy-kind="boolean-card"]')
                || documentRef.querySelector('[data-schema-policy-id="VisualSearchEnabled"][data-schema-policy-kind="object-card"]');

            if (kind === "availability") {
                return aiControlsCardEl
                    || generativeAiCardEl
                    || findSettingsTarget("policy:AIControls")
                    || findSettingsTarget("policy:GenerativeAI")
                    || findSettingsTarget("shell-policy:7:AIControls")
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
                { el: wizardAiSummaryAvailabilityJumpEl, enabled: summary.aiControlsManaged > 0 || summary.generativeAiControls > 0, kind: "availability" },
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
                summary.aiControlsManaged > 0
                    ? formatCountLabel("profiles.wizard_ai_review_feature_controls_state", summary.aiControlsManaged)
                    : (summary.generativeAiControls > 0
                        ? formatCountLabel("profiles.wizard_ai_review_availability_state", summary.generativeAiControls)
                        : t("profiles.wizard_review_default")),
                summary.aiControlsManaged > 0 || summary.generativeAiControls > 0 ? "active" : "default",
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
                ipProtectionManaged: typeof parsed?.IPProtectionAvailable === "boolean",
                ipProtectionAvailable: parsed?.IPProtectionAvailable === true,
                reducedDataCollection: parsed?.DisableTelemetry === true || parsed?.DisableFirefoxStudies === true,
                privateBrowsingDisabled: parsed?.DisablePrivateBrowsing === true,
                passwordFlowTightened: parsed?.OfferToSaveLogins === false || parsed?.PasswordManagerEnabled === false,
                lockdownControls: [
                    parsed?.BlockAboutConfig === true,
                    parsed?.BlockAboutProfiles === true,
                    parsed?.DisableDeveloperTools === true,
                    parsed?.DisableBuiltinPDFViewer === true,
                    typeof parsed?.HttpsOnlyMode === "string" && parsed.HttpsOnlyMode.trim().length > 0,
                ].filter(Boolean).length,
                shutdownCleanupEnabled: Boolean(
                    parsed?.SanitizeOnShutdown
                    && (
                        parsed.SanitizeOnShutdown === true
                        || (typeof parsed.SanitizeOnShutdown === "object" && Object.keys(parsed.SanitizeOnShutdown).length > 0)
                    )
                ),
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

        function getPrivacyVpnSectionStatus(summary) {
            if (!summary.ipProtectionManaged) {
                return t("profiles.wizard_privacy_vpn_section_state_empty");
            }
            return summary.ipProtectionAvailable
                ? t("profiles.wizard_privacy_vpn_section_state_available")
                : t("profiles.wizard_privacy_vpn_section_state_hidden");
        }

        function renderPrivacySectionStatuses(parsed, summary) {
            setText(wizardPrivacyUserDataSectionStatusEl, getPrivacyUserDataSectionStatus(parsed));
            setText(wizardLockdownSectionStatusEl, getLockdownSectionStatus(parsed));
            setText(wizardPrivacySiteSectionStatusEl, getPrivacySiteSectionStatus(summary));
            setText(wizardPrivacyVpnSectionStatusEl, getPrivacyVpnSectionStatus(summary));
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
                aiControlsManaged: countConfiguredObjectEntries(parsed?.AIControls),
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
            if (features.aiControlsManaged > 0) {
                aiFragments.push(formatCountText("profiles.wizard_export_guided_ai_feature_controls", features.aiControlsManaged));
            } else if (features.generativeAiControls > 0) {
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
            if (privacy.reducedDataCollection) {
                privacyFragments.push(t("profiles.wizard_export_guided_privacy_data_collection"));
            }
            if (privacy.privateBrowsingDisabled) {
                privacyFragments.push(t("profiles.wizard_export_guided_privacy_private_browsing_off"));
            }
            if (privacy.passwordFlowTightened) {
                privacyFragments.push(t("profiles.wizard_export_guided_privacy_passwords_tightened"));
            }
            if (privacy.lockdownControls > 0) {
                privacyFragments.push(formatCountText("profiles.wizard_export_guided_privacy_lockdown", privacy.lockdownControls));
            }
            if (privacy.shutdownCleanupEnabled) {
                privacyFragments.push(t("profiles.wizard_export_guided_privacy_shutdown_cleanup"));
            }
            if (privacy.configuredPermissionCategories > 0) {
                privacyFragments.push(formatPermissionsObjectState(privacy.permissionsSummary));
            }
            if (privacy.cookieRuleCount > 0) {
                privacyFragments.push(formatCookiesObjectState(privacy.cookiesSummary));
            }
            if (privacy.ipProtectionManaged) {
                privacyFragments.push(
                    privacy.ipProtectionAvailable
                        ? t("profiles.wizard_export_guided_privacy_vpn_available")
                        : t("profiles.wizard_export_guided_privacy_vpn_hidden"),
                );
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
                privacyTone: (
                    privacy.lockedPermissionCategories > 0
                    || privacy.cookiesSummary.state === "strict"
                    || privacy.lockdownControls > 0
                    || privacy.shutdownCleanupEnabled
                    || privacy.privateBrowsingDisabled
                )
                    ? "strict"
                    : (privacyFragments.length ? "active" : "default"),
            };
        }

        function findPrivacyReviewTarget(kind) {
            const permissionsCardEl = documentRef.querySelector('[data-schema-policy-id="Permissions"][data-schema-policy-kind="object-card"]');
            const cookiesCardEl = documentRef.querySelector('[data-schema-policy-id="Cookies"][data-schema-policy-kind="object-card"]');

            if (kind === "user-data") {
                return documentRef.getElementById("wizard-privacy-user-data-presets")
                    || documentRef.getElementById("wizard-privacy-fine-tuning-toggle");
            }
            if (kind === "cleanup") {
                return documentRef.getElementById("wizard-cleanup-presets");
            }
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
                {
                    el: wizardPrivacySummaryUserDataJumpEl,
                    count: summary.reducedDataCollection || summary.privateBrowsingDisabled || summary.passwordFlowTightened ? 1 : 0,
                    kind: "user-data",
                },
                {
                    el: wizardPrivacySummaryCleanupJumpEl,
                    count: summary.shutdownCleanupEnabled ? 1 : 0,
                    kind: "cleanup",
                },
                {
                    el: wizardPrivacySummaryPermissionsJumpEl,
                    count: summary.configuredPermissionCategories + summary.lockedPermissionCategories,
                    kind: "permissions",
                },
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
                wizardPrivacySummaryUserDataEl,
                buildCompactStateText([
                    summary.reducedDataCollection ? t("profiles.wizard_export_guided_privacy_data_collection") : "",
                    summary.privateBrowsingDisabled ? t("profiles.wizard_export_guided_privacy_private_browsing_off") : "",
                    summary.passwordFlowTightened ? t("profiles.wizard_export_guided_privacy_passwords_tightened") : "",
                ].filter(Boolean)) || t("profiles.wizard_review_default"),
                summary.privateBrowsingDisabled || summary.passwordFlowTightened
                    ? "strict"
                    : (summary.reducedDataCollection ? "active" : "default"),
            );
            setSummaryValue(
                wizardPrivacySummaryCleanupEl,
                summary.shutdownCleanupEnabled
                    ? (summary.lockdownControls > 0
                        ? t("profiles.wizard_cleanup_section_state_strict")
                        : t("profiles.wizard_cleanup_section_state_shared"))
                    : t("profiles.wizard_review_default"),
                summary.shutdownCleanupEnabled ? "strict" : "default",
            );
            setSummaryValue(
                wizardPrivacySummaryPermissionsEl,
                summary.configuredPermissionCategories > 0 || summary.lockedPermissionCategories > 0
                    ? t("profiles.wizard_privacy_review_permissions_subcounts")
                        .replace("{configured}", String(summary.configuredPermissionCategories))
                        .replace("{locked}", String(summary.lockedPermissionCategories))
                    : t("profiles.wizard_review_default"),
                summary.lockedPermissionCategories > 0
                    ? "strict"
                    : (summary.configuredPermissionCategories > 0 ? "active" : "default"),
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
            let downloadHint = "";
            let downloadHintTone = "strict";
            if (currentProfile?.is_deleted) {
                exportState = t("profiles.wizard_export_state_archived");
                exportReadyCopy = exportState;
                downloadHint = t("profiles.wizard_export_download_hint_archived");
                downloadHintTone = "attention";
            } else if (!currentId) {
                exportState = t("profiles.wizard_export_state_unsaved_new");
                exportReadyCopy = t("profiles.wizard_export_ready_create");
                downloadHint = t("profiles.wizard_export_download_hint_unsaved_new");
            } else if (invalid) {
                exportState = t("profiles.wizard_export_state_invalid_dirty");
                exportReadyCopy = exportState;
                downloadHint = t("profiles.wizard_export_download_hint_invalid_dirty");
                downloadHintTone = "attention";
            } else if (dirty) {
                exportState = t("profiles.wizard_export_state_unsaved_existing");
                exportReadyCopy = exportState;
                downloadHint = t("profiles.wizard_export_download_hint_unsaved_existing");
            } else {
                exportState = t("profiles.wizard_export_state_ready");
                exportReadyCopy = t("profiles.wizard_export_ready_saved");
                exportTone = "ready";
                downloadHint = t("profiles.wizard_export_download_hint_ready");
                downloadHintTone = "ready";
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
                downloadHint,
                downloadHintTone,
                policyCount: topLevelKeys.length,
                preferencesCount: Object.keys(preferences).length,
                rawFallbackKeys,
                deprecatedKeys,
                unknownKeys,
            };
        }

        function buildFinalReviewAdvancedContext(kind, keys, policyIndex) {
            const normalizedKeys = Array.isArray(keys)
                ? keys.filter((key) => typeof key === "string" && key.trim())
                : [];
            if (!normalizedKeys.length) {
                return null;
            }

            const items = normalizedKeys.slice(0, 2).map((key) => policyIndex[key]?.label || key);
            let title = t("profiles.wizard_export_drilldown_title");
            if (kind === "unknown" && normalizedKeys.length === 1) {
                title = t("profiles.wizard_export_drilldown_unknown_title")
                    .replace("{label}", normalizedKeys[0]);
            } else if (kind === "deprecated" && normalizedKeys.length === 1) {
                title = t("profiles.wizard_export_drilldown_deprecated_title")
                    .replace("{label}", policyIndex[normalizedKeys[0]]?.label || normalizedKeys[0]);
            } else if (kind === "raw" && normalizedKeys.length === 1) {
                title = t("profiles.wizard_export_drilldown_raw_title")
                    .replace("{label}", policyIndex[normalizedKeys[0]]?.label || normalizedKeys[0]);
            }

            return {
                step: 8,
                stepTitle: title,
                items,
                remaining: Math.max(0, normalizedKeys.length - items.length),
            };
        }

        function formatCisDecisionPath(decision) {
            const path = Array.isArray(decision?.path) ? decision.path : [];
            return path.join(".");
        }

        function getCisDecisionPolicyKey(decision) {
            const path = Array.isArray(decision?.path) ? decision.path : [];
            if (path[0] === "Preferences") {
                return "Preferences";
            }
            return path[0] || "";
        }

        function getCisDecisionNoteKey(decision) {
            const policyKey = getCisDecisionPolicyKey(decision);
            if (policyKey) return policyKey;
            const recommendationIds = Array.isArray(decision?.recommendation_ids)
                ? decision.recommendation_ids.filter(Boolean)
                : [];
            if (recommendationIds.length) return `cis:${recommendationIds[0]}`;
            if (decision?.decision) return `cis:${decision.decision}`;
            return "";
        }

        function buildCisDecisionTitle(decision) {
            const pathLabel = formatCisDecisionPath(decision) || t("profiles.wizard_cis_review_unknown_path");
            if (decision.review_required) {
                return t("profiles.wizard_cis_review_manual_title").replace("{path}", pathLabel);
            }
            if (decision.decision === "cis_replaced_base") {
                return t("profiles.wizard_cis_review_raised_title").replace("{path}", pathLabel);
            }
            if (decision.decision === "added_from_cis") {
                return t("profiles.wizard_cis_review_added_title").replace("{path}", pathLabel);
            }
            if (decision.decision === "kept_base_stricter") {
                return t("profiles.wizard_cis_review_base_stricter_title").replace("{path}", pathLabel);
            }
            if (decision.decision === "already_satisfied") {
                return t("profiles.wizard_cis_review_satisfied_title").replace("{path}", pathLabel);
            }
            return t("profiles.wizard_cis_review_decision_title").replace("{path}", pathLabel);
        }

        function buildCisDecisionBody(decision) {
            const recommendationIds = Array.isArray(decision?.recommendation_ids)
                ? decision.recommendation_ids.filter(Boolean)
                : [];
            const source = recommendationIds.length
                ? t("profiles.wizard_cis_review_recommendations").replace("{ids}", recommendationIds.slice(0, 3).join(", "))
                : t("profiles.wizard_cis_review_recommendations_empty");
            const reason = decision?.reason || t("profiles.wizard_cis_review_reason_empty");
            return `${source} ${reason}`;
        }

        function countCisDecisions(summary, decisions, keys, fallbackFilter = null) {
            const resolvedSummary = summary && typeof summary === "object" ? summary : {};
            const resolvedKeys = Array.isArray(keys) ? keys : [keys];
            const summaryCount = resolvedKeys.reduce((total, key) => total + Number(resolvedSummary[key] || 0), 0);
            if (summaryCount > 0 || !fallbackFilter) {
                return summaryCount;
            }
            return decisions.filter(fallbackFilter).length;
        }

        function renderCisFinalSummary(complianceInfo) {
            if (!wizardCisFinalSummaryEl) return;
            const layer = complianceInfo?.layer || "none";
            const decisions = Array.isArray(complianceInfo?.decisions) ? complianceInfo.decisions : [];
            const summary = complianceInfo?.summary && typeof complianceInfo.summary === "object"
                ? complianceInfo.summary
                : {};

            if (!layer || layer === "none") {
                wizardCisFinalSummaryEl.innerHTML = `
                    <div class="wizard-export-plan-item" data-plan-tone="default">
                        <div class="wizard-export-plan-copy">${escapeHtml(t("profiles.wizard_cis_final_summary_empty"))}</div>
                    </div>
                `;
                return;
            }

            const appliedCount = countCisDecisions(
                summary,
                decisions,
                ["added_from_cis", "cis_replaced_base"],
                (decision) => decision.decision === "added_from_cis" || decision.decision === "cis_replaced_base",
            );
            const satisfiedCount = countCisDecisions(
                summary,
                decisions,
                "already_satisfied",
                (decision) => decision.decision === "already_satisfied",
            );
            const keptBaselineCount = countCisDecisions(
                summary,
                decisions,
                ["kept_base_stricter", "kept_base_only"],
                (decision) => decision.decision === "kept_base_stricter" || decision.decision === "kept_base_only",
            );
            const manualReviewCount = countCisDecisions(
                summary,
                decisions,
                "review_required",
                (decision) => decision.review_required,
            );
            const totalCount = decisions.length
                || Object.entries(summary)
                    .filter(([key]) => key !== "review_required")
                    .reduce((total, [, value]) => total + Number(value || 0), 0);
            const layerLabel = complianceInfo?.label || t("profiles.wizard_cis_l1_title");

            const items = [
                {
                    count: appliedCount,
                    label: t("profiles.wizard_cis_final_summary_applied"),
                    tone: appliedCount > 0 ? "active" : "default",
                },
                {
                    count: satisfiedCount,
                    label: t("profiles.wizard_cis_final_summary_satisfied"),
                    tone: satisfiedCount > 0 ? "ready" : "default",
                },
                {
                    count: keptBaselineCount,
                    label: t("profiles.wizard_cis_final_summary_kept"),
                    tone: keptBaselineCount > 0 ? "ready" : "default",
                },
                {
                    count: manualReviewCount,
                    label: t("profiles.wizard_cis_final_summary_manual"),
                    tone: manualReviewCount > 0 ? "attention" : "ready",
                },
            ];

            wizardCisFinalSummaryEl.innerHTML = `
                <div class="wizard-export-plan-item wizard-cis-final-summary-head" data-plan-tone="${manualReviewCount > 0 ? "active" : "ready"}">
                    <div class="wizard-export-plan-copy">
                        ${escapeHtml(t("profiles.wizard_cis_final_summary_layer")
                            .replace("{level}", layerLabel)
                            .replace("{count}", String(totalCount)))}
                    </div>
                </div>
                <div class="wizard-cis-final-summary-grid">
                    ${items.map((item) => `
                        <div class="wizard-export-plan-item wizard-cis-final-summary-item" data-plan-tone="${escapeHtml(item.tone)}">
                            <div class="wizard-export-plan-copy">
                                <strong>${escapeHtml(String(item.count))}</strong>
                                <span>${escapeHtml(item.label)}</span>
                            </div>
                        </div>
                    `).join("")}
                </div>
            `;
        }

        function renderCisExceptionNotes(decisions) {
            if (!wizardCisExceptionsListEl) return;
            const items = Array.isArray(decisions) ? decisions : [];
            wizardCisExceptionsListEl.innerHTML = "";
            setText(
                wizardCisExceptionsCountEl,
                items.length
                    ? t("profiles.wizard_cis_exceptions_count").replace("{count}", String(items.length))
                    : t("profiles.wizard_cis_exceptions_count_empty"),
            );
            if (wizardCisExceptionsCountEl) {
                if (items.length) {
                    wizardCisExceptionsCountEl.removeAttribute("data-i18n");
                } else {
                    wizardCisExceptionsCountEl.dataset.i18n = "profiles.wizard_cis_exceptions_count_empty";
                }
            }
            if (wizardCisExceptionsDetailsEl) {
                wizardCisExceptionsDetailsEl.hidden = !items.length;
                if (!items.length) {
                    wizardCisExceptionsDetailsEl.open = false;
                }
            }
            if (wizardCisExceptionsReasonsGroupEl) {
                wizardCisExceptionsReasonsGroupEl.hidden = !items.length;
            }
            if (wizardCisExceptionsReasonsEl) {
                wizardCisExceptionsReasonsEl.innerHTML = items.slice(0, 3)
                    .map((decision) => `
                        <div class="wizard-export-plan-item" data-plan-tone="active">
                            <div class="wizard-export-plan-copy">
                                <strong>${escapeHtml(buildCisDecisionTitle(decision))}</strong>
                                <span>${escapeHtml(buildCisDecisionBody(decision))}</span>
                            </div>
                        </div>
                    `)
                    .join("");
            }
            if (!items.length) {
                wizardCisExceptionsListEl.innerHTML = `
                    <div class="wizard-summary-row wizard-summary-row--stacked">
                        <span class="wizard-summary-key" data-i18n="profiles.wizard_cis_exceptions_empty">
                            ${t("profiles.wizard_cis_exceptions_empty")}
                        </span>
                    </div>
                `;
                return;
            }
            items.forEach((decision) => {
                const decisionKey = getCisDecisionNoteKey(decision);
                const title = buildCisDecisionTitle(decision);
                const body = buildCisDecisionBody(decision);
                const noteValue = decision?.exception_note || decision?.exceptionNote || "";
                const row = documentRef.createElement("div");
                row.className = "wizard-summary-row wizard-summary-row--stacked wizard-summary-row--decision";
                row.innerHTML = `
                    <span class="wizard-summary-key">${escapeHtml(title)}</span>
                    <span class="wizard-summary-value wizard-summary-value--left">${escapeHtml(body)}</span>
                    <label class="wizard-summary-value wizard-summary-value--left wizard-cis-note-label" data-i18n="profiles.wizard_cis_exceptions_note_label">
                        ${t("profiles.wizard_cis_exceptions_note_label")}
                    </label>
                    <textarea
                        class="soft-input wizard-cis-note-textarea"
                        rows="3"
                        placeholder="${escapeHtml(t("profiles.wizard_cis_exceptions_note_placeholder"))}"
                        ${decisionKey ? "" : "disabled"}>${escapeHtml(noteValue)}</textarea>
                `;
                const textarea = row.querySelector("textarea");
                if (textarea && decisionKey) {
                    textarea.addEventListener("input", () => {
                        setWizardComplianceDecisionNote(decisionKey, textarea.value);
                    });
                }
                wizardCisExceptionsListEl.appendChild(row);
            });
        }

        function buildCisAdvancedContext(decision) {
            const policyKey = getCisDecisionPolicyKey(decision);
            const items = [formatCisDecisionPath(decision)].filter(Boolean);
            return {
                step: 8,
                stepTitle: t("profiles.wizard_cis_review_context_title").replace("{path}", policyKey || "CIS"),
                items,
                remaining: 0,
            };
        }

        function getFinalReviewSelection(kind, options = {}) {
            const resolvedSummary = options.summary
                || getFinalExportSummaryData(readWizardSchemaSource().data || {}, false, false);
            const policyIndex = getActiveSchemaPolicyIndex();
            if (kind === "cis") {
                const policyKey = options.key || "";
                const complianceInfo = getWizardComplianceMergeInfo();
                const decision = options.decision || (Array.isArray(complianceInfo.decisions)
                    ? complianceInfo.decisions.find((entry) => getCisDecisionPolicyKey(entry) === policyKey)
                    : null);
                return {
                    target: policyKey
                        ? (
                            findSettingsTarget(`policy:${policyKey}`)
                            || findSettingsTarget(`shell-policy:8:${policyKey}`)
                            || editorEl
                        )
                        : (editorEl || overviewPanelEl),
                    context: decision ? buildCisAdvancedContext(decision) : null,
                };
            }

            if (kind === "network") {
                return {
                    target: findSettingsTarget("field:wizard-proxy-mode")
                    || findNetworkReviewTarget("dns")
                    || findNetworkReviewTarget("authentication")
                    || findNetworkReviewTarget("certificates")
                    || findNetworkReviewTarget("windows_sso"),
                };
            }
            if (kind === "home") {
                return {
                    target: findHomeReviewTarget("homepage")
                    || findHomeReviewTarget("overrides")
                    || findHomeReviewTarget("firefox_home")
                    || findHomeReviewTarget("user_messaging"),
                };
            }
            if (kind === "search") {
                return {
                    target: findSearchReviewTarget("defaults")
                    || findSearchReviewTarget("custom")
                    || findSearchReviewTarget("hidden")
                    || findSearchReviewTarget("suggest"),
                };
            }
            if (kind === "features") {
                return {
                    target: findSettingsTarget("policy:DisableFirefoxAccounts")
                    || findSettingsTarget("policy:RequestedLocales")
                    || findSettingsTarget("policy:TranslateEnabled")
                    || findSettingsTarget("field:wizard-extension-default-mode")
                    || findSettingsTarget("policy:WebsiteFilter")
                    || findSettingsTarget("shell-policy:6:ExtensionSettings"),
                };
            }
            if (kind === "ai") {
                return {
                    target: findSettingsTarget("policy:GenerativeAI")
                    || findSettingsTarget("policy:VisualSearchEnabled")
                    || findSettingsTarget("shell-policy:7:GenerativeAI"),
                };
            }
            if (kind === "privacy") {
                return {
                    target: findSettingsTarget("policy:Permissions")
                    || findSettingsTarget("policy:Cookies")
                    || findPrivacyReviewTarget("permissions")
                    || findPrivacyReviewTarget("cookies"),
                };
            }
            if (kind === "raw") {
                const keys = options.key ? [options.key] : resolvedSummary.rawFallbackKeys;
                const key = keys[0];
                const item = key ? policyIndex[key] : null;
                return {
                    target: (item?.target ? findSettingsTarget(item.target) : null)
                        || wizardSchemaShellViews["8"]?.raw
                        || editorEl,
                    context: buildFinalReviewAdvancedContext("raw", keys, policyIndex),
                };
            }
            if (kind === "deprecated") {
                const keys = options.key ? [options.key] : resolvedSummary.deprecatedKeys;
                const key = keys[0];
                const item = key ? policyIndex[key] : null;
                return {
                    target: (item?.target ? findSettingsTarget(item.target) : null)
                        || wizardSchemaShellViews["8"]?.raw
                        || editorEl,
                    context: buildFinalReviewAdvancedContext("deprecated", keys, policyIndex),
                };
            }
            if (kind === "unknown") {
                const keys = options.key ? [options.key] : resolvedSummary.unknownKeys;
                return {
                    target: editorEl || overviewPanelEl,
                    context: buildFinalReviewAdvancedContext("unknown", keys, policyIndex),
                };
            }
            return { target: null, context: null };
        }

        function findFinalReviewTarget(kind, summary = null, options = {}) {
            return getFinalReviewSelection(kind, { ...options, summary }).target;
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
                { el: wizardExportRawSummaryJumpEl, count: summary.rawFallbackKeys.length, kind: "raw" },
                { el: wizardExportDeprecatedSummaryJumpEl, count: summary.deprecatedKeys.length, kind: "deprecated" },
                { el: wizardExportUnknownSummaryJumpEl, count: summary.unknownKeys.length, kind: "unknown" },
            ].forEach(({ el, count, kind }) => {
                if (!el) return;
                el.disabled = !count || !findFinalReviewTarget(kind, summary);
            });
        }

        function renderFinalExportTechnicalAlerts(summary) {
            const technicalAlertsContainerEl = documentRef.getElementById("wizard-export-technical-alerts")
                || wizardExportTechnicalAlertsEl;
            const rawSummaryJumpEl = documentRef.getElementById("wizard-export-raw-summary-jump")
                || wizardExportRawSummaryJumpEl;
            const deprecatedSummaryJumpEl = documentRef.getElementById("wizard-export-deprecated-summary-jump")
                || wizardExportDeprecatedSummaryJumpEl;
            const unknownSummaryJumpEl = documentRef.getElementById("wizard-export-unknown-summary-jump")
                || wizardExportUnknownSummaryJumpEl;
            const rawSummaryCountEl = documentRef.getElementById("wizard-export-raw-summary-count")
                || wizardExportRawSummaryCountEl;
            const deprecatedSummaryCountEl = documentRef.getElementById("wizard-export-deprecated-summary-count")
                || wizardExportDeprecatedSummaryCountEl;
            const unknownSummaryCountEl = documentRef.getElementById("wizard-export-unknown-summary-count")
                || wizardExportUnknownSummaryCountEl;
            const items = [
                {
                    buttonEl: rawSummaryJumpEl,
                    countEl: rawSummaryCountEl,
                    count: summary.rawFallbackKeys.length,
                },
                {
                    buttonEl: deprecatedSummaryJumpEl,
                    countEl: deprecatedSummaryCountEl,
                    count: summary.deprecatedKeys.length,
                },
                {
                    buttonEl: unknownSummaryJumpEl,
                    countEl: unknownSummaryCountEl,
                    count: summary.unknownKeys.length,
                },
            ];
            const visibleCount = items.reduce((total, { buttonEl, countEl, count }) => {
                setText(countEl, count);
                if (buttonEl) {
                    buttonEl.hidden = count <= 0;
                }
                return total + (count > 0 ? 1 : 0);
            }, 0);
            if (technicalAlertsContainerEl) {
                technicalAlertsContainerEl.hidden = visibleCount <= 0;
            }
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

        function renderExportPlanItems(container, items, emptyLabel, emptyTone = "ready") {
            if (!container) return;
            const resolvedItems = items.length
                ? items
                : [{ tone: emptyTone, label: emptyLabel }];
            container.innerHTML = resolvedItems.map((item) => {
                const attributes = [];
                if (item.action?.kind === "assist") {
                    attributes.push(`data-export-assist-action="${escapeHtml(item.action.value)}"`);
                } else if (item.action?.kind === "scope") {
                    attributes.push(`data-workspace-scope-target="${escapeHtml(item.action.value)}"`);
                } else if (item.action?.kind === "jump") {
                    attributes.push(`data-final-review-jump="${escapeHtml(item.action.value)}"`);
                    if (item.action.key) {
                        attributes.push(`data-final-review-key="${escapeHtml(item.action.key)}"`);
                    }
                }
                const buttonHtml = item.action
                    ? `<button type="button" class="button-base ghost-button wizard-export-plan-action" ${attributes.join(" ")}>${escapeHtml(item.action.label)}</button>`
                    : "";
                return `<div class="wizard-export-plan-item" data-plan-tone="${escapeHtml(item.tone || "default")}"><div class="wizard-export-plan-copy">${escapeHtml(item.label)}</div>${buttonHtml}</div>`;
            }).join("");
        }

        function renderExportDrilldownItems(container, items, emptyLabel) {
            if (!container) return;
            const resolvedItems = items.length
                ? items
                : [{ tone: "ready", title: emptyLabel, body: "" }];
            container.innerHTML = resolvedItems.map((item) => {
                const attributes = [];
                if (item.action?.kind === "jump") {
                    attributes.push(`data-final-review-jump="${escapeHtml(item.action.value)}"`);
                    if (item.action.key) {
                        attributes.push(`data-final-review-key="${escapeHtml(item.action.key)}"`);
                    }
                } else if (item.action?.kind === "scope") {
                    attributes.push(`data-workspace-scope-target="${escapeHtml(item.action.value)}"`);
                }
                const buttonHtml = item.action
                    ? `<button type="button" class="button-base ghost-button wizard-export-plan-action" ${attributes.join(" ")}>${escapeHtml(item.action.label)}</button>`
                    : "";
                return `<div class="wizard-export-plan-item wizard-export-drilldown-item" data-plan-tone="${escapeHtml(item.tone || "default")}"><div class="wizard-export-plan-copy"><div class="wizard-export-drilldown-title">${escapeHtml(item.title || "")}</div>${item.body ? `<div class="wizard-export-drilldown-body">${escapeHtml(item.body)}</div>` : ""}</div>${buttonHtml}</div>`;
            }).join("");
        }

        function renderFinalExportActionPlan(summary, dirty, invalid) {
            const currentId = getCurrentId();
            const currentProfile = getCurrentProfile();
            const nextSteps = [];
            const readyNow = [];

            if (currentProfile?.is_deleted) {
                nextSteps.push({
                    tone: "attention",
                    label: t("profiles.wizard_export_plan_restore_profile"),
                    action: { kind: "assist", value: "restore", label: t("profiles.restore") },
                });
            } else if (!currentId) {
                nextSteps.push({
                    tone: "strict",
                    label: t("profiles.wizard_export_plan_save_first"),
                    action: { kind: "assist", value: "save", label: t("profiles.create_submit") },
                });
            } else if (dirty && !invalid) {
                nextSteps.push({
                    tone: "strict",
                    label: t("profiles.wizard_export_plan_save_latest"),
                    action: { kind: "assist", value: "save", label: t("profiles.save") },
                });
            }

            if (invalid) {
                nextSteps.push({
                    tone: "attention",
                    label: t("profiles.wizard_export_plan_fix_current_file"),
                    action: { kind: "scope", value: "advanced", label: t("profiles.advanced_handoff_open") },
                });
            } else if (summary.validationStateTone !== "ready") {
                nextSteps.push({
                    tone: "active",
                    label: t("profiles.wizard_export_plan_validate_once_more"),
                    action: { kind: "assist", value: "validate", label: t("profiles.validate") },
                });
            }

            if (summary.rawFallbackKeys.length > 0) {
                nextSteps.push({
                    tone: "active",
                    label: t("profiles.wizard_export_plan_review_raw")
                        .replace("{count}", String(summary.rawFallbackKeys.length)),
                    action: { kind: "jump", value: "raw", label: t("profiles.wizard_export_open") },
                });
            }
            if (summary.deprecatedKeys.length > 0) {
                nextSteps.push({
                    tone: "active",
                    label: t("profiles.wizard_export_plan_review_deprecated")
                        .replace("{count}", String(summary.deprecatedKeys.length)),
                    action: { kind: "jump", value: "deprecated", label: t("profiles.wizard_export_open") },
                });
            }
            if (summary.unknownKeys.length > 0) {
                nextSteps.push({
                    tone: "attention",
                    label: t("profiles.wizard_export_plan_review_unknown")
                        .replace("{count}", String(summary.unknownKeys.length)),
                    action: { kind: "jump", value: "unknown", label: t("profiles.wizard_export_open") },
                });
            }

            if (currentId && !currentProfile?.is_deleted) {
                readyNow.push({ tone: "ready", label: t("profiles.wizard_export_check_saved_record") });
            }
            if (!invalid) {
                readyNow.push({ tone: "ready", label: t("profiles.wizard_export_check_syntax_ok") });
            }
            if (currentId && !dirty && !currentProfile?.is_deleted) {
                readyNow.push({ tone: "ready", label: t("profiles.wizard_export_check_synced") });
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
                readyNow.unshift({ tone: "ready", label: t("profiles.wizard_export_check_ready") });
            }

            renderExportPlanItems(
                wizardExportNextStepsEl,
                nextSteps,
                t("profiles.wizard_export_next_steps_clear"),
                "ready",
            );
            renderExportPlanItems(
                wizardExportReadyNowEl,
                readyNow,
                t("profiles.wizard_export_ready_now_empty"),
                "default",
            );
        }

        function renderFinalExportExplainability(summary, dirty, invalid) {
            const currentId = getCurrentId();
            const currentProfile = getCurrentProfile();
            const includedNow = [];
            const missingNow = [];
            const reviewNow = [];
            const drilldown = [];
            const policyIndex = getActiveSchemaPolicyIndex();
            const complianceInfo = getWizardComplianceMergeInfo();
            const complianceDecisions = Array.isArray(complianceInfo.decisions)
                ? complianceInfo.decisions
                : [];
            const manualCisDecisions = complianceDecisions.filter((decision) => decision.review_required);
            const raisedCisDecisions = complianceDecisions.filter((decision) =>
                decision.decision === "added_from_cis" || decision.decision === "cis_replaced_base"
            );
            renderCisFinalSummary(complianceInfo);
            renderCisExceptionNotes(manualCisDecisions);

            if (currentId && !currentProfile?.is_deleted) {
                includedNow.push({
                    tone: dirty || invalid ? "active" : "ready",
                    label: dirty || invalid
                        ? t("profiles.wizard_export_included_saved_previous")
                        : t("profiles.wizard_export_included_saved_latest"),
                });
                includedNow.push({
                    tone: "default",
                    label: t("profiles.wizard_export_included_counts")
                        .replace("{policies}", String(summary.policyCount))
                        .replace("{preferences}", String(summary.preferencesCount)),
                });
            }

            if (summary.rawFallbackKeys.length > 0) {
                includedNow.push({
                    tone: "active",
                    label: t("profiles.wizard_export_included_raw")
                        .replace("{count}", String(summary.rawFallbackKeys.length)),
                });
                reviewNow.push({
                    tone: "active",
                    label: t("profiles.wizard_export_review_raw")
                        .replace("{count}", String(summary.rawFallbackKeys.length)),
                    action: { kind: "jump", value: "raw", label: t("profiles.wizard_export_open") },
                });
                summary.rawFallbackKeys.slice(0, 3).forEach((key) => {
                    const item = policyIndex[key];
                    drilldown.push({
                        tone: "active",
                        title: t("profiles.wizard_export_drilldown_raw_title")
                            .replace("{label}", item?.label || key),
                        body: t("profiles.wizard_export_drilldown_raw_body"),
                        action: { kind: "jump", value: "raw", key, label: t("profiles.wizard_export_open") },
                    });
                });
            }
            if (summary.deprecatedKeys.length > 0) {
                includedNow.push({
                    tone: "active",
                    label: t("profiles.wizard_export_included_deprecated")
                        .replace("{count}", String(summary.deprecatedKeys.length)),
                });
                reviewNow.push({
                    tone: "active",
                    label: t("profiles.wizard_export_review_deprecated")
                        .replace("{count}", String(summary.deprecatedKeys.length)),
                    action: { kind: "jump", value: "deprecated", label: t("profiles.wizard_export_open") },
                });
                summary.deprecatedKeys.slice(0, 3).forEach((key) => {
                    const item = policyIndex[key];
                    drilldown.push({
                        tone: "strict",
                        title: t("profiles.wizard_export_drilldown_deprecated_title")
                            .replace("{label}", item?.label || key),
                        body: t("profiles.wizard_export_drilldown_deprecated_body"),
                        action: { kind: "jump", value: "deprecated", key, label: t("profiles.wizard_export_open") },
                    });
                });
            }
            if (summary.unknownKeys.length > 0) {
                includedNow.push({
                    tone: "active",
                    label: t("profiles.wizard_export_included_unknown")
                        .replace("{count}", String(summary.unknownKeys.length)),
                });
                reviewNow.push({
                    tone: "attention",
                    label: t("profiles.wizard_export_review_unknown")
                        .replace("{count}", String(summary.unknownKeys.length)),
                    action: { kind: "jump", value: "unknown", label: t("profiles.wizard_export_open") },
                });
                summary.unknownKeys.slice(0, 3).forEach((key) => {
                    drilldown.push({
                        tone: "attention",
                        title: t("profiles.wizard_export_drilldown_unknown_title")
                            .replace("{label}", key),
                        body: t("profiles.wizard_export_drilldown_unknown_body"),
                        action: { kind: "jump", value: "unknown", key, label: t("profiles.wizard_export_open") },
                    });
                });
            }

            if (complianceInfo.layer && complianceInfo.layer !== "none") {
                includedNow.push({
                    tone: "active",
                    label: t("profiles.wizard_export_included_cis")
                        .replace("{level}", complianceInfo.label || t("profiles.wizard_cis_l1_title"))
                        .replace("{count}", String(raisedCisDecisions.length)),
                });
            }

            if (manualCisDecisions.length > 0) {
                reviewNow.push({
                    tone: "active",
                    label: t("profiles.wizard_export_review_cis_manual")
                        .replace("{count}", String(manualCisDecisions.length)),
                    action: {
                        kind: "jump",
                        value: "cis",
                        key: getCisDecisionPolicyKey(manualCisDecisions[0]),
                        label: t("profiles.wizard_export_open"),
                        decision: manualCisDecisions[0],
                    },
                });
                manualCisDecisions.slice(0, 5).forEach((decision) => {
                    drilldown.push({
                        tone: "active",
                        title: buildCisDecisionTitle(decision),
                        body: buildCisDecisionBody(decision),
                        action: {
                            kind: "jump",
                            value: "cis",
                            key: getCisDecisionPolicyKey(decision),
                            label: t("profiles.wizard_export_open"),
                            decision,
                        },
                    });
                });
            }

            if (currentProfile?.is_deleted) {
                missingNow.push({
                    tone: "attention",
                    label: t("profiles.wizard_export_missing_archived"),
                    action: { kind: "assist", value: "restore", label: t("profiles.restore") },
                });
            } else if (!currentId) {
                missingNow.push({
                    tone: "strict",
                    label: t("profiles.wizard_export_missing_unsaved_new"),
                    action: { kind: "assist", value: "save", label: t("profiles.create_submit") },
                });
            }

            if (dirty && currentId && !currentProfile?.is_deleted) {
                missingNow.push({
                    tone: "strict",
                    label: t("profiles.wizard_export_missing_unsaved_existing"),
                    action: { kind: "assist", value: "save", label: t("profiles.save") },
                });
            }

            if (invalid && !currentProfile?.is_deleted) {
                missingNow.push({
                    tone: "attention",
                    label: t("profiles.wizard_export_missing_invalid"),
                    action: { kind: "scope", value: "advanced", label: t("profiles.advanced_handoff_open") },
                });
            }

            renderExportPlanItems(
                wizardExportIncludedNowEl,
                includedNow,
                t("profiles.wizard_export_included_empty"),
                "default",
            );
            renderExportPlanItems(
                wizardExportMissingNowEl,
                missingNow,
                t("profiles.wizard_export_missing_empty"),
                "ready",
            );
            renderExportPlanItems(
                wizardExportReviewNowEl,
                reviewNow,
                t("profiles.wizard_export_review_empty"),
                "ready",
            );
            renderExportDrilldownItems(
                wizardExportDrilldownEl,
                drilldown,
                t("profiles.wizard_export_drilldown_empty"),
            );
        }

        function renderFinalExportStepSummary(dirty, invalid) {
            const sourceState = readWizardSchemaSource();
            const currentRaw = getCurrentRaw();
            const parsed = sourceState.ok
                ? sourceState.data
                : (currentRaw && typeof currentRaw === "object" ? currentRaw : {});
            const summary = getFinalExportSummaryData(parsed, dirty, invalid);
            const guidedSummary = getExportGuidedSummaryData(parsed);
            const baselineSummary = getBaselineSummary(getWizardStarter());

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
            setHintValue(wizardExportDownloadHintEl, summary.downloadHint, summary.downloadHintTone);
            renderFinalExportTechnicalAlerts(summary);
            setText(wizardExportBaselineCopyEl, baselineSummary.copy || "");
            if (wizardExportBaselineListEl) {
                wizardExportBaselineListEl.innerHTML = (Array.isArray(baselineSummary.items) ? baselineSummary.items : [])
                    .map((item) => `<div class="wizard-baseline-summary-item">${escapeHtml(item)}</div>`)
                    .join("");
            }
            setSummaryValue(wizardExportSummaryNetworkEl, guidedSummary.networkText, guidedSummary.networkTone);
            setSummaryValue(wizardExportSummaryHomeEl, guidedSummary.homeText, guidedSummary.homeTone);
            setSummaryValue(wizardExportSummarySearchEl, guidedSummary.searchText, guidedSummary.searchTone);
            setSummaryValue(wizardExportSummaryFeaturesEl, guidedSummary.featuresText, guidedSummary.featuresTone);
            setSummaryValue(wizardExportSummaryAiEl, guidedSummary.aiText, guidedSummary.aiTone);
            setSummaryValue(wizardExportSummaryPrivacyEl, guidedSummary.privacyText, guidedSummary.privacyTone);
            if (wizardExportShareableTextEl) {
                wizardExportShareableTextEl.value = buildShareableGuidedSummaryText({
                    exportSummary: summary,
                    guidedSummary,
                    baselineSummary,
                });
            }
            setHintValue(
                wizardExportShareableStatusEl,
                t("profiles.wizard_export_shareable_status_ready"),
                summary.exportTone === "ready" ? "ready" : "active",
            );
            if (wizardExportShareableCopyEl) {
                wizardExportShareableCopyEl.disabled = !(wizardExportShareableTextEl?.value || "").trim();
            }
            renderFinalReviewJumpButtons(summary);
            renderFinalExportChecklist(summary, dirty, invalid);
            renderFinalExportActionPlan(summary, dirty, invalid);
            renderFinalExportExplainability(summary, dirty, invalid);
        }

        return {
            findExtensionReviewTarget,
            findNetworkReviewTarget,
            findHomeReviewTarget,
            findSearchReviewTarget,
            findAiReviewTarget,
            findBookmarkReviewTarget,
            findWebsiteAccessReviewTarget,
            findPrivacyReviewTarget,
            findFinalReviewTarget,
            getFinalReviewSelection,
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
