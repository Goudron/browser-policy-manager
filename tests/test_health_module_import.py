from __future__ import annotations

import asyncio
import inspect

from app.api import health  # type: ignore
from app.main import app
from tests.support import make_test_client


def test_health_module_import_and_handlers():
    assert hasattr(health, "router")

    with make_test_client(app) as client:
        for path in ("/health", "/health/ready"):
            response = client.get(path)
            assert response.status_code == 200

    for route in health.router.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            continue
        result = endpoint()  # type: ignore[misc]
        if asyncio.iscoroutine(result):
            result = asyncio.run(result)
        assert result is None or isinstance(result, (dict, str))

    for name in dir(health):
        obj = getattr(health, name)
        if inspect.isfunction(obj) or asyncio.iscoroutinefunction(obj):
            try:
                result = obj()  # type: ignore[misc]
            except TypeError:
                continue
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)
            assert result is None or isinstance(result, (dict, str))
