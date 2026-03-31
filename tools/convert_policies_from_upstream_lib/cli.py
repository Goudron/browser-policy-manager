from __future__ import annotations

import argparse
import json
from pathlib import Path

from .common import (
    ESR_SCHEMA_PATH,
    LINUX_POLICIES_PATH,
    RELEASE_SCHEMA_PATH,
    SCHEMAS_DIR,
    UPSTREAM_HTML_PATH,
    SchemaPolicyDefinition,
)
from .conversion import (
    build_schema_policy,
    convert_upstream_html_to_policies,
    filter_policies_for_target_version,
    schema_to_json_schema,
)
from .snippet_parser import load_linux_policy_examples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Mozilla policy-templates documentation to internal JSON schemas."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=UPSTREAM_HTML_PATH,
        help=(
            "Path to the downloaded HTML from https://mozilla.github.io/policy-templates/ "
            f"(default: {UPSTREAM_HTML_PATH})"
        ),
    )
    parser.add_argument(
        "--linux-policies-input",
        type=Path,
        default=LINUX_POLICIES_PATH,
        help=(
            "Path to the official Linux example policies.json snapshot used to enrich nested "
            f"schema inference (default: {LINUX_POLICIES_PATH})"
        ),
    )
    parser.add_argument(
        "--release-output",
        type=Path,
        default=RELEASE_SCHEMA_PATH,
        help=f"Output path for Firefox Release schema (default: {RELEASE_SCHEMA_PATH})",
    )
    parser.add_argument(
        "--esr-output",
        type=Path,
        default=ESR_SCHEMA_PATH,
        help=f"Output path for Firefox ESR schema (default: {ESR_SCHEMA_PATH})",
    )
    parser.add_argument(
        "--release-channel",
        default="release-149",
        help="Channel string stored in the Release schema (default: release-149).",
    )
    parser.add_argument(
        "--release-version",
        default="149.0",
        help="Version string stored in the Release schema (default: 149.0).",
    )
    parser.add_argument(
        "--esr-channel",
        default="esr-140.9",
        help="Channel string stored in the ESR schema (default: esr-140.9).",
    )
    parser.add_argument(
        "--esr-version",
        default="140.9",
        help="Version string stored in the ESR schema (default: 140.9).",
    )
    parser.add_argument(
        "--source-tag",
        default="mozilla-policy-templates-v7.9",
        help=(
            "Source tag identifier stored in the schemas (default: mozilla-policy-templates-v7.9). "
            "Useful for tracking which upstream snapshot was used."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    upstream_entries = convert_upstream_html_to_policies(args.input)
    linux_policy_examples = load_linux_policy_examples(args.linux_policies_input)

    schema_policies: list[SchemaPolicyDefinition] = [
        build_schema_policy(entry, linux_policy_examples=linux_policy_examples)
        for entry in upstream_entries
    ]

    release_schema = schema_to_json_schema(
        channel=args.release_channel,
        version=args.release_version,
        source=args.source_tag,
        policies=filter_policies_for_target_version(schema_policies, args.release_version),
    )

    esr_schema = schema_to_json_schema(
        channel=args.esr_channel,
        version=args.esr_version,
        source=args.source_tag,
        policies=filter_policies_for_target_version(schema_policies, args.esr_version),
    )

    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    args.release_output.write_text(
        json.dumps(release_schema, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    args.esr_output.write_text(
        json.dumps(esr_schema, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Wrote Release schema to {args.release_output}")
    print(f"Wrote ESR schema to {args.esr_output}")
