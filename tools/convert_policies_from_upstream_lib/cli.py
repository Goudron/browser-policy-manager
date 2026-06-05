from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.schema_channels import (
    CURRENT_ESR_SCHEMA_CHANNEL,
    CURRENT_RELEASE_SCHEMA_CHANNEL,
    SCHEMA_MOZILLA_VERSIONS,
)

from .common import (
    ESR_SCHEMA_PATH,
    LINUX_POLICIES_PATH,
    RELEASE_SCHEMA_PATH,
    SCHEMAS_DIR,
    UPSTREAM_HTML_PATH,
    SchemaPolicyDefinition,
)
from .conversion import (
    add_missing_linux_example_entries,
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
        default=CURRENT_RELEASE_SCHEMA_CHANNEL,
        help=(
            "Channel string stored in the Release schema "
            f"(default: {CURRENT_RELEASE_SCHEMA_CHANNEL})."
        ),
    )
    parser.add_argument(
        "--release-version",
        default=SCHEMA_MOZILLA_VERSIONS[CURRENT_RELEASE_SCHEMA_CHANNEL],
        help=(
            "Version string stored in the Release schema "
            f"(default: {SCHEMA_MOZILLA_VERSIONS[CURRENT_RELEASE_SCHEMA_CHANNEL]})."
        ),
    )
    parser.add_argument(
        "--esr-channel",
        default=CURRENT_ESR_SCHEMA_CHANNEL,
        help=(
            "Channel string stored in the ESR schema "
            f"(default: {CURRENT_ESR_SCHEMA_CHANNEL})."
        ),
    )
    parser.add_argument(
        "--esr-version",
        default=SCHEMA_MOZILLA_VERSIONS[CURRENT_ESR_SCHEMA_CHANNEL],
        help=(
            "Version string stored in the ESR schema "
            f"(default: {SCHEMA_MOZILLA_VERSIONS[CURRENT_ESR_SCHEMA_CHANNEL]})."
        ),
    )
    parser.add_argument(
        "--source-tag",
        default="mozilla-policy-templates-v7.11",
        help=(
            "Source tag identifier stored in the schemas (default: mozilla-policy-templates-v7.11). "
            "Useful for tracking which upstream snapshot was used."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    linux_policy_examples = load_linux_policy_examples(args.linux_policies_input)
    upstream_entries = add_missing_linux_example_entries(
        convert_upstream_html_to_policies(args.input),
        linux_policy_examples,
    )

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
