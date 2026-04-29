from __future__ import annotations

import argparse
import json
import sys

from app.compliance.firefox.cis.validation import build_coverage_report, format_coverage_markdown


def main() -> int:
    parser = argparse.ArgumentParser(description="Report CIS Firefox source mapping coverage.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on validation warnings.")
    args = parser.parse_args()

    report = build_coverage_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_coverage_markdown(report), end="")

    if not report["ok"] or (args.strict and report["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

