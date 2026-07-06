from __future__ import annotations

from tests.docs_index import doc_path_from_index


def _decision() -> str:
    decision = doc_path_from_index(
        "architecture/documentation-identifiers-and-url-conventions-0.9.0.md",
        status="active",
    ).read_text(encoding="utf-8")
    return " ".join(decision.split())


def test_documentation_identity_layers_are_distinct_and_immutable():
    decision = _decision()

    assert "Status: **Accepted for BPM 0.9.0**" in decision
    assert "Backlog item: `BPM090-M2-07`" in decision
    for layer in (
        "Guide ID",
        "Topic ID",
        "Anchor ID",
        "DITA key",
        "Target ID",
        "Source slug",
        "URL path",
        "Asset ID",
        "Alias",
    ):
        assert f"| {layer} |" in decision
    assert "IDs are never translated, reused for a different meaning" in decision
    assert "it is append-only" in decision


def test_documentation_conventions_adopt_inventory_topic_and_target_identities():
    decision = _decision()

    for identifier in (
        "`ug-task-*`",
        "`fx-policy-{exact_policy_id}`",
        "`fx-policy-AIControls`",
        "`fx-pref-browser-download-dir`",
        "`cis-rec-1-1-1-1`",
        "`cis-source-{exact_dotted_id}`",
        "`api-ref-update-profile`",
        "`admin-*`",
        "`administrator-guide`",
        "`policy:{exact_policy_id}`",
        "`known-preference:{exact.preference.id}`",
        "`cis:{exact.dotted.recommendation_id}`",
        "`api-operation:{operation_id}`",
        "`capability:{capability_id}`",
    ):
        assert identifier in decision
    assert "Channel or browser versions never enter a policy topic ID" in decision


def test_documentation_conventions_define_dita_keys_anchors_and_file_indirection():
    decision = _decision()

    for contract in (
        "`topic.{topic_id}`",
        "`guide.{guide_id}`",
        "`asset.{asset_id}`",
        "`a-{semantic-kebab-slug}`",
        "`#topic-id/anchor-id`",
        "published HTML exposes exactly `#anchor-id`",
        "Topics link internally with `keyref`/`conkeyref`",
        "not relative paths",
        "identical in all six locale trees",
    ):
        assert contract in decision


def test_documentation_conventions_define_canonical_urls_and_compatibility():
    decision = _decision()

    for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES"):
        assert f"`{locale}`" in decision
    for contract in (
        "`/help/{locale}/`",
        "/help/{locale}/{guide-root}/{url-path}/",
        "`/help/` may choose the current BPM locale",
        "A canonical path ends with `/` and has no `.html`",
        "HTTP `308`",
        "Redirect chains and locale-crossing aliases are forbidden",
        "returns `410`",
        "anchor aliases separately",
    ):
        assert contract in decision


def test_documentation_conventions_define_localized_screenshot_identity():
    decision = _decision()

    for contract in (
        "`asset_id`",
        "`shot-{primary-topic-id}-{semantic-view}`",
        "documentation/assets/screenshots/{locale}/{asset_id}.{extension}",
        "The filename stem and DITA `asset.{asset_id}` key are identical across locales.",
        "Captions and alt text live in localized DITA.",
        "Published asset paths may be content-hashed and are not stable deep-link contracts.",
    ):
        assert contract in decision
