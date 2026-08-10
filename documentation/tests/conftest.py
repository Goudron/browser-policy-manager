"""Apply the repository execution taxonomy to documentation-only pytest runs."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.marker_policy import OwnershipPolicyError, markers_for_path, primary_markers

pytest_plugins = ("tests.browser.harness",)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    root = Path(str(config.rootpath))
    for item in items:
        try:
            path = Path(str(item.fspath)).resolve().relative_to(root)
        except ValueError:
            path = Path(str(item.fspath))
        try:
            markers = markers_for_path(path)
        except OwnershipPolicyError as error:
            raise pytest.UsageError(str(error)) from error
        for marker in sorted(markers):
            item.add_marker(marker)
        layers = primary_markers(marker.name for marker in item.iter_markers())
        if len(layers) != 1:
            raise pytest.UsageError(
                f"{item.nodeid} must have exactly one primary test layer; found {sorted(layers)}"
            )
