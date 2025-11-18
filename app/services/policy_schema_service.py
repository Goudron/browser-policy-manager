from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from app.models.policy_schema import PolicyDefinition, PolicySchema

BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = BASE_DIR / "schemas" / "policies"


# Channels we support and their corresponding schema files.
CHANNEL_TO_FILENAME: dict[str, str] = {
    "release-145": "firefox-release-145.json",
    "esr-140": "firefox-esr-140.json",
}


class UnknownPolicyChannelError(ValueError):
    """Raised when an unknown policy channel is requested."""


def _get_schema_path(channel: str) -> Path:
    try:
        filename = CHANNEL_TO_FILENAME[channel]
    except KeyError as exc:
        raise UnknownPolicyChannelError(f"Unknown policy channel: {channel!r}") from exc

    path = SCHEMAS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Policy schema file not found: {path}")
    return path


@cache
def load_policy_schema(channel: str) -> PolicySchema:
    """Load and cache the policy schema for a given channel.

    The result is cached in memory for the lifetime of the process.
    """
    path = _get_schema_path(channel)
    data = json.loads(path.read_text(encoding="utf-8"))
    return PolicySchema.model_validate(data)


def get_policy_definition(channel: str, policy_id: str) -> PolicyDefinition | None:
    """Return a specific policy definition by ID for the given channel."""
    schema = load_policy_schema(channel)
    return schema.get_policy(policy_id)
