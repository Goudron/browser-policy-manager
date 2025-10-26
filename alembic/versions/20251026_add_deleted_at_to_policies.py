"""add deleted_at to policies

Revision ID: 20251026_add_deleted_at
Revises: 5cb73fdb68ed
Create Date: 2025-10-26 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251026_add_deleted_at"
down_revision = "5cb73fdb68ed"
branch_labels = None
depends_on = None


def _insp():
    return sa.inspect(op.get_bind())


def _has_table(table: str) -> bool:
    return _insp().has_table(table)


def _has_column(table: str, column: str) -> bool:
    cols = {c["name"] for c in _insp().get_columns(table)} if _has_table(table) else set()
    return column in cols


def upgrade() -> None:
    insp = _insp()
    # 1) Если таблицы policies нет — создаём минимальную схему
    if not insp.has_table("policies"):
        op.create_table(
            "policies",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(length=255), nullable=False, unique=True),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column(
                "schema_version", sa.String(length=50), nullable=False, server_default="esr-140"
            ),
            # Храним flags как TEXT (JSON сериализуется приложением)
            sa.Column("flags", sa.Text, nullable=False, server_default="{}"),
            sa.Column("owner", sa.String(length=255), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        # Можно убрать server_default, если не нужно в рантайме:
        with op.batch_alter_table("policies") as batch_op:
            batch_op.alter_column("schema_version", server_default=None)
            batch_op.alter_column("flags", server_default=None)
            batch_op.alter_column("created_at", server_default=None)
            batch_op.alter_column("updated_at", server_default=None)
        return  # таблица уже создана с deleted_at, дальше идти не нужно

    # 2) Если таблица есть — добавляем колонку, если её нет
    if not _has_column("policies", "deleted_at"):
        with op.batch_alter_table("policies") as batch_op:
            batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Не удаляем таблицу, только колонку при её наличии
    if _has_table("policies") and _has_column("policies", "deleted_at"):
        with op.batch_alter_table("policies") as batch_op:
            batch_op.drop_column("deleted_at")
