# BPM 0.9.0 Product Documentation Accessibility And Security Contract

Status: **Accepted for BPM 0.9.0**  
Decision date: 2026-06-21  
Backlog item: `BPM090-M2-10`

## Purpose And Scope

This contract defines the accessibility and security gates for DITA source, generated HTML,
localized screenshots, deterministic search, static assets, manifest-driven serving, and BPM links
under `/help/`. It applies to all five guides and exactly `en`, `ru`, `de`, `zh-CN`, `fr`, and
`es-ES`, including guide homes, topics, search states, aliases, tombstones, unavailable/error pages,
and narrow-screen layouts.

The accessibility target is **WCAG 2.2 Level AA**. This is a release acceptance target, not a claim
that one automated scan proves conformance or that it satisfies every jurisdiction-specific legal
obligation. Automated checks, DOM contracts, keyboard/browser tests, and manual assistive-
technology review provide complementary evidence.

The security model assumes documentation is static after build but does not assume every source
string, schema description, translated value, search term, URL, or generated path is safe merely
because it is in the repository. Source validation, contextual escaping, post-build inspection,
artifact hashing, strict serving, and browser policy are separate defenses.

This decision does not implement the portal. `BPM090-M3-08` implements the shell/theme,
`BPM090-M3-09` implements generated artifact metadata, `BPM090-M8-*` implements search and locale
content, `BPM090-M9-*` implements serving/navigation, and `BPM090-M11-*` implements the isolated
test/release gates.

## Accessibility Baseline

### Document language and identity

- Every HTML page has a unique localized `<title>`, exactly one visible primary `<h1>`, and one
  `<main id="main-content">` landmark.
- `<html lang>` is exactly the route locale. Foreign-language passages use the appropriate `lang`;
  identifiers, code, policy names, and API fields are not falsely marked as translated prose.
- Canonical and alternate-language links resolve the same stable topic identity. Locale switching
  never serves English content under another locale's URL.
- Page title, H1, breadcrumbs, current guide, locale, and BPM/documentation version give users a
  consistent orientation without relying on color or visual position alone.

### Structure and landmarks

- Use native semantic HTML first: `header`, labeled `nav`, `main`, `aside` where genuinely
  complementary, and `footer`. Do not add redundant ARIA roles when native semantics suffice.
- Multiple navigation landmarks have distinct localized accessible names. Breadcrumbs use a
  labeled navigation landmark and mark the current item with `aria-current="page"`.
- Heading levels form a logical outline and are not selected for visual size. Sections, notes,
  examples, warnings, and related links have meaningful localized headings or labels.
- The first focusable control is a visible-on-focus skip link to `#main-content`. It works on every
  page, including errors and search results.
- The whole portal is a document/site, not an ARIA `application`. ARIA is used only to fill a real
  semantic gap and every state/property is tested.

### Keyboard and focus

- Every action is operable with keyboard alone. There is no keyboard trap, hover-only action,
  drag-only action, or interaction that requires a precision pointer.
- Focus order follows reading and task order. Opening/closing navigation, locale/guide controls,
  search, copy controls, and disclosures preserves or returns focus predictably.
- Focus is always visibly indicated, is not removed by CSS, and is not fully obscured by sticky
  headers, drawers, cookie banners, or overlays. The focus indicator has at least 3:1 contrast
  against adjacent colors as a BPM design requirement.
- Native links, buttons, inputs, and `<details>/<summary>` are preferred. Custom disclosure controls
  expose localized names plus correct `aria-expanded` and `aria-controls`; Escape closes a modal or
  temporary overlay and returns focus to its opener.
- Pointer targets meet WCAG 2.2 AA target-size requirements (normally at least 24 by 24 CSS pixels
  or the applicable spacing/inline exception). Adjacent icon-only controls receive additional
  spacing and an accessible name.
- Keyboard shortcuts are not single printable characters unless they can be disabled/remapped or
  are active only while a focused component owns them.

### Visual presentation and reflow

- Normal text meets 4.5:1 contrast; large text meets 3:1; meaningful UI components, boundaries,
  charts, and focus states meet 3:1 non-text contrast.
- Color is never the only carrier of policy support, CIS state, warning level, current navigation,
  search match, required field, or success/error state.
- Text resizes to 200% without lost content or controls. At 400% zoom / a 320 CSS-pixel content
  width, ordinary content reflows without two-dimensional page scrolling.
- Wide code and genuinely two-dimensional data tables may use a labeled keyboard-scrollable
  region. They do not force the entire page to scroll horizontally, and an equivalent text summary
  is available when spatial relationships convey meaning.
- Content remains usable in light, dark, forced-colors/high-contrast, and `prefers-reduced-motion`
  modes. Theme choice does not change semantics or hide focus.
- Animation is not required to understand or operate the portal. Non-essential motion is disabled
  under `prefers-reduced-motion`; no autoplaying audio/video, flashing content, parallax, timed
  dismissal, or auto-advancing carousel is allowed.
- Content and controls remain readable with increased text/line/paragraph spacing and with long
  German/French/Russian labels or CJK line breaking.

### Images, screenshots, diagrams, and icons

- Every informative image has concise localized alt text that communicates purpose in context.
  Localized screenshots also have a localized caption explaining what the reader should notice.
- Decorative images use `alt=""` and are absent from the accessibility tree; linked/action images
  describe the action rather than their appearance.
- Complex diagrams have a nearby structured text equivalent. Screenshots never carry the only copy
  of steps, values, errors, policy state, or warnings.
- Alt text does not repeat an adjacent caption verbatim, start with filler such as “image of,” or
  expose filenames/hashes. The six-locale parity check treats missing/English fallback alt or
  caption text as a release failure.
- Icon-only controls have visible-on-focus/hover text where useful and an accessible name. Icons are
  not distinguished by color alone.

### Tables, lists, notes, and code

- Data tables have a localized caption, header cells, correct `scope`, and simple structure where
  possible. Layout tables are forbidden. Complex tables include an explanatory summary in prose.
- Ordered steps, unordered choices, definitions, notes, warnings, and code use their native
  structures; visual indentation is not used as a substitute.
- Code is emitted as escaped text inside `pre`/`code`, with a visible language/purpose label. Long
  lines can scroll inside a labeled region and remain keyboard reachable.
- A copy-code button, if implemented, is a real localized button, copies exactly the displayed
  inert text, reports success/failure in a polite status region, does not steal focus, and is never
  the only way to select the example.
- Destructive commands, irreversible API calls, placeholder values, prerequisites, and expected
  results have visible text warnings outside the code block.

### Links, navigation, and search

- Link text states its destination or purpose in context. Repeated “click here/read more” links and
  title-attribute-only explanations are forbidden.
- External links are visibly distinguishable in text, identify the external source, and do not open
  a new tab by default. If a new context is required, users are warned and the link uses
  `rel="noopener noreferrer"`.
- Guide and locale switchers use native controls, have persistent visible labels, expose current
  values, and work without pointer or typeahead assumptions. Navigation position is consistent
  across topics and locales.
- Search has a programmatic and visible localized label, an explicit submit action, and a labeled
  results region. Search is usable without JavaScript through guide navigation even if enhanced
  search is unavailable.
- Search is deterministic local retrieval over the packaged static documentation index. It does not
  provide conversational answers, semantic embeddings, vector retrieval, RAG, generative summaries,
  automatic recommendations, telemetry learning, personalization, or calls to external AI/search
  services. Future AI-assisted documentation functionality requires a separate approved epic.
- Search does not move focus on every keystroke. Submitted results announce a bounded result count
  through `role="status"`/`aria-live="polite"`; no-results, malformed-index, and unavailable states
  are readable and actionable.
- Highlighting preserves original text and is not the only indication of a match. Result title,
  guide, breadcrumb/context, and snippet are available to screen readers and keyboard users.

### Errors and status communication

- Documentation unavailable, invalid manifest, unsupported version, 404, alias, and 410 tombstone
  states use the same landmarks, language, title, H1, skip link, and navigation fundamentals as
  ordinary topics.
- Errors state what happened and the safe next action without exposing filesystem paths, hashes,
  stack traces, source snippets, server versions, or internal exception text.
- Dynamic status updates use an appropriate polite/assertive live region only when necessary;
  ordinary page navigation relies on title/H1/focus rather than excessive announcements.

## Security Trust Boundaries

The pipeline has five independent boundaries:

```text
reviewed DITA/inventories/assets
        -> build-time parsing, validation, escaping, allowlist
        -> immutable hashed artifact and manifest
        -> path-safe read-only /help/ serving with security headers
        -> browser DOM/search code using safe sinks
```

Passing one boundary never bypasses the next. The runtime does not read DITA, run DITA-OT, render
Markdown, transform XML, sanitize arbitrary HTML, or fetch upstream content.

## DITA And Generated HTML Safety

### Source restrictions

- Product content is DITA 1.3 XML parsed with network and external-entity resolution disabled except
  for the pinned local DITA catalog. No remote DTD/schema/entity is fetched.
- Raw HTML passthrough and active-content constructs are forbidden. Published sources may not emit
  `script`, inline event handlers, `iframe`, `frame`, `object`, `embed`, `applet`, `form`, active SVG,
  `foreignObject`, refresh redirects, or executable URL schemes.
- The generated portal shell may attach the reviewed first-party search script
  `assets/bpm-docs-search.js` with `defer`. Inline scripts, remote scripts, module imports,
  JSONP-style executable data, and source-authored scripts remain forbidden.
- A DITA foreign/object extension requires a separate reviewed allowlist change, provenance record,
  security fixture, and CSP review. It is not enabled merely because DITA-OT accepts it.
- Code samples, schema descriptions, titles, captions, translated strings, policy IDs, CIS fields,
  API examples, and search text are data. They are XML/HTML-escaped for their exact context and are
  never concatenated as markup.

### Post-build output validation

Every generated HTML page is parsed as HTML and checked before packaging:

- only the approved element and attribute set is present;
- no duplicate IDs, broken ID references, forbidden active elements, event-handler attributes,
  inline script/style, `style` attributes, or unexpected ARIA attributes exist;
- every URL is relative/same-origin or an approved `https` navigation link; `javascript:`,
  `vbscript:`, protocol-relative, encoded-control, and unexpected `data:` URLs fail;
- canonical, alternate, asset, stylesheet, script, anchor, and manifest references resolve inside
  the validated artifact or approved external-link registry;
- headings, landmarks, labels, language, alt text, table semantics, and accessible names satisfy
  the static accessibility contract;
- generated HTML is never edited to “fix” a failure; source or the first-party transform is fixed
  and the artifact is rebuilt.

This allowlist validation is not presented as a general HTML sanitizer. BPM avoids accepting
arbitrary HTML in the first place. If a future feature genuinely needs untrusted HTML, it requires
a separately pinned, maintained sanitizer and threat-model decision.

## Safe Search And Browser DOM Contract

- Search consumes only a schema-valid, SHA-256-verified, same-artifact locale index. JSON is parsed
  as data; `eval`, `Function`, executable JSONP, dynamic module URLs, and runtime templates from the
  index are forbidden.
- Queries are normalized as text, limited to 256 Unicode scalar values, and never compiled directly
  as a regular expression or selector. Result work and returned results are bounded (maximum 50
  visible results per query) to prevent accidental browser denial of service.
- Titles, breadcrumbs, snippets, matches, and errors are inserted with `textContent` or equivalent
  text-node creation. `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, and string-
  evaluated timers are forbidden in documentation runtime code.
- Highlighting splits trusted text ranges into DOM text nodes plus fixed project-created `<mark>`
  elements; index content never controls element names or attributes.
- Search queries, results, viewed topics, and copy actions are not sent to BPM APIs, analytics,
  telemetry, remote suggestions, CDNs, or third parties. The most recent query may be persisted only
  in locale-scoped browser `localStorage`; queries are not persisted in cookies, logs, the BPM
  profile database, or any server-side state by the documentation feature.
- The 0.9.0 offline capability is static/self-hosted behavior, not a service worker. Service workers,
  background sync, push, remote update checks, and runtime content downloads are out of scope.

## Static Asset And File-Serving Contract

- Every served file is named by the validated manifest, has an allowed extension/media type,
  exists as a regular non-symlink file below the activated artifact root, and matches its SHA-256.
- Path resolution rejects absolute paths, `..`, encoded separators, backslashes, NUL/control bytes,
  repeated separators, case-fold collisions, and any resolved path outside the artifact root.
- The runtime serves only `GET` and `HEAD`; no documentation upload, authoring, preview, form submit,
  WebSocket, or arbitrary file endpoint is introduced.
- Assets are self-hosted. Remote scripts, styles, fonts, images, iframes, embeds, CDN resources,
  trackers, analytics, pixels, and hotlinks are forbidden.
- Allowed release types are generated HTML, first-party CSS/JavaScript, validated JSON, approved
  raster images, licensed self-hosted WOFF2 fonts, notices, and explicitly registered inert
  downloads. HTML/SVG supplied as downloadable examples is forbidden in 0.9.0.
- Localized screenshots have bounded byte size and dimensions and are decoded/verified at build
  time. Archives, executable files, source maps, unknown MIME types, polyglot files, and user-
  supplied content are not packaged.
- CSS and JavaScript filenames are content-hashed or covered by the artifact build hash. HTML,
  manifest, target map, and search indexes revalidate; immutable hashed assets may use long-lived
  cache headers. A failed/stale build is never mixed with a new manifest.

## Safe Documentation Examples

- Examples use deterministic synthetic fixtures, `https://example.invalid` or an explicit
  `$BPM_BASE_URL` placeholder, non-secret tokens such as `<TOKEN>`, and fictional identities.
- No example contains real credentials, cookies, API keys, internal hosts, private IPs, customer
  names, local absolute paths, environment dumps, production IDs, or copied incident data.
- JSON/YAML/profile/policy examples pass the current schema or are prominently labeled as an
  intentionally invalid troubleshooting example with its expected error.
- Shell examples quote variables, avoid hidden command substitution, and do not use `curl | sh`,
  destructive wildcards, privilege escalation, or irreversible commands without a separate warning
  and explicit placeholder confirmation.
- API examples state current absence of authentication/rate-limit/idempotency guarantees rather
  than teaching unsafe assumptions. Destructive archive/reset/delete examples are isolated and use
  disposable fixture data.
- Examples are displayed inertly. A copy control never executes them, fills secrets, or submits a
  request.

## `/help/` Content Security Policy

The default BPM CSP is already self-hosted, but the static documentation route can and must be
stricter. `/help/` HTML responses use this route-specific header policy as the implementation target:

```text
default-src 'none';
script-src 'self';
script-src-attr 'none';
style-src 'self';
style-src-attr 'none';
img-src 'self';
font-src 'self';
connect-src 'self';
worker-src 'none';
child-src 'none';
frame-src 'none';
object-src 'none';
media-src 'none';
manifest-src 'none';
base-uri 'none';
form-action 'none';
frame-ancestors 'none'
```

The header is sent as HTTP, not only `<meta>`, on successful pages and documentation errors. There
is no `'unsafe-inline'`, `'unsafe-eval'`, `data:` source, wildcard, remote origin, nonce generated at
build time, or CSP exception for copied upstream content. External links are navigations and need no
CSP source permission.

If later implementation proves a directive must be widened, the change needs a route-specific
threat analysis, exact resource/feature, focused failing/passing tests, and approval in this
decision. It may not weaken the general application policy or inherit the Profile UI's temporary
`style-src 'unsafe-inline'` exception.

## HTTP Response Headers And Caching

All `/help/` HTML, alias/tombstone/error, manifest, target-map, search, and asset responses carry
appropriate security headers, including non-2xx responses:

| Header | Required contract |
| --- | --- |
| `Content-Security-Policy` | Exact route policy above for HTML; compatible restrictive policy or `default-src 'none'` for non-HTML. |
| `X-Content-Type-Options` | `nosniff`. |
| `Referrer-Policy` | `no-referrer`, retaining BPM's current stricter privacy default. |
| `X-Frame-Options` | `DENY` as defense in depth with `frame-ancestors 'none'`. |
| `X-XSS-Protection` | `0`; legacy browser filtering is not treated as an XSS defense. |
| `Permissions-Policy` | At minimum `geolocation=(), microphone=(), camera=()`; any additional feature is deny-by-default unless required and reviewed. |
| `Cross-Origin-Resource-Policy` | `same-origin` for documentation files. |
| `Cross-Origin-Opener-Policy` | `same-origin` for HTML after focused external-link/new-window compatibility tests. |
| `Content-Type` | Exact allowlisted MIME; HTML and textual types include UTF-8 where applicable. |
| `Cache-Control` | HTML/manifest/target/search require revalidation; content-hashed immutable assets may be public long-lived. |

HSTS is deployment-specific and is not enabled by this documentation architecture task. It must be
configured only by a future HTTPS distribution/deployment contract after certificate, subdomain,
and rollback behavior are known. The portal itself emits no cookies, CORS relaxation, server-version
header, or `X-Powered-By` header.

## Accessibility Verification Matrix

| Layer | Scope | Required evidence |
| --- | --- | --- |
| DITA authoring | Every topic/locale | Required title/type/lang, image alt/caption, table headers/caption, link purpose, no forbidden raw HTML. |
| Static HTML contract | Every generated page | Parsed DOM landmarks, title/H1, heading order, labels/names, IDs/refs, images, tables, URLs, active-content allowlist. |
| CSS/static audit | Every shipped stylesheet/theme | Contrast tokens, visible focus, zoom/text spacing/reflow, forced-colors, reduced-motion, print and narrow layouts. |
| Keyboard browser smoke | Representative topic, search, menu, switchers, code, errors in all six locales | Tab/Shift+Tab/Enter/Space/Escape operation, no trap, focus return/order/visibility, skip link. |
| Automated accessibility scan | Representative page/state matrix in all six locales | Zero serious/critical violations; every result reviewed, with no blanket suppressions. |
| Manual accessibility review | English plus risk-based non-English/CJK samples | Screen-reader landmarks/headings/links/status, zoom/reflow, contrast, reading order, meaningful alt text and language. |
| Security static contract | Every generated file/index/asset | Escaping/allowlist, forbidden tags/attributes/schemes/sinks, local paths, hashes, MIME, size and dependency checks. |
| HTTP/browser security | All `/help/` response classes | CSP and headers on 2xx/3xx/4xx/5xx, no console CSP errors, no remote requests, traversal/symlink/hash failures fail closed. |

Automated tools are pinned with the documentation test dependencies before use. A tool pass cannot
waive manual checks, and a manual note cannot waive a deterministic contract failure. Browser and
screenshot checks run with immediate sandbox escalation under the backlog protocol.

## Blocking Acceptance Checklist

Release is blocked unless all of these are true:

- WCAG 2.2 AA acceptance evidence exists for the representative interactive matrix and static
  checks cover every generated page in every locale;
- no missing/English-fallback title, label, alt text, caption, status, or accessible name exists;
- keyboard, focus, zoom/reflow, contrast, reduced-motion, forced-colors, and error-state checks pass;
- every source/output/asset/index passes the DITA/HTML/URL/path/hash/MIME allowlists;
- code examples are inert, synthetic, validated, escaped, and visibly warn about destructive use;
- search uses bounded verified local data, safe DOM sinks, no persistence, and no network/telemetry;
- the exact `/help/` CSP works without violation and required headers appear on every response class;
- there are no inline handlers/styles/scripts, eval-like execution, remote assets, frames/forms,
  active SVG/HTML downloads, service workers, unsafe URL schemes, path traversal, or stale mixed
  artifacts;
- no accessibility/security exception is a blanket suppression; each accepted exception names the
  page/component, criterion/threat, evidence, owner, expiry, and remediation task.

## Official Standards And Guidance Reviewed

Verified on 2026-06-21:

- W3C WCAG 2.2 Recommendation: `https://www.w3.org/TR/WCAG22/`
- W3C WAI page-structure tutorial: `https://www.w3.org/WAI/tutorials/page-structure/`
- W3C WAI accessibility tutorials: `https://www.w3.org/WAI/tutorials/`
- W3C WAI WCAG 2.2 reflow guidance:
  `https://www.w3.org/WAI/WCAG22/Understanding/reflow.html`
- OWASP Content Security Policy Cheat Sheet:
  `https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html`
- OWASP HTTP Security Response Headers Cheat Sheet:
  `https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html`
- OWASP HTML5 Security Cheat Sheet:
  `https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html`
