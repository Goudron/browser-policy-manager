# BPM 0.9.6 Navigation and site-access coverage inventory

Date: 2026-08-21

Backlog item: `BPM096-M8-01`

Status: active implementation ledger for M8. This record is inventory and ownership metadata only;
it does not move a control, change a policy value, normalize a URL, or add a Guided editor.

M8-04 has now materialized the handlers and managed-navigation family once in the step-2
progressive disclosure: `Handlers`, `AutoLaunchProtocolsFromOrigins`,
`GoToIntranetSiteForSingleWordEntryInAddressBar`, `Bookmarks`, `ManagedBookmarks`, and
`NoDefaultBookmarks`. The historical step-5 host is removed; the following disposition stays as
audit provenance, while the ownership matrix is the current runtime source.

## Decision

The one Guided owner for a browser destination or a site-access rule is **step 2, URLs, sites,
and navigation**. A nested schema shape, a historical host on step 1 or step 5, or a URL-looking
string is not an exception. M8-02 owns homepage/startup/new-tab/Firefox Home and their managed
preferences; M8-03 owns allowed/blocked site and origin lists; M8-04 owns handlers, bookmarks,
and managed navigation. Every typed value must retain its exact Firefox shape or expose a
raw-preserving fallback in the same domain.

This scope is deliberately not based on the word `URL`. Proxy PAC and proxy endpoint values remain
with Browser, network, and search (step 1); extension installation/update URLs remain with
Extensions (step 6); certificate file paths and authentication hosts remain with Certificates and
trust (step 4). Search-engine URL templates remain step 1 because they configure search, not a
user destination. Opaque, unknown, or unsupported values remain All settings only and may be
reported from Review without becoming a second Guided editor.

The authoritative common owner map remains the
[Guided ownership matrix](profile-guided-ownership-matrix-contract-0.9.6.md). This inventory
expands only its M8 family; later M8 work must update the matrix runtime-materialization ledger
rather than introduce another owner list.

## Normative coverage fixture

<!-- bpm096-profile-navigation-site-coverage-inventory-v1 -->
```json
{
  "inventory_id": "bpm096-profile-navigation-site-coverage",
  "inventory_version": 1,
  "backlog_item": "BPM096-M8-01",
  "guided_owner": {"step": 2, "id": "urls-sites-navigation"},
  "supported_schema_channels": ["release-153", "esr-153.0", "esr-140.13", "esr-115.39"],
  "policy_coverage": {
    "Homepage": {"disposition": "urls-step-control", "delivery": "BPM096-M8-02", "paths": ["URL", "Additional[]", "Locked", "StartPage", "NewTabOnRestore"]},
    "FirefoxHome": {"disposition": "urls-step-control", "delivery": "BPM096-M8-02", "paths": ["Search", "TopSites", "SponsoredTopSites", "Highlights", "Pocket", "SponsoredPocket", "Snippets", "Weather", "Locked", "Stories", "SponsoredStories"]},
    "DisablePocket": {"disposition": "urls-step-control", "delivery": "BPM096-M8-02", "paths": ["<boolean>"]},
    "NewTabPage": {"disposition": "urls-step-control", "delivery": "BPM096-M8-02", "paths": ["<boolean>"]},
    "OverrideFirstRunPage": {"disposition": "urls-step-control", "delivery": "BPM096-M8-02", "paths": ["<string>"]},
    "OverridePostUpdatePage": {"disposition": "urls-step-control", "delivery": "BPM096-M8-02", "paths": ["<string>"]},
    "WebsiteFilter": {"disposition": "urls-step-control", "delivery": "BPM096-M8-03", "paths": ["Block[]", "Exceptions[]"]},
    "AllowedDomainsForApps": {"disposition": "urls-step-control", "delivery": "BPM096-M8-03", "paths": ["<comma-separated domains>"]},
    "HttpAllowlist": {"disposition": "urls-step-control", "delivery": "BPM096-M8-03", "channels": ["release-153", "esr-153.0", "esr-140.13"], "paths": ["<origin>[]"]},
    "LocalFileLinks": {"disposition": "urls-step-control", "delivery": "BPM096-M8-03", "paths": ["<origin>[]"]},
    "AutoLaunchProtocolsFromOrigins": {"disposition": "urls-step-control", "delivery": "BPM096-M8-04", "paths": ["[].protocol", "[].allowed_origins[]"]},
    "GoToIntranetSiteForSingleWordEntryInAddressBar": {"disposition": "urls-step-control", "delivery": "BPM096-M8-04", "paths": ["<boolean>"]},
    "Handlers": {"disposition": "urls-step-control", "delivery": "BPM096-M8-04", "paths": ["mimeTypes.<mime>.action", "mimeTypes.<mime>.ask", "schemes.mailto.action", "schemes.mailto.ask", "schemes.mailto.handlers[].name", "schemes.mailto.handlers[].uriTemplate", "extensions.pdf.action", "extensions.pdf.ask", "extensions.pdf.handlers[].name", "extensions.pdf.handlers[].path"]},
    "Bookmarks": {"disposition": "urls-step-control", "delivery": "BPM096-M8-04", "paths": ["[].Title", "[].URL", "[].Favicon", "[].Placement", "[].Folder"]},
    "ManagedBookmarks": {"disposition": "urls-step-control", "delivery": "BPM096-M8-04", "paths": ["[].toplevel_name", "[].url", "[].name", "[].children[].url", "[].children[].name"]},
    "NoDefaultBookmarks": {"disposition": "urls-step-control", "delivery": "BPM096-M8-04", "paths": ["<boolean>"]}
  },
  "preference_coverage": {
    "general": {"delivery": "BPM096-M8-02", "preferences": ["browser.startup.homepage", "browser.startup.page"]},
    "home": {"delivery": "BPM096-M8-02", "preferences": ["browser.newtabpage.enabled", "browser.newtabpage.activity-stream.feeds.topsites", "browser.newtabpage.activity-stream.feeds.section.highlights", "browser.newtabpage.activity-stream.feeds.system.topstories", "browser.newtabpage.activity-stream.showSponsoredTopSites", "browser.newtabpage.activity-stream.feeds.snippets", "browser.newtabpage.activity-stream.showSearch", "browser.newtabpage.activity-stream.topSitesRows"]}
  },
  "starter_presets": {
    "blank": [],
    "keep_current": [],
    "basic_corporate": ["Homepage", "FirefoxHome"],
    "classroom_kiosk": ["Homepage", "FirefoxHome", "WebsiteFilter"],
    "soc_hard": ["FirefoxHome"]
  },
  "cis": {
    "cis_l1": [],
    "cis_l2": ["NewTabPage=false"],
    "rule": "M8 must expose provenance and review state without altering CIS baseline semantics"
  },
  "raw_fallback": {
    "typed_navigation_or_site_value": {"owner": "urls-sites-navigation", "step": 2, "rule": "preserve exact imported schema value and expose a raw fallback when it cannot be safely structured"},
    "unknown_or_opaque_value": {"owner": "all-settings-only", "rule": "preserve without inferred URL/site ownership; report from Review only"}
  },
  "non_url_step_exclusions": {
    "browser-network-search": ["Proxy.AutoConfigURL and proxy endpoints", "SearchEngines.*.URLTemplate", "AppUpdateURL", "CaptivePortal", "SupportMenu", "ShowHomeButton"],
    "extensions": ["ExtensionSettings.<guid>.install_url", "ExtensionSettings.<guid>.update_url", "ExtensionSettings.<guid>.restricted_domains", "ExtensionSettings.<guid>.runtime_allowed_hosts", "ExtensionSettings.<guid>.runtime_blocked_hosts"],
    "certificates-trust": ["Certificates.Install[]", "Authentication.SPNEGO[]", "Authentication.Delegated[]", "Authentication.NTLM[]", "Authentication.AllowNonFQDN.<host>", "Authentication.AllowProxies.<host>"],
    "users-language-sync": ["UserMessaging"],
    "all-settings-only": ["SitePolicies", "unknown policy or unregistered managed preference"]
  },
  "temporary_host_dispositions": {
    "home_surfaces_and_home_preferences": {"previous_host_step": 1, "required_owner_step": 2, "delivery": "BPM096-M8-02", "sources": ["_page_wizard_step_general.html", "_page_wizard_step_home.html", "profiles_catalogs.js", "profiles_settings_search.js"]},
    "website_filter_and_site_access": {"previous_host_step": 5, "required_owner_step": 2, "delivery": "BPM096-M8-03", "sources": ["_page_wizard_step_sync.html", "profiles_review.js", "profiles_schema_shell_sections.js"]},
    "handlers_and_managed_navigation": {"previous_host_step": 5, "required_owner_step": 2, "delivery": "BPM096-M8-04", "sources": ["_page_wizard_step_sync.html", "profiles_review.js", "profiles_schema_shell_sections.js"]}
  }
}
```

## Verification boundary

The focused contract reads all four shipped policy artifacts, the shared home preference catalog,
starter catalog, and generated CIS layers. It proves that every listed path has the step-2 owner,
that `HttpAllowlist` is absent only on ESR 115, and that proxy/extension/certificate URL-bearing
values are explicitly excluded. It also makes the current temporary step-1/step-5 locations
reviewable without treating them as owners. M8-02 through M8-06 own implementation, validation,
rendering, conversion, and browser behavior.
