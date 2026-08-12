from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path

import pytest

from tools import provision_firefox_schema_inputs as provisioner
from tools.convert_policies_from_upstream_lib.common import load_schema_build_targets


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _input_set(policy_document: bytes, linux_policies: bytes) -> provisioner.InputSet:
    return provisioner.InputSet(
        source_tag="mozilla-policy-templates-v-test",
        upstream_tag="v-test",
        upstream_release_url="https://example.test/releases/v-test",
        license_spdx="MPL-2.0",
        license_url="https://www.mozilla.org/MPL/2.0/",
        files=(
            provisioner.InputFile(
                "policy-templates.md",
                "https://example.test/docs",
                len(policy_document),
                _digest(policy_document),
            ),
            provisioner.InputFile(
                "linux-policies.json",
                "https://example.test/linux",
                len(linux_policies),
                _digest(linux_policies),
            ),
        ),
    )


def test_manifest_covers_each_declared_schema_source_and_converter_input() -> None:
    input_sets = provisioner.load_manifest()
    declared = {(item.upstream_tag, file.name) for item in input_sets for file in item.files}
    source_tags = {item.source_tag for item in input_sets}

    for target in load_schema_build_targets():
        assert target.source_tag in source_tags
        relative_documentation = target.documentation_input.relative_to(
            provisioner.DEFAULT_DESTINATION
        )
        relative_policies = target.linux_policies_input.relative_to(provisioner.DEFAULT_DESTINATION)
        assert (relative_documentation.parent.name, relative_documentation.name) in declared
        assert (relative_policies.parent.name, relative_policies.name) in declared


def test_manifest_pins_esr115_template_baseline_with_independent_provenance() -> None:
    input_sets = {input_set.upstream_tag: input_set for input_set in provisioner.load_manifest()}

    esr115 = input_sets["v5.12"]
    assert esr115.source_tag == "mozilla-policy-templates-v5.12"
    assert esr115.upstream_release_url == (
        "https://github.com/mozilla/policy-templates/releases/tag/v5.12"
    )
    assert (esr115.license_spdx, esr115.license_url) == (
        "MPL-2.0",
        "https://www.mozilla.org/MPL/2.0/",
    )
    assert {(item.name, item.bytes, item.sha256) for item in esr115.files} == {
        (
            "policy-templates.md",
            180619,
            "ce84a587dabc8e995e93206866e8d8ab3c9cf8423bb7dfbe74f20b9b28aaac42",
        ),
        (
            "linux-policies.json",
            11922,
            "da9caaefe75f7f5e54694bccda8a044e62f034dbd5889bcf1595bb08d6a04347",
        ),
    }


def test_provision_downloads_once_then_verifies_cached_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy_document = b"policy document"
    linux_policies = b'{"policies": {}}\n'
    input_set = _input_set(policy_document, linux_policies)
    downloaded: list[str] = []

    def fake_download(spec: provisioner.InputFile, destination: Path) -> None:
        downloaded.append(spec.name)
        payload = policy_document if spec.name == "policy-templates.md" else linux_policies
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        provisioner._verify(destination, spec.bytes, spec.sha256)

    monkeypatch.setattr(provisioner, "_download_verified", fake_download)
    provisioner.provision((input_set,), tmp_path)
    provisioner.provision((input_set,), tmp_path)

    assert downloaded == ["policy-templates.md", "linux-policies.json"]


def test_provision_quarantines_invalid_cache_before_replacing_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_set = _input_set(b"policy document", b'{"policies": {}}\n')
    cached = tmp_path / "v-test" / "policy-templates.md"
    cached.parent.mkdir(parents=True)
    cached.write_bytes(b"stale")
    downloaded: list[str] = []

    def fake_download(spec: provisioner.InputFile, destination: Path) -> None:
        downloaded.append(spec.name)
        payload = (
            b"policy document" if spec.name == "policy-templates.md" else b'{"policies": {}}\n'
        )
        destination.write_bytes(payload)

    monkeypatch.setattr(provisioner, "_download_verified", fake_download)
    provisioner.provision((input_set,), tmp_path)

    quarantined = list((tmp_path / "v-test" / ".quarantine").glob("policy-templates.md.*.invalid"))
    assert len(quarantined) == 1
    assert quarantined[0].read_bytes() == b"stale"
    assert cached.read_bytes() == b"policy document"
    assert downloaded == ["policy-templates.md", "linux-policies.json"]


def test_verify_rejects_wrong_size_before_checksum(tmp_path: Path) -> None:
    cached = tmp_path / "input"
    cached.write_bytes(b"short")

    with pytest.raises(provisioner.ProvisioningError, match="Size mismatch"):
        provisioner._verify(cached, expected_bytes=20, expected_sha256=_digest(b"expected payload"))


def test_verify_rejects_same_size_checksum_mismatch(tmp_path: Path) -> None:
    cached = tmp_path / "input"
    cached.write_bytes(b"corrupt")

    with pytest.raises(provisioner.ProvisioningError, match="Checksum mismatch"):
        provisioner._verify(cached, expected_bytes=7, expected_sha256=_digest(b"correct"))


def test_offline_mode_reuses_valid_cache_and_never_fetches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy_document = b"policy document"
    linux_policies = b'{"policies": {}}\n'
    input_set = _input_set(policy_document, linux_policies)
    for spec, payload in zip(input_set.files, (policy_document, linux_policies), strict=True):
        cached = tmp_path / input_set.upstream_tag / spec.name
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(payload)

    monkeypatch.setattr(
        provisioner,
        "_download_verified",
        lambda *_args: pytest.fail("offline mode must not fetch"),
    )
    provisioner.provision((input_set,), tmp_path, offline=True)


def test_offline_mode_fails_after_quarantining_invalid_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_set = _input_set(b"policy document", b'{"policies": {}}\n')
    cached = tmp_path / input_set.upstream_tag / "policy-templates.md"
    cached.parent.mkdir(parents=True)
    cached.write_bytes(b"invalid")
    monkeypatch.setattr(
        provisioner,
        "_download_verified",
        lambda *_args: pytest.fail("offline mode must not fetch"),
    )

    with pytest.raises(provisioner.ProvisioningError, match="Offline mode cannot replace invalid"):
        provisioner.provision((input_set,), tmp_path, offline=True)

    assert list((cached.parent / ".quarantine").glob("policy-templates.md.*.invalid"))


def test_download_retries_then_atomically_places_verified_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = b"policy document"
    spec = _input_set(payload, b'{"policies": {}}\n').files[0]
    attempts = 0
    replaced: list[tuple[Path, Path]] = []
    real_replace = os.replace

    class Response(io.BytesIO):
        def __enter__(self) -> Response:
            return self

        def __exit__(self, *_args: object) -> None:
            self.close()

    def fake_urlopen(*_args: object, **_kwargs: object) -> Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("temporary upstream failure")
        return Response(payload)

    def recording_replace(source: str | Path, destination: str | Path) -> None:
        replaced.append((Path(source), Path(destination)))
        real_replace(source, destination)

    monkeypatch.setattr(provisioner, "urlopen", fake_urlopen)
    monkeypatch.setattr(provisioner.os, "replace", recording_replace)
    destination = tmp_path / "v-test" / spec.name

    provisioner._download_verified(spec, destination)

    assert attempts == 2
    assert destination.read_bytes() == payload
    assert len(replaced) == 1
    assert replaced[0][1] == destination
    assert replaced[0][0].name.endswith(".part")
    assert not list(destination.parent.glob("*.part"))


def test_provision_reports_phase_input_and_completed_total_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    policy_document = b"policy document"
    linux_policies = b'{"policies": {}}\n'
    input_set = _input_set(policy_document, linux_policies)

    def fake_download(spec: provisioner.InputFile, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(
            policy_document if spec.name == "policy-templates.md" else linux_policies
        )

    monkeypatch.setattr(provisioner, "_download_verified", fake_download)
    provisioner.provision((input_set,), tmp_path)

    output = capsys.readouterr().out
    assert "phase cache:" in output
    assert "phase download: v-test/policy-templates.md" in output
    assert "[1/2] input: v-test/policy-templates.md" in output
    assert "[2/2] complete: linux-policies.json" in output


def test_load_manifest_rejects_unpinned_or_incomplete_input_set(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "inputs": [
                    {
                        "source_tag": "source",
                        "upstream_tag": "v-test",
                        "upstream_release_url": "https://example.test/releases/v-test",
                        "license_spdx": "MPL-2.0",
                        "license_url": "https://www.mozilla.org/MPL/2.0/",
                        "files": [
                            {
                                "name": "policy-templates.md",
                                "url": "https://example.test/docs",
                                "bytes": 1,
                                "sha256": "not-a-digest",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(provisioner.ProvisioningError, match="lowercase SHA-256"):
        provisioner.load_manifest(manifest)
