from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools import provision_firefox_schema_inputs as provisioner
from tools.convert_policies_from_upstream_lib.common import load_schema_build_targets


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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


def test_provision_downloads_once_then_verifies_cached_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy_document = b"policy document"
    linux_policies = b'{"policies": {}}\n'
    input_set = provisioner.InputSet(
        source_tag="mozilla-policy-templates-v-test",
        upstream_tag="v-test",
        files=(
            provisioner.InputFile(
                "policy-templates.md", "https://example.test/docs", _digest(policy_document)
            ),
            provisioner.InputFile(
                "linux-policies.json", "https://example.test/linux", _digest(linux_policies)
            ),
        ),
    )
    downloaded: list[str] = []

    def fake_download(spec: provisioner.InputFile, destination: Path) -> None:
        downloaded.append(spec.name)
        payload = policy_document if spec.name == "policy-templates.md" else linux_policies
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        provisioner._verify(destination, spec.sha256)

    monkeypatch.setattr(provisioner, "_download_verified", fake_download)
    provisioner.provision((input_set,), tmp_path)
    provisioner.provision((input_set,), tmp_path)

    assert downloaded == ["policy-templates.md", "linux-policies.json"]


def test_load_manifest_rejects_unpinned_or_incomplete_input_set(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "inputs": [
                    {
                        "source_tag": "source",
                        "upstream_tag": "v-test",
                        "files": [
                            {
                                "name": "policy-templates.md",
                                "url": "https://example.test/docs",
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
