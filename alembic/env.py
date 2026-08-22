from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic.script import ScriptDirectory
from sqlalchemy import inspect, pool, text
from sqlalchemy.engine import Connection, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# If your project has a declarative Base, you can import its metadata here:
# from app.db_models import Base
# target_metadata = Base.metadata
target_metadata = None  # We do not use autogeneration in this project.

# Alembic configuration
config = context.config

# Logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


LEGACY_REVISION_ALIASES = {
    "5cb73fdb68ed": "20251022_init_profiles",
    "20251026_add_deleted_at": "20251026_add_deleted_at_profiles",
    "20260323_rename_profiles": "20260323_normalize_profiles",
}

_PROFILE_TABLES = {"profiles", "policies"}
_BASE_PROFILE_COLUMNS = {
    "id",
    "name",
    "description",
    "schema_version",
    "flags",
    "owner",
    "created_at",
    "updated_at",
}
_SOURCE_SHAPES: dict[str, tuple[str, set[str]]] = {
    "5cb73fdb68ed": ("policies", _BASE_PROFILE_COLUMNS),
    "20251022_init_profiles": ("profiles", _BASE_PROFILE_COLUMNS),
    "20251026_add_deleted_at": ("policies", _BASE_PROFILE_COLUMNS | {"deleted_at"}),
    "20251026_add_deleted_at_profiles": (
        "profiles",
        _BASE_PROFILE_COLUMNS | {"deleted_at"},
    ),
    "20260323_rename_profiles": (
        "profiles",
        _BASE_PROFILE_COLUMNS | {"deleted_at", "revision"},
    ),
    "20260323_normalize_profiles": (
        "profiles",
        _BASE_PROFILE_COLUMNS | {"deleted_at", "revision"},
    ),
    "20260330_upgrade_profiles_to_firefox149": (
        "profiles",
        _BASE_PROFILE_COLUMNS | {"deleted_at", "revision"},
    ),
    "20260423_upgrade_profiles_to_firefox150": (
        "profiles",
        _BASE_PROFILE_COLUMNS | {"deleted_at", "revision"},
    ),
    "20260521_upgrade_profiles_to_firefox151": (
        "profiles",
        _BASE_PROFILE_COLUMNS | {"deleted_at", "revision"},
    ),
    "20260606_drop_profile_owner": (
        "profiles",
        (_BASE_PROFILE_COLUMNS - {"owner"}) | {"deleted_at", "revision"},
    ),
    "20260620_upgrade_profiles_to_firefox152": (
        "profiles",
        (_BASE_PROFILE_COLUMNS - {"owner"}) | {"deleted_at", "revision"},
    ),
    "20260721_upgrade_profiles_to_firefox153_dual_esr": (
        "profiles",
        (_BASE_PROFILE_COLUMNS - {"owner"}) | {"deleted_at", "revision"},
    ),
    "20260804_alembic_owns_profile_schema_and_data": (
        "profiles",
        (_BASE_PROFILE_COLUMNS - {"owner"}) | {"deleted_at", "revision", "compliance"},
    ),
    "20260804_add_profile_name_casefold": (
        "profiles",
        (_BASE_PROFILE_COLUMNS - {"owner"})
        | {"deleted_at", "revision", "compliance", "name_casefold"},
    ),
    "20260820_add_profile_baseline_provenance": (
        "profiles",
        (_BASE_PROFILE_COLUMNS - {"owner"})
        | {
            "deleted_at",
            "revision",
            "compliance",
            "name_casefold",
            "baseline_provenance",
            "preparation_idempotency_key",
            "preparation_request_fingerprint",
        },
    ),
    "20260821_add_profile_extension_provenance": (
        "profiles",
        (_BASE_PROFILE_COLUMNS - {"owner"})
        | {
            "deleted_at",
            "revision",
            "compliance",
            "name_casefold",
            "baseline_provenance",
            "extension_provenance",
            "preparation_idempotency_key",
            "preparation_request_fingerprint",
        },
    ),
    "20260821_add_profile_certificate_provenance": (
        "profiles",
        (_BASE_PROFILE_COLUMNS - {"owner"})
        | {
            "deleted_at",
            "revision",
            "compliance",
            "name_casefold",
            "baseline_provenance",
            "extension_provenance",
            "certificate_provenance",
            "preparation_idempotency_key",
            "preparation_request_fingerprint",
        },
    ),
}
_ALEMBIC_VERSION_MINIMUM_LENGTH = 128
_DEFAULT_ALEMBIC_URL = "sqlite:///./data/bpm.db"


# Read the URL ONLY from alembic.ini / injected Config
# (tests set it via set_main_option).
def get_url() -> str:
    """Resolve the target database from the same explicit setting as BPM."""
    configured_url = config.get_main_option("sqlalchemy.url")
    runtime_url = os.environ.get("BPM_DATABASE_URL")
    # Tests and recovery tooling intentionally inject a non-default Config URL
    # while their process has a separate BPM runtime database. That explicit
    # Config target must win; the checked-in default instead follows BPM's
    # runtime setting when an operator provides one.
    url = (
        configured_url
        if configured_url and configured_url != _DEFAULT_ALEMBIC_URL
        else runtime_url or configured_url
    )
    if not url:
        # Retained only for a deliberately injected Alembic-only configuration.
        url = os.environ.get("ALEMBIC_SQLALCHEMY_URL", "")
    if not url:
        raise RuntimeError("SQLAlchemy URL is not configured for Alembic")
    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return url


def run_migrations_offline() -> None:
    """Run migrations in offline mode (generate SQL without connecting)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Shared migration runner for an active connection."""
    _preflight_retained_source(connection)

    def ensure_version_capacity_after_step(*_args: object, **_kwargs: object) -> None:
        # Fresh installs create alembic_version in the first historical step.
        # Resize it while that short initial revision is current, before the
        # following long released revision identifier is written.
        _ensure_alembic_version_capacity(connection)

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        on_version_apply=[ensure_version_capacity_after_step],
    )
    with context.begin_transaction():
        context.run_migrations()


def _preflight_retained_source(connection: Connection) -> None:
    """
    Reject ambiguous input before Alembic writes and canonicalize the three
    released aliases only after their documented source shape is confirmed.

    This is intentionally a small migration preflight, not a repair tool:
    it never guesses an Alembic stamp, merges profile tables, or inspects row
    values. M4-06 owns backup/recovery proof for failures after a write.
    """
    inspector = inspect(connection)
    table_names = set(inspector.get_table_names())
    if "alembic_version" not in table_names:
        user_tables = table_names - {"sqlite_sequence"}
        if user_tables:
            raise RuntimeError(
                "Refusing unstamped non-empty database; restore/preflight a retained source "
                "instead of guessing an Alembic revision"
            )
        return

    rows = connection.execute(text("SELECT version_num FROM alembic_version")).fetchall()
    if len(rows) != 1:
        raise RuntimeError(
            "Refusing database with missing or multiple Alembic version rows; restore/preflight "
            "a retained source"
        )

    (version_num,) = rows[0]
    source_shape = _SOURCE_SHAPES.get(version_num)
    if source_shape is None:
        known = {script.revision for script in ScriptDirectory.from_config(config).walk_revisions()}
        if version_num not in known:
            raise RuntimeError(f"Refusing unknown Alembic revision {version_num!r}")
        raise RuntimeError(
            f"Refusing unsupported retained source shape for Alembic revision {version_num!r}"
        )

    expected_table, required_columns = source_shape
    actual_profile_tables = table_names & _PROFILE_TABLES
    if actual_profile_tables != {expected_table}:
        raise RuntimeError(
            "Refusing profile-table shape that disagrees with its Alembic revision: "
            f"expected {expected_table!r}, found {sorted(actual_profile_tables)!r}"
        )
    actual_columns = {column["name"] for column in inspector.get_columns(expected_table)}
    missing_columns = sorted(required_columns - actual_columns)
    if missing_columns:
        raise RuntimeError(
            f"Refusing {expected_table!r} shape for revision {version_num!r}: "
            f"missing {', '.join(missing_columns)}"
        )

    target = LEGACY_REVISION_ALIASES.get(version_num)
    if target is not None:
        connection.execute(
            text("""
                UPDATE alembic_version
                SET version_num = :target
                WHERE version_num = :current
                """),
            {"target": target, "current": version_num},
        )

    _ensure_alembic_version_capacity(connection)


def _ensure_alembic_version_capacity(connection: Connection) -> None:
    """Expand Alembic's historical PostgreSQL revision column before a long ID is written.

    Early BPM revisions inherited Alembic's ``VARCHAR(32)`` tracking column,
    while the released 20260330 revision identifier is longer. A later Alembic
    revision cannot repair that width because Alembic must write the long ID
    before it can reach it. The preflight expands retained stamped sources;
    Alembic's post-step callback expands fresh installs immediately after the
    short root revision is written. Runtime application code never alters
    schema or version data.
    """
    if connection.dialect.name != "postgresql":
        return
    version_column = next(
        (
            column
            for column in inspect(connection).get_columns("alembic_version")
            if column["name"] == "version_num"
        ),
        None,
    )
    if version_column is None:
        raise RuntimeError("Alembic version table is missing its version_num column")
    current_length = getattr(version_column["type"], "length", None)
    if current_length is None or current_length >= _ALEMBIC_VERSION_MINIMUM_LENGTH:
        return
    connection.execute(
        text(
            "ALTER TABLE alembic_version "
            f"ALTER COLUMN version_num TYPE VARCHAR({_ALEMBIC_VERSION_MINIMUM_LENGTH})"
        )
    )


def run_migrations_online_sync() -> None:
    """Synchronous engine path (sqlite+pysqlite, etc.)."""
    url = get_url()
    connectable = create_engine(url, poolclass=pool.NullPool, future=True)
    with connectable.connect() as connection:
        do_run_migrations(connection)
        if connection.in_transaction():
            connection.commit()
    connectable.dispose()


async def run_migrations_online_async() -> None:
    """Asynchronous engine path (sqlite+aiosqlite, postgresql+asyncpg, etc.)."""
    url = get_url()
    connectable: AsyncEngine = create_async_engine(url, poolclass=pool.NullPool, future=True)
    async with connectable.connect() as async_connection:
        await async_connection.run_sync(do_run_migrations)
        if async_connection.in_transaction():
            await async_connection.commit()
    await connectable.dispose()


def run_migrations_online() -> None:
    """Choose sync or async mode based on the URL scheme."""
    url = get_url()
    if "+aiosqlite" in url or "+asyncpg" in url or url.startswith("postgresql+"):
        # Rough heuristic: use async path when the driver is async.
        asyncio.run(run_migrations_online_async())
    else:
        run_migrations_online_sync()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
