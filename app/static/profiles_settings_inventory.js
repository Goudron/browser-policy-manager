(() => {
    function create({
        dependencies = {},
        allSettingsCategoryCatalog = {},
        wizardPreferencesCatalog = {},
        wizardSchemaShellCatalog = {},
    }) {
        const {
            t,
            getActiveWizardSchemaVersion,
            getValidationIssues,
            getComplianceInfo,
            getManualEdits,
        } = dependencies;

        function hasOwn(source, key) {
            return Boolean(source && Object.prototype.hasOwnProperty.call(source, key));
        }

        function isPlainObject(value) {
            return Boolean(value && typeof value === "object" && !Array.isArray(value));
        }

        function normalizeSourceData(sourceData = {}) {
            if (!isPlainObject(sourceData)) return {};
            if (!hasOwn(sourceData, "policies")) return sourceData;
            return isPlainObject(sourceData.policies) ? sourceData.policies : {};
        }

        function categoryTitle(categoryId) {
            const category = allSettingsCategoryCatalog.categories_by_id?.[categoryId]
                || allSettingsCategoryCatalog.categories_by_id?.["raw-unmapped"];
            return category
                ? (t(category.title_key) || category.fallback || category.id)
                : "";
        }

        function compactText(value, maxLength = 36) {
            const text = String(value ?? "").trim();
            if (text.length <= maxLength) return text;
            return `${text.slice(0, Math.max(0, maxLength - 3))}...`;
        }

        function formatPreviewItem(value) {
            if (Array.isArray(value)) return t("profiles.settings_list_value_array")
                .replace("{count}", String(value.length));
            if (value && typeof value === "object") return t("profiles.settings_list_value_object")
                .replace("{count}", String(Object.keys(value).length));
            if (typeof value === "string") return compactText(value, 32);
            if (value === undefined) return t("profiles.settings_list_value_not_configured");
            return compactText(JSON.stringify(value), 32);
        }

        function appendPreview(summary, values) {
            const preview = values.slice(0, 3).map((value) => compactText(value, 28)).filter(Boolean);
            const hiddenCount = values.length - preview.length;
            if (hiddenCount > 0) {
                preview.push(`+${hiddenCount}`);
            }
            return preview.length ? `${summary} (${preview.join(", ")})` : summary;
        }

        function formatStructuredValue(value) {
            if (Array.isArray(value)) {
                const summary = t("profiles.settings_list_value_array")
                    .replace("{count}", String(value.length));
                return appendPreview(summary, value.map((item) => formatPreviewItem(item)));
            }
            if (value && typeof value === "object") {
                const keys = Object.keys(value);
                const summary = t("profiles.settings_list_value_object")
                    .replace("{count}", String(Object.keys(value).length));
                return appendPreview(summary, keys);
            }
            if (typeof value === "string") {
                return compactText(value, 72);
            }
            if (value === undefined) {
                return t("profiles.settings_list_value_not_configured");
            }
            return JSON.stringify(value);
        }

        function formatPreferenceStatus(status) {
            const keyByStatus = {
                default: "profiles.wizard_preferences_status_default",
                locked: "profiles.wizard_preferences_status_locked",
                user: "profiles.wizard_preferences_status_user",
                clear: "profiles.wizard_preferences_status_clear",
            };
            return keyByStatus[status] ? t(keyByStatus[status], status) : status;
        }

        function formatPreferenceType(type) {
            const keyByType = {
                boolean: "profiles.wizard_preferences_type_boolean",
                number: "profiles.wizard_preferences_type_number",
                string: "profiles.wizard_preferences_type_string",
            };
            return keyByType[type] ? t(keyByType[type], type) : type;
        }

        function formatPreferenceEntry(entry) {
            if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
                return formatStructuredValue(entry);
            }

            const parts = [];
            if (hasOwn(entry, "Value")) {
                parts.push(formatStructuredValue(entry.Value));
            } else if (entry.Status === "clear") {
                parts.push(formatPreferenceStatus("clear"));
            }
            if (entry.Status && entry.Status !== "clear") {
                parts.push(formatPreferenceStatus(entry.Status));
            }
            if (entry.Type) {
                parts.push(formatPreferenceType(entry.Type));
            }

            return parts.join(" • ")
                || t("profiles.settings_list_value_not_configured");
        }

        function resolvePreferenceSection(prefName) {
            const sections = Array.isArray(wizardPreferencesCatalog.sections)
                ? wizardPreferencesCatalog.sections
                : [];
            const trimmed = String(prefName || "").trim();
            if (!trimmed) return "";

            return sections.find((section) =>
                Array.isArray(section.prefixes)
                && section.prefixes.some((prefix) => trimmed === prefix || trimmed.startsWith(prefix))
            )?.id || "";
        }

        function getPreferenceSection(sectionId) {
            const sections = Array.isArray(wizardPreferencesCatalog.sections)
                ? wizardPreferencesCatalog.sections
                : [];
            return sections.find((section) => section?.id === sectionId) || null;
        }

        function getKnownPreference(prefName) {
            const knownPreferences = Array.isArray(wizardPreferencesCatalog.known_preferences)
                ? wizardPreferencesCatalog.known_preferences
                : [];
            return knownPreferences.find((item) => item?.pref === prefName) || null;
        }

        function uniqueStrings(values) {
            return [...new Set(values.filter(Boolean))];
        }

        function normalizePathParts(path) {
            return Array.isArray(path)
                ? path.map((part) => String(part))
                : [];
        }

        function sourcePathForEntry(entry) {
            if (entry.kind === "preference") {
                return ["Preferences", entry.id];
            }
            return [entry.id];
        }

        function decisionSources(decision) {
            if (!decision || typeof decision !== "object") return [];
            const selectedSource = String(decision.selected_source || decision.selectedSource || "").trim();
            const decisionType = String(decision.decision || "").trim();
            if (decisionType === "kept_base_only") return ["baseline"];
            if (decisionType === "added_from_cis") return ["cis"];
            if (decisionType === "cis_replaced_base") return ["cis", "baseline"];
            if (decisionType === "already_satisfied" || decisionType === "kept_base_stricter") {
                return ["baseline", "cis"];
            }
            if (decision.review_required || decisionType === "manual_review_kept_base") {
                return ["baseline", "cis"];
            }
            if (selectedSource === "base") return ["baseline"];
            if (selectedSource === "cis") return ["cis"];
            return [];
        }

        function cisRecommendationIds(decision) {
            return Array.isArray(decision?.recommendation_ids)
                ? decision.recommendation_ids.filter(Boolean).map((id) => String(id))
                : [];
        }

        function cisDecisionPath(decision) {
            return normalizePathParts(decision?.path);
        }

        function cisDecisionKey(decision) {
            const recommendationIds = cisRecommendationIds(decision);
            if (recommendationIds.length) return `cis:${recommendationIds[0]}`;
            const path = cisDecisionPath(decision);
            const decisionType = String(decision?.decision || "").trim();
            if (path.length && decisionType) return `cis:${path.join(".")}:${decisionType}`;
            if (path.length) return `cis:${path.join(".")}`;
            return decisionType ? `cis:${decisionType}` : "";
        }

        function normalizeCisDecisionList(entryOrDecisions) {
            if (Array.isArray(entryOrDecisions)) return entryOrDecisions;
            if (Array.isArray(entryOrDecisions?.sourceDetails?.decisions)) {
                return entryOrDecisions.sourceDetails.decisions;
            }
            if (Array.isArray(entryOrDecisions?.decisions)) return entryOrDecisions.decisions;
            return [];
        }

        function getCisDecisionMetadata(entryOrDecisions) {
            const decisions = normalizeCisDecisionList(entryOrDecisions)
                .filter((decision) => decision && typeof decision === "object");
            const primaryDecision = decisions[0] || null;
            const decisionTypes = uniqueStrings(decisions.map((decision) => decision.decision || ""));
            const selectedSources = uniqueStrings(decisions.map((decision) =>
                decision.selected_source || decision.selectedSource || ""
            ));
            const recommendationIds = uniqueStrings(decisions.flatMap((decision) =>
                cisRecommendationIds(decision)
            ));
            const decisionKeys = uniqueStrings(decisions.map((decision) => cisDecisionKey(decision)));
            return {
                hasDecision: decisions.length > 0,
                decisions,
                primaryDecision,
                primaryDecisionType: primaryDecision?.decision || "",
                primarySelectedSource: primaryDecision?.selected_source || primaryDecision?.selectedSource || "",
                reviewRequired: decisions.some((decision) => Boolean(decision.review_required)),
                recommendationIds,
                selectedSources,
                decisionTypes,
                decisionKeys,
                paths: decisions.map((decision) => cisDecisionPath(decision)),
            };
        }

        function pathMatchesDecision(entryPath, decisionPath) {
            if (!entryPath.length || !decisionPath.length) return false;
            if (decisionPath.length === 1 && decisionPath[0] === "Preferences" && entryPath[0] === "Preferences") {
                return true;
            }
            return entryPath.every((part, index) => decisionPath[index] === part)
                || decisionPath.every((part, index) => entryPath[index] === part);
        }

        function getComplianceDecisions() {
            const complianceInfo = getComplianceInfo?.();
            return Array.isArray(complianceInfo?.decisions) ? complianceInfo.decisions : [];
        }

        function getManualEditEntries() {
            const manualEdits = getManualEdits?.();
            return Array.isArray(manualEdits) ? manualEdits : [];
        }

        function buildSourceAttribution(entry) {
            const entryPath = sourcePathForEntry(entry);
            const decisions = getComplianceDecisions().filter((decision) =>
                pathMatchesDecision(entryPath, normalizePathParts(decision?.path))
            );
            const manualEdits = getManualEditEntries().filter((edit) =>
                pathMatchesDecision(entryPath, normalizePathParts(edit?.path))
            );
            const sources = [];
            if (manualEdits.length) sources.push("manual");
            decisions.forEach((decision) => sources.push(...decisionSources(decision)));
            if (entry.rawFallback) sources.push("raw-fallback");
            if (entry.unknown && entry.configured) sources.push("imported", "unknown");
            if (!entry.configured) sources.push("catalog");
            if (entry.configured && !entry.unknown && !entry.rawFallback && !decisions.length && !manualEdits.length) {
                sources.push("manual");
            }

            return {
                path: entryPath,
                sources: uniqueStrings(sources),
                decisions,
                manualEdits,
                cis: getCisDecisionMetadata(decisions),
            };
        }

        function sourceTags(entry, attribution = {}) {
            const sources = Array.isArray(attribution.sources) ? attribution.sources : [];
            if (sources.length) {
                return sources;
            }
            if (entry.unknown && entry.configured) return ["imported", "unknown"];
            if (entry.rawFallback) return ["raw-fallback"];
            if (entry.configured) return ["manual"];
            return ["catalog"];
        }

        function attentionFlags(entry, attribution = {}) {
            const reviewRequired = Boolean(
                entry.invalid
                || entry.deprecated
                || entry.rawFallback
                || entry.unknown
                || attribution.cis?.reviewRequired
            );
            return {
                invalid: Boolean(entry.invalid),
                deprecated: Boolean(entry.deprecated),
                rawFallback: Boolean(entry.rawFallback),
                unknown: Boolean(entry.unknown),
                cisReviewRequired: Boolean(attribution.cis?.reviewRequired),
                manualEdit: Boolean(attribution.manualEdits?.length),
                validationIssueCount: Number(entry.validationIssueCount || 0),
                reviewRequired,
            };
        }

        function finalizeEntry(entry) {
            const attribution = buildSourceAttribution(entry);
            const state = entry.configured ? "configured" : "available";
            const sources = sourceTags(entry, attribution);
            const attention = attentionFlags(entry, attribution);
            const valueSummary = entry.value;
            const cis = attribution.cis;
            return {
                ...entry,
                state,
                source: sources[0] || "",
                sources,
                cis,
                sourceDetails: {
                    path: attribution.path,
                    decisions: attribution.decisions,
                    manualEdits: attribution.manualEdits,
                    recommendationIds: cis.recommendationIds,
                    selectedSources: cis.selectedSources,
                    decisionKeys: cis.decisionKeys,
                    decisionTypes: cis.decisionTypes,
                    reviewRequired: cis.reviewRequired,
                    primaryDecision: cis.primaryDecision,
                },
                attentionFlags: attention,
                validationPaths: entry.validationPaths || [],
                validationIssueCount: Number(entry.validationIssueCount || 0),
                valueSummary,
                editor: {
                    target: entry.target,
                    kind: entry.kind,
                    schemaItem: entry.schemaItem || null,
                    knownPreference: entry.knownPreference || null,
                    preferenceSectionId: entry.preferenceSectionId || "",
                    preferenceSection: entry.preferenceSection || null,
                    preferenceValue: entry.preferenceValue ?? null,
                    preference: entry.kind === "preference" ? entry.id : "",
                },
            };
        }

        function buildPolicyEntries(sourceData) {
            const schemaVersion = getActiveWizardSchemaVersion();
            const shellSteps = Array.isArray(wizardSchemaShellCatalog.steps)
                ? wizardSchemaShellCatalog.steps
                : [];
            const channelData = wizardSchemaShellCatalog.channels?.[schemaVersion];
            const entries = [];
            const seenIds = new Set();

            shellSteps.forEach((stepMeta) => {
                const stepData = channelData?.steps?.[String(stepMeta.step)] || {};
                [
                    ["recommended", stepData.recommended],
                    ["additional", stepData.additional],
                    ["raw_fallback", stepData.raw_fallback],
                ].forEach(([bucketKey, bucketItems]) => {
                    (Array.isArray(bucketItems) ? bucketItems : []).forEach((item) => {
                        if (!item?.id || seenIds.has(item.id)) return;
                        seenIds.add(item.id);

                        const configured = item.id !== "Preferences" && hasOwn(sourceData, item.id);
                        const categoryId = allSettingsCategoryCatalog.policy_section_to_category_id?.[item.section_id]
                            || "raw-unmapped";
                        entries.push({
                            id: item.id,
                            label: item.id,
                            kind: "policy",
                            kindLabel: t("profiles.settings_list_kind_policy"),
                            categoryId,
                            categoryLabel: categoryTitle(categoryId),
                            configured,
                            guided: bucketKey === "recommended",
                            deprecated: Boolean(item.deprecated),
                            rawFallback: bucketKey === "raw_fallback" || item.support_level === "fallback",
                            unknown: false,
                            schemaBucket: bucketKey,
                            schemaStepId: stepMeta.id || "",
                            schemaStepNumber: stepMeta.step || 0,
                            schemaItem: item,
                            target: item.target || `policy:${item.id}`,
                            value: configured
                                ? formatStructuredValue(sourceData[item.id])
                                : t("profiles.settings_list_value_not_configured"),
                        });
                    });
                });
            });

            return entries;
        }

        function buildPreferenceEntries(sourceData) {
            const preferences = sourceData?.Preferences && typeof sourceData.Preferences === "object"
                && !Array.isArray(sourceData.Preferences)
                ? sourceData.Preferences
                : {};
            const knownPreferences = Array.isArray(wizardPreferencesCatalog.known_preferences)
                ? wizardPreferencesCatalog.known_preferences
                : [];
            const entries = [];
            const knownPrefNames = new Set();

            knownPreferences.forEach((item) => {
                if (!item?.pref) return;
                knownPrefNames.add(item.pref);

                const configured = hasOwn(preferences, item.pref);
                const preferenceSection = getPreferenceSection(item.section_id);
                const categoryId = allSettingsCategoryCatalog.preference_section_to_category_id?.[item.section_id]
                    || "raw-unmapped";
                entries.push({
                    id: item.pref,
                    label: item.pref,
                    kind: "preference",
                    kindLabel: t("profiles.settings_list_kind_preference"),
                    categoryId,
                    categoryLabel: categoryTitle(categoryId),
                    configured,
                    preferenceSectionId: item.section_id || "",
                    preferenceSection,
                    knownPreference: item,
                    preferenceValue: configured ? preferences[item.pref] : null,
                    guided: false,
                    deprecated: false,
                    rawFallback: false,
                    unknown: false,
                    target: `known-preference:${item.pref}`,
                    value: configured
                        ? formatPreferenceEntry(preferences[item.pref])
                        : t("profiles.settings_list_value_not_configured"),
                });
            });

            Object.entries(preferences).forEach(([prefName, entry]) => {
                if (knownPrefNames.has(prefName)) return;

                const sectionId = resolvePreferenceSection(prefName);
                const preferenceSection = getPreferenceSection(sectionId);
                const categoryId = allSettingsCategoryCatalog.preference_section_to_category_id?.[sectionId]
                    || "raw-unmapped";
                entries.push({
                    id: prefName,
                    label: prefName,
                    kind: "preference",
                    kindLabel: t("profiles.settings_list_kind_preference"),
                    categoryId,
                    categoryLabel: categoryTitle(categoryId),
                    configured: true,
                    preferenceSectionId: sectionId,
                    preferenceSection,
                    knownPreference: null,
                    preferenceValue: entry,
                    guided: false,
                    deprecated: false,
                    rawFallback: false,
                    unknown: true,
                    target: sectionId ? `pref-section:${sectionId}` : "pref-section:general",
                    value: formatPreferenceEntry(entry),
                });
            });

            return entries;
        }

        function buildUnknownPolicyEntries(sourceData, knownPolicyIds) {
            return Object.keys(sourceData || {})
                .filter((key) => key !== "Preferences" && !knownPolicyIds.has(key))
                .map((key) => ({
                    id: key,
                    label: key,
                    kind: "policy",
                    kindLabel: t("profiles.settings_list_kind_policy"),
                    categoryId: "raw-unmapped",
                    categoryLabel: categoryTitle("raw-unmapped"),
                    configured: true,
                    guided: false,
                    deprecated: false,
                    rawFallback: false,
                    unknown: true,
                    target: "settings-schema-shell-step-8",
                    value: formatStructuredValue(sourceData[key]),
                }));
        }

        function normalizeIssuePath(issue) {
            return Array.isArray(issue?.path)
                ? issue.path.map((part) => String(part))
                : [];
        }

        function validationPathsForEntry(entry) {
            if (entry.kind === "preference") {
                return [
                    ["Preferences", entry.id],
                    [entry.id],
                ];
            }
            return [[entry.id]];
        }

        function pathStartsWith(path, expected) {
            return expected.length > 0
                && expected.every((part, index) => path[index] === part);
        }

        function issueMatchesEntry(issue, entry) {
            const issuePath = normalizeIssuePath(issue);
            if (entry.kind === "preference") {
                return issue?.policy === "Preferences"
                    && validationPathsForEntry(entry).some((path) => pathStartsWith(issuePath, path));
            }
            if (entry.id === "Preferences" && issue?.policy === "Preferences") {
                return issuePath.length <= 1;
            }
            return issue?.policy === entry.id
                || validationPathsForEntry(entry).some((path) => pathStartsWith(issuePath, path));
        }

        function getIssuesByEntryKey(entries) {
            const issues = Array.isArray(getValidationIssues?.()) ? getValidationIssues() : [];
            return new Map(entries.map((entry) => [
                `${entry.kind}:${entry.id}`,
                issues.filter((issue) => issueMatchesEntry(issue, entry)),
            ]));
        }

        function sortEntries(entries) {
            const categoryOrder = Object.fromEntries(
                (Array.isArray(allSettingsCategoryCatalog.categories)
                    ? allSettingsCategoryCatalog.categories
                    : []
                ).map((category, index) => [category.id, index]),
            );

            return entries.sort((left, right) => {
                const categoryDelta = (categoryOrder[left.categoryId] ?? Number.MAX_SAFE_INTEGER)
                    - (categoryOrder[right.categoryId] ?? Number.MAX_SAFE_INTEGER);
                if (categoryDelta !== 0) return categoryDelta;
                if (left.configured !== right.configured) return left.configured ? -1 : 1;
                if (left.kind !== right.kind) return left.kind.localeCompare(right.kind);
                return left.label.localeCompare(right.label);
            });
        }

        function collect(sourceData = {}) {
            const normalizedSourceData = normalizeSourceData(sourceData);
            const policyEntries = buildPolicyEntries(normalizedSourceData);
            const entries = sortEntries([
                ...policyEntries,
                ...buildPreferenceEntries(normalizedSourceData),
                ...buildUnknownPolicyEntries(normalizedSourceData, new Set(policyEntries.map((entry) => entry.id))),
            ]);
            const issuesByEntryKey = getIssuesByEntryKey(entries);
            return entries.map((entry) => {
                const issues = issuesByEntryKey.get(`${entry.kind}:${entry.id}`) || [];
                return finalizeEntry({
                    ...entry,
                    validationPaths: validationPathsForEntry(entry),
                    validationIssueCount: issues.length,
                    issues,
                    invalid: issues.length > 0,
                });
            });
        }

        return {
            collect,
            formatStructuredValue,
            formatPreferenceEntry,
            categoryTitle,
            getKnownPreference,
            getPreferenceSection,
            getCisDecisionMetadata,
            cisDecisionKey,
        };
    }

    window.BPMProfilesSettingsInventory = { create };
})();
