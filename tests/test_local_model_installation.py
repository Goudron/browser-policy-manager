from __future__ import annotations

import hashlib
from pathlib import Path

import httpx
import pytest

import app.ai.model_installation as installation


@pytest.fixture
def small_artifact(monkeypatch: pytest.MonkeyPatch) -> installation.ModelArtifact:
    payload = b"selected-local-model-test-payload"
    artifact = installation.ModelArtifact(
        model_id=installation.MODEL_ID,
        filename=installation.ARTIFACT_FILENAME,
        source="https://model.example.invalid/pinned.gguf",
        sha256=hashlib.sha256(payload).hexdigest(),
        byte_count=len(payload),
        license_spdx="Apache-2.0",
        upstream="Qwen / test fixture",
        source_revision="0123456789012345678901234567890123456789",
        target_architectures=("x86_64",),
    )
    monkeypatch.setattr(installation, "SELECTED_ARTIFACT", artifact)
    return artifact


def _client_for(handler: httpx.MockTransport) -> installation.ClientFactory:
    return lambda: httpx.Client(transport=handler)


def test_install_requires_confirmation_and_never_calls_network_without_it(
    tmp_path: Path, small_artifact: installation.ModelArtifact
) -> None:
    called = False

    def unexpected_client() -> httpx.Client:
        nonlocal called
        called = True
        raise AssertionError("network client must not be created")

    installer = installation.ModelInstaller(tmp_path / "models", client_factory=unexpected_client)

    with pytest.raises(installation.ExplicitConfirmationRequired):
        installer.install(confirmed=False)

    assert called is False
    assert installer.verify().reason_code == "artifact_missing"


def test_cancelled_install_never_creates_a_network_client_or_promotes_an_artifact(
    tmp_path: Path, small_artifact: installation.ModelArtifact
) -> None:
    called = False

    def unexpected_client() -> httpx.Client:
        nonlocal called
        called = True
        raise AssertionError("cancelled installation must not create an HTTP client")

    installer = installation.ModelInstaller(tmp_path / "models", client_factory=unexpected_client)

    with pytest.raises(installation.InstallationCancelled, match="installation_cancelled"):
        installer.install(confirmed=True, cancelled=lambda: True)

    assert called is False
    assert installer.verify().state == "not-installed"


def test_cancelling_during_download_leaves_only_a_non_runnable_partial_artifact(
    tmp_path: Path, small_artifact: installation.ModelArtifact
) -> None:
    installer = installation.ModelInstaller(
        tmp_path / "models",
        client_factory=_client_for(
            httpx.MockTransport(
                lambda request: httpx.Response(200, content=b"selected-local-model-test-payload")
            )
        ),
    )
    checks = iter((False, False, True))

    with pytest.raises(installation.InstallationCancelled, match="installation_cancelled"):
        installer.install(confirmed=True, cancelled=lambda: next(checks))

    partial = installer._staging_dir / f"{small_artifact.filename}.part"
    assert partial.is_file()
    assert partial.stat().st_size == 0
    assert installer.verify().state == "not-installed"


def test_install_verifies_checksum_promotes_atomically_and_can_be_removed(
    tmp_path: Path, small_artifact: installation.ModelArtifact
) -> None:
    payload = b"selected-local-model-test-payload"
    seen_progress: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL(small_artifact.source)
        assert request.headers["Accept-Encoding"] == "identity"
        return httpx.Response(200, content=payload)

    installer = installation.ModelInstaller(
        tmp_path / "models", client_factory=_client_for(httpx.MockTransport(handler))
    )

    result = installer.install(
        confirmed=True, progress=lambda item: seen_progress.append(item.downloaded_bytes)
    )

    assert result.state == "installed"
    assert installer.verify().verified is True
    assert installer.artifact_path.read_bytes() == payload
    assert seen_progress == [0, len(payload)]
    assert installer.remove(confirmed=True).state == "removed"
    assert installer.verify().state == "not-installed"


def test_install_resumes_a_manifest_owned_partial_download(
    tmp_path: Path, small_artifact: installation.ModelArtifact
) -> None:
    payload = b"selected-local-model-test-payload"
    seen_range: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_range.append(request.headers.get("Range"))
        return httpx.Response(206, content=payload[8:])

    installer = installation.ModelInstaller(
        tmp_path / "models", client_factory=_client_for(httpx.MockTransport(handler))
    )
    installer._ensure_store()
    installer._prepare_staging()
    part_path = installer._staging_dir / f"{small_artifact.filename}.part"
    part_path.write_bytes(payload[:8])

    assert installer.install(confirmed=True).state == "installed"
    assert seen_range == ["bytes=8-"]
    assert installer.verify().verified is True


def test_install_promotes_a_complete_verified_partial_without_a_network_request(
    tmp_path: Path, small_artifact: installation.ModelArtifact
) -> None:
    payload = b"selected-local-model-test-payload"
    installer = installation.ModelInstaller(
        tmp_path / "models",
        client_factory=lambda: pytest.fail("complete verified partial must not use the network"),
    )
    installer._ensure_store()
    installer._prepare_staging()
    part_path = installer._staging_dir / f"{small_artifact.filename}.part"
    part_path.write_bytes(payload)

    assert installer.install(confirmed=True).state == "installed"
    assert installer.verify().verified is True


def test_dead_install_lock_is_recovered_but_live_lock_blocks_install(
    tmp_path: Path, small_artifact: installation.ModelArtifact, monkeypatch: pytest.MonkeyPatch
) -> None:
    installer = installation.ModelInstaller(tmp_path / "models")
    installer._ensure_store()
    installer._lock_path.write_text("99999999", encoding="ascii")
    monkeypatch.setattr(installation._OperationLock, "_process_is_alive", lambda self, pid: False)

    with installer._exclusive_operation():
        assert installer._lock_path.exists()

    installer._lock_path.write_text("12345", encoding="ascii")
    monkeypatch.setattr(installation._OperationLock, "_process_is_alive", lambda self, pid: True)
    with pytest.raises(installation.InstallationBusyError):
        with installer._exclusive_operation():
            pass


def test_offline_local_artifact_install_needs_confirmation_and_never_uses_network(
    tmp_path: Path, small_artifact: installation.ModelArtifact
) -> None:
    source_path = tmp_path / "pre-obtained.gguf"
    source_path.write_bytes(b"selected-local-model-test-payload")
    installer = installation.ModelInstaller(
        tmp_path / "models",
        client_factory=lambda: pytest.fail("offline install must not construct an HTTP client"),
    )

    with pytest.raises(installation.ExplicitConfirmationRequired):
        installer.install_local(source_path, confirmed=False)

    assert installer.install_local(source_path, confirmed=True).state == "installed"
    assert installer.verify().verified is True


def test_corrupt_download_fails_closed_without_an_installed_artifact(
    tmp_path: Path, small_artifact: installation.ModelArtifact
) -> None:
    installer = installation.ModelInstaller(
        tmp_path / "models",
        client_factory=_client_for(
            httpx.MockTransport(lambda request: httpx.Response(200, content=b"x" * 33))
        ),
    )

    with pytest.raises(installation.ArtifactVerificationError, match="download_checksum_mismatch"):
        installer.install(confirmed=True)

    assert installer.verify().state == "not-installed"
    assert installer.artifact_path.exists() is False


def test_disclosure_is_owned_by_each_supported_locale() -> None:
    installer = installation.ModelInstaller(Path("data") / "ai" / "models")

    assert set(installation.DISCLOSURES) == set(installation.ACTIVE_CATALOG_LOCALES)
    for locale in installation.ACTIVE_CATALOG_LOCALES:
        disclosure = installer.disclosure(locale)
        assert disclosure["license"] == "Apache-2.0"
        assert disclosure["byte_count"] == installation.ARTIFACT_BYTES
        assert disclosure["sha256"] == installation.ARTIFACT_SHA256
        assert "response" in disclosure["summary"].lower() or locale != "en"


def test_symlink_owned_artifact_is_never_verified_or_removed(tmp_path: Path) -> None:
    installer = installation.ModelInstaller(tmp_path / "models")
    installer._ensure_store()
    installer.model_dir.mkdir()
    installer.artifact_path.symlink_to(tmp_path / "outside.gguf")

    assert installer.verify().reason_code == "unsafe_or_missing_artifact"
    with pytest.raises(installation.ArtifactVerificationError, match="refusing_to_remove_symlink"):
        installer.remove(confirmed=True)


def test_default_model_client_disables_redirects_and_proxy_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(installation.httpx, "Client", FakeClient)

    installation.ModelInstaller(tmp_path / "models")._new_client()

    assert captured["follow_redirects"] is False
    assert captured["trust_env"] is False


def test_verify_reports_each_invalid_owned_artifact_state(
    tmp_path: Path, small_artifact: installation.ModelArtifact, monkeypatch: pytest.MonkeyPatch
) -> None:
    installer = installation.ModelInstaller(tmp_path / "models")
    monkeypatch.setattr(installation, "_machine_architecture", lambda: "unsupported")
    assert installer.verify().reason_code == "unsupported_architecture"
    monkeypatch.setattr(installation, "_machine_architecture", lambda: "x86_64")
    installer._ensure_store()
    installer.model_dir.mkdir()
    assert installer.verify().reason_code == "unsafe_or_missing_artifact"
    installer.artifact_path.write_bytes(b"x")
    assert installer.verify().reason_code == "unsafe_or_missing_metadata"
    installer.metadata_path.write_text("{}", encoding="utf-8")
    assert installer.verify().reason_code == "artifact_size_mismatch"
    installer.artifact_path.write_bytes(b"selected-local-model-test-payload")
    assert installer.verify().reason_code == "metadata_mismatch"
    installer.metadata_path.write_text("{", encoding="utf-8")
    assert installer.verify().reason_code == "metadata_unreadable"


def test_download_redirect_validation_and_write_guards(
    tmp_path: Path, small_artifact: installation.ModelArtifact
) -> None:
    response = httpx.Response(302, headers={"location": "https://cdn.hf.co/model"}, request=httpx.Request("GET", "https://huggingface.co/model"))
    assert installation.ModelInstaller._verified_redirect(response) == "https://cdn.hf.co/model"
    for headers in ({}, {"location": "http://example.invalid/model"}):
        bad = httpx.Response(302, headers=headers, request=httpx.Request("GET", "https://huggingface.co/model"))
        with pytest.raises(installation.ModelInstallationError):
            installation.ModelInstaller._verified_redirect(bad)
    installer = installation.ModelInstaller(tmp_path / "models")
    part = tmp_path / "part"
    with pytest.raises(installation.ModelInstallationError, match="download_http"):
        installer._write_download(httpx.Response(500), part, 0, None, None)
    with pytest.raises(installation.ArtifactVerificationError, match="exceeds"):
        installer._write_download(httpx.Response(200, content=b"x" * (small_artifact.byte_count + 1)), part, 0, None, None)
