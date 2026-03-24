(() => {
    function create({
        documentRef = document,
        dependencies = {},
        helpers = {},
    }) {
        const { t, getManagedExtensionProfileById } = dependencies;
        const {
            readSchemaArrayRowEntry,
            readSchemaDictionaryRowEntry,
            readSchemaObjectCardValue,
            getSchemaNestedValueAtPath,
            pathHasSchemaParseError,
        } = helpers;

        function countHandlerRuleBucket(bucket) {
            return bucket && typeof bucket === "object" && !Array.isArray(bucket)
                ? Object.keys(bucket).filter(Boolean).length
                : 0;
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

        function getBookmarkArrayRowState(policyId, entryValue, parseErrors = []) {
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};

            if (policyId === "Bookmarks") {
                const title = typeof currentObject.Title === "string" ? currentObject.Title.trim() : "";
                const url = typeof currentObject.URL === "string" ? currentObject.URL.trim() : "";
                const placement = typeof currentObject.Placement === "string" ? currentObject.Placement.trim() : "";
                const hasAny = Boolean(title || url || placement);

                if (!hasAny) return "empty";
                if (title && url && placement === "toolbar") return "toolbar";
                if (title && url && placement === "menu") return "menu";
                return "draft";
            }

            if (policyId === "ManagedBookmarks") {
                const folderName = typeof currentObject.toplevel_name === "string" ? currentObject.toplevel_name.trim() : "";
                const hasChildren = Array.isArray(currentObject.children) && currentObject.children.length > 0;
                const hasAny = Boolean(folderName || hasChildren || parseErrors.length > 0);

                if (!hasAny) return "empty";
                if (parseErrors.includes("children")) return "invalid";
                if (folderName && hasChildren) return "children";
                if (folderName) return "name_only";
                if (hasChildren) return "tree_only";
                return "draft";
            }

            return "empty";
        }

        function formatBookmarkArrayRowState(policyId, state) {
            if (policyId === "Bookmarks") {
                if (state === "toolbar") {
                    return t("profiles.wizard_bookmarks_row_state_toolbar", "Toolbar bookmark");
                }
                if (state === "menu") {
                    return t("profiles.wizard_bookmarks_row_state_menu", "Menu bookmark");
                }
                if (state === "draft") {
                    return t("profiles.wizard_bookmarks_row_state_draft", "Incomplete bookmark");
                }
                return t("profiles.wizard_bookmarks_row_state_empty", "No bookmark fields yet");
            }

            if (state === "children") {
                return t("profiles.wizard_managed_bookmarks_row_state_children", "Folder with nested children");
            }
            if (state === "name_only") {
                return t("profiles.wizard_managed_bookmarks_row_state_name_only", "Folder name only");
            }
            if (state === "tree_only") {
                return t("profiles.wizard_managed_bookmarks_row_state_tree_only", "Children tree only");
            }
            if (state === "invalid") {
                return t("profiles.wizard_managed_bookmarks_row_state_invalid", "Children JSON needs attention");
            }
            return t("profiles.wizard_managed_bookmarks_row_state_empty", "No managed folder fields yet");
        }

        function renderBookmarkArrayStatuses(card) {
            if (!card || !["Bookmarks", "ManagedBookmarks"].includes(card.dataset.schemaPolicyId || "") || card.dataset.schemaPolicyKind !== "array-of-objects") {
                return;
            }

            const policyId = card.dataset.schemaPolicyId || "";
            const rows = Array.from(card.querySelectorAll("[data-schema-array-row]"));

            rows.forEach((row) => {
                const { entryValue, parseErrors } = readSchemaArrayRowEntry(row);
                const state = getBookmarkArrayRowState(policyId, entryValue, parseErrors);
                let statusEl = row.querySelector("[data-schema-array-status]");

                if (!statusEl) {
                    statusEl = documentRef.createElement("div");
                    statusEl.className = "wizard-search-engine-preset-copy wizard-search-engine-preset-status";
                    statusEl.dataset.schemaArrayStatus = "true";
                    row.querySelector(".wizard-search-engine-head > div")?.appendChild(statusEl);
                }

                statusEl.textContent = formatBookmarkArrayRowState(policyId, state);
                row.dataset.schemaArrayRowState = state;
                row.classList.remove(
                    "wizard-search-engine-preset--applied",
                    "wizard-search-engine-preset--partial",
                    "wizard-search-engine-preset--conflict",
                );
                if (["toolbar", "menu", "children"].includes(state)) {
                    row.classList.add("wizard-search-engine-preset--applied");
                }
                if (["draft", "name_only", "tree_only"].includes(state)) {
                    row.classList.add("wizard-search-engine-preset--partial");
                }
                if (state === "invalid") {
                    row.classList.add("wizard-search-engine-preset--conflict");
                }
            });
        }

        function getWebsiteFilterObjectSummary(entryValue, parseErrors = []) {
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            const blockedCount = Array.isArray(currentObject.Block) ? currentObject.Block.length : 0;
            const exceptionCount = Array.isArray(currentObject.Exceptions) ? currentObject.Exceptions.length : 0;
            const hasRules = blockedCount > 0 || exceptionCount > 0 || parseErrors.length > 0;
            let state = "empty";

            if (parseErrors.length > 0) {
                state = "invalid";
            } else if (blockedCount > 0 && exceptionCount > 0) {
                state = "configured";
            } else if (blockedCount > 0 || exceptionCount > 0) {
                state = "partial";
            }

            return {
                blockedCount,
                exceptionCount,
                hasRules,
                state,
            };
        }

        function countSchemaObjectEntries(entryValue) {
            return entryValue && typeof entryValue === "object" && !Array.isArray(entryValue)
                ? Object.keys(entryValue).filter(Boolean).length
                : 0;
        }

        function formatWebsiteFilterObjectState(summary) {
            if (summary.state === "invalid") {
                return t("profiles.wizard_website_filter_state_invalid", "Site filter values need attention");
            }
            if (summary.state === "configured") {
                return t("profiles.wizard_website_filter_state_configured", "Blocked: {blocked} • Exceptions: {exceptions}")
                    .replace("{blocked}", String(summary.blockedCount))
                    .replace("{exceptions}", String(summary.exceptionCount));
            }
            if (summary.blockedCount > 0) {
                return t("profiles.wizard_website_filter_state_blocked_only", "Blocked sites: {blocked}")
                    .replace("{blocked}", String(summary.blockedCount));
            }
            if (summary.exceptionCount > 0) {
                return t("profiles.wizard_website_filter_state_exceptions_only", "Exceptions only: {exceptions}")
                    .replace("{exceptions}", String(summary.exceptionCount));
            }
            return t("profiles.wizard_website_filter_state_empty", "No site filter rules yet");
        }

        function getAuthenticationObjectSummary(entryValue, parseErrors = []) {
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            const spnegoCount = Array.isArray(currentObject.SPNEGO) ? currentObject.SPNEGO.length : 0;
            const delegatedCount = Array.isArray(currentObject.Delegated) ? currentObject.Delegated.length : 0;
            const ntlmCount = Array.isArray(currentObject.NTLM) ? currentObject.NTLM.length : 0;
            const allowNonFqdnCount = countSchemaObjectEntries(currentObject.AllowNonFQDN);
            const allowProxiesCount = countSchemaObjectEntries(currentObject.AllowProxies);
            const hostRuleCount = allowNonFqdnCount + allowProxiesCount;
            const locked = currentObject.Locked === true;
            const privateBrowsing = currentObject.PrivateBrowsing === true;
            const configuredControls = [
                spnegoCount > 0,
                delegatedCount > 0,
                ntlmCount > 0,
                allowNonFqdnCount > 0,
                allowProxiesCount > 0,
                locked,
                privateBrowsing,
            ].filter(Boolean).length;
            let state = "empty";

            if (parseErrors.length > 0) {
                state = "invalid";
            } else if (configuredControls > 0) {
                state = "configured";
            }

            return {
                configuredControls,
                hostRuleCount,
                locked,
                privateBrowsing,
                state,
            };
        }

        function formatAuthenticationObjectState(summary) {
            if (summary.state === "invalid") {
                return t("profiles.wizard_authentication_state_invalid", "Authentication values need attention");
            }
            if (summary.state === "configured") {
                let text = t("profiles.wizard_authentication_state_configured", "Controls: {controls} • Host rules: {rules}")
                    .replace("{controls}", String(summary.configuredControls))
                    .replace("{rules}", String(summary.hostRuleCount));
                if (summary.locked) {
                    text += ` • ${t("profiles.wizard_authentication_state_locked", "Locked")}`;
                }
                if (summary.privateBrowsing) {
                    text += ` • ${t("profiles.wizard_authentication_state_private", "Private windows")}`;
                }
                return text;
            }
            return t("profiles.wizard_authentication_state_empty", "No enterprise authentication rules yet");
        }

        function getCertificatesObjectSummary(entryValue, parseErrors = []) {
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            const installCount = Array.isArray(currentObject.Install) ? currentObject.Install.length : 0;
            const importEnterpriseRoots = currentObject.ImportEnterpriseRoots === true;
            const configuredEntries = installCount + (importEnterpriseRoots ? 1 : 0);
            let state = "empty";

            if (parseErrors.length > 0) {
                state = "invalid";
            } else if (configuredEntries > 0) {
                state = "configured";
            }

            return {
                installCount,
                importEnterpriseRoots,
                configuredEntries,
                state,
            };
        }

        function formatCertificatesObjectState(summary) {
            if (summary.state === "invalid") {
                return t("profiles.wizard_certificates_state_invalid", "Certificate values need attention");
            }
            if (summary.installCount > 0 && summary.importEnterpriseRoots) {
                return t("profiles.wizard_certificates_state_with_roots", "Installed: {count} • Enterprise roots enabled")
                    .replace("{count}", String(summary.installCount));
            }
            if (summary.installCount > 0) {
                return t("profiles.wizard_certificates_state_installed", "Installed certificates: {count}")
                    .replace("{count}", String(summary.installCount));
            }
            if (summary.importEnterpriseRoots) {
                return t("profiles.wizard_certificates_state_roots_only", "Enterprise roots enabled");
            }
            return t("profiles.wizard_certificates_state_empty", "No managed certificate trust yet");
        }

        function getDnsOverHttpsObjectSummary(entryValue, parseErrors = []) {
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            const hasEnabled = typeof currentObject.Enabled === "boolean";
            const enabled = currentObject.Enabled === true;
            const providerUrl = typeof currentObject.ProviderURL === "string" ? currentObject.ProviderURL.trim() : "";
            const locked = currentObject.Locked === true;
            const excludedCount = Array.isArray(currentObject.ExcludedDomains) ? currentObject.ExcludedDomains.length : 0;
            const fallbackDisabled = currentObject.Fallback === false;
            const configuredEntries = (hasEnabled ? 1 : 0)
                + (providerUrl ? 1 : 0)
                + (locked ? 1 : 0)
                + excludedCount
                + (fallbackDisabled ? 1 : 0);
            let state = "empty";

            if (parseErrors.length > 0) {
                state = "invalid";
            } else if (configuredEntries > 0) {
                state = "configured";
            }

            return {
                configuredEntries,
                enabled,
                hasEnabled,
                hasProvider: Boolean(providerUrl),
                locked,
                excludedCount,
                fallbackDisabled,
                state,
            };
        }

        function formatDnsOverHttpsObjectState(summary) {
            if (summary.state === "invalid") {
                return t("profiles.wizard_doh_state_invalid", "DNS-over-HTTPS values need attention");
            }
            if (summary.state !== "configured") {
                return t("profiles.wizard_doh_state_empty", "No DNS-over-HTTPS rules yet");
            }

            const parts = [];
            if (summary.hasEnabled) {
                parts.push(
                    summary.enabled
                        ? t("profiles.wizard_doh_state_enabled", "Enabled")
                        : t("profiles.wizard_doh_state_disabled", "Disabled"),
                );
            }
            if (summary.hasProvider) {
                parts.push(t("profiles.wizard_doh_state_provider", "Custom provider"));
            }
            if (summary.excludedCount > 0) {
                parts.push(
                    t("profiles.wizard_doh_state_excluded", "Excluded: {count}")
                        .replace("{count}", String(summary.excludedCount)),
                );
            }
            if (summary.locked) {
                parts.push(t("profiles.wizard_doh_state_locked", "Locked"));
            }
            if (summary.fallbackDisabled) {
                parts.push(t("profiles.wizard_doh_state_no_fallback", "No fallback"));
            }
            return parts.join(" • ");
        }

        function getUserMessagingObjectSummary(entryValue, parseErrors = []) {
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            const messagingKeys = [
                "ExtensionRecommendations",
                "FeatureRecommendations",
                "UrlbarInterventions",
                "SkipOnboarding",
                "MoreFromMozilla",
                "FirefoxLabs",
            ];
            let enabledCount = 0;
            let disabledCount = 0;
            messagingKeys.forEach((key) => {
                if (currentObject[key] === true) enabledCount += 1;
                if (currentObject[key] === false) disabledCount += 1;
            });

            const locked = currentObject.Locked === true;
            const configuredSurfaces = enabledCount + disabledCount + (locked ? 1 : 0);
            let state = "empty";

            if (parseErrors.length > 0) {
                state = "invalid";
            } else if (configuredSurfaces > 0) {
                state = "configured";
            }

            return {
                enabledCount,
                disabledCount,
                locked,
                configuredSurfaces,
                state,
            };
        }

        function formatUserMessagingObjectState(summary) {
            if (summary.state === "invalid") {
                return t("profiles.wizard_user_messaging_state_invalid", "Messaging values need attention");
            }
            if (summary.state !== "configured") {
                return t("profiles.wizard_user_messaging_state_empty", "No messaging controls yet");
            }

            let text = t("profiles.wizard_user_messaging_state_configured", "Enabled: {enabled} • Hidden: {disabled}")
                .replace("{enabled}", String(summary.enabledCount))
                .replace("{disabled}", String(summary.disabledCount));
            if (summary.locked) {
                text += ` • ${t("profiles.wizard_user_messaging_state_locked", "Locked")}`;
            }
            return text;
        }

        function applySchemaNestedStatus(container, text) {
            if (!container) return;
            const statusEl = container.querySelector("[data-schema-nested-status]");
            if (statusEl) {
                statusEl.textContent = text;
            }
        }

        function formatPermissionsNestedState(summary) {
            if (!summary.hasRules) {
                return t("profiles.wizard_permissions_nested_state_empty", "No allow/block rules yet");
            }

            let text = t("profiles.wizard_permissions_nested_state_configured", "Allow: {allow} • Block: {block}")
                .replace("{allow}", String(summary.allowCount))
                .replace("{block}", String(summary.blockCount));

            if (summary.hasDefault) {
                text += ` • ${t("profiles.wizard_permissions_nested_default", "Default: {value}").replace("{value}", String(summary.defaultValue || ""))}`;
            }
            if (summary.hasStrictControl) {
                text += ` • ${t("profiles.wizard_permissions_nested_state_strict", "Strict")}`;
            }

            return text;
        }

        function renderPermissionsNestedStatuses(card) {
            if (!card || card.dataset.schemaPolicyId !== "Permissions" || card.dataset.schemaPolicyKind !== "object-card") {
                return;
            }

            const { entryValue, parseErrors } = readSchemaObjectCardValue(card);
            const nestedContainers = Array.from(card.querySelectorAll('[data-schema-policy-field][data-schema-field-kind="nested-object"]'));

            nestedContainers.forEach((container) => {
                const path = container.dataset.schemaNestedPath || container.dataset.schemaPolicyField || "";
                const hasParseError = pathHasSchemaParseError(path, parseErrors);
                const categoryValue = getSchemaNestedValueAtPath(entryValue, path);
                const categorySummary = hasParseError
                    ? { hasRules: false, hasDefault: false, defaultValue: "", allowCount: 0, blockCount: 0, hasStrictControl: false }
                    : (() => {
                        const currentObject = categoryValue && typeof categoryValue === "object" && !Array.isArray(categoryValue) ? categoryValue : {};
                        const base = getPermissionCategorySummary(currentObject);
                        return {
                            ...base,
                            allowCount: Array.isArray(currentObject.Allow) ? currentObject.Allow.length : 0,
                            blockCount: Array.isArray(currentObject.Block) ? currentObject.Block.length : 0,
                            hasDefault: typeof currentObject.Default === "string" && currentObject.Default.trim().length > 0,
                            defaultValue: typeof currentObject.Default === "string" ? currentObject.Default.trim() : "",
                        };
                    })();

                const text = hasParseError
                    ? t("profiles.wizard_permissions_state_invalid", "Permission values need attention")
                    : formatPermissionsNestedState(categorySummary);
                applySchemaNestedStatus(container, text);
            });
        }

        function formatHandlersNestedDictionaryState(entryValue) {
            const count = countHandlerRuleBucket(entryValue);
            if (!count) {
                return t("profiles.wizard_handlers_nested_dictionary_empty", "No entries yet");
            }
            return t("profiles.wizard_handlers_nested_dictionary_configured", "Entries: {count}")
                .replace("{count}", String(count));
        }

        function formatHandlersNestedObjectState(entryValue) {
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            const action = typeof currentObject.action === "string" ? currentObject.action.trim() : "";
            const handlerCount = Array.isArray(currentObject.handlers) ? currentObject.handlers.length : 0;
            const hasRules = Boolean(action || currentObject.ask === true || currentObject.ask === false || handlerCount > 0);

            if (!hasRules) {
                return t("profiles.wizard_handlers_nested_object_empty", "No handler rule yet");
            }

            const actionLabel = action || t("profiles.wizard_handlers_nested_action_inherit", "inherit");
            return t("profiles.wizard_handlers_nested_object_configured", "Action: {action} • Apps: {count}")
                .replace("{action}", actionLabel)
                .replace("{count}", String(handlerCount));
        }

        function formatHandlersNestedArrayState(entryValue) {
            const count = Array.isArray(entryValue) ? entryValue.length : 0;
            if (!count) {
                return t("profiles.wizard_handlers_nested_array_empty", "No helper apps yet");
            }
            return t("profiles.wizard_handlers_nested_array_configured", "Helper apps: {count}")
                .replace("{count}", String(count));
        }

        function renderHandlersNestedStatuses(card) {
            if (!card || card.dataset.schemaPolicyId !== "Handlers" || card.dataset.schemaPolicyKind !== "object-card") {
                return;
            }

            const { entryValue, parseErrors } = readSchemaObjectCardValue(card);
            const nestedContainers = Array.from(card.querySelectorAll("[data-schema-nested-path]"));

            nestedContainers.forEach((container) => {
                const path = container.dataset.schemaNestedPath || "";
                if (!path) return;

                const hasParseError = pathHasSchemaParseError(path, parseErrors);
                const value = getSchemaNestedValueAtPath(entryValue, path);
                let text = "";

                if (hasParseError) {
                    text = t("profiles.wizard_handlers_state_invalid", "Handler values need attention");
                } else if (container.dataset.schemaNestedKind === "nested-dictionary-object") {
                    text = formatHandlersNestedDictionaryState(value);
                } else if (container.dataset.schemaNestedKind === "nested-array-of-objects") {
                    text = formatHandlersNestedArrayState(value);
                } else if (container.dataset.schemaNestedKind === "nested-object") {
                    text = formatHandlersNestedObjectState(value);
                }

                applySchemaNestedStatus(container, text);
            });
        }

        function getPermissionsObjectSummary(entryValue, parseErrors = []) {
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            let configuredCategories = 0;
            let strictCategories = 0;

            Object.values(currentObject).forEach((categoryValue) => {
                const categorySummary = getPermissionCategorySummary(categoryValue);
                if (categorySummary.hasRules) configuredCategories += 1;
                if (categorySummary.hasStrictControl) strictCategories += 1;
            });

            let state = "empty";
            if (parseErrors.length > 0) {
                state = "invalid";
            } else if (configuredCategories > 0 && strictCategories > 0) {
                state = "strict";
            } else if (configuredCategories > 0) {
                state = "configured";
            }

            return {
                configuredCategories,
                strictCategories,
                state,
            };
        }

        function formatPermissionsObjectState(summary) {
            if (summary.state === "invalid") {
                return t("profiles.wizard_permissions_state_invalid", "Permission values need attention");
            }
            if (summary.state === "strict") {
                return t("profiles.wizard_permissions_state_strict", "Configured: {configured} • Strict: {strict}")
                    .replace("{configured}", String(summary.configuredCategories))
                    .replace("{strict}", String(summary.strictCategories));
            }
            if (summary.state === "configured") {
                return t("profiles.wizard_permissions_state_configured", "Configured categories: {configured}")
                    .replace("{configured}", String(summary.configuredCategories));
            }
            return t("profiles.wizard_permissions_state_empty", "No permission categories configured");
        }

        function getCookiesObjectSummary(entryValue, parseErrors = []) {
            const ruleCount = getCookiesReviewCount(entryValue);
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            const strictMode = currentObject.Locked === true
                || (typeof currentObject.Behavior === "string" && currentObject.Behavior.trim() && currentObject.Behavior !== "accept")
                || (typeof currentObject.BehaviorPrivateBrowsing === "string" && currentObject.BehaviorPrivateBrowsing.trim() && currentObject.BehaviorPrivateBrowsing !== "accept");
            let state = "empty";

            if (parseErrors.length > 0) {
                state = "invalid";
            } else if (ruleCount > 0 && strictMode) {
                state = "strict";
            } else if (ruleCount > 0) {
                state = "configured";
            }

            return {
                ruleCount,
                state,
            };
        }

        function formatCookiesObjectState(summary) {
            if (summary.state === "invalid") {
                return t("profiles.wizard_cookies_state_invalid", "Cookie values need attention");
            }
            if (summary.state === "strict") {
                return t("profiles.wizard_cookies_state_strict", "Cookie rules: {count} • Restricted")
                    .replace("{count}", String(summary.ruleCount));
            }
            if (summary.state === "configured") {
                return t("profiles.wizard_cookies_state_configured", "Cookie rules configured: {count}")
                    .replace("{count}", String(summary.ruleCount));
            }
            return t("profiles.wizard_cookies_state_empty", "No cookie rules yet");
        }

        function getHandlersObjectSummary(entryValue, parseErrors = []) {
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            const mimeTypeRules = countHandlerRuleBucket(currentObject.mimeTypes);
            const schemeRules = countHandlerRuleBucket(currentObject.schemes);
            const extensionRules = countHandlerRuleBucket(currentObject.extensions);
            const totalRules = mimeTypeRules + schemeRules + extensionRules;
            let state = "empty";

            if (parseErrors.length > 0) {
                state = "invalid";
            } else if (totalRules > 0) {
                state = "configured";
            }

            return {
                mimeTypeRules,
                schemeRules,
                extensionRules,
                totalRules,
                state,
            };
        }

        function formatHandlersObjectState(summary) {
            if (summary.state === "invalid") {
                return t("profiles.wizard_handlers_state_invalid", "Handler values need attention");
            }
            if (summary.state === "configured") {
                return t("profiles.wizard_handlers_state_configured", "Mappings: {total} • MIME: {mime} • Schemes: {schemes} • Extensions: {extensions}")
                    .replace("{total}", String(summary.totalRules))
                    .replace("{mime}", String(summary.mimeTypeRules))
                    .replace("{schemes}", String(summary.schemeRules))
                    .replace("{extensions}", String(summary.extensionRules));
            }
            return t("profiles.wizard_handlers_state_empty", "No handler mappings yet");
        }

        function renderWebsiteFilterObjectStatus(card) {
            if (!card || card.dataset.schemaPolicyId !== "WebsiteFilter" || card.dataset.schemaPolicyKind !== "object-card") {
                return;
            }

            const { entryValue, parseErrors } = readSchemaObjectCardValue(card);
            const summary = getWebsiteFilterObjectSummary(entryValue, parseErrors);
            let statusEl = card.querySelector("[data-schema-object-status]");

            if (!statusEl) {
                statusEl = documentRef.createElement("div");
                statusEl.className = "wizard-search-engine-preset-copy wizard-search-engine-preset-status";
                statusEl.dataset.schemaObjectStatus = "true";
                card.querySelector(".wizard-shell-card-copy")?.after(statusEl);
            }

            statusEl.textContent = formatWebsiteFilterObjectState(summary);
            card.dataset.websiteFilterState = summary.state;
        }

        function renderAuthenticationObjectStatus(card) {
            if (!card || card.dataset.schemaPolicyId !== "Authentication" || card.dataset.schemaPolicyKind !== "object-card") {
                return;
            }

            const { entryValue, parseErrors } = readSchemaObjectCardValue(card);
            const summary = getAuthenticationObjectSummary(entryValue, parseErrors);
            let statusEl = card.querySelector("[data-schema-object-status]");

            if (!statusEl) {
                statusEl = documentRef.createElement("div");
                statusEl.className = "wizard-search-engine-preset-copy wizard-search-engine-preset-status";
                statusEl.dataset.schemaObjectStatus = "true";
                card.querySelector(".wizard-shell-card-copy")?.after(statusEl);
            }

            statusEl.textContent = formatAuthenticationObjectState(summary);
            card.dataset.authenticationState = summary.state;
        }

        function renderCertificatesObjectStatus(card) {
            if (!card || card.dataset.schemaPolicyId !== "Certificates" || card.dataset.schemaPolicyKind !== "object-card") {
                return;
            }

            const { entryValue, parseErrors } = readSchemaObjectCardValue(card);
            const summary = getCertificatesObjectSummary(entryValue, parseErrors);
            let statusEl = card.querySelector("[data-schema-object-status]");

            if (!statusEl) {
                statusEl = documentRef.createElement("div");
                statusEl.className = "wizard-search-engine-preset-copy wizard-search-engine-preset-status";
                statusEl.dataset.schemaObjectStatus = "true";
                card.querySelector(".wizard-shell-card-copy")?.after(statusEl);
            }

            statusEl.textContent = formatCertificatesObjectState(summary);
            card.dataset.certificatesState = summary.state;
        }

        function renderDnsOverHttpsObjectStatus(card) {
            if (!card || card.dataset.schemaPolicyId !== "DNSOverHTTPS" || card.dataset.schemaPolicyKind !== "object-card") {
                return;
            }

            const { entryValue, parseErrors } = readSchemaObjectCardValue(card);
            const summary = getDnsOverHttpsObjectSummary(entryValue, parseErrors);
            let statusEl = card.querySelector("[data-schema-object-status]");

            if (!statusEl) {
                statusEl = documentRef.createElement("div");
                statusEl.className = "wizard-search-engine-preset-copy wizard-search-engine-preset-status";
                statusEl.dataset.schemaObjectStatus = "true";
                card.querySelector(".wizard-shell-card-copy")?.after(statusEl);
            }

            statusEl.textContent = formatDnsOverHttpsObjectState(summary);
            card.dataset.dnsOverHttpsState = summary.state;
        }

        function renderPermissionsObjectStatus(card) {
            if (!card || card.dataset.schemaPolicyId !== "Permissions" || card.dataset.schemaPolicyKind !== "object-card") {
                return;
            }

            const { entryValue, parseErrors } = readSchemaObjectCardValue(card);
            const summary = getPermissionsObjectSummary(entryValue, parseErrors);
            let statusEl = card.querySelector("[data-schema-object-status]");

            if (!statusEl) {
                statusEl = documentRef.createElement("div");
                statusEl.className = "wizard-search-engine-preset-copy wizard-search-engine-preset-status";
                statusEl.dataset.schemaObjectStatus = "true";
                card.querySelector(".wizard-shell-card-copy")?.after(statusEl);
            }

            statusEl.textContent = formatPermissionsObjectState(summary);
            card.dataset.permissionsState = summary.state;
        }

        function renderCookiesObjectStatus(card) {
            if (!card || card.dataset.schemaPolicyId !== "Cookies" || card.dataset.schemaPolicyKind !== "object-card") {
                return;
            }

            const { entryValue, parseErrors } = readSchemaObjectCardValue(card);
            const summary = getCookiesObjectSummary(entryValue, parseErrors);
            let statusEl = card.querySelector("[data-schema-object-status]");

            if (!statusEl) {
                statusEl = documentRef.createElement("div");
                statusEl.className = "wizard-search-engine-preset-copy wizard-search-engine-preset-status";
                statusEl.dataset.schemaObjectStatus = "true";
                card.querySelector(".wizard-shell-card-copy")?.after(statusEl);
            }

            statusEl.textContent = formatCookiesObjectState(summary);
            card.dataset.cookiesState = summary.state;
        }

        function renderHandlersObjectStatus(card) {
            if (!card || card.dataset.schemaPolicyId !== "Handlers" || card.dataset.schemaPolicyKind !== "object-card") {
                return;
            }

            const { entryValue, parseErrors } = readSchemaObjectCardValue(card);
            const summary = getHandlersObjectSummary(entryValue, parseErrors);
            let statusEl = card.querySelector("[data-schema-object-status]");

            if (!statusEl) {
                statusEl = documentRef.createElement("div");
                statusEl.className = "wizard-search-engine-preset-copy wizard-search-engine-preset-status";
                statusEl.dataset.schemaObjectStatus = "true";
                card.querySelector(".wizard-shell-card-copy")?.after(statusEl);
            }

            statusEl.textContent = formatHandlersObjectState(summary);
            card.dataset.handlersState = summary.state;
        }

        function renderUserMessagingObjectStatus(card) {
            if (!card || card.dataset.schemaPolicyId !== "UserMessaging" || card.dataset.schemaPolicyKind !== "object-card") {
                return;
            }

            const { entryValue, parseErrors } = readSchemaObjectCardValue(card);
            const summary = getUserMessagingObjectSummary(entryValue, parseErrors);
            let statusEl = card.querySelector("[data-schema-object-status]");

            if (!statusEl) {
                statusEl = documentRef.createElement("div");
                statusEl.className = "wizard-search-engine-preset-copy wizard-search-engine-preset-status";
                statusEl.dataset.schemaObjectStatus = "true";
                card.querySelector(".wizard-shell-card-copy")?.after(statusEl);
            }

            statusEl.textContent = formatUserMessagingObjectState(summary);
            card.dataset.userMessagingState = summary.state;
        }

        function getExtensionSettingsDictionaryRowState(entryKey, entryValue) {
            const currentObject = entryValue && typeof entryValue === "object" && !Array.isArray(entryValue) ? entryValue : {};
            const managedProfile = getManagedExtensionProfileById(entryKey);
            const installationMode = typeof currentObject.installation_mode === "string" ? currentObject.installation_mode.trim() : "";
            const installUrl = typeof currentObject.install_url === "string" ? currentObject.install_url.trim() : "";
            const hasFlags = currentObject.updates_disabled === true || currentObject.private_browsing === true;
            const hasManagedFields = Boolean(installationMode || installUrl || hasFlags);

            if (!hasManagedFields) return "missing";
            if (installUrl && managedProfile && installUrl === managedProfile.defaultUrl) return "catalog_url";
            if (installUrl && managedProfile && installUrl !== managedProfile.defaultUrl) return "custom_url";
            if (installUrl) return "install_url";
            if (installationMode && !hasFlags) return "mode_only";
            if (hasFlags && !installationMode) return "flags_only";
            return "configured";
        }

        function formatExtensionSettingsDictionaryRowState(state) {
            if (state === "catalog_url") {
                return t("profiles.wizard_extension_settings_row_state_catalog_url", "Uses catalog install URL");
            }
            if (state === "custom_url") {
                return t("profiles.wizard_extension_settings_row_state_custom_url", "Custom install URL");
            }
            if (state === "install_url") {
                return t("profiles.wizard_extension_settings_row_state_install_url", "Install URL rule");
            }
            if (state === "mode_only") {
                return t("profiles.wizard_extension_settings_row_state_mode_only", "Mode-only rule");
            }
            if (state === "flags_only") {
                return t("profiles.wizard_extension_settings_row_state_flags_only", "Behavior flags only");
            }
            if (state === "configured") {
                return t("profiles.wizard_extension_settings_row_state_configured", "Rule configured");
            }
            return t("profiles.wizard_extension_settings_row_state_missing", "No managed fields yet");
        }

        function renderExtensionSettingsDictionaryStatuses(card) {
            if (!card || card.dataset.schemaPolicyId !== "ExtensionSettings" || card.dataset.schemaPolicyKind !== "dictionary-object") {
                return;
            }

            const rows = Array.from(card.querySelectorAll("[data-schema-dict-row]"));
            rows.forEach((row) => {
                const { entryKey, entryValue } = readSchemaDictionaryRowEntry(row);
                const state = getExtensionSettingsDictionaryRowState(entryKey, entryValue);
                let statusEl = row.querySelector("[data-schema-dict-status]");

                if (!statusEl) {
                    statusEl = documentRef.createElement("div");
                    statusEl.className = "wizard-search-engine-preset-copy wizard-search-engine-preset-status";
                    statusEl.dataset.schemaDictStatus = "true";
                    row.querySelector(".wizard-search-engine-head > div")?.appendChild(statusEl);
                }

                statusEl.textContent = formatExtensionSettingsDictionaryRowState(state);
                row.dataset.extensionSettingsRowState = state;
                row.dataset.extensionSettingsRowKind = getManagedExtensionProfileById(entryKey) ? "curated" : (entryKey && entryKey !== "*" ? "arbitrary" : "special");
                row.classList.remove(
                    "wizard-search-engine-preset--applied",
                    "wizard-search-engine-preset--partial",
                    "wizard-search-engine-preset--conflict",
                );
                if (state === "catalog_url") row.classList.add("wizard-search-engine-preset--applied");
                if (["install_url", "mode_only", "flags_only", "configured"].includes(state)) {
                    row.classList.add("wizard-search-engine-preset--partial");
                }
                if (state === "custom_url") row.classList.add("wizard-search-engine-preset--conflict");
            });
        }

        function renderSchemaPolicyReviewState(card) {
            if (!card) return;
            renderBookmarkArrayStatuses(card);
            renderAuthenticationObjectStatus(card);
            renderCertificatesObjectStatus(card);
            renderDnsOverHttpsObjectStatus(card);
            renderWebsiteFilterObjectStatus(card);
            renderPermissionsNestedStatuses(card);
            renderPermissionsObjectStatus(card);
            renderCookiesObjectStatus(card);
            renderHandlersNestedStatuses(card);
            renderHandlersObjectStatus(card);
            renderUserMessagingObjectStatus(card);
            renderExtensionSettingsDictionaryStatuses(card);
        }

        return {
            renderSchemaPolicyReviewState,
            getAuthenticationObjectSummary,
            getCertificatesObjectSummary,
            getDnsOverHttpsObjectSummary,
            getUserMessagingObjectSummary,
        };
    }

    window.BPMProfilesSchemaShellReview = { create };
})();
