"""Focused reader-source contract for BPM096-M10-02."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
EN_DITA = REPO_ROOT / "documentation" / "src" / "dita" / "en"
BACKLOG = REPO_ROOT / "docs" / "bpm_0_9_6_profile_creation_guided_editor_backlog_2026-08-20.md"


def _topic(area: str, topic: str) -> str:
    return (EN_DITA / area / f"{topic}.dita").read_text(encoding="utf-8")


def test_english_user_topics_describe_atomic_preparation_and_eight_step_ownership() -> None:
    create = _topic("user", "ug-task-create-first-profile")
    duplicate = _topic("user", "ug-task-duplicate-profile")
    guided = _topic("user", "ug-task-use-guided-editor")

    for required in (
        "atomic preparation",
        "name, schema, preset, and CIS baseline",
        "saved profile",
    ):
        assert required in create
    assert "no profile is created" in create
    for required in (
        "Duplicate preparation",
        "never silently drops source values",
        "creates no target",
        "leaves the source unchanged",
    ):
        assert required in duplicate
    for required in (
        "eight Guided editor steps",
        "read-only facts",
        "Step 2, <uicontrol>URLs, sites &amp; navigation</uicontrol>",
        "Step 4, <uicontrol>Certificates &amp; trust</uicontrol>",
        "Step 6, <uicontrol>Extensions</uicontrol>",
        "Step 7, <uicontrol>AI</uicontrol>",
        "Step 8, <uicontrol>Review &amp; export</uicontrol>",
    ):
        assert required in guided
    assert "Profile &amp; baseline" not in guided
    assert "six task-first steps" not in guided


def test_english_policy_and_cis_topics_keep_safe_amo_certificate_and_review_boundaries() -> None:
    policy = _topic("firefox", "fx-concept-complex-policy-families")
    cis = _topic("cis", "cis-concept-presets-layers-merge")
    manual_review = _topic("cis", "cis-concept-manual-review-exceptions")

    for required in (
        "AMO search is a user-initiated, optional name lookup",
        "does not fetch an XPI",
        "manual GUID and validated install-URL",
        "does not upload, open, hash, read, or validate certificate or device contents",
        "Unsafe or unsupported imported URL/site shapes are preserved",
    ):
        assert required in policy
    assert "Certificate/trust attribution is a separate path-level ledger" in cis
    assert "does not promote a baseline claim" in cis
    assert "not proof of benchmark compliance" in manual_review


def test_english_api_topics_match_public_preparation_and_amo_envelopes() -> None:
    conventions = _topic("admin", "admin-concept-api-conventions")
    lifecycle = _topic("admin", "admin-task-sync-profile-lifecycle")
    examples = _topic("admin", "admin-task-use-reusable-api-examples")

    for required in (
        "POST /api/profiles/prepare/new",
        "POST /api/profiles/prepare/duplicate",
        "POST /api/profiles/prepare/duplicate/preview",
        "ProfilePreparationErrorEnvelope",
        'mutation="none"',
        "Callers cannot submit flags, compliance, provenance, or a conversion candidate",
    ):
        assert required in conventions
    assert "preparation_idempotency_key" in lifecycle
    assert "expected_source_revision" in lifecycle
    assert "no target was created and the source was not changed" in lifecycle
    for required in (
        "/api/profiles/prepare/new",
        "/api/profiles/prepare/duplicate",
        "/api/profiles/extensions/amo-search",
        "same-origin browser context",
        "manual GUID and validated install-URL entry available",
    ):
        assert required in examples


def test_backlog_records_english_source_delivery() -> None:
    assert "### BPM096-M10-02 — English product and API source updated" in BACKLOG.read_text(
        encoding="utf-8"
    )
