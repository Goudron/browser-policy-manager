"""Focused BPM096-M9-04 proof for certificate/trust source attribution."""

from __future__ import annotations

from app.compliance.firefox.profile_initialization_composition import (
    compose_profile_initialization,
)
from app.core.profile_certificate_provenance import (
    certificate_value_paths,
    converted_certificate_provenance,
    duplicate_certificate_provenance,
    imported_certificate_provenance,
    is_valid_certificate_provenance,
    reconcile_certificate_provenance,
)


def test_prepared_starter_and_cis_certificate_values_use_server_ledgers_only() -> None:
    result = compose_profile_initialization(
        schema_id="release-153",
        preset_id="basic_corporate",
        cis_baseline_id="cis_l1",
    )

    assert result.status == "valid"
    assert result.document is not None
    assert result.certificate_provenance is not None
    paths = result.certificate_provenance["paths"]
    assert paths["/Certificates/ImportEnterpriseRoots"] == "baseline"
    assert paths["/Authentication/NTLM"] == "cis"
    assert set(paths) == set(certificate_value_paths(result.document))
    assert is_valid_certificate_provenance(result.certificate_provenance)


def test_duplicate_preserves_same_schema_sources_and_marks_only_supported_values_converted() -> (
    None
):
    source = {
        "Certificates": {"Install": ["/etc/firefox/company.pem"]},
        "SecurityDevices": {"Add": {"company": "/usr/lib/pkcs11.so"}},
    }
    source_provenance = imported_certificate_provenance(source)

    same_schema = duplicate_certificate_provenance(
        source,
        source_provenance,
        source,
        cross_schema=False,
    )
    converted = duplicate_certificate_provenance(
        source,
        source_provenance,
        source,
        cross_schema=True,
    )

    assert set(same_schema["paths"].values()) == {"imported"}
    assert set(converted["paths"].values()) == {"converted"}
    assert converted == converted_certificate_provenance(source)


def test_update_keeps_untouched_cis_value_and_rejects_client_relabelling() -> None:
    before = {
        "Authentication": {"NTLM": [], "Locked": True},
        "Certificates": {"ImportEnterpriseRoots": True},
    }
    previous = {
        "contract_id": "bpm096-profile-certificate-provenance",
        "contract_version": 1,
        "paths": {
            "/Authentication/NTLM": "cis",
            "/Authentication/Locked": "baseline",
            "/Certificates/ImportEnterpriseRoots": "baseline",
        },
    }
    after = {
        "Authentication": {"NTLM": [], "Locked": False},
        "Certificates": {"ImportEnterpriseRoots": True},
    }
    submitted = {
        "contract_id": "bpm096-profile-certificate-provenance",
        "contract_version": 1,
        "paths": {
            "/Authentication/NTLM": "manual",
            "/Authentication/Locked": "cis",
            "/Certificates/ImportEnterpriseRoots": "imported",
        },
    }

    result = reconcile_certificate_provenance(before, previous, after, submitted)

    assert result["paths"] == {
        "/Authentication/Locked": "manual",
        "/Authentication/NTLM": "cis",
        "/Certificates/ImportEnterpriseRoots": "baseline",
    }


def test_raw_marker_is_only_retained_for_a_real_changed_raw_value() -> None:
    before = {"Certificates": {"Install": ["/etc/firefox/old.pem"]}}
    after = {"Certificates": {"Install": ["/etc/firefox/new.pem"]}}

    result = reconcile_certificate_provenance(
        before,
        imported_certificate_provenance(before),
        after,
        {
            "contract_id": "bpm096-profile-certificate-provenance",
            "contract_version": 1,
            "paths": {"/Certificates/Install/0": "raw"},
        },
    )

    assert result["paths"] == {"/Certificates/Install/0": "raw"}
