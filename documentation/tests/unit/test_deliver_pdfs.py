from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "documentation/tools/deliver_pdfs.py"
SPEC = importlib.util.spec_from_file_location("deliver_pdfs", MODULE_PATH)
assert SPEC and SPEC.loader
deliver_pdfs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deliver_pdfs)


def _pdf_payload() -> bytes:
    return b"%PDF-1.5\n" + (b"% PDF delivery test padding\n" * 80) + b"%%EOF\n"


def _layout() -> dict[str, object]:
    return {
        "guides": [
            {
                "id": "user-guide",
                "filename": "browser-policy-manager-user-guide-{locale}-{bpm_version}.pdf",
            },
            {
                "id": "administrator-guide",
                "filename": "browser-policy-manager-administrator-guide-{locale}-{bpm_version}.pdf",
            },
        ]
    }


def _delivery_contract(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "contract_id": "bpm-pdf-delivery-0.9.5",
                "backlog_item": "BPM095-M8-05",
                "target_bpm_version": "0.9.5",
                "candidate_root": "documentation/build/pdf",
                "delivery_root": "distributions/documentation",
                "delivery_directory": "{bpm_version}",
                "operator_commands": {
                    "build_candidate": "make docs-pdf-build",
                    "verify_candidate": "make docs-pdf-verify",
                    "promote": "make docs-pdf-deliver",
                    "verify_delivery": "make docs-pdf-delivery-verify",
                },
            }
        ),
        encoding="utf-8",
    )


def test_promote_pdf_delivery_replaces_only_the_target_version_atomically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(deliver_pdfs.build_docs, "_product_version", lambda: "0.9.5")
    candidate = tmp_path / "candidate"
    for locale in deliver_pdfs.build_docs.LOCALES:
        for guide_id, _map_name in deliver_pdfs.build_docs.PDF_GUIDE_MAPS:
            filename = deliver_pdfs.build_docs._pdf_guide_filename(_layout(), guide_id, locale)
            path = candidate / locale / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(_pdf_payload())
    (candidate / "pdf-build-manifest.json").write_text(
        json.dumps(
            {
                "source_revision": "a" * 40,
                "source_fingerprint": "source-fingerprint",
            }
        ),
        encoding="utf-8",
    )
    contract = tmp_path / "delivery-contract.json"
    _delivery_contract(contract)
    delivery_root = tmp_path / "distributions/documentation"
    previous = delivery_root / "0.9.5"
    previous.mkdir(parents=True)
    (previous / "obsolete.txt").write_text("obsolete", encoding="utf-8")
    monkeypatch.setattr(deliver_pdfs, "DELIVERY_CONTRACT", contract)
    monkeypatch.setattr(deliver_pdfs, "DELIVERY_ROOT", delivery_root)
    monkeypatch.setattr(deliver_pdfs.build_docs, "PDF_BUILD_ROOT", candidate)
    monkeypatch.setattr(deliver_pdfs.build_docs, "validate_pdf_tree", lambda _root: None)
    monkeypatch.setattr(deliver_pdfs.build_docs, "_pdf_layout", _layout)

    deliver_pdfs.promote_delivery()

    promoted = delivery_root / "0.9.5"
    assert not (promoted / "obsolete.txt").exists()
    assert len(list(promoted.rglob("*.pdf"))) == 12
    assert {path.name for path in promoted.iterdir() if path.is_file()} == {
        "manifest.json",
        "checksums.sha256",
        "NOTICE.txt",
    }
    deliver_pdfs.verify_delivery()


def test_delivery_verification_rejects_an_unexpected_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(deliver_pdfs.build_docs, "_product_version", lambda: "0.9.5")
    candidate = tmp_path / "candidate"
    destination = tmp_path / "delivery"
    for locale in deliver_pdfs.build_docs.LOCALES:
        for guide_id, _map_name in deliver_pdfs.build_docs.PDF_GUIDE_MAPS:
            filename = deliver_pdfs.build_docs._pdf_guide_filename(_layout(), guide_id, locale)
            path = candidate / locale / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(_pdf_payload())
    (candidate / "pdf-build-manifest.json").write_text(
        json.dumps(
            {
                "source_revision": "a" * 40,
                "source_fingerprint": "source-fingerprint",
            }
        ),
        encoding="utf-8",
    )
    contract = tmp_path / "delivery-contract.json"
    _delivery_contract(contract)
    monkeypatch.setattr(deliver_pdfs, "DELIVERY_CONTRACT", contract)
    monkeypatch.setattr(deliver_pdfs.build_docs, "PDF_BUILD_ROOT", candidate)
    monkeypatch.setattr(deliver_pdfs.build_docs, "validate_pdf_tree", lambda _root: None)
    monkeypatch.setattr(deliver_pdfs.build_docs, "_pdf_layout", _layout)

    deliver_pdfs.build_delivery_tree(destination)
    (destination / "unexpected.txt").write_text("not allowed", encoding="utf-8")

    with pytest.raises(deliver_pdfs.DeliveryError, match="file set"):
        deliver_pdfs.validate_delivery_tree(destination)
