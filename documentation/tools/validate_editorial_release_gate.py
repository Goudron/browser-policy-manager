from __future__ import annotations

import json
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = (
    REPOSITORY_ROOT / "documentation" / "config" / "documentation-editorial-release-gate-0.9.2.json"
)
M11_REVIEW_PATH = (
    REPOSITORY_ROOT
    / "documentation"
    / "config"
    / "documentation-editorial-pdf-release-review-0.9.4.json"
)
REQUIRED_LOCALES = {"en", "ru", "de", "zh-CN", "fr", "es-ES"}


def load_gate(path: Path = GATE_PATH) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def release_blockers(gate: dict[str, object]) -> list[str]:
    locales = gate.get("locales")
    if not isinstance(locales, dict):
        return ["the locale review registry is missing"]

    blockers: list[str] = []
    actual_locales = set(locales)
    if actual_locales != REQUIRED_LOCALES:
        blockers.append(
            "the locale review registry must contain exactly "
            f"{', '.join(sorted(REQUIRED_LOCALES))}; found {', '.join(sorted(actual_locales))}"
        )

    for locale in sorted(REQUIRED_LOCALES):
        entry = locales.get(locale)
        if not isinstance(entry, dict):
            blockers.append(f"{locale}: review record is missing")
            continue
        review_state = entry.get("review_state")
        review_record = entry.get("review_record")
        acceptance_marker = entry.get("record_acceptance_marker")
        if review_state != "accepted":
            blockers.append(f"{locale}: review state is {review_state!r}, not 'accepted'")
        if not isinstance(review_record, str) or not isinstance(acceptance_marker, str):
            blockers.append(f"{locale}: review record metadata is invalid")
            continue
        record_path = REPOSITORY_ROOT / review_record
        if not record_path.is_file():
            blockers.append(f"{locale}: review record does not exist: {review_record}")
            continue
        if review_state == "accepted" and acceptance_marker not in record_path.read_text(
            encoding="utf-8"
        ):
            blockers.append(f"{locale}: accepted review is missing its record marker")
    return blockers


def m11_review_blockers(review: dict[str, object]) -> list[str]:
    """Keep the current editorial/PDF review fail-closed beside historical gates."""

    required = {
        "schema_version": 1,
        "review_id": "bpm-0.9.4-editorial-pdf-release-review",
        "backlog_item": "BPM094-M11-06",
        "target_bpm_version": "0.9.4",
        "release_blocking": True,
    }
    blockers = [
        f"M11-06 review has invalid {key}: {review.get(key)!r}"
        for key, value in required.items()
        if review.get(key) != value
    ]
    if review.get("status") != "accepted":
        finding_ids = [
            finding.get("finding_id")
            for finding in review.get("blocking_findings", [])
            if isinstance(finding, dict)
        ]
        detail = ", ".join(str(finding_id) for finding_id in finding_ids) or "no finding id"
        blockers.append(f"M11-06 editorial/PDF review is not accepted: {detail}")
    return blockers


def main() -> int:
    gate = load_gate()
    review = load_gate(M11_REVIEW_PATH)
    blockers = release_blockers(gate) + m11_review_blockers(review)
    if blockers:
        print("Documentation editorial release gate is blocked:")
        for blocker in blockers:
            print(f"- {blocker}")
        return 1

    print("Documentation editorial release gate accepted for all six locales.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
