from __future__ import annotations

from pathlib import Path

import pytest

from documentation.buildlib.lifecycle import (
    Progress,
    StagedDirectory,
    atomic_promote,
    atomic_promote_many,
    remove_path,
    sha256_file,
    tracked_operation,
)


def test_progress_reports_only_completed_units_and_a_terminal_state(
    capsys: pytest.CaptureFixture[str],
) -> None:
    progress = Progress("Test build", 2)

    with tracked_operation(progress):
        progress.phase("prepare")
        progress.complete_unit("first")
        progress.complete_unit("second")

    output = capsys.readouterr().out
    assert "phase=prepare; completed=0/2" in output
    assert "completed=1/2; unit=first" in output
    assert "completed=2/2; unit=second" in output
    assert "terminal=complete; completed=2/2" in output
    assert "%" not in output


def test_failed_candidate_is_quarantined_without_replacing_active_artifact(tmp_path: Path) -> None:
    active = tmp_path / "site"
    active.mkdir()
    (active / "state.txt").write_text("verified", encoding="utf-8")

    with pytest.raises(RuntimeError, match="candidate validation failed"):
        with StagedDirectory(tmp_path, "site-build") as staging:
            candidate = staging.candidate("site")
            candidate.mkdir()
            (candidate / "state.txt").write_text("candidate", encoding="utf-8")
            atomic_promote(
                candidate,
                active,
                validate=lambda _candidate: (_ for _ in ()).throw(
                    RuntimeError("candidate validation failed")
                ),
            )

    assert (active / "state.txt").read_text(encoding="utf-8") == "verified"
    quarantines = list((tmp_path / ".quarantine").glob("site-build-*"))
    assert len(quarantines) == 1
    assert (quarantines[0] / "site" / "state.txt").read_text(encoding="utf-8") == "candidate"


def test_interrupted_candidate_is_quarantined_and_reports_terminal_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    active = tmp_path / "site"
    active.mkdir()
    (active / "state.txt").write_text("verified", encoding="utf-8")

    with pytest.raises(KeyboardInterrupt):
        with StagedDirectory(tmp_path, "site-build") as staging:
            candidate = staging.candidate("site")
            candidate.mkdir()
            (candidate / "state.txt").write_text("partial", encoding="utf-8")
            with tracked_operation(Progress("Site build", 1)):
                raise KeyboardInterrupt

    output = capsys.readouterr().out
    assert "Site build: terminal=interrupted; completed=0/1" in output
    assert (active / "state.txt").read_text(encoding="utf-8") == "verified"
    quarantines = list((tmp_path / ".quarantine").glob("site-build-*"))
    assert len(quarantines) == 1
    assert (quarantines[0] / "site" / "state.txt").read_text(encoding="utf-8") == "partial"


def test_atomic_promotion_replaces_a_verified_artifact_set_together(tmp_path: Path) -> None:
    archive = tmp_path / "artifact.tar.gz"
    checksum = tmp_path / "artifact.tar.gz.sha256"
    archive.write_text("old archive", encoding="utf-8")
    checksum.write_text("old checksum", encoding="utf-8")
    candidate_archive = tmp_path / "candidate.tar.gz"
    candidate_checksum = tmp_path / "candidate.tar.gz.sha256"
    candidate_archive.write_text("new archive", encoding="utf-8")
    candidate_checksum.write_text("new checksum", encoding="utf-8")

    atomic_promote_many(
        ((candidate_archive, archive), (candidate_checksum, checksum)),
    )

    assert archive.read_text(encoding="utf-8") == "new archive"
    assert checksum.read_text(encoding="utf-8") == "new checksum"
    assert not list(tmp_path.glob(".*-previous"))


def test_lifecycle_helpers_validate_progress_boundaries_and_remove_controlled_paths(
    tmp_path: Path,
) -> None:
    payload = tmp_path / "artifact.bin"
    payload.write_bytes(b"documentation artifact")
    directory = tmp_path / "candidate"
    directory.mkdir()
    (directory / "payload.txt").write_text("candidate", encoding="utf-8")

    assert (
        sha256_file(payload) == "645951d562ac51189f7061a150724054df976f98c97ce0b9709b76c64e4d1981"
    )
    remove_path(payload)
    remove_path(directory)
    assert not payload.exists()
    assert not directory.exists()

    with pytest.raises(ValueError, match="cannot be negative"):
        Progress("Broken", -1)
    progress = Progress("Bounded", 0)
    with pytest.raises(ValueError, match="exceeds declared total"):
        progress.complete_unit("extra")


def test_staging_validates_ownership_and_cleans_successful_candidates(tmp_path: Path) -> None:
    staging = StagedDirectory(tmp_path, "candidate")
    with pytest.raises(RuntimeError, match="not active"):
        staging.candidate("site")

    with StagedDirectory(tmp_path, "candidate") as staging:
        with pytest.raises(ValueError, match="unsafe staged candidate name"):
            staging.candidate("../site")
        candidate = staging.candidate("site")
        candidate.mkdir()

    assert not list(tmp_path.glob(".candidate-*"))
    quarantine = tmp_path / ".quarantine"
    assert not quarantine.exists() or not list(quarantine.glob("candidate-*"))


def test_tracked_operation_reports_failed_terminal_state(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(RuntimeError, match="failed"):
        with tracked_operation(Progress("Failure", 1)):
            raise RuntimeError("failed")

    assert "Failure: terminal=failed; completed=0/1" in capsys.readouterr().out


def test_atomic_promotion_rejects_invalid_sets_and_restores_after_replace_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "active.txt"
    destination.write_text("verified", encoding="utf-8")
    candidate = tmp_path / "candidate.txt"
    candidate.write_text("candidate", encoding="utf-8")

    with pytest.raises(ValueError, match="requires at least one"):
        atomic_promote_many(())
    with pytest.raises(ValueError, match="must be unique"):
        atomic_promote_many(((candidate, destination), (candidate, destination)))

    original_replace = Path.replace

    def fail_candidate_promotion(source: Path, target: Path) -> Path:
        if source == candidate and target == destination:
            raise OSError("promote failed")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_candidate_promotion)

    with pytest.raises(OSError, match="promote failed"):
        atomic_promote(candidate, destination)

    assert destination.read_text(encoding="utf-8") == "verified"
    assert candidate.read_text(encoding="utf-8") == "candidate"


def test_staging_exit_and_atomic_promotion_cover_no_active_path_and_full_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staging = StagedDirectory(tmp_path, "inactive")
    assert staging.__exit__(None, None, None) is False

    first_candidate = tmp_path / "first-candidate.txt"
    second_candidate = tmp_path / "second-candidate.txt"
    first_destination = tmp_path / "first.txt"
    second_destination = tmp_path / "second.txt"
    first_candidate.write_text("first candidate", encoding="utf-8")
    second_candidate.write_text("second candidate", encoding="utf-8")
    first_destination.write_text("first verified", encoding="utf-8")

    original_replace = Path.replace

    def fail_second_promotion(source: Path, target: Path) -> Path:
        if source == second_candidate and target == second_destination:
            raise OSError("second promote failed")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_second_promotion)

    with pytest.raises(OSError, match="second promote failed"):
        atomic_promote_many(
            ((first_candidate, first_destination), (second_candidate, second_destination))
        )

    assert first_destination.read_text(encoding="utf-8") == "first verified"
    assert second_candidate.read_text(encoding="utf-8") == "second candidate"
    assert not second_destination.exists()
