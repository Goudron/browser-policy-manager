from __future__ import annotations

import json
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = (
    REPOSITORY_ROOT
    / "documentation"
    / "config"
    / "documentation-editorial-release-gate-0.9.2.json"
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


def main() -> int:
    gate = load_gate()
    blockers = release_blockers(gate)
    if blockers:
        print("Documentation editorial release gate is blocked:")
        for blocker in blockers:
            print(f"- {blocker}")
        return 1

    print("Documentation editorial release gate accepted for all six locales.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
