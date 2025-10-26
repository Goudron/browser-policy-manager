# app/utils/yaml_io.py
# YAML serialization helpers with safe defaults.

from __future__ import annotations

from typing import Any

import yaml


def to_yaml(data: Any) -> str:
    """
    Serialize Python data to a YAML string using safe dumper.

    - Ensure Unicode output.
    - Block style for readability.
    - Sort keys disabled to preserve semantic ordering where present.
    """
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
