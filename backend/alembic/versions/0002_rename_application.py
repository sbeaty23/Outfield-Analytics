"""Rename the application metadata.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    metadata = sa.table(
        "system_metadata",
        sa.column("key", sa.String()),
        sa.column("value", sa.Text()),
    )
    op.execute(
        metadata.update()
        .where(metadata.c.key == "application_name")
        .values(value="Outfield Analytics")
    )


def downgrade() -> None:
    # The former branding is intentionally not restored.
    pass
