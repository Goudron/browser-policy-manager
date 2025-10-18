from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, create_engine, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

# ---------------------------------------------------------------------
# Конфигурация БД (SQLite по умолчанию в ./var/bpm.sqlite3)
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # корень проекта
VAR_DIR = BASE_DIR / "var"
VAR_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = os.getenv("BPM_DB_PATH", str(VAR_DIR / "bpm.sqlite3"))

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Базовый класс декларативных моделей SQLAlchemy 2.0."""

    pass


# ---------------------------------------------------------------------
# Модели
# ---------------------------------------------------------------------


class PolicyProfile(Base):
    __tablename__ = "policy_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # форвард-ссылка на PolicyVersion без ignore
    versions: Mapped[list["PolicyVersion"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("policy_profiles.id"), nullable=False
    )
    author: Mapped[str] = mapped_column(String(128), default="system", nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile: Mapped[PolicyProfile] = relationship(back_populates="versions")


# ---------------------------------------------------------------------
# Инициализация схемы
# ---------------------------------------------------------------------


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


# Создаём таблицы при импорте модуля (безопасно для SQLite)
init_db()


# ---------------------------------------------------------------------
# Зависимость FastAPI: выдаёт Session и закрывает её по завершении запроса
# ---------------------------------------------------------------------


def get_session() -> Generator[Session, None, None]:
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
