from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
UPSTREAM_HTML_PATH = BASE_DIR / "data" / "upstream" / "policy-templates" / "policy-templates.html"

SCHEMAS_DIR = BASE_DIR / "app" / "schemas" / "policies"
DEFAULT_SCHEMA_TARGETS_PATH = BASE_DIR / "tools" / "firefox_schema_targets.json"
DEFAULT_SCHEMA_INPUTS_MANIFEST_PATH = (
    BASE_DIR / "tools" / "firefox_schema_inputs_manifest_0_9_4.json"
)
GENERATOR_IDENTITY = "bpm-firefox-policy-schema-converter/v1"
GENERATOR_ENTRYPOINT = "tools/convert_policies_from_upstream.py"

ENUM_WRAPPER_KEY = "__bpm_enum__"
SCALAR_TYPES = {"boolean", "integer", "number", "string"}
PREFERENCES_STATUS_ENUM = ["default", "locked", "user", "clear"]
PREFERENCES_TYPE_ENUM = ["number", "boolean", "string"]
HTTP_OR_HTTPS_PATTERN = r"^https?://"
HTTPS_URI_TEMPLATE_PATTERN = r"^https://.*%s.*$"
SEARCH_TERMS_PATTERN = r"\{searchTerms\}"
HANDLER_ACTION_ENUM = ["saveToDisk", "useHelperApp", "useSystemDefault"]


@dataclass
class UpstreamPolicyEntry:
    """A single policy as extracted from the documentation site."""

    name: str
    policy_key: str
    description: str
    compatibility: str | None
    section_text: str | None
    policies_json_snippet: str | None
    property_descriptions: dict[str, str] | None = None


@dataclass
class SchemaPolicyDefinition:
    """Representation of a policy in our internal JSON schema."""

    id: str
    type: str
    description_key: str
    categories: list[str]
    min_version: str | None
    max_version: str | None
    deprecated: bool
    enum: list[Any] | None
    items_type: str | None
    items: dict[str, Any] | None
    properties: dict[str, dict]
    additional_properties: bool
    additional_properties_schema: dict[str, Any] | None
    schema: dict[str, Any] | None = None


@dataclass(frozen=True)
class SchemaBuildTarget:
    """One independently generated bundled Firefox policy schema."""

    channel: str
    version: str
    source_tag: str
    documentation_input: Path
    linux_policies_input: Path
    output: Path
    schema_metadata: dict[str, Any] | None = None


def _repository_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def _load_input_provenance() -> dict[str, dict[str, Any]]:
    """Return checksum-pinned source identity indexed by BPM source tag.

    The target manifest deliberately names only a source tag and local cache paths.
    This keeps raw URLs and checksums in the single M3-01 provisioning manifest while
    making every generated bundle carry the exact identity used to verify its inputs.
    """
    payload = json.loads(DEFAULT_SCHEMA_INPUTS_MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 2:
        raise ValueError("Schema input manifest must use schema_version 2")
    raw_inputs = payload.get("inputs")
    if not isinstance(raw_inputs, list):
        raise ValueError("Schema input manifest must contain an inputs list")

    result: dict[str, dict[str, Any]] = {}
    for item in raw_inputs:
        if not isinstance(item, dict):
            raise ValueError("Schema input manifest contains an invalid input set")
        source_tag = item.get("source_tag")
        files = item.get("files")
        if not isinstance(source_tag, str) or not isinstance(files, list):
            raise ValueError("Schema input manifest contains an incomplete input set")
        if source_tag in result:
            raise ValueError("Schema input manifest contains duplicate source tags")
        files_by_name = {
            file.get("name"): file
            for file in files
            if isinstance(file, dict) and isinstance(file.get("name"), str)
        }
        expected_files = {"policy-templates.md", "linux-policies.json"}
        if set(files_by_name) != expected_files:
            raise ValueError("Schema input manifest must declare the two converter inputs exactly")
        for file in files_by_name.values():
            if not all(
                isinstance(file.get(field), expected_type)
                for field, expected_type in (("url", str), ("bytes", int), ("sha256", str))
            ):
                raise ValueError("Schema input manifest contains invalid file provenance")
        if not all(
            isinstance(item.get(field), str)
            for field in ("upstream_tag", "upstream_release_url", "license_spdx", "license_url")
        ):
            raise ValueError("Schema input manifest contains incomplete source provenance")
        result[source_tag] = item
    return result


def _schema_metadata(
    raw_target: dict[str, Any],
    source_input: dict[str, Any],
) -> dict[str, Any]:
    """Build the immutable x-bpm metadata emitted into a schema bundle."""
    required_target_fields = {
        "artifact_id",
        "line_id",
        "firefox_line",
        "firefox_version",
        "ui_label",
    }
    if not all(
        isinstance(raw_target.get(field), str) and raw_target[field]
        for field in required_target_fields
    ):
        raise ValueError("Schema target manifest contains incomplete artifact metadata")
    if raw_target["artifact_id"] != raw_target["channel"]:
        raise ValueError("Schema target artifact_id must equal its exact channel")
    try:
        firefox_line = int(raw_target["firefox_line"])
    except ValueError as error:
        raise ValueError("Schema target firefox_line must be numeric") from error
    if firefox_line <= 0:
        raise ValueError("Schema target firefox_line must be positive")

    expected_documentation = (
        BASE_DIR
        / "data"
        / "upstream"
        / "policy-templates"
        / source_input["upstream_tag"]
        / "policy-templates.md"
    )
    expected_linux = expected_documentation.with_name("linux-policies.json")
    if _repository_path(raw_target["documentation_input"]) != expected_documentation:
        raise ValueError("Schema target documentation input does not match its pinned source tag")
    if _repository_path(raw_target["linux_policies_input"]) != expected_linux:
        raise ValueError("Schema target Linux input does not match its pinned source tag")

    files = {file["name"]: file for file in source_input["files"]}
    return {
        "artifact_id": raw_target["artifact_id"],
        "line_id": raw_target["line_id"],
        "firefox_line": firefox_line,
        "firefox_version": raw_target["firefox_version"],
        "ui_label": raw_target["ui_label"],
        "source_provenance": {
            "source_tag": raw_target["source_tag"],
            "upstream_tag": source_input["upstream_tag"],
            "upstream_release_url": source_input["upstream_release_url"],
            "license_spdx": source_input["license_spdx"],
            "license_url": source_input["license_url"],
            "inputs": {
                "policy-templates.md": {
                    "url": files["policy-templates.md"]["url"],
                    "bytes": files["policy-templates.md"]["bytes"],
                    "sha256": files["policy-templates.md"]["sha256"],
                },
                "linux-policies.json": {
                    "url": files["linux-policies.json"]["url"],
                    "bytes": files["linux-policies.json"]["bytes"],
                    "sha256": files["linux-policies.json"]["sha256"],
                },
            },
        },
        "generator": {
            "identity": GENERATOR_IDENTITY,
            "entrypoint": GENERATOR_ENTRYPOINT,
        },
    }


def load_schema_build_targets(
    path: Path = DEFAULT_SCHEMA_TARGETS_PATH,
) -> tuple[SchemaBuildTarget, ...]:
    """Load and validate the declarative, multi-channel schema build manifest."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_targets = payload.get("targets")
    if not isinstance(raw_targets, list) or not raw_targets:
        raise ValueError(f"Schema target manifest {path} must contain a non-empty targets list")

    required = {
        "channel",
        "version",
        "source_tag",
        "documentation_input",
        "linux_policies_input",
        "output",
        "artifact_id",
        "line_id",
        "firefox_line",
        "firefox_version",
        "ui_label",
    }
    input_provenance = _load_input_provenance()
    targets: list[SchemaBuildTarget] = []
    for raw_target in raw_targets:
        if not isinstance(raw_target, dict) or set(raw_target) != required:
            raise ValueError(
                f"Schema target manifest {path} has invalid target fields; expected {sorted(required)}"
            )
        if not all(isinstance(raw_target[field], str) and raw_target[field] for field in required):
            raise ValueError(f"Schema target manifest {path} contains an empty target field")
        source_tag = raw_target["source_tag"]
        source_input = input_provenance.get(source_tag)
        if source_input is None:
            raise ValueError(f"Schema target {raw_target['channel']} has an unknown source tag")
        targets.append(
            SchemaBuildTarget(
                channel=raw_target["channel"],
                version=raw_target["version"],
                source_tag=source_tag,
                documentation_input=_repository_path(raw_target["documentation_input"]),
                linux_policies_input=_repository_path(raw_target["linux_policies_input"]),
                output=_repository_path(raw_target["output"]),
                schema_metadata=_schema_metadata(raw_target, source_input),
            )
        )

    channels = [target.channel for target in targets]
    outputs = [target.output for target in targets]
    if len(channels) != len(set(channels)) or len(outputs) != len(set(outputs)):
        raise ValueError(f"Schema target manifest {path} contains duplicate channels or outputs")
    return tuple(targets)
