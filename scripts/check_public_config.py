"""Conservative checks for accidentally published connection configuration."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_CREDENTIAL_FIELDS = {
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
}
_CREDENTIAL_SUFFIXES = ("_API_KEY", "_PASSWORD", "_SECRET", "_TOKEN")
_ASSIGNMENT = re.compile(
    r"^\s*[\"']?(?P<name>[A-Z][A-Z0-9_]*)[\"']?\s*[:=]\s*(?P<value>.*?)\s*$"
)
_IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
_IPV6_LOOPBACK = re.compile(r"\[\s*:{2}\s*1\s*\]")
_NUMERIC_PORT_ASSIGNMENT = re.compile(
    r"^\s*[A-Z][A-Z0-9_]*PORT[A-Z0-9_]*\s*[:=]\s*[\"']?\d+[\"']?\s*$",
    re.MULTILINE,
)
_NUMERIC_URL_PORT = re.compile(r"[a-z][a-z0-9+.-]*://[^\s/:]+:\d+(?:[/\s]|$)")
_URL_CREDENTIALS = re.compile(r"[a-z][a-z0-9+.-]*://[^\s/:]+:[^\s/@]+@")


def _is_credential_field(name: str) -> bool:
    return name in _CREDENTIAL_FIELDS or name.endswith(_CREDENTIAL_SUFFIXES)


def _is_environment_reference(value: str) -> bool:
    value = value.strip().strip("\"'")
    return value.startswith("${") and value.endswith("}")


def _content_violations(path: str, content: str) -> list[str]:
    """Return safe, value-free findings for one public file."""
    findings: list[str] = []
    normalized_path = path.replace("\\", "/")
    filename = Path(normalized_path).name

    if filename.startswith(".env") and not filename.endswith(".example"):
        findings.append(
            f"{normalized_path}: private environment file must not be public"
        )

    for line_number, line in enumerate(content.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = _ASSIGNMENT.match(line)
        if not match:
            continue
        name = match.group("name")
        value = match.group("value").strip()
        if not value or not _is_credential_field(name):
            continue
        if filename.endswith(".env.example"):
            findings.append(
                f"{normalized_path}:{line_number}: credential field {name} must be blank"
            )
        elif not _is_environment_reference(value):
            findings.append(
                f"{normalized_path}:{line_number}: literal credential in {name}"
            )

    if _IPV4.search(content) or _IPV6_LOOPBACK.search(content):
        findings.append(f"{normalized_path}: literal IP address")
    if _NUMERIC_PORT_ASSIGNMENT.search(content) or _NUMERIC_URL_PORT.search(content):
        findings.append(f"{normalized_path}: literal numeric network port")
    if _URL_CREDENTIALS.search(content):
        findings.append(f"{normalized_path}: credentials embedded in URL")

    return findings


def violations(path: str | None = None, content: str | None = None) -> list[str]:
    """Check one supplied file, or the repository's public configuration files."""
    if path is not None:
        return _content_violations(path, content or "")
    if content is not None:
        raise TypeError("content requires path")

    findings: list[str] = []
    for config_path in (ROOT / ".env.example", ROOT / "frontend" / ".env.example"):
        if config_path.exists():
            findings.extend(
                _content_violations(
                    config_path.relative_to(ROOT).as_posix(),
                    config_path.read_text(encoding="utf-8"),
                )
            )

    compose_path = ROOT / "docker-compose.yml"
    compose = compose_path.read_text(encoding="utf-8")
    db_block = compose.split("  backend:", 1)[0]
    if "    ports:" in db_block:
        findings.append("PostgreSQL must not publish host ports")
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
