from __future__ import annotations

import sys

from app.compliance.firefox.cis.validation import format_validation_summary, validate_sources


def main() -> int:
    result = validate_sources()
    print(format_validation_summary(result))
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())

