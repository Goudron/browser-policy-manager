## alembic/script.py.mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision if down_revision is not None else "None"}
Create Date: ${create_date}

"""

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
% if down_revision is None:
down_revision = None
% else:
down_revision = ${repr(down_revision)}
% endif
% if branch_labels is None:
branch_labels = None
% else:
branch_labels = ${repr(branch_labels)}
% endif
% if depends_on is None:
depends_on = None
% else:
depends_on = ${repr(depends_on)}
% endif


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
