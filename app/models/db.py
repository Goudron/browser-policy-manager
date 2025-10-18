from __future__ import annotations

import os
from datetime import UTC, datetime

from sqlmodel import Field, Session, SQLModel, create_engine

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..")
DB_PATH = os.path.abspath(os.path.join(DATA_DIR, "data.db"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False}
)


class PolicyProfile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str | None = None
    active_schema_version: str
    payload_json: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PolicyVersion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="policyprofile.id")
    author: str | None = None
    payload_json: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
