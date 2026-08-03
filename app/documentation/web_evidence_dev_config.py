"""Content-free development readiness for the optional external-sources path."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Literal

from app.core.config import Settings, get_settings
from app.documentation.web_evidence_consent import WebEvidenceConfiguration

ReadinessState = Literal["disabled", "credential_missing", "available"]


@dataclass(frozen=True)
class ExternalSourcesDevReadiness:
    """Safe startup state that never contains the provider credential."""

    state: ReadinessState
    available: bool
    reason_code: str
    guidance: str
    provider_probe_performed: bool = False


def assess_external_sources(settings: Settings) -> ExternalSourcesDevReadiness:
    """Classify local configuration without network access or secret rendering."""

    configuration = WebEvidenceConfiguration.from_settings(settings)
    reason_code = configuration.availability_code
    if reason_code == "assistant_web_disabled":
        return ExternalSourcesDevReadiness(
            state="disabled",
            available=False,
            reason_code=reason_code,
            guidance="set BPM_WEB_EVIDENCE_ENABLED=true in the ignored project-root .env",
        )
    if reason_code == "assistant_web_credential_unavailable":
        return ExternalSourcesDevReadiness(
            state="credential_missing",
            available=False,
            reason_code=reason_code,
            guidance=(
                "set BPM_BRAVE_SEARCH_API_SUBSCRIPTION_TOKEN in the ignored project-root .env"
            ),
        )
    return ExternalSourcesDevReadiness(
        state="available",
        available=True,
        reason_code=reason_code,
        guidance=(
            "configuration present; provider authentication is checked on the first "
            "reader-requested external question"
        ),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report optional external-source readiness without contacting the provider."
    )
    parser.add_argument("--json", action="store_true", help="emit the safe status as JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    readiness = assess_external_sources(get_settings())
    if args.json:
        print(json.dumps(asdict(readiness), sort_keys=True), flush=True)
    else:
        print(
            f"M13-08: external sources: {readiness.state}; {readiness.guidance}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
