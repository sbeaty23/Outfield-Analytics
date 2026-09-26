"""Create the system metadata table.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    system_metadata = op.create_table(
        "system_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_system_metadata_key"),
    )
    op.bulk_insert(
        system_metadata,
        [
            {"key": "application_name", "value": "Outfield Analytics"},
            {"key": "schema_version", "value": "1"},
        ],
    )


def downgrade() -> None:
    op.drop_table("system_metadata")
