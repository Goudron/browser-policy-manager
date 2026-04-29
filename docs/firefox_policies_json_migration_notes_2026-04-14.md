# Firefox policies.json Migration Notes

## Summary

Browser Policy Manager now uses Firefox Enterprise `policies.json` as the product import and export format.

The profile library still stores normalized profile flags internally, but user-facing file handoff is now Firefox `policies.json` only.

## Import

Use:

- `POST /api/profiles/import/firefox/policies.json`

The import endpoint accepts:

- `application/json` with a `document` value shaped as `{ "policies": ... }`;
- `multipart/form-data` with a `file` field containing a Firefox `policies.json` document.

Choose the target Firefox schema channel before import. The selected `schema_version` controls validation.

## Export

Use:

- `GET /api/export/profiles/{profile_id}/firefox/policies.json`

The final wizard step and the advanced download area now expose only the Firefox `policies.json` handoff file.

## Breaking API Change

Internal BPM JSON/YAML export routes were removed from the user-facing API surface.

Removed routes:

- `GET /api/export/profiles`
- `GET /api/export/profiles/{profile_id}`
- `GET /api/export/profiles/{profile_id}?fmt=json`
- `GET /api/export/profiles/{profile_id}?fmt=yaml`
- `GET /api/export/profiles/{profile_id}.json`
- `GET /api/export/profiles/{profile_id}.yaml`

Existing integrations that used those internal JSON/YAML exports should move to:

- `GET /api/export/profiles/{profile_id}/firefox/policies.json`

There is no compatibility export route for BPM internal JSON/YAML in this release.
