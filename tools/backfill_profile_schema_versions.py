#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json

from app.db import get_session, init_db
from app.services.profile_schema_normalization import normalize_legacy_profile_schema_versions


async def run_backfill() -> dict[str, int]:
    await init_db()
    session_generator = get_session()
    session = await session_generator.__anext__()
    try:
        result = await normalize_legacy_profile_schema_versions(session)
        await session.commit()
        return {
            "scanned": result.scanned,
            "normalized": result.normalized,
            "skipped_invalid": result.skipped_invalid,
        }
    finally:
        try:
            await session_generator.__anext__()
        except StopAsyncIteration:
            pass


def main() -> int:
    print(json.dumps(asyncio.run(run_backfill()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
