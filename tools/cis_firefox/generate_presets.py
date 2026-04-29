from __future__ import annotations

import argparse
import sys

from app.compliance.firefox.cis.generation import write_generated_layers


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CIS Firefox policy layer artifacts.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Build and validate layers without writing generated artifacts.",
    )
    parser.add_argument("--benchmark-id", help="Benchmark id to generate (default: current).")
    parser.add_argument("--upstream-version", help="Benchmark version to generate.")
    args = parser.parse_args()

    if args.check:
        from app.compliance.firefox.cis.generation import build_all_cis_layers

        layers = build_all_cis_layers(
            benchmark_id=args.benchmark_id,
            upstream_version=args.upstream_version,
        )
        for layer in layers:
            print(
                f"validated cis_l{layer.level}.{layer.schema_channel}: "
                f"{len(layer.recommendation_ids)} recommendations, {len(layer.policies)} top-level policies"
            )
        return 0

    written = write_generated_layers(
        benchmark_id=args.benchmark_id,
        upstream_version=args.upstream_version,
    )
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
