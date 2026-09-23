import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def run_alembic(database_url: str, *arguments: str) -> None:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", *arguments],
        check=True,
        env=environment,
    )


def test_initial_migration_upgrades_and_downgrades(tmp_path: Path) -> None:
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"

    run_alembic(database_url, "upgrade", "head")

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            'SELECT "key", "value" FROM system_metadata ORDER BY "key"'
        ).fetchall()

    assert rows == [
        ("application_name", "Outfield Analytics"),
        ("schema_version", "1"),
    ]

    run_alembic(database_url, "downgrade", "base")

    with sqlite3.connect(database_path) as connection:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name = 'system_metadata'"
        ).fetchone()

    assert table is None
