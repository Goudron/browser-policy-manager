# BPM 0.9.3 Historical Floating Assistant External-Sources Switch

Backlog item: `BPM093-M12B-06`.

This document records the retained implementation for a future investigation. The 0.9.3 generated
portal does not include its script, markup or browser transport path. Historically, when the
floating assistant was `Ready`, its bottom status row contained a native, six-locale
`role=switch` control for optional external sources. It starts off. If the administrator has not
enabled the M12A-04 server capability and supplied its credential, the switch remains visible but
unchecked and disabled. It is hidden and disabled while the assistant is busy or not ready.

The preference and a cryptographically random opaque tab ID live only in the existing
locale-private `sessionStorage` record. The same-origin server mode is keyed by the HttpOnly
assistant session, that tab ID and the exact locale. A new tab therefore starts off and cannot alter
another tab's record. Reload and documentation navigation reconcile the retained preference after
the reader explicitly opens the assistant; page load itself makes no assistant or web request.
Answer completion, Clear, cancellation and provider failure do not reset the preference. Only an
explicit switch-off, locale change or tab close ends it.

The browser sends the tab ID with chat, but neither the tab ID nor the compatibility `web_mode`
field grants provider authority. The server uses only its stored state and rechecks configuration,
scope, rate limits and the fixed provider policy. Reading or toggling mode calls only the same-origin
API and never Brave.

A web-assisted terminal event preserves the existing local answer and local citations, then adds a
bounded `external_claims` collection. The portal resolves its opaque source handles and renders
claims in a separately labelled External sources region. It accepts only the fixed external source
kind/provider and rechecks the reviewed Mozilla HTTPS host/path allowlist before creating a
`noopener noreferrer` link. Claims and external URLs are never placed in browser storage.

The normative historical record is
`documentation/config/documentation-assistant-floating-web-mode-contract-0.9.3.json`.
