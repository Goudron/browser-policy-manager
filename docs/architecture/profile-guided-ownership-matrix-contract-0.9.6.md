# BPM 0.9.6 Guided Ownership Matrix Contract

Date: 2026-08-20

Backlog item: `BPM096-M2-07`

Status: active runtime ownership contract.  M6 materialized the eight-step topology; M7-05
materialized the Extensions owner and updates the evidence below before M7-06 continues with its
manual-fallback-specific work.

## Purpose and authority

This record freezes the one-owner topology materialized by M6 and is the common source for the
focused M7, M8, and M9 coverage inventories.  It maps the current schema-backed policy catalog,
known preference catalog, manual controls, template controls, presets, summaries, deep links,
search targets, and raw fallback entries.  A later implementation must derive its step catalog,
placement, search result, jump, summary, and raw-fallback destination from this matrix; it cannot
create a second ownership list.

`All settings only` means the complete All settings/JSON path remains the only future visual
catalog owner.  It is not a reason to drop a supported policy or preference.  A raw value is
either owned by the same domain as its schema-backed setting or is explicitly All-settings-only;
Review and export may report it but never becomes a second editing owner.

The old `Profile & baseline` inputs are deliberately not policy settings.  M2-03 and M2-06
already require their move to preparation and read-only chrome, respectively.  The separate
preparation handoff ledger below makes that removal auditable without falsely putting a lifecycle
choice into All settings.  It is the sole non-editor handoff in this record.

The M8 URL/site family is expanded by the executable
[`profile-navigation-site-coverage-inventory-0.9.6.md`](profile-navigation-site-coverage-inventory-0.9.6.md).
That ledger records paths, schema differences, preset/CIS inputs, raw fallback, temporary hosts,
and explicit non-URL-domain exclusions. It does not alter this matrix's runtime-materialization
ledger until a later M8 task rehomes a control.

## Future steps and domain boundaries

1. **Browser, network, and search** owns browser behavior, proxy (including PAC URLs), network
   access, DNS/DoH, and search configuration.  It does not own destination/site or trust inputs.
2. **URLs, sites, and navigation** owns home/startup/new-tab/Firefox Home destinations, managed
   bookmarks, handlers, site filters, and site-access lists.  It does not own proxy PAC URLs,
   extension install URLs, or certificate paths.
3. **Security and privacy** owns privacy, browser hardening, cookies, permissions, and security
   posture that is not a trust-store/certificate task.
4. **Certificates and trust** owns certificate installation, enterprise roots, authentication and
   SSO links, and security devices.  It does not absorb all network policy merely because a
   setting is security-related.
5. **Users, language, and sync** owns accounts, user messaging, locales, translation, containers,
   and sync.
6. **Extensions** owns the complete add-on governance family: global/default behavior, allowed or
   blocked rules, force/normal install, uninstall, install URL, update/private-browsing detail,
   `InstallAddonsPermission`, and `ExtensionSettings`.  AMO lookup is later M7 work, not part of
   this planning-only contract.
7. **AI and smart features** owns schema-supported AI controls only.
8. **Review and export** owns final validation/save/export, cross-domain summaries, technical
   boundary reporting, and jump actions.  It does not duplicate editable policy controls.

`Certificates`, `Authentication`, `SecurityDevices`, and the enterprise-root preference are one
Certificates-and-trust family.  `ExtensionSettings`, `Extensions`, `ExtensionUpdate`,
`InstallAddonsPermission`, and `3rdparty` are one Extensions family.  Homepage/home surfaces,
bookmarks, handlers, website filters, and site-navigation policies are one URLs/sites/navigation
family.  These focused families are intentionally asserted by the fixture rather than inferred
from their old step or an identifier containing a URL.

## Normative executable matrix

<!-- bpm096-guided-ownership-matrix-contract-v1 -->
```json
{
  "contract_id": "bpm096-guided-ownership-matrix",
  "contract_version": 1,
  "status": "runtime-materialized-through-BPM096-M9-04",
  "allowed_owners": [
    "browser-network-search",
    "urls-sites-navigation",
    "security-privacy",
    "certificates-trust",
    "users-language-sync",
    "extensions",
    "ai-smart-features",
    "review-export",
    "all-settings-only"
  ],
  "steps": [
    {"number": 1, "id": "browser-network-search", "label": "Browser, network, and search"},
    {"number": 2, "id": "urls-sites-navigation", "label": "URLs, sites, and navigation"},
    {"number": 3, "id": "security-privacy", "label": "Security and privacy"},
    {"number": 4, "id": "certificates-trust", "label": "Certificates and trust"},
    {"number": 5, "id": "users-language-sync", "label": "Users, language, and sync"},
    {"number": 6, "id": "extensions", "label": "Extensions"},
    {"number": 7, "id": "ai-smart-features", "label": "AI and smart features"},
    {"number": 8, "id": "review-export", "label": "Review and export"}
  ],
  "current_sources": {
    "step_catalog": "app/web/firefox_wizard_steps.py",
    "schema_shell": "app/web/firefox_wizard_shell/catalog.py",
    "policy_schema": "app/services/policy_schema_service.py",
    "manual_controls": "app/web/firefox_manual_policy_controls.py",
    "settings_catalog": "app/web/firefox_settings_catalog/",
    "templates": "app/templates/profiles/_page_wizard_step_*.html",
    "search_and_target_aliases": [
      "app/static/profiles_settings_search.js",
      "app/static/profiles_catalogs.js",
      "app/web/profile_navigation.py"
    ],
    "review_and_jumps": [
      "app/static/profiles_review.js",
      "app/static/profiles_runtime.js"
    ]
  },
  "policy_owner_rules": {
    "by_current_ui_section": {
      "browser_behavior": "browser-network-search",
      "network_access": "browser-network-search",
      "search": "browser-network-search",
      "home_startup": "urls-sites-navigation",
      "privacy_security": "security-privacy",
      "ai_smart": "ai-smart-features",
      "advanced": "all-settings-only"
    },
    "overrides": {
      "3rdparty": "extensions",
      "AllowedDomainsForApps": "urls-sites-navigation",
      "AppUpdatePin": "browser-network-search",
      "Authentication": "certificates-trust",
      "AutoLaunchProtocolsFromOrigins": "urls-sites-navigation",
      "Bookmarks": "urls-sites-navigation",
      "Certificates": "certificates-trust",
      "Containers": "users-language-sync",
      "ContentAnalysis": "security-privacy",
      "DefaultBrowserSettingEnabled": "browser-network-search",
      "DefaultDownloadDirectory": "browser-network-search",
      "DisableDefaultBrowserAgent": "browser-network-search",
      "DisableSecurityBypass": "certificates-trust",
      "DisableEncryptedClientHello": "security-privacy",
      "DisableFirefoxAccounts": "users-language-sync",
      "DisableRemoteImprovements": "security-privacy",
      "DisableRemoteSettingsAndAcceptSecurityConsequences": "security-privacy",
      "DisableSafeMode": "security-privacy",
      "DisableSetDesktopBackground": "users-language-sync",
      "DisableThirdPartyModuleBlocking": "security-privacy",
      "DisabledCiphers": "security-privacy",
      "ExtensionSettings": "extensions",
      "ExtensionUpdate": "extensions",
      "Extensions": "extensions",
      "GoToIntranetSiteForSingleWordEntryInAddressBar": "urls-sites-navigation",
      "Handlers": "urls-sites-navigation",
      "Homepage": "urls-sites-navigation",
      "HttpAllowlist": "urls-sites-navigation",
      "InstallAddonsPermission": "extensions",
      "LegacySameSiteCookieBehaviorEnabled": "security-privacy",
      "LegacySameSiteCookieBehaviorEnabledForDomainList": "security-privacy",
      "LocalFileLinks": "urls-sites-navigation",
      "ManagedBookmarks": "urls-sites-navigation",
      "ManualAppUpdateOnly": "browser-network-search",
      "MicrosoftEntraSSO": "certificates-trust",
      "NoDefaultBookmarks": "urls-sites-navigation",
      "OfferToSaveLoginsDefault": "security-privacy",
      "LegacyProfiles": "all-settings-only",
      "PasswordManagerExceptions": "security-privacy",
      "PostQuantumKeyAgreementEnabled": "security-privacy",
      "PrivateBrowsingModeAvailability": "security-privacy",
      "RequestedLocales": "users-language-sync",
      "OverrideFirstRunPage": "urls-sites-navigation",
      "OverridePostUpdatePage": "urls-sites-navigation",
      "SearchSuggestEnabled": "browser-network-search",
      "SecurityDevices": "certificates-trust",
      "SkipTermsOfUse": "users-language-sync",
      "TranslateEnabled": "users-language-sync",
      "UserMessaging": "users-language-sync",
      "WebsiteFilter": "urls-sites-navigation",
      "WindowsSSO": "certificates-trust"
    }
  },
  "preference_owner_rules": {
    "by_current_section": {
      "general": "browser-network-search",
      "home": "urls-sites-navigation",
      "search": "browser-network-search",
      "privacy": "security-privacy",
      "sync": "users-language-sync"
    },
    "overrides": {
      "general:browser.startup.homepage": "urls-sites-navigation",
      "general:browser.startup.page": "urls-sites-navigation",
      "privacy:network.trr.mode": "browser-network-search",
      "privacy:security.enterprise_roots.enabled": "certificates-trust"
    },
    "unregistered_manual_preference": "all-settings-only"
  },
  "manual_policy_group_owners": {
    "general_browser_behavior": "browser-network-search",
    "home_surfaces": "urls-sites-navigation",
    "privacy_user_data": "security-privacy",
    "privacy_lockdown": "security-privacy",
    "sync_accounts": "users-language-sync"
  },
  "focused_domain_policy_ids": {
    "extensions": ["3rdparty", "ExtensionSettings", "ExtensionUpdate", "Extensions", "InstallAddonsPermission"],
    "urls-sites-navigation": ["AllowedDomainsForApps", "AutoLaunchProtocolsFromOrigins", "Bookmarks", "FirefoxHome", "GoToIntranetSiteForSingleWordEntryInAddressBar", "Handlers", "Homepage", "HttpAllowlist", "LocalFileLinks", "ManagedBookmarks", "NewTabPage", "NoDefaultBookmarks", "OverrideFirstRunPage", "OverridePostUpdatePage", "WebsiteFilter"],
    "certificates-trust": ["Authentication", "Certificates", "MicrosoftEntraSSO", "SecurityDevices", "WindowsSSO"]
  },
  "focused_domain_preference_ids": {
    "certificates-trust": ["privacy:security.enterprise_roots.enabled"]
  },
  "schema_variants": {
    "AIControls": ["release-153", "esr-153.0"],
    "AllowFileSelectionDialogs": ["release-153", "esr-153.0", "esr-140.13"],
    "AutofillAddressEnabled": ["release-153", "esr-153.0", "esr-140.13"],
    "AutofillCreditCardEnabled": ["release-153", "esr-153.0", "esr-140.13"],
    "BrowserDataBackup": ["release-153", "esr-153.0"],
    "ContentAnalysis": ["release-153", "esr-153.0", "esr-140.13"],
    "DefaultBrowserSettingEnabled": ["esr-153.0"],
    "DefaultSerialGuardSetting": ["release-153", "esr-153.0", "esr-140.13"],
    "DisableEncryptedClientHello": ["release-153", "esr-153.0", "esr-140.13"],
    "DisableRemoteImprovements": ["release-153", "esr-153.0"],
    "DisableRemoteSettingsAndAcceptSecurityConsequences": ["release-153", "esr-153.0"],
    "FirefoxSuggest": ["release-153", "esr-153.0", "esr-140.13"],
    "GenerativeAI": ["release-153", "esr-153.0"],
    "HttpAllowlist": ["release-153", "esr-153.0", "esr-140.13"],
    "HttpsOnlyMode": ["release-153", "esr-153.0", "esr-140.13"],
    "IPProtectionAvailable": ["release-153", "esr-153.0"],
    "LocalNetworkAccess": ["release-153", "esr-153.0"],
    "MicrosoftEntraSSO": ["release-153", "esr-153.0", "esr-140.13"],
    "PostQuantumKeyAgreementEnabled": ["release-153", "esr-153.0", "esr-140.13"],
    "PrintingEnabled": ["release-153", "esr-153.0", "esr-140.13"],
    "PrivateBrowsingModeAvailability": ["release-153", "esr-153.0", "esr-140.13"],
    "SitePolicies": ["release-153"],
    "SkipTermsOfUse": ["release-153", "esr-153.0", "esr-140.13"],
    "TranslateEnabled": ["release-153", "esr-153.0", "esr-140.13"],
    "VisualSearchEnabled": ["release-153", "esr-153.0"],
    "XSLTEnabled": ["release-153", "esr-153.0"]
  },
  "template_inventory": {
    "field_control_ids": {
      "browser-network-search": ["wizard-proxy-auto-config-url", "wizard-proxy-auto-login", "wizard-proxy-ftp", "wizard-proxy-http", "wizard-proxy-locked", "wizard-proxy-mode", "wizard-proxy-passthrough", "wizard-proxy-socks", "wizard-proxy-socks-version", "wizard-proxy-ssl", "wizard-proxy-use-dns", "wizard-proxy-use-http-for-all", "wizard-search-bar", "wizard-search-default-engine", "wizard-search-prevent-installs", "wizard-search-remove", "wizard-search-suggest"],
      "urls-sites-navigation": ["wizard-homepage-additional", "wizard-homepage-locked", "wizard-homepage-start-page", "wizard-homepage-url", "wizard-new-tab-page", "wizard-override-first-run", "wizard-override-post-update"],
      "certificates-trust": ["wizard-certificate-authentication-field", "wizard-certificate-authentication-host", "wizard-certificate-authentication-locked", "wizard-certificate-authentication-private-browsing", "wizard-certificate-enterprise-roots", "wizard-certificate-entra-sso", "wizard-certificate-error-bypass", "wizard-certificate-install-reference", "wizard-certificate-system-trust", "wizard-certificate-windows-sso", "wizard-security-device-delete-name", "wizard-security-device-name", "wizard-security-device-path"],
      "extensions": ["wizard-extension-amo-query", "wizard-extension-rule-guid", "wizard-extension-rule-install-url", "wizard-extension-update", "wizard-extension-install-default", "wizard-extension-install-allow", "wizard-extension-install", "wizard-extension-locked", "wizard-extension-uninstall"],
      "review-export": ["wizard-export-shareable-text"]
    },
    "field_data_selectors": {
      "browser-network-search": ["data-firefox-suggest-key:ImproveSuggest", "data-firefox-suggest-key:Locked", "data-firefox-suggest-key:SponsoredSuggestions", "data-firefox-suggest-key:WebSuggestions", "data-search-engine-field:Alias", "data-search-engine-field:Description", "data-search-engine-field:IconURL", "data-search-engine-field:Method", "data-search-engine-field:Name", "data-search-engine-field:PostData", "data-search-engine-field:SuggestURLTemplate", "data-search-engine-field:URLTemplate"],
      "urls-sites-navigation": ["data-firefox-home-key:Highlights", "data-firefox-home-key:Locked", "data-firefox-home-key:Pocket", "data-firefox-home-key:Search", "data-firefox-home-key:Snippets", "data-firefox-home-key:SponsoredPocket", "data-firefox-home-key:SponsoredStories", "data-firefox-home-key:SponsoredTopSites", "data-firefox-home-key:Stories", "data-firefox-home-key:TopSites"],
      "all-settings-only": ["data-preference-field:name", "data-preference-field:status", "data-preference-field:type", "data-preference-field:value"]
    },
    "search_targets": {
      "browser-network-search": ["field:firefox-suggest-improve", "field:firefox-suggest-locked", "field:firefox-suggest-sponsored", "field:firefox-suggest-web", "field:wizard-proxy-auto-config-url", "field:wizard-proxy-http", "field:wizard-proxy-locked", "field:wizard-proxy-mode", "field:wizard-proxy-passthrough", "field:wizard-search-bar", "field:wizard-search-default-engine", "field:wizard-search-prevent-installs", "field:wizard-search-remove", "field:wizard-search-suggest", "policy:DNSOverHTTPS", "search-engine-preset:duckduckgo", "search-engine-preset:ticket_queue", "search-engine-preset:wiki_portal"],
      "urls-sites-navigation": ["field:firefox-home-highlights", "field:firefox-home-locked", "field:firefox-home-pocket", "field:firefox-home-search", "field:firefox-home-snippets", "field:firefox-home-sponsored-pocket", "field:firefox-home-sponsored-stories", "field:firefox-home-sponsored-top-sites", "field:firefox-home-stories", "field:firefox-home-top-sites", "field:wizard-homepage-additional", "field:wizard-homepage-locked", "field:wizard-homepage-start-page", "field:wizard-homepage-url", "field:wizard-new-tab-page", "field:wizard-override-first-run", "field:wizard-override-post-update", "policy:AllowedDomainsForApps", "policy:AutoLaunchProtocolsFromOrigins", "policy:Bookmarks", "policy:GoToIntranetSiteForSingleWordEntryInAddressBar", "policy:Handlers", "policy:HttpAllowlist", "policy:LocalFileLinks", "policy:ManagedBookmarks", "policy:NoDefaultBookmarks", "policy:WebsiteFilter"],
      "security-privacy": ["policy:Cookies", "policy:IPProtectionAvailable", "policy:LocalNetworkAccess", "policy:Permissions"],
      "certificates-trust": [],
      "users-language-sync": ["policy:RequestedLocales", "policy:TranslateEnabled", "policy:UserMessaging"],
      "extensions": ["policy:ExtensionSettings", "policy:ExtensionUpdate", "policy:Extensions", "policy:InstallAddonsPermission"],
      "ai-smart-features": ["policy:AIControls", "policy:GenerativeAI", "policy:VisualSearchEnabled"]
    },
    "preset_selectors": {
      "browser-network-search": ["data-general-policy-preset:browser_prompt", "data-general-policy-preset:defaults", "data-general-policy-preset:downloads", "data-general-policy-preset:managed", "data-general-policy-preset:updates", "data-proxy-preset:autoConfig", "data-proxy-preset:defaults", "data-proxy-preset:manual", "data-proxy-preset:none", "data-proxy-preset:system", "data-search-defaults-preset:custom_engines", "data-search-defaults-preset:defaults", "data-search-defaults-preset:managed_default", "data-search-defaults-preset:restricted", "data-search-engine-preset:duckduckgo", "data-search-engine-preset:ticket_queue", "data-search-engine-preset:wiki_portal", "data-firefox-suggest-preset:defaults", "data-firefox-suggest-preset:locked_down", "data-firefox-suggest-preset:managed", "data-firefox-suggest-preset:private"],
      "urls-sites-navigation": ["data-firefox-home-preset:defaults", "data-firefox-home-preset:focused", "data-firefox-home-preset:managed", "data-firefox-home-preset:shortcuts", "data-home-overrides-preset:defaults", "data-home-overrides-preset:first_run", "data-home-overrides-preset:managed", "data-home-overrides-preset:new_tab", "data-homepage-preset:defaults", "data-homepage-preset:locked", "data-homepage-preset:portal", "data-homepage-preset:session", "data-homepage-shared-preset:portal_locked", "data-homepage-shared-preset:return_session"],
      "security-privacy": ["data-cleanup-preset:defaults", "data-cleanup-preset:shared", "data-cleanup-preset:strict", "data-hardening-preset:balanced", "data-hardening-preset:defaults", "data-hardening-preset:strict", "data-site-data-preset:balanced", "data-site-data-preset:defaults", "data-site-data-preset:strict"],
      "certificates-trust": [],
      "users-language-sync": ["data-language-preset:defaults", "data-language-preset:locales", "data-language-preset:managed", "data-language-preset:translation_off", "data-sync-focus-preset:accounts", "data-sync-focus-preset:defaults", "data-sync-focus-preset:guidance", "data-sync-focus-preset:managed"],
      "extensions": [],
      "ai-smart-features": ["data-ai-posture-preset:availability", "data-ai-posture-preset:defaults", "data-ai-posture-preset:disable", "data-ai-posture-preset:mixed"]
    },
    "deep_links_and_jumps": {
      "browser-network-search": ["#wizard-step-1-basics", "#wizard-step-1-default-search", "#wizard-step-1-managed-engines", "#wizard-step-1-proxy", "#wizard-step-1-suggestions", "data-network-review-jump:dns", "data-search-review-jump:custom", "data-search-review-jump:defaults", "data-search-review-jump:hidden", "data-search-review-jump:suggest"],
      "urls-sites-navigation": ["#wizard-home-surface-firefox-home", "#wizard-home-surface-new-tab", "#wizard-home-surface-startup", "#wizard-managed-navigation", "#wizard-site-access", "data-home-review-jump:firefox_home", "data-home-review-jump:homepage", "data-home-review-jump:overrides"],
      "security-privacy": ["#wizard-step-3-cleanup", "#wizard-step-3-posture", "#wizard-step-3-site-data", "#wizard-step-3-vpn", "data-privacy-review-jump:cleanup", "data-privacy-review-jump:cookies", "data-privacy-review-jump:permissions", "data-privacy-review-jump:user-data"],
      "certificates-trust": ["#wizard-step-4-authentication", "#wizard-step-4-devices", "#wizard-step-4-references", "#wizard-step-4-trust-posture"],
      "users-language-sync": ["#wizard-step-5-accounts", "#wizard-step-5-language"],
      "extensions": [],
      "ai-smart-features": ["#wizard-step-7-availability", "#wizard-step-7-posture", "#wizard-step-7-surfaces"],
      "review-export": ["#wizard-step-1-review", "#wizard-step-3-review", "data-final-review-jump:ai", "data-final-review-jump:browser", "data-final-review-jump:certificates", "data-final-review-jump:deprecated", "data-final-review-jump:extensions", "data-final-review-jump:privacy", "data-final-review-jump:raw", "data-final-review-jump:review", "data-final-review-jump:unknown", "data-final-review-jump:urls", "data-final-review-jump:users"]
    },
    "summary_ids": {
      "browser-network-search": ["wizard-network-summary-dns", "wizard-search-summary-custom", "wizard-search-summary-defaults", "wizard-search-summary-hidden", "wizard-search-summary-suggest"],
      "urls-sites-navigation": ["wizard-home-summary-firefox-home", "wizard-home-summary-homepage", "wizard-home-summary-overrides"],
      "security-privacy": ["wizard-privacy-summary-cleanup", "wizard-privacy-summary-cookies", "wizard-privacy-summary-permissions", "wizard-privacy-summary-user-data"],
      "certificates-trust": [],
      "extensions": [],
      "review-export": ["wizard-cis-final-summary", "wizard-export-deprecated-summary-count", "wizard-export-guided-summary-list", "wizard-export-raw-summary-count", "wizard-export-summary-ai", "wizard-export-summary-browser", "wizard-export-summary-certificates", "wizard-export-summary-extensions", "wizard-export-summary-privacy", "wizard-export-summary-review", "wizard-export-summary-urls", "wizard-export-summary-users", "wizard-export-unknown-summary-count", "wizard-summary-extensions", "wizard-summary-mode", "wizard-summary-policies"]
    }
  },
  "raw_fallback": {
    "policy_owner": "policy_owner_rules",
    "final_review_reporting_owner": "review-export",
    "raw_deprecated_unknown_jump_targets": ["raw", "deprecated", "unknown"],
    "raw_value_is_not_a_second_guided_editor": true,
    "unmapped_or_unknown_policy": "all-settings-only"
  },
  "preparation_handoff": {
    "non_editor_lifecycle_owner": "BPM096-M2-03-preparation",
    "guided_disposition": "remove-in-M5-05-and-never-rehome-to-all-settings",
    "id_selectors": ["wizard-mode", "wizard-name", "wizard-schema"],
    "data_selector_values": {
      "data-scenario-key": ["corporate_default", "extension_rollout", "hardened", "shared_devices", "targeted_edits"],
      "data-starter-key": ["basic_corporate", "blank", "classroom_kiosk", "keep_current", "soc_hard"],
      "data-cis-layer-key": ["cis_l1", "cis_l2", "none"]
    },
    "summary_ids": ["wizard-scenario-summary-copy", "wizard-scenario-summary-list", "wizard-baseline-summary-copy", "wizard-baseline-summary-list", "wizard-summary-name", "wizard-summary-schema", "wizard-summary-starter", "wizard-summary-cis", "wizard-summary-derived", "wizard-summary-derived-row", "wizard-summary-lifecycle-list"],
    "authority": ["BPM096-M2-03", "BPM096-M2-04", "BPM096-M2-06"],
    "not_all_settings_controls": true
  },
  "runtime_materialization": {
    "guard_owner": "BPM096-M6-04",
    "phase": "after-BPM096-M9-02-before-BPM096-M9-03",
    "owner_steps": {
      "browser-network-search": 1,
      "urls-sites-navigation": 2,
      "security-privacy": 3,
      "certificates-trust": 4,
      "users-language-sync": 5,
      "extensions": 6,
      "ai-smart-features": 7,
      "review-export": 8,
      "all-settings-only": 8
    },
    "guided_step_catalog_ids": {
      "browser-network-search": "browser_network_search",
      "urls-sites-navigation": "urls_sites_navigation",
      "security-privacy": "security_privacy",
      "certificates-trust": "certificates_trust",
      "users-language-sync": "users_language_sync",
      "extensions": "extensions",
      "ai-smart-features": "ai",
      "review-export": "review_export"
    },
    "allowed_current_template_host_steps": {
      "browser-network-search": [1],
      "urls-sites-navigation": [2],
      "security-privacy": [3],
      "certificates-trust": [1, 4],
      "users-language-sync": [5],
      "extensions": [6],
      "ai-smart-features": [7],
      "review-export": [8],
      "all-settings-only": []
    },
    "allowed_schema_shell_host_steps": {
      "browser-network-search": [1, 8],
      "urls-sites-navigation": [2],
      "security-privacy": [3, 5, 8],
      "certificates-trust": [4],
      "users-language-sync": [1, 5, 8],
      "extensions": [8],
      "ai-smart-features": [7],
      "review-export": [8],
      "all-settings-only": [5, 8]
    },
    "allowed_preference_shell_host_steps": {
      "browser-network-search": [1, 3],
      "urls-sites-navigation": [1, 2],
      "security-privacy": [3],
      "certificates-trust": [3],
      "users-language-sync": [5],
      "extensions": [],
      "ai-smart-features": [],
      "review-export": [],
      "all-settings-only": []
    },
    "deferred_domain_materialization": {
      "certificates-trust": {
        "delivery_milestone": "BPM096-M9-03",
        "required_owner_step": 4
      }
    },
    "search_section_hosts": {
      "general": {"owner": "browser-network-search", "host_step": 1},
      "home": {"owner": "urls-sites-navigation", "host_step": 2},
      "search": {"owner": "browser-network-search", "host_step": 1},
      "privacy": {"owner": "security-privacy", "host_step": 3},
      "sync": {"owner": "users-language-sync", "host_step": 5},
      "ai": {"owner": "ai-smart-features", "host_step": 7},
      "review": {"owner": "review-export", "host_step": 8}
    },
    "rendered_manual_policy_groups": {
      "general_browser_behavior": {"owner": "browser-network-search", "host_step": 1},
      "home_surfaces": {"owner": "urls-sites-navigation", "host_step": 2},
      "sync_accounts": {"owner": "users-language-sync", "host_step": 5}
    },
    "field_data_selector_counts": {
      "data-preference-field:value": 2
    },
    "mounted_policy_controls": {
      "DNSOverHTTPS": {"owner": "browser-network-search", "host_step": 1},
      "RequestedLocales": {"owner": "users-language-sync", "host_step": 5},
      "TranslateEnabled": {"owner": "users-language-sync", "host_step": 5},
      "IPProtectionAvailable": {"owner": "security-privacy", "host_step": 3},
      "AIControls": {"owner": "ai-smart-features", "host_step": 7},
      "VisualSearchEnabled": {"owner": "ai-smart-features", "host_step": 7},
      "GenerativeAI": {"owner": "ai-smart-features", "host_step": 7},
      "UserMessaging": {"owner": "users-language-sync", "host_step": 5},
      "WebsiteFilter": {"owner": "urls-sites-navigation", "host_step": 2},
      "AllowedDomainsForApps": {"owner": "urls-sites-navigation", "host_step": 2},
      "HttpAllowlist": {"owner": "urls-sites-navigation", "host_step": 2},
      "LocalFileLinks": {"owner": "urls-sites-navigation", "host_step": 2},
      "Handlers": {"owner": "urls-sites-navigation", "host_step": 2},
      "AutoLaunchProtocolsFromOrigins": {"owner": "urls-sites-navigation", "host_step": 2},
      "GoToIntranetSiteForSingleWordEntryInAddressBar": {"owner": "urls-sites-navigation", "host_step": 2},
      "Bookmarks": {"owner": "urls-sites-navigation", "host_step": 2},
      "ManagedBookmarks": {"owner": "urls-sites-navigation", "host_step": 2},
      "NoDefaultBookmarks": {"owner": "urls-sites-navigation", "host_step": 2},
      "Permissions": {"owner": "security-privacy", "host_step": 3},
      "Cookies": {"owner": "security-privacy", "host_step": 3},
      "LocalNetworkAccess": {"owner": "security-privacy", "host_step": 3}
    }
  },
  "implementation_boundary": {
    "m6": ["step-catalog", "navigation-and-focus", "matrix-guard", "review-summary"],
    "m7": ["extensions-and-amo"],
    "m8": ["urls-sites-navigation"],
    "m9": ["certificates-trust"],
    "current_runtime_change": "BPM096-M9-02"
  }
}
```

## Resolution and verification rules

For each active schema channel, take every policy with a UI definition.  Resolve an exact policy
override first; otherwise resolve its current UI section.  The result must be one of
`allowed_owners`.  A new UI section, an override for a policy that no current schema exposes, a
policy with no result, a schema availability difference not listed in `schema_variants`, or a
policy present in more than one materialized destination is a failure.  Raw fallback policies use
the same resolver.  A future implementation may change the current source section only by first
changing this record and its test.

Known preferences and catalog presets resolve by their catalog section, with the exact
`section:preference` overrides above.  The generic manual Preferences row has no inferred Guided
domain and is All-settings-only.  The test also enumerates every current template data target,
preset selector, anchor/jump, summary ID, field control ID, and step-1 lifecycle selector so a
new unowned control cannot appear silently.

The retained step-1 entry for the two `general:browser.startup.*` catalog preferences is a
non-rendered compatibility bridge for the generic preference catalog only.  It is not a Guided
control: the real homepage, startup, new-tab, and Firefox Home inputs are materialized exactly
once in step 2, and their template/search/review owners are checked separately by this matrix.

M9-02 removed the old composite `network-enterprise` preset from Browser, network, and search.
Step 4 now owns compact, schema-aware choices for the system-trust preference, enterprise roots,
certificate-error bypass, Windows SSO, and (where supported) Microsoft Entra SSO. Detailed
certificate references, security devices, and authentication lists remain explicitly deferred to
M9-03; M9-02 must not introduce a second owner for them. DNS/DoH continues with Browser, network,
and search. Likewise, homepage/startup controls move as one URL/navigation family, while proxy
PAC values remain in the browser/network family and extension install URLs remain in Extensions.

## Delivery boundary

M6-04 consumes this fixture as the single machine-readable owner map.  Its runtime guard fails on
a duplicate, orphan, stale template selector, missing schema variant, or disagreement among the
step catalog, rendered controls, search index, raw fallback, jump target, and final summary.  The
`runtime_materialization` ledger records the only temporary hosts permitted after M6-03: it is not
a second owner map and does not make those host steps owners of URL, certificate, or extension
settings.  M7-M9 must replace the corresponding temporary host with its `required_owner_step` and
cannot close by adding a duplicate to an older step.  M6-05 remains responsible for rebuilding the
final review groups; this guard only verifies that every current review selector is owned and has a
recorded host.
