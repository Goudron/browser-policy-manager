# Browser Policy Manager

Browser Policy Manager (BPM) is a FastAPI application for building, reviewing, validating,
and exporting Firefox Enterprise policy profiles.

It is designed for system administrators and security teams who need a practical daily tool
for managing Firefox `policies.json` documents without forcing every workflow through raw JSON.

**License:** [MPL-2.0](LICENSE)<br>
**Python:** `3.14+`

## Product Scope

BPM manages one canonical profile model and exposes it through five dedicated UI surfaces:

| Surface | Purpose |
|---|---|
| Profile library | Manage saved profiles, lifecycle state, schema channel, validation status, duplication, export, and editor entry points. |
| Profile comparison | Quickly find two saved profiles and compare policy and managed-preference settings side by side. |
| Guided editor | Build common Firefox policy profiles through a shorter task-first workflow. |
| All settings | Search and edit the full visual catalog of supported schema-backed controls. |
| JSON editor | Edit the complete Firefox Enterprise `policies.json` document directly. |

The UI is route-based rather than a single hidden-panel workspace. Saved profiles can be opened
in different modes in separate tabs. Unsaved drafts stay in the guided editor until the first save
creates a profile ID.

## Main Capabilities

- Database-backed Firefox policy profile library.
- Create, edit, duplicate, archive, restore, permanently delete, import, and export workflows.
- Named clone drafts that preserve the source configuration while letting the user choose the new
  profile name before opening the draft.
- Dedicated saved-profile comparison with fast two-profile search and a two-column settings table
  covering both policies and managed preferences.
- Firefox Enterprise `policies.json` import and export at the product boundary.
- Version-aware validation against bundled Firefox policy schemas.
- Guided editor for common administrator and security-team scenarios.
- Dedicated AI and smart browser features step for schema versions that support those policies.
- Schema-aware Release/ESR behavior across Release 153, ESR 153.0, and ESR 140.13.
- Triage-first All settings workflow with Review, Configured, and Catalog modes, source attribution,
  grouped search, bounded long lists, and one primary detail editor.
- JSON editor backed by the locally bundled Monaco editor.
- CIS Firefox hardening assets, starter presets, generated layers, and merge logic.
- English source UI with six active runtime locale catalogs.

## Supported Firefox Schemas

| Channel | Schema key | Status |
|---|---|---|
| Firefox Release 153 | `release-153` | Active |
| Firefox ESR 153.0 | `esr-153.0` | Active |
| Firefox ESR 140.13 | `esr-140.13` | Active |

The selected schema controls validation, imported-profile normalization, available UI controls,
and schema-specific behavior. Firefox Release 153 and ESR 153.0 expose the current AI policy
controls; ESR 140.13 does not. ESR 140.13 and ESR 153.0 are distinct supported channels, and BPM
does not migrate a profile automatically from one ESR channel to the other.

## Web Routes

| Route | Purpose |
|---|---|
| `GET /` | JSON root endpoint with app status and version. |
| `GET /profiles` | Profile library. |
| `GET /profiles/compare` | Dedicated saved-profile comparison interface. |
| `GET /profiles/new` | Guided editor for a new draft. |
| `GET /profiles/{id}/edit` | Guided editor for an existing profile. |
| `GET /profiles/{id}/settings` | All settings catalog for an existing profile. |
| `GET /profiles/{id}/json` | JSON editor for an existing profile. |
| `GET /help/` | Installed product documentation portal. |
| `GET /help/{locale}/...` | Locale-specific documentation pages, assets, manifest-backed topic links, and static search indexes. |
| `GET /i18n/{locale}.json` | Localization catalog. |
| `GET /health` | Liveness probe. |
| `GET /health/ready` | Readiness probe. |

## API Surface

### Profiles

| Endpoint | Purpose |
|---|---|
| `GET /api/profiles` | List profiles with filtering, sorting, and pagination. |
| `GET /api/profiles/stats` | Get profile-library counts. |
| `GET /api/profiles/{id}` | Fetch one profile. |
| `POST /api/profiles` | Create a profile. |
| `PATCH /api/profiles/{id}` | Update a profile. |
| `DELETE /api/profiles/{id}` | Archive a profile. |
| `POST /api/profiles/{id}/restore` | Restore an archived profile. |
| `DELETE /api/profiles/{id}/hard` | Permanently delete a profile. |
| `DELETE /api/profiles/reset` | Permanently clear the profile library. |

### Firefox Import, Export, And Validation

| Endpoint | Purpose |
|---|---|
| `POST /api/profiles/import/firefox/policies.json` | Import a Firefox Enterprise `policies.json` document. |
| `GET /api/export/profiles/{id}/firefox/policies.json` | Export a profile as Firefox Enterprise `policies.json`. |
| `POST /api/validate/{profile}` | Validate a profile document against a supported schema channel. |

## Firefox `policies.json` Contract

BPM imports and exports the Firefox Enterprise `policies.json` shape at product boundaries.
Internally, profiles are stored in BPM's normalized model so the library, guided editor,
All settings, JSON editor, validation, and export flows can work on the same source of truth.

Choose the Firefox schema channel before import. The selected `schema_version` controls how the
document is validated and how the imported profile is normalized for editing.

Import endpoint:

```text
POST /api/profiles/import/firefox/policies.json
```

Export endpoint:

```text
GET /api/export/profiles/{id}/firefox/policies.json
```

JSON import example:

The Firefox file supplied for import is a complete `policies.json` document, not an internal BPM
`flags` fragment:

```json
{
  "policies": {
    "DisableTelemetry": true,
    "BlockAboutConfig": true
  }
}
```

The API request carries that complete document in its `document` field:

```json
{
  "name": "Workstation baseline",
  "description": "Imported Firefox deployment policy",
  "schema_version": "esr-140.13",
  "document": {
    "policies": {
      "DisableTelemetry": true,
      "Preferences": {
        "browser.tabs.warnOnClose": {
          "Value": true,
          "Status": "locked"
        }
      }
    }
  }
}
```

The import endpoint also accepts `multipart/form-data` with a `file` field containing a Firefox
`policies.json` file. Optional form fields include `name`, `description`, `schema_version`, and
`compliance`.

Export example:

```json
{
  "policies": {
    "DisableTelemetry": true
  }
}
```

## Product Documentation Portal

BPM provides localized product documentation at `/help/` and keeps FastAPI OpenAPI documentation
at `/docs`. The product header and contextual help links open the relevant documentation topic;
unavailable settings show a localized non-link state.

The portal uses the same BPM product header and visual language as the application, including the
single BPM version derived from product metadata. It supports light, dark, and system themes; the
light theme uses light-gray primary surfaces instead of a pure-white page. Search starts as a
compact one-line control. Advanced filters are hidden by default and change only through their
explicit toggle; search, URL/history hydration, results, and clear preserve that choice.

Documentation search is local, deterministic, and available in English, Russian, German,
Simplified Chinese, French, and Spanish. The separate documentation assistant shows a localized
training notice; it does not provide generated answers, citations, or external-search results.
Search remains available independently of the assistant. No provider token or external-source configuration is required.

The portal contains four guide families in all six active locales:

| Guide | Scope |
|---|---|
| User Guide | Case-oriented help for every user-visible BPM capability and recovery path. |
| Firefox Policy Guide | Supported Firefox Release/ESR policies, managed preferences, examples, channel differences, caveats, and provenance. |
| CIS Settings Guide | BPM's CIS mappings, presets, merge workflow, manual-review states, and source/provenance boundaries without copying restricted benchmark prose. |
| Administrator/DevOps Guide | Source deployment for Linux and Windows 10/11 through WSL, operations, update-from-source, API integration, external control-product runbooks, troubleshooting, and current production/HA/reverse-proxy boundaries. |

Documentation locales match the runtime UI locale matrix: `en`, `ru`, `de`, `zh-CN`, `fr`, and
`es-ES`. Topic titles, navigation, search controls, captions, and prose use each locale's maintained
BPM UI terminology. The User Guide includes a reviewed minimal set of locale-specific screenshots
for the Library, Guided editor, All settings, JSON editor, profile comparison, and settings search.

The Administrator/DevOps Guide covers supported source deployment, operations, API integration,
troubleshooting, and the current production, high-availability, and reverse-proxy boundaries.

After starting BPM, open the product UI and use the documentation link in the header, or open:

```text
http://127.0.0.1:8000/help/
```

## UI Modes

### Profile Library

The library is the operational home for saved profiles. It supports profile search and filtering,
schema and lifecycle visibility, validation state, duplication, import, export, archive/restore,
and direct entry into the guided editor, All settings, or JSON editor.

Archive is reversible: archived profiles can be restored. Permanent delete is a distinct destructive
action available for active and archived profiles; it requires confirmation that the profile will
not be kept in the archive and cannot be restored.
Permanent deletion requires an explicit irreversible confirmation.

Comparison is intentionally not embedded in the Library. The Library provides a compare action that
opens `/profiles/compare` in a new tab and carries the selected language and theme preference into
the comparison route.
Saved-profile comparison lives only in the dedicated `/profiles/compare` interface.

Duplicating a profile opens a clone-name control first. After the name is confirmed, BPM opens a
new guided-editor draft initialized from the selected profile and the requested clone name. The
clone-name controls wrap within the Library action panel across the active locale set.

### Profile Comparison

The comparison interface is built for quick side-by-side review of two saved profiles. Each side
has its own profile search and selected-profile summary. The settings table compares the union of
policy and managed-preference settings present in either profile, with explicit missing, same-value,
and different-value states. Result lists are bounded and scrollable for larger libraries, and the
setting column keeps policy/preference identity readable without repeating the same identifier.
Because Compare opens from Library in a new tab, its header intentionally has no redundant
return-to-Library control.

### Guided Editor

The guided editor is the recommended starting point for most profile work. It uses scenario-first
sections, starter presets, compliance-aware baselines, and focused controls for common Firefox
administration tasks. It intentionally stays smaller than a full schema mirror.

The AI and smart browser features step remains a dedicated guided step. It shows current Firefox
AI controls for Release 153 and ESR 153.0 where the selected schema supports them. For ESR 140.13,
the step clearly states that the schema does not support AI settings and does not render unsupported
controls.

### All Settings

All settings is the full visual manager for schema-backed configuration and uses three explicit
working modes:

- **Review** is the default for saved enterprise profiles. It prioritizes invalid values, CIS manual
  review, raw fallback, unknown/imported keys, and deprecated settings; clean profiles get a concise
  completion state.
- **Configured** shows what the profile applies, starting with domain summaries and source filters
  for baseline, CIS, manual, imported, and raw settings. Category drilldown is deliberate rather
  than automatically narrowing the initial list.
- **Catalog** exposes all available schema-backed policies and known managed preferences without
  forcing that complete inventory into the default view.

All three modes consume the same settings inventory. Search groups configured settings, available
policies, preferences, and actions instead of presenting ambiguous duplicate targets. Selecting an
entry opens the primary detail editor with its value, source, validation state, location, and
apply/remove/reset actions. Advanced schema-shell and preference controls remain reachable from
Catalog/detail, but no longer compete as duplicate full-page editors.

Each supported policy and known managed preference row has a localized circled-info documentation
link. It opens the matching topic in a new tab without selecting the row. Unknown raw settings and
missing, stale, incompatible, or unavailable documentation render a localized noninteractive state
instead of a broken link.

Long lists are budgeted or paginated, and responsive layouts keep modes, search, rows, and detail
usable on desktop and narrow screens. Use All settings when a profile needs complete inspection,
review, or detailed changes beyond the shorter Guided workflow.

### JSON Editor

The JSON editor is the direct `policies.json` editing surface. It is useful for exact document
review, troubleshooting, migration checks, and values that are easier to handle as raw JSON.

## Localization

The primary UI source language is English. BPM is available in these locales:

| Locale | Native label | Status |
|---|---|---|
| `en` | English | Available |
| `ru` | Русский | Available |
| `de` | Deutsch | Available |
| `zh-CN` | 简体中文 | Available |
| `fr` | Français | Available |
| `es-ES` | Español | Available |

Unsupported or regional browser-language matches use the closest available locale.

Mozilla, Firefox, browser UI, privacy, permission, add-on, translation, and policy terminology
should follow Mozilla Pontoon and SUMO style where applicable. English text should not appear in a
localized UI unless it is a brand name, policy key, product identifier, API term, JSON value, or
another intentionally untranslated technical value.

Locale terminology follows Mozilla Pontoon and SUMO style where applicable.

## License

This project is licensed under the [MPL-2.0](LICENSE).

## Author

**Valery Ledovskoy**<br>
📧 [valery@ledovskoy.com](mailto:valery@ledovskoy.com)<br>
Only emails with `[BPM]` in the subject line are reviewed.

© 2025-2026 • Released under [Mozilla Public License 2.0](LICENSE)
