from __future__ import annotations
from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
from datetime import datetime
import os, json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..")
DB_PATH = os.path.abspath(os.path.join(DATA_DIR, "data.db"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

class PolicyProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    active_schema_version: str
    payload_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PolicyVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="policyprofile.id")
    author: Optional[str] = None
    payload_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

def init_db() -> None:
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
