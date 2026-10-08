"""Conservative checks for accidentally published connection configuration."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def violations() -> list[str]:
    findings: list[str] = []
    connection_fields = {
        "DATABASE_URL",
        "MIGRATION_DATABASE_URL",
        "SYNC_DATABASE_URL",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_APP_USER",
        "POSTGRES_APP_PASSWORD",
        "POSTGRES_SYNC_USER",
        "POSTGRES_SYNC_PASSWORD",
        "POSTGRES_PORT",
        "MLB_API_BASE_URL",
        "FRONTEND_URL",
        "NEXT_PUBLIC_API_URL",
        "API_INTERNAL_URL",
        "BACKEND_HOST",
        "BACKEND_BIND_HOST",
        "BACKEND_PORT",
        "BACKEND_ALLOWED_HOSTS",
        "FRONTEND_HOST",
        "FRONTEND_BIND_HOST",
        "FRONTEND_PORT",
        "FRONTEND_ALLOWED_HOSTS",
    }
    for path in (ROOT / ".env.example", ROOT / "frontend" / ".env.example"):
        values = dict(
            line.split("=", 1)
            for line in path.read_text(encoding="utf-8").splitlines()
            if "=" in line and not line.startswith("#")
        )
        required = (
            connection_fields
            if path.parent == ROOT
            else {
                "API_INTERNAL_URL",
                "NEXT_PUBLIC_API_URL",
                "FRONTEND_ALLOWED_HOSTS",
            }
        )
        for name in required:
            if values.get(name) != "":
                findings.append(f"{path.relative_to(ROOT)} must keep {name} blank")
    db_block = (
        (ROOT / "docker-compose.yml")
        .read_text(encoding="utf-8")
        .split("  backend:", 1)[0]
    )
    if "    ports:" in db_block:
        findings.append("PostgreSQL must not publish host ports")
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    if "env_file:" in compose:
        findings.append("Compose services must receive only explicitly listed settings")
    if '"${BACKEND_BIND_HOST}:${BACKEND_PORT}:${BACKEND_PORT}"' not in compose:
        findings.append("Backend host publishing must use BACKEND_BIND_HOST")
    if '"${FRONTEND_BIND_HOST}:${FRONTEND_PORT}:${FRONTEND_PORT}"' not in compose:
        findings.append("Frontend host publishing must use FRONTEND_BIND_HOST")
    return findings


if __name__ == "__main__":
    errors = violations()
    if errors:
        raise SystemExit("\n".join(errors))
    print("Public configuration check passed")
