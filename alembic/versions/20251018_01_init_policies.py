import sqlalchemy as sa

from alembic import op

# Revision identifiers, used by Alembic.
revision = "20251018_01_init_policies"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("schema_version", sa.String(length=50), nullable=False),
        sa.Column("flags", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_policies_name", "policies", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_policies_name", table_name="policies")
    op.drop_table("policies")
