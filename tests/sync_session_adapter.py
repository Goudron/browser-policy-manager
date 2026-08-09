from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session


class SyncSessionAdapter:
    """Test-only bridge for legacy unit fixtures that intentionally use sync SQLite."""

    def __init__(self, session: Session) -> None:
        self._session = session

    async def scalars(self, *args: Any, **kwargs: Any) -> Any:
        return self._session.scalars(*args, **kwargs)

    async def scalar(self, *args: Any, **kwargs: Any) -> Any:
        return self._session.scalar(*args, **kwargs)

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        return self._session.execute(*args, **kwargs)

    async def flush(self) -> None:
        self._session.flush()

    async def refresh(self, instance: Any) -> None:
        self._session.refresh(instance)

    async def commit(self) -> None:
        self._session.commit()

    async def rollback(self) -> None:
        self._session.rollback()

    async def close(self) -> None:
        self._session.close()

    def add(self, instance: Any) -> None:
        self._session.add(instance)
