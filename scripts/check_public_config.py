"""Reject private connection configuration in tracked files without printing values."""

import ipaddress
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IP_CANDIDATE = re.compile(
    r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])|[\da-fA-F:]*:[\da-fA-F:]+"
)
LITERAL_PORT = re.compile(
    r"\b[a-z][a-z0-9+.-]*://[^\s/]+:\d+\b"
    r"|\b\w*PORT\s*[:=]\s*[\"']?\d+\b"
    r"|^\s*EXPOSE\s+\d+|^\s*[-]\s*[\"']?\d+:\d+",
    re.IGNORECASE,
)
CREDENTIAL = re.compile(
    r"\b[a-z][a-z0-9+.-]*://[^\s/:]+:([^\s@]+)@"
    r"|^\s*[\"']?\w*(?:PASSWORD|SECRET|API_KEY|ACCESS_TOKEN|PRIVATE_KEY)"
    r"[\"']?\s*[:=]\s*(.+)",
    re.IGNORECASE,
)


def is_reference(value: str) -> bool:
    value = value.strip().strip("\"'")
    return not value or value.startswith(("$", "<", "os.environ", "process.env"))


def violations(path: str, content: str) -> list[tuple[int, str]]:
    name = Path(path).name
    if name.startswith(".env") and not name.endswith(".example"):
        return [(1, "private environment file is tracked")]
    issues = []
    for number, line in enumerate(content.splitlines(), 1):
        if name.startswith(".env") and name.endswith(".example"):
            key, separator, value = line.partition("=")
            if (
                separator
                and not key.startswith("#")
                and key != "ENVIRONMENT"
                and value.strip()
            ):
                issues.append((number, "environment example must leave values blank"))
        for match in IP_CANDIDATE.finditer(line):
            try:
                ipaddress.ip_address(match.group())
            except ValueError:
                continue
            issues.append((number, "literal IP address"))
        if LITERAL_PORT.search(line):
            issues.append((number, "literal port configuration"))
        for match in CREDENTIAL.finditer(line):
            value = next(group for group in match.groups() if group is not None)
            if not is_reference(value):
                issues.append((number, "literal credential assignment"))
    return issues


def main() -> int:
    paths = (
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
        )
        .decode()
        .split("\0")
    )
    errors = []
    for name in filter(None, paths):
        path = ROOT / name
        if not path.is_file():
            continue
        content = path.read_bytes()
        if b"\0" in content:
            continue
        for line, reason in violations(name, content.decode("utf-8", errors="replace")):
            errors.append(f"{name}:{line}: {reason}")
    if errors:
        print("Public configuration check failed (values redacted):")
        print("\n".join(errors))
        return 1
    print("Public configuration check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
