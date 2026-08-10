from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_only_checksum_protected_upstream_payloads_are_excluded_from_whitespace_checks():
    lines = [
        line
        for line in (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]

    assert lines == [
        "app/static/vendor/profiles_monaco.js -whitespace",
        "app/static/vendor/dompurify.LICENSE-MPL -whitespace",
        "app/static/vendor/monaco.ThirdPartyNotices.txt -whitespace",
    ]
