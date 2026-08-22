import {
    ALL_URLS,
    analyzeWebsiteFilterLists,
    applyWebsiteFilterPosture,
    inspectImportedWebsiteFilter,
    omitEmptyWebsiteFilterFields,
    resolveWebsiteFilterPosture,
    validateWebsiteFilterPattern,
} from "./profiles_modules/website_filter.mjs";
import {
    getNavigationInputKind,
    getSafeExternalLink,
    inspectImportedNavigationValue,
} from "./profiles_modules/navigation_url.mjs";

    function create({
        documentRef = document,
        elements = {},
        dependencies = {},
        state = {},
        wizardSchemaShellCatalog = {},
        wizardSchemaShellViews = {},
        components = {},
    }) {
        const {
            t,
            escapeHtml,
            humanizeIdentifier,
            formatBooleanSelectValue,
            parseBooleanSelectValue,
            formatSchemaLabel,
            fromEditorValue,
            toEditorValue,
            setStatus,
            readWizardSchemaSource,
            getActiveWizardSchemaVersion,
            renderManualHomeAndSearchSectionStatuses,
            renderNetworkReviewSummary,
            renderHomeReviewSummary,
            renderSearchReviewSummary,
            renderBookmarkReviewSummary,
            renderWebsiteAccessReviewSummary,
            renderPrivacyReviewSummary,
            getManagedExtensionProfileById,
            textToList,
        } = dependencies;
        const {
            createValueIO,
            createReview,
            createActions,
        } = components;
        const renderAiReviewSummary = dependencies.renderAiReviewSummary || (() => {});
        const onDocumentChange = dependencies.onDocumentChange || (() => {});

        const getEditor = state.getEditor || (() => null);
        const setCurrentRaw = state.setCurrentRaw || (() => {});

        const {
            wizardDnsOverHttpsCardEl,
            wizardRequestedLocalesCardEl,
            wizardTranslateEnabledCardEl,
            wizardIpProtectionAvailableCardEl,
            wizardAiControlsCardEl,
            wizardVisualSearchEnabledCardEl,
            wizardGenerativeAiCardEl,
            wizardUserMessagingCardEl,
            wizardWebsiteFilterCardEl,
            wizardAllowedDomainsForAppsCardEl,
            wizardHttpAllowlistCardEl,
            wizardLocalFileLinksCardEl,
            wizardHandlersCardEl,
            wizardAutoLaunchProtocolsCardEl,
            wizardIntranetNavigationCardEl,
            wizardBookmarksCardEl,
            wizardManagedBookmarksCardEl,
            wizardNoDefaultBookmarksCardEl,
            wizardPermissionsCardEl,
            wizardCookiesCardEl,
            wizardLocalNetworkAccessCardEl,
        } = elements;

        const valueIO = createValueIO({
            dependencies: {
                t,
                textToList,
                parseBooleanSelectValue,
            },
        });

        const review = createReview({
            documentRef,
            dependencies: {
                t,
                getManagedExtensionProfileById,
            },
            helpers: valueIO,
        });

        const TASK_FIRST_POLICY_LAYOUTS = {
            Authentication: {
                intro: {
                    key: "profiles.wizard_schema_authentication_intro",
                    fallback: "Start with browser-wide sign-in behavior, then add trusted hosts only where they are really needed.",
                },
                groups: [
                    {
                        title: {
                            key: "profiles.wizard_schema_authentication_group_main_title",
                            fallback: "Browser-wide behavior",
                        },
                        body: {
                            key: "profiles.wizard_schema_authentication_group_main_body",
                            fallback: "Decide whether Firefox locks these rules and whether enterprise sign-in works in private windows.",
                        },
                        fields: ["Locked", "PrivateBrowsing"],
                    },
                    {
                        title: {
                            key: "profiles.wizard_schema_authentication_group_hosts_title",
                            fallback: "Trusted hosts and protocols",
                        },
                        body: {
                            key: "profiles.wizard_schema_authentication_group_hosts_body",
                            fallback: "List only the hosts or origins that should use enterprise sign-in methods.",
                        },
                        fields: ["SPNEGO", "NTLM", "Delegated"],
                    },
                    {
                        title: {
                            key: "profiles.wizard_schema_authentication_group_exceptions_title",
                            fallback: "Non-standard host exceptions",
                        },
                        body: {
                            key: "profiles.wizard_schema_authentication_group_exceptions_body",
                            fallback: "Use these only when short hostnames or proxy auth exceptions are required in your environment.",
                        },
                        fields: ["AllowNonFQDN", "AllowProxies"],
                    },
                ],
            },
            Certificates: {
                intro: {
                    key: "profiles.wizard_schema_certificates_intro",
                    fallback: "Choose whether Firefox should trust enterprise roots first, then add certificate files only if you manage your own trust chain.",
                },
                groups: [
                    {
                        title: {
                            key: "profiles.wizard_schema_certificates_group_main_title",
                            fallback: "Enterprise trust",
                        },
                        body: {
                            key: "profiles.wizard_schema_certificates_group_main_body",
                            fallback: "This is the fast path when your operating system already distributes the right root certificates.",
                        },
                        fields: ["ImportEnterpriseRoots"],
                    },
                    {
                        title: {
                            key: "profiles.wizard_schema_certificates_group_install_title",
                            fallback: "Managed certificate files",
                        },
                        body: {
                            key: "profiles.wizard_schema_certificates_group_install_body",
                            fallback: "Add certificate files only when Firefox should import specific trust material directly.",
                        },
                        fields: ["Install"],
                    },
                ],
            },
            Cookies: {
                intro: {
                    key: "profiles.wizard_schema_cookies_intro",
                    fallback: "Choose the default cookie posture first, then add site-specific exceptions only where users need them.",
                },
                groups: [
                    {
                        title: {
                            key: "profiles.wizard_schema_cookies_group_defaults_title",
                            fallback: "Default cookie behavior",
                        },
                        body: {
                            key: "profiles.wizard_schema_cookies_group_defaults_body",
                            fallback: "Set the baseline for normal and private browsing, then lock it only if people should not change it.",
                        },
                        fields: ["Behavior", "BehaviorPrivateBrowsing", "Locked"],
                    },
                    {
                        title: {
                            key: "profiles.wizard_schema_cookies_group_sites_title",
                            fallback: "Site-specific exceptions",
                        },
                        body: {
                            key: "profiles.wizard_schema_cookies_group_sites_body",
                            fallback: "Allow, session-only allow, or block cookies for specific sites.",
                        },
                        fields: ["Allow", "AllowSession", "Block"],
                    },
                ],
            },
            Permissions: {
                intro: {
                    key: "profiles.wizard_schema_permissions_intro",
                    fallback: "Pick the permission areas Firefox should manage, then add allow or block lists only for the categories that matter.",
                },
                groups: [
                    {
                        title: {
                            key: "profiles.wizard_schema_permissions_group_capture_title",
                            fallback: "Communication and capture",
                        },
                        body: {
                            key: "profiles.wizard_schema_permissions_group_capture_body",
                            fallback: "Camera, microphone, and screen sharing controls usually matter first in managed environments.",
                        },
                        fields: ["Camera", "Microphone", "ScreenShare"],
                    },
                    {
                        title: {
                            key: "profiles.wizard_schema_permissions_group_alerts_title",
                            fallback: "Location and notifications",
                        },
                        body: {
                            key: "profiles.wizard_schema_permissions_group_alerts_body",
                            fallback: "Decide whether websites can ask for location and notification access, or whether Firefox should block that flow.",
                        },
                        fields: ["Location", "Notifications"],
                    },
                    {
                        title: {
                            key: "profiles.wizard_schema_permissions_group_media_title",
                            fallback: "Media and immersive features",
                        },
                        body: {
                            key: "profiles.wizard_schema_permissions_group_media_body",
                            fallback: "Use these controls for autoplay and VR-style capabilities that may need tighter defaults.",
                        },
                        fields: ["Autoplay", "VirtualReality"],
                    },
                ],
            },
            UserMessaging: {
                intro: {
                    key: "profiles.wizard_schema_user_messaging_intro",
                    fallback: "Turn the browser messages people should or should not see on first, then lock the result if needed.",
                },
                groups: [
                    {
                        title: {
                            key: "profiles.wizard_schema_user_messaging_group_onboarding_title",
                            fallback: "Onboarding and lock state",
                        },
                        body: {
                            key: "profiles.wizard_schema_user_messaging_group_onboarding_body",
                            fallback: "Control the first-run experience and whether users can change these messaging surfaces later.",
                        },
                        fields: ["SkipOnboarding", "Locked"],
                    },
                    {
                        title: {
                            key: "profiles.wizard_schema_user_messaging_group_recommendations_title",
                            fallback: "Recommendations and promos",
                        },
                        body: {
                            key: "profiles.wizard_schema_user_messaging_group_recommendations_body",
                            fallback: "Choose whether Firefox can recommend add-ons, features, or other Mozilla content.",
                        },
                        fields: ["ExtensionRecommendations", "FeatureRecommendations", "MoreFromMozilla"],
                    },
                    {
                        title: {
                            key: "profiles.wizard_schema_user_messaging_group_surfaces_title",
                            fallback: "In-product surfaces",
                        },
                        body: {
                            key: "profiles.wizard_schema_user_messaging_group_surfaces_body",
                            fallback: "Use these controls for address-bar interventions and Firefox Labs style entry points.",
                        },
                        fields: ["UrlbarInterventions", "FirefoxLabs"],
                    },
                ],
            },
        };

        function getLocalizedTaskCopy(copySpec) {
            if (!copySpec) return "";
            return t(copySpec.key);
        }

        function renderTaskFirstFieldGroup(policyId, groupSpec, fields, currentObject, disabled) {
            const selectedFields = groupSpec.fields
                .map((fieldName) => fields.find((field) => field.name === fieldName))
                .filter(Boolean);

            if (!selectedFields.length) {
                return "";
            }

            const fieldsMarkup = selectedFields
                .map((field) => renderWizardSchemaInlineField(policyId, field, currentObject[field.name], disabled))
                .join("");
            const title = getLocalizedTaskCopy(groupSpec.title);
            const body = getLocalizedTaskCopy(groupSpec.body);

            return `
                <section class="wizard-shell-task-group">
                    <div class="wizard-shell-task-group-head">
                        <div class="wizard-shell-task-group-title">${escapeHtml(title)}</div>
                        ${body ? `<div class="wizard-shell-task-group-body">${escapeHtml(body)}</div>` : ""}
                    </div>
                    <div class="wizard-grid">
                        ${fieldsMarkup}
                    </div>
                </section>
            `;
        }

        function renderNestedTaskFieldGroup(policyId, groupSpec, fields, currentObject, disabled, fieldPath) {
            const selectedFields = groupSpec.fields
                .map((fieldName) => fields.find((field) => field.name === fieldName))
                .filter(Boolean);

            if (!selectedFields.length) {
                return "";
            }

            const fieldsMarkup = selectedFields
                .map((field) => renderWizardSchemaNestedField(policyId, fieldPath, field, currentObject[field.name], disabled))
                .join("");
            const title = getLocalizedTaskCopy(groupSpec.title);
            const body = getLocalizedTaskCopy(groupSpec.body);

            return `
                <section class="wizard-shell-task-group">
                    <div class="wizard-shell-task-group-head">
                        <div class="wizard-shell-task-group-title">${escapeHtml(title)}</div>
                        ${body ? `<div class="wizard-shell-task-group-body">${escapeHtml(body)}</div>` : ""}
                    </div>
                    <div class="wizard-grid">
                        ${fieldsMarkup}
                    </div>
                </section>
            `;
        }

        function getNestedTaskLayout(policyId, fieldPath, field) {
            const fieldNames = new Set((field.fields || []).map((entry) => entry.name));
            if (policyId === "Permissions" && field.kind === "nested-object" && fieldNames.has("Allow") && fieldNames.has("Block")) {
                return {
                    intro: {
                        key: "profiles.wizard_schema_permissions_category_intro",
                        fallback: "Set the default behavior for this permission area first, then add site-specific allow and block rules only if you need them.",
                    },
                    groups: [
                        {
                            title: {
                                key: "profiles.wizard_schema_permissions_category_group_defaults_title",
                                fallback: "Default behavior",
                            },
                            body: {
                                key: "profiles.wizard_schema_permissions_category_group_defaults_body",
                                fallback: "Choose whether Firefox blocks new requests, locks this permission, or uses a built-in default.",
                            },
                            fields: ["BlockNewRequests", "Default", "Locked"],
                        },
                        {
                            title: {
                                key: "profiles.wizard_schema_permissions_category_group_sites_title",
                                fallback: "Site-specific lists",
                            },
                            body: {
                                key: "profiles.wizard_schema_permissions_category_group_sites_body",
                                fallback: "List the sites that should always be allowed or blocked for this permission area.",
                            },
                            fields: ["Allow", "Block"],
                        },
                    ],
                };
            }
            return null;
        }

        function renderTaskFirstNestedFields(policyId, fieldPath, field, currentObject, disabled) {
            const layout = getNestedTaskLayout(policyId, fieldPath, field);
            const defaultMarkup = `
                <div class="wizard-grid">
                    ${(field.fields || [])
                        .map((nestedField) => renderWizardSchemaNestedField(policyId, fieldPath, nestedField, currentObject[nestedField.name], disabled))
                        .join("")}
                </div>
            `;

            if (!layout?.groups?.length) {
                return defaultMarkup;
            }

            const usedFieldNames = new Set();
            const groupsMarkup = layout.groups
                .map((groupSpec) => {
                    groupSpec.fields.forEach((fieldName) => usedFieldNames.add(fieldName));
                    return renderNestedTaskFieldGroup(policyId, groupSpec, field.fields || [], currentObject, disabled, fieldPath);
                })
                .filter(Boolean)
                .join("");
            const remainingFields = (field.fields || []).filter((nestedField) => !usedFieldNames.has(nestedField.name));
            const intro = getLocalizedTaskCopy(layout.intro);

            return `
                <div class="wizard-shell-task-layout">
                    ${intro ? `<div class="wizard-shell-task-intro">${escapeHtml(intro)}</div>` : ""}
                    ${groupsMarkup}
                    ${remainingFields.length ? `
                        <section class="wizard-shell-task-group">
                            <div class="wizard-grid">
                                ${remainingFields
                                    .map((nestedField) => renderWizardSchemaNestedField(policyId, fieldPath, nestedField, currentObject[nestedField.name], disabled))
                                    .join("")}
                            </div>
                        </section>
                    ` : ""}
                </div>
            `;
        }

        function getNestedFieldUiCopy(policyId, fieldPath, field) {
            if (policyId === "Handlers" && field.kind === "nested-dictionary-object") {
                if (fieldPath === "mimeTypes") {
                    return {
                        intro: t("profiles.wizard_schema_handlers_mimeTypes_intro"),
                        addLabel: t("profiles.wizard_schema_handlers_mimeTypes_add"),
                        keyLabel: t("profiles.wizard_schema_handlers_mimeTypes_key_label"),
                        metaLabel: t("profiles.wizard_schema_handlers_entry_meta"),
                    };
                }
                if (fieldPath === "schemes") {
                    return {
                        intro: t("profiles.wizard_schema_handlers_schemes_intro"),
                        addLabel: t("profiles.wizard_schema_handlers_schemes_add"),
                        keyLabel: t("profiles.wizard_schema_handlers_schemes_key_label"),
                        metaLabel: t("profiles.wizard_schema_handlers_entry_meta"),
                    };
                }
                if (fieldPath === "extensions") {
                    return {
                        intro: t("profiles.wizard_schema_handlers_extensions_intro"),
                        addLabel: t("profiles.wizard_schema_handlers_extensions_add"),
                        keyLabel: t("profiles.wizard_schema_handlers_extensions_key_label"),
                        metaLabel: t("profiles.wizard_schema_handlers_entry_meta"),
                    };
                }
            }

            if (field.kind === "nested-array-of-objects" && fieldPath.endsWith(".handlers")) {
                return {
                    intro: t("profiles.wizard_schema_handlers_helper_apps_intro"),
                    addLabel: t("profiles.wizard_schema_handlers_helper_apps_add"),
                };
            }

            return null;
        }

        function getListFieldUiCopy(policyId, fieldPath, field, fieldKind) {
            const normalizedPath = String(fieldPath || field.name || "");

            if (policyId === "Authentication" && ["SPNEGO", "Delegated", "NTLM"].includes(field.name || "")) {
                return {
                    hint: t("profiles.wizard_schema_authentication_hosts_hint"),
                    addLabel: t("profiles.wizard_schema_authentication_hosts_add"),
                    emptyLabel: t("profiles.wizard_schema_list_empty_hosts"),
                };
            }

            if (
                ["Permissions", "Cookies", "WebsiteFilter"].includes(policyId)
                && ["Allow", "AllowSession", "Block", "Exceptions"].includes(field.name || "")
            ) {
                return {
                    hint: t("profiles.wizard_schema_sites_list_hint"),
                    addLabel: t("profiles.wizard_schema_sites_list_add"),
                    emptyLabel: t("profiles.wizard_schema_list_empty_sites"),
                };
            }

            if (policyId === "Certificates" && field.name === "Install") {
                return {
                    hint: t("profiles.wizard_schema_certificates_install_hint"),
                    addLabel: t("profiles.wizard_schema_certificates_install_add"),
                    emptyLabel: t("profiles.wizard_schema_list_empty_files"),
                };
            }

            if (policyId === "Handlers" && normalizedPath.endsWith(".handlers")) {
                return {
                    hint: t("profiles.wizard_schema_handlers_helper_apps_intro"),
                    addLabel: t("profiles.wizard_schema_handlers_helper_apps_add"),
                    emptyLabel: t("profiles.wizard_shell_array_empty"),
                };
            }

            if (fieldKind === "true-map") {
                return {
                    hint: t("profiles.wizard_shell_true_map_hint"),
                    addLabel: t("profiles.wizard_schema_list_add_entry"),
                    emptyLabel: t("profiles.wizard_schema_list_empty_entries"),
                };
            }

            return {
                addLabel: t("profiles.wizard_schema_list_add_entry"),
                emptyLabel: t("profiles.wizard_schema_list_empty_entries"),
            };
        }

        function navigationFieldAttributes(policyId, fieldPath, label, currentValue) {
            const kind = getNavigationInputKind(policyId, fieldPath);
            if (!kind) return "";
            const original = typeof currentValue === "string" ? ` data-navigation-url-original="${escapeHtml(currentValue)}"` : "";
            return ` data-navigation-url-kind="${escapeHtml(kind)}" data-navigation-url-field-label="${escapeHtml(label)}"${original}`;
        }

        function renderNavigationExternalLink(value, kind) {
            const link = getSafeExternalLink(value, kind);
            if (!link) return "";
            return `
                <a class="wizard-navigation-external-link" href="${escapeHtml(link.href)}" target="${link.target}" rel="${link.rel}" referrerpolicy="${link.referrerPolicy}">
                    ${escapeHtml(t("profiles.wizard_navigation_open_external"))}
                </a>
            `;
        }

        function renderImportedNavigationRawNotice(value, kind, label) {
            if (value == null || value === "") return "";
            const inspected = inspectImportedNavigationValue(value, kind);
            if (inspected.kind !== "raw_fallback") return "";
            const rule = String(inspected.verdict.code || "invalid_value").replaceAll("_", "-");
            const message = t("profiles.wizard_navigation_url_raw_fallback")
                .replace("{field}", label)
                .replace("{rule}", rule);
            return `<div class="wizard-input-hint" data-navigation-url-raw-fallback>${escapeHtml(message)}</div>`;
        }

        function renderSchemaListRows(values, disabledAttr, navigation = null) {
            const rows = Array.isArray(values) ? values : [];
            return rows
                .map((value) => {
                    const text = String(value || "");
                    const navigationAttrs = navigation
                        ? ` data-navigation-url-kind="${escapeHtml(navigation.kind)}" data-navigation-url-field-label="${escapeHtml(navigation.label)}" data-navigation-url-original="${escapeHtml(text)}"`
                        : "";
                    return `
                    <div class="wizard-inline-list-row" data-schema-list-row>
                        <input type="text" class="soft-input" data-schema-list-item value="${escapeHtml(text)}"${navigationAttrs} ${disabledAttr} />
                        <button type="button" class="button-base danger-button" data-schema-list-remove ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_array_remove"))}</button>
                    </div>
                `;
                })
                .join("");
        }

        function renderNavigationRawListFallback(value, label, rule) {
            const message = t("profiles.wizard_navigation_url_raw_fallback")
                .replace("{field}", label)
                .replace("{rule}", rule);
            const serialized = JSON.stringify(value, null, 2);
            return `
                <div class="wizard-field-full" data-navigation-url-raw-fallback>
                    <div class="field-label mb-1">${escapeHtml(label)}</div>
                    <pre class="wizard-input-hint">${escapeHtml(serialized)}</pre>
                    <div class="wizard-input-hint">${escapeHtml(message)}</div>
                </div>
            `;
        }

        function renderSchemaListEditor({
            policyId = "",
            field = {},
            fieldPath = "",
            currentValue = null,
            disabled = false,
            targetAttr = "",
            kindAttr = "",
        }) {
            const disabledAttr = disabled ? "disabled" : "";
            const label = getSchemaFieldLabel(field);
            const fieldKind = field.kind;
            const listValues = fieldKind === "true-map"
                ? (
                    currentValue && typeof currentValue === "object" && !Array.isArray(currentValue)
                        ? Object.entries(currentValue).filter(([, enabled]) => enabled === true).map(([key]) => key)
                        : []
                )
                : (Array.isArray(currentValue) ? currentValue : []);
            const uiCopy = getListFieldUiCopy(policyId, fieldPath, field, fieldKind);
            const navigationKind = getNavigationInputKind(policyId, fieldPath);
            const navigation = navigationKind ? { kind: navigationKind, label } : null;
            const malformedNavigationList = navigation && currentValue != null && (
                !Array.isArray(currentValue) || currentValue.some((value) => typeof value !== "string")
            );
            if (malformedNavigationList) {
                return renderNavigationRawListFallback(currentValue, label, "not-list-of-strings");
            }
            const rowsMarkup = renderSchemaListRows(listValues, disabledAttr, navigation);
            const rawListValue = navigation
                ? listValues.find((value) => inspectImportedNavigationValue(value, navigation.kind).kind === "raw_fallback")
                : null;
            const navigationAttrs = navigation
                ? ` data-navigation-url-kind="${escapeHtml(navigation.kind)}" data-navigation-url-field-label="${escapeHtml(navigation.label)}"`
                : "";

            return `
                <div class="wizard-field-full wizard-inline-list-field" ${targetAttr} ${kindAttr}${navigationAttrs}>
                    <div class="wizard-search-engine-head">
                        <div>
                            <div class="field-label mb-1">${escapeHtml(label)}</div>
                            ${uiCopy.hint ? `<div class="wizard-input-hint">${escapeHtml(uiCopy.hint)}</div>` : ""}
                        </div>
                        <button type="button" class="button-base ghost-button" data-schema-list-add ${disabledAttr}>${escapeHtml(uiCopy.addLabel || t("profiles.wizard_schema_list_add_entry"))}</button>
                    </div>
                    <div class="wizard-inline-list" data-schema-list data-schema-list-empty-label="${escapeHtml(uiCopy.emptyLabel || t("profiles.wizard_schema_list_empty_entries"))}">
                        ${rowsMarkup || `<div class="wizard-shell-empty" data-schema-list-empty>${escapeHtml(uiCopy.emptyLabel || t("profiles.wizard_schema_list_empty_entries"))}</div>`}
                    </div>
                    ${rawListValue == null ? "" : renderImportedNavigationRawNotice(rawListValue, navigation.kind, label)}
                </div>
            `;
        }

        function renderTaskFirstObjectFields(policyId, fields, currentObject, disabled) {
            const layout = TASK_FIRST_POLICY_LAYOUTS[policyId];
            const defaultMarkup = `
                <div class="wizard-grid">
                    ${fields
                        .map((field) => renderWizardSchemaInlineField(policyId, field, currentObject[field.name], disabled))
                        .join("")}
                </div>
            `;

            if (!layout?.groups?.length) {
                return defaultMarkup;
            }

            const usedFieldNames = new Set();
            const groupsMarkup = layout.groups
                .map((groupSpec) => {
                    groupSpec.fields.forEach((fieldName) => usedFieldNames.add(fieldName));
                    return renderTaskFirstFieldGroup(policyId, groupSpec, fields, currentObject, disabled);
                })
                .filter(Boolean)
                .join("");
            const remainingFields = fields.filter((field) => !usedFieldNames.has(field.name));
            const intro = getLocalizedTaskCopy(layout.intro);

            return `
                <div class="wizard-shell-task-layout">
                    ${intro ? `<div class="wizard-shell-task-intro">${escapeHtml(intro)}</div>` : ""}
                    ${groupsMarkup}
                    ${remainingFields.length ? `
                        <section class="wizard-shell-task-group">
                            <div class="wizard-grid">
                                ${remainingFields
                                    .map((field) => renderWizardSchemaInlineField(policyId, field, currentObject[field.name], disabled))
                                    .join("")}
                            </div>
                        </section>
                    ` : ""}
                </div>
            `;
        }

        function renderWizardSchemaShell() {
            const schemaVersion = getActiveWizardSchemaVersion();
            const channelData = wizardSchemaShellCatalog.channels?.[schemaVersion];
            const shellSteps = Array.isArray(wizardSchemaShellCatalog.steps) ? wizardSchemaShellCatalog.steps : [];
            const sourceState = readWizardSchemaSource();

            shellSteps.forEach((stepMeta) => {
                const view = wizardSchemaShellViews[String(stepMeta.step)];
                if (!view) return;

                const stepData = channelData?.steps?.[String(stepMeta.step)] || {
                    recommended: [],
                    additional: [],
                    raw_fallback: [],
                    preferences: [],
                    compatibility: { total: 0, mapped: 0, raw_fallback: 0, deprecated: 0 },
                };

                renderWizardSchemaShellCoverage(view.coverage, stepData.compatibility || {});
                renderWizardSchemaShellBadges(view.badges, schemaVersion, stepData.compatibility || {});
                renderWizardSchemaShellPolicyBucket(
                    view.recommended,
                    stepData.recommended || [],
                    t("profiles.wizard_shell_empty_recommended"),
                    sourceState.data,
                    !sourceState.ok,
                );
                renderWizardSchemaShellPolicyBucket(
                    view.additional,
                    stepData.additional || [],
                    t("profiles.wizard_shell_empty_additional"),
                    sourceState.data,
                    !sourceState.ok,
                );
                renderWizardSchemaShellPreferenceBucket(
                    view.preferences,
                    stepData.preferences || [],
                    t("profiles.wizard_shell_empty_preferences"),
                );
                renderWizardSchemaShellPolicyBucket(
                    view.raw,
                    stepData.raw_fallback || [],
                    t("profiles.wizard_shell_empty_raw"),
                    sourceState.data,
                    !sourceState.ok,
                );
            });

            renderManualHomeAndSearchSectionStatuses(sourceState.data);
            renderNetworkReviewSummary(sourceState.data);
            renderHomeReviewSummary(sourceState.data);
            renderSearchReviewSummary(sourceState.data);
            renderAiReviewSummary(sourceState.data);
            renderMountedSchemaPolicies(sourceState.data, !sourceState.ok, channelData);
            syncManualPolicyControls(channelData);
        }

        function syncManualPolicyControls(channelData) {
            const supportedPolicyIds = new Set();

            Object.values(channelData?.steps || {}).forEach((stepData) => {
                ["recommended", "additional", "raw_fallback"].forEach((bucket) => {
                    (Array.isArray(stepData?.[bucket]) ? stepData[bucket] : []).forEach((item) => {
                        if (item?.id) supportedPolicyIds.add(item.id);
                    });
                });
            });

            documentRef.querySelectorAll("[data-schema-policy-control]").forEach((control) => {
                const available = supportedPolicyIds.has(control.dataset.schemaPolicyControl || "");
                control.hidden = !available;
                control.setAttribute("aria-hidden", available ? "false" : "true");
                control.querySelectorAll("input, select, button").forEach((input) => {
                    input.disabled = !available;
                });
            });
        }

        function getWizardSchemaPolicyItem(policyId, channelData, preferredStep = null) {
            if (!policyId || !channelData?.steps) return null;

            const stepKeys = preferredStep != null
                ? [String(preferredStep)]
                : Object.keys(channelData.steps);

            for (const stepKey of stepKeys) {
                const stepData = channelData.steps?.[stepKey];
                const buckets = [
                    ...(Array.isArray(stepData?.recommended) ? stepData.recommended : []),
                    ...(Array.isArray(stepData?.additional) ? stepData.additional : []),
                    ...(Array.isArray(stepData?.raw_fallback) ? stepData.raw_fallback : []),
                ];
                const match = buckets.find((item) => item.id === policyId);
                if (match) return match;
            }

            return null;
        }

        function renderMountedSchemaPolicyUnavailable(container, policyId) {
            if (!container) return;

            const isAiPolicy = ["AIControls", "GenerativeAI", "VisualSearchEnabled"].includes(policyId);
            if (!isAiPolicy) {
                container.innerHTML = "";
                container.hidden = true;
                return;
            }

            container.hidden = false;
            container.innerHTML = `
                <div
                    class="wizard-shell-card"
                    data-schema-policy-card
                    data-schema-policy-id="${escapeHtml(policyId || "")}"
                    data-schema-policy-kind="unsupported"
                    data-settings-target="policy:${escapeHtml(policyId || "")}">
                    <div>
                        <div class="wizard-shell-card-title">${escapeHtml(humanizeIdentifier(policyId || ""))}</div>
                        <div class="wizard-shell-card-copy">${escapeHtml(t("profiles.wizard_ai_policy_unavailable"))}</div>
                    </div>
                </div>
            `;
        }

        function websiteFilterRowMarkup(field, entry, index, disabled) {
            const verdict = validateWebsiteFilterPattern(entry);
            const raw = !verdict.valid;
            const disabledAttr = disabled ? "disabled" : "";
            const fieldLabel = field === "Block"
                ? t("profiles.wizard_website_filter_block_title")
                : t("profiles.wizard_website_filter_allow_title");
            return `
                <div
                    class="wizard-website-filter-row${raw ? " wizard-website-filter-row--raw" : ""}"
                    data-website-filter-row
                    data-website-filter-field="${field}"
                    data-website-filter-index="${index}"
                    data-website-filter-imported="true"
                    data-website-filter-original="${escapeHtml(entry)}">
                    <label class="wizard-website-filter-pattern-field">
                        <span class="sr-only">${escapeHtml(fieldLabel)}</span>
                        <input
                            type="text"
                            class="soft-input"
                            value="${escapeHtml(entry)}"
                            data-website-filter-pattern
                            autocomplete="off"
                            spellcheck="false"
                            ${disabledAttr} />
                    </label>
                    <div class="wizard-website-filter-row-actions" role="group" aria-label="${escapeHtml(fieldLabel)}">
                        <button type="button" class="button-base ghost-button" data-website-filter-move="up" ${disabledAttr} aria-label="${escapeHtml(t("profiles.wizard_website_filter_move_up"))}">↑</button>
                        <button type="button" class="button-base ghost-button" data-website-filter-move="down" ${disabledAttr} aria-label="${escapeHtml(t("profiles.wizard_website_filter_move_down"))}">↓</button>
                        <button type="button" class="button-base danger-button" data-website-filter-remove ${disabledAttr}>${escapeHtml(t("profiles.wizard_website_filter_remove"))}</button>
                    </div>
                    <div class="wizard-website-filter-row-message" data-website-filter-row-message></div>
                </div>
            `;
        }

        function websiteFilterListMarkup(field, entries, disabled) {
            const isBlock = field === "Block";
            const label = t(isBlock
                ? "profiles.wizard_website_filter_block_title"
                : "profiles.wizard_website_filter_allow_title");
            const addLabel = t(isBlock
                ? "profiles.wizard_website_filter_add_block"
                : "profiles.wizard_website_filter_add_allow");
            const emptyLabel = t(isBlock
                ? "profiles.wizard_website_filter_empty_block"
                : "profiles.wizard_website_filter_empty_allow");
            const disabledAttr = disabled ? "disabled" : "";
            return `
                <section class="wizard-website-filter-list" data-website-filter-list="${field}">
                    <div class="wizard-search-engine-head">
                        <div>
                            <h4 class="field-label">${escapeHtml(label)}</h4>
                            <p class="wizard-input-hint">${escapeHtml(t("profiles.wizard_website_filter_pattern_hint"))}</p>
                        </div>
                        <button type="button" class="button-base ghost-button" data-website-filter-add="${field}" ${disabledAttr}>${escapeHtml(addLabel)}</button>
                    </div>
                    <div class="wizard-website-filter-rows" data-website-filter-rows="${field}">
                        ${entries.length
                            ? entries.map((entry, index) => websiteFilterRowMarkup(field, entry, index, disabled)).join("")
                            : `<div class="wizard-shell-empty" data-website-filter-empty>${escapeHtml(emptyLabel)}</div>`}
                    </div>
                </section>
            `;
        }

        function renderWebsiteFilterManager(container, item, currentValue, disabled) {
            const inspected = inspectImportedWebsiteFilter(currentValue);
            const policyLabel = getShellPolicyLabel(item);
            const disabledAttr = disabled ? "disabled" : "";
            if (inspected.kind !== "typed") {
                container.innerHTML = `
                    <section
                        class="wizard-shell-card wizard-website-filter-manager"
                        data-schema-policy-card
                        data-schema-policy-id="WebsiteFilter"
                        data-schema-policy-kind="website-filter-raw"
                        data-settings-target="${escapeHtml(item.target || "policy:WebsiteFilter")}">
                        <div>
                            <div class="wizard-shell-card-title">${escapeHtml(policyLabel)}</div>
                            <div class="wizard-input-hint" data-website-filter-raw-fallback>${escapeHtml(t("profiles.wizard_website_filter_raw_fallback"))}</div>
                        </div>
                        <pre class="wizard-website-filter-raw-value">${escapeHtml(JSON.stringify(inspected.value, null, 2))}</pre>
                    </section>
                `;
                return;
            }

            const posture = resolveWebsiteFilterPosture(inspected.value);
            const postureButtons = [
                ["defaults", "profiles.wizard_website_filter_preset_defaults_title"],
                ["block_some", "profiles.wizard_website_filter_shared_preset_block_some_title"],
                ["allow_only", "profiles.wizard_website_filter_shared_preset_allow_only_title"],
                ["mixed", "profiles.wizard_website_filter_preset_mixed_title"],
            ].map(([key, labelKey]) => `
                <button
                    type="button"
                    class="button-base ghost-button wizard-search-engine-preset${posture === key ? " wizard-search-engine-preset--applied" : ""}"
                    data-website-filter-posture="${key}"
                    aria-pressed="${posture === key ? "true" : "false"}"
                    ${disabledAttr}>${escapeHtml(t(labelKey))}</button>
            `).join("");
            container.innerHTML = `
                <section
                    class="wizard-shell-card wizard-website-filter-manager"
                    data-schema-policy-card
                    data-schema-policy-id="WebsiteFilter"
                    data-schema-policy-kind="website-filter"
                    data-settings-target="${escapeHtml(item.target || "policy:WebsiteFilter")}">
                    <div>
                        <div class="wizard-shell-card-title">${escapeHtml(policyLabel)}</div>
                        <div class="wizard-shell-card-copy">${escapeHtml(t("profiles.wizard_website_filter_guidance"))}</div>
                    </div>
                    <div class="wizard-search-engine-preset-grid wizard-website-filter-postures" data-website-filter-postures>
                        ${postureButtons}
                    </div>
                    <div class="wizard-website-filter-lists">
                        ${websiteFilterListMarkup("Block", inspected.value.Block, disabled)}
                        ${websiteFilterListMarkup("Exceptions", inspected.value.Exceptions, disabled)}
                    </div>
                    <div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" role="status" aria-live="polite" data-website-filter-status></div>
                </section>
            `;
            refreshWebsiteFilterManagerState(container.querySelector("[data-schema-policy-card]"));
        }

        function readWebsiteFilterManagerValue(card) {
            const inspected = {
                Block: [],
                Exceptions: [],
            };
            const invalidNewEntries = [];
            const fieldIndexes = { Block: 0, Exceptions: 0 };
            card?.querySelectorAll("[data-website-filter-row]").forEach((row) => {
                const field = row.dataset.websiteFilterField;
                const input = row.querySelector("[data-website-filter-pattern]");
                const value = input?.value ?? "";
                if (field !== "Block" && field !== "Exceptions") return;
                const index = fieldIndexes[field];
                fieldIndexes[field] += 1;
                if (!value) return;
                const verdict = validateWebsiteFilterPattern(value);
                const imported = row.dataset.websiteFilterImported === "true";
                if (!verdict.valid && !imported) {
                    invalidNewEntries.push({ field, index, value, code: verdict.code });
                }
                inspected[field].push(value);
            });
            return { value: omitEmptyWebsiteFilterFields(inspected), invalidNewEntries };
        }

        function refreshWebsiteFilterManagerState(card) {
            if (!card || card.dataset.schemaPolicyKind !== "website-filter") return { valid: false };
            const { value, invalidNewEntries } = readWebsiteFilterManagerValue(card);
            const analysis = analyzeWebsiteFilterLists(value);
            const duplicateRows = new Set();
            analysis.duplicates.forEach((duplicate) => {
                duplicateRows.add(`${duplicate.field}:${duplicate.first}`);
                duplicateRows.add(`${duplicate.field}:${duplicate.index}`);
            });
            const conflictRows = new Set();
            analysis.conflicts.forEach((conflict) => {
                if (Number.isInteger(conflict.blockIndex)) conflictRows.add(`Block:${conflict.blockIndex}`);
                if (Number.isInteger(conflict.exceptionIndex)) conflictRows.add(`Exceptions:${conflict.exceptionIndex}`);
            });
            const invalidRows = new Set(invalidNewEntries.map((entry) => `${entry.field}:${entry.index}`));
            const rawRows = new Set((analysis.rawEntries || []).map((entry) => `${entry.field}:${entry.index}`));

            card.querySelectorAll("[data-website-filter-row]").forEach((row) => {
                const field = row.dataset.websiteFilterField || "";
                const input = row.querySelector("[data-website-filter-pattern]");
                const value = input?.value ?? "";
                const listIndex = Array.from(card.querySelectorAll(`[data-website-filter-row][data-website-filter-field="${field}"]`)).indexOf(row);
                const message = row.querySelector("[data-website-filter-row-message]");
                row.classList.remove("wizard-website-filter-row--invalid", "wizard-website-filter-row--raw", "wizard-website-filter-row--warning");
                if (!value) {
                    message.textContent = "";
                    return;
                }
                if (invalidRows.has(`${field}:${listIndex}`)) {
                    row.classList.add("wizard-website-filter-row--invalid");
                    message.textContent = t("profiles.wizard_website_filter_invalid");
                } else if (rawRows.has(`${field}:${listIndex}`)) {
                    row.classList.add("wizard-website-filter-row--raw");
                    message.textContent = t("profiles.wizard_website_filter_raw_fallback");
                } else if (duplicateRows.has(`${field}:${listIndex}`)) {
                    row.classList.add("wizard-website-filter-row--warning");
                    message.textContent = t("profiles.wizard_website_filter_duplicate");
                } else if (conflictRows.has(`${field}:${listIndex}`)) {
                    row.classList.add("wizard-website-filter-row--warning");
                    message.textContent = t("profiles.wizard_website_filter_conflict");
                } else {
                    message.textContent = "";
                }
            });

            const status = card.querySelector("[data-website-filter-status]");
            if (status) {
                if (invalidNewEntries.length) status.textContent = t("profiles.wizard_website_filter_invalid");
                else if ((analysis.rawEntries || []).length) status.textContent = t("profiles.wizard_website_filter_raw_fallback");
                else if (analysis.duplicates.length || analysis.conflicts.length) status.textContent = t("profiles.wizard_website_filter_conflict");
                else status.textContent = review.formatWebsiteFilterObjectState(
                    review.getWebsiteFilterObjectSummary(value),
                );
            }
            card.dataset.websiteFilterState = invalidNewEntries.length ? "invalid" : review.getWebsiteFilterObjectSummary(value).state;
            return { valid: invalidNewEntries.length === 0, value, analysis };
        }

        function applyWebsiteFilterFromCard(card) {
            const editor = getEditor();
            if (!editor || !card || card.dataset.schemaPolicyKind !== "website-filter") return false;
            const rendered = refreshWebsiteFilterManagerState(card);
            if (!rendered.valid) {
                setStatus(t("profiles.wizard_website_filter_invalid"), "warn");
                return false;
            }
            try {
                const mode = documentRef.getElementById("mode")?.value || "";
                const parsed = fromEditorValue(editor.getValue(), mode);
                const normalized = parsed && typeof parsed === "object" ? { ...parsed } : {};
                if (Object.keys(rendered.value).length) normalized.WebsiteFilter = rendered.value;
                else delete normalized.WebsiteFilter;
                setCurrentRaw(normalized);
                editor.setValue(toEditorValue(normalized, mode));
                renderWebsiteAccessReviewSummary(normalized);
                setStatus(t("profiles.wizard_schema_policy_applied"), "info");
                return true;
            } catch (error) {
                setStatus(t("profiles.error_schema_policy").replace("{detail}", error?.message || error), "error");
                return false;
            }
        }

        function appendWebsiteFilterRow(card, field) {
            if (!card || !["Block", "Exceptions"].includes(field)) return;
            const rows = card.querySelector(`[data-website-filter-rows="${field}"]`);
            if (!rows) return;
            rows.querySelector("[data-website-filter-empty]")?.remove();
            const index = rows.querySelectorAll("[data-website-filter-row]").length;
            rows.insertAdjacentHTML("beforeend", websiteFilterRowMarkup(field, "", index, false));
            const input = rows.querySelector("[data-website-filter-row]:last-child [data-website-filter-pattern]");
            refreshWebsiteFilterManagerState(card);
            input?.focus();
        }

        function removeWebsiteFilterRow(card, row) {
            if (!card || !row) return;
            row.remove();
            card.querySelectorAll("[data-website-filter-rows]").forEach((rows) => {
                if (rows.querySelector("[data-website-filter-row]")) return;
                const field = rows.dataset.websiteFilterRows;
                const message = t(field === "Block"
                    ? "profiles.wizard_website_filter_empty_block"
                    : "profiles.wizard_website_filter_empty_allow");
                rows.innerHTML = `<div class="wizard-shell-empty" data-website-filter-empty>${escapeHtml(message)}</div>`;
            });
            applyWebsiteFilterFromCard(card);
        }

        function moveWebsiteFilterRow(card, row, direction) {
            if (!card || !row || !["up", "down"].includes(direction)) return;
            const previous = row.previousElementSibling;
            const next = row.nextElementSibling;
            if (direction === "up" && previous?.matches("[data-website-filter-row]")) {
                row.parentElement?.insertBefore(row, previous);
            }
            if (direction === "down" && next?.matches("[data-website-filter-row]")) {
                row.parentElement?.insertBefore(next, row);
            }
            applyWebsiteFilterFromCard(card);
        }

        function applyWebsiteFilterPostureFromCard(card, posture) {
            if (!card || !["defaults", "block_some", "allow_only", "mixed"].includes(posture)) return;
            const current = readWebsiteFilterManagerValue(card);
            if (current.invalidNewEntries.length) {
                refreshWebsiteFilterManagerState(card);
                setStatus(t("profiles.wizard_website_filter_invalid"), "warn");
                return;
            }
            const result = applyWebsiteFilterPosture(current.value, posture);
            if (!result.ok) return;
            const item = getWizardSchemaPolicyItem(
                "WebsiteFilter",
                wizardSchemaShellCatalog.channels?.[getActiveWizardSchemaVersion()],
                2,
            ) || { id: "WebsiteFilter", target: "policy:WebsiteFilter", label: "Website Filter" };
            renderWebsiteFilterManager(card.parentElement, item, result.value, false);
            applyWebsiteFilterFromCard(card.parentElement.querySelector("[data-schema-policy-card]"));
        }

        function renderMountedSchemaPolicy(container, item, sourceData = {}, disabled = false, policyId = "") {
            if (!container) return;

            if (!item?.inline_editor) {
                renderMountedSchemaPolicyUnavailable(container, policyId);
                return;
            }

            container.hidden = false;
            if (policyId === "WebsiteFilter") {
                renderWebsiteFilterManager(container, item, sourceData?.[item.id], disabled);
                return;
            }
            container.innerHTML = renderWizardSchemaInlineEditor(item, sourceData?.[item.id], disabled);
            review.renderSchemaPolicyReviewState(container.querySelector("[data-schema-policy-card]"));
        }

        function renderMountedSchemaPolicies(sourceData = {}, disabled = false, channelData = null) {
            const resolvedChannelData = channelData || wizardSchemaShellCatalog.channels?.[getActiveWizardSchemaVersion()];

            [
                { el: wizardDnsOverHttpsCardEl, policyId: "DNSOverHTTPS", step: 1 },
                { el: wizardRequestedLocalesCardEl, policyId: "RequestedLocales", step: 5 },
                { el: wizardTranslateEnabledCardEl, policyId: "TranslateEnabled", step: 5 },
                { el: wizardIpProtectionAvailableCardEl, policyId: "IPProtectionAvailable", step: 3 },
                { el: wizardAiControlsCardEl, policyId: "AIControls", step: 7 },
                { el: wizardVisualSearchEnabledCardEl, policyId: "VisualSearchEnabled", step: 7 },
                { el: wizardGenerativeAiCardEl, policyId: "GenerativeAI", step: 7 },
                { el: wizardUserMessagingCardEl, policyId: "UserMessaging", step: 5 },
                { el: wizardWebsiteFilterCardEl, policyId: "WebsiteFilter", step: 2 },
                { el: wizardAllowedDomainsForAppsCardEl, policyId: "AllowedDomainsForApps", step: 2 },
                { el: wizardHttpAllowlistCardEl, policyId: "HttpAllowlist", step: 2 },
                { el: wizardLocalFileLinksCardEl, policyId: "LocalFileLinks", step: 2 },
                { el: wizardHandlersCardEl, policyId: "Handlers", step: 2 },
                { el: wizardAutoLaunchProtocolsCardEl, policyId: "AutoLaunchProtocolsFromOrigins", step: 2 },
                { el: wizardIntranetNavigationCardEl, policyId: "GoToIntranetSiteForSingleWordEntryInAddressBar", step: 2 },
                { el: wizardBookmarksCardEl, policyId: "Bookmarks", step: 2 },
                { el: wizardManagedBookmarksCardEl, policyId: "ManagedBookmarks", step: 2 },
                { el: wizardNoDefaultBookmarksCardEl, policyId: "NoDefaultBookmarks", step: 2 },
                { el: wizardPermissionsCardEl, policyId: "Permissions", step: 3 },
                { el: wizardCookiesCardEl, policyId: "Cookies", step: 3 },
                { el: wizardLocalNetworkAccessCardEl, policyId: "LocalNetworkAccess", step: 3 },
            ].forEach(({ el, policyId, step }) => {
                renderMountedSchemaPolicy(
                    el,
                    getWizardSchemaPolicyItem(policyId, resolvedChannelData, step)
                        || getWizardSchemaPolicyItem(policyId, resolvedChannelData),
                    sourceData,
                    disabled,
                    policyId,
                );
            });

            renderBookmarkReviewSummary(sourceData);
            renderWebsiteAccessReviewSummary(sourceData);
            renderPrivacyReviewSummary(sourceData);
            renderAiReviewSummary(sourceData);
        }

        function renderWizardSchemaShellBadges(container, schemaVersion, compatibility) {
            if (!container) return;

            const badges = [
                {
                    tone: "accent",
                    label: `${t("profiles.wizard_shell_badge_schema")} • ${formatSchemaLabel(schemaVersion)}`,
                },
                {
                    tone: "accent",
                    label: `${t("profiles.wizard_shell_badge_mapped")} • ${compatibility.mapped || 0}`,
                },
                {
                    tone: "warm",
                    label: `${t("profiles.wizard_shell_badge_raw")} • ${compatibility.raw_fallback || 0}`,
                },
            ];
            if ((compatibility.deprecated || 0) > 0) {
                badges.push({
                    tone: "warm",
                    label: `${t("profiles.wizard_shell_badge_deprecated")} • ${compatibility.deprecated}`,
                });
            }

            container.innerHTML = badges
                .map((badge) => `<span class="wizard-shell-badge wizard-shell-badge--${badge.tone}">${escapeHtml(badge.label)}</span>`)
                .join("");
        }

        function renderWizardSchemaShellCoverage(container, compatibility) {
            if (!container) return;

            const total = compatibility.total || 0;
            const mapped = compatibility.mapped || 0;
            const rawFallback = compatibility.raw_fallback || 0;

            let message = "";
            if (total <= 0) {
                message = t("profiles.wizard_shell_coverage_empty");
            } else if (rawFallback <= 0) {
                message = t("profiles.wizard_shell_coverage_full")
                    .replace("{mapped}", String(mapped))
                    .replace("{total}", String(total));
            } else {
                message = t("profiles.wizard_shell_coverage_partial")
                    .replace("{mapped}", String(mapped))
                    .replace("{total}", String(total))
                    .replace("{advanced}", String(rawFallback));
            }

            container.textContent = message;
        }

        function renderWizardSchemaShellPolicyBucket(container, items, emptyMessage, sourceData = {}, disabled = false) {
            if (!container) return;

            if (!Array.isArray(items) || items.length === 0) {
                container.innerHTML = `<div class="wizard-shell-empty">${escapeHtml(emptyMessage)}</div>`;
                return;
            }

            container.innerHTML = items
                .map((item) => {
                    if (item.inline_editor) {
                        return renderWizardSchemaInlineEditor(item, sourceData?.[item.id], disabled);
                    }

                    const tags = Array.isArray(item.tags) && item.tags.length > 0
                        ? `<div class="wizard-shell-item-tags">${item.tags.slice(0, 3).map((tag) => `<span class="wizard-shell-item-tag">${escapeHtml(getShellTagLabel(tag))}</span>`).join("")}</div>`
                        : "";
                    const metaParts = getShellMetaParts(item);

                    return `
                        <button
                            type="button"
                            class="button-base ghost-button wizard-shell-item"
                            data-wizard-shell-target="policy"
                            data-wizard-shell-policy-id="${escapeHtml(item.id || "")}"
                            data-settings-target="${escapeHtml(item.target || "")}">
                            <span class="wizard-shell-item-title">${escapeHtml(getShellPolicyLabel(item))}</span>
                            <span class="wizard-shell-item-meta">${escapeHtml(metaParts.join(" • "))}</span>
                            ${tags}
                        </button>
                    `;
                })
                .join("");

            container.querySelectorAll("[data-schema-policy-card]").forEach((card) => {
                review.renderSchemaPolicyReviewState(card);
            });
        }

        function renderWizardSchemaInlineEditor(item, currentValue, disabled) {
            const inlineEditor = item.inline_editor || {};
            const metaParts = getShellMetaParts(item);
            const policyLabel = getShellPolicyLabel(item);
            const disabledAttr = disabled ? "disabled" : "";
            const currentObject = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue) ? currentValue : {};
            const unsupportedNotice = inlineEditor.unsupported_field_count > 0
                ? `<div class="wizard-input-hint">${escapeHtml(
                    t(
                        "profiles.wizard_shell_inline_partial_notice",
                        "Some nested fields are still preserved through raw JSON.",
                    ),
                )}</div>`
                : "";

            if (inlineEditor.kind === "boolean-select") {
                return `
                    <div
                        class="wizard-shell-card"
                        data-schema-policy-card
                        data-schema-policy-id="${escapeHtml(item.id || "")}"
                        data-schema-policy-kind="boolean-select"
                        data-settings-target="${escapeHtml(item.target || "")}">
                        <div>
                            <div class="wizard-shell-card-title">${escapeHtml(policyLabel)}</div>
                            <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                        </div>
                        <label>
                            <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_shell_field_value"))}</div>
                            <select class="soft-input" data-schema-policy-field="__value__" ${disabledAttr}>
                                ${renderBooleanSelectOptions(currentValue)}
                            </select>
                        </label>
                    </div>
                `;
            }

            if (inlineEditor.kind === "enum-select") {
                const options = [`<option value=""></option>`]
                    .concat((inlineEditor.enum || []).map((option) => `<option value="${escapeHtml(option)}"${currentValue === option ? " selected" : ""}>${escapeHtml(option)}</option>`))
                    .join("");
                return `
                    <div
                        class="wizard-shell-card"
                        data-schema-policy-card
                        data-schema-policy-id="${escapeHtml(item.id || "")}"
                        data-schema-policy-kind="enum-select"
                        data-settings-target="${escapeHtml(item.target || "")}">
                        <div>
                            <div class="wizard-shell-card-title">${escapeHtml(policyLabel)}</div>
                            <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                        </div>
                        <label>
                            <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_shell_field_value"))}</div>
                            <select class="soft-input" data-schema-policy-field="__value__" ${disabledAttr}>
                                ${options}
                            </select>
                        </label>
                    </div>
                `;
            }

            if (inlineEditor.kind === "number") {
                return `
                    <div
                        class="wizard-shell-card"
                        data-schema-policy-card
                        data-schema-policy-id="${escapeHtml(item.id || "")}"
                        data-schema-policy-kind="number"
                        data-settings-target="${escapeHtml(item.target || "")}">
                        <div>
                            <div class="wizard-shell-card-title">${escapeHtml(policyLabel)}</div>
                            <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                        </div>
                        <label>
                            <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_shell_field_value"))}</div>
                            <input type="number" class="soft-input" data-schema-policy-field="__value__" value="${currentValue ?? ""}" ${disabledAttr} />
                        </label>
                    </div>
                `;
            }

            if (inlineEditor.kind === "text") {
                const navigationKind = getNavigationInputKind(item.id, "__value__");
                const navigationAttrs = navigationFieldAttributes(
                    item.id,
                    "__value__",
                    t("profiles.wizard_shell_field_value"),
                    currentValue,
                );
                return `
                    <div
                        class="wizard-shell-card"
                        data-schema-policy-card
                        data-schema-policy-id="${escapeHtml(item.id || "")}"
                        data-schema-policy-kind="text"
                        data-settings-target="${escapeHtml(item.target || "")}">
                        <div>
                            <div class="wizard-shell-card-title">${escapeHtml(policyLabel)}</div>
                            <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                        </div>
                        <label>
                            <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_shell_field_value"))}</div>
                            <input type="text" class="soft-input" data-schema-policy-field="__value__" value="${escapeHtml(currentValue ?? "")}"${navigationAttrs} ${disabledAttr} />
                            ${navigationKind ? renderImportedNavigationRawNotice(currentValue, navigationKind, t("profiles.wizard_shell_field_value")) : ""}
                            ${navigationKind ? renderNavigationExternalLink(currentValue, navigationKind) : ""}
                        </label>
                    </div>
                `;
            }

            if (inlineEditor.kind === "string-list") {
                const listEditor = renderSchemaListEditor({
                    policyId: item.id,
                    field: { name: "__value__", label: policyLabel, kind: "string-list" },
                    fieldPath: "__value__",
                    currentValue,
                    disabled,
                    targetAttr: 'data-schema-policy-field="__value__"',
                    kindAttr: 'data-schema-field-kind="string-list"',
                });
                return `
                    <div
                        class="wizard-shell-card"
                        data-schema-policy-card
                        data-schema-policy-id="${escapeHtml(item.id || "")}"
                        data-schema-policy-kind="string-list"
                        data-settings-target="${escapeHtml(item.target || "")}">
                        <div>
                            <div class="wizard-shell-card-title">${escapeHtml(policyLabel)}</div>
                            <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                        </div>
                        ${listEditor}
                    </div>
                `;
            }

            if (inlineEditor.kind === "branch") {
                const branchMode = typeof currentValue === "boolean"
                    ? "boolean"
                    : (currentValue && typeof currentValue === "object" && !Array.isArray(currentValue) ? "object" : "");
                const objectBranch = (inlineEditor.branches || []).find((branch) => branch.id === "object");
                const objectValue = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue) ? currentValue : {};
                const objectFieldsMarkup = (objectBranch?.fields || [])
                    .map((field) => renderWizardSchemaInlineField(item.id, field, objectValue[field.name], disabled))
                    .join("");

                return `
                    <div
                        class="wizard-shell-card"
                        data-schema-policy-card
                        data-schema-policy-id="${escapeHtml(item.id || "")}"
                        data-schema-policy-kind="branch"
                        data-schema-branch-object-managed-fields="${escapeHtml(((objectBranch?.managed_fields) || []).join(","))}"
                        data-settings-target="${escapeHtml(item.target || "")}">
                        <div>
                            <div class="wizard-shell-card-title">${escapeHtml(policyLabel)}</div>
                            <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                        </div>
                        <label>
                            <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_shell_branch_mode_label"))}</div>
                            <select class="soft-input" data-schema-branch-mode ${disabledAttr}>
                                <option value=""></option>
                                <option value="boolean"${branchMode === "boolean" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_shell_branch_mode_simple"))}</option>
                                <option value="object"${branchMode === "object" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_shell_branch_mode_custom"))}</option>
                            </select>
                        </label>
                        <div data-schema-branch-section="boolean"${branchMode === "boolean" ? "" : " hidden"}>
                            <label>
                                <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_shell_field_value"))}</div>
                                <select class="soft-input" data-schema-policy-field="__branch_boolean__" ${disabledAttr}>
                                    ${renderBooleanSelectOptions(typeof currentValue === "boolean" ? currentValue : null)}
                                </select>
                            </label>
                        </div>
                        <div data-schema-branch-section="object"${branchMode === "object" ? "" : " hidden"}>
                            <div class="wizard-grid">
                                ${objectFieldsMarkup}
                            </div>
                        </div>
                    </div>
                `;
            }

            if (inlineEditor.kind === "array-of-objects") {
                const rows = Array.isArray(currentValue) ? currentValue : [];
                const rowMarkup = rows.length > 0
                    ? rows.map((rowValue, index) => renderWizardSchemaArrayRow(item, inlineEditor, rowValue, index, disabled)).join("")
                    : `<div class="wizard-shell-empty">${escapeHtml(t("profiles.wizard_shell_array_empty"))}</div>`;

                return `
                    <div
                        class="wizard-shell-card"
                        data-schema-policy-card
                        data-schema-policy-id="${escapeHtml(item.id || "")}"
                        data-schema-policy-kind="array-of-objects"
                        data-settings-target="${escapeHtml(item.target || "")}">
                        <div class="wizard-search-engine-head">
                            <div>
                                <div class="wizard-shell-card-title">${escapeHtml(policyLabel)}</div>
                                <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                            </div>
                            <button type="button" class="button-base ghost-button" data-schema-array-add ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_array_add"))}</button>
                        </div>
                        <div class="wizard-search-engine-list" data-schema-array-list>
                            ${rowMarkup}
                        </div>
                    </div>
                `;
            }

            if (inlineEditor.kind === "dictionary-object") {
                const entries = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue)
                    ? Object.entries(currentValue)
                    : [];
                const rowMarkup = entries.length > 0
                    ? entries.map(([entryKey, entryValue], index) => renderWizardSchemaDictionaryRow(item, inlineEditor, entryKey, entryValue, index, disabled)).join("")
                    : `<div class="wizard-shell-empty">${escapeHtml(t("profiles.wizard_shell_dictionary_empty"))}</div>`;

                return `
                    <div
                        class="wizard-shell-card"
                        data-schema-policy-card
                        data-schema-policy-id="${escapeHtml(item.id || "")}"
                        data-schema-policy-kind="dictionary-object"
                        data-settings-target="${escapeHtml(item.target || "")}">
                        <div class="wizard-search-engine-head">
                            <div>
                                <div class="wizard-shell-card-title">${escapeHtml(policyLabel)}</div>
                                <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                            </div>
                            <button type="button" class="button-base ghost-button" data-schema-dict-add ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_dictionary_add"))}</button>
                        </div>
                        <div class="wizard-search-engine-list" data-schema-dict-list>
                            ${rowMarkup}
                        </div>
                    </div>
                `;
            }

            const fieldsMarkup = renderTaskFirstObjectFields(
                item.id,
                inlineEditor.fields || [],
                currentObject,
                disabled,
            );

            return `
                <div
                    class="wizard-shell-card"
                    data-schema-policy-card
                    data-schema-policy-id="${escapeHtml(item.id || "")}"
                    data-schema-policy-kind="object-card"
                    data-schema-managed-fields="${escapeHtml((inlineEditor.managed_fields || []).join(","))}"
                    data-settings-target="${escapeHtml(item.target || "")}">
                    <div>
                        <div class="wizard-shell-card-title">${escapeHtml(policyLabel)}</div>
                        <div class="wizard-shell-card-copy">${escapeHtml(metaParts.join(" • "))}</div>
                        ${["Authentication", "Certificates", "Cookies", "DNSOverHTTPS", "Handlers", "Permissions", "UserMessaging", "WebsiteFilter"].includes(item.id) ? `<div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-object-status></div>` : ""}
                    </div>
                    ${fieldsMarkup}
                    ${unsupportedNotice}
                </div>
            `;
        }

        function renderWizardSchemaInlineField(policyId, field, currentValue, disabled) {
            const disabledAttr = disabled ? "disabled" : "";
            const label = getSchemaFieldLabel(field);
            const fieldName = escapeHtml(field.name || "");
            const fieldPath = field.name || "";
            const navigationKind = getNavigationInputKind(policyId, fieldPath);
            const navigationAttrs = navigationFieldAttributes(policyId, fieldPath, label, currentValue);

            if (field.kind === "nested-object") {
                const nestedValue = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue)
                    ? currentValue
                    : {};
                const nestedFieldsMarkup = renderTaskFirstNestedFields(policyId, fieldPath, field, nestedValue, disabled);
                const unsupportedNotice = (field.unsupported_field_count || 0) > 0
                    ? `<div class="wizard-input-hint">${escapeHtml(t("profiles.wizard_shell_nested_unsupported"))}</div>`
                    : "";

                return `
                    <div class="wizard-field-full" data-schema-policy-field="${fieldName}" data-schema-field-kind="nested-object" data-schema-nested-path="${escapeHtml(fieldPath)}">
                        <div class="wizard-search-engine-head">
                            <div>
                                <div class="field-label mb-1">${escapeHtml(label)}</div>
                                <div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-nested-status></div>
                            </div>
                        </div>
                        <div class="wizard-section-group">
                            <div class="wizard-grid">
                                ${nestedFieldsMarkup}
                            </div>
                            ${unsupportedNotice}
                        </div>
                    </div>
                `;
            }

            if (field.kind === "boolean-select") {
                return `
                    <label>
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <select class="soft-input" data-schema-policy-field="${fieldName}" data-schema-field-kind="boolean-select" ${disabledAttr}>
                            ${renderBooleanSelectOptions(currentValue)}
                        </select>
                    </label>
                `;
            }

            if (field.kind === "enum-select") {
                const options = [`<option value=""></option>`]
                    .concat((field.enum || []).map((option) => `<option value="${escapeHtml(option)}"${currentValue === option ? " selected" : ""}>${escapeHtml(option)}</option>`))
                    .join("");
                return `
                    <label>
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <select class="soft-input" data-schema-policy-field="${fieldName}" data-schema-field-kind="enum-select" ${disabledAttr}>
                            ${options}
                        </select>
                    </label>
                `;
            }

            if (field.kind === "string-list") {
                return renderSchemaListEditor({
                    policyId,
                    field,
                    fieldPath,
                    currentValue,
                    disabled,
                    targetAttr: `data-schema-policy-field="${fieldName}"`,
                    kindAttr: `data-schema-field-kind="string-list"`,
                });
            }

            if (field.kind === "true-map") {
                return renderSchemaListEditor({
                    policyId,
                    field,
                    fieldPath,
                    currentValue,
                    disabled,
                    targetAttr: `data-schema-policy-field="${fieldName}"`,
                    kindAttr: `data-schema-field-kind="true-map"`,
                });
            }

            if (field.kind === "json") {
                const serialized = currentValue == null
                    ? ""
                    : JSON.stringify(currentValue, null, 2);
                return `
                    <label class="wizard-field-full">
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <textarea class="soft-input" rows="4" data-schema-policy-field="${fieldName}" data-schema-field-kind="json" ${disabledAttr}>${escapeHtml(serialized)}</textarea>
                        <div class="wizard-input-hint">${escapeHtml(t("profiles.wizard_shell_json_hint"))}</div>
                    </label>
                `;
            }

            if (field.kind === "number") {
                return `
                    <label>
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <input type="number" class="soft-input" data-schema-policy-field="${fieldName}" data-schema-field-kind="number" value="${currentValue ?? ""}" ${disabledAttr} />
                    </label>
                `;
            }

            return `
                <label>
                    <div class="field-label mb-1">${escapeHtml(label)}</div>
                    <input type="text" class="soft-input" data-schema-policy-field="${fieldName}" data-schema-field-kind="text" value="${escapeHtml(currentValue ?? "")}"${navigationAttrs} ${disabledAttr} />
                    ${navigationKind ? renderImportedNavigationRawNotice(currentValue, navigationKind, label) : ""}
                    ${navigationKind ? renderNavigationExternalLink(currentValue, navigationKind) : ""}
                </label>
            `;
        }

        function renderWizardSchemaNestedField(policyId, parentFieldName, field, currentValue, disabled) {
            const disabledAttr = disabled ? "disabled" : "";
            const label = getSchemaFieldLabel(field);
            const fieldName = escapeHtml(field.name || "");
            const fieldPath = parentFieldName ? `${parentFieldName}.${field.name || ""}` : (field.name || "");
            const navigationKind = getNavigationInputKind(policyId, fieldPath);
            const navigationAttrs = navigationFieldAttributes(policyId, fieldPath, label, currentValue);

            if (field.kind === "nested-dictionary-object") {
                const uiCopy = getNestedFieldUiCopy(policyId, fieldPath, field);
                const rowField = {
                    ...field,
                    entryKeyLabel: uiCopy?.keyLabel || "",
                    metaLabel: uiCopy?.metaLabel || "",
                };
                const entries = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue)
                    ? Object.entries(currentValue)
                    : [];
                const rowMarkup = entries.length > 0
                    ? entries.map(([entryKey, entryValue], index) => renderWizardSchemaNestedDictionaryRow(rowField, entryKey, entryValue, index, disabled)).join("")
                    : `<div class="wizard-shell-empty" data-schema-nested-empty>${escapeHtml(t("profiles.wizard_shell_dictionary_empty"))}</div>`;

                return `
                    <div
                        class="wizard-field-full"
                        data-schema-nested-field="${fieldName}"
                        data-schema-nested-kind="nested-dictionary-object"
                        data-schema-nested-path="${escapeHtml(fieldPath)}"
                        data-schema-nested-label="${escapeHtml(label)}"
                        data-schema-entry-key-label="${escapeHtml(uiCopy?.keyLabel || t("profiles.wizard_shell_dictionary_key_label"))}"
                        data-schema-entry-meta-label="${escapeHtml(uiCopy?.metaLabel || t("profiles.wizard_shell_dictionary_item_meta"))}"
                        data-schema-nested-fields='${escapeHtml(JSON.stringify(field.fields || []))}'>
                        <div class="wizard-search-engine-head">
                            <div>
                                <div class="field-label mb-1">${escapeHtml(label)}</div>
                                <div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-nested-status></div>
                                ${uiCopy?.intro ? `<div class="wizard-input-hint">${escapeHtml(uiCopy.intro)}</div>` : ""}
                            </div>
                            <button type="button" class="button-base ghost-button" data-schema-nested-dict-add ${disabledAttr}>${escapeHtml(uiCopy?.addLabel || t("profiles.wizard_shell_dictionary_add"))}</button>
                        </div>
                        <div class="wizard-search-engine-list" data-schema-nested-dict-list>
                            ${rowMarkup}
                        </div>
                    </div>
                `;
            }

            if (field.kind === "nested-array-of-objects") {
                const uiCopy = getNestedFieldUiCopy(policyId, fieldPath, field);
                const rows = Array.isArray(currentValue) ? currentValue : [];
                const rowMarkup = rows.length > 0
                    ? rows.map((rowValue, index) => renderWizardSchemaNestedArrayRow(field, rowValue, index, disabled)).join("")
                    : `<div class="wizard-shell-empty" data-schema-nested-empty>${escapeHtml(t("profiles.wizard_shell_array_empty"))}</div>`;

                return `
                    <div
                        class="wizard-field-full"
                        data-schema-nested-field="${fieldName}"
                        data-schema-nested-kind="nested-array-of-objects"
                        data-schema-nested-path="${escapeHtml(fieldPath)}"
                        data-schema-nested-label="${escapeHtml(label)}"
                        data-schema-nested-fields='${escapeHtml(JSON.stringify(field.fields || []))}'>
                        <div class="wizard-search-engine-head">
                            <div>
                                <div class="field-label mb-1">${escapeHtml(label)}</div>
                                <div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-nested-status></div>
                                ${uiCopy?.intro ? `<div class="wizard-input-hint">${escapeHtml(uiCopy.intro)}</div>` : ""}
                            </div>
                            <button type="button" class="button-base ghost-button" data-schema-nested-array-add ${disabledAttr}>${escapeHtml(uiCopy?.addLabel || t("profiles.wizard_shell_array_add"))}</button>
                        </div>
                        <div class="wizard-search-engine-list" data-schema-nested-array-list>
                            ${rowMarkup}
                        </div>
                    </div>
                `;
            }

            if (field.kind === "nested-object") {
                const nestedValue = currentValue && typeof currentValue === "object" && !Array.isArray(currentValue)
                    ? currentValue
                    : {};
                const nestedFieldsMarkup = renderTaskFirstNestedFields(policyId, fieldPath, field, nestedValue, disabled);
                const unsupportedNotice = (field.unsupported_field_count || 0) > 0
                    ? `<div class="wizard-input-hint">${escapeHtml(t("profiles.wizard_shell_nested_unsupported"))}</div>`
                    : "";

                return `
                    <div class="wizard-field-full" data-schema-nested-field="${fieldName}" data-schema-nested-kind="nested-object" data-schema-nested-path="${escapeHtml(fieldPath)}">
                        <div class="wizard-search-engine-head">
                            <div>
                                <div class="field-label mb-1">${escapeHtml(label)}</div>
                                <div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-nested-status></div>
                            </div>
                        </div>
                        <div class="wizard-section-group">
                            <div class="wizard-grid">
                                ${nestedFieldsMarkup}
                            </div>
                            ${unsupportedNotice}
                        </div>
                    </div>
                `;
            }

            if (field.kind === "boolean-select") {
                return `
                    <label>
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <select class="soft-input" data-schema-nested-field="${fieldName}" data-schema-nested-kind="boolean-select" ${disabledAttr}>
                            ${renderBooleanSelectOptions(currentValue)}
                        </select>
                    </label>
                `;
            }

            if (field.kind === "enum-select") {
                const options = [`<option value=""></option>`]
                    .concat((field.enum || []).map((option) => `<option value="${escapeHtml(option)}"${currentValue === option ? " selected" : ""}>${escapeHtml(option)}</option>`))
                    .join("");
                return `
                    <label>
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <select class="soft-input" data-schema-nested-field="${fieldName}" data-schema-nested-kind="enum-select" ${disabledAttr}>
                            ${options}
                        </select>
                    </label>
                `;
            }

            if (field.kind === "string-list") {
                return renderSchemaListEditor({
                    policyId,
                    field,
                    fieldPath,
                    currentValue,
                    disabled,
                    targetAttr: `data-schema-nested-field="${fieldName}"`,
                    kindAttr: `data-schema-nested-kind="string-list"`,
                });
            }

            if (field.kind === "true-map") {
                return renderSchemaListEditor({
                    policyId,
                    field,
                    fieldPath,
                    currentValue,
                    disabled,
                    targetAttr: `data-schema-nested-field="${fieldName}"`,
                    kindAttr: `data-schema-nested-kind="true-map"`,
                });
            }

            if (field.kind === "json") {
                const serialized = currentValue == null
                    ? ""
                    : JSON.stringify(currentValue, null, 2);
                return `
                    <label class="wizard-field-full">
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <textarea class="soft-input" rows="4" data-schema-nested-field="${fieldName}" data-schema-nested-kind="json" ${disabledAttr}>${escapeHtml(serialized)}</textarea>
                        <div class="wizard-input-hint">${escapeHtml(t("profiles.wizard_shell_json_hint"))}</div>
                    </label>
                `;
            }

            if (field.kind === "number") {
                return `
                    <label>
                        <div class="field-label mb-1">${escapeHtml(label)}</div>
                        <input type="number" class="soft-input" data-schema-nested-field="${fieldName}" data-schema-nested-kind="number" value="${currentValue ?? ""}" ${disabledAttr} />
                    </label>
                `;
            }

            return `
                <label>
                    <div class="field-label mb-1">${escapeHtml(label)}</div>
                    <input type="text" class="soft-input" data-schema-nested-field="${fieldName}" data-schema-nested-kind="text" value="${escapeHtml(currentValue ?? "")}"${navigationAttrs} ${disabledAttr} />
                    ${navigationKind ? renderImportedNavigationRawNotice(currentValue, navigationKind, label) : ""}
                    ${navigationKind ? renderNavigationExternalLink(currentValue, navigationKind) : ""}
                </label>
            `;
        }

        function renderWizardSchemaNestedArrayRow(field, rowValue, index, disabled) {
            const disabledAttr = disabled ? "disabled" : "";
            const currentObject = rowValue && typeof rowValue === "object" && !Array.isArray(rowValue) ? rowValue : {};
            const rowTitle = currentObject.name
                || currentObject.Title
                || currentObject.URL
                || currentObject.path
                || `${getSchemaFieldLabel(field) || field.name || "Item"} ${index + 1}`;
            const fieldsMarkup = (field.fields || [])
                .map((nestedField) => renderWizardSchemaNestedField("", field.name || "", nestedField, currentObject[nestedField.name], disabled))
                .join("");

            return `
                <div class="wizard-search-engine-card" data-schema-nested-array-row data-schema-nested-array-index="${index}">
                    <div class="wizard-search-engine-head">
                        <div>
                            <div class="wizard-search-engine-title">${escapeHtml(rowTitle)}</div>
                            <div class="wizard-search-engine-meta">${escapeHtml(t("profiles.wizard_shell_array_item_meta"))} ${index + 1}</div>
                        </div>
                        <button type="button" class="button-base danger-button" data-schema-nested-array-remove ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_array_remove"))}</button>
                    </div>
                    <div class="wizard-grid">
                        ${fieldsMarkup}
                    </div>
                </div>
            `;
        }

        function renderWizardSchemaNestedDictionaryRow(field, entryKey, entryValue, index, disabled) {
            const disabledAttr = disabled ? "disabled" : "";
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            const rowTitle = entryKey || `${getSchemaFieldLabel(field) || field.name || "Entry"} ${index + 1}`;
            const keyLabel = field.entryKeyLabel || t("profiles.wizard_shell_dictionary_key_label");
            const metaLabel = field.metaLabel || t("profiles.wizard_shell_dictionary_item_meta");
            const fieldsMarkup = (field.fields || [])
                .map((nestedField) => renderWizardSchemaNestedField("", field.name || "", nestedField, currentObject[nestedField.name], disabled))
                .join("");

            return `
                <div class="wizard-search-engine-card" data-schema-nested-dict-row data-schema-nested-dict-index="${index}">
                    <div class="wizard-search-engine-head">
                        <div>
                            <div class="wizard-search-engine-title">${escapeHtml(rowTitle)}</div>
                            <div class="wizard-search-engine-meta">${escapeHtml(metaLabel)} ${index + 1}</div>
                        </div>
                        <button type="button" class="button-base danger-button" data-schema-nested-dict-remove ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_dictionary_remove"))}</button>
                    </div>
                    <label class="wizard-field-full">
                        <div class="field-label mb-1">${escapeHtml(keyLabel)}</div>
                        <input type="text" class="soft-input" data-schema-nested-dict-key value="${escapeHtml(entryKey || "")}" ${disabledAttr} />
                    </label>
                    <div class="wizard-grid">
                        ${fieldsMarkup}
                    </div>
                </div>
            `;
        }

        function renderBooleanSelectOptions(currentValue) {
            const selected = formatBooleanSelectValue(currentValue);
            return `
                <option value=""></option>
                <option value="true"${selected === "true" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_shell_boolean_true"))}</option>
                <option value="false"${selected === "false" ? " selected" : ""}>${escapeHtml(t("profiles.wizard_shell_boolean_false"))}</option>
            `;
        }

        function renderWizardSchemaArrayRow(item, inlineEditor, rowValue, index, disabled) {
            const disabledAttr = disabled ? "disabled" : "";
            const currentObject = rowValue && typeof rowValue === "object" && !Array.isArray(rowValue) ? rowValue : {};
            const rowTitle = currentObject.Title
                || currentObject.name
                || currentObject.toplevel_name
                || currentObject.URL
                || currentObject.url
                || `${item.label || item.id} ${index + 1}`;
            const fieldsMarkup = (inlineEditor.fields || [])
                .map((field) => renderWizardSchemaInlineField(item.id, field, currentObject[field.name], disabled))
                .join("");
            const statusMarkup = ["Bookmarks", "ManagedBookmarks"].includes(item.id)
                ? `<div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-array-status></div>`
                : "";

            return `
                <div class="wizard-search-engine-card" data-schema-array-row data-schema-array-index="${index}">
                    <div class="wizard-search-engine-head">
                        <div>
                            <div class="wizard-search-engine-title">${escapeHtml(rowTitle)}</div>
                            <div class="wizard-search-engine-meta">${escapeHtml(t("profiles.wizard_shell_array_item_meta"))} ${index + 1}</div>
                            ${statusMarkup}
                        </div>
                        <button type="button" class="button-base danger-button" data-schema-array-remove data-schema-array-index="${index}" ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_array_remove"))}</button>
                    </div>
                    <div class="wizard-grid">
                        ${fieldsMarkup}
                    </div>
                </div>
            `;
        }

        function renderWizardSchemaDictionaryRow(item, inlineEditor, entryKey, entryValue, index, disabled) {
            const disabledAttr = disabled ? "disabled" : "";
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            const rowTitle = entryKey || `${item.label || item.id} ${index + 1}`;
            const fieldsMarkup = (inlineEditor.fields || [])
                .map((field) => renderWizardSchemaInlineField(item.id, field, currentObject[field.name], disabled))
                .join("");
            const statusMarkup = item.id === "ExtensionSettings"
                ? `<div class="wizard-search-engine-preset-copy wizard-search-engine-preset-status" data-schema-dict-status></div>`
                : "";

            return `
                <div class="wizard-search-engine-card" data-schema-dict-row data-schema-dict-index="${index}">
                    <div class="wizard-search-engine-head">
                        <div>
                            <div class="wizard-search-engine-title">${escapeHtml(rowTitle)}</div>
                            <div class="wizard-search-engine-meta">${escapeHtml(t("profiles.wizard_shell_dictionary_item_meta"))} ${index + 1}</div>
                            ${statusMarkup}
                        </div>
                        <button type="button" class="button-base danger-button" data-schema-dict-remove data-schema-dict-index="${index}" ${disabledAttr}>${escapeHtml(t("profiles.wizard_shell_dictionary_remove"))}</button>
                    </div>
                    <label class="wizard-field-full">
                        <div class="field-label mb-1">${escapeHtml(t("profiles.wizard_shell_dictionary_key_label"))}</div>
                        <input type="text" class="soft-input" data-schema-dict-key value="${escapeHtml(entryKey || "")}" ${disabledAttr} />
                    </label>
                    <div class="wizard-grid">
                        ${fieldsMarkup}
                    </div>
                </div>
            `;
        }

        const actions = createActions({
            documentRef,
            dependencies: {
                t,
                escapeHtml,
                fromEditorValue,
                toEditorValue,
                setStatus,
                parseBooleanSelectValue,
                onDocumentChange,
            },
            state: {
                getEditor,
                setCurrentRaw,
            },
            helpers: {
                ...valueIO,
                renderWizardSchemaNestedArrayRow,
                renderWizardSchemaNestedDictionaryRow,
            },
        });

        function toSnakeCase(value = "") {
            return String(value)
                .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
                .replace(/[-:\s]+/g, "_")
                .toLowerCase();
        }

        function getShellPolicyLabel(item) {
            const policyId = String(item?.id || "").trim();
            if (!policyId) return "";
            return t(`profiles.shell_policy_${toSnakeCase(policyId)}`);
        }

        function getShellSubsectionLabel(subsection) {
            const normalized = String(subsection || "").trim();
            if (!normalized) return "";
            return t(`profiles.wizard_shell_subsection_${normalized}`);
        }

        function getSchemaFieldLabel(field) {
            const fallback = field?.label || humanizeIdentifier(field?.name || "");
            return field?.label_key ? t(field.label_key) : fallback;
        }

        function getShellWidgetLabel(widget) {
            const normalized = String(widget || "").trim();
            if (!normalized) return "";
            return t(`profiles.wizard_shell_widget_${normalized}`);
        }

        function getShellTagLabel(tag) {
            const normalized = String(tag || "").trim();
            if (!normalized) return "";
            return t(`profiles.wizard_shell_tag_${normalized}`);
        }

        function getShellMetaParts(item) {
            return [
                getShellSubsectionLabel(item?.subsection || item?.subsection_label || ""),
                getShellWidgetLabel(item?.widget || ""),
                item?.complexity === "basic"
                    ? t("profiles.wizard_shell_meta_basic")
                    : t("profiles.wizard_shell_meta_advanced"),
            ].filter(Boolean);
        }

        function renderWizardSchemaShellPreferenceBucket(container, items, emptyMessage) {
            if (!container) return;

            if (!Array.isArray(items) || items.length === 0) {
                container.innerHTML = `<div class="wizard-shell-empty">${escapeHtml(emptyMessage)}</div>`;
                return;
            }

            container.innerHTML = items
                .map((item) => {
                    const meta = t("profiles.wizard_shell_preferences_meta")
                        .replace("{prefixes}", String(item.prefix_count || 0))
                        .replace("{presets}", String(item.preset_count || 0));

                    return `
                        <button
                            type="button"
                            class="button-base ghost-button wizard-shell-item"
                            data-wizard-shell-jump="preferences"
                            data-settings-jump-target="${escapeHtml(item.target || "")}">
                            <span class="wizard-shell-item-title">${escapeHtml(t(item.title_key))}</span>
                            <span class="wizard-shell-item-meta">${escapeHtml(meta)}</span>
                        </button>
                    `;
                })
                .join("");
        }

        return {
            renderWizardSchemaShell,
            renderSchemaPolicyEditorCard: renderWizardSchemaInlineEditor,
            renderSchemaPolicyReviewState: review.renderSchemaPolicyReviewState,
            applySchemaPolicyFromCard: actions.applySchemaPolicyFromCard,
            refreshWebsiteFilterManagerState,
            applyWebsiteFilterFromCard,
            appendWebsiteFilterRow,
            removeWebsiteFilterRow,
            moveWebsiteFilterRow,
            applyWebsiteFilterPostureFromCard,
            refreshSchemaListRows: actions.refreshSchemaListRows,
            appendSchemaListItem: actions.appendSchemaListItem,
            removeSchemaListItem: actions.removeSchemaListItem,
            refreshSchemaNestedArrayRows: actions.refreshSchemaNestedArrayRows,
            refreshSchemaNestedDictionaryRows: actions.refreshSchemaNestedDictionaryRows,
            appendSchemaNestedArrayItem: actions.appendSchemaNestedArrayItem,
            removeSchemaNestedArrayItem: actions.removeSchemaNestedArrayItem,
            appendSchemaNestedDictionaryEntry: actions.appendSchemaNestedDictionaryEntry,
            removeSchemaNestedDictionaryEntry: actions.removeSchemaNestedDictionaryEntry,
            appendSchemaArrayItem: actions.appendSchemaArrayItem,
            removeSchemaArrayItem: actions.removeSchemaArrayItem,
            appendSchemaDictionaryEntry: actions.appendSchemaDictionaryEntry,
            removeSchemaDictionaryEntry: actions.removeSchemaDictionaryEntry,
            getAuthenticationObjectSummary: review.getAuthenticationObjectSummary,
            formatAuthenticationObjectState: review.formatAuthenticationObjectState,
            getCertificatesObjectSummary: review.getCertificatesObjectSummary,
            formatCertificatesObjectState: review.formatCertificatesObjectState,
            getDnsOverHttpsObjectSummary: review.getDnsOverHttpsObjectSummary,
            formatDnsOverHttpsObjectState: review.formatDnsOverHttpsObjectState,
            getWebsiteFilterObjectSummary: review.getWebsiteFilterObjectSummary,
            formatWebsiteFilterObjectState: review.formatWebsiteFilterObjectState,
            getPermissionsObjectSummary: review.getPermissionsObjectSummary,
            formatPermissionsObjectState: review.formatPermissionsObjectState,
            getCookiesObjectSummary: review.getCookiesObjectSummary,
            formatCookiesObjectState: review.formatCookiesObjectState,
            getHandlersObjectSummary: review.getHandlersObjectSummary,
            formatHandlersObjectState: review.formatHandlersObjectState,
            getUserMessagingObjectSummary: review.getUserMessagingObjectSummary,
            formatUserMessagingObjectState: review.formatUserMessagingObjectState,
        };
    }

    export { create };
