from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/architecture/firefox-153-dual-esr-schema-contract-0.9.2.md"

pytestmark = pytest.mark.docs_contract


def test_firefox_153_dual_esr_contract_declares_three_independent_channels() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")

    for required in (
        "`release-153`",
        "`esr-153.0`",
        "`esr-140.13`",
        "`mozilla-policy-templates-master-a892b621f7f98ee91c8ed84290641f2703e88490`",
        "`mozilla-policy-templates-v7.12`",
    ):
        assert required in contract


def test_firefox_140_esr_never_auto_migrates_to_firefox_153_esr() -> None:
    contract = " ".join(CONTRACT.read_text(encoding="utf-8").split())

    assert "`release-152`, `release-153` | `release-153`" in contract
    assert "`esr-140.12`, `esr-140.13` | `esr-140.13`" in contract
    assert (
        "There is no automatic migration from any Firefox 140 ESR channel to `esr-153.0`"
        in contract
    )
    assert "must not determine any persistence migration while two ESRs are supported" in contract
