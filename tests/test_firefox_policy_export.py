from __future__ import annotations

from app.services.firefox_policy_export import render_firefox_policies_document


def test_render_firefox_policies_document_wraps_flags_under_policies_key():
    document = render_firefox_policies_document({"BlockAboutConfig": True})

    assert document == {"policies": {"BlockAboutConfig": True}}


def test_render_firefox_policies_document_handles_empty_flags():
    assert render_firefox_policies_document(None) == {"policies": {}}
    assert render_firefox_policies_document({}) == {"policies": {}}
