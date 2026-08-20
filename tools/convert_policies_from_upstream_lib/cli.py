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

    for target_index, target in enumerate(targets, start=1):
        print(
            f"phase schema-target: [{target_index}/{len(targets)}] channel={target.channel}",
            flush=True,
        )
        source_key = (target.documentation_input, target.linux_policies_input)
        schema_policies = policy_cache.get(source_key)
        if schema_policies is None:
            linux_policy_examples = load_linux_policy_examples(
                target.linux_policies_input,
                source_tag=target.source_tag,
            )
            upstream_entries = add_missing_linux_example_entries(
                convert_upstream_document_to_policies(target.documentation_input),
                linux_policy_examples,
            )
            schema_policies = []
            policy_total = len(upstream_entries)
            for policy_index, entry in enumerate(upstream_entries, start=1):
                schema_policies.append(
                    build_schema_policy(entry, linux_policy_examples=linux_policy_examples)
                )
                if policy_index == 1 or policy_index % 25 == 0 or policy_index == policy_total:
                    print(
                        "phase schema-policy: "
                        f"channel={target.channel} [{policy_index}/{policy_total}] "
                        f"policy={entry.policy_key}",
                        flush=True,
                    )
            policy_cache[source_key] = schema_policies

        selected_policies = filter_policies_for_target_version(
            schema_policies,
            target.version,
            target_channel=target.channel,
        )
        print(
            "phase schema-policy-filter: "
            f"channel={target.channel} [{len(selected_policies)}/{len(schema_policies)}]",
            flush=True,
        )
        schema = schema_to_json_schema(
            channel=target.channel,
            version=target.version,
            source=target.source_tag,
            policies=selected_policies,
            schema_metadata=target.schema_metadata,
        )
        apply_documented_schema_overrides(
            schema,
            target.version,
            target_channel=target.channel,
        )
        target.output.parent.mkdir(parents=True, exist_ok=True)
        target.output.write_text(
            json.dumps(schema, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Wrote {target.channel} schema to {target.output}")


def main() -> None:
    args = parse_args()
    generate_schema_targets(load_schema_build_targets(args.targets_file))
