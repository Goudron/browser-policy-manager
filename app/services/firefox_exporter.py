from __future__ import annotations

from typing import Any, Dict

import yaml


def to_yaml(policies: Dict[str, Any]) -> str:
    """
    Produce a Firefox Enterprise Policies YAML string.
    Tests expect a YAML document containing the 'policies' root.
    """
    doc = {"policies": policies}
    # Stable, readable YAML; do not use flow style
    return yaml.safe_dump(doc, sort_keys=True, allow_unicode=True)
