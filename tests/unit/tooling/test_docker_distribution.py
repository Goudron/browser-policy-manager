from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCKER_ROOT = REPO_ROOT / "distributions" / "docker"


def test_docker_distribution_keeps_release_payload_and_explicit_migration_boundary() -> None:
    dockerfile = (DOCKER_ROOT / "Dockerfile").read_text(encoding="utf-8")
    entrypoint = (DOCKER_ROOT / "entrypoint.sh").read_text(encoding="utf-8")

    assert "python:3.14.3-slim-bookworm@sha256:" in dockerfile
    assert "COPY documentation/dist/bpm-documentation-0.9.6.tar.gz" in dockerfile
    assert "COPY alembic ./alembic" in dockerfile
    assert "USER bpm" in dockerfile
    assert 'VOLUME ["/var/lib/bpm"]' in dockerfile
    assert "COPY distributions/docker/requirements.lock /tmp/requirements.lock" in dockerfile
    assert "pip install --no-deps /tmp/wheels/browser_policy_manager-*.whl" in dockerfile
    assert "alembic -c /opt/bpm/alembic.ini upgrade head" in entrypoint
    assert "exec uvicorn app.main:app" in entrypoint


def test_compose_is_loopback_bound_and_never_runs_migrate_as_an_application_dependency() -> None:
    compose = (DOCKER_ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert '"127.0.0.1:${BPM_PORT:-8000}:8000"' in compose
    assert "bpm-migrate:" in compose
    assert 'command: ["migrate"]' in compose
    assert "depends_on:" not in compose


def test_make_targets_require_verified_docs_and_keep_volume_removal_out_of_automation() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "docker-build: docs-package-verify" in makefile
    assert "docker-migrate: docker-build" in makefile
    assert "docker-up: docker-build" in makefile
    assert "docker-smoke: docker-build" in makefile
    assert "docker volume rm" not in makefile


def test_runtime_lock_is_exact_and_excludes_optional_release_contours() -> None:
    lock = (DOCKER_ROOT / "requirements.lock").read_text(encoding="utf-8")

    assert "fastapi==0.141.1" in lock
    assert "alembic==1.19.1" in lock
    assert all(name not in lock.lower() for name in ("numpy", "onnxruntime", "tokenizers"))
    assert all(">=" not in line for line in lock.splitlines() if line and not line.startswith("#"))


def test_docker_release_smoke_workflow_is_manual_and_does_not_publish() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "docker-distribution-smoke.yml").read_text(
        encoding="utf-8"
    )

    assert "workflow_dispatch:" in workflow
    assert "inputs.run_docker_smoke == 'RUN'" in workflow
    assert "make docs-package" in workflow
    assert "make docker-build" in workflow
    assert "Build and verify BPM 0.9.6 Docker distribution" in workflow
    assert "docker_distribution_smoke.py --image browser-policy-manager:0.9.6" in workflow
    assert "bpm-documentation-0.9.6.tar.gz" in workflow
    assert "browser-policy-manager:0.9.6" in workflow
    assert "0.9.5" not in workflow
    assert "docker push" not in workflow
