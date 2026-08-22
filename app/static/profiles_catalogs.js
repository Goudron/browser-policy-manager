    function readEmbeddedJson(documentRef, elementId) {
        const element = documentRef.getElementById(elementId);
        try {
            return element ? JSON.parse(element.textContent || "{}") : {};
        } catch {
            return {};
        }
    }

    function read(documentRef) {
        const wizardManualPolicyControls = readEmbeddedJson(documentRef, "wizard-manual-policy-controls");
        const wizardSettingsCatalog = readEmbeddedJson(documentRef, "wizard-settings-catalog");
        const wizardPreferencesCatalog = readEmbeddedJson(documentRef, "wizard-preferences-catalog");
        const wizardSchemaShellCatalog = readEmbeddedJson(documentRef, "wizard-schema-shell-catalog");
        const allSettingsCategoryCatalog = readEmbeddedJson(documentRef, "all-settings-category-catalog");
        const schemaChannelsCatalog = readEmbeddedJson(documentRef, "schema-channels-catalog");
        const allSettingsRowHelpLinks = readEmbeddedJson(documentRef, "all-settings-row-help-links");
        const allSettingsRowHelpStatus = readEmbeddedJson(documentRef, "all-settings-row-help-status");

        const wizardPreferenceSections = Array.isArray(wizardPreferencesCatalog.sections)
            ? wizardPreferencesCatalog.sections
            : [];
        const wizardKnownPreferences = Array.isArray(wizardPreferencesCatalog.known_preferences)
            ? wizardPreferencesCatalog.known_preferences
            : [];

        return {
            wizardManualPolicyControls,
            allSettingsRowHelpLinks,
            allSettingsRowHelpStatus,
            settingsTargetAliases: {
                "field:wizard-homepage-start-page": "shell-policy:2:Homepage",
                "field:wizard-homepage-url": "shell-policy:2:Homepage",
                "field:wizard-homepage-additional": "shell-policy:2:Homepage",
                "field:wizard-homepage-locked": "shell-policy:2:Homepage",
                "field:wizard-new-tab-page": "shell-policy:2:NewTabPage",
                "field:wizard-override-first-run": "shell-policy:2:OverrideFirstRunPage",
                "field:wizard-override-post-update": "shell-policy:2:OverridePostUpdatePage",
                "field:firefox-home-search": "shell-policy:2:FirefoxHome",
                "field:firefox-home-top-sites": "shell-policy:2:FirefoxHome",
                "field:firefox-home-pocket": "shell-policy:2:FirefoxHome",
                "field:wizard-proxy-mode": "shell-policy:1:Proxy",
                "field:wizard-proxy-auto-config-url": "shell-policy:1:Proxy",
                "field:wizard-proxy-http": "shell-policy:1:Proxy",
                "field:wizard-proxy-passthrough": "shell-policy:1:Proxy",
                "field:wizard-proxy-locked": "shell-policy:1:Proxy",
                "field:wizard-search-default-engine": "shell-policy:1:SearchEngines",
                "field:wizard-search-prevent-installs": "shell-policy:1:SearchEngines",
                "field:wizard-search-remove": "shell-policy:1:SearchEngines",
                "field:wizard-search-bar": "shell-policy:1:SearchBar",
                "field:wizard-search-suggest": "shell-policy:1:SearchSuggestEnabled",
                "field:firefox-suggest-web": "shell-policy:1:FirefoxSuggest",
                "field:firefox-suggest-sponsored": "shell-policy:1:FirefoxSuggest",
                "field:firefox-suggest-improve": "shell-policy:1:FirefoxSuggest",
                "field:firefox-suggest-locked": "shell-policy:1:FirefoxSuggest",
                "policy:ExtensionUpdate": "shell-policy:6:ExtensionUpdate",
                "policy:Extensions": "shell-policy:6:Extensions",
                "policy:ExtensionSettings": "shell-policy:6:ExtensionSettings",
                "policy:InstallAddonsPermission": "shell-policy:6:InstallAddonsPermission",
                "search-engine-preset:ticket_queue": "shell-policy:1:SearchEngines",
                "search-engine-preset:wiki_portal": "shell-policy:1:SearchEngines",
                "search-engine-preset:duckduckgo": "shell-policy:1:SearchEngines",
            },
            quickPolicyKeys: Array.isArray(wizardManualPolicyControls.quick_policy_keys)
                ? wizardManualPolicyControls.quick_policy_keys
                : [],
            wizardLandingScalarKeys: [
                "SearchBar",
                "SearchSuggestEnabled",
                "NewTabPage",
                "OverrideFirstRunPage",
                "OverridePostUpdatePage",
            ],
            wizardSearchEnginesManagedKeys: ["Add", "Default", "Remove", "PreventInstalls"],
            wizardSearchEngineItemManagedKeys: [
                "Name",
                "URLTemplate",
                "Method",
                "IconURL",
                "Alias",
                "Description",
                "PostData",
                "SuggestURLTemplate",
            ],
            searchEnginePresets: {
                ticket_queue: {
                    Name: "Ticket Queue",
                    URLTemplate: "https://tickets.example.local/search?q={searchTerms}",
                    Method: "GET",
                    Alias: "ticket",
                    Description: "Managed search for helpdesk and issue tracking",
                },
                wiki_portal: {
                    Name: "Wiki Portal",
                    URLTemplate: "https://wiki.example.local/index.php?search={searchTerms}",
                    Method: "GET",
                    Alias: "wiki",
                    Description: "Managed search for internal wiki content",
                },
                duckduckgo: {
                    Name: "DuckDuckGo",
                    URLTemplate: "https://duckduckgo.com/?q={searchTerms}",
                    Method: "GET",
                    Alias: "ddg",
                    Description: "DuckDuckGo web search",
                },
            },
            wizardFirefoxHomeManagedKeys: [
                "Search",
                "TopSites",
                "SponsoredTopSites",
                "Highlights",
                "Pocket",
                "Stories",
                "SponsoredPocket",
                "SponsoredStories",
                "Snippets",
                "Locked",
            ],
            wizardFirefoxSuggestManagedKeys: [
                "WebSuggestions",
                "SponsoredSuggestions",
                "ImproveSuggest",
                "Locked",
            ],
            wizardSettingsCatalog,
            wizardPreferencesCatalog,
            wizardSchemaShellCatalog,
            allSettingsCategoryCatalog,
            schemaChannelsCatalog,
            defaultSchemaVersion: typeof schemaChannelsCatalog.default_channel === "string"
                ? schemaChannelsCatalog.default_channel
                : "",
            wizardPreferenceSections,
            wizardKnownPreferences,
            wizardKnownPreferenceIndex: Object.fromEntries(
                wizardKnownPreferences.map((entry) => [entry.pref, entry]),
            ),
            wizardSearchSectionSteps: {
                general: { step: 1, key: "profiles.wizard_step_one", fallback: "Browser, network & search" },
                home: { step: 2, key: "profiles.wizard_step_two", fallback: "URLs, sites & navigation" },
                search: { step: 1, key: "profiles.wizard_step_one", fallback: "Browser, network & search" },
                privacy: { step: 3, key: "profiles.wizard_step_three", fallback: "Security & privacy" },
                sync: { step: 5, key: "profiles.wizard_step_five", fallback: "Users, language & sync" },
                ai: { step: 7, key: "profiles.wizard_step_seven", fallback: "AI" },
                review: { step: 8, key: "profiles.wizard_step_eight", fallback: "Review & export" },
            },
            searchEnginePresetCatalog: [
                {
                    id: "ticket_queue",
                    title_key: "profiles.wizard_search_preset_ticket_title",
                    description_key: "profiles.wizard_search_preset_ticket_copy",
                    target: "search-engine-preset:ticket_queue",
                },
                {
                    id: "wiki_portal",
                    title_key: "profiles.wizard_search_preset_wiki_title",
                    description_key: "profiles.wizard_search_preset_wiki_copy",
                    target: "search-engine-preset:wiki_portal",
                },
                {
                    id: "duckduckgo",
                    title_key: "profiles.wizard_search_preset_ddg_title",
                    description_key: "profiles.wizard_search_preset_ddg_copy",
                    target: "search-engine-preset:duckduckgo",
                },
            ],
            wizardPreferenceEntryManagedKeys: ["Value", "Status", "Type"],
        };
    }

    export { read };
