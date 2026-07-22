from __future__ import annotations

import argparse
import json
from pathlib import Path

from .common import (
    DEFAULT_SCHEMA_TARGETS_PATH,
    SchemaBuildTarget,
    SchemaPolicyDefinition,
    load_schema_build_targets,
)
from .conversion import (
    add_missing_linux_example_entries,
    apply_documented_schema_overrides,
    build_schema_policy,
    convert_upstream_document_to_policies,
    filter_policies_for_target_version,
    schema_to_json_schema,
)
from .snippet_parser import load_linux_policy_examples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Mozilla policy-templates documentation to internal JSON schemas."
    )
    parser.add_argument(
        "--targets-file",
        type=Path,
        default=DEFAULT_SCHEMA_TARGETS_PATH,
        help=(
            "JSON manifest that declares each independent channel, version, source, input, and output "
            f"(default: {DEFAULT_SCHEMA_TARGETS_PATH})"
        ),
    )
    return parser.parse_args()


def generate_schema_targets(targets: tuple[SchemaBuildTarget, ...]) -> None:
    """Generate every target independently, caching only identical upstream input parsing."""
    policy_cache: dict[tuple[Path, Path], list[SchemaPolicyDefinition]] = {}

    for target in targets:
        source_key = (target.documentation_input, target.linux_policies_input)
        schema_policies = policy_cache.get(source_key)
        if schema_policies is None:
            linux_policy_examples = load_linux_policy_examples(target.linux_policies_input)
            upstream_entries = add_missing_linux_example_entries(
                convert_upstream_document_to_policies(target.documentation_input),
                linux_policy_examples,
            )
            schema_policies = [
                build_schema_policy(entry, linux_policy_examples=linux_policy_examples)
                for entry in upstream_entries
            ]
            policy_cache[source_key] = schema_policies

        schema = schema_to_json_schema(
            channel=target.channel,
            version=target.version,
            source=target.source_tag,
            policies=filter_policies_for_target_version(schema_policies, target.version),
        )
        apply_documented_schema_overrides(schema, target.version)
        target.output.parent.mkdir(parents=True, exist_ok=True)
        target.output.write_text(
            json.dumps(schema, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Wrote {target.channel} schema to {target.output}")


def main() -> None:
    args = parse_args()
    generate_schema_targets(load_schema_build_targets(args.targets_file))
