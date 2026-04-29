(() => {
    function readEmbeddedJson(documentRef, elementId) {
        const element = documentRef.getElementById(elementId);
        try {
            return element ? JSON.parse(element.textContent || "{}") : {};
        } catch {
            return {};
        }
    }

    function read(documentRef) {
        const wizardStarterCatalog = readEmbeddedJson(documentRef, "wizard-starter-catalog");
        const wizardManualPolicyControls = readEmbeddedJson(documentRef, "wizard-manual-policy-controls");
        const wizardSettingsCatalog = readEmbeddedJson(documentRef, "wizard-settings-catalog");
        const wizardPreferencesCatalog = readEmbeddedJson(documentRef, "wizard-preferences-catalog");
        const wizardSchemaShellCatalog = readEmbeddedJson(documentRef, "wizard-schema-shell-catalog");
        const schemaChannelsCatalog = readEmbeddedJson(documentRef, "schema-channels-catalog");

        const wizardPreferenceSections = Array.isArray(wizardPreferencesCatalog.sections)
            ? wizardPreferencesCatalog.sections
            : [];
        const wizardKnownPreferences = Array.isArray(wizardPreferencesCatalog.known_preferences)
            ? wizardPreferencesCatalog.known_preferences
            : [];

        return {
            wizardStarterCatalog,
            wizardManualPolicyControls,
            quickPolicyKeys: Array.isArray(wizardManualPolicyControls.quick_policy_keys)
                ? wizardManualPolicyControls.quick_policy_keys
                : [],
            quickPolicyEnabledValues: wizardStarterCatalog.quick_policy_enabled_values || {},
            starterPresets: wizardStarterCatalog.presets || {},
            complianceLayers: wizardStarterCatalog.compliance_layers || {},
            complianceMergedPresets: wizardStarterCatalog.compliance_merged_presets || {},
            complianceMetadata: wizardStarterCatalog.compliance_metadata || {},
            starterManagedKeys: Array.isArray(wizardStarterCatalog.managed_policy_keys)
                ? wizardStarterCatalog.managed_policy_keys
                : [],
            managedExtensionProfiles: [
                {
                    id: "uBlock0@raymondhill.net",
                    defaultUrl: "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi",
                },
                {
                    id: "adguardadblocker@adguard.com",
                    defaultUrl: "https://addons.mozilla.org/firefox/downloads/latest/adguardadblocker@adguard.com/latest.xpi",
                },
                {
                    id: "https-everywhere@eff.org",
                    defaultUrl: "https://addons.mozilla.org/firefox/downloads/latest/https-everywhere/latest.xpi",
                },
            ],
            wizardHomepageManagedKeys: ["URL", "Additional", "StartPage", "Locked"],
            wizardProxyManagedKeys: [
                "Mode",
                "Locked",
                "HTTPProxy",
                "UseHTTPProxyForAllProtocols",
                "SSLProxy",
                "FTPProxy",
                "SOCKSProxy",
                "SOCKSVersion",
                "Passthrough",
                "AutoConfigURL",
                "AutoLogin",
                "UseProxyForDNS",
            ],
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
                docs_portal: {
                    Name: "Docs Portal",
                    URLTemplate: "https://docs.example.local/search?q={searchTerms}",
                    Method: "GET",
                    Alias: "docs",
                    Description: "Managed search for internal documentation",
                },
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
            wizardExtensionManagedKeys: [
                "installation_mode",
                "install_url",
                "updates_disabled",
                "private_browsing",
            ],
            wizardSettingsCatalog,
            wizardPreferencesCatalog,
            wizardSchemaShellCatalog,
            schemaChannelsCatalog,
            defaultSchemaVersion: typeof schemaChannelsCatalog.default_channel === "string"
                ? schemaChannelsCatalog.default_channel
                : "esr-140.10",
            wizardPreferenceSections,
            wizardKnownPreferences,
            wizardKnownPreferenceIndex: Object.fromEntries(
                wizardKnownPreferences.map((entry) => [entry.pref, entry]),
            ),
            wizardSearchSectionSteps: {
                general: { step: 2, key: "profiles.wizard_step_two", fallback: "General" },
                home: { step: 3, key: "profiles.wizard_step_three", fallback: "Home" },
                search: { step: 4, key: "profiles.wizard_step_four", fallback: "Search" },
                privacy: { step: 5, key: "profiles.wizard_step_five", fallback: "Privacy & security" },
                sync: { step: 6, key: "profiles.wizard_step_six", fallback: "Accounts and add-ons" },
                ai: { step: 7, key: "profiles.wizard_step_seven", fallback: "AI and smart features" },
                review: { step: 8, key: "profiles.wizard_step_eight", fallback: "Review and export" },
            },
            searchEnginePresetCatalog: [
                {
                    id: "docs_portal",
                    title_key: "profiles.wizard_search_preset_docs_title",
                    description_key: "profiles.wizard_search_preset_docs_copy",
                    target: "search-engine-preset:docs_portal",
                },
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

    window.BPMProfilesCatalogs = { read };
})();
