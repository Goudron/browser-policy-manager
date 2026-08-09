#!/usr/bin/env python3
"""Atomically promote the verified BPM PDF candidate into the release delivery tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from documentation.buildlib.lifecycle import (  # noqa: E402
    Progress,
    StagedDirectory,
    atomic_promote,
    tracked_operation,
)
from documentation.tools import build_docs  # noqa: E402

DELIVERY_CONTRACT = REPOSITORY_ROOT / "documentation/config/pdf-delivery-contract-0.9.3.json"
DELIVERY_ROOT = REPOSITORY_ROOT / "distributions/documentation"
METADATA_FILES = ("manifest.json", "checksums.sha256", "NOTICE.txt")


class DeliveryError(RuntimeError):
    """A release-documentation promotion or verification failure."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeliveryError(f"cannot read JSON {path}: {exc}") from exc


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return str(path)


def _contract() -> dict[str, Any]:
    contract = _read_json(DELIVERY_CONTRACT)
    if (
        contract.get("schema_version") != 1
        or contract.get("backlog_item") != "BPM094-M11-05"
        or contract.get("target_bpm_version") != build_docs._product_version()
        or contract.get("candidate_root") != "documentation/build/pdf"
        or contract.get("delivery_root") != "distributions/documentation"
        or contract.get("delivery_directory") != "{bpm_version}"
    ):
        raise DeliveryError("PDF delivery contract is unsupported or does not match BPM")
    return contract


def _version_directory(contract: dict[str, Any]) -> str:
    version = build_docs._product_version()
    try:
        directory = contract["delivery_directory"].format(bpm_version=version)
    except (AttributeError, KeyError) as exc:
        raise DeliveryError("cannot format delivery version directory") from exc
    if directory != version or Path(directory).name != directory or directory in {"", ".", ".."}:
        raise DeliveryError(f"unsafe delivery version directory: {directory!r}")
    return directory


def _pdf_records(layout: dict[str, Any], candidate_root: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for locale in build_docs.LOCALES:
        for guide_id, _map_name in build_docs.PDF_GUIDE_MAPS:
            filename = build_docs._pdf_guide_filename(layout, guide_id, locale)
            candidate_path = candidate_root / locale / filename
            delivery_path = Path("pdf") / locale / filename
            records.append(
                {
                    "locale": locale,
                    "guide_id": guide_id,
                    "candidate_path": candidate_path.relative_to(candidate_root).as_posix(),
                    "path": delivery_path.as_posix(),
                    "sha256": _sha256(candidate_path),
                }
            )
    return records


def _expected_paths(layout: dict[str, Any]) -> set[str]:
    return {
        *(METADATA_FILES),
        *(f"pdf/{path}" for path in build_docs._expected_pdf_paths(layout)),
    }


def _notice(candidate_manifest: dict[str, Any]) -> str:
    return "\n".join(
        (
            f"Browser Policy Manager {build_docs._product_version()} documentation PDFs",
            "",
            "Generated release artifact. Do not edit files in this directory manually.",
            "Source: reviewed six-locale DITA documentation.",
            f"Source revision: {candidate_manifest['source_revision']}",
            f"Source fingerprint: {candidate_manifest['source_fingerprint']}",
            "",
            "Rebuild candidate: make docs-pdf-build",
            "Verify candidate: make docs-pdf-verify",
            "Promote delivery: make docs-pdf-deliver",
            "Verify delivery: make docs-pdf-delivery-verify",
            "",
            "This delivery contains documentation PDFs and declared metadata only.",
            "It must not contain source DITA, HTML sites, local models, embeddings, RAG indexes, caches, logs, reports, credentials or secrets.",
            "",
        )
    )


def _checksums(root: Path, paths: set[str]) -> str:
    return "".join(f"{_sha256(root / path)}  {path}\n" for path in sorted(paths))


def build_delivery_tree(destination: Path) -> None:
    contract = _contract()
    layout = build_docs._pdf_layout()
    candidate_root = build_docs.PDF_BUILD_ROOT
    build_docs.validate_pdf_tree(candidate_root)
    destination.mkdir(parents=True, exist_ok=False)
    candidate_manifest_path = candidate_root / build_docs.PDF_BUILD_MANIFEST
    candidate_manifest = _read_json(candidate_manifest_path)
    records = _pdf_records(layout, candidate_root)
    for record in records:
        target = destination / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(candidate_root / record["candidate_path"], target)
    manifest = {
        "schema_version": 1,
        "contract_id": contract["contract_id"],
        "backlog_item": contract["backlog_item"],
        "bpm_version": build_docs._product_version(),
        "source_revision": candidate_manifest["source_revision"],
        "source_fingerprint": candidate_manifest["source_fingerprint"],
        "candidate_manifest": {
            "path": "documentation/build/pdf/pdf-build-manifest.json",
            "sha256": _sha256(candidate_manifest_path),
        },
        "pdfs": records,
    }
    _write_json(destination / "manifest.json", manifest)
    (destination / "NOTICE.txt").write_text(_notice(candidate_manifest), encoding="utf-8")
    (destination / "checksums.sha256").write_text(
        _checksums(destination, _expected_paths(layout) - {"checksums.sha256"}),
        encoding="ascii",
    )
    validate_delivery_tree(destination)


def validate_delivery_tree(root: Path) -> None:
    contract = _contract()
    layout = build_docs._pdf_layout()
    if not root.is_dir() or root.is_symlink():
        raise DeliveryError(f"delivery root is missing or unsafe: {root}")
    expected_paths = _expected_paths(layout)
    paths = list(root.rglob("*"))
    if any(path.is_symlink() for path in paths):
        raise DeliveryError("delivery contains a symbolic link")
    actual_paths = {
        path.relative_to(root).as_posix()
        for path in paths
        if path.is_file() and not path.is_symlink()
    }
    if actual_paths != expected_paths:
        raise DeliveryError(
            "delivery file set does not match contract: "
            f"missing={sorted(expected_paths - actual_paths)}, "
            f"unexpected={sorted(actual_paths - expected_paths)}"
        )
    manifest = _read_json(root / "manifest.json")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("contract_id") != contract["contract_id"]
        or manifest.get("backlog_item") != contract["backlog_item"]
        or manifest.get("bpm_version") != build_docs._product_version()
    ):
        raise DeliveryError("delivery manifest identity is invalid")
    candidate_root = build_docs.PDF_BUILD_ROOT
    build_docs.validate_pdf_tree(candidate_root)
    candidate_manifest_path = candidate_root / build_docs.PDF_BUILD_MANIFEST
    candidate_manifest = _read_json(candidate_manifest_path)
    if (
        manifest.get("source_revision") != candidate_manifest.get("source_revision")
        or manifest.get("source_fingerprint") != candidate_manifest.get("source_fingerprint")
        or manifest.get("candidate_manifest", {}).get("sha256") != _sha256(candidate_manifest_path)
    ):
        raise DeliveryError("delivery provenance does not match the verified PDF candidate")
    records = manifest.get("pdfs")
    if not isinstance(records, list) or len(records) != len(build_docs.LOCALES) * len(
        build_docs.PDF_GUIDE_MAPS
    ):
        raise DeliveryError("delivery PDF inventory is invalid")
    expected_records = {record["path"]: record for record in _pdf_records(layout, candidate_root)}
    actual_records = {record.get("path"): record for record in records if isinstance(record, dict)}
    if set(actual_records) != set(expected_records):
        raise DeliveryError("delivery PDF paths do not match the candidate inventory")
    for path, expected in expected_records.items():
        actual = actual_records[path]
        if actual != expected or _sha256(root / path) != expected["sha256"]:
            raise DeliveryError(f"delivery PDF provenance mismatch: {path}")
        build_docs._validate_pdf_file(root / path)
    expected_checksums = _checksums(root, expected_paths - {"checksums.sha256"})
    if (root / "checksums.sha256").read_text(encoding="ascii") != expected_checksums:
        raise DeliveryError("delivery checksums do not match declared files")
    notice = (root / "NOTICE.txt").read_text(encoding="utf-8")
    for command in contract["operator_commands"].values():
        if command not in notice:
            raise DeliveryError("delivery notice is missing an operator command")


def promote_delivery() -> None:
    contract = _contract()
    version = _version_directory(contract)
    build_docs.validate_pdf_tree(build_docs.PDF_BUILD_ROOT)
    DELIVERY_ROOT.mkdir(parents=True, exist_ok=True)
    destination = DELIVERY_ROOT / version
    with StagedDirectory(DELIVERY_ROOT, f"{version}-delivery") as staging:
        candidate = staging.candidate(version)
        progress = Progress("PDF delivery", 2)
        with tracked_operation(progress):
            progress.phase("build verified release directory")
            build_delivery_tree(candidate)
            progress.complete_unit("release directory")
            progress.phase("atomically promote verified release directory")
            atomic_promote(candidate, destination, validate=validate_delivery_tree)
            progress.complete_unit("release directory promotion")
    validate_delivery_tree(destination)
    print(
        f"PDF delivery promoted to {_display_path(destination)}",
        flush=True,
    )


def verify_delivery() -> None:
    contract = _contract()
    destination = DELIVERY_ROOT / _version_directory(contract)
    validate_delivery_tree(destination)
    print(
        f"PDF delivery verified: {_display_path(destination)}",
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("promote", "verify"))
    args = parser.parse_args()
    try:
        {"promote": promote_delivery, "verify": verify_delivery}[args.command]()
    except (DeliveryError, build_docs.BuildError, OSError) as exc:
        print(f"PDF delivery failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
