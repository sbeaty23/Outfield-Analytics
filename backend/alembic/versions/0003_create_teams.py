"""create teams table

Revision ID: 0003_create_teams
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_create_teams"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mlb_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("location_name", sa.String(100), nullable=False),
        sa.Column("team_name", sa.String(100)),
        sa.Column("abbreviation", sa.String(8), nullable=False),
        sa.Column("league_id", sa.Integer()),
        sa.Column("league_name", sa.String(100), nullable=False),
        sa.Column("division_id", sa.Integer()),
        sa.Column("division_name", sa.String(100)),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("mlb_id"),
    )
    op.create_index("ix_teams_mlb_id", "teams", ["mlb_id"])


def downgrade() -> None:
    op.drop_index("ix_teams_mlb_id", table_name="teams")
    op.drop_table("teams")
